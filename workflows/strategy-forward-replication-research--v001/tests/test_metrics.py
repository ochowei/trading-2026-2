from __future__ import annotations

import pytest
from helpers import evaluation_evidence
from validator.artifacts import evaluate_historical
from validator.canonical_yaml import load_canonical
from validator.errors import ValidationError
from validator.metrics import validate_study_gates


def test_historical_floor_passes(workflow_root) -> None:
    floors = load_canonical(workflow_root / "rules/workflow-floors.yml")
    metrics, failures = evaluate_historical(
        evaluation_evidence(),
        floors["historical_evaluation"],
    )
    assert failures == []
    assert metrics["completed_trades"] == 20
    assert metrics["traded_folds"] == 5


def test_historical_trade_shortage_is_fail(workflow_root) -> None:
    floors = load_canonical(workflow_root / "rules/workflow-floors.yml")
    evidence = evaluation_evidence()
    evidence["trades"] = evidence["trades"][:19]
    _, failures = evaluate_historical(evidence, floors["historical_evaluation"])
    assert "completed_trades" in failures


def test_study_gate_cannot_relax_workflow_floor(workflow_root) -> None:
    floors = load_canonical(workflow_root / "rules/workflow-floors.yml")
    with pytest.raises(ValidationError, match="寬鬆"):
        validate_study_gates(
            {"completed_trades": {"operator": ">=", "value": 19}},
            floors["historical_evaluation"],
        )


def test_fold_warmup_and_unapproved_order_type_are_rejected(workflow_root) -> None:
    floors = load_canonical(workflow_root / "rules/workflow-floors.yml")
    evidence = evaluation_evidence()
    evidence["trades"][0]["signal_date"] = "2020-01-02"
    evidence["trades"][0]["exit_date"] = "2020-01-03"
    with pytest.raises(ValidationError, match="Warmup"):
        evaluate_historical(
            evidence,
            floors["historical_evaluation"],
            fold_warmup_sessions=2,
            maximum_holding_sessions=5,
        )

    evidence = evaluation_evidence()
    evidence["trades"][0]["order_type"] = "TRAILING_STOP"
    with pytest.raises(ValidationError, match="Proposal Order Type"):
        evaluate_historical(evidence, floors["historical_evaluation"])
