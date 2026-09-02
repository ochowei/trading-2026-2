"""只使用 warmup-only 與 Development 快照產生 2% 風險預算候選 evidence。"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from trading_2026_2.fxi_mean_reversion_risk_budget import (
    BASE_COST,
    DEFAULT_RISK_FRACTION,
    STRESS_COST,
    backtest,
    qualification_metrics,
)
from trading_2026_2.fxi_risk2_seedfix import (
    bootstrap,
    evaluate_gate_records,
    path_metrics,
    text,
    trade_rates,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--warmup", type=Path, required=True)
    result.add_argument("--development", type=Path, required=True)
    result.add_argument("--preregistration", type=Path, required=True)
    result.add_argument("--qualification-spec", type=Path, required=True)
    result.add_argument("--trial-inputs", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--acquisition-digest", required=True)
    result.add_argument("--preregistration-digest", required=True)
    result.add_argument("--source-bundle-digest", required=True)
    result.add_argument("--strategy-engine-digest", required=True)
    result.add_argument("--trial-inputs-digest", required=True)
    result.add_argument("--warmup-digest", required=True)
    result.add_argument("--development-digest", required=True)
    return result


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
    preregistration = yaml.safe_load(args.preregistration.read_text(encoding="utf-8"))
    qualification = yaml.safe_load(args.qualification_spec.read_text(encoding="utf-8"))
    trial_inputs = yaml.safe_load(args.trial_inputs.read_text(encoding="utf-8"))
    development_rules = preregistration["eligibility_rules"]["development_gates"]
    if qualification["development"] != development_rules:
        raise RuntimeError("qualification development gates 與 preregistration 不一致")
    bootstrap_registration = preregistration["eligibility_rules"]["development_diagnostics"][
        "block_bootstrap"
    ]
    expected_diagnostics = {
        "block_lengths": bootstrap_registration["block_lengths"],
        "bootstrap_seed": bootstrap_registration["seed"],
        "leave_one_signal_year_out": True,
        "repetitions": bootstrap_registration["repetitions"],
        "seed_application": "exact-same-seed-for-each-block-length",
    }
    if trial_inputs["development_diagnostics"] != expected_diagnostics:
        raise RuntimeError("Trial inputs 的 Development diagnostics 與 preregistration 不一致")
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
    base_bootstrap = [
        bootstrap(
            base_rates,
            block_length,
            repetitions=bootstrap_registration["repetitions"],
            seed=bootstrap_registration["seed"],
        )
        for block_length in bootstrap_registration["block_lengths"]
    ]
    stress_bootstrap = [
        bootstrap(
            stress_rates,
            block_length,
            repetitions=bootstrap_registration["repetitions"],
            seed=bootstrap_registration["seed"],
        )
        for block_length in bootstrap_registration["block_lengths"]
    ]
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

    actuals = {
        "completed_trades": base_metrics["completed_trades"],
        "traded_years": base_metrics["traded_years"],
        "base_return": base_metrics["return"],
        "stress_return": stress_metrics["return"],
        "base_profit_factor": base_metrics["profit_factor"],
        "stress_profit_factor": stress_metrics["profit_factor"],
        "stress_maximum_drawdown": stress_metrics["maximum_drawdown"],
        "maximum_realized_trade_loss_fraction": max_realized_loss,
        "minimum_stress_block_bootstrap_positive_return_ratio": min_stress_bootstrap_positive,
        "maximum_stress_block_bootstrap_drawdown_above_10pct_ratio": (
            max_stress_bootstrap_drawdown
        ),
        "minimum_stress_leave_one_year_out_return": min_stress_loyo_return,
        "minimum_stress_leave_one_year_out_profit_factor": min_stress_loyo_pf,
        "maximum_stress_leave_one_year_out_drawdown": max_stress_loyo_drawdown,
    }
    gates, failures = evaluate_gate_records(actuals, development_rules)

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
        "candidate_id": "fxi-mr-risk2-exitcd7-devverify-v001",
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
