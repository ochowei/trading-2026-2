"""TASK-023 的相對落後 overlay 與固定 v009 比較組。

候選是一個單部位組合：v009 訊號沿用原引擎，SOXX 上漲且 TSM 五日報酬
落後 SOXX 至少 3 個百分點時另有一種入場來源。此模組不連線、不下載資料，
也不建立真實委託；所有訊號只在共同 XNYS session 收盤後判定。
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd

_REPOSITORY = Path(__file__).resolve().parents[2]
_V009_PATH = (
    _REPOSITORY
    / "src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py"
)
_V009_SPEC = importlib.util.spec_from_file_location("task023_fixed_v009", _V009_PATH)
if _V009_SPEC is None or _V009_SPEC.loader is None:
    raise ImportError(f"無法載入 Source Bundle 綁定的 v009 引擎：{_V009_PATH}")
_V009 = importlib.util.module_from_spec(_V009_SPEC)
sys.modules[_V009_SPEC.name] = _V009
_V009_SPEC.loader.exec_module(_V009)

CostModel = _V009.CostModel
StrategySpec = _V009.StrategySpec
DEFAULT_SPEC = _V009.DEFAULT_SPEC
BASELINE_SPEC = _V009.DEFAULT_SPEC
BASE_COST = _V009.BASE_COST
STRESS_COST = _V009.STRESS_COST
indicators = _V009.indicators
_intraday_exit = _V009._intraday_exit

Component = Literal["v009", "industry-relative-lag"]


@dataclass(frozen=True)
class CombinedTrade:
    signal_session: pd.Timestamp
    entry_session: pd.Timestamp
    exit_session: pd.Timestamp
    raw_entry_price: float
    raw_exit_price: float
    executed_entry_price: float
    executed_exit_price: float
    shares: int
    fees: float
    pnl: float
    exit_reason: str
    held_sessions: int
    strategy_component: Component
    trigger_components: tuple[Component, ...]
    pre_entry_equity: float


def dual_asset_signals(
    tsm_bars: pd.DataFrame,
    soxx_bars: pd.DataFrame,
    *,
    spec: StrategySpec = DEFAULT_SPEC,
) -> pd.DataFrame:
    """回傳固定 v009 訊號、relative-lag 訊號及非交易的 absolute-only 對照分類。"""

    tsm = _V009.validate_bars(tsm_bars)
    soxx = _V009.validate_bars(soxx_bars)
    if not tsm.index.equals(soxx.index):
        raise ValueError("TSM 與 SOXX 必須使用完全相同的 XNYS session")
    frame = _V009.indicators(tsm, spec)
    tsm_return_5 = tsm["Close"] / tsm["Close"].shift(5) - 1.0
    soxx_return_5 = soxx["Close"] / soxx["Close"].shift(5) - 1.0
    relative_lag = (soxx_return_5 > 0.0) & ((tsm_return_5 - soxx_return_5) <= -0.03)
    absolute_only_control = (tsm_return_5 < 0.0) & ~relative_lag
    frame["tsm_return_5"] = tsm_return_5
    frame["soxx_return_5"] = soxx_return_5
    frame["relative_gap_5"] = tsm_return_5 - soxx_return_5
    frame["relative_lag_signal"] = relative_lag.fillna(False)
    # 這是固定的負向對照分類，不是候選訊號，也不產生額外 trial 或部位。
    frame["absolute_only_control"] = absolute_only_control.fillna(False)
    frame["v009_signal"] = frame["raw_signal"].fillna(False)
    return frame


def backtest(
    bars: pd.DataFrame,
    *,
    spec: StrategySpec = DEFAULT_SPEC,
    cost: CostModel = BASE_COST,
    reset_at_start: bool = False,
    signal_start: str | pd.Timestamp | None = None,
    signal_end: str | pd.Timestamp | None = None,
):
    """v005 legacy contract adapter：單資產時驗證固定 v009 訊號與執行元件。"""

    return _V009.backtest(
        bars,
        spec=spec,
        cost=cost,
        reset_at_start=reset_at_start,
        signal_start=signal_start,
        signal_end=signal_end,
    )


def combined_backtest(
    tsm_bars: pd.DataFrame,
    soxx_bars: pd.DataFrame,
    *,
    cost: CostModel,
    signal_start: str | pd.Timestamp,
    signal_end: str | pd.Timestamp,
) -> tuple[CombinedTrade, ...]:
    """執行 candidate：v009 同日優先、單一部位、next-open 進場與 v009 風控。"""

    spec = DEFAULT_SPEC
    frame = dual_asset_signals(tsm_bars, soxx_bars, spec=spec)
    cash = float(spec.initial_cash)
    trades: list[CombinedTrade] = []
    pending_signal_index: int | None = None
    pending_component: Component | None = None
    pending_triggers: tuple[Component, ...] = ()
    last_exit_index: int | None = None
    position: dict[str, object] | None = None
    time_exit_index: int | None = None
    start = pd.Timestamp(signal_start).normalize()
    end = pd.Timestamp(signal_end).normalize()
    first_signal_index = _V009._required_history_sessions(spec)

    for index, (session, bar) in enumerate(frame.iterrows()):
        if position is not None and time_exit_index == index:
            raw_exit = float(bar["Open"])
            executed_exit = _V009._exit_fill(raw_exit, cost)
            shares = int(position["shares"])
            exit_fee = shares * executed_exit * cost.fee_bps / 10_000.0
            cash += shares * executed_exit - exit_fee
            trades.append(
                _close_trade(
                    position,
                    session,
                    raw_exit,
                    executed_exit,
                    exit_fee,
                    "time",
                    spec.holding_sessions,
                )
            )
            position = None
            time_exit_index = None
            last_exit_index = index

        if pending_signal_index is not None and pending_signal_index + 1 == index:
            raw_entry = float(bar["Open"])
            executed_entry = _V009._entry_fill(raw_entry, cost)
            pre_entry_equity = cash
            shares = _V009.risk_budget_shares(
                cash,
                raw_entry,
                stop_return=spec.stop_return,
                risk_fraction=spec.risk_fraction,
                cost=cost,
            )
            if shares > 0:
                entry_fee = shares * executed_entry * cost.fee_bps / 10_000.0
                cash -= shares * executed_entry + entry_fee
                position = {
                    "signal_session": frame.index[pending_signal_index],
                    "entry_session": session,
                    "raw_entry": raw_entry,
                    "executed_entry": executed_entry,
                    "entry_fee": entry_fee,
                    "cash_before_entry": pre_entry_equity,
                    "pre_entry_equity": pre_entry_equity,
                    "shares": shares,
                    "target": raw_entry * (1.0 + spec.target_return),
                    "stop": raw_entry * (1.0 + spec.stop_return),
                    "held_sessions": 0,
                    "strategy_component": pending_component,
                    "trigger_components": pending_triggers,
                }
                time_exit_index = index + spec.holding_sessions
            pending_signal_index = None
            pending_component = None
            pending_triggers = ()

        if position is not None:
            exit_match = _V009._intraday_exit(
                bar, float(position["target"]), float(position["stop"])
            )
            if exit_match is not None:
                raw_exit, exit_reason = exit_match
                executed_exit = _V009._exit_fill(raw_exit, cost)
                shares = int(position["shares"])
                exit_fee = shares * executed_exit * cost.fee_bps / 10_000.0
                cash += shares * executed_exit - exit_fee
                held_sessions = int(position["held_sessions"]) + 1
                trades.append(
                    _close_trade(
                        position,
                        session,
                        raw_exit,
                        executed_exit,
                        exit_fee,
                        exit_reason,
                        held_sessions,
                    )
                )
                position = None
                time_exit_index = None
                last_exit_index = index
            else:
                position["held_sessions"] = int(position["held_sessions"]) + 1

        enough_time_to_exit = index + spec.holding_sessions + 1 < len(frame)
        lifecycle_within_end = (
            index + spec.holding_sessions + 1 >= len(frame)
            or frame.index[index + spec.holding_sessions + 1] <= end
        )
        cooldown_ready = last_exit_index is None or index - last_exit_index >= spec.cooldown_sessions
        date_is_eligible = start <= session <= end
        if (
            index >= first_signal_index
            and date_is_eligible
            and enough_time_to_exit
            and lifecycle_within_end
            and position is None
            and pending_signal_index is None
            and cooldown_ready
        ):
            triggers: list[Component] = []
            if bool(frame.iloc[index]["v009_signal"]):
                triggers.append("v009")
            if bool(frame.iloc[index]["relative_lag_signal"]):
                triggers.append("industry-relative-lag")
            if triggers:
                pending_signal_index = index
                pending_component = "v009" if "v009" in triggers else "industry-relative-lag"
                pending_triggers = tuple(triggers)

    return tuple(trades)


def baseline_trades(
    tsm_bars: pd.DataFrame,
    *,
    cost: CostModel,
    signal_start: str | pd.Timestamp,
    signal_end: str | pd.Timestamp,
) -> tuple[_V009.Trade, ...]:
    """固定比較組：原 v009 candidate，包含其完整訊號與執行規則。"""

    return _V009.backtest(
        tsm_bars,
        spec=_V009.DEFAULT_SPEC,
        cost=cost,
        signal_start=signal_start,
        signal_end=signal_end,
    ).trades


def _close_trade(
    position: dict[str, object],
    exit_session: pd.Timestamp,
    raw_exit: float,
    executed_exit: float,
    exit_fee: float,
    exit_reason: str,
    held_sessions: int,
) -> CombinedTrade:
    shares = int(position["shares"])
    total_fees = float(position["entry_fee"]) + exit_fee
    pnl = shares * (executed_exit - float(position["executed_entry"])) - total_fees
    component = position["strategy_component"]
    if component not in {"v009", "industry-relative-lag"}:
        raise ValueError("成交缺少有效的 strategy_component")
    triggers = tuple(position["trigger_components"])
    return CombinedTrade(
        signal_session=position["signal_session"],
        entry_session=position["entry_session"],
        exit_session=exit_session,
        raw_entry_price=float(position["raw_entry"]),
        raw_exit_price=raw_exit,
        executed_entry_price=float(position["executed_entry"]),
        executed_exit_price=executed_exit,
        shares=shares,
        fees=total_fees,
        pnl=pnl,
        exit_reason=exit_reason,
        held_sessions=held_sessions,
        strategy_component=component,
        trigger_components=triggers,
        pre_entry_equity=float(position["pre_entry_equity"]),
    )


def serialize_trade_pair(
    base_trades: tuple[object, ...], stress_trades: tuple[object, ...], *, candidate: bool
) -> list[dict[str, object]]:
    """把兩套成本輸出配對成 v005 raw Development trade rows。"""

    def signature(trade: object) -> tuple[str, str, str, str, str, int]:
        component = getattr(trade, "strategy_component", "v009")
        return (
            trade.signal_session.strftime("%Y-%m-%d"),
            trade.entry_session.strftime("%Y-%m-%d"),
            trade.exit_session.strftime("%Y-%m-%d"),
            str(trade.exit_reason),
            str(component),
            int(trade.held_sessions),
        )

    if [signature(item) for item in base_trades] != [signature(item) for item in stress_trades]:
        raise ValueError("base/stress 成本改變了成交訊號或持有區間，不能配對")

    rows: list[dict[str, object]] = []
    base_equity = float(DEFAULT_SPEC.initial_cash)
    stress_equity = float(DEFAULT_SPEC.initial_cash)
    for base, stress in zip(base_trades, stress_trades, strict=True):
        base_pnl = float(base.pnl)
        stress_pnl = float(stress.pnl)
        base_component = getattr(base, "strategy_component", "v009")
        stress_component = getattr(stress, "strategy_component", "v009")
        if base_component != stress_component:
            raise ValueError("base/stress 的策略來源不一致")
        component = str(base_component)
        signal_session = base.signal_session
        if isinstance(base, CombinedTrade):
            triggers = list(base.trigger_components)
        else:
            triggers = ["v009"]
        trade_id = f"{component}:{signal_session:%Y-%m-%d}"

        def detail(trade: object, equity: float) -> dict[str, object]:
            pnl = float(trade.pnl)
            return {
                "executed_entry_price": str(float(trade.executed_entry_price)),
                "executed_exit_price": str(float(trade.executed_exit_price)),
                "fees": str(float(trade.fees)),
                "pnl": str(pnl),
                "pnl_fraction_of_pre_entry_equity": str(pnl / equity),
                "shares": int(trade.shares),
            }

        record: dict[str, object] = {
            "trade_id": trade_id,
            "signal_session": signal_session.strftime("%Y-%m-%d"),
            "entry_session": base.entry_session.strftime("%Y-%m-%d"),
            "exit_session": base.exit_session.strftime("%Y-%m-%d"),
            "exit_reason": str(base.exit_reason),
            "held_sessions": int(base.held_sessions),
            "base": detail(base, base_equity),
            "stress": detail(stress, stress_equity),
        }
        if candidate:
            record["strategy_component"] = component
            record["trigger_components"] = triggers
        else:
            record["strategy_component"] = "v009"
            record["trigger_components"] = ["v009"]
        rows.append(record)
        base_equity += base_pnl
        stress_equity += stress_pnl
    return rows


__all__ = [
    "BASE_COST",
    "BASELINE_SPEC",
    "DEFAULT_SPEC",
    "STRESS_COST",
    "StrategySpec",
    "CostModel",
    "backtest",
    "baseline_trades",
    "combined_backtest",
    "dual_asset_signals",
    "indicators",
    "_intraday_exit",
    "serialize_trade_pair",
]
