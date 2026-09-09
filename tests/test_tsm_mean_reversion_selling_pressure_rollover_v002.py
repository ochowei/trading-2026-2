from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import load_canonical

RESEARCH_ROOT = (
    REPOSITORY_ROOT
    / "research"
    / "tsm-mean-reversion-selling-pressure-rollover--v002"
)
RUNNER_PATH = RESEARCH_ROOT / "run_development.py"
RUNNER_SPEC = importlib.util.spec_from_file_location("tsm_selling_pressure_rollover_v002_runner", RUNNER_PATH)
assert RUNNER_SPEC is not None and RUNNER_SPEC.loader is not None
run_development = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(run_development)


def _actual_for_rule(rule: dict[str, object], *, passed: bool) -> object:
    operator = rule["operator"]
    required = rule["value"]
    if operator == "equals":
        return required
    value = Decimal(str(required))
    if passed:
        if operator == ">":
            return str(value + Decimal("1"))
        if operator == "<":
            return str(value - Decimal("1"))
        return str(value)
    if operator in {">", ">="}:
        return str(value - Decimal("1"))
    return str(value + Decimal("1"))


def test_formal_gate_disposition_is_independent_from_research_targets() -> None:
    preregistration = load_canonical(RESEARCH_ROOT / "preregistration.yml")
    formal_rules = preregistration["eligibility_rules"]["development_gates"]
    target_rules = preregistration["eligibility_rules"]["research_targets"]
    evidence = {
        "disposition": "fail",
        "gates": [
            {
                "actual": _actual_for_rule(rule, passed=True),
                "gate": name,
                "operator": rule["operator"],
                "passed": True,
                "required": rule["value"],
            }
            for name, rule in formal_rules.items()
        ],
        "research_target_records": [
            {
                "actual": (
                    [2020, 2021, 2022, 2023, 2024]
                    if name == "evaluation_years"
                    else _actual_for_rule(rule, passed=False)
                ),
                "operator": rule.get("operator", "equals"),
                "passed": name == "evaluation_years",
                "required": rule.get("value", [2020, 2021, 2022, 2023, 2024]),
                "target": name,
            }
            for name, rule in target_rules.items()
        ],
    }

    finalized = run_development.finalize_status(evidence, preregistration)

    assert finalized["disposition"] == "pass"
    assert finalized["failed_gates"] == []
    assert finalized["research_target_failures"] == [
        "maximum_stress_drawdown",
        "minimum_completed_trades",
        "minimum_stress_profit_factor",
        "minimum_stress_return",
    ]
    assert finalized["development_status"]["formal_development_gates"] == {
        "failed": [],
        "status": "passed",
    }
    assert finalized["development_status"]["development_evidence_validity"] == {
        "status": "valid",
        "validated": True,
    }
    assert finalized["candidate_selection_eligible"] is False
    assert finalized["candidate_selection_ineligibility_reasons"] == finalized[
        "research_target_failures"
    ]


def test_contract_freezes_status_producer_and_canonical_runner_path() -> None:
    contract = load_canonical(RESEARCH_ROOT / "implementation-contract.yml")

    assert contract["procedure"]["path"] == (
        "research/tsm-mean-reversion-selling-pressure-rollover--v002/run_development.py"
    )
    assert contract["development_status"] == {
        "candidate_eligibility_field": "candidate_selection_eligible",
        "disposition_scope": "formal_development_gates_only",
        "helper_path": "research/tools/development_status.py",
        "research_target_records_field": "research_target_records",
        "research_target_failures_field": "research_target_failures",
        "schema_path": "research/tools/development-status.schema.yml",
        "validation_function": "validate_development_status_table",
    }


def test_new_runner_does_not_copy_forward_the_prior_research_path() -> None:
    source = (RESEARCH_ROOT / "run_development.py").read_text(encoding="utf-8")

    assert "research/tsm-mean-reversion-selling-pressure-rollover--v001" not in source
    assert run_development.STUDY_ID == "tsm-mean-reversion-selling-pressure-rollover--v002"
    assert run_development.PROCEDURE_PATH.endswith(
        "tsm-mean-reversion-selling-pressure-rollover--v002/run_development.py"
    )
