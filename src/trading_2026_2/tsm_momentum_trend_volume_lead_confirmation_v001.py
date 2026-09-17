"""TSM「動能趨勢＋量先價行」Study 的可重算日線引擎。

本模組只接受已凍結的日線 OHLCV，不下載資料、不連線券商，也不建立真實委託。
候選只有一條順勢路徑：先在已成立的非下彎 SMA(20) 趨勢中觀察成交量相對於前
20 個 session 均量至少 1.10 倍的事件，再在事件後最多五個 session 內等待收盤
高於前一個 session 的價格確認。事件日不會同日進場，確認失效後也不回看未來資料。

`mean_reversion_min` 與 `rsi_max` 是 workflow preflight 所要求的明示技術欄位；
本 Study 不使用均值回歸超跌條件，RSI(2) 只作為 ready／有限值的技術檢查，主要
交易機制是趨勢狀態、成交量先行與之後的價格確認。
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
    """事前登記的候選與執行參數。"""

    sma_lookback: int = 20
    sma_min_periods: int = 20
    mean_reversion_min: float = 0.0
    rsi_lookback: int = 2
    rsi_min_periods: int = 2
    rsi_max: float = 100.0
    volume_lookback: int = 20
    volume_average_min_periods: int = 20
    volume_lead_window: int = 5
    volume_lead_min_periods: int = 5
    volume_spike_ratio: float = 1.10
    volume_lead_enabled: bool = True
    require_close_above_prior_close: bool = True
    trend_sma_lag_sessions: int = 5
    event_close_floor_fraction: float = 0.85
    cooldown_sessions: int = 5
    target_return: float = 0.04
    stop_return: float = -0.04
    holding_sessions: int = 10
    fold_warmup_sessions: int = 25
    initial_cash: float = 100_000.0
    risk_fraction: float = 0.02

    def with_changes(self, **changes: object) -> StrategySpec:
        """建立明示的簡化基準變體，不修改 frozen candidate。"""

        return replace(self, **changes)


BASE_COST = CostModel(slippage_bps=5.0, fee_bps=1.0)
STRESS_COST = CostModel(slippage_bps=20.0, fee_bps=2.0)
DEFAULT_SPEC = StrategySpec()
BASELINE_SPEC = DEFAULT_SPEC.with_changes(volume_lead_enabled=False)


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


@dataclass(frozen=True)
class BacktestResult:
    trades: tuple[Trade, ...]
    accepted_signal_sessions: tuple[pd.Timestamp, ...]
    ending_cash: float


def validate_bars(bars: pd.DataFrame) -> pd.DataFrame:
    """驗證並正規化 OHLCV；不允許缺值、重複或錯序 session。"""

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
        result["High"].lt(result[["Open", "Close", "Low"]].max(axis=1)).any()
        or result["Low"].gt(result[["Open", "Close", "High"]].min(axis=1)).any()
    ):
        raise ValueError("OHLC 高低價關係不合法")
    return result


def _rsi(
    close: pd.Series,
    length: int,
    min_periods: int | None = None,
) -> pd.Series:
    """用簡單 rolling mean 計算 RSI；未 ready 時保留 NaN。"""

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
    """只使用當日與更早資料建立量能事件及後續價格確認。"""

    clean = validate_bars(bars)
    sma = clean["Close"].rolling(
        spec.sma_lookback, min_periods=spec.sma_min_periods
    ).mean()
    rsi = _rsi(clean["Close"], spec.rsi_lookback, spec.rsi_min_periods)
    prior_volume_average = clean["Volume"].shift(1).rolling(
        spec.volume_lookback, min_periods=spec.volume_average_min_periods
    ).mean()
    volume_event_ratio = clean["Volume"] / prior_volume_average
    prior_volume_spike_ratio = volume_event_ratio.shift(1).rolling(
        spec.volume_lead_window, min_periods=spec.volume_lead_min_periods
    ).max()
    prior_close = clean["Close"].shift(1)
    close_above_prior_close = clean["Close"] > prior_close

    prior_sma = sma.shift(1)
    prior_lagged_sma = sma.shift(1 + spec.trend_sma_lag_sessions)
    trend_state = prior_sma >= prior_lagged_sma
    event_price_aligned = clean["Close"] >= sma
    rsi_ready_and_bounded = rsi.notna() & (rsi <= spec.rsi_max)
    volume_event = (
        spec.volume_lead_enabled
        & volume_event_ratio.ge(spec.volume_spike_ratio)
        & trend_state
        & event_price_aligned
        & rsi_ready_and_bounded
    )

    raw_signal = pd.Series(False, index=clean.index, dtype=bool)
    price_confirmation = pd.Series(False, index=clean.index, dtype=bool)
    confirmation_delay = pd.Series(np.nan, index=clean.index, dtype=float)
    event_origin_index = pd.Series(np.nan, index=clean.index, dtype=float)
    event_origin: int | None = None

    for index in range(len(clean)):
        if event_origin is not None:
            age = index - event_origin
            event_close = float(clean["Close"].iloc[event_origin])
            event_floor = event_close * spec.event_close_floor_fraction
            if age > spec.volume_lead_window:
                event_origin = None
            elif float(clean["Close"].iloc[index]) < event_floor:
                event_origin = None
            elif (
                age >= 1
                and bool(close_above_prior_close.iloc[index])
                and bool(rsi_ready_and_bounded.iloc[index])
            ):
                raw_signal.iloc[index] = True
                price_confirmation.iloc[index] = True
                confirmation_delay.iloc[index] = float(age)
                event_origin_index.iloc[index] = float(event_origin)
                # A confirmation blocked by an open position or cooldown must
                # remain observable until the fixed window ends.  The portfolio
                # state decides acceptance; indicators do not use that future
                # state to erase a still-valid volume event.

        if bool(volume_event.iloc[index]) and not raw_signal.iloc[index]:
            event_origin = index

    result = clean.copy()
    result["sma_20"] = sma
    result["trend_sma_prior"] = prior_sma
    result["trend_sma_lagged"] = prior_lagged_sma
    result["trend_state"] = trend_state
    result["trend_close_aligned"] = event_price_aligned
    result["rsi_2"] = rsi
    result["prior_volume_average"] = prior_volume_average
    result["volume_event_ratio"] = volume_event_ratio
    result["prior_volume_spike_ratio"] = prior_volume_spike_ratio
    result["volume_event"] = volume_event
    result["prior_close"] = prior_close
    result["close_above_prior_close"] = close_above_prior_close
    result["price_confirmation"] = price_confirmation
    result["confirmation_delay_sessions"] = confirmation_delay
    result["event_origin_index"] = event_origin_index
    result["momentum_raw_signal"] = raw_signal
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
    """回傳符合現金上限與成本內含 stop 風險預算的最大整數股數。"""

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
    """依 gap 優先、同日採悲觀 stop 優先決定 raw fill。"""

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
    """回傳第一個可使用完整指標的 zero-based index。"""

    return max(
        spec.sma_min_periods - 1,
        spec.rsi_min_periods,
        spec.volume_average_min_periods + spec.volume_lead_min_periods,
        spec.sma_min_periods + spec.trend_sma_lag_sessions,
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
    """執行不可重疊持倉的確定性回測。

    `reset_at_start=True` 用於年度 fold：前 25 個 session 只暖機，不接受訊號。
    `signal_start` 用於 Development；暖機事件不能跨過 Development 邊界確認。
    """

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
    start_index = (
        int(frame.index.searchsorted(start)) if start is not None else None
    )
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
                held_sessions = index - int(
                    frame.index.get_loc(position["entry_session"])
                ) + 1
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

        enough_time_to_exit = index + spec.holding_sessions + 1 < len(frame)
        lifecycle_within_end = end is None or (
            enough_time_to_exit
            and frame.index[index + spec.holding_sessions + 1] <= end
        )
        cooldown_ready = (
            last_exit_index is None
            or index - last_exit_index >= spec.cooldown_sessions
        )
        date_is_eligible = (start is None or session >= start) and (
            end is None or session <= end
        )
        origin = frame["event_origin_index"].iloc[index]
        event_is_from_eligible_view = (
            start_index is None
            or pd.isna(origin)
            or int(origin) >= start_index
        )
        if (
            index >= first_signal_index
            and date_is_eligible
            and lifecycle_within_end
            and position is None
            and pending_signal_index is None
            and cooldown_ready
            and event_is_from_eligible_view
            and bool(frame["momentum_raw_signal"].iloc[index])
        ):
            accepted.append(session)
            pending_signal_index = index

    return BacktestResult(tuple(trades), tuple(accepted), cash)


def qualification_metrics(
    result: BacktestResult, *, initial_cash: float = 100_000.0
) -> dict[str, float | int]:
    """從已完成交易重算基本 Development 摘要。"""

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
    return {
        "completed_trades": len(result.trades),
        "traded_years": len({trade.signal_session.year for trade in result.trades}),
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
    """以持倉期間 Low 的成本後清算價作描述性壓力診斷。"""

    clean = validate_bars(bars)
    trade_by_entry = {trade.entry_session: trade for trade in result.trades}
    equity = initial_cash
    peak = equity
    maximum_drawdown = 0.0
    for session, _bar in clean.iterrows():
        trade = trade_by_entry.get(session)
        if trade is None:
            continue
        entry_value = trade.shares * trade.executed_entry_price
        entry_fee = entry_value * cost.fee_bps / 10_000.0
        cash_after_entry = equity - entry_value - entry_fee
        for holding_session in clean.loc[session : trade.exit_session].itertuples():
            liquidation = _exit_fill(float(holding_session.Low), cost)
            fee = trade.shares * liquidation * cost.fee_bps / 10_000.0
            marked_equity = cash_after_entry + trade.shares * liquidation - fee
            peak = max(peak, marked_equity)
            maximum_drawdown = max(
                maximum_drawdown,
                (peak - marked_equity) / peak if peak > 0 else 0.0,
            )
        equity += trade.pnl
    return maximum_drawdown
