"""TSM 低檔量價背離補充型短線均值回歸研究的可重算核心。

本模組只接受已凍結的日線 OHLCV，不下載資料、不連線券商，也不建立真實委託。

策略保留 v009 原有的「兩階段量先價行」進場路徑：
1. 20 日均線負偏離（Close <= SMA20 * (1 - 0.015)）；
2. 訊號日反轉收紅（Close > prior Close）；
3. 反彈後 2 日 RSI 仍 <= 50；
4. 前 5 個 session 內出現溫和放量（Volume / SMA20(Volume.shift(1)) >= 1.05）。

並在此基礎上增加一條「補充型均值回歸」進場路徑：
1. 最近 5 個交易日內曾出現 20 日布林通道 %B <= 0.25（ddof=0, multiplier=2.0）；
2. 確認日收盤仍低於 20 日均線（Close < SMA20），但不再要求負偏離至少 1.5% 或確認日 %B <= 0.25，不使用 RSI；
3. 量能改善先於價格回升確認：
   每日分數為 Volume * (2 * Close - High - Low) / (High - Low)（High==Low 時為 0）；
   最近 3 日分數合計由非正轉正（score3.shift(1) <= 0 and score3 > 0）作為量能改善事件；
4. 量能改善事件發生時，價格必須接近近期回檔低點：
   Close - Low.rolling(10).min() <= 1.0 * ATR(20)；
   事件參考低點定義為該 3 日分數累積窗口的最低價（Low.rolling(3).min()）；
5. 量能改善後，在 5 個交易日內等待縮量回測：
   回測日成交量低於此前 20 個交易日均量（Volume < SMA20(Volume.shift(1))），且收盤守住事件參考低點（Close >= ref_low）；
   若收盤跌破事件參考低點，事件即刻失效；
   之後收盤高於前一日（Close > prior Close），且收盤低於 20 日均線並滿足最近 5 日曾 %B <= 0.25，於下一交易日開盤進場；
   縮量回測與價格確認可同日成立，但量能改善必須至少早一個交易日。

整合規則：
- 空手且符合資格時，優先採用 v009 訊號；當日不符合 v009，才檢查補充路徑；
- 最多持有一個部位，不加碼、不使用槓桿；
- 沿用 v009 的成本（base 5 bps / 1 bps, stress 20 bps / 2 bps）、
  部位風險（2% pre-entry equity, stop 4%）、停損（-4%）、停利（+4%）、
  持有期（10 個完整 session 後 time exit）、冷卻（5 個 session）與成交順序假設。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal
from math import floor, inf
from typing import Any, Literal

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
    """預先登記的 TSM 候選、消融與 baseline 共用參數。"""

    # 共用指標與 v009 主路徑參數
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

    # 補充型均值回歸路徑參數
    supplemental_path_enabled: bool = True
    supplemental_volume_lead_enabled: bool = True
    bollinger_lookback: int = 20
    bollinger_min_periods: int = 20
    bollinger_std_multiplier: float = 2.0
    bollinger_ddof: int = 0
    bollinger_percent_b_max: float = 0.25
    bollinger_recent_window: int = 5
    volume_score_window: int = 3
    pullback_low_lookback: int = 10
    atr_lookback: int = 20
    atr_min_periods: int = 20
    atr_distance_multiplier: float = 1.0
    observation_window_sessions: int = 5
    ref_low_type: str = "window_3d_low"
    repeat_event_handling: str = "replace"

    # 執行、風控與持有期常數
    cooldown_sessions: int = 5
    target_return: float = 0.04
    stop_return: float = -0.04
    holding_sessions: int = 10
    fold_warmup_sessions: int = 25
    initial_cash: float = 100_000.0
    risk_fraction: float = 0.02

    def with_changes(self, **changes: object) -> StrategySpec:
        """建立明示的 baseline、消融或變體，不修改 frozen candidate。"""

        return replace(self, **changes)


BASE_COST = CostModel(slippage_bps=5.0, fee_bps=1.0)
STRESS_COST = CostModel(slippage_bps=20.0, fee_bps=2.0)
DEFAULT_SPEC = StrategySpec()

# 簡單均值回歸 baseline：關閉成交量、價格反轉與補充路徑
BASELINE_SPEC = DEFAULT_SPEC.with_changes(
    volume_lead_enabled=False,
    require_close_above_prior_close=False,
    supplemental_path_enabled=False,
)

# 僅 v009 路徑（主要比較基準）
V009_ONLY_SPEC = DEFAULT_SPEC.with_changes(
    supplemental_path_enabled=False,
)

# 機制消融：v009 + 移除「量能先改善」條件的補充路徑
WITHOUT_VOLUME_LEAD_SPEC = DEFAULT_SPEC.with_changes(
    supplemental_volume_lead_enabled=False,
)


def _decimal_text(value: int | float) -> str:
    return format(Decimal(str(value)).normalize(), "f")


def signal_definition(spec: StrategySpec = DEFAULT_SPEC) -> dict[str, object]:
    """讓候選文件與 runner 共用完整、可核對的訊號規格。"""

    return {
        "accepted_only_when_flat": True,
        "cooldown": {
            "clock_anchor": "completed-position-exit",
            "completed_session_steps_after_exit": spec.cooldown_sessions,
        },
        "decision_time": "completed-session-close",
        "mean_reversion": {
            "close_vs_sma20_gap_minimum": _decimal_text(spec.mean_reversion_min),
            "rsi_length": spec.rsi_lookback,
            "rsi_maximum": _decimal_text(spec.rsi_max),
            "sma_length": spec.sma_lookback,
        },
        "price_direction_confirmation": {
            "close_above_prior_close": spec.require_close_above_prior_close,
        },
        "supplemental_path": {
            "atr_distance_multiplier": _decimal_text(spec.atr_distance_multiplier),
            "atr_lookback": spec.atr_lookback,
            "bollinger_ddof": spec.bollinger_ddof,
            "bollinger_lookback": spec.bollinger_lookback,
            "bollinger_percent_b_max": _decimal_text(spec.bollinger_percent_b_max),
            "bollinger_recent_window": spec.bollinger_recent_window,
            "bollinger_standard_deviation_multiplier": _decimal_text(spec.bollinger_std_multiplier),
            "enabled": spec.supplemental_path_enabled,
            "event_reference_low_type": spec.ref_low_type,
            "observation_window_sessions": spec.observation_window_sessions,
            "pullback_low_lookback": spec.pullback_low_lookback,
            "retest_volume_lookback": spec.volume_lookback,
            "volume_lead_enabled": spec.supplemental_volume_lead_enabled,
            "volume_score_window": spec.volume_score_window,
        },
        "symbol": "TSM",
        "volume_leads_price": {
            "enabled": spec.volume_lead_enabled,
            "prior_session_window": spec.volume_lead_window,
            "volume_average_length": spec.volume_lookback,
            "volume_ratio_minimum": _decimal_text(spec.volume_spike_ratio),
        },
    }


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
    signal_origin: str = "v009"


@dataclass(frozen=True)
class BacktestResult:
    trades: tuple[Trade, ...]
    accepted_signal_sessions: tuple[pd.Timestamp, ...]
    ending_cash: float
    trade_origins: tuple[str, ...] = field(default_factory=tuple)


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
    """計算所有策略與補充路徑指標；所有指標嚴格只使用當下及過去 session。"""

    clean = validate_bars(bars)
    close = clean["Close"]
    high = clean["High"]
    low = clean["Low"]
    volume = clean["Volume"]

    # SMA 與負偏離
    sma = close.rolling(spec.sma_lookback, min_periods=spec.sma_min_periods).mean()
    mean_reversion_gap = (sma - close) / sma

    # RSI(2)
    rsi = _rsi(close, spec.rsi_lookback, spec.rsi_min_periods)

    # v009 量先特徵（前 5 個 session 內成交量相對於前 20 日均量的倍數）
    prior_volume_average = (
        volume.shift(1)
        .rolling(spec.volume_lookback, min_periods=spec.volume_average_min_periods)
        .mean()
    )
    volume_spike_ratio = volume / prior_volume_average
    prior_volume_spike = (
        volume_spike_ratio.shift(1)
        .rolling(spec.volume_lead_window, min_periods=spec.volume_lead_min_periods)
        .max()
    )

    # 價格回升確認（Close > prior Close）
    prior_close = close.shift(1)
    close_above_prior_close = close > prior_close

    # 布林通道與 %B
    bollinger_std = close.rolling(
        spec.bollinger_lookback, min_periods=spec.bollinger_min_periods
    ).std(ddof=spec.bollinger_ddof)
    bollinger_lower = sma - spec.bollinger_std_multiplier * bollinger_std
    bollinger_upper = sma + spec.bollinger_std_multiplier * bollinger_std
    bandwidth = bollinger_upper - bollinger_lower
    bollinger_percent_b = ((close - bollinger_lower) / bandwidth).where(bollinger_std > 0, np.nan)
    recent_bollinger_oversold = (
        (bollinger_percent_b <= spec.bollinger_percent_b_max)
        .rolling(spec.bollinger_recent_window, min_periods=1)
        .max()
        == 1
    )

    # 每日成交量加權位置分數（Close Location Value * Volume）
    bar_range = high - low
    clv = np.where(bar_range > 0, (2.0 * close - high - low) / bar_range, 0.0)
    daily_volume_score = volume * clv
    score3 = daily_volume_score.rolling(
        spec.volume_score_window, min_periods=spec.volume_score_window
    ).sum()
    volume_turnaround_event = (score3.shift(1) <= 0) & (score3 > 0)

    # ATR(20) 與近期回檔低點
    tr = pd.concat(
        [high - low, (high - prior_close).abs(), (low - prior_close).abs()], axis=1
    ).max(axis=1)
    atr = tr.rolling(spec.atr_lookback, min_periods=spec.atr_min_periods).mean()
    pullback_low = low.rolling(
        spec.pullback_low_lookback, min_periods=spec.pullback_low_lookback
    ).min()
    price_near_pullback_low = (close - pullback_low) <= (spec.atr_distance_multiplier * atr)

    # 組裝結果 DataFrame
    result = clean.copy()
    result["sma_20"] = sma
    result["mean_reversion_gap"] = mean_reversion_gap
    result["rsi_2"] = rsi
    result["volume_spike_ratio"] = volume_spike_ratio
    result["prior_volume_spike_ratio"] = prior_volume_spike
    result["prior_close"] = prior_close
    result["close_above_prior_close"] = close_above_prior_close

    result["bollinger_std"] = bollinger_std
    result["bollinger_lower"] = bollinger_lower
    result["bollinger_upper"] = bollinger_upper
    result["bollinger_percent_b"] = bollinger_percent_b
    result["recent_bollinger_oversold"] = recent_bollinger_oversold

    result["daily_volume_score"] = daily_volume_score
    result["volume_score_3d"] = score3
    result["volume_turnaround_event"] = volume_turnaround_event

    result["atr_20"] = atr
    result["pullback_low_10"] = pullback_low
    result["price_near_pullback_low"] = price_near_pullback_low
    result["prior_volume_average"] = prior_volume_average

    # v009 原生原始訊號
    v009_signal = (
        (mean_reversion_gap >= spec.mean_reversion_min)
        & (rsi <= spec.rsi_max)
    )
    if spec.volume_lead_enabled:
        v009_signal &= prior_volume_spike >= spec.volume_spike_ratio
    if spec.require_close_above_prior_close:
        v009_signal &= close_above_prior_close
    result["v009_raw_signal"] = v009_signal
    # 對單日無狀態檢查（如 synthetic tests），raw_signal 以 v009_raw_signal 為主
    result["raw_signal"] = v009_signal

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
        spec.bollinger_min_periods - 1,
        spec.atr_min_periods - 1,
        spec.pullback_low_lookback - 1,
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
    """以單一 TSM sleeve 執行整合主路徑與補充路徑的確定性回測。

    ``reset_at_start`` 用於每個 Historical Evaluation fold：前 25 個
    session 只暖機，不接受訊號。Development 則把 2013 warmup 與 2014--2018
    合併，並以 ``signal_start``／``signal_end`` 限制正式訊號與完整交易期間。
    """

    if spec.cooldown_sessions < 0 or spec.holding_sessions <= 0:
        raise ValueError("cooldown 與持有期設定不合法")
    frame = indicators(bars, spec)
    cash = float(spec.initial_cash)
    trades: list[Trade] = []
    accepted: list[pd.Timestamp] = []
    trade_origins: list[str] = []

    pending_signal_index: int | None = None
    pending_signal_origin: str | None = None
    last_exit_index: int | None = None
    position: dict[str, Any] | None = None
    time_exit_index: int | None = None

    active_supplemental_event: dict[str, Any] | None = None

    first_signal_index = (
        spec.fold_warmup_sessions if reset_at_start else _required_history_sessions(spec)
    )
    start = pd.Timestamp(signal_start).normalize() if signal_start is not None else None
    end = pd.Timestamp(signal_end).normalize() if signal_end is not None else None
    if start is not None and end is not None and start > end:
        raise ValueError("signal_start 不得晚於 signal_end")

    for index, (session, bar) in enumerate(frame.iterrows()):
        # 1. 檢查持有部位的 time exit（第 10 個完整持有 session 結束後於下一個 open 出場）
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
                    signal_origin=position["origin"],
                )
            )
            trade_origins.append(position["origin"])
            position = None
            time_exit_index = None
            last_exit_index = index

        # 2. 處理已確認訊號在次日開盤的進場執行
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
                    "origin": pending_signal_origin,
                }
                time_exit_index = index + spec.holding_sessions
            pending_signal_index = None
            pending_signal_origin = None

        # 3. 檢查持倉內日內停損／停利
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
                        signal_origin=position["origin"],
                    )
                )
                trade_origins.append(position["origin"])
                position = None
                time_exit_index = None
                last_exit_index = index
            else:
                position["held_sessions"] = int(position["held_sessions"]) + 1

        # 4. 補充路徑事件狀態機更新
        if spec.supplemental_path_enabled:
            if spec.supplemental_volume_lead_enabled:
                # 檢查當日是否觸發量能改善事件
                if bool(bar["volume_turnaround_event"]):
                    if bool(bar["price_near_pullback_low"]):
                        # 決定事件參考低點
                        window_start = max(0, index - spec.volume_score_window + 1)
                        ref_l = float(frame["Low"].iloc[window_start : index + 1].min())
                        if active_supplemental_event is None or spec.repeat_event_handling == "replace":
                            active_supplemental_event = {
                                "event_index": index,
                                "ref_low": ref_l,
                                "retest_seen": False,
                            }

        # 5. 評估補充路徑回測與價格確認
        supplemental_signal = False
        if spec.supplemental_path_enabled:
            c = float(bar["Close"])
            if spec.supplemental_volume_lead_enabled:
                if active_supplemental_event is not None:
                    e_idx = int(active_supplemental_event["event_index"])
                    ref_l = float(active_supplemental_event["ref_low"])
                    if index > e_idx and index <= e_idx + spec.observation_window_sessions:
                        # 守低檢查：若收盤跌破事件參考低點，即刻失效
                        if c < ref_l:
                            active_supplemental_event = None
                        else:
                            # 縮量回測：成交量低於此前 20 日均量
                            is_low_vol = float(bar["Volume"]) < float(bar["prior_volume_average"])
                            if is_low_vol:
                                active_supplemental_event["retest_seen"] = True
                            # 價格確認：收盤守住低點、收盤高於前一日、收盤低於 20MA、近 5 日曾 %B <= 0.25
                            price_confirm = (
                                (c > float(frame["Close"].iloc[index - 1]))
                                and (c < float(bar["sma_20"]))
                                and bool(bar["recent_bollinger_oversold"])
                            )
                            if active_supplemental_event["retest_seen"] and price_confirm:
                                supplemental_signal = True
                                active_supplemental_event = None
                    elif index > e_idx + spec.observation_window_sessions:
                        active_supplemental_event = None
            else:
                # 機制消融：移除量能先改善與事件記憶，直接檢查縮量回測與價格回升
                is_low_vol = float(bar["Volume"]) < float(bar["prior_volume_average"])
                price_confirm = (
                    (c > float(frame["Close"].iloc[index - 1]))
                    and (c < float(bar["sma_20"]))
                    and bool(bar["recent_bollinger_oversold"])
                )
                if is_low_vol and price_confirm:
                    supplemental_signal = True

        # 6. 進場資格檢查與訊號優先序判定
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

        v009_sig = bool(bar["v009_raw_signal"])

        if (
            index >= first_signal_index
            and date_is_eligible
            and enough_time_to_exit
            and lifecycle_within_end
            and position is None
            and pending_signal_index is None
            and cooldown_ready
        ):
            # 優先採用 v009 訊號；未符合 v009 時才檢查補充路徑
            if v009_sig:
                accepted.append(session)
                pending_signal_index = index
                pending_signal_origin = "v009"
            elif supplemental_signal:
                accepted.append(session)
                pending_signal_index = index
                pending_signal_origin = "supplemental"

    return BacktestResult(
        tuple(trades),
        tuple(accepted),
        cash,
        trade_origins=tuple(trade_origins),
    )


def qualification_metrics(
    result: BacktestResult, *, initial_cash: float = 100_000.0
) -> dict[str, float | int]:
    """從已完成交易重算報酬、profit factor 與 realized equity drawdown。"""

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
    """以持倉中的每日 Low 做保守估值，重算持倉內資金壓力。"""

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
    "STRESS_COST",
    "V009_ONLY_SPEC",
    "WITHOUT_VOLUME_LEAD_SPEC",
    "BacktestResult",
    "CostModel",
    "StrategySpec",
    "Trade",
    "backtest",
    "indicators",
    "mark_to_market_drawdown",
    "qualification_metrics",
    "risk_budget_shares",
    "signal_definition",
    "validate_bars",
]
