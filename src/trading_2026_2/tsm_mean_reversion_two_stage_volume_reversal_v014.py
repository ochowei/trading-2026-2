"""TSM「放量承接後的縮量淺回測」Study 的可重算核心。

本模組只接受已凍結的日線 OHLCV，不下載資料、不連線券商，也不建立真實委託。
它逐字保留 v009 的原有進場路徑，並加入一條事前固定的補充路徑：最新有效
放量事件必須在訊號日前第 2 至第 5 個交易日，之後先出現收跌且成交量不超過
事件量 80% 的縮量回測，低點不能跌破事件低點，最後才用收盤上漲、RSI(2) <= 50、
低於 SMA(20) 1.0%（含）但未滿 1.5% 確認。事件只使用一次，新的有效事件會取代舊事件。
持有、停損停利、成本、風控與最多一個部位的執行規則沿用 v009。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
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
    """預先登記的 TSM 候選與對照路徑共用參數。"""

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
    cooldown_sessions: int = 5
    target_return: float = 0.04
    stop_return: float = -0.04
    holding_sessions: int = 10
    fold_warmup_sessions: int = 25
    initial_cash: float = 100_000.0
    risk_fraction: float = 0.02
    supplemental_path_enabled: bool = True
    supplemental_volume_ratio: float = 1.25
    supplemental_pullback_volume_ratio: float = 0.80
    supplemental_event_window_min_sessions: int = 2
    supplemental_event_window_max_sessions: int = 5
    supplemental_event_close_position_minimum: float = 0.50
    supplemental_signal_gap_min: float = 0.010
    supplemental_signal_gap_max: float = 0.015

    def with_changes(self, **changes: object) -> StrategySpec:
        """建立明示的 baseline 或 challenge 變體，不修改 frozen candidate。"""

        return replace(self, **changes)


BASE_COST = CostModel(slippage_bps=5.0, fee_bps=1.0)
STRESS_COST = CostModel(slippage_bps=20.0, fee_bps=2.0)
DEFAULT_SPEC = StrategySpec()
BASELINE_SPEC = DEFAULT_SPEC.with_changes(
    volume_lead_enabled=False,
    require_close_above_prior_close=False,
    supplemental_path_enabled=False,
)
PRICE_ONLY_SPEC = DEFAULT_SPEC.with_changes(volume_lead_enabled=False)
VOLUME_ONLY_SPEC = DEFAULT_SPEC.with_changes(require_close_above_prior_close=False)
V009_ONLY_SPEC = DEFAULT_SPEC.with_changes(supplemental_path_enabled=False)


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
    signal_origin: Literal["original", "supplemental"] = "original"


@dataclass(frozen=True)
class BacktestResult:
    trades: tuple[Trade, ...]
    accepted_signal_sessions: tuple[pd.Timestamp, ...]
    ending_cash: float
    accepted_signal_origins: tuple[str, ...] = ()
    supplemental_event_sessions: tuple[pd.Timestamp | None, ...] = ()
    supplemental_diagnostics: dict[str, int] = field(default_factory=dict)


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
    """只用當下及更早 session 計算訊號與放量事件。"""

    clean = validate_bars(bars)
    sma = clean["Close"].rolling(
        spec.sma_lookback, min_periods=spec.sma_min_periods
    ).mean()
    rsi = _rsi(clean["Close"], spec.rsi_lookback, spec.rsi_min_periods)
    prior_volume_average = clean["Volume"].shift(1).rolling(
        spec.volume_lookback, min_periods=spec.volume_average_min_periods
    ).mean()
    volume_spike_ratio = clean["Volume"] / prior_volume_average
    prior_volume_spike = volume_spike_ratio.shift(1).rolling(
        spec.volume_lead_window, min_periods=spec.volume_lead_min_periods
    ).max()
    prior_close = clean["Close"].shift(1)
    close_above_prior_close = clean["Close"] > prior_close
    day_range = clean["High"] - clean["Low"]
    close_position = (clean["Close"] - clean["Low"]) / day_range
    supplemental_volume_event = (
        prior_volume_average.gt(0)
        & clean["High"].gt(clean["Low"])
        & clean["Volume"].ge(
            prior_volume_average * spec.supplemental_volume_ratio
        )
        & close_position.ge(spec.supplemental_event_close_position_minimum)
    )

    result = clean.copy()
    result["sma_20"] = sma
    result["mean_reversion_gap"] = (sma - clean["Close"]) / sma
    result["rsi_2"] = rsi
    result["volume_spike_ratio"] = volume_spike_ratio
    result["prior_volume_spike_ratio"] = prior_volume_spike
    result["prior_close"] = prior_close
    result["close_above_prior_close"] = close_above_prior_close
    raw_signal = (
        (result["mean_reversion_gap"] >= spec.mean_reversion_min)
        & (result["rsi_2"] <= spec.rsi_max)
    )
    if spec.volume_lead_enabled:
        raw_signal &= result["prior_volume_spike_ratio"] >= spec.volume_spike_ratio
    if spec.require_close_above_prior_close:
        raw_signal &= result["close_above_prior_close"]
    result["close_position_in_day_range"] = close_position
    result["supplemental_volume_event"] = supplemental_volume_event
    result["supplemental_retest_seen"] = False
    result["v009_raw_signal"] = raw_signal
    result["raw_signal"] = raw_signal
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
    """以單一 TSM sleeve 執行不可重疊持倉的確定性回測。

    補充事件在每個收盤完成後更新，所有事件狀態只向前走。事件的生命週期
    是 ``event+2`` 到 ``event+5``；新事件直接取代舊事件，第一個符合價格
    確認的訊號就消耗事件，即使當下因持倉、冷卻或年末 cutoff 而不能成交。
    ``reset_at_start`` 用於每個 Historical Evaluation fold：前 25 個 session
    只暖機，不接受訊號。
    """

    if spec.cooldown_sessions < 0 or spec.holding_sessions <= 0:
        raise ValueError("cooldown 與持有期設定不合法")
    frame = indicators(bars, spec)
    cash = float(spec.initial_cash)
    trades: list[Trade] = []
    accepted: list[pd.Timestamp] = []
    accepted_origins: list[str] = []
    trade_event_sessions: list[pd.Timestamp | None] = []
    pending_signal_index: int | None = None
    pending_signal_origin: Literal["original", "supplemental"] | None = None
    pending_event_session: pd.Timestamp | None = None
    last_exit_index: int | None = None
    position: dict[str, object] | None = None
    time_exit_index: int | None = None
    active_event: dict[str, object] | None = None
    event_diagnostics = {
        "volume_events_created": 0,
        "volume_events_replaced": 0,
        "volume_events_invalidated": 0,
        "volume_events_expired": 0,
        "supplemental_confirmations": 0,
        "supplemental_confirmations_blocked": 0,
        "supplemental_signals_accepted": 0,
        "original_signals_accepted": 0,
    }
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
                    signal_origin=position["signal_origin"],
                )
            )
            trade_event_sessions.append(position["event_session"])
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
                    "event_session": pending_event_session,
                }
                time_exit_index = index + spec.holding_sessions
            pending_signal_index = None
            pending_signal_origin = None
            pending_event_session = None

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
                trade_event_sessions.append(position["event_session"])
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
        original_signal = bool(bar["v009_raw_signal"])
        supplemental_signal = False
        supplemental_event_session: pd.Timestamp | None = None
        if spec.supplemental_path_enabled:
            if active_event is not None:
                event_index = int(active_event["index"])
                age = index - event_index
                if age > spec.supplemental_event_window_max_sessions:
                    event_diagnostics["volume_events_expired"] += 1
                    active_event = None
                elif age >= 1 and float(bar["Low"]) < float(active_event["low"]):
                    event_diagnostics["volume_events_invalidated"] += 1
                    active_event = None
                elif (
                    1 <= age <= spec.supplemental_event_window_max_sessions
                    and bool(bar["Close"] < bar["prior_close"])
                    and float(bar["Volume"])
                    <= float(active_event["volume"])
                    * spec.supplemental_pullback_volume_ratio
                ):
                    active_event["retest_seen"] = True
                    if active_event.get("retest_session") is None:
                        active_event["retest_session"] = session

            if bool(bar["supplemental_volume_event"]):
                if active_event is not None:
                    event_diagnostics["volume_events_replaced"] += 1
                active_event = {
                    "index": index,
                    "session": session,
                    "volume": float(bar["Volume"]),
                    "low": float(bar["Low"]),
                    "retest_seen": False,
                    "retest_session": None,
                }
                event_diagnostics["volume_events_created"] += 1

            if active_event is not None:
                event_index = int(active_event["index"])
                age = index - event_index
                signal_values_ready = (
                    pd.notna(bar["mean_reversion_gap"])
                    and pd.notna(bar["rsi_2"])
                    and pd.notna(bar["prior_close"])
                )
                supplemental_signal = bool(
                    index >= first_signal_index
                    and date_is_eligible
                    and spec.supplemental_event_window_min_sessions <= age
                    and age <= spec.supplemental_event_window_max_sessions
                    and bool(active_event["retest_seen"])
                    and signal_values_ready
                    and float(bar["mean_reversion_gap"])
                    >= spec.supplemental_signal_gap_min
                    and float(bar["mean_reversion_gap"])
                    < spec.supplemental_signal_gap_max
                    and float(bar["rsi_2"]) <= spec.rsi_max
                    and bool(bar["close_above_prior_close"])
                )
                if supplemental_signal:
                    event_diagnostics["supplemental_confirmations"] += 1
                    supplemental_event_session = active_event["session"]
                    active_event = None

        if supplemental_signal and original_signal:
            signal_origin: Literal["original", "supplemental"] = "original"
        elif original_signal:
            signal_origin = "original"
        elif supplemental_signal:
            signal_origin = "supplemental"
        else:
            signal_origin = None

        signal_can_be_accepted = (
            index >= first_signal_index
            and date_is_eligible
            and enough_time_to_exit
            and lifecycle_within_end
            and position is None
            and pending_signal_index is None
            and cooldown_ready
        )
        if supplemental_signal and not signal_can_be_accepted:
            event_diagnostics["supplemental_confirmations_blocked"] += 1
        if (
            signal_can_be_accepted
            and signal_origin is not None
        ):
            accepted.append(session)
            accepted_origins.append(signal_origin)
            pending_signal_index = index
            pending_signal_origin = signal_origin
            pending_event_session = supplemental_event_session
            if signal_origin == "supplemental":
                event_diagnostics["supplemental_signals_accepted"] += 1
            else:
                event_diagnostics["original_signals_accepted"] += 1

    return BacktestResult(
        tuple(trades),
        tuple(accepted),
        cash,
        tuple(accepted_origins),
        tuple(trade_event_sessions),
        event_diagnostics,
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
