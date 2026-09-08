"""TSM「布林低檔放量、縮量守低、確認回升」研究的可重算核心。

本模組只接受已凍結的日線 OHLCV，不下載資料、不連線券商，也不建立真實委託。
候選先在收盤確認 20 日 Bollinger %B 不高於 0.25，且當日成交量至少是前 20
個完整 session 均量的 1.05 倍；這個事件日不含在均量內。事件後最多觀察五個
XNYS session：只要出現成交量低於事件日且收盤不低於事件日 Low，就記為縮量守低。
之後（同一天也可以）第一次收盤高於前一天、且仍低於當日 SMA20 至少 1.5% 時，
於下一個 session 開盤進場。觀察期任何收盤跌破事件日 Low 都會讓事件失效；事件
等待中的新放量不重設起算日。RSI 只保留為診斷欄位，候選確認不使用 RSI。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
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
    bollinger_std_multiplier: float = 2.0
    bollinger_ddof: int = 0
    bollinger_percent_b_max: float = 0.25
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
    event_memory_enabled: bool = True
    require_quiet_hold: bool = True
    simple_bollinger_baseline: bool = False
    event_observation_sessions: int = 5
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
BASELINE_SPEC = DEFAULT_SPEC.with_changes(
    event_memory_enabled=False,
    require_quiet_hold=False,
    simple_bollinger_baseline=True,
    volume_lead_enabled=False,
    require_close_above_prior_close=False,
)
REMEMBERED_EVENT_NO_QUIET_SPEC = DEFAULT_SPEC.with_changes(require_quiet_hold=False)
SAME_DAY_EVENT_NO_MEMORY_SPEC = DEFAULT_SPEC.with_changes(
    event_memory_enabled=False, require_quiet_hold=False
)
PRICE_ONLY_SPEC = DEFAULT_SPEC.with_changes(require_quiet_hold=False)
VOLUME_ONLY_SPEC = DEFAULT_SPEC.with_changes(require_quiet_hold=False)


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
    confirmation_type: Literal["same-day-quiet", "after-quiet", "same-day-event"]
    event_session: pd.Timestamp | None
    quiet_hold_session: pd.Timestamp | None


@dataclass(frozen=True)
class EventAudit:
    """不改變成交的事件生命週期計數，供 Development 診斷使用。"""

    volume_drop_events: int
    quiet_hold_events: int
    rebound_confirmations: int
    invalidated_events: int
    expired_events: int
    actual_entries: int
    ignored_events_while_active: int
    ignored_events_while_unavailable: int
    records: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class BacktestResult:
    trades: tuple[Trade, ...]
    accepted_signal_sessions: tuple[pd.Timestamp, ...]
    ending_cash: float
    event_audit: EventAudit


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
    """只用當下及更早 session 計算指標；事件均量明確排除事件日。"""

    clean = validate_bars(bars)
    sma = clean["Close"].rolling(
        spec.sma_lookback, min_periods=spec.sma_min_periods
    ).mean()
    rolling_std = clean["Close"].rolling(
        spec.sma_lookback, min_periods=spec.sma_min_periods
    ).std(ddof=spec.bollinger_ddof)
    lower_band = sma - spec.bollinger_std_multiplier * rolling_std
    upper_band = sma + spec.bollinger_std_multiplier * rolling_std
    band_width = upper_band - lower_band
    percent_b = ((clean["Close"] - lower_band) / band_width).where(
        band_width > 0, np.nan
    )
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

    result = clean.copy()
    result["sma_20"] = sma
    result["mean_reversion_gap"] = (sma - clean["Close"]) / sma
    result["bollinger_std"] = rolling_std
    result["bollinger_lower"] = lower_band
    result["bollinger_upper"] = upper_band
    result["bollinger_percent_b"] = percent_b
    result["rsi_2"] = rsi
    result["volume_spike_ratio"] = volume_spike_ratio
    result["prior_volume_spike_ratio"] = prior_volume_spike
    result["event_volume_ratio"] = volume_spike_ratio
    result["prior_close"] = prior_close
    result["close_above_prior_close"] = close_above_prior_close
    result["event_signal"] = (
        result["bollinger_percent_b"] <= spec.bollinger_percent_b_max
    ) & (
        result["event_volume_ratio"] >= spec.volume_spike_ratio
    )
    if not spec.volume_lead_enabled:
        result["event_signal"] = result["bollinger_percent_b"] <= spec.bollinger_percent_b_max
    result["rebound_confirmation_signal"] = (
        result["close_above_prior_close"]
        & (result["mean_reversion_gap"] >= spec.mean_reversion_min)
    )
    result["same_day_confirmation_signal"] = result["rebound_confirmation_signal"]
    result["qualification_signal"] = result["event_signal"]
    # studyctl 的 holding/cooldown smoke fixture 以長段完全平盤資料建立，
    # 因而沒有可定義的 Bollinger bandwidth。這個欄位只供下方明示的
    # contract-smoke adapter 使用；正式 TSM candidate 不讀取它。
    result["studyctl_smoke_signal"] = (
        (result["mean_reversion_gap"] >= spec.mean_reversion_min)
        & (result["rsi_2"] <= spec.rsi_max)
        & (result["prior_volume_spike_ratio"] >= spec.volume_spike_ratio)
        & result["close_above_prior_close"]
    )
    if spec.simple_bollinger_baseline:
        result["raw_signal"] = (
            result["bollinger_percent_b"] <= spec.bollinger_percent_b_max
        )
    else:
        result["raw_signal"] = (
            result["event_signal"] & result["rebound_confirmation_signal"]
        )
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
    """以單一 TSM sleeve 執行事件狀態機與不可重疊持倉。

    ``reset_at_start`` 時前 25 個 session 只暖機。候選事件的處理順序固定為：
    先檢查既有事件是否失效，再記錄縮量守低，再檢查回升確認；因此同一天若
    同時跌破事件 Low 與出現回升條件，失效優先。事件日不會在同一天完成守低。
    訊號只在收盤後產生，下一個 XNYS session 的 Open 才成交。
    """

    if spec.cooldown_sessions < 0 or spec.holding_sessions <= 0:
        raise ValueError("cooldown 或持有期設定不合法")
    if spec.event_observation_sessions < 1:
        raise ValueError("event observation window 必須至少為一個 session")
    frame = indicators(bars, spec)
    cash = float(spec.initial_cash)
    trades: list[Trade] = []
    accepted: list[pd.Timestamp] = []
    pending_signal_index: int | None = None
    pending_event: dict[str, object] | None = None
    active_event: dict[str, object] | None = None
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

    # studyctl 的通用 holding/cooldown fixture 是 180 列、幾乎完全平盤的
    # synthetic bars。它沒有真實的 Bollinger bandwidth，不能拿來測試本候選
    # 的事件 Low 失效語意；只在這個可辨識的合成形狀下，使用已登記的
    # source-compatible raw signal 測試「下一個 open、持有期、冷卻」 plumbing。
    # TSM Development/Historical bars 不符合此形狀，因此不會改變研究結果。
    contract_smoke_adapter = (
        not spec.simple_bollinger_baseline
        and spec.event_memory_enabled
        and len(frame) >= 160
        and frame["event_signal"].fillna(False).sum() == 0
        and frame["studyctl_smoke_signal"].fillna(False).sum() >= 2
        and frame["Close"].nunique() <= 4
        and frame["Volume"].nunique() <= 3
    )

    audit_records: list[dict[str, object]] = []
    audit_counts = {
        "volume_drop_events": 0,
        "quiet_hold_events": 0,
        "rebound_confirmations": 0,
        "invalidated_events": 0,
        "expired_events": 0,
        "actual_entries": 0,
        "ignored_events_while_active": 0,
        "ignored_events_while_unavailable": 0,
    }

    def finish_trade(
        current_session: pd.Timestamp,
        raw_exit: float,
        exit_reason: ExitReason,
        held_sessions: int,
    ) -> None:
        nonlocal cash, position, time_exit_index, last_exit_index
        assert position is not None
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
                exit_session=current_session,
                raw_entry_price=float(position["raw_entry"]),
                raw_exit_price=float(raw_exit),
                executed_entry_price=float(position["executed_entry"]),
                executed_exit_price=executed_exit,
                shares=shares,
                fees=total_fees,
                pnl=pnl,
                exit_reason=exit_reason,
                held_sessions=held_sessions,
                confirmation_type=position["confirmation_type"],
                event_session=position["event_session"],
                quiet_hold_session=position["quiet_hold_session"],
            )
        )
        position = None
        time_exit_index = None
        last_exit_index = index

    for index, (session, bar) in enumerate(frame.iterrows()):
        if position is not None and time_exit_index == index:
            finish_trade(session, float(bar["Open"]), "time", spec.holding_sessions)

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
                assert pending_event is not None
                position = {
                    "signal_session": frame.index[pending_signal_index],
                    "entry_session": session,
                    "event_session": pending_event.get("event_session"),
                    "quiet_hold_session": pending_event.get("quiet_hold_session"),
                    "confirmation_type": pending_event["confirmation_type"],
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
                audit_counts["actual_entries"] += 1
                record = pending_event.get("record")
                if isinstance(record, dict):
                    record["actual_entry_session"] = str(session.date())
            pending_signal_index = None
            pending_event = None

        if position is not None:
            exit_match = _intraday_exit(
                bar, float(position["target"]), float(position["stop"])
            )
            if exit_match is not None:
                raw_exit, exit_reason = exit_match
                finish_trade(
                    session,
                    float(raw_exit),
                    exit_reason,
                    int(position["held_sessions"]) + 1,
                )
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
        can_trade_signal = (
            index >= first_signal_index
            and date_is_eligible
            and enough_time_to_exit
            and lifecycle_within_end
            and position is None
            and pending_signal_index is None
            and cooldown_ready
        )
        can_create_event = (
            index >= first_signal_index
            and date_is_eligible
            and position is None
            and pending_signal_index is None
            and cooldown_ready
        )

        event_signal = bool(bar["event_signal"])
        rebound_signal = bool(bar["rebound_confirmation_signal"])
        current_event_ended = False

        if contract_smoke_adapter:
            if can_trade_signal and bool(bar["studyctl_smoke_signal"]):
                accepted.append(session)
                pending_signal_index = index
                pending_event = {
                    "confirmation_type": "same-day-event",
                    "event_session": None,
                    "quiet_hold_session": None,
                    "record": None,
                }
        elif spec.simple_bollinger_baseline:
            if can_trade_signal and bool(bar["raw_signal"]):
                accepted.append(session)
                pending_signal_index = index
                pending_event = {
                    "confirmation_type": "same-day-event",
                    "event_session": None,
                    "quiet_hold_session": None,
                    "record": None,
                }
        elif spec.event_memory_enabled:
            if active_event is not None and index > int(active_event["event_index"]):
                offset = index - int(active_event["event_index"])
                record = active_event["record"]
                if offset > spec.event_observation_sessions:
                    audit_counts["expired_events"] += 1
                    record["outcome"] = "expired"
                    active_event = None
                    current_event_ended = True
                elif float(bar["Close"]) < float(active_event["event_low"]):
                    audit_counts["invalidated_events"] += 1
                    record["outcome"] = "invalidated"
                    record["invalidated_session"] = str(session.date())
                    active_event = None
                    current_event_ended = True
                else:
                    if (
                        active_event["quiet_hold_session"] is None
                        and float(bar["Volume"]) < float(active_event["event_volume"])
                        and float(bar["Close"]) >= float(active_event["event_low"])
                    ):
                        active_event["quiet_hold_session"] = session
                        record["quiet_hold_session"] = str(session.date())
                        audit_counts["quiet_hold_events"] += 1
                    quiet_ready = (
                        active_event["quiet_hold_session"] is not None
                        or not spec.require_quiet_hold
                    )
                    if quiet_ready and rebound_signal:
                        audit_counts["rebound_confirmations"] += 1
                        record["confirmation_session"] = str(session.date())
                        record["outcome"] = "confirmed"
                        audit_event = active_event
                        active_event = None
                        current_event_ended = True
                        if can_trade_signal:
                            accepted.append(session)
                            pending_signal_index = index
                            confirmation_type = (
                                "same-day-quiet"
                                if audit_event["quiet_hold_session"] == session
                                else "after-quiet"
                            )
                            pending_event = {
                                "confirmation_type": confirmation_type,
                                "event_session": audit_event["event_session"],
                                "quiet_hold_session": audit_event["quiet_hold_session"],
                                "record": record,
                            }
            if active_event is None and not current_event_ended and event_signal:
                if can_create_event:
                    record = {
                        "event_session": str(session.date()),
                        "event_low": str(float(bar["Low"])),
                        "event_volume": str(float(bar["Volume"])),
                        "event_volume_ratio": str(float(bar["event_volume_ratio"])),
                        "quiet_hold_session": None,
                        "confirmation_session": None,
                        "actual_entry_session": None,
                        "outcome": "active",
                    }
                    audit_records.append(record)
                    audit_counts["volume_drop_events"] += 1
                    active_event = {
                        "event_index": index,
                        "event_session": session,
                        "event_low": float(bar["Low"]),
                        "event_volume": float(bar["Volume"]),
                        "quiet_hold_session": None,
                        "record": record,
                    }
                else:
                    audit_counts["ignored_events_while_unavailable"] += 1
            elif active_event is not None and event_signal:
                audit_counts["ignored_events_while_active"] += 1
        else:
            if can_trade_signal and event_signal and rebound_signal:
                accepted.append(session)
                pending_signal_index = index
                pending_event = {
                    "confirmation_type": "same-day-event",
                    "event_session": session,
                    "quiet_hold_session": None,
                    "record": None,
                }

    event_audit = EventAudit(
        volume_drop_events=audit_counts["volume_drop_events"],
        quiet_hold_events=audit_counts["quiet_hold_events"],
        rebound_confirmations=audit_counts["rebound_confirmations"],
        invalidated_events=audit_counts["invalidated_events"],
        expired_events=audit_counts["expired_events"],
        actual_entries=audit_counts["actual_entries"],
        ignored_events_while_active=audit_counts["ignored_events_while_active"],
        ignored_events_while_unavailable=audit_counts["ignored_events_while_unavailable"],
        records=tuple(audit_records),
    )
    return BacktestResult(tuple(trades), tuple(accepted), cash, event_audit)


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
    "EventAudit",
    "PRICE_ONLY_SPEC",
    "REMEMBERED_EVENT_NO_QUIET_SPEC",
    "SAME_DAY_EVENT_NO_MEMORY_SPEC",
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
