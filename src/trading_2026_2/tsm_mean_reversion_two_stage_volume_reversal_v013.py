"""TSM v013：退場後放量事件可有條件提前結束冷卻期。

本模組沿用 v009 的指標、成本、部位風險、停損停利與持有期。唯一新增的
行為是：持倉退場後，從下一個完整交易日的收盤開始辨識新的放量事件；事件
後第 1 至第 3 個交易日若通過原有超跌、RSI 與收盤方向條件，下一個交易日
開盤進場。事件日不作確認日，事件只在冷卻期尚未結束時有效。

日線資料只在每個 session 收盤完成後觀察。事件使用 v009 相同的
``Volume / prior 20-session average``，而平均值只使用當日前的成交量，因而
不會讀取未來資料。每個冷卻期只保留第一個事件；重疊事件不重設期限、不排隊。
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import pandas as pd

from trading_2026_2 import tsm_mean_reversion_two_stage_volume_reversal_v009 as _v009

CostModel = _v009.CostModel
Trade = _v009.Trade
ExitReason = _v009.ExitReason
BASE_COST = _v009.BASE_COST
STRESS_COST = _v009.STRESS_COST
_intraday_exit = _v009._intraday_exit
_rsi = _v009._rsi


@dataclass(frozen=True)
class StrategySpec(_v009.StrategySpec):
    """v009 規格加上預先登記的提前冷卻期規則。"""

    early_cooldown_enabled: bool = True
    early_cooldown_window_sessions: int = 3
    early_volume_ratio_minimum: float = 1.05

    def with_changes(self, **changes: object) -> StrategySpec:
        return replace(self, **changes)


DEFAULT_SPEC = StrategySpec()
BASELINE_SPEC = DEFAULT_SPEC.with_changes(
    volume_lead_enabled=False,
    require_close_above_prior_close=False,
    early_cooldown_enabled=False,
)
PRICE_ONLY_SPEC = DEFAULT_SPEC.with_changes(volume_lead_enabled=False)
VOLUME_ONLY_SPEC = DEFAULT_SPEC.with_changes(require_close_above_prior_close=False)


@dataclass(frozen=True)
class BacktestResult:
    """回測結果；新增兩個欄位保存進場來源與觸發事件。"""

    trades: tuple[Trade, ...]
    accepted_signal_sessions: tuple[pd.Timestamp, ...]
    ending_cash: float
    entry_modes: tuple[str, ...] = ()
    volume_event_sessions: tuple[pd.Timestamp | None, ...] = ()


def validate_bars(bars: pd.DataFrame) -> pd.DataFrame:
    return _v009.validate_bars(bars)


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """沿用 v009 指標，另外標記當日放量與價格確認條件。"""

    result = _v009.indicators(bars, spec).copy()
    result["early_volume_event"] = (
        result["volume_spike_ratio"] >= spec.early_volume_ratio_minimum
    )
    result["early_price_confirmation"] = (
        (result["mean_reversion_gap"] >= spec.mean_reversion_min)
        & (result["rsi_2"] <= spec.rsi_max)
        & result["close_above_prior_close"]
    )
    return result


def risk_budget_shares(*args: object, **kwargs: object) -> int:
    return _v009.risk_budget_shares(*args, **kwargs)


def backtest(
    bars: pd.DataFrame,
    *,
    spec: StrategySpec = DEFAULT_SPEC,
    cost: CostModel = BASE_COST,
    reset_at_start: bool = False,
    signal_start: str | pd.Timestamp | None = None,
    signal_end: str | pd.Timestamp | None = None,
) -> BacktestResult:
    """以固定 v009 執行規則加入單一提前事件狀態機。"""

    if spec.cooldown_sessions < 0 or spec.holding_sessions <= 0:
        raise ValueError("cooldown 與持有期設定不合法")
    if spec.early_cooldown_window_sessions < 1:
        raise ValueError("提前冷卻事件有效期必須至少為 1 個交易日")

    frame = indicators(bars, spec)
    cash = float(spec.initial_cash)
    trades: list[Trade] = []
    accepted: list[pd.Timestamp] = []
    entry_modes: list[str] = []
    volume_event_sessions: list[pd.Timestamp | None] = []
    pending_signal_index: int | None = None
    pending_signal_mode: str | None = None
    pending_event_index: int | None = None
    last_exit_index: int | None = None
    active_event_index: int | None = None
    position: dict[str, object] | None = None
    time_exit_index: int | None = None
    first_signal_index = (
        spec.fold_warmup_sessions
        if reset_at_start
        else _v009._required_history_sessions(spec)
    )
    start = pd.Timestamp(signal_start).normalize() if signal_start is not None else None
    end = pd.Timestamp(signal_end).normalize() if signal_end is not None else None
    if start is not None and end is not None and start > end:
        raise ValueError("signal_start 不得晚於 signal_end")

    for index, (session, bar) in enumerate(frame.iterrows()):
        if position is not None and time_exit_index == index:
            raw_exit = float(bar["Open"])
            executed_exit = _v009._exit_fill(raw_exit, cost)
            shares = int(position["shares"])
            exit_fee = shares * executed_exit * cost.fee_bps / 10_000.0
            cash += shares * executed_exit - exit_fee
            total_fees = float(position["entry_fee"]) + exit_fee
            pnl = cash - float(position["cash_before_entry"])
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
                )
            )
            position = None
            time_exit_index = None
            last_exit_index = index
            active_event_index = None

        if pending_signal_index is not None and pending_signal_index + 1 == index:
            raw_entry = float(bar["Open"])
            executed_entry = _v009._entry_fill(raw_entry, cost)
            cash_before_entry = cash
            shares = _v009.risk_budget_shares(
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
                }
                time_exit_index = index + spec.holding_sessions
                entry_modes.append(pending_signal_mode or "normal-v009")
                volume_event_sessions.append(
                    None
                    if pending_event_index is None
                    else frame.index[pending_event_index]
                )
            pending_signal_index = None
            pending_signal_mode = None
            pending_event_index = None

        if position is not None:
            exit_match = _v009._intraday_exit(
                bar, float(position["target"]), float(position["stop"])
            )
            if exit_match is not None:
                raw_exit, exit_reason = exit_match
                executed_exit = _v009._exit_fill(raw_exit, cost)
                shares = int(position["shares"])
                exit_fee = shares * executed_exit * cost.fee_bps / 10_000.0
                cash += shares * executed_exit - exit_fee
                total_fees = float(position["entry_fee"]) + exit_fee
                pnl = cash - float(position["cash_before_entry"])
                held_sessions = int(position["held_sessions"]) + 1
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
                    )
                )
                position = None
                time_exit_index = None
                last_exit_index = index
                active_event_index = None
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
            active_event_index is not None
            and index > active_event_index + spec.early_cooldown_window_sessions
        ):
            active_event_index = None

        can_decide = (
            index >= first_signal_index
            and date_is_eligible
            and enough_time_to_exit
            and lifecycle_within_end
            and position is None
            and pending_signal_index is None
        )
        if not can_decide:
            continue

        # 第一筆交易沒有退場事件，沿用 v009 的正常訊號；提前事件只會在
        # 至少有一筆已完成交易之後出現。
        if last_exit_index is None:
            if bool(bar["raw_signal"]):
                accepted.append(session)
                pending_signal_index = index
                pending_signal_mode = "normal-v009"
            continue

        # 冷卻期第五個交易日以 v009 正常訊號為唯一決策來源；等待事件先清除，
        # 並且該日新放量也不得再建立提前事件。
        if cooldown_ready:
            active_event_index = None
            if bool(bar["raw_signal"]):
                accepted.append(session)
                pending_signal_index = index
                pending_signal_mode = "normal-v009"
            continue

        if not spec.early_cooldown_enabled:
            continue

        # 已有事件時，只檢查它的第 1 至第 3 個交易日；同日的新放量不會
        # 改變 active_event_index。事件日 index 本身也不會進入確認分支。
        if active_event_index is not None:
            event_age = index - active_event_index
            if 1 <= event_age <= spec.early_cooldown_window_sessions and bool(
                bar["early_price_confirmation"]
            ):
                accepted.append(session)
                pending_signal_index = index
                pending_signal_mode = "early-cooldown-reset"
                pending_event_index = active_event_index
                active_event_index = None
            continue

        # 事件只能在退場後的完整日線收盤辨識；因此 index > last_exit_index
        # 明確排除退場日，也不會沿用退場前的量能事件。
        if index > last_exit_index and bool(bar["early_volume_event"]):
            active_event_index = index

    return BacktestResult(
        tuple(trades),
        tuple(accepted),
        cash,
        tuple(entry_modes),
        tuple(volume_event_sessions),
    )


def qualification_metrics(
    result: BacktestResult, *, initial_cash: float = 100_000.0
) -> dict[str, float | int]:
    return _v009.qualification_metrics(result, initial_cash=initial_cash)


def mark_to_market_drawdown(
    bars: pd.DataFrame,
    result: BacktestResult,
    *,
    cost: CostModel = BASE_COST,
    initial_cash: float = 100_000.0,
) -> float:
    return _v009.mark_to_market_drawdown(
        bars, result, cost=cost, initial_cash=initial_cash
    )


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
    "mark_to_market_drawdown",
    "qualification_metrics",
    "risk_budget_shares",
    "validate_bars",
]
