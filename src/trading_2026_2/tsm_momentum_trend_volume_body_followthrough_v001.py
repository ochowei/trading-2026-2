"""TSM v004「量能加權日內實體延續」研究引擎。

本模組測試一個與收盤到收盤報酬、隔夜缺口及收盤位置不同的量先價行機制：
訊號日前五個已完成 session 中，成交量是否集中在同日 Open 到 Close 的正向
實體走勢，而且量能加權的日內實體報酬是否高於同窗口的未加權平均。當日仍由
既定趨勢、價格加速與五日量能參與條件確認進場。

所有日內實體指標只使用訊號日前已完成的資料，不讀取訊號日以後的價格；模組
只處理離線 OHLCV，不下載資料、不連線券商，也不建立真實委託。
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

    volume_body_followthrough_enabled: bool = True
    volume_body_return_min: float = 0.0
    volume_body_advantage_min: float = 0.0


DEFAULT_SPEC = StrategySpec(
    volume_gap_anchoring_enabled=False,
    volume_lead_enabled=True,
    volume_spike_ratio=1.05,
    volume_body_followthrough_enabled=True,
    volume_body_return_min=0.0,
    volume_body_advantage_min=0.0,
)
BASELINE_SPEC = DEFAULT_SPEC.with_changes(volume_body_followthrough_enabled=False)


def _required_history_sessions(spec: StrategySpec) -> int:
    """回傳所有指標 ready 的最早 zero-based index。"""

    return max(
        spec.sma_min_periods - 1,
        spec.rsi_min_periods,
        spec.volume_average_min_periods + spec.volume_lead_window,
        spec.sma_min_periods - 1 + spec.trend_slope_lookback,
        spec.volume_lead_window + 1,
    )


def indicators(
    bars: pd.DataFrame,
    spec: StrategySpec = DEFAULT_SPEC,
) -> pd.DataFrame:
    """計算只使用訊號日前資料的趨勢、價格、量能與日內實體指標。"""

    clean = validate_bars(bars)
    close = clean["Close"]
    open_price = clean["Open"]
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

    # 日內實體只看同一 session 的 Open 到 Close，並在訊號日之前完成。
    body_return = close / open_price - 1.0
    prior_volume_sum = volume.shift(1).rolling(
        spec.volume_lead_window,
        min_periods=spec.volume_lead_min_periods,
    ).sum()
    prior_volume_body_return = (
        (body_return * volume).shift(1).rolling(
            spec.volume_lead_window,
            min_periods=spec.volume_lead_min_periods,
        ).sum()
        / prior_volume_sum
    )
    prior_unweighted_body_return = body_return.shift(1).rolling(
        spec.volume_lead_window,
        min_periods=spec.volume_lead_min_periods,
    ).mean()
    prior_volume_body_advantage = (
        prior_volume_body_return - prior_unweighted_body_return
    )
    body_ready = (
        prior_volume_ratio.notna()
        & prior_volume_body_return.notna()
        & prior_unweighted_body_return.notna()
        & prior_volume_body_advantage.notna()
    )
    prior_volume_ratio = prior_volume_ratio.where(body_ready)
    prior_volume_body_return = prior_volume_body_return.where(body_ready)
    prior_unweighted_body_return = prior_unweighted_body_return.where(body_ready)
    prior_volume_body_advantage = prior_volume_body_advantage.where(body_ready)

    trend_slope_ratio = sma / sma.shift(spec.trend_slope_lookback)
    price_to_sma = close / sma
    price_acceleration = close / close.shift(spec.price_acceleration_lookback) - 1.0
    close_above_prior_close = close > prior_close
    trend_regime = trend_slope_ratio >= spec.trend_slope_floor
    volume_ratio_lead = prior_volume_ratio >= spec.volume_spike_ratio
    volume_body_followthrough_lead = (
        (
            (prior_volume_body_return >= spec.volume_body_return_min)
            & (
                prior_volume_body_advantage
                >= spec.volume_body_advantage_min
            )
        )
        if spec.volume_body_followthrough_enabled
        else pd.Series(True, index=clean.index)
    )
    volume_lead = (
        volume_ratio_lead & volume_body_followthrough_lead
        if spec.volume_lead_enabled
        else pd.Series(True, index=clean.index)
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
    raw_signal = (momentum_signal & volume_lead).fillna(False).astype(bool)

    result = clean.copy()
    result["sma_20"] = sma
    result["rsi_2"] = rsi
    result["prior_volume_average"] = prior_volume_average
    result["volume_spike_ratio"] = volume_spike_ratio
    result["prior_volume_ratio"] = prior_volume_ratio
    result["intraday_body_return"] = body_return
    result["prior_volume_body_return"] = prior_volume_body_return
    result["prior_unweighted_body_return"] = prior_unweighted_body_return
    result["prior_volume_body_advantage"] = prior_volume_body_advantage
    result["trend_slope_ratio"] = trend_slope_ratio
    result["price_to_sma"] = price_to_sma
    result["price_acceleration"] = price_acceleration
    result["prior_close"] = prior_close
    result["close_above_prior_close"] = close_above_prior_close
    result["trend_regime"] = trend_regime
    result["volume_ratio_lead"] = volume_ratio_lead
    result["volume_body_followthrough_lead"] = volume_body_followthrough_lead
    result["volume_lead"] = volume_lead
    result["raw_momentum_signal"] = momentum_signal
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
