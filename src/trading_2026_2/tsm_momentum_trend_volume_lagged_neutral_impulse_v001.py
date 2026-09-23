"""TSM v004「固定五日延遲的高量中性事件」研究引擎。

候選檢驗訊號日前恰好五個已完成 session 的高量中性日：事件量至少為事件日前
20-session 平均量的 1.50 倍，Open-to-Close 與 Close-to-prior-Close 絕對報酬
都不超過 0.5%；其後四個 session 每日量都不超過事件量的一半，且尚未出現
2% 以上上漲，才由訊號日的趨勢與價格加速確認延遲回應。比較組只移除此序列條件。

模組只處理離線 OHLCV，不下載資料、不連線券商，也不建立真實委託。
"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from trading_2026_2 import tsm_momentum_trend_volume_gap_anchoring_v001 as _execution

BASE_COST=_execution.BASE_COST
STRESS_COST=_execution.STRESS_COST
BacktestResult=_execution.BacktestResult
CostModel=_execution.CostModel
Trade=_execution.Trade
validate_bars=_execution.validate_bars
_intraday_exit=_execution._intraday_exit
_rsi=_execution._rsi
_base_required_history_sessions=_execution._required_history_sessions

@dataclass(frozen=True)
class StrategySpec(_execution.StrategySpec):
    event_lag_sessions:int=5
    event_volume_lookback:int=20
    event_volume_ratio_min:float=1.50
    event_close_prior_abs_max:float=0.005
    event_body_abs_max:float=0.005
    post_event_volume_fraction_max:float=0.50
    intervening_positive_return_max:float=0.02
    lagged_neutral_volume_impulse_enabled:bool=True

DEFAULT_SPEC=StrategySpec(volume_gap_anchoring_enabled=False,volume_lead_enabled=False,lagged_neutral_volume_impulse_enabled=True)
BASELINE_SPEC=DEFAULT_SPEC.with_changes(lagged_neutral_volume_impulse_enabled=False)

def _required_history_sessions(spec:StrategySpec)->int:
    """回傳全部趨勢與固定滯後量能條件就緒的最早 index。"""
    event_history=spec.event_lag_sessions+spec.event_volume_lookback
    return max(_base_required_history_sessions(spec),event_history)

def indicators(bars:pd.DataFrame,spec:StrategySpec=DEFAULT_SPEC)->pd.DataFrame:
    """計算只依賴訊號日以前資料的延遲量能事件與趨勢訊號。"""
    clean=validate_bars(bars)
    close=clean['Close']; open_price=clean['Open']; volume=clean['Volume']
    sma=close.rolling(spec.sma_lookback,min_periods=spec.sma_min_periods).mean()
    rsi=_rsi(close,spec.rsi_lookback,spec.rsi_min_periods)
    prior_close=close.shift(1)
    prior_volume_average=volume.shift(1).rolling(spec.volume_lookback,min_periods=spec.volume_average_min_periods).mean()
    volume_spike_ratio=volume/prior_volume_average.where(prior_volume_average>0.0)
    lag=spec.event_lag_sessions
    post_count=lag-1
    event_volume=volume.shift(lag)
    event_average=volume.shift(lag+1).rolling(spec.event_volume_lookback,min_periods=spec.event_volume_lookback).mean()
    event_volume_ratio=event_volume/event_average.where(event_average>0.0)
    event_close_prior_return=close.shift(lag)/close.shift(lag+1)-1.0
    event_body_return=close.shift(lag)/open_price.shift(lag)-1.0
    post_volume_peak=volume.shift(1).rolling(post_count,min_periods=post_count).max()
    close_return=close.pct_change()
    intervening_positive_return_peak=close_return.shift(1).rolling(post_count,min_periods=post_count).max()
    impulse_ready=(event_volume_ratio.notna() & event_close_prior_return.notna() & event_body_return.notna() & post_volume_peak.notna() & intervening_positive_return_peak.notna())
    impulse=(
        (event_volume_ratio>=spec.event_volume_ratio_min)
        & (event_close_prior_return.abs()<=spec.event_close_prior_abs_max)
        & (event_body_return.abs()<=spec.event_body_abs_max)
        & (post_volume_peak<=event_volume*spec.post_event_volume_fraction_max)
        & (intervening_positive_return_peak<spec.intervening_positive_return_max)
    ).where(impulse_ready)
    if spec.lagged_neutral_volume_impulse_enabled:
        lagged_lead=impulse
    else:
        lagged_lead=pd.Series(True,index=clean.index,dtype=bool)
    trend_slope_ratio=sma/sma.shift(spec.trend_slope_lookback)
    price_to_sma=close/sma
    price_acceleration=close/close.shift(spec.price_acceleration_lookback)-1.0
    close_above_prior_close=close>prior_close
    trend_regime=trend_slope_ratio>=spec.trend_slope_floor
    momentum_signal=(
        trend_regime & (price_to_sma>=spec.price_to_sma_floor)
        & (price_acceleration>=spec.price_acceleration_min)
        & (rsi<=spec.rsi_max) & rsi.notna()
        & (close_above_prior_close | ~spec.require_close_above_prior_close)
        & ((sma-close)/sma>=spec.mean_reversion_min)
    )
    raw_signal=(momentum_signal & lagged_lead.fillna(False)).fillna(False).astype(bool)
    result=clean.copy()
    result['sma_20']=sma;result['rsi_2']=rsi
    result['prior_volume_average']=prior_volume_average;result['volume_spike_ratio']=volume_spike_ratio
    result['lagged_event_volume']=event_volume;result['lagged_event_volume_average']=event_average
    result['lagged_event_volume_ratio']=event_volume_ratio
    result['lagged_event_close_prior_return']=event_close_prior_return
    result['lagged_event_body_return']=event_body_return
    result['post_event_volume_peak']=post_volume_peak
    result['intervening_positive_return_peak']=intervening_positive_return_peak
    result['lagged_neutral_volume_impulse_lead']=lagged_lead.fillna(False).astype(bool)
    result['trend_slope_ratio']=trend_slope_ratio;result['price_to_sma']=price_to_sma
    result['price_acceleration']=price_acceleration;result['prior_close']=prior_close
    result['close_above_prior_close']=close_above_prior_close
    result['trend_regime']=trend_regime
    result['trend_context_signal']=momentum_signal.fillna(False).astype(bool)
    result['raw_signal']=raw_signal
    return result

def backtest(bars:pd.DataFrame,*,spec:StrategySpec=DEFAULT_SPEC,cost:CostModel=BASE_COST,reset_at_start:bool=False,signal_start:str|pd.Timestamp|None=None,signal_end:str|pd.Timestamp|None=None)->BacktestResult:
    """用共用 v004 執行引擎回測，將訊號覆蓋到固定延遲指標。"""
    original_indicators=_execution.indicators
    original_history=_execution._required_history_sessions
    _execution.indicators=indicators
    _execution._required_history_sessions=_required_history_sessions
    try:
        return _execution.backtest(bars,spec=spec,cost=cost,reset_at_start=reset_at_start,signal_start=signal_start,signal_end=signal_end)
    finally:
        _execution.indicators=original_indicators
        _execution._required_history_sessions=original_history

def risk_budget_shares(*args:object,**kwargs:object)->int:
    return _execution.risk_budget_shares(*args,**kwargs)

def qualification_metrics(result:BacktestResult,*,initial_cash:float=100_000.0)->dict[str,float|int]:
    return _execution.qualification_metrics(result,initial_cash=initial_cash)

__all__=['BASE_COST','BASELINE_SPEC','BacktestResult','CostModel','DEFAULT_SPEC','STRESS_COST','StrategySpec','Trade','_intraday_exit','backtest','indicators','qualification_metrics','risk_budget_shares','validate_bars']
