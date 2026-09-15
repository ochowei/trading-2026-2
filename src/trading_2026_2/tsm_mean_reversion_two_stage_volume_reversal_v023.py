"""TSM v023「上升趨勢放量蓄勢後短期突破」補充路徑研究引擎。

本模組保留 v009 的原有均值回歸路徑，只增加一組完整、不可拆分的動能補充
機制：上升趨勢中的放量蓄勢事件，接著在五個交易日內首次收盤突破固定價位。
事件、持倉、冷卻與成交邊界都在這裡固定；模組不下載資料、不連線券商，也不
建立真實委託，只接受已凍結的日線 OHLCV。
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
    """v009 參數與 v023 動能補充路徑的固定參數。"""

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
    supplemental_trend_sma_lookback: int = 5
    supplemental_event_high_lookback: int = 5
    supplemental_event_volume_ratio: float = 1.25
    supplemental_confirmation_window: int = 5
    cooldown_sessions: int = 5
    target_return: float = 0.04
    stop_return: float = -0.04
    holding_sessions: int = 10
    fold_warmup_sessions: int = 25
    initial_cash: float = 100_000.0
    risk_fraction: float = 0.02

    def with_changes(self, **changes: object) -> StrategySpec:
        """建立明示的 control 或描述性消融變體。"""

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
    baseline_path_enabled=False,
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
    """回傳所有原有與補充指標都 ready 的最早 zero-based index。"""

    original = v009._required_history_sessions(spec)
    trend = spec.sma_min_periods - 1 + spec.supplemental_trend_sma_lookback
    event_high = spec.supplemental_event_high_lookback
    event_volume = spec.volume_average_min_periods
    return max(original, trend, event_high, event_volume)


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """計算 v009 原有指標與逐日可觀察的放量事件條件。

    放量事件的平均量、前五日最高價與趨勢比較都排除當日；確認本身需要事件
    狀態，因此由 ``backtest`` 在事件日後逐日判定，不能只靠無狀態欄位猜測。
    """

    base = v009.indicators(bars, spec=spec)
    result = base.copy()
    sma_five_sessions_ago = result["sma_20"].shift(
        spec.supplemental_trend_sma_lookback
    )
    prior_volume_average = result["Volume"].shift(1).rolling(
        spec.volume_lookback,
        min_periods=spec.volume_average_min_periods,
    ).mean()
    event_volume_ratio = result["Volume"] / prior_volume_average
    previous_high = result["High"].shift(1).rolling(
        spec.supplemental_event_high_lookback,
        min_periods=spec.supplemental_event_high_lookback,
    ).max()

    trend_ready = result["sma_20"].notna() & sma_five_sessions_ago.notna()
    trend_condition = trend_ready & (
        (result["Close"] > result["sma_20"])
        & (result["sma_20"] > sma_five_sessions_ago)
    )
    event_volume_ready = prior_volume_average.notna() & previous_high.notna()
    event_volume_threshold_pass = event_volume_ready & (
        event_volume_ratio >= spec.supplemental_event_volume_ratio
    )
    event_close_ceiling_pass = event_volume_ready & (
        result["Close"] <= previous_high
    )
    volume_event = (
        trend_condition
        & event_volume_threshold_pass
        & event_close_ceiling_pass
    )
    fixed_breakout_price = pd.concat(
        [previous_high.rename("previous_high"), result["High"].rename("event_high")],
        axis=1,
    ).max(axis=1)

    if spec.original_path_enabled or spec.baseline_path_enabled:
        v009_raw_signal = base["raw_signal"].astype(bool)
    else:
        v009_raw_signal = pd.Series(False, index=result.index, dtype=bool)

    result["sma_20_five_sessions_ago"] = sma_five_sessions_ago
    result["prior_volume_average"] = prior_volume_average
    result["event_volume_ratio"] = event_volume_ratio
    result["previous_five_high"] = previous_high
    result["trend_condition"] = trend_condition
    result["event_volume_threshold_pass"] = event_volume_threshold_pass
    result["event_close_ceiling_pass"] = event_close_ceiling_pass
    result["volume_event"] = volume_event if spec.supplemental_path_enabled else False
    result["fixed_breakout_price"] = fixed_breakout_price
    result["v009_raw_signal"] = v009_raw_signal
    # studyctl 的 generic synthetic fixture 需要一個可判讀的 raw signal 欄位；
    # 狀態化確認由 backtest 另行驗證，不能把未來五日資訊倒灌到 indicators。
    result["supplemental_raw_signal"] = pd.Series(
        False, index=result.index, dtype=bool
    )
    result["raw_signal"] = v009_raw_signal
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


def _text(value: float) -> str:
    return str(float(value))


def _new_diagnostics() -> dict[str, object]:
    return {
        "scope": (
            "指標 ready 且位於 2014-01-01 至 2018-12-31 signal view 的 session；"
            "事件可在持倉或冷卻期間成立，但確認後不延後。"
        ),
        "condition_pass_counts": {
            "trend_condition": 0,
            "event_volume_threshold": 0,
            "event_close_not_above_previous_five_high": 0,
            "volume_event": 0,
            "confirmation_close_strictly_above_breakout": 0,
            "confirmation_trend_condition": 0,
            "confirmation_both_conditions": 0,
        },
        "volume_event_count": 0,
        "events_started_count": 0,
        "events_ignored_while_tracking_count": 0,
        "confirmation_count": 0,
        "invalidated_event_count": 0,
        "expired_event_count": 0,
        "censored_at_signal_end_count": 0,
        "supplemental_confirmation_unfilled_due_position_count": 0,
        "supplemental_confirmation_unfilled_due_cooldown_count": 0,
        "supplemental_confirmation_unfilled_due_original_priority_count": 0,
        "supplemental_confirmation_unfilled_due_pending_signal_count": 0,
        "supplemental_confirmation_unfilled_due_cutoff_count": 0,
        "supplemental_confirmations_accepted_count": 0,
        "original_raw_signal_count": 0,
        "original_signals_accepted": 0,
        "candidate_raw_signal_count": 0,
        "accepted_signal_count": 0,
        "completed_trade_origin_counts": {"original": 0, "supplemental": 0},
        "event_ledger": [],
        "confirmation_ledger": [],
    }


def _increment(counts: dict[str, int], name: str, passed: bool) -> None:
    if passed:
        counts[name] += 1


def _finish_event(
    event: dict[str, object], *, outcome: str, resolution_session: pd.Timestamp
) -> None:
    event["outcome"] = outcome
    event["resolution_session"] = str(resolution_session.date())


def backtest(
    bars: pd.DataFrame,
    *,
    spec: StrategySpec = DEFAULT_SPEC,
    cost: CostModel = BASE_COST,
    reset_at_start: bool = False,
    signal_start: str | pd.Timestamp | None = None,
    signal_end: str | pd.Timestamp | None = None,
) -> BacktestResult:
    """以單一 sleeve 執行 v009 原路徑加 v023 狀態化補充路徑。

    事件規則的固定順序是：

    1. 事件日只建立事件，不可在當日確認；
    2. 第 1--5 個後續 session 先檢查「收盤嚴格高於固定突破價且仍在趨勢」；
    3. 未確認時才檢查收盤跌破事件低點，最後才在第 5 日到期；
    4. 確認即消耗，且同日若有 v009 raw signal，原路徑優先、不作補充路徑備援。
    """

    if spec.cooldown_sessions < 0 or spec.holding_sessions <= 0:
        raise ValueError("cooldown 與持有期設定不合法")
    if spec.supplemental_confirmation_window != 5:
        raise ValueError("v023 supplemental confirmation window 必須固定為 5")
    frame = indicators(bars, spec)
    cash = float(spec.initial_cash)
    trades: list[Trade] = []
    accepted: list[pd.Timestamp] = []
    diagnostics = _new_diagnostics()
    condition_counts = diagnostics["condition_pass_counts"]
    assert isinstance(condition_counts, dict)
    pending_signal_index: int | None = None
    pending_signal_origin: Literal["original", "supplemental"] | None = None
    last_exit_index: int | None = None
    position: dict[str, object] | None = None
    time_exit_index: int | None = None
    active_event: dict[str, object] | None = None
    event_counter = 0
    last_in_scope_session: pd.Timestamp | None = None
    first_signal_index = (
        spec.fold_warmup_sessions
        if reset_at_start
        else _required_history_sessions(spec)
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
                    "shares": shares,
                    "target": raw_entry * (1.0 + spec.target_return),
                    "stop": raw_entry * (1.0 + spec.stop_return),
                    "held_sessions": 0,
                    "signal_origin": pending_signal_origin or "original",
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
            last_exit_index is None
            or index - last_exit_index >= spec.cooldown_sessions
        )
        date_is_eligible = (start is None or session >= start) and (
            end is None or session <= end
        )
        in_scope = index >= first_signal_index and date_is_eligible
        if not in_scope:
            continue
        last_in_scope_session = session

        original_raw = bool(frame.iloc[index]["v009_raw_signal"])
        diagnostics["original_raw_signal_count"] += int(original_raw)
        _increment(
            condition_counts,
            "trend_condition",
            bool(frame.iloc[index]["trend_condition"]),
        )
        _increment(
            condition_counts,
            "event_volume_threshold",
            bool(frame.iloc[index]["event_volume_threshold_pass"])
            and bool(frame.iloc[index]["trend_condition"]),
        )
        _increment(
            condition_counts,
            "event_close_not_above_previous_five_high",
            bool(frame.iloc[index]["event_close_ceiling_pass"])
            and bool(frame.iloc[index]["trend_condition"]),
        )
        _increment(
            condition_counts,
            "volume_event",
            bool(frame.iloc[index]["volume_event"]),
        )

        active_at_start = active_event is not None
        supplemental_confirmed = False
        if active_event is not None:
            age = index - int(active_event["event_index"])
            if 1 <= age <= spec.supplemental_confirmation_window:
                breakout_pass = float(bar["Close"]) > float(
                    active_event["fixed_breakout_price"]
                )
                trend_pass = bool(frame.iloc[index]["trend_condition"])
                _increment(
                    condition_counts,
                    "confirmation_close_strictly_above_breakout",
                    breakout_pass,
                )
                _increment(
                    condition_counts,
                    "confirmation_trend_condition",
                    trend_pass,
                )
                _increment(
                    condition_counts,
                    "confirmation_both_conditions",
                    breakout_pass and trend_pass,
                )
                if breakout_pass and trend_pass:
                    diagnostics["confirmation_count"] += 1
                    supplemental_confirmed = True
                    active_event["confirmation_session"] = str(session.date())
                    _finish_event(
                        active_event,
                        outcome="confirmed",
                        resolution_session=session,
                    )
                    diagnostics["confirmation_ledger"].append(
                        {
                            "event_id": active_event["event_id"],
                            "confirmation_session": str(session.date()),
                            "fixed_breakout_price": _text(
                                float(active_event["fixed_breakout_price"])
                            ),
                            "trend_condition": True,
                            "close_strictly_above_breakout": True,
                            "decision": "pending",
                        }
                    )
                    active_event = None
                elif float(bar["Close"]) < float(active_event["event_low"]):
                    diagnostics["invalidated_event_count"] += 1
                    _finish_event(
                        active_event,
                        outcome="invalidated-close-below-event-low",
                        resolution_session=session,
                    )
                    active_event = None
                elif age == spec.supplemental_confirmation_window:
                    diagnostics["expired_event_count"] += 1
                    _finish_event(
                        active_event,
                        outcome="expired-after-fifth-session",
                        resolution_session=session,
                    )
                    active_event = None

        event_condition = bool(frame.iloc[index]["volume_event"])
        if event_condition:
            diagnostics["volume_event_count"] += 1
            if active_at_start:
                diagnostics["events_ignored_while_tracking_count"] += 1
            elif spec.supplemental_path_enabled:
                event_counter += 1
                event = {
                    "event_id": f"supplemental-event-{event_counter:03d}",
                    "event_session": str(session.date()),
                    "event_low": _text(float(bar["Low"])),
                    "previous_five_high": _text(
                        float(frame.iloc[index]["previous_five_high"])
                    ),
                    "event_high": _text(float(bar["High"])),
                    "fixed_breakout_price": _text(
                        float(frame.iloc[index]["fixed_breakout_price"])
                    ),
                    "confirmation_window_sessions": spec.supplemental_confirmation_window,
                    "outcome": "tracking",
                }
                diagnostics["event_ledger"].append(event)
                active_event = {
                    "event_id": event["event_id"],
                    "event_index": index,
                    "event_low": float(bar["Low"]),
                    "fixed_breakout_price": float(
                        frame.iloc[index]["fixed_breakout_price"]
                    ),
                    "event_record": event,
                }
                diagnostics["events_started_count"] += 1

        if original_raw or supplemental_confirmed:
            diagnostics["candidate_raw_signal_count"] += 1
        selected_origin: Literal["original", "supplemental"] | None = None
        if original_raw:
            selected_origin = "original"
        elif supplemental_confirmed:
            selected_origin = "supplemental"

        if original_raw and supplemental_confirmed:
            diagnostics[
                "supplemental_confirmation_unfilled_due_original_priority_count"
            ] += 1
            confirmation = diagnostics["confirmation_ledger"][-1]
            assert isinstance(confirmation, dict)
            confirmation["decision"] = "blocked-by-original-priority"
        elif supplemental_confirmed:
            confirmation = diagnostics["confirmation_ledger"][-1]
            assert isinstance(confirmation, dict)
            confirmation["decision"] = "pending"

        if selected_origin is not None:
            if not enough_time_to_exit or not lifecycle_within_end:
                if supplemental_confirmed and not original_raw:
                    diagnostics[
                        "supplemental_confirmation_unfilled_due_cutoff_count"
                    ] += 1
                    confirmation["decision"] = "blocked-by-signal-cutoff"
            elif position is not None:
                if supplemental_confirmed and not original_raw:
                    diagnostics[
                        "supplemental_confirmation_unfilled_due_position_count"
                    ] += 1
                    confirmation["decision"] = "blocked-by-position"
            elif pending_signal_index is not None:
                if supplemental_confirmed and not original_raw:
                    diagnostics[
                        "supplemental_confirmation_unfilled_due_pending_signal_count"
                    ] += 1
                    confirmation["decision"] = "blocked-by-pending-signal"
            elif not cooldown_ready:
                if supplemental_confirmed and not original_raw:
                    diagnostics[
                        "supplemental_confirmation_unfilled_due_cooldown_count"
                    ] += 1
                    confirmation["decision"] = "blocked-by-cooldown"
            else:
                accepted.append(session)
                diagnostics["accepted_signal_count"] += 1
                pending_signal_index = index
                pending_signal_origin = selected_origin
                if selected_origin == "original":
                    diagnostics["original_signals_accepted"] += 1
                else:
                    diagnostics["supplemental_confirmations_accepted_count"] += 1
                    confirmation["decision"] = "accepted"

    if active_event is not None:
        # signal_end 之後的資料只用來完成既有持倉，不應把事件的裁切日誤記成
        # 整份共享資料的最後一天。這個 session 也會供診斷核對資料邊界。
        last_session = last_in_scope_session or frame.index[-1]
        diagnostics["censored_at_signal_end_count"] += 1
        _finish_event(
            active_event["event_record"],
            outcome="censored-at-signal-end",
            resolution_session=last_session,
        )

    origin_counts = diagnostics["completed_trade_origin_counts"]
    assert isinstance(origin_counts, dict)
    origin_counts["original"] = sum(
        trade.signal_origin == "original" for trade in trades
    )
    origin_counts["supplemental"] = sum(
        trade.signal_origin == "supplemental" for trade in trades
    )
    return BacktestResult(
        tuple(trades), tuple(accepted), cash, diagnostics
    )


def qualification_metrics(
    result: BacktestResult, *, initial_cash: float = 100_000.0
) -> dict[str, float | int]:
    """從完成交易重算報酬、Profit Factor 與 realized drawdown。"""

    pnls = [trade.pnl for trade in result.trades]
    gross_profit = sum(value for value in pnls if value > 0)
    gross_loss = -sum(value for value in pnls if value < 0)
    profit_factor = (
        gross_profit / gross_loss if gross_loss else (inf if gross_profit else 0.0)
    )
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
    """以持倉中的每日 Low 做保守估值；不改變正式 realized gate。"""

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
