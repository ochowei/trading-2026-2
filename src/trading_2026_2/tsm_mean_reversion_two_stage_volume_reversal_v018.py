"""TSM v018「連續放量卻跌不動，隨後收盤轉強」淺回落研究引擎。

本模組保留 v009 的原有進場路徑，只增加一條事前固定的補充路徑：訊號日前
兩個交易日各自放量、跌幅收斂且低點未再降低；訊號日收盤位於 SMA(20) 下方
1.0% 至未滿 1.5%，RSI(2) 不高於 50，並且收盤高於前一日。指標只使用訊號
日當下及更早資料，進場與退場沿用 v009 的單一部位執行口徑。

這裡的「放量」與「低點守住」只是待驗證條件，不代表承接已被證實。引擎不
下載資料、不連線券商，也不建立真實委託；它只接受已凍結的日線 OHLCV。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import inf
from typing import Literal

import pandas as pd

from trading_2026_2 import tsm_mean_reversion_two_stage_volume_reversal_v009 as v009

ExitReason = v009.ExitReason
CostModel = v009.CostModel


@dataclass(frozen=True)
class StrategySpec:
    """v009 原有參數與 v018 補充路徑開關。"""

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
    original_path_enabled: bool = True
    baseline_path_enabled: bool = False
    supplemental_path_enabled: bool = True
    supplemental_gap_min: float = 0.01
    supplemental_gap_max_exclusive: float = 0.015
    supplemental_rsi_max: float = 50.0
    cooldown_sessions: int = 5
    target_return: float = 0.04
    stop_return: float = -0.04
    holding_sessions: int = 10
    fold_warmup_sessions: int = 25
    initial_cash: float = 100_000.0
    risk_fraction: float = 0.02

    def with_changes(self, **changes: object) -> StrategySpec:
        """建立明示的 baseline、control 或消融變體。"""

        return replace(self, **changes)


BASE_COST = v009.BASE_COST
STRESS_COST = v009.STRESS_COST
DEFAULT_SPEC = StrategySpec()
BASELINE_SPEC = DEFAULT_SPEC.with_changes(
    volume_lead_enabled=False,
    require_close_above_prior_close=False,
    original_path_enabled=False,
    baseline_path_enabled=True,
    supplemental_path_enabled=False,
)
V009_ONLY_SPEC = DEFAULT_SPEC.with_changes(supplemental_path_enabled=False)
SUPPLEMENTAL_ONLY_SPEC = DEFAULT_SPEC.with_changes(
    volume_lead_enabled=False,
    require_close_above_prior_close=False,
    original_path_enabled=False,
)
PRICE_ONLY_SPEC = DEFAULT_SPEC.with_changes(
    volume_lead_enabled=False,
    supplemental_path_enabled=False,
    original_path_enabled=False,
)
VOLUME_ONLY_SPEC = DEFAULT_SPEC.with_changes(
    require_close_above_prior_close=False,
    supplemental_path_enabled=False,
    original_path_enabled=False,
)


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
    signal_origin: Literal["original", "supplemental"]


@dataclass(frozen=True)
class BacktestResult:
    trades: tuple[Trade, ...]
    accepted_signal_sessions: tuple[pd.Timestamp, ...]
    ending_cash: float
    supplemental_diagnostics: dict[str, object]


def validate_bars(bars: pd.DataFrame) -> pd.DataFrame:
    """沿用 v009 的 OHLCV 驗證，避免兩個 Study 使用不同資料口徑。"""

    return v009.validate_bars(bars)


def _required_history_sessions(spec: StrategySpec) -> int:
    """回傳訊號用到的最早完整指標列的 zero-based index。"""

    return max(
        spec.sma_min_periods - 1,
        spec.rsi_min_periods,
        spec.volume_average_min_periods + spec.volume_lead_min_periods,
    )


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """建立原有訊號與 v018 補充條件的逐日欄位。"""

    # v009 的實作是本 Study 原有路徑的 single source of truth。StrategySpec
    # 保留 v009 所需的全部欄位，因此這個呼叫不會改變原有指標公式。
    base = v009.indicators(bars, spec=spec)
    result = base.copy()
    daily_return = result["Close"].pct_change()
    volume_ratio_t_minus_2 = result["volume_spike_ratio"].shift(2)
    volume_ratio_t_minus_1 = result["volume_spike_ratio"].shift(1)
    return_t_minus_2 = daily_return.shift(2)
    return_t_minus_1 = daily_return.shift(1)
    low_t_minus_2 = result["Low"].shift(2)
    low_t_minus_1 = result["Low"].shift(1)

    if spec.original_path_enabled:
        result["v009_raw_signal"] = result["raw_signal"].astype(bool)
    elif spec.baseline_path_enabled:
        result["v009_raw_signal"] = result["raw_signal"].astype(bool)
    else:
        result["v009_raw_signal"] = pd.Series(False, index=result.index, dtype=bool)
    result["volume_ratio_t_minus_2"] = volume_ratio_t_minus_2
    result["volume_ratio_t_minus_1"] = volume_ratio_t_minus_1
    result["return_t_minus_2"] = return_t_minus_2
    result["return_t_minus_1"] = return_t_minus_1
    result["low_t_minus_2"] = low_t_minus_2
    result["low_t_minus_1"] = low_t_minus_1

    volume_ready = volume_ratio_t_minus_2.notna() & volume_ratio_t_minus_1.notna()
    volume_t_minus_2_pass = volume_ready & (
        volume_ratio_t_minus_2 >= spec.volume_spike_ratio
    )
    volume_t_minus_1_pass = volume_ready & (
        volume_ratio_t_minus_1 >= spec.volume_spike_ratio
    )
    volume_sequence_pass = volume_t_minus_2_pass & volume_t_minus_1_pass

    price_ready = (
        return_t_minus_2.notna()
        & return_t_minus_1.notna()
        & low_t_minus_2.notna()
        & low_t_minus_1.notna()
    )
    return_convergence_pass = price_ready & (
        return_t_minus_2 < return_t_minus_1
    )
    return_non_positive_pass = price_ready & (return_t_minus_1 <= 0)
    low_held_pass = price_ready & (low_t_minus_1 >= low_t_minus_2)
    price_sequence_pass = (
        return_convergence_pass & return_non_positive_pass & low_held_pass
    )

    shallow_ready = result["sma_20"].notna() & result["rsi_2"].notna()
    shallow_gap_pass = shallow_ready & (
        (result["mean_reversion_gap"] >= spec.supplemental_gap_min)
        & (result["mean_reversion_gap"] < spec.supplemental_gap_max_exclusive)
    )
    shallow_rsi_pass = shallow_ready & (
        result["rsi_2"] <= spec.supplemental_rsi_max
    )
    close_confirmation_pass = result["close_above_prior_close"].fillna(False).astype(bool)
    supplemental_raw_signal = (
        volume_sequence_pass
        & price_sequence_pass
        & shallow_gap_pass
        & shallow_rsi_pass
        & close_confirmation_pass
    )
    if not spec.supplemental_path_enabled:
        supplemental_raw_signal = pd.Series(False, index=result.index, dtype=bool)

    result["volume_sequence_ready"] = volume_ready
    result["volume_t_minus_2_pass"] = volume_t_minus_2_pass
    result["volume_t_minus_1_pass"] = volume_t_minus_1_pass
    result["volume_sequence_pass"] = volume_sequence_pass
    result["price_sequence_ready"] = price_ready
    result["return_convergence_pass"] = return_convergence_pass
    result["return_non_positive_pass"] = return_non_positive_pass
    result["low_held_pass"] = low_held_pass
    result["price_sequence_pass"] = price_sequence_pass
    result["shallow_ready"] = shallow_ready
    result["shallow_gap_pass"] = shallow_gap_pass
    result["shallow_rsi_pass"] = shallow_rsi_pass
    result["close_confirmation_pass"] = close_confirmation_pass
    result["supplemental_raw_signal"] = supplemental_raw_signal
    result["raw_signal"] = result["v009_raw_signal"] | supplemental_raw_signal
    return result


def _entry_fill(raw_open: float, cost: CostModel) -> float:
    return v009._entry_fill(raw_open, cost)


def _exit_fill(raw_price: float, cost: CostModel) -> float:
    return v009._exit_fill(raw_price, cost)


def risk_budget_shares(
    cash: float,
    raw_entry: float,
    *,
    stop_return: float,
    risk_fraction: float,
    cost: CostModel,
) -> int:
    return v009.risk_budget_shares(
        cash,
        raw_entry,
        stop_return=stop_return,
        risk_fraction=risk_fraction,
        cost=cost,
    )


def _intraday_exit(
    bar: pd.Series, target: float, stop: float
) -> tuple[float, ExitReason] | None:
    return v009._intraday_exit(bar, target, stop)


def _new_diagnostics() -> dict[str, object]:
    return {
        "scope": "所有達到 25-session 指標就緒邊界且在指定 signal 日期內的 session；cutoff、持倉與冷卻另行計數。",
        "condition_pass_counts": {
            "volume_t_minus_2": 0,
            "volume_t_minus_1": 0,
            "volume_sequence": 0,
            "return_t_minus_2_lt_return_t_minus_1": 0,
            "return_t_minus_1_non_positive": 0,
            "low_t_minus_1_ge_low_t_minus_2": 0,
            "price_sequence": 0,
            "shallow_gap_1pct_to_under_1_5pct": 0,
            "rsi_2_le_50": 0,
            "close_t_gt_close_t_minus_1": 0,
            "supplemental_raw_signal": 0,
        },
        "candidate_raw_signal_count": 0,
        "original_raw_signal_count": 0,
        "supplemental_raw_signal_count": 0,
        "supplemental_overlap_with_original": 0,
        "entry_possible_count": 0,
        "entry_blocked_by_position": 0,
        "entry_blocked_by_cooldown": 0,
        "entry_blocked_by_pending_signal": 0,
        "entry_blocked_by_cutoff": 0,
        "original_signals_accepted": 0,
        "supplemental_signals_accepted": 0,
        "accepted_signal_count": 0,
        "completed_trade_origin_counts": {"original": 0, "supplemental": 0},
    }


def _increment(condition_counts: dict[str, int], name: str, passed: bool) -> None:
    if passed:
        condition_counts[name] += 1


def backtest(
    bars: pd.DataFrame,
    *,
    spec: StrategySpec = DEFAULT_SPEC,
    cost: CostModel = BASE_COST,
    reset_at_start: bool = False,
    signal_start: str | pd.Timestamp | None = None,
    signal_end: str | pd.Timestamp | None = None,
) -> BacktestResult:
    """以單一 TSM sleeve 執行 v009 原路徑加 v018 補充路徑。"""

    if spec.cooldown_sessions < 0 or spec.holding_sessions <= 0:
        raise ValueError("cooldown 與持有期設定不合法")
    frame = indicators(bars, spec)
    cash = float(spec.initial_cash)
    trades: list[Trade] = []
    accepted: list[pd.Timestamp] = []
    diagnostics = _new_diagnostics()
    pending_signal_index: int | None = None
    pending_signal_origin: Literal["original", "supplemental"] | None = None
    last_exit_index: int | None = None
    position: dict[str, object] | None = None
    time_exit_index: int | None = None
    first_signal_index = (
        spec.fold_warmup_sessions
        if reset_at_start
        else _required_history_sessions(spec)
    )
    start = pd.Timestamp(signal_start).normalize() if signal_start is not None else None
    end = pd.Timestamp(signal_end).normalize() if signal_end is not None else None
    if start is not None and end is not None and start > end:
        raise ValueError("signal_start 不得晚於 signal_end")
    condition_counts = diagnostics["condition_pass_counts"]
    assert isinstance(condition_counts, dict)

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
                    signal_origin=position["signal_origin"],
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
                    "target": raw_entry * (1.0 + spec.target_return),
                    "stop": raw_entry * (1.0 + spec.stop_return),
                    "held_sessions": 0,
                    "signal_origin": pending_signal_origin or "original",
                    "shares": shares,
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
                        signal_origin=position["signal_origin"],
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
        in_diagnostic_scope = index >= first_signal_index and date_is_eligible
        if in_diagnostic_scope:
            original_raw = bool(frame.iloc[index]["v009_raw_signal"])
            supplemental_raw = bool(frame.iloc[index]["supplemental_raw_signal"])
            _increment(
                condition_counts,
                "volume_t_minus_2",
                bool(frame.iloc[index]["volume_t_minus_2_pass"]),
            )
            _increment(
                condition_counts,
                "volume_t_minus_1",
                bool(frame.iloc[index]["volume_t_minus_1_pass"]),
            )
            _increment(
                condition_counts,
                "volume_sequence",
                bool(frame.iloc[index]["volume_sequence_pass"]),
            )
            _increment(
                condition_counts,
                "return_t_minus_2_lt_return_t_minus_1",
                bool(frame.iloc[index]["return_convergence_pass"]),
            )
            _increment(
                condition_counts,
                "return_t_minus_1_non_positive",
                bool(frame.iloc[index]["return_non_positive_pass"]),
            )
            _increment(
                condition_counts,
                "low_t_minus_1_ge_low_t_minus_2",
                bool(frame.iloc[index]["low_held_pass"]),
            )
            _increment(
                condition_counts,
                "price_sequence",
                bool(frame.iloc[index]["price_sequence_pass"]),
            )
            _increment(
                condition_counts,
                "shallow_gap_1pct_to_under_1_5pct",
                bool(frame.iloc[index]["shallow_gap_pass"]),
            )
            _increment(
                condition_counts,
                "rsi_2_le_50",
                bool(frame.iloc[index]["shallow_rsi_pass"]),
            )
            _increment(
                condition_counts,
                "close_t_gt_close_t_minus_1",
                bool(frame.iloc[index]["close_confirmation_pass"]),
            )
            _increment(condition_counts, "supplemental_raw_signal", supplemental_raw)
            if original_raw:
                diagnostics["original_raw_signal_count"] += 1
            if supplemental_raw:
                diagnostics["supplemental_raw_signal_count"] += 1
            if original_raw and supplemental_raw:
                diagnostics["supplemental_overlap_with_original"] += 1
            if original_raw or supplemental_raw:
                diagnostics["candidate_raw_signal_count"] += 1

            selected_origin: Literal["original", "supplemental"] | None = None
            if original_raw:
                selected_origin = "original"
            elif supplemental_raw:
                selected_origin = "supplemental"

            if selected_origin is not None:
                if not enough_time_to_exit or not lifecycle_within_end:
                    diagnostics["entry_blocked_by_cutoff"] += 1
                elif position is not None:
                    diagnostics["entry_blocked_by_position"] += 1
                elif pending_signal_index is not None:
                    diagnostics["entry_blocked_by_pending_signal"] += 1
                elif not cooldown_ready:
                    diagnostics["entry_blocked_by_cooldown"] += 1
                else:
                    diagnostics["entry_possible_count"] += 1
                    accepted.append(session)
                    diagnostics["accepted_signal_count"] += 1
                    if selected_origin == "original":
                        diagnostics["original_signals_accepted"] += 1
                    else:
                        diagnostics["supplemental_signals_accepted"] += 1
                    pending_signal_origin = selected_origin
                    pending_signal_index = index

    origin_counts = diagnostics["completed_trade_origin_counts"]
    assert isinstance(origin_counts, dict)
    origin_counts["original"] = sum(
        trade.signal_origin == "original" for trade in trades
    )
    origin_counts["supplemental"] = sum(
        trade.signal_origin == "supplemental" for trade in trades
    )
    return BacktestResult(tuple(trades), tuple(accepted), cash, diagnostics)


def qualification_metrics(
    result: BacktestResult, *, initial_cash: float = 100_000.0
) -> dict[str, float | int]:
    """從已完成交易重算報酬、profit factor 與 realized drawdown。"""

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
    """以持倉中的每日 Low 做成本後可清算價估值。"""

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
    "SUPPLEMENTAL_ONLY_SPEC",
    "V009_ONLY_SPEC",
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
