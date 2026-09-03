"""TSM「量先於價」均值回歸 setup 的 v003 策略介面。

本 Study 延續既有的 20 日均線偏離、RSI(2) 超賣與「過去五個 session
曾有成交量異常」條件，但移除訊號日必須收高於前一個 session 的額外
確認。假說是：成交量先行本身已經提供參與度訊息，若再要求同日收盤
方向，可能把尚未完成止跌但仍有均值回歸優勢的 setup 過度篩掉。

交易執行、成本、風險預算與 baseline 全部沿用已凍結的核心實作，避免
把訊號條件的改變和成交模型的改變混在一起。
"""

from __future__ import annotations

import pandas as pd

from trading_2026_2.tsm_mean_reversion_reversal_trigger_v001 import (
    BASE_COST,
    STRESS_COST,
    BacktestResult,
    CostModel,
    StrategySpec,
    Trade,
    qualification_metrics,
    risk_budget_shares,
    validate_bars,
)
from trading_2026_2.tsm_mean_reversion_reversal_trigger_v001 import (
    BASELINE_SPEC as _PREVIOUS_BASELINE_SPEC,
)
from trading_2026_2.tsm_mean_reversion_reversal_trigger_v001 import (
    DEFAULT_SPEC as _PREVIOUS_DEFAULT_SPEC,
)
from trading_2026_2.tsm_mean_reversion_reversal_trigger_v001 import (
    backtest as _backtest,
)
from trading_2026_2.tsm_mean_reversion_reversal_trigger_v001 import (
    indicators as _indicators,
)

# v003 唯一的候選訊號變更：不再要求訊號日 Close 高於前一日 Close。
DEFAULT_SPEC = _PREVIOUS_DEFAULT_SPEC.with_changes(
    require_close_above_prior_close=False,
)
BASELINE_SPEC = _PREVIOUS_BASELINE_SPEC


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """以 v003 訊號規格計算只依賴當下及過去 session 的指標。"""

    return _indicators(bars, spec=spec)


def backtest(
    bars: pd.DataFrame,
    *,
    spec: StrategySpec = DEFAULT_SPEC,
    cost: CostModel = BASE_COST,
    reset_at_start: bool = False,
    signal_start: str | pd.Timestamp | None = None,
    signal_end: str | pd.Timestamp | None = None,
) -> BacktestResult:
    """用既有、已固定的下一 session open 與持倉生命週期執行回測。"""

    return _backtest(
        bars,
        spec=spec,
        cost=cost,
        reset_at_start=reset_at_start,
        signal_start=signal_start,
        signal_end=signal_end,
    )


__all__ = [
    "BASE_COST",
    "BASELINE_SPEC",
    "DEFAULT_SPEC",
    "STRESS_COST",
    "BacktestResult",
    "CostModel",
    "StrategySpec",
    "Trade",
    "backtest",
    "indicators",
    "qualification_metrics",
    "risk_budget_shares",
    "validate_bars",
]
