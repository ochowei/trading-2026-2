from __future__ import annotations

from typing import Any

import exchange_calendars as xcals

DIGESTS = {
    name: character * 64
    for name, character in {
        "source": "a",
        "candidate": "b",
        "qualification": "c",
        "evaluation_snapshot": "d",
        "fold_inventory": "f",
        "artifact": "1",
    }.items()
}


def preregistration() -> dict[str, Any]:
    return {
        "hypothesis": "候選策略在固定歷史日曆下通過不可降低門檻。",
        "complete_candidate_family": ["trial-1"],
        "maximum_trials": 1,
        "eligibility_rules": {
            "development_diagnostics": {
                "block_bootstrap": {
                    "block_lengths": [3, 5],
                    "repetitions": 100,
                    "seed": 42,
                }
            },
            "development_gates": {"completed_trades": {"operator": ">=", "value": 1}},
            "minimum_history": "fixed-calendar",
        },
        "selection_rule": {"metric": "base_return", "order": "descending"},
        "tie_handling": {"method": "stable-trial-id"},
        "baseline_definition": {
            "baseline_id": "cash-baseline",
            "family": "cash",
            "simpler_rule": "zero-signal-parameters",
        },
        "maximum_holding_sessions": 5,
        "fold_warmup_sessions": 2,
        "initial_cash": "10000",
        "evaluation_gates": {},
    }


def development_inputs(preregistration_digest: str, source_bundle_digest: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "candidate_id": "trial-1",
        "preregistration_digest": preregistration_digest,
        "source_bundle_digest": source_bundle_digest,
        "development_diagnostics": {
            "block_lengths": [3, 5],
            "bootstrap_seed": 42,
            "repetitions": 100,
            "seed_application": "exact-same-seed-for-each-block-length",
        },
    }


def development_evidence(
    preregistration_digest: str,
    source_bundle_digest: str,
    trial_inputs_digest: str,
    *,
    seed: int = 42,
) -> dict[str, Any]:
    def bootstrap_record(length: int, return_value: str) -> dict[str, Any]:
        return {
            "block_length": length,
            "repetitions": 100,
            "seed": seed,
            "return_q05_q50_q95": [return_value, return_value, return_value],
            "profit_factor_q05_q50_q95": ["nan", "nan", "nan"],
            "maximum_drawdown_q05_q50_q95": ["0.0", "0.0", "0.0"],
            "positive_return_ratio": "1.0",
            "profit_factor_above_one_ratio": "1.0",
            "drawdown_above_10pct_ratio": "0.0",
        }

    base_bootstrap = [bootstrap_record(length, "0.010000000000000009") for length in (3, 5)]
    stress_bootstrap = [bootstrap_record(length, "0.008000000000000007") for length in (3, 5)]
    return {
        "schema_version": 1,
        "stage": "development",
        "candidate_id": "trial-1",
        "disposition": "pass",
        "failed_gates": [],
        "network_access_during_run": False,
        "accepted_signal_count": 1,
        "bindings": {
            "preregistration_digest": preregistration_digest,
            "source_bundle_digest": source_bundle_digest,
            "trial_inputs_digest": trial_inputs_digest,
        },
        "diagnostics": {
            "by_signal_year": {"2014": {"trades": 1, "base_pnl": "100.0", "stress_pnl": "80.0"}},
            "leave_one_signal_year_out": {
                "base": {
                    "2014": {
                        "omitted_trades": 1,
                        "remaining_trades": 0,
                        "return": "0.0",
                        "profit_factor": "inf",
                        "maximum_drawdown": "0.0",
                    }
                },
                "stress": {
                    "2014": {
                        "omitted_trades": 1,
                        "remaining_trades": 0,
                        "return": "0.0",
                        "profit_factor": "inf",
                        "maximum_drawdown": "0.0",
                    }
                },
                "gating": True,
            },
            "block_bootstrap": {
                "base": base_bootstrap,
                "stress": stress_bootstrap,
                "gating": True,
            },
        },
        "metrics": {
            "base": {
                "completed_trades": 1,
                "maximum_drawdown": "0.0",
                "maximum_realized_trade_loss_fraction": "0.0",
                "profit_factor": "inf",
                "return": "0.01",
                "traded_years": 1,
            },
            "stress": {
                "completed_trades": 1,
                "maximum_drawdown": "0.0",
                "maximum_realized_trade_loss_fraction": "0.0",
                "profit_factor": "inf",
                "return": "0.008",
                "traded_years": 1,
            },
            "trade_count_by_signal_year": {"2014": 1},
        },
        "gates": [
            {
                "gate": "completed_trades",
                "actual": 1,
                "operator": ">=",
                "required": 1,
                "passed": True,
            }
        ],
        "trades": [
            {
                "trade_id": "development-001",
                "signal_session": "2014-01-02",
                "entry_session": "2014-01-03",
                "exit_session": "2014-01-06",
                "exit_reason": "target",
                "held_sessions": 1,
                "base": {
                    "executed_entry_price": "100",
                    "executed_exit_price": "101",
                    "shares": 100,
                    "fees": "0",
                    "pnl": "100",
                    "pnl_fraction_of_pre_entry_equity": "0.01",
                },
                "stress": {
                    "executed_entry_price": "100",
                    "executed_exit_price": "100.8",
                    "shares": 100,
                    "fees": "0",
                    "pnl": "80",
                    "pnl_fraction_of_pre_entry_equity": "0.008",
                },
            }
        ],
    }


def evaluation_evidence() -> dict[str, Any]:
    calendar = xcals.get_calendar("XNYS")
    trades = []
    counter = 1
    for year in range(2020, 2025):
        sessions = [
            timestamp.strftime("%Y-%m-%d")
            for timestamp in calendar.sessions_in_range(f"{year}-01-01", f"{year}-12-31")
        ]
        for session_index in range(20, 24):
            trades.append(
                {
                    "trade_id": f"trade-{counter}",
                    "fold": year,
                    "signal_date": sessions[session_index],
                    "exit_date": sessions[session_index + 1],
                    "order_type": "MARKET",
                    "base_pnl": "100",
                    "stress_pnl": "60",
                }
            )
            counter += 1
    return {
        "schema_version": 1,
        "stage": "historical-evaluation",
        "initial_cash": "10000",
        "family_wise_confidence": "0.95",
        "stress_drawdown_limit": "0.20",
        "trades": trades,
    }
