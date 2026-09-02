"""只使用 warmup-only 與 Development 快照產生 2% 風險預算候選 evidence。"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from trading_2026_2.fxi_mean_reversion_risk_budget import (
    BASE_COST,
    DEFAULT_RISK_FRACTION,
    STRESS_COST,
    backtest,
    qualification_metrics,
)

BOOTSTRAP_REPETITIONS = 50_000
BOOTSTRAP_SEED = 20260904


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


def trade_rates(trades) -> np.ndarray:
    cash = 100_000.0
    rates: list[float] = []
    for trade in trades:
        rates.append(trade.pnl / cash)
        cash += trade.pnl
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
    profit_factor = gross_profit / gross_loss if gross_loss else float("inf")
    return {
        "return": equity / 100_000.0 - 1.0,
        "profit_factor": profit_factor,
        "maximum_drawdown": maximum_drawdown,
    }


def bootstrap(rates: np.ndarray, block_length: int) -> dict[str, object]:
    rng = np.random.default_rng(BOOTSTRAP_SEED + block_length)
    count = len(rates)
    blocks = (count + block_length - 1) // block_length
    returns = np.empty(BOOTSTRAP_REPETITIONS)
    profit_factors = np.empty(BOOTSTRAP_REPETITIONS)
    drawdowns = np.empty(BOOTSTRAP_REPETITIONS)
    for repetition in range(BOOTSTRAP_REPETITIONS):
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
        "repetitions": BOOTSTRAP_REPETITIONS,
        "seed": BOOTSTRAP_SEED + block_length,
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


def leave_one_signal_year_out(trades) -> dict[str, dict[str, str | int]]:
    rates = trade_rates(trades)
    years = np.asarray([trade.signal_session.year for trade in trades])
    result: dict[str, dict[str, str | int]] = {}
    for year in sorted(set(years)):
        kept = rates[years != year]
        values = path_metrics(kept)
        result[str(year)] = {
            "omitted_trades": int(np.sum(years == year)),
            "remaining_trades": int(np.sum(years != year)),
            "return": text(values["return"]),
            "profit_factor": text(values["profit_factor"]),
            "maximum_drawdown": text(values["maximum_drawdown"]),
        }
    return result


def maximum_loss_fraction(trades) -> float:
    rates = trade_rates(trades)
    return max((float(-rate) for rate in rates if rate < 0), default=0.0)


def trade_record(
    index: int,
    base_trade,
    stress_trade,
    base_rate: float,
    stress_rate: float,
) -> dict[str, object]:
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
            "pnl_fraction_of_pre_entry_equity": text(base_rate),
        },
        "stress": {
            "executed_entry_price": text(stress_trade.executed_entry_price),
            "executed_exit_price": text(stress_trade.executed_exit_price),
            "shares": stress_trade.shares,
            "fees": text(stress_trade.fees),
            "pnl": text(stress_trade.pnl),
            "pnl_fraction_of_pre_entry_equity": text(stress_rate),
        },
    }


def main() -> int:
    args = parser().parse_args()
    warmup = pd.read_csv(args.warmup, parse_dates=["Date"], index_col="Date")
    development = pd.read_csv(args.development, parse_dates=["Date"], index_col="Date")
    bars = pd.concat([warmup, development])
    run_args = {
        "signal_start": "2014-01-01",
        "signal_end": "2018-12-31",
        "risk_fraction": DEFAULT_RISK_FRACTION,
    }
    base = backtest(bars, cost=BASE_COST, **run_args)
    stress = backtest(bars, cost=STRESS_COST, **run_args)
    base_metrics = qualification_metrics(base)
    stress_metrics = qualification_metrics(stress)
    base_rates = trade_rates(base.trades)
    stress_rates = trade_rates(stress.trades)
    base_bootstrap = [bootstrap(base_rates, 3), bootstrap(base_rates, 5)]
    stress_bootstrap = [bootstrap(stress_rates, 3), bootstrap(stress_rates, 5)]
    base_loyo = leave_one_signal_year_out(base.trades)
    stress_loyo = leave_one_signal_year_out(stress.trades)

    max_realized_loss = max(
        maximum_loss_fraction(base.trades), maximum_loss_fraction(stress.trades)
    )
    min_stress_bootstrap_positive = min(
        float(result["positive_return_ratio"]) for result in stress_bootstrap
    )
    max_stress_bootstrap_drawdown = max(
        float(result["drawdown_above_10pct_ratio"]) for result in stress_bootstrap
    )
    min_stress_loyo_return = min(float(result["return"]) for result in stress_loyo.values())
    min_stress_loyo_pf = min(float(result["profit_factor"]) for result in stress_loyo.values())
    max_stress_loyo_drawdown = max(
        float(result["maximum_drawdown"]) for result in stress_loyo.values()
    )

    checks = [
        (
            "completed_trades",
            base_metrics["completed_trades"],
            ">=",
            20,
            base_metrics["completed_trades"] >= 20,
        ),
        ("traded_years", base_metrics["traded_years"], ">=", 3, base_metrics["traded_years"] >= 3),
        ("base_return", base_metrics["return"], ">", 0.0, base_metrics["return"] > 0),
        ("stress_return", stress_metrics["return"], ">", 0.0, stress_metrics["return"] > 0),
        (
            "base_profit_factor",
            base_metrics["profit_factor"],
            ">",
            1.10,
            base_metrics["profit_factor"] > 1.10,
        ),
        (
            "stress_profit_factor",
            stress_metrics["profit_factor"],
            ">",
            1.00,
            stress_metrics["profit_factor"] > 1.00,
        ),
        (
            "stress_maximum_drawdown",
            stress_metrics["maximum_drawdown"],
            "<=",
            0.10,
            stress_metrics["maximum_drawdown"] <= 0.10,
        ),
        (
            "maximum_realized_trade_loss_fraction",
            max_realized_loss,
            "<=",
            0.04,
            max_realized_loss <= 0.04,
        ),
        (
            "minimum_stress_block_bootstrap_positive_return_ratio",
            min_stress_bootstrap_positive,
            ">=",
            0.80,
            min_stress_bootstrap_positive >= 0.80,
        ),
        (
            "maximum_stress_block_bootstrap_drawdown_above_10pct_ratio",
            max_stress_bootstrap_drawdown,
            "<=",
            0.10,
            max_stress_bootstrap_drawdown <= 0.10,
        ),
        (
            "minimum_stress_leave_one_year_out_return",
            min_stress_loyo_return,
            ">",
            0.0,
            min_stress_loyo_return > 0,
        ),
        (
            "minimum_stress_leave_one_year_out_profit_factor",
            min_stress_loyo_pf,
            ">",
            1.00,
            min_stress_loyo_pf > 1.00,
        ),
        (
            "maximum_stress_leave_one_year_out_drawdown",
            max_stress_loyo_drawdown,
            "<=",
            0.10,
            max_stress_loyo_drawdown <= 0.10,
        ),
    ]
    failures = [name for name, _actual, _operator, _required, passed in checks if not passed]
    gates = [
        {
            "gate": name,
            "actual": actual if isinstance(actual, int) else text(actual),
            "operator": operator,
            "required": required if isinstance(required, int) else text(required),
            "passed": passed,
        }
        for name, actual, operator, required, passed in checks
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
        "candidate_id": "fxi-mr-risk2-exitcd7-v001",
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
            "base": {
                **{
                    key: text(value) if isinstance(value, float) else value
                    for key, value in base_metrics.items()
                },
                "maximum_realized_trade_loss_fraction": text(maximum_loss_fraction(base.trades)),
            },
            "stress": {
                **{
                    key: text(value) if isinstance(value, float) else value
                    for key, value in stress_metrics.items()
                },
                "maximum_realized_trade_loss_fraction": text(maximum_loss_fraction(stress.trades)),
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
            "leave_one_signal_year_out": {
                "base": base_loyo,
                "stress": stress_loyo,
                "gating": True,
            },
            "block_bootstrap": {
                "base": base_bootstrap,
                "stress": stress_bootstrap,
                "gating": True,
            },
        },
        "trades": [
            trade_record(index, base_trade, stress_trade, base_rate, stress_rate)
            for index, (base_trade, stress_trade, base_rate, stress_rate) in enumerate(
                zip(base.trades, stress.trades, base_rates, stress_rates, strict=True), start=1
            )
        ],
    }
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
