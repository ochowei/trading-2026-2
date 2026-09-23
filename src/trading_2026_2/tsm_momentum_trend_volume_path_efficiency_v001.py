"""TSM v004 成交量加權方向路徑效率研究引擎。

本模組以訊號日前五個完整交易日為窗，計算成交量相對此前二十日均量加權的
    收盤淨位移絕對值，除以同日隔夜缺口與日內高低區間構成的總價格路徑。
    它測量高量是否伴隨低折返的價格位移；交易方向仍由既有趨勢及價格條件決定。
"""

from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True)
class StrategySpec(_execution.StrategySpec):
    """候選與 baseline 共用的事前固定訊號及執行規格。"""

    volume_path_efficiency_enabled: bool = True
    volume_path_efficiency_minimum: float = 0.20


DEFAULT_SPEC = StrategySpec(
    volume_gap_anchoring_enabled=False,
    volume_lead_enabled=True,
    volume_spike_ratio=1.05,
    volume_path_efficiency_enabled=True,
    volume_path_efficiency_minimum=0.20,
)
BASELINE_SPEC = DEFAULT_SPEC.with_changes(volume_path_efficiency_enabled=False)


def _required_history_sessions(spec: StrategySpec) -> int:
    """回傳所有訊號欄位 ready 的最早 zero-based index。"""

    return max(
        spec.sma_min_periods - 1,
        spec.rsi_min_periods,
        spec.volume_average_min_periods + spec.volume_lead_window,
        spec.sma_min_periods - 1 + spec.trend_slope_lookback,
    )


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """計算趨勢、價格加速及只使用先前五個 session 的方向路徑效率。"""

    clean = validate_bars(bars)
    close = clean["Close"]
    open_price = clean["Open"]
    high = clean["High"]
    low = clean["Low"]
    volume = clean["Volume"]

    sma = close.rolling(spec.sma_lookback, min_periods=spec.sma_min_periods).mean()
    rsi = _rsi(close, spec.rsi_lookback, spec.rsi_min_periods)
    prior_close = close.shift(1)
    prior_volume_average = volume.shift(1).rolling(
        spec.volume_lookback,
        min_periods=spec.volume_average_min_periods,
    ).mean()
    volume_spike_ratio = volume / prior_volume_average
    prior_volume_ratio = volume_spike_ratio.shift(1).rolling(
        spec.volume_lead_window,
        min_periods=spec.volume_lead_min_periods,
    ).mean()

    net_close_progress = close / prior_close - 1.0
    overnight_gap_path = (open_price / prior_close - 1.0).abs()
    intraday_range_path = (high - low) / prior_close
    total_path = overnight_gap_path + intraday_range_path
    weighted_net_progress = volume_spike_ratio * net_close_progress
    weighted_total_path = volume_spike_ratio * total_path
    prior_weighted_net_progress = weighted_net_progress.shift(1).rolling(
        spec.volume_lead_window,
        min_periods=spec.volume_lead_min_periods,
    ).sum()
    prior_weighted_total_path = weighted_total_path.shift(1).rolling(
        spec.volume_lead_window,
        min_periods=spec.volume_lead_min_periods,
    ).sum()
    prior_volume_path_efficiency = prior_weighted_net_progress.abs().div(
        prior_weighted_total_path.where(prior_weighted_total_path > 0)
    )

    trend_slope_ratio = sma / sma.shift(spec.trend_slope_lookback)
    price_to_sma = close / sma
    price_acceleration = close / close.shift(spec.price_acceleration_lookback) - 1.0
    close_above_prior_close = close > prior_close
    trend_regime = trend_slope_ratio >= spec.trend_slope_floor
    volume_ratio_lead = prior_volume_ratio >= spec.volume_spike_ratio
    path_efficiency_lead = (
        prior_volume_path_efficiency >= spec.volume_path_efficiency_minimum
        if spec.volume_path_efficiency_enabled
        else pd.Series(True, index=clean.index)
    )
    volume_lead = volume_ratio_lead if spec.volume_lead_enabled else pd.Series(True, index=clean.index)
    momentum_signal = (
        trend_regime
        & (price_to_sma >= spec.price_to_sma_floor)
        & (price_acceleration >= spec.price_acceleration_min)
        & (rsi <= spec.rsi_max)
        & rsi.notna()
        & (close_above_prior_close | ~spec.require_close_above_prior_close)
        & ((sma - close) / sma >= spec.mean_reversion_min)
    )
    raw_signal = (momentum_signal & volume_lead & path_efficiency_lead).fillna(False).astype(bool)

    result = clean.copy()
    result["sma_20"] = sma
    result["rsi_2"] = rsi
    result["prior_volume_average"] = prior_volume_average
    result["volume_spike_ratio"] = volume_spike_ratio
    result["prior_volume_ratio"] = prior_volume_ratio
    result["net_close_progress"] = net_close_progress
    result["total_price_path"] = total_path
    result["weighted_net_progress"] = weighted_net_progress
    result["weighted_total_path"] = weighted_total_path
    result["prior_weighted_net_progress"] = prior_weighted_net_progress
    result["prior_weighted_total_path"] = prior_weighted_total_path
    result["prior_volume_path_efficiency"] = prior_volume_path_efficiency
    result["trend_slope_ratio"] = trend_slope_ratio
    result["price_to_sma"] = price_to_sma
    result["price_acceleration"] = price_acceleration
    result["prior_close"] = prior_close
    result["close_above_prior_close"] = close_above_prior_close
    result["trend_regime"] = trend_regime
    result["volume_ratio_lead"] = volume_ratio_lead
    result["volume_path_efficiency_lead"] = path_efficiency_lead
    result["volume_lead"] = volume_lead
    result["momentum_setup"] = momentum_signal
    result["raw_signal"] = raw_signal
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
