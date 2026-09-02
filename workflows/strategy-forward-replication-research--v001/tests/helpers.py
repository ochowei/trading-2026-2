from __future__ import annotations

from pathlib import Path
from typing import Any

import exchange_calendars as xcals
from validator.canonical_yaml import canonical_digest
from validator.study import WorkflowRules
from writer.service import StudyService

DIGESTS = {
    name: character * 64
    for name, character in {
        "source": "a",
        "candidate": "b",
        "qualification": "c",
        "evaluation_snapshot": "d",
        "replay_snapshot": "e",
        "fold_inventory": "f",
        "artifact": "1",
    }.items()
}


def service(workflow_root: Path, tmp_path: Path) -> StudyService:
    return StudyService(workflow_root, tmp_path / "authority", allow_draft=True)


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
            "development_gates": {
                "completed_trades": {"operator": ">=", "value": 1}
            },
            "minimum_history": "fixed-calendar",
        },
        "selection_rule": {"metric": "development-sharpe", "order": "descending"},
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
        "replay_gates": {},
    }


def development_inputs(
    preregistration_digest: str, source_bundle_digest: str
) -> dict[str, Any]:
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

    base_bootstrap = [
        bootstrap_record(length, "0.010000000000000009") for length in (3, 5)
    ]
    stress_bootstrap = [
        bootstrap_record(length, "0.008000000000000007") for length in (3, 5)
    ]
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
            "by_signal_year": {
                "2014": {"trades": 1, "base_pnl": "100.0", "stress_pnl": "80.0"}
            },
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
            }
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
            for timestamp in calendar.sessions_in_range(
                f"{year}-01-01", f"{year}-12-31"
            )
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


def challenge_evidence(bindings: dict[str, str]) -> dict[str, Any]:
    rules = WorkflowRules(Path(__file__).resolve().parents[1])
    seed_required = set(rules.evidence_requirements["seed_required_challenges"])
    challenges = []
    for index, challenge_id in enumerate(rules.evidence_requirements["required_challenges"]):
        item = {
            "challenge_id": challenge_id,
            "artifact_path": f"evidence/challenges/{challenge_id}.yml",
            "artifact_digest": canonical_digest(challenge_artifact(challenge_id)),
            "bindings": dict(bindings),
            "actual": "2",
            "operator": ">",
            "expected": "1",
        }
        if challenge_id in seed_required:
            item["seed"] = 42 + index
        challenges.append(item)
    return {
        "schema_version": 1,
        "stage": "robustness-challenges",
        "challenges": challenges,
    }


def challenge_artifact(challenge_id: str) -> dict[str, Any]:
    return {"challenge_id": challenge_id, "raw_result": "fixture-result"}


def replay_evidence() -> dict[str, Any]:
    calendar = xcals.get_calendar("XNYS")
    sessions = [
        timestamp.strftime("%Y-%m-%d")
        for timestamp in calendar.sessions_in_range("2025-01-01", "2025-12-31")
    ]
    fills = [
        {
            "fill_id": f"fill-{index}",
            "session": sessions[10 + index],
            "exit_session": sessions[11 + index],
            "proposal_actionable": False,
            "order_type": "LIMIT",
            "base_pnl": "20",
            "stress_pnl": "10",
        }
        for index in range(1, 13)
    ]
    return {
        "schema_version": 1,
        "stage": "retrospective-execution-replay",
        "initial_cash": "10000",
        "expected_sessions": sessions,
        "observed_sessions": sessions,
        "critical_drift_passed": True,
        "stress_drawdown_limit": "0.20",
        "fills": fills,
    }


def terminal_evidence(
    projection: dict[str, Any], outcome: str, reasons: list[str]
) -> dict[str, Any]:
    bindings = {
        "event_chain_head_digest": projection["lifecycle"]["event_chain_head_digest"],
        "workflow_digest": projection["workflow_binding"]["workflow_digest"],
        "policy_set_digest": projection["workflow_binding"]["policy_set_digest"],
        "source_bundle_digest": projection["workflow_binding"]["source_bundle_digest"],
    }
    if projection["preregistration"]["digest"]:
        bindings["preregistration_digest"] = projection["preregistration"]["digest"]
    if projection["trial_registry"]["digest"]:
        bindings["trial_registry_digest"] = projection["trial_registry"]["digest"]
    evidence_names = {
        "development": "development_evidence_digest",
        "candidate-freeze": "candidate_freeze_digest",
        "historical-evaluation": "historical_evaluation_digest",
        "robustness-challenges": "robustness_challenges_digest",
        "retrospective-execution-replay": "retrospective_replay_digest",
        "evidence-unavailable": "evidence_unavailable_digest",
    }
    for evidence_name, binding_name in evidence_names.items():
        if evidence_name in projection["evidence"]:
            bindings[binding_name] = projection["evidence"][evidence_name]
    return {
        "schema_version": 1,
        "outcome": outcome,
        "authority": "retrospectively-supported" if outcome == "pass" else "none",
        "recomputed": True,
        "bindings": bindings,
        "reasons": reasons,
    }


