"""TSM v001「量能加權收盤報酬一致性先於價格加速」研究引擎。

本模組測試一個和總量集中、量能脈衝、量能吸收、日內區間效率及收盤位置
承接不同的機制：在趨勢仍然成立時，先觀察最近五個已完成 session 的
成交量是否集中在正向收盤報酬較高的日子；當日再以價格加速確認，將
「高量日承擔較多正向收盤報酬」視為動能可能延續的先行訊號。

所有指標只讀取當日或更早的日線 OHLCV。模組不下載資料、不連線券商，
也不建立真實委託。
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
    """候選與 baseline 共用的事前固定執行及訊號規格。"""

    sma_lookback: int = 20
    sma_min_periods: int = 20
    mean_reversion_min: float = -0.10
    rsi_lookback: int = 2
    rsi_min_periods: int = 2
    rsi_max: float = 70.0
    volume_lookback: int = 20
    volume_average_min_periods: int = 20
    volume_lead_window: int = 5
    volume_lead_min_periods: int = 5
    volume_spike_ratio: float = 1.05
    volume_lead_enabled: bool = False
    return_alignment_window: int = 5
    return_alignment_min_periods: int = 5
    volume_weighted_return_min: float = -0.02
    volume_return_alignment_min: float = 0.0005
    volume_return_alignment_enabled: bool = True
    require_close_above_prior_close: bool = True
    volume_pressure_enabled: bool = False
    pressure_lookback: int = 5
    pressure_concentration_min: float = 1.25
    pressure_up_volume_share_min: float = 0.50
    trend_slope_lookback: int = 5
    trend_slope_floor: float = 0.95
    price_to_sma_floor: float = 0.90
    price_acceleration_lookback: int = 1
    price_acceleration_min: float = 0.02
    cooldown_sessions: int = 5
    target_return: float = 0.04
    stop_return: float = -0.04
    holding_sessions: int = 10
    fold_warmup_sessions: int = 25
    initial_cash: float = 100_000.0
    risk_fraction: float = 0.02

    def with_changes(self, **changes: object) -> StrategySpec:
        """建立事前登記的 baseline 或消融規格。"""

        return replace(self, **changes)


BASE_COST = CostModel(slippage_bps=5.0, fee_bps=1.0)
STRESS_COST = CostModel(slippage_bps=20.0, fee_bps=2.0)
DEFAULT_SPEC = StrategySpec()
BASELINE_SPEC = DEFAULT_SPEC.with_changes(
    volume_return_alignment_enabled=False,
)
VOLUME_RETURN_ALIGNMENT_ONLY_SPEC = DEFAULT_SPEC.with_changes(
    require_close_above_prior_close=False,
    volume_return_alignment_enabled=True,
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


@dataclass(frozen=True)
class BacktestResult:
    trades: tuple[Trade, ...]
    accepted_signal_sessions: tuple[pd.Timestamp, ...]
    ending_cash: float


def validate_bars(bars: pd.DataFrame) -> pd.DataFrame:
    """驗證並正規化已調整 OHLCV。"""

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


def _required_history_sessions(spec: StrategySpec) -> int:
    """回傳所有指標 ready 的最早 zero-based index。"""

    return max(
        spec.sma_min_periods - 1,
        spec.rsi_min_periods,
        spec.volume_average_min_periods + spec.return_alignment_window,
        spec.sma_min_periods - 1 + spec.trend_slope_lookback,
    )


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """計算只使用當日以前資訊的趨勢、價格加速及量報酬一致性指標。"""

    clean = validate_bars(bars)
    close = clean["Close"]
    volume = clean["Volume"]
    sma = close.rolling(spec.sma_lookback, min_periods=spec.sma_min_periods).mean()
    rsi = _rsi(close, spec.rsi_lookback, spec.rsi_min_periods)
    prior_close = close.shift(1)
    daily_return = close / prior_close - 1.0
    prior_volume_sum = volume.shift(1).rolling(
        spec.return_alignment_window,
        min_periods=spec.return_alignment_min_periods,
    ).sum()
    prior_volume_weighted_return = (
        (daily_return * volume).shift(1).rolling(
            spec.return_alignment_window,
            min_periods=spec.return_alignment_min_periods,
        ).sum()
        / prior_volume_sum
    )
    prior_unweighted_return = daily_return.shift(1).rolling(
        spec.return_alignment_window,
        min_periods=spec.return_alignment_min_periods,
    ).mean()
    # 與 v003 contract 宣告的 20 + 5 ready 邊界一致：先完成一段完整的
    # 20-session volume baseline，再讓後續五個已完成 session 形成可辨識的
    # return-alignment window。這個遮罩只延後 ready 狀態，不改變任何已
    # ready row 的數值，也不引入當日資料。
    prior_volume_average = volume.shift(1).rolling(
        spec.volume_lookback,
        min_periods=spec.volume_average_min_periods,
    ).mean()
    alignment_ready = (
        prior_volume_weighted_return.notna()
        & prior_unweighted_return.notna()
        & prior_volume_average.shift(spec.return_alignment_window).notna()
    )
    prior_volume_weighted_return = prior_volume_weighted_return.where(alignment_ready)
    prior_unweighted_return = prior_unweighted_return.where(alignment_ready)
    prior_volume_return_alignment = (
        prior_volume_weighted_return - prior_unweighted_return
    )
    trend_slope_ratio = sma / sma.shift(spec.trend_slope_lookback)
    price_to_sma = close / sma
    price_acceleration = close / close.shift(spec.price_acceleration_lookback) - 1.0
    close_above_prior_close = close > prior_close
    # 趨勢條件看均線斜率，不把「收盤高於 SMA」當成必要條件；這保留
    # 趨勢中的淺回撤，並讓價格相對 SMA 的下限另行表達。
    trend_regime = trend_slope_ratio >= spec.trend_slope_floor
    volume_return_alignment_lead = (
        (prior_volume_weighted_return >= spec.volume_weighted_return_min)
        & (prior_volume_return_alignment >= spec.volume_return_alignment_min)
    )
    momentum_signal = (
        trend_regime
        & (price_to_sma >= spec.price_to_sma_floor)
        & (price_acceleration >= spec.price_acceleration_min)
        & (rsi <= spec.rsi_max)
        & (rsi.notna())
        & (close_above_prior_close | ~spec.require_close_above_prior_close)
        & ((sma - close) / sma >= spec.mean_reversion_min)
    )
    raw_signal = momentum_signal.copy()
    if spec.volume_return_alignment_enabled:
        raw_signal &= volume_return_alignment_lead
    result = clean.copy()
    result["sma_20"] = sma
    result["rsi_2"] = rsi
    result["prior_volume_sum"] = prior_volume_sum
    result["daily_return"] = daily_return
    result["prior_volume_weighted_return"] = prior_volume_weighted_return
    result["prior_unweighted_return"] = prior_unweighted_return
    result["prior_volume_return_alignment"] = prior_volume_return_alignment
    result["trend_slope_ratio"] = trend_slope_ratio
    result["price_to_sma"] = price_to_sma
    result["price_acceleration"] = price_acceleration
    result["prior_close"] = prior_close
    result["close_above_prior_close"] = close_above_prior_close
    result["trend_regime"] = trend_regime
    result["volume_return_alignment_lead"] = volume_return_alignment_lead
    result["raw_momentum_signal"] = momentum_signal
    result["raw_signal"] = raw_signal.fillna(False).astype(bool)
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
    """回傳同時符合現金上限與 stop 風險預算的最大整數股數。"""

    if cash < 0:
        raise ValueError("可用現金不得小於 0")
    if raw_entry <= 0:
        raise ValueError("原始進場價必須大於 0")
    if not 0 < risk_fraction <= 1:
        raise ValueError("risk_fraction 必須大於 0 且不超過 1")
    if not -1 < stop_return < 0:
        raise ValueError("stop_return 必須介於 -1 與 0 之間")
    executed_entry = _entry_fill(raw_entry, cost)
    executed_stop = _exit_fill(raw_entry * (1.0 + stop_return), cost)
    entry_cash_per_share = executed_entry * (1.0 + cost.fee_bps / 10_000.0)
    stop_proceeds_per_share = executed_stop * (1.0 - cost.fee_bps / 10_000.0)
    modeled_loss_per_share = entry_cash_per_share - stop_proceeds_per_share
    if modeled_loss_per_share <= 0:
        raise ValueError("成本內含的 stop 每股損失必須大於 0")
    affordable = floor(cash / entry_cash_per_share)
    risk_limited = floor((cash * risk_fraction) / modeled_loss_per_share)
    return max(0, min(affordable, risk_limited))


def _intraday_exit(
    bar: pd.Series,
    target: float,
    stop: float,
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


def backtest(
    bars: pd.DataFrame,
    *,
    spec: StrategySpec = DEFAULT_SPEC,
    cost: CostModel = BASE_COST,
    reset_at_start: bool = False,
    signal_start: str | pd.Timestamp | None = None,
    signal_end: str | pd.Timestamp | None = None,
) -> BacktestResult:
    """以不可重疊持倉、下一個 open 進場的確定性回測。"""

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
        spec.fold_warmup_sessions
        if reset_at_start
        else _required_history_sessions(spec)
    )
    start = pd.Timestamp(signal_start).normalize() if signal_start is not None else None
    end = pd.Timestamp(signal_end).normalize() if signal_end is not None else None
    if start is not None and end is not None and start > end:
        raise ValueError("signal_start 不得晚於 signal_end")

    def close_position(
        session: pd.Timestamp,
        bar: pd.Series,
        raw_exit: float,
        exit_reason: ExitReason,
        held_sessions: int,
        state: dict[str, object],
    ) -> None:
        nonlocal cash, position, time_exit_index, last_exit_index
        executed_exit = _exit_fill(raw_exit, cost)
        shares = int(state["shares"])
        exit_fee = shares * executed_exit * cost.fee_bps / 10_000.0
        cash += shares * executed_exit - exit_fee
        total_fees = float(state["entry_fee"]) + exit_fee
        pnl = cash - float(state["cash_before_entry"])
        trades.append(
            Trade(
                signal_session=state["signal_session"],
                entry_session=state["entry_session"],
                exit_session=session,
                raw_entry_price=float(state["raw_entry"]),
                raw_exit_price=raw_exit,
                executed_entry_price=float(state["executed_entry"]),
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
        last_exit_index = frame.index.get_loc(session)

    for index, (session, bar) in enumerate(frame.iterrows()):
        if position is not None and time_exit_index == index:
            state = position
            close_position(
                session,
                bar,
                float(bar["Open"]),
                "time",
                spec.holding_sessions,
                state,
            )

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
            state = position
            exit_match = _intraday_exit(
                bar,
                float(state["target"]),
                float(state["stop"]),
            )
            if exit_match is not None:
                raw_exit, exit_reason = exit_match
                close_position(
                    session,
                    bar,
                    raw_exit,
                    exit_reason,
                    int(state["held_sessions"]) + 1,
                    state,
                )
            else:
                state["held_sessions"] = int(state["held_sessions"]) + 1

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


def qualification_metrics(
    result: BacktestResult,
    *,
    initial_cash: float = 100_000.0,
) -> dict[str, float | int]:
    """從已完成交易重算報酬、profit factor 與 realized drawdown。"""

    pnls = [trade.pnl for trade in result.trades]
    gross_profit = sum(value for value in pnls if value > 0)
    gross_loss = -sum(value for value in pnls if value < 0)
    profit_factor = gross_profit / gross_loss if gross_loss else (
        inf if gross_profit else 0.0
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


__all__ = [
    "BASE_COST",
    "BASELINE_SPEC",
    "BacktestResult",
    "CostModel",
    "DEFAULT_SPEC",
    "STRESS_COST",
    "StrategySpec",
    "Trade",
    "VOLUME_RETURN_ALIGNMENT_ONLY_SPEC",
    "_entry_fill",
    "_exit_fill",
    "_intraday_exit",
    "_required_history_sessions",
    "_rsi",
    "backtest",
    "indicators",
    "qualification_metrics",
    "risk_budget_shares",
    "validate_bars",
]
