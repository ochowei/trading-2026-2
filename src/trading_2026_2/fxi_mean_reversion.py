"""FXI 深度回檔短期均值回歸研究的可重算核心。

這個模組不下載資料，也不送出任何真實委託。正式研究只能把已凍結的日線快照
傳入這裡，並由上層研究流程保存結果與 digest。
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
    """已預先登記的候選策略參數。"""

    high_lookback: int = 10
    pullback_min: float = 0.05
    pullback_max: float = 0.12
    williams_lookback: int = 10
    williams_max: float = -80.0
    atr_fast: int = 5
    atr_slow: int = 20
    atr_ratio_min: float = 1.05
    cooldown_sessions: int = 7
    target_return: float = 0.055
    stop_return: float = -0.05
    holding_sessions: int = 20
    fold_warmup_sessions: int = 20
    initial_cash: float = 100_000.0

    def with_changes(self, **changes: object) -> StrategySpec:
        """建立 challenge 用的明示變體，不改動 frozen candidate。"""

        return replace(self, **changes)


BASE_COST = CostModel(slippage_bps=5.0, fee_bps=1.0)
STRESS_COST = CostModel(slippage_bps=20.0, fee_bps=2.0)
DEFAULT_SPEC = StrategySpec()


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


def _wilder_average(values: pd.Series, length: int) -> pd.Series:
    """Wilder moving average；第一個值以最初 ``length`` 筆的算術平均起算。"""

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


def indicators(bars: pd.DataFrame, spec: StrategySpec = DEFAULT_SPEC) -> pd.DataFrame:
    """只以當下及更早 session 計算候選訊號所需指標。"""

    clean = validate_bars(bars)
    previous_close = clean["Close"].shift(1)
    true_range = pd.concat(
        [
            clean["High"] - clean["Low"],
            (clean["High"] - previous_close).abs(),
            (clean["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    high_10 = clean["High"].rolling(spec.high_lookback).max()
    williams_high = clean["High"].rolling(spec.williams_lookback).max()
    williams_low = clean["Low"].rolling(spec.williams_lookback).min()
    williams_range = williams_high - williams_low
    williams_r = -100.0 * (williams_high - clean["Close"]) / williams_range
    williams_r = williams_r.where(williams_range > 0)
    atr_fast = _wilder_average(true_range, spec.atr_fast)
    atr_slow = _wilder_average(true_range, spec.atr_slow)
    result = clean.copy()
    result["high_10"] = high_10
    result["pullback"] = (high_10 - clean["Close"]) / high_10
    result["williams_r_10"] = williams_r
    result["atr_5"] = atr_fast
    result["atr_20"] = atr_slow
    result["atr_ratio"] = atr_fast / atr_slow
    result["raw_signal"] = (
        result["pullback"].between(spec.pullback_min, spec.pullback_max, inclusive="both")
        & (result["williams_r_10"] <= spec.williams_max)
        & (result["atr_ratio"] > spec.atr_ratio_min)
    )
    return result


def _entry_fill(raw_open: float, cost: CostModel) -> float:
    return raw_open * (1.0 + cost.slippage_bps / 10_000.0)


def _exit_fill(raw_price: float, cost: CostModel) -> float:
    return raw_price * (1.0 - cost.slippage_bps / 10_000.0)


def _intraday_exit(
    bar: pd.Series, target: float, stop: float
) -> tuple[float, ExitReason] | None:
    """依 gap 優先、同 session 悲觀 stop 優先的固定規則決定 raw fill。"""

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
    """以一個 FXI sleeve、不得重疊持倉的規則執行確定性回測。

    ``reset_at_start`` 用於 Evaluation 年度 fold 與 2025 replay：前 20 sessions 僅暖機，
    不接受訊號。Development 傳入含 2013 warmup、截至 2018 年底的資料，並以
    ``signal_start="2014-01-01"`` 禁止 warmup 期間接受訊號。
    """

    if spec.cooldown_sessions < 0 or spec.holding_sessions <= 0:
        raise ValueError("cooldown 與持有期設定不合法")
    frame = indicators(bars, spec)
    cash = float(spec.initial_cash)
    trades: list[Trade] = []
    accepted: list[pd.Timestamp] = []
    pending_signal_index: int | None = None
    last_accepted_index: int | None = None
    position: dict[str, object] | None = None
    time_exit_index: int | None = None
    first_signal_index = spec.fold_warmup_sessions if reset_at_start else spec.atr_slow - 1
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
                )
            )
            position = None
            time_exit_index = None

        if pending_signal_index is not None and pending_signal_index + 1 == index:
            raw_entry = float(bar["Open"])
            executed_entry = _entry_fill(raw_entry, cost)
            cash_before_entry = cash
            shares = floor(cash / (executed_entry * (1.0 + cost.fee_bps / 10_000.0)))
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
                        raw_exit_price=raw_exit,
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
            else:
                position["held_sessions"] = int(position["held_sessions"]) + 1

        enough_time_to_exit = index + spec.holding_sessions + 1 < len(frame)
        cooldown_ready = (
            last_accepted_index is None
            or index - last_accepted_index >= spec.cooldown_sessions
        )
        date_is_eligible = (start is None or session >= start) and (
            end is None or session <= end
        )
        if (
            index >= first_signal_index
            and date_is_eligible
            and enough_time_to_exit
            and position is None
            and pending_signal_index is None
            and cooldown_ready
            and bool(bar["raw_signal"])
        ):
            accepted.append(session)
            last_accepted_index = index
            pending_signal_index = index

    return BacktestResult(tuple(trades), tuple(accepted), cash)


def qualification_metrics(
    result: BacktestResult, *, initial_cash: float = 100_000.0
) -> dict[str, float | int]:
    """從已完成交易重算報酬、profit factor 與最大回撤。"""

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


def development_gate_failures(
    base_result: BacktestResult,
    stress_result: BacktestResult,
    *,
    initial_cash: float = 100_000.0,
) -> tuple[str, ...]:
    """依使用者指定的 2014--2018 Development gates 回傳所有失敗原因。"""

    base = qualification_metrics(base_result, initial_cash=initial_cash)
    stress = qualification_metrics(stress_result, initial_cash=initial_cash)
    failures: list[str] = []
    checks = {
        "completed_trades": base["completed_trades"] >= 20,
        "traded_years": base["traded_years"] >= 3,
        "base_return": base["return"] > 0,
        "stress_return": stress["return"] > 0,
        "base_profit_factor": base["profit_factor"] > 1.10,
        "stress_profit_factor": stress["profit_factor"] > 1.00,
        "stress_maximum_drawdown": stress["maximum_drawdown"] <= 0.20,
    }
    for name, passed in checks.items():
        if not passed:
            failures.append(name)
    return tuple(failures)