def advance_to_candidate(
    service: StudyService,
    study_id: str = "study-1",
    *,
    selection_rule_digest: str | None = None,
) -> None:
    service.create_study(
        study_id,
        "same-person",
        research_round_id="round-1",
        experiment_family="family-a",
        research_owner="same-person",
        replay_operator="same-person",
        source_bundle={
            "schema_version": 1,
            "files": [{"path": "runner.py", "digest": DIGESTS["source"]}],
        },
    )
    prereg_path, prereg_digest = service.publish_artifact(
        study_id,
        "manifests/preregistration.yml",
        preregistration(),
    )
    service.append_event(
        study_id,
        "preregistration-approved",
        "same-person",
        {"preregistration_path": prereg_path, "preregistration_digest": prereg_digest},
    )
    auth_path, auth_digest = service.publish_artifact(
        study_id,
        "evidence/development-authorization.yml",
        {"authorized": True, "scope": "development-only"},
    )
    service.append_event(
        study_id,
        "development-authorized",
        "same-person",
        {"evidence_path": auth_path, "evidence_digest": auth_digest},
    )
    source_bundle_digest = service.validate(study_id)["workflow_binding"][
        "source_bundle_digest"
    ]
    inputs_path, inputs_digest = service.publish_artifact(
        study_id,
        "manifests/development-trial-inputs.yml",
        development_inputs(prereg_digest, source_bundle_digest),
    )
    evidence_path, evidence_digest = service.publish_artifact(
        study_id,
        "evidence/development.yml",
        development_evidence(prereg_digest, source_bundle_digest, inputs_digest),
    )
    trial = {
        "trial_id": "trial-1",
        "inputs_path": inputs_path,
        "inputs_digest": inputs_digest,
        "development_evidence_path": evidence_path,
        "development_evidence_digest": evidence_digest,
        "status": "completed",
    }
    service.append_event(study_id, "trial-recorded", "same-person", trial)
    registry_digest = canonical_digest({"trials": [trial]})
    service.append_event(
        study_id,
        "trial-registry-frozen",
        "same-person",
        {
            "maximum_trials": 1,
            "recorded_trial_count": 1,
            "complete_family_trial_ids": ["trial-1"],
            "trial_registry_digest": registry_digest,
            "candidate_available": True,
        },
    )
    provenance_path, provenance_digest = service.publish_artifact(
        study_id,
        "evidence/provenance.yml",
        {"status": "verified-clean", "sources": ["development-only"]},
    )
    service.append_event(
        study_id,
        "provenance-audited",
        "same-person",
        {
            "status": "verified-clean",
            "artifact_path": provenance_path,
            "artifact_digest": provenance_digest,
        },
    )
    calendar = xcals.get_calendar("XNYS")
    role_digests = {
        "warmup-only": "7" * 64,
        "development": "8" * 64,
        "quarantine": "9" * 64,
        "historical-evaluation": DIGESTS["evaluation_snapshot"],
        "retrospective-execution-replay": DIGESTS["replay_snapshot"],
    }
    snapshots = []
    for interval in service.rules.workflow["data_intervals"]["intervals"]:
        sessions = [
            timestamp.strftime("%Y-%m-%d")
            for timestamp in calendar.sessions_in_range(
                interval["start_date"], interval["end_date"]
            )
        ]
        snapshots.append(
            {
                "schema_version": 1,
                "role": interval["role"],
                "provider": "yahoo",
                "symbols": ["TEST"],
                "timezone": "America/New_York",
                "calendar": "XNYS",
                "interval": "1d",
                "adjustment_policy": "auto_adjusted",
                "fields": ["open", "high", "low", "close", "volume"],
                "sessions": sessions,
                "data_digest": role_digests[interval["role"]],
            }
        )
    snapshot_path, snapshot_digest = service.publish_artifact(
        study_id,
        "manifests/data-snapshot-set.yml",
        {"schema_version": 1, "snapshots": snapshots},
    )
    selection_path, selection_digest = service.publish_artifact(
        study_id,
        "evidence/selection-evidence.yml",
        {
            "schema_version": 1,
            "ordered_eligible_trial_ids": ["trial-1"],
            "selected_candidate_id": "trial-1",
            "rule_digest": selection_rule_digest
            or canonical_digest(
                {
                    "eligibility_rules": preregistration()["eligibility_rules"],
                    "selection_rule": preregistration()["selection_rule"],
                    "tie_handling": preregistration()["tie_handling"],
                }
            ),
        },
    )
    evaluation_sessions = next(
        snapshot["sessions"]
        for snapshot in snapshots
        if snapshot["role"] == "historical-evaluation"
    )
    fold_inventory_digest = canonical_digest({"sessions": evaluation_sessions})
    service.append_event(
        study_id,
        "candidate-frozen",
        "same-person",
        {
            "selected_candidate_id": "trial-1",
            "baseline_id": "cash-baseline",
            "baseline_family": "cash",
            "baseline_objectively_simpler": True,
            "candidate_digest": DIGESTS["candidate"],
            "trial_registry_digest": registry_digest,
            "qualification_spec_digest": DIGESTS["qualification"],
            "evaluation_snapshot_digest": DIGESTS["evaluation_snapshot"],
            "replay_snapshot_digest": DIGESTS["replay_snapshot"],
            "fold_inventory_digest": fold_inventory_digest,
            "development_evidence_digest": evidence_digest,
            "snapshot_set_path": snapshot_path,
            "snapshot_set_digest": snapshot_digest,
            "selection_evidence_path": selection_path,
            "selection_evidence_digest": selection_digest,
        },
    )
