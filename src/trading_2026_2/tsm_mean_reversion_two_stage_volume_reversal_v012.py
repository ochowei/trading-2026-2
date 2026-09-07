"""TSM v012：保留 v009 超跌資格，新增當日盤中反轉確認。

本模組沿用 v009 的均線、RSI、成交量領先、成本、部位大小、停損、停利、持有期
與冷卻語意；唯一策略變更是訊號日確認改為：v009 原有的收盤高於前收，或在
收盤不高於前收時，收盤高於開盤、日內高低價有效，且收盤位於日內區間上方三分之一。
所有條件只使用訊號日收盤時已完成的 OHLCV 資料，下一個交易日開盤進場。
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from trading_2026_2 import tsm_mean_reversion_two_stage_volume_reversal_v009 as _v009

ExitReason = Literal[
    "target-gap",
    "target",
    "stop-gap",
    "stop",
    "stop-same-session",
    "time",
]

CostModel = _v009.CostModel
StrategySpec = _v009.StrategySpec
Trade = _v009.Trade
BacktestResult = _v009.BacktestResult
BASE_COST = _v009.BASE_COST
STRESS_COST = _v009.STRESS_COST
DEFAULT_SPEC = _v009.DEFAULT_SPEC
BASELINE_SPEC = _v009.BASELINE_SPEC
PRICE_ONLY_SPEC = _v009.PRICE_ONLY_SPEC
VOLUME_ONLY_SPEC = _v009.VOLUME_ONLY_SPEC

validate_bars = _v009.validate_bars
risk_budget_shares = _v009.risk_budget_shares
_entry_fill = _v009._entry_fill
_exit_fill = _v009._exit_fill
_intraday_exit = _v009._intraday_exit
mark_to_market_drawdown = _v009.mark_to_market_drawdown
qualification_metrics = _v009.qualification_metrics


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """計算 v009 資格與固定的兩種當日確認方式。"""

    # 先關閉 v009 的方向閘門，只留下完全相同的超跌、RSI 與 prior-only
    # volume lead 資格；之後再把兩種事前固定的確認方式合併。
    qualification_spec = spec.with_changes(require_close_above_prior_close=False)
    result = _v009.indicators(bars, qualification_spec)
    intraday_range = result["High"] - result["Low"]
    close_location = (result["Close"] - result["Low"]) / intraday_range
    intraday_reversal = (
        (result["Close"] <= result["prior_close"])
        & (result["Close"] > result["Open"])
        & (result["High"] > result["Low"])
        & (close_location >= (2.0 / 3.0))
    )
    result["intraday_reversal_confirmation"] = intraday_reversal
    result["same_day_v009_confirmation"] = result["close_above_prior_close"]
    result["raw_signal"] = result["raw_signal"] & (
        result["close_above_prior_close"] | result["intraday_reversal_confirmation"]
    )
    return result


def _required_history_sessions(spec: StrategySpec) -> int:
    """回傳訊號用到的最早完整指標列的 zero-based index。"""

    return max(
        spec.sma_min_periods - 1,
        spec.rsi_min_periods,
        spec.volume_average_min_periods + spec.volume_lead_min_periods,
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
    """以 v009 完整交易生命週期執行 v012 固定訊號。"""

    if spec.cooldown_sessions < 0 or spec.holding_sessions <= 0:
        raise ValueError("cooldown 與持有期設定不合法")
    frame = indicators(bars, spec)
    cash = float(spec.initial_cash)
    trades: list[Trade] = []
    accepted: list[pd.Timestamp] = []
    pending_signal_index: int | None = None
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
                }
                time_exit_index = index + spec.holding_sessions
            pending_signal_index = None

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
            and bool(bar["raw_signal"])
        ):
            accepted.append(session)
            pending_signal_index = index

    return BacktestResult(tuple(trades), tuple(accepted), cash)


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
