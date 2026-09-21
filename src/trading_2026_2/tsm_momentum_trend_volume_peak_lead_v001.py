"""TSM v004「量峰先於價峰」研究引擎。

本模組測試訊號日前五個已完成 session 的量能峰值，是否至少早於同一視窗的
收盤報酬峰值一個 session，形成量先於價的時序，再由訊號日價格加速確認。
量能與報酬峰值只使用訊號日前資料；執行與風控沿用固定的離線 OHLCV 實作。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from trading_2026_2 import tsm_momentum_trend_volume_gap_anchoring_v001 as _execution

BASE_COST = _execution.BASE_COST
STRESS_COST = _execution.STRESS_COST
BacktestResult = _execution.BacktestResult
CostModel = _execution.CostModel
Trade = _execution.Trade
validate_bars = _execution.validate_bars
_intraday_exit = _execution._intraday_exit
_rsi = _execution._rsi
_BASE_REQUIRED_HISTORY_SESSIONS = _execution._required_history_sessions


@dataclass(frozen=True)
class StrategySpec(_execution.StrategySpec):
    """候選與 baseline 共用的事前固定訊號及執行規格。"""

    volume_peak_lead_enabled: bool = True
    volume_peak_window: int = 5
    volume_peak_ratio_minimum: float = 1.20
    volume_peak_lead_minimum_sessions: int = 1
    price_peak_return_minimum: float = 0.0


DEFAULT_SPEC = StrategySpec(
    volume_gap_anchoring_enabled=False,
    volume_lead_enabled=True,
    volume_peak_lead_enabled=True,
    volume_peak_window=5,
    volume_peak_ratio_minimum=1.20,
    volume_peak_lead_minimum_sessions=1,
    price_peak_return_minimum=0.0,
)
BASELINE_SPEC = DEFAULT_SPEC.with_changes(volume_peak_lead_enabled=False)


def _last_max_position(values: np.ndarray) -> float:
    """回傳視窗內最後一個最大值位置，平手時選較新的 session。"""

    maximum = np.nanmax(values)
    positions = np.flatnonzero(values == maximum)
    return float(positions[-1])


def _required_history_sessions(spec: StrategySpec) -> int:
    """回傳所有指標 ready 的最早 zero-based index。"""

    return max(
        _BASE_REQUIRED_HISTORY_SESSIONS(spec),
        spec.volume_average_min_periods + spec.volume_peak_window,
    )


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """計算只使用當日以前資訊的趨勢、價格加速與量峰先行指標。"""

    clean = validate_bars(bars)
    close = clean["Close"]
    volume = clean["Volume"]
    sma = close.rolling(spec.sma_lookback, min_periods=spec.sma_min_periods).mean()
    rsi = _rsi(close, spec.rsi_lookback, spec.rsi_min_periods)
    prior_close = close.shift(1)
    prior_volume_average = volume.shift(1).rolling(
        spec.volume_lookback,
        min_periods=spec.volume_average_min_periods,
    ).mean()
    volume_spike_ratio = volume / prior_volume_average
    prior_spike = volume_spike_ratio.shift(1)
    prior_volume_ratio = prior_spike.rolling(
        spec.volume_peak_window,
        min_periods=spec.volume_peak_window,
    ).mean()
    prior_volume_peak_ratio = prior_spike.rolling(
        spec.volume_peak_window,
        min_periods=spec.volume_peak_window,
    ).max()
    prior_volume_peak_position = prior_spike.rolling(
        spec.volume_peak_window,
        min_periods=spec.volume_peak_window,
    ).apply(lambda values: float(np.argmax(values)), raw=True)
    close_return = close.pct_change()
    prior_return = close_return.shift(1)
    prior_price_return_peak = prior_return.rolling(
        spec.volume_peak_window,
        min_periods=spec.volume_peak_window,
    ).max()
    prior_price_return_peak_position = prior_return.rolling(
        spec.volume_peak_window,
        min_periods=spec.volume_peak_window,
    ).apply(_last_max_position, raw=True)
    peak_ready = (
        prior_volume_ratio.notna()
        & prior_volume_peak_ratio.notna()
        & prior_volume_peak_position.notna()
        & prior_price_return_peak.notna()
        & prior_price_return_peak_position.notna()
    )
    prior_volume_ratio = prior_volume_ratio.where(peak_ready)
    prior_volume_peak_ratio = prior_volume_peak_ratio.where(peak_ready)
    prior_volume_peak_position = prior_volume_peak_position.where(peak_ready)
    prior_price_return_peak = prior_price_return_peak.where(peak_ready)
    prior_price_return_peak_position = prior_price_return_peak_position.where(peak_ready)
    trend_slope_ratio = sma / sma.shift(spec.trend_slope_lookback)
    price_to_sma = close / sma
    price_acceleration = close / close.shift(spec.price_acceleration_lookback) - 1.0
    close_above_prior_close = close > prior_close
    trend_regime = trend_slope_ratio >= spec.trend_slope_floor
    volume_peak_qualifies = (
        (prior_volume_ratio >= spec.volume_spike_ratio)
        & (prior_volume_peak_ratio >= spec.volume_peak_ratio_minimum)
        & (prior_price_return_peak >= spec.price_peak_return_minimum)
        & (
            prior_price_return_peak_position - prior_volume_peak_position
            >= spec.volume_peak_lead_minimum_sessions
        )
    )
    volume_peak_lead = (
        volume_peak_qualifies
        if spec.volume_peak_lead_enabled and spec.volume_lead_enabled
        else pd.Series(False, index=clean.index)
    )
    momentum_signal = (
        trend_regime
        & (price_to_sma >= spec.price_to_sma_floor)
        & (price_acceleration >= spec.price_acceleration_min)
        & (rsi <= spec.rsi_max)
        & rsi.notna()
        & (close_above_prior_close | ~spec.require_close_above_prior_close)
        & ((sma - close) / sma >= spec.mean_reversion_min)
    )
    raw_signal = momentum_signal & (prior_volume_ratio >= spec.volume_spike_ratio)
    if spec.volume_peak_lead_enabled and spec.volume_lead_enabled:
        raw_signal &= volume_peak_lead
    result = clean.copy()
    result["sma_20"] = sma
    result["rsi_2"] = rsi
    result["prior_volume_average"] = prior_volume_average
    result["volume_spike_ratio"] = volume_spike_ratio
    result["prior_volume_ratio"] = prior_volume_ratio
    result["prior_volume_spike_ratio"] = prior_volume_peak_ratio
    result["prior_volume_peak_ratio"] = prior_volume_peak_ratio
    result["prior_volume_peak_position"] = prior_volume_peak_position
    result["prior_price_return_peak"] = prior_price_return_peak
    result["prior_price_return_peak_position"] = prior_price_return_peak_position
    result["trend_slope_ratio"] = trend_slope_ratio
    result["price_to_sma"] = price_to_sma
    result["price_acceleration"] = price_acceleration
    result["prior_close"] = prior_close
    result["close_above_prior_close"] = close_above_prior_close
    result["trend_regime"] = trend_regime
    result["volume_peak_lead"] = volume_peak_lead
    result["raw_momentum_signal"] = momentum_signal
    result["raw_signal"] = raw_signal.fillna(False).astype(bool)
    return result


def backtest(
    bars: pd.DataFrame,
    *,
    spec: StrategySpec = DEFAULT_SPEC,
    cost: CostModel = BASE_COST,
    reset_at_start: bool = False,
    signal_start: str | pd.Timestamp | None = None,
    signal_end: str | pd.Timestamp | None = None,
) -> BacktestResult:
    """以固定的下一個 open 進場、風控與持有期執行回測。"""

    original_indicators = _execution.indicators
    original_history = _execution._required_history_sessions
    _execution.indicators = indicators
    _execution._required_history_sessions = _required_history_sessions
    try:
        return _execution.backtest(
            bars,
            spec=spec,
            cost=cost,
            reset_at_start=reset_at_start,
            signal_start=signal_start,
            signal_end=signal_end,
        )
    finally:
        _execution.indicators = original_indicators
        _execution._required_history_sessions = original_history


def risk_budget_shares(*args: object, **kwargs: object) -> int:
    """使用共用執行模組的固定風險預算計算。"""

    return _execution.risk_budget_shares(*args, **kwargs)


def qualification_metrics(
    result: BacktestResult,
    *,
    initial_cash: float = 100_000.0,
) -> dict[str, float | int]:
    """從完成交易重算基本績效摘要。"""

    return _execution.qualification_metrics(result, initial_cash=initial_cash)


__all__ = [
    "BASE_COST",
    "BASELINE_SPEC",
    "BacktestResult",
    "CostModel",
    "DEFAULT_SPEC",
    "STRESS_COST",
    "StrategySpec",
    "Trade",
    "_intraday_exit",
    "backtest",
    "indicators",
    "qualification_metrics",
    "risk_budget_shares",
    "validate_bars",
]
