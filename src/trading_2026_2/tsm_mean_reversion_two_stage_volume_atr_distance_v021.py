"""TSM 以 ATR 正規化均線距離的兩階段量先價行均值回歸研究核心。

本模組只接受已凍結的日線 OHLCV，不下載資料、不連線券商，也不建立真實委託。
它沿用 v009 的成交量先行、收盤高於前收、持有期、冷卻、部位風險、停損停利
與成本規則；唯一的訊號變更，是把固定的 SMA(20) 負偏離 1.5% 換成：

    (SMA20_t - Close_t) / ATR14_(t-1) >= 1.0

其中 SMA20 包含訊號日收盤，ATR14 使用 Wilder 平滑。第一個 session 沒有前收，
其真實波幅固定採當日 High-Low；ATR 的第一個值以最初 14 個真實波幅的算術平均
初始化，之後使用 Wilder 遞迴更新。訊號分母永遠是前一日已完成的 ATR；缺值或
非正 ATR 一律不產生訊號。
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
    """候選與描述性 baseline 共用的固定參數。"""

    sma_lookback: int = 20
    sma_min_periods: int = 20
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
    atr_lookback: int = 14
    atr_min_periods: int = 14
    atr_distance_multiplier: float = 1.0
    mean_reversion_mode: Literal["atr-distance", "fixed-gap"] = "atr-distance"
    fixed_gap: float = 0.015
    cooldown_sessions: int = 5
    target_return: float = 0.04
    stop_return: float = -0.04
    holding_sessions: int = 10
    fold_warmup_sessions: int = 25
    initial_cash: float = 100_000.0
    risk_fraction: float = 0.02
    signal_origin: str = "atr-distance"

    def with_changes(self, **changes: object) -> StrategySpec:
        """建立明示的 baseline 或 v009 control，不修改 frozen candidate。"""

        return replace(self, **changes)


BASE_COST = CostModel(slippage_bps=5.0, fee_bps=1.0)
STRESS_COST = CostModel(slippage_bps=20.0, fee_bps=2.0)
DEFAULT_SPEC = StrategySpec()

# Workflow 要求一個較簡單 baseline；它使用 v009 的固定 1.5% 門檻，
# 但移除成交量先行與收盤止跌條件，其他執行規則完全相同。
BASELINE_SPEC = DEFAULT_SPEC.with_changes(
    mean_reversion_mode="fixed-gap",
    volume_lead_enabled=False,
    require_close_above_prior_close=False,
    signal_origin="simple-baseline",
)

# 這是同一份新引擎內的 v009 固定門檻 control，用於逐筆確認只有超跌條件改變。
V009_ONLY_SPEC = DEFAULT_SPEC.with_changes(
    mean_reversion_mode="fixed-gap",
    signal_origin="v009-control",
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
    signal_origin: str = "atr-distance"


@dataclass(frozen=True)
class BacktestResult:
    trades: tuple[Trade, ...]
    accepted_signal_sessions: tuple[pd.Timestamp, ...]
    ending_cash: float


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
        result["High"].lt(result[["Open", "Close", "Low"]].max(axis=1)).any()
        or result["Low"].gt(result[["Open", "Close", "High"]].min(axis=1)).any()
    ):
        raise ValueError("OHLC 高低價關係不合法")
    return result


def _rsi(close: pd.Series, length: int, min_periods: int | None = None) -> pd.Series:
    """沿用 v009 的簡單 rolling mean RSI 與零增減分支。"""

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


def _wilder_average(values: pd.Series, length: int) -> pd.Series:
    """Wilder 平滑：前 length 筆算術平均，之後以 RMA 遞迴更新。"""

    if length <= 0:
        raise ValueError("Wilder 長度必須大於 0")
    source = values.astype(float).to_numpy()
    output = np.full(len(source), np.nan, dtype=float)
    if len(source) < length or np.isnan(source[:length]).any():
        return pd.Series(output, index=values.index, dtype=float)
    output[length - 1] = float(np.mean(source[:length]))
    for index in range(length, len(source)):
        value = source[index]
        if np.isnan(value):
            output[index] = np.nan
        else:
            output[index] = (output[index - 1] * (length - 1) + value) / length
    return pd.Series(output, index=values.index, dtype=float)


def signal_definition(spec: StrategySpec = DEFAULT_SPEC) -> dict[str, object]:
    """由 frozen spec 組出候選 signal 定義，供 runner 做一致性核對。"""

    return {
        "accepted_only_when_flat": True,
        "cooldown": {
            "clock_anchor": "completed-position-exit",
            "completed_session_steps_after_exit": spec.cooldown_sessions,
        },
        "decision_time": "completed-session-close",
        "mean_reversion": {
            "atr_distance_operator": ">=",
            "atr_distance_threshold": "1.0",
            "atr_lookback": spec.atr_lookback,
            "close_distance_formula": "(SMA20_t - Close_t) / ATR14_(t-1)",
            "rsi_length": spec.rsi_lookback,
            "rsi_maximum": format(spec.rsi_max, "g"),
            "sma_includes_signal_close": True,
            "sma_length": spec.sma_lookback,
        },
        "price_direction_confirmation": {
            "close_above_prior_close": spec.require_close_above_prior_close,
        },
        "supplemental_path": {
            "atr_distance_multiplier": format(spec.atr_distance_multiplier, "g"),
            "atr_lookback": spec.atr_lookback,
            "atr_min_periods": spec.atr_min_periods,
            "denominator": "ATR14_(t-1)",
            "role": "replacement-of-v009-sma-gap-not-parallel-entry",
        },
        "symbol": "TSM",
        "volume_leads_price": {
            "enabled": spec.volume_lead_enabled,
            "prior_session_window": spec.volume_lead_window,
            "volume_average_length": spec.volume_lookback,
            "volume_ratio_minimum": format(spec.volume_spike_ratio, "g"),
            "volume_ratio_operator": ">=",
            "volume_shock_is_before_signal": True,
        },
    }


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """只用當下及更早 session 計算訊號，且 ATR 分母只用前一日。"""

    clean = validate_bars(bars)
    close = clean["Close"]
    high = clean["High"]
    low = clean["Low"]
    prior_close = close.shift(1)
    sma = close.rolling(spec.sma_lookback, min_periods=spec.sma_min_periods).mean()
    rsi = _rsi(close, spec.rsi_lookback, spec.rsi_min_periods)
    prior_volume_average = clean["Volume"].shift(1).rolling(
        spec.volume_lookback, min_periods=spec.volume_average_min_periods
    ).mean()
    volume_spike_ratio = clean["Volume"] / prior_volume_average
    prior_volume_spike = volume_spike_ratio.shift(1).rolling(
        spec.volume_lead_window, min_periods=spec.volume_lead_min_periods
    ).max()
    close_above_prior_close = close > prior_close

    # 首日沒有前收，明示以當日 high-low 作為初始化 TR；其後每日納入跳空距離。
    true_range = pd.concat(
        [high - low, (high - prior_close).abs(), (low - prior_close).abs()], axis=1
    ).max(axis=1)
    atr = _wilder_average(true_range, spec.atr_lookback)
    prior_atr = atr.shift(1)
    atr_distance = ((sma - close) / prior_atr).where(prior_atr > 0)
    fixed_gap = ((sma - close) / sma).where(sma > 0)

    if spec.mean_reversion_mode == "atr-distance":
        distance_condition = atr_distance >= spec.atr_distance_multiplier
    elif spec.mean_reversion_mode == "fixed-gap":
        distance_condition = fixed_gap >= spec.fixed_gap
    else:
        raise ValueError(f"未知 mean_reversion_mode: {spec.mean_reversion_mode}")

    raw_signal = distance_condition & (rsi <= spec.rsi_max)
    if spec.volume_lead_enabled:
        raw_signal &= prior_volume_spike >= spec.volume_spike_ratio
    if spec.require_close_above_prior_close:
        raw_signal &= close_above_prior_close
    # 未就緒或 ATR 非正時，無論其他條件如何都不得產生 ATR 候選訊號。
    if spec.mean_reversion_mode == "atr-distance":
        raw_signal &= prior_atr.notna() & (prior_atr > 0)

    result = clean.copy()
    result["sma_20"] = sma
    result["mean_reversion_gap"] = fixed_gap
    result["rsi_2"] = rsi
    result["volume_spike_ratio"] = volume_spike_ratio
    result["prior_volume_spike_ratio"] = prior_volume_spike
    result["prior_close"] = prior_close
    result["close_above_prior_close"] = close_above_prior_close
    result["true_range"] = true_range
    result["atr_14"] = atr
    result["prior_atr_14"] = prior_atr
    result["atr_distance"] = atr_distance
    result["atr_distance_valid"] = prior_atr.notna() & (prior_atr > 0)
    result["fixed_gap_condition"] = fixed_gap >= spec.fixed_gap
    result["distance_condition"] = distance_condition
    result["raw_signal"] = raw_signal.fillna(False)
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
    bar: pd.Series, target: float, stop: float
) -> tuple[float, ExitReason] | None:
    """依 gap 優先、同日悲觀 stop 優先決定 raw fill。"""

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
    """回傳訊號用到的最早完整指標列 zero-based index。"""

    return max(
        spec.sma_min_periods - 1,
        spec.rsi_min_periods,
        spec.volume_average_min_periods + spec.volume_lead_min_periods,
        spec.atr_min_periods - 1,
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
    """以單一不可重疊持倉 sleeve 執行 v009 的確定性交易規則。"""

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
                    signal_origin=spec.signal_origin,
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
                    "held_sessions": 0,
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
                        signal_origin=spec.signal_origin,
                    )
                )
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
    result: BacktestResult, *, initial_cash: float = 100_000.0
) -> dict[str, float | int]:
    """從已完成交易 PnL 重算報酬、PF 與 realized equity drawdown。"""

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
    """以持倉中每個 session 的 Low 與成本後清算價估算壓力回撤。"""

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
                liquidation_fee = trade.shares * liquidation * cost.fee_bps / 10_000.0
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
    "_intraday_exit",
    "_rsi",
    "_wilder_average",
]
