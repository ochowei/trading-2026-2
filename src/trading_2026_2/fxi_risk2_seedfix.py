"""FXI risk2 seed-fix Study 的研究程序工具。

策略成交邏輯沿用已凍結的 ``fxi_mean_reversion_risk_budget``；本模組只修正
Development bootstrap seed、完整 gate 重算，以及 Historical Evaluation fold 輸出。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd

from .fxi_mean_reversion_risk_budget import (
    BASE_COST,
    DEFAULT_RISK_FRACTION,
    STRESS_COST,
    backtest,
)


def text(value: float) -> str:
    return str(float(value))


def trade_rates(trades: tuple[Any, ...]) -> np.ndarray:
    equity = 100_000.0
    rates: list[float] = []
    for trade in trades:
        rates.append(trade.pnl / equity)
        equity += trade.pnl
    return np.asarray(rates)


def path_metrics(rates: np.ndarray) -> dict[str, float]:
    equity = 100_000.0
    peak = equity
    gross_profit = 0.0
    gross_loss = 0.0
    maximum_drawdown = 0.0
    for rate in rates:
        pnl = equity * rate
        if pnl > 0:
            gross_profit += pnl
        elif pnl < 0:
            gross_loss -= pnl
        equity += pnl
        peak = max(peak, equity)
        maximum_drawdown = max(maximum_drawdown, (peak - equity) / peak)
    return {
        "return": equity / 100_000.0 - 1.0,
        "profit_factor": gross_profit / gross_loss if gross_loss else float("inf"),
        "maximum_drawdown": maximum_drawdown,
    }


def bootstrap(
    rates: np.ndarray,
    block_length: int,
    *,
    repetitions: int,
    seed: int,
) -> dict[str, object]:
    """每個 block length 都直接使用同一個 preregistered seed。"""

    rng = np.random.default_rng(seed)
    count = len(rates)
    if count == 0:
        raise ValueError("bootstrap 至少需要一筆 Development 交易")
    blocks = (count + block_length - 1) // block_length
    returns = np.empty(repetitions)
    profit_factors = np.empty(repetitions)
    drawdowns = np.empty(repetitions)
    for repetition in range(repetitions):
        starts = rng.integers(0, count, size=blocks)
        indexes = np.concatenate(
            [np.arange(start, start + block_length) % count for start in starts]
        )[:count]
        values = path_metrics(rates[indexes])
        returns[repetition] = values["return"]
        profit_factors[repetition] = values["profit_factor"]
        drawdowns[repetition] = values["maximum_drawdown"]
    return {
        "block_length": block_length,
        "repetitions": repetitions,
        "seed": seed,
        "return_q05_q50_q95": [text(value) for value in np.quantile(returns, [0.05, 0.5, 0.95])],
        "profit_factor_q05_q50_q95": [
            text(value) for value in np.quantile(profit_factors, [0.05, 0.5, 0.95])
        ],
        "maximum_drawdown_q05_q50_q95": [
            text(value) for value in np.quantile(drawdowns, [0.05, 0.5, 0.95])
        ],
        "positive_return_ratio": text(np.mean(returns > 0)),
        "profit_factor_above_one_ratio": text(np.mean(profit_factors > 1)),
        "drawdown_above_10pct_ratio": text(np.mean(drawdowns > 0.10)),
    }


def _compare(actual: str | int | float, operator: str, required: str | int) -> bool:
    left = Decimal(str(actual))
    right = Decimal(str(required))
    operations = {
        ">": left > right,
        ">=": left >= right,
        "<": left < right,
        "<=": left <= right,
    }
    if operator not in operations:
        raise ValueError(f"不支援的 Development gate operator: {operator}")
    return operations[operator]


def evaluate_gate_records(
    actuals: dict[str, str | int | float], rules: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    """以 preregistration 的完整 Development gates 為唯一門檻來源。"""

    if set(actuals) != set(rules):
        missing = sorted(set(rules).difference(actuals))
        extra = sorted(set(actuals).difference(rules))
        raise ValueError(f"Development metrics 與 gates 不一致；缺少={missing}，額外={extra}")
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    for name, rule in rules.items():
        actual = actuals[name]
        passed = _compare(actual, rule["operator"], rule["value"])
        records.append(
            {
                "gate": name,
                "actual": actual if isinstance(actual, int) else text(float(actual)),
                "operator": rule["operator"],
                "required": rule["value"],
                "passed": passed,
            }
        )
        if not passed:
            failures.append(name)
    return records, failures


def historical_evidence(bars: pd.DataFrame, *, family_wise_confidence: str) -> dict[str, Any]:
    """逐年重設狀態，只產生 schema-compliant 的 raw Evaluation trades。"""

    trades: list[dict[str, Any]] = []
    counter = 1
    for year in range(2020, 2025):
        fold = bars.loc[f"{year}-01-01":f"{year}-12-31"]
        base = backtest(
            fold,
            cost=BASE_COST,
            risk_fraction=DEFAULT_RISK_FRACTION,
            reset_at_start=True,
        )
        stress = backtest(
            fold,
            cost=STRESS_COST,
            risk_fraction=DEFAULT_RISK_FRACTION,
            reset_at_start=True,
        )
        if len(base.trades) != len(stress.trades):
            raise RuntimeError("base 與 stress 的 Evaluation 交易數不一致")
        for base_trade, stress_trade in zip(base.trades, stress.trades, strict=True):
            lifecycle = (
                base_trade.signal_session,
                base_trade.entry_session,
                base_trade.exit_session,
                base_trade.exit_reason,
            )
            stress_lifecycle = (
                stress_trade.signal_session,
                stress_trade.entry_session,
                stress_trade.exit_session,
                stress_trade.exit_reason,
            )
            if lifecycle != stress_lifecycle:
                raise RuntimeError("base 與 stress 的 Evaluation 交易生命週期不一致")
            if base_trade.signal_session.year != year or base_trade.exit_session.year != year:
                raise RuntimeError("Evaluation trade 不得跨越 fold")
            trades.append(
                {
                    "trade_id": f"evaluation-{counter:03d}",
                    "fold": year,
                    "signal_date": str(base_trade.signal_session.date()),
                    "exit_date": str(base_trade.exit_session.date()),
                    "order_type": "MARKET",
                    "base_pnl": text(base_trade.pnl),
                    "stress_pnl": text(stress_trade.pnl),
                }
            )
            counter += 1
    return {
        "schema_version": 1,
        "stage": "historical-evaluation",
        "initial_cash": "100000",
        "family_wise_confidence": family_wise_confidence,
        "stress_drawdown_limit": "0.10",
        "trades": trades,
    }


__all__ = [
    "bootstrap",
    "evaluate_gate_records",
    "historical_evidence",
    "path_metrics",
    "text",
    "trade_rates",
]
