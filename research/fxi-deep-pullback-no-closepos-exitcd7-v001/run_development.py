"""只使用 warmup-only 與 Development 快照產生新候選的原始 evidence。"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from trading_2026_2.fxi_mean_reversion_exit_cooldown import (
    BASE_COST,
    STRESS_COST,
    backtest,
    development_gate_failures,
    qualification_metrics,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--warmup", type=Path, required=True)
    result.add_argument("--development", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--acquisition-digest", required=True)
    result.add_argument("--preregistration-digest", required=True)
    result.add_argument("--source-bundle-digest", required=True)
    result.add_argument("--strategy-engine-digest", required=True)
    result.add_argument("--trial-inputs-digest", required=True)
    result.add_argument("--warmup-digest", required=True)
    result.add_argument("--development-digest", required=True)
    return result


def text(value: float) -> str:
    return str(float(value))


def trade_record(index: int, base_trade, stress_trade) -> dict[str, object]:
    if (
        base_trade.signal_session != stress_trade.signal_session
        or base_trade.entry_session != stress_trade.entry_session
        or base_trade.exit_session != stress_trade.exit_session
        or base_trade.exit_reason != stress_trade.exit_reason
    ):
        raise RuntimeError("base 與 stress 的交易生命週期不一致")
    return {
        "trade_id": f"development-{index:03d}",
        "signal_session": str(base_trade.signal_session.date()),
        "entry_session": str(base_trade.entry_session.date()),
        "exit_session": str(base_trade.exit_session.date()),
        "raw_entry_price": text(base_trade.raw_entry_price),
        "raw_exit_price": text(base_trade.raw_exit_price),
        "exit_reason": base_trade.exit_reason,
        "held_sessions": base_trade.held_sessions,
        "base": {
            "executed_entry_price": text(base_trade.executed_entry_price),
            "executed_exit_price": text(base_trade.executed_exit_price),
            "shares": base_trade.shares,
            "fees": text(base_trade.fees),
            "pnl": text(base_trade.pnl),
        },
        "stress": {
            "executed_entry_price": text(stress_trade.executed_entry_price),
            "executed_exit_price": text(stress_trade.executed_exit_price),
            "shares": stress_trade.shares,
            "fees": text(stress_trade.fees),
            "pnl": text(stress_trade.pnl),
        },
    }


def trade_rates(trades) -> np.ndarray:
    cash = 100_000.0
    rates: list[float] = []
    for trade in trades:
        rates.append(trade.pnl / cash)
        cash += trade.pnl
    return np.asarray(rates)


def path_metrics(rates: np.ndarray) -> tuple[float, float, float]:
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
    profit_factor = gross_profit / gross_loss if gross_loss else float("inf")
    return equity / 100_000.0 - 1.0, profit_factor, maximum_drawdown


def bootstrap(rates: np.ndarray, block_length: int) -> dict[str, object]:
    repetitions = 50_000
    rng = np.random.default_rng(20260902 + block_length)
    count = len(rates)
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
        returns[repetition], profit_factors[repetition], drawdowns[repetition] = values
    return {
        "block_length": block_length,
        "repetitions": repetitions,
        "return_q05_q50_q95": [text(value) for value in np.quantile(returns, [0.05, 0.5, 0.95])],
        "profit_factor_q05_q50_q95": [
            text(value) for value in np.quantile(profit_factors, [0.05, 0.5, 0.95])
        ],
        "maximum_drawdown_q05_q50_q95": [
            text(value) for value in np.quantile(drawdowns, [0.05, 0.5, 0.95])
        ],
        "positive_return_ratio": text(np.mean(returns > 0)),
        "profit_factor_above_one_ratio": text(np.mean(profit_factors > 1)),
        "drawdown_above_20pct_ratio": text(np.mean(drawdowns > 0.20)),
    }


def main() -> int:
    args = parser().parse_args()
    warmup = pd.read_csv(args.warmup, parse_dates=["Date"], index_col="Date")
    development = pd.read_csv(args.development, parse_dates=["Date"], index_col="Date")
    bars = pd.concat([warmup, development])
    run_args = {"signal_start": "2014-01-01", "signal_end": "2018-12-31"}
    base = backtest(bars, cost=BASE_COST, **run_args)
    stress = backtest(bars, cost=STRESS_COST, **run_args)
    base_metrics = qualification_metrics(base)
    stress_metrics = qualification_metrics(stress)
    failures = list(development_gate_failures(base, stress))
    gate_definitions = [
        ("completed_trades", base_metrics["completed_trades"], ">=", 20),
        ("traded_years", base_metrics["traded_years"], ">=", 3),
        ("base_return", base_metrics["return"], ">", 0),
        ("stress_return", stress_metrics["return"], ">", 0),
        ("base_profit_factor", base_metrics["profit_factor"], ">", 1.10),
        ("stress_profit_factor", stress_metrics["profit_factor"], ">", 1.00),
        ("stress_maximum_drawdown", stress_metrics["maximum_drawdown"], "<=", 0.20),
    ]
    gates = [
        {
            "gate": name,
            "actual": actual if isinstance(actual, int) else text(actual),
            "operator": operator,
            "required": required if isinstance(required, int) else text(required),
            "passed": name not in failures,
        }
        for name, actual, operator, required in gate_definitions
    ]
    years: dict[str, dict[str, object]] = defaultdict(
        lambda: {"trades": 0, "base_pnl": 0.0, "stress_pnl": 0.0}
    )
    for base_trade, stress_trade in zip(base.trades, stress.trades, strict=True):
        year = str(base_trade.signal_session.year)
        years[year]["trades"] = int(years[year]["trades"]) + 1
        years[year]["base_pnl"] = float(years[year]["base_pnl"]) + base_trade.pnl
        years[year]["stress_pnl"] = float(years[year]["stress_pnl"]) + stress_trade.pnl
    evidence = {
        "schema_version": 1,
        "stage": "development",
        "candidate_id": "fxi-mr-no-closepos-exitcd7-v001",
        "disposition": "fail" if failures else "pass",
        "failed_gates": failures,
        "network_access_during_run": False,
        "accepted_signal_count": len(base.accepted_signal_sessions),
        "bindings": {
            "acquisition_manifest_digest": args.acquisition_digest,
            "development_data_digest": args.development_digest,
            "preregistration_digest": args.preregistration_digest,
            "source_bundle_digest": args.source_bundle_digest,
            "strategy_engine_digest": args.strategy_engine_digest,
            "trial_inputs_digest": args.trial_inputs_digest,
            "warmup_data_digest": args.warmup_digest,
        },
        "gates": gates,
        "metrics": {
            "base": {key: text(value) if isinstance(value, float) else value for key, value in base_metrics.items()},
            "stress": {
                key: text(value) if isinstance(value, float) else value
                for key, value in stress_metrics.items()
            },
            "trade_count_by_signal_year": {
                year: values["trades"] for year, values in sorted(years.items())
            },
        },
        "diagnostics": {
            "by_signal_year": {
                year: {
                    "trades": values["trades"],
                    "base_pnl": text(float(values["base_pnl"])),
                    "stress_pnl": text(float(values["stress_pnl"])),
                }
                for year, values in sorted(years.items())
            },
            "block_bootstrap": {
                "base": [bootstrap(trade_rates(base.trades), 3), bootstrap(trade_rates(base.trades), 5)],
                "stress": [
                    bootstrap(trade_rates(stress.trades), 3),
                    bootstrap(trade_rates(stress.trades), 5),
                ],
                "gating": False,
            },
        },
        "trades": [
            trade_record(index, base_trade, stress_trade)
            for index, (base_trade, stress_trade) in enumerate(
                zip(base.trades, stress.trades, strict=True), start=1
            )
        ],
    }
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
