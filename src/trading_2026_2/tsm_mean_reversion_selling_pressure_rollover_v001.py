"""TSM selling-pressure rollover 均值回歸研究的可重算核心。

本模組只接受已凍結的日線 OHLCV，不下載資料、不連線券商，也不建立真實委託。
Path A 原封不動保留 v009 的 base oversold、訊號日前 5 個 session 的 prior-volume
lead 與 Close > prior Close 條件。Path B 只新增一條補充進場：base oversold 且
3-session Signed Volume Balance 從前 5 個已完成 session 的極負值回升到不低於
-0.15；Path B 不要求訊號日 Close 高於前一日，訊號在收盤判定、下一個 session
open 進場。Signed Volume Balance 的上漲、下跌、平盤方向分別記為 +1、-1、0，
零成交量分母與指標尚未就緒時保留為 NaN。

兩條路徑同一訊號日只保留一筆交易，並共用既有 v009 的成本、部位風險、停損、
停利、持有期、冷卻期與成交順序假設。正式 Historical Evaluation 由獨立 runner
執行；本模組本身不連線外部資料服務。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from math import floor, inf
from typing import Literal

import numpy as np
import pandas as pd

ExitReason = Literal[
    "target-gap",
    "target",
    "stop-gap",
    "stop",
    "stop-same-session",
    "time",
]


@dataclass(frozen=True)
class CostModel:
    """單邊滑價與費用，以 basis point（萬分之一）表示。"""

    slippage_bps: float
    fee_bps: float


@dataclass(frozen=True)
class StrategySpec:
    """預先登記的 TSM 候選與 baseline 共用參數。"""

    sma_lookback: int = 20
    sma_min_periods: int = 20
    mean_reversion_min: float = 0.015
    rsi_lookback: int = 2
    rsi_min_periods: int = 2
    rsi_max: float = 50.0
    volume_lookback: int = 20
    volume_average_min_periods: int = 20
    volume_lead_window: int = 5
    volume_lead_min_periods: int = 5
    volume_spike_ratio: float = 1.05
    volume_lead_enabled: bool = True
    require_close_above_prior_close: bool = True

    # Path B 的 Signed Volume Balance（SVB3）規格
    supplemental_path_enabled: bool = True
    supplemental_volume_lead_enabled: bool = True
    svb_lookback: int = 3
    svb_min_periods: int = 3
    svb_prior_window: int = 5
    svb_prior_min_periods: int = 5
    svb_prior_minimum: float = -0.50
    svb_current_minimum: float = -0.15
    cooldown_sessions: int = 5
    target_return: float = 0.04
    stop_return: float = -0.04
    holding_sessions: int = 10
    fold_warmup_sessions: int = 25
    initial_cash: float = 100_000.0
    risk_fraction: float = 0.02

    def with_changes(self, **changes: object) -> StrategySpec:
        """建立明示的 baseline 或 challenge 變體，不修改 frozen candidate。"""

        return replace(self, **changes)


BASE_COST = CostModel(slippage_bps=5.0, fee_bps=1.0)
STRESS_COST = CostModel(slippage_bps=20.0, fee_bps=2.0)
DEFAULT_SPEC = StrategySpec()

# 共同 base oversold 的簡化 baseline，不加入任何路徑專屬確認。
BASELINE_SPEC = DEFAULT_SPEC.with_changes(
    volume_lead_enabled=False,
    require_close_above_prior_close=False,
    supplemental_path_enabled=False,
)

# 只保留既有 v009 Path A，用於證明新增 Path B 的增量。
V009_ONLY_SPEC = DEFAULT_SPEC.with_changes(
    supplemental_path_enabled=False,
)

# 消融用變體：保留 Path A，移除 Path B 的 SVB 條件。
WITHOUT_VOLUME_LEAD_SPEC = DEFAULT_SPEC.with_changes(
    supplemental_volume_lead_enabled=False,
)

# 供既有挑戰與 runner 相容的兩個簡化變體。
PRICE_ONLY_SPEC = DEFAULT_SPEC.with_changes(volume_lead_enabled=False)
VOLUME_ONLY_SPEC = DEFAULT_SPEC.with_changes(require_close_above_prior_close=False)


def _decimal_text(value: int | float) -> str:
    return format(Decimal(str(value)).normalize(), "f")


def signal_definition(spec: StrategySpec = DEFAULT_SPEC) -> dict[str, object]:
    """回傳 candidate-definition.signal 的單一來源。"""

    return {
        "accepted_only_when_flat": True,
        "cooldown": {
            "clock_anchor": "completed-position-exit",
            "completed_session_steps_after_exit": spec.cooldown_sessions,
        },
        "decision_time": "completed-session-close",
        "final_signal": "path-a-or-path-b-one-trade-per-signal-session",
        "mean_reversion": {
            "close_vs_sma20_gap_minimum": _decimal_text(spec.mean_reversion_min),
            "rsi_length": spec.rsi_lookback,
            "rsi_maximum": _decimal_text(spec.rsi_max),
            "sma_length": spec.sma_lookback,
        },
        "path_a": {
            "source_engine_path": "src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py",
            "source_semantics": (
                "base-oversold-and-prior-volume-lead-and-close-above-prior-close"
            ),
            "source_strategy": "tsm-mean-reversion-two-stage-volume-reversal--v009",
        },
        "path_b": {
            "base_oversold": {
                "close_multiplier_of_sma20": _decimal_text(1.0 - spec.mean_reversion_min),
                "close_operator": "<=",
                "rsi_length": spec.rsi_lookback,
                "rsi_operator": "<=",
                "rsi_value": _decimal_text(spec.rsi_max),
            },
            "name": "selling-pressure-rollover",
            "price_direction_confirmation": "not-required",
            "svb3": {
                "current_minimum": _decimal_text(spec.svb_current_minimum),
                "current_operator": ">=",
                "formula": (
                    "sum(sign(close_i_minus_prior_close_i) * volume_i, i=t-2..t) "
                    "/ sum(volume_i, i=t-2..t)"
                ),
                "prior_minimum": "-0.50",
                "prior_minimum_operator": "<=",
                "prior_window_end": "t-1",
                "prior_window_start": "t-5",
            },
        },
        "price_direction_confirmation": {
            "applies_to": "path-a-only",
            "close_above_prior_close": spec.require_close_above_prior_close,
        },
        "symbol": "TSM",
        "volume_leads_price": {
            "enabled": spec.volume_lead_enabled,
            "prior_session_window": spec.volume_lead_window,
            "volume_average_length": spec.volume_lookback,
            "volume_ratio_minimum": _decimal_text(spec.volume_spike_ratio),
        },
    }


@dataclass(frozen=True)
class Trade:
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
    exit_reason: ExitReason
    held_sessions: int
    signal_origin: str = "path_a"


@dataclass(frozen=True)
class BacktestResult:
    trades: tuple[Trade, ...]
    accepted_signal_sessions: tuple[pd.Timestamp, ...]
    ending_cash: float
    trade_origins: tuple[str, ...] = ()


def validate_bars(bars: pd.DataFrame) -> pd.DataFrame:
    """驗證並正規化已調整 OHLCV；不允許缺值、重複或錯序 session。"""

    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [column for column in required if column not in bars.columns]
    if missing:
        raise ValueError(f"缺少必要欄位: {', '.join(missing)}")
    result = bars.loc[:, required].copy()
    if not isinstance(result.index, pd.DatetimeIndex):
        raise ValueError("資料 index 必須是 DatetimeIndex")
    if result.index.tz is not None:
        result.index = result.index.tz_localize(None)
    result.index = result.index.normalize()
    if result.index.has_duplicates:
        raise ValueError("session 日期不得重複")
    if not result.index.is_monotonic_increasing:
        raise ValueError("session 日期必須嚴格遞增")
    result = result.astype(float)
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError("OHLCV 不得包含缺值或無限值")
    if (result[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise ValueError("OHLC 價格必須大於 0")
    if (result["Volume"] < 0).any():
        raise ValueError("Volume 不得小於 0")
    if (
        (result["High"] < result[["Open", "Close", "Low"]].max(axis=1)).any()
        or (result["Low"] > result[["Open", "Close", "High"]].min(axis=1)).any()
    ):
        raise ValueError("OHLC 高低價關係不合法")
    return result


def _rsi(
    close: pd.Series,
    length: int,
    min_periods: int | None = None,
) -> pd.Series:
    """以簡單 rolling mean 計算 RSI，未就緒時保留 NaN。"""

    if length <= 0:
        raise ValueError("RSI 長度必須大於 0")
    minimum = length if min_periods is None else min_periods
    if not 1 <= minimum <= length:
        raise ValueError("RSI min_periods 必須介於 1 與 length 之間")
    change = close.diff()
    gain = change.clip(lower=0).rolling(length, min_periods=minimum).mean()
    loss = (-change.clip(upper=0)).rolling(length, min_periods=minimum).mean()
    with np.errstate(divide="ignore", invalid="ignore"):
        result = 100.0 - 100.0 / (1.0 + gain / loss)
    ready = gain.notna() & loss.notna()
    result = result.where(ready, np.nan)
    result = result.mask(ready & (gain == 0) & (loss == 0), 50.0)
    result = result.mask(ready & (loss == 0) & (gain > 0), 100.0)
    result = result.mask(ready & (gain == 0) & (loss > 0), 0.0)
    return result


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """計算 Path A、Path B 與必要診斷欄位；只使用訊號日及更早 session。"""

    clean = validate_bars(bars)
    close = clean["Close"]
    volume = clean["Volume"]

    sma = close.rolling(
        spec.sma_lookback, min_periods=spec.sma_min_periods
    ).mean()
    mean_reversion_gap = (sma - close) / sma
    rsi = _rsi(close, spec.rsi_lookback, spec.rsi_min_periods)

    # Path A 完全沿用 v009：量能比值的均量只看訊號日前 20 個 session。
    prior_volume_average = volume.shift(1).rolling(
        spec.volume_lookback, min_periods=spec.volume_average_min_periods
    ).mean()
    volume_spike_ratio = volume / prior_volume_average
    prior_volume_spike = volume_spike_ratio.shift(1).rolling(
        spec.volume_lead_window, min_periods=spec.volume_lead_min_periods
    ).max()
    prior_close = close.shift(1)
    close_above_prior_close = close > prior_close

    base_oversold = (
        (mean_reversion_gap >= spec.mean_reversion_min)
        & (rsi <= spec.rsi_max)
    )
    path_a_signal = base_oversold.copy()
    if spec.volume_lead_enabled:
        path_a_signal &= prior_volume_spike >= spec.volume_spike_ratio
    if spec.require_close_above_prior_close:
        path_a_signal &= close_above_prior_close

    # Path B：平盤方向為 0；三日零成交量分母保留 NaN，不能誤當成 rollover。
    direction = np.sign(close.diff()).fillna(0.0)
    svb_numerator = (
        (direction * volume)
        .rolling(spec.svb_lookback, min_periods=spec.svb_min_periods)
        .sum()
    )
    svb_denominator = volume.rolling(
        spec.svb_lookback, min_periods=spec.svb_min_periods
    ).sum()
    svb3 = svb_numerator.div(svb_denominator).where(svb_denominator != 0)
    prior_svb3_minimum = (
        svb3.shift(1)
        .rolling(spec.svb_prior_window, min_periods=spec.svb_prior_min_periods)
        .min()
    )
    if spec.supplemental_path_enabled:
        if spec.supplemental_volume_lead_enabled:
            path_b_svb_condition = (
                (prior_svb3_minimum <= spec.svb_prior_minimum)
                & (svb3 >= spec.svb_current_minimum)
            )
        else:
            # 僅供 Development mechanism ablation；候選永遠使用上面的 SVB 條件。
            path_b_svb_condition = pd.Series(True, index=clean.index)
        path_b_signal = base_oversold & path_b_svb_condition
    else:
        path_b_signal = pd.Series(False, index=clean.index)

    result = clean.copy()
    result["sma_20"] = sma
    result["mean_reversion_gap"] = mean_reversion_gap
    result["rsi_2"] = rsi
    result["volume_spike_ratio"] = volume_spike_ratio
    result["prior_volume_spike_ratio"] = prior_volume_spike
    result["prior_close"] = prior_close
    result["close_above_prior_close"] = close_above_prior_close
    result["base_oversold"] = base_oversold
    result["svb3_numerator"] = svb_numerator
    result["svb3_denominator"] = svb_denominator
    result["svb3"] = svb3
    result["prior_svb3_min_5"] = prior_svb3_minimum
    result["path_a_raw_signal"] = path_a_signal
    result["path_b_raw_signal"] = path_b_signal
    result["raw_signal"] = path_a_signal | path_b_signal
    return result


def _entry_fill(raw_open: float, cost: CostModel) -> float:
    return raw_open * (1.0 + cost.slippage_bps / 10_000.0)


def _exit_fill(raw_price: float, cost: CostModel) -> float:
    return raw_price * (1.0 - cost.slippage_bps / 10_000.0)


def risk_budget_shares(
    cash: float,
    raw_entry: float,
    *,
    stop_return: float,
    risk_fraction: float,
    cost: CostModel,
) -> int:
    """回傳同時符合現金上限與成本內含 stop 風險預算的最大整數股數。"""

    if cash < 0:
        raise ValueError("可用現金不得小於 0")
    if raw_entry <= 0:
        raise ValueError("原始進場價必須大於 0")
    if not 0 < risk_fraction <= 1:
        raise ValueError("risk_fraction 必須大於 0 且不超過 1")
    if not -1 < stop_return < 0:
        raise ValueError("stop_return 必須介於 -1 與 0 之間")

    executed_entry = _entry_fill(raw_entry, cost)
    raw_stop = raw_entry * (1.0 + stop_return)
    executed_stop = _exit_fill(raw_stop, cost)
    entry_cash_per_share = executed_entry * (1.0 + cost.fee_bps / 10_000.0)
    stop_proceeds_per_share = executed_stop * (1.0 - cost.fee_bps / 10_000.0)
    modeled_loss_per_share = entry_cash_per_share - stop_proceeds_per_share
    if modeled_loss_per_share <= 0:
        raise ValueError("成本內含的 stop 每股損失必須大於 0")

    affordable = floor(cash / entry_cash_per_share)
    risk_limited = floor((cash * risk_fraction) / modeled_loss_per_share)
    return max(0, min(affordable, risk_limited))


def _intraday_exit(
    bar: pd.Series, target: float, stop: float
) -> tuple[float, ExitReason] | None:
    """依 gap 優先、同 session 悲觀 stop 優先決定 raw fill。"""

    if bar["Open"] <= stop:
        return float(bar["Open"]), "stop-gap"
    if bar["Open"] >= target:
        return float(bar["Open"]), "target-gap"
    stop_hit = bar["Low"] <= stop
    target_hit = bar["High"] >= target
    if stop_hit and target_hit:
        return stop, "stop-same-session"
    if stop_hit:
        return stop, "stop"
    if target_hit:
        return target, "target"
    return None


def _required_history_sessions(spec: StrategySpec) -> int:
    """回傳訊號用到的最早完整指標列的 zero-based index。"""

    return max(
        spec.sma_min_periods - 1,
        spec.rsi_min_periods,
        spec.volume_average_min_periods + spec.volume_lead_min_periods,
        spec.svb_min_periods + spec.svb_prior_window,
    )


def backtest(
    bars: pd.DataFrame,
    *,
    spec: StrategySpec = DEFAULT_SPEC,
    cost: CostModel = BASE_COST,
    reset_at_start: bool = False,
    signal_start: str | pd.Timestamp | None = None,
    signal_end: str | pd.Timestamp | None = None,
) -> BacktestResult:
    """執行不可重疊、次日 open 進場的整合 Path A / Path B 回測。"""

    if spec.cooldown_sessions < 0 or spec.holding_sessions <= 0:
        raise ValueError("cooldown 與持有期設定不合法")
    frame = indicators(bars, spec)
    cash = float(spec.initial_cash)
    trades: list[Trade] = []
    accepted: list[pd.Timestamp] = []
    trade_origins: list[str] = []
    pending_signal_index: int | None = None
    pending_signal_origin: str | None = None
    last_exit_index: int | None = None
    position: dict[str, object] | None = None
    time_exit_index: int | None = None
    first_signal_index = (
        spec.fold_warmup_sessions if reset_at_start else _required_history_sessions(spec)
    )
    start = pd.Timestamp(signal_start).normalize() if signal_start is not None else None
    end = pd.Timestamp(signal_end).normalize() if signal_end is not None else None
    if start is not None and end is not None and start > end:
        raise ValueError("signal_start 不得晚於 signal_end")

    for index, (session, bar) in enumerate(frame.iterrows()):
        if position is not None and time_exit_index == index:
            raw_exit = float(bar["Open"])
            executed_exit = _exit_fill(raw_exit, cost)
            shares = int(position["shares"])
            exit_fee = shares * executed_exit * cost.fee_bps / 10_000.0
            cash += shares * executed_exit - exit_fee
            total_fees = float(position["entry_fee"]) + exit_fee
            pnl = cash - float(position["cash_before_entry"])
            signal_origin = str(position["signal_origin"])
            trades.append(
                Trade(
                    signal_session=position["signal_session"],
                    entry_session=position["entry_session"],
                    exit_session=session,
                    raw_entry_price=float(position["raw_entry"]),
                    raw_exit_price=raw_exit,
                    executed_entry_price=float(position["executed_entry"]),
                    executed_exit_price=executed_exit,
                    shares=shares,
                    fees=total_fees,
                    pnl=pnl,
                    exit_reason="time",
                    held_sessions=spec.holding_sessions,
                    signal_origin=signal_origin,
                )
            )
            trade_origins.append(signal_origin)
            position = None
            time_exit_index = None
            last_exit_index = index

        if pending_signal_index is not None and pending_signal_index + 1 == index:
            raw_entry = float(bar["Open"])
            executed_entry = _entry_fill(raw_entry, cost)
            cash_before_entry = cash
            shares = risk_budget_shares(
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
                    "cash_before_entry": cash_before_entry,
                    "shares": shares,
                    "target": raw_entry * (1.0 + spec.target_return),
                    "stop": raw_entry * (1.0 + spec.stop_return),
                    "held_sessions": 0,
                    "signal_origin": pending_signal_origin or "path_a",
                }
                time_exit_index = index + spec.holding_sessions
            pending_signal_index = None
            pending_signal_origin = None

        if position is not None:
            exit_match = _intraday_exit(
                bar, float(position["target"]), float(position["stop"])
            )
            if exit_match is not None:
                raw_exit, exit_reason = exit_match
                executed_exit = _exit_fill(raw_exit, cost)
                shares = int(position["shares"])
                exit_fee = shares * executed_exit * cost.fee_bps / 10_000.0
                cash += shares * executed_exit - exit_fee
                total_fees = float(position["entry_fee"]) + exit_fee
                pnl = cash - float(position["cash_before_entry"])
                held_sessions = int(position["held_sessions"]) + 1
                signal_origin = str(position["signal_origin"])
                trades.append(
                    Trade(
                        signal_session=position["signal_session"],
                        entry_session=position["entry_session"],
                        exit_session=session,
                        raw_entry_price=float(position["raw_entry"]),
                        raw_exit_price=float(raw_exit),
                        executed_entry_price=float(position["executed_entry"]),
                        executed_exit_price=executed_exit,
                        shares=shares,
                        fees=total_fees,
                        pnl=pnl,
                        exit_reason=exit_reason,
                        held_sessions=held_sessions,
                        signal_origin=signal_origin,
                    )
                )
                trade_origins.append(signal_origin)
                position = None
                time_exit_index = None
                last_exit_index = index
            else:
                position["held_sessions"] = int(position["held_sessions"]) + 1

        enough_time_to_exit = index + spec.holding_sessions + 1 < len(frame)
        lifecycle_within_end = (
            end is None
            or not enough_time_to_exit
            or frame.index[index + spec.holding_sessions + 1] <= end
        )
        cooldown_ready = (
            last_exit_index is None or index - last_exit_index >= spec.cooldown_sessions
        )
        date_is_eligible = (start is None or session >= start) and (
            end is None or session <= end
        )
        if (
            index >= first_signal_index
            and date_is_eligible
            and enough_time_to_exit
            and lifecycle_within_end
            and position is None
            and pending_signal_index is None
            and cooldown_ready
        ):
            if bool(bar["path_a_raw_signal"]):
                accepted.append(session)
                pending_signal_index = index
                pending_signal_origin = "path_a"
            elif bool(bar["path_b_raw_signal"]):
                accepted.append(session)
                pending_signal_index = index
                pending_signal_origin = "path_b"

    return BacktestResult(
        tuple(trades),
        tuple(accepted),
        cash,
        trade_origins=tuple(trade_origins),
    )


def qualification_metrics(
    result: BacktestResult, *, initial_cash: float = 100_000.0
) -> dict[str, float | int]:
    """從已完成交易重算報酬、profit factor 與 realized equity drawdown。

    這裡的 ``maximum_drawdown`` 明確只看已完成交易的資金曲線；持倉內的
    OHLC 壓力另由 ``mark_to_market_drawdown`` 計算，不和正式 gate 混用。
    """

    pnls = [trade.pnl for trade in result.trades]
    gross_profit = sum(value for value in pnls if value > 0)
    gross_loss = -sum(value for value in pnls if value < 0)
    profit_factor = gross_profit / gross_loss if gross_loss else (inf if gross_profit else 0.0)
    equity = initial_cash
    peak = initial_cash
    maximum_drawdown = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        maximum_drawdown = max(maximum_drawdown, (peak - equity) / peak)
    traded_years = len({trade.signal_session.year for trade in result.trades})
    return {
        "completed_trades": len(result.trades),
        "traded_years": traded_years,
        "return": sum(pnls) / initial_cash,
        "profit_factor": profit_factor,
        "maximum_drawdown": maximum_drawdown,
    }


def mark_to_market_drawdown(
    bars: pd.DataFrame,
    result: BacktestResult,
    *,
    cost: CostModel = BASE_COST,
    initial_cash: float = 100_000.0,
) -> float:
    """以持倉中的每日 Low 做保守估值，重算持倉內資金壓力。

    正式 Development gate 使用 realized drawdown，因為 Workflow validator 只
    能從已完成交易 PnL 重算；這個診斷則在每個持倉 session 以當日 Low 估算
    可清算價，並在停損／停利成交前先記錄該日壓力。time exit 在下一個 open
    成交，因此該日不再把部位留到 Low。這個定義不會改變交易或 gate。
    """

    clean = validate_bars(bars)
    equity = float(initial_cash)
    peak = equity
    maximum_drawdown = 0.0
    trades = iter(result.trades)
    next_trade = next(trades, None)
    position: dict[str, float | int | Trade] | None = None

    for session, bar in clean.iterrows():
        if next_trade is not None and next_trade.entry_session == session:
            if position is not None:
                raise ValueError("mark-to-market 診斷遇到重疊持倉")
            entry_fee = (
                next_trade.shares
                * next_trade.executed_entry_price
                * cost.fee_bps
                / 10_000.0
            )
            position = {
                "trade": next_trade,
                "cash_after_entry": equity
                - next_trade.shares * next_trade.executed_entry_price
                - entry_fee,
                "pre_entry_equity": equity,
            }
            next_trade = next(trades, None)

        if position is not None:
            trade = position["trade"]
            assert isinstance(trade, Trade)
            is_exit_session = trade.exit_session == session
            if is_exit_session and trade.exit_reason == "time":
                equity = float(position["pre_entry_equity"]) + trade.pnl
            else:
                liquidation = _exit_fill(float(bar["Low"]), cost)
                liquidation_fee = (
                    trade.shares * liquidation * cost.fee_bps / 10_000.0
                )
                equity = (
                    float(position["cash_after_entry"])
                    + trade.shares * liquidation
                    - liquidation_fee
                )
                peak = max(peak, equity)
                maximum_drawdown = max(maximum_drawdown, (peak - equity) / peak)
                if is_exit_session:
                    equity = float(position["pre_entry_equity"]) + trade.pnl
            if is_exit_session:
                position = None

        peak = max(peak, equity)
        maximum_drawdown = max(maximum_drawdown, (peak - equity) / peak)

    if position is not None or next_trade is not None:
        raise ValueError("mark-to-market 診斷資料未涵蓋完整交易生命週期")
    return maximum_drawdown


__all__ = [
    "BASE_COST",
    "BASELINE_SPEC",
    "DEFAULT_SPEC",
    "PRICE_ONLY_SPEC",
    "STRESS_COST",
    "VOLUME_ONLY_SPEC",
    "BacktestResult",
    "CostModel",
    "StrategySpec",
    "Trade",
    "backtest",
    "indicators",
    "signal_definition",
    "mark_to_market_drawdown",
    "qualification_metrics",
    "risk_budget_shares",
    "validate_bars",
]
