from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import canonical_bytes, load_canonical  # noqa: E402

from research.tools.development_status import (  # noqa: E402
    blind_review_status,
    build_development_evidence_failure_status,
    finalize_development_evidence,
    independent_stage_status,
    main,
    validate_development_status_table,
)

PREREGISTRATION = {
    "eligibility_rules": {
        "development_gates": {
            "completed_trades": {"operator": ">=", "value": 1},
        },
        "research_targets": {
            "minimum_completed_trades": {"operator": ">=", "value": 2},
        },
    },
}


def _synthetic_evidence() -> dict[str, object]:
    return {
        # 模擬舊 runner 把 research target 失敗誤塞進 disposition；finalizer 必須重算。
        "disposition": "fail",
        "gates": [
            {
                "actual": 1,
                "gate": "completed_trades",
                "operator": ">=",
                "passed": True,
                "required": 1,
            }
        ],
        "research_target_records": [
            {
                "actual": 1,
                "operator": ">=",
                "passed": False,
                "required": 2,
                "target": "minimum_completed_trades",
            }
        ],
    }


def test_formal_gates_can_pass_while_research_target_fails(tmp_path: Path) -> None:
    evidence = finalize_development_evidence(_synthetic_evidence(), PREREGISTRATION)
    development_path = tmp_path / "evidence" / "development.yml"
    development_path.parent.mkdir()
    development_path.write_bytes(canonical_bytes(evidence))

    loaded = load_canonical(development_path)
    status = validate_development_status_table(loaded, PREREGISTRATION)

    assert loaded["disposition"] == "pass"
    assert loaded["failed_gates"] == []
    assert loaded["research_target_failures"] == ["minimum_completed_trades"]
    assert status["formal_development_gates"] == {"failed": [], "status": "passed"}
    assert status["research_targets"] == {
        "failed": ["minimum_completed_trades"],
        "status": "failed",
    }
    assert status["development_evidence_validity"] == {
        "status": "valid",
        "validated": True,
    }
    assert status["candidate_freeze_eligibility"]["eligible"] is False


def test_blind_review_is_independent_from_historical_status() -> None:
    development = finalize_development_evidence(_synthetic_evidence(), PREREGISTRATION)

    stage = independent_stage_status(
        development["development_status"],
        historical_evaluation_status="not_started",
        study_terminal_status="terminal",
    )

    assert stage["historical_evaluation"]["status"] == "not_started"
    assert stage["study_terminal"]["status"] == "terminal"
    assert stage["blind_review"]["eligible"] is True
    assert stage["blind_review"]["eligibility_basis"] == "explicit-outcome-exposure-only"
    assert blind_review_status(
        development_evidence_available=True,
        formal_evaluation_exposed=False,
        outcome_bearing_terminal_exposed=False,
    )["eligible"] is True


def test_exposed_outcome_blocks_blind_review_even_when_other_stages_are_separate() -> None:
    result = blind_review_status(
        development_evidence_available=False,
        formal_evaluation_exposed=True,
    )

    assert result == {
        "eligible": False,
        "reasons": ["formal_evaluation_exposed"],
        "status": "blocked-by-exposed-outcome",
    }


def test_missing_development_evidence_is_reported_without_blocking_blind_review() -> None:
    development = build_development_evidence_failure_status(
        PREREGISTRATION,
        evidence_status="unavailable",
        reason="synthetic Development evidence is missing",
    )
    stage = independent_stage_status(
        development,
        historical_evaluation_status="not_started",
        development_evidence_available=False,
    )

    assert stage["development"]["development_evidence_validity"]["status"] == "unavailable"
    assert stage["blind_review"]["eligible"] is True
    assert stage["blind_review"]["status"] == "eligible-with-development-evidence-unavailable"
    assert stage["historical_evaluation"]["status"] == "not_started"


def test_status_cli_keeps_missing_evidence_separate_from_blind_review(
    tmp_path: Path, capsys: object
) -> None:
    preregistration_path = tmp_path / "preregistration.yml"
    preregistration_path.write_bytes(canonical_bytes(PREREGISTRATION))

    returncode = main(
        [
            "--evidence",
            str(tmp_path / "missing-development.yml"),
            "--preregistration",
            str(preregistration_path),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert returncode == 1
    assert output["stage_status"]["development"]["development_evidence_validity"]["status"] == (
        "unavailable"
    )
    assert output["stage_status"]["blind_review"]["eligible"] is True
    assert (
        output["stage_status"]["blind_review"]["status"]
        == "eligible-with-development-evidence-unavailable"
    )


def test_repairable_evidence_failure_is_not_terminal() -> None:
    status = build_development_evidence_failure_status(
        PREREGISTRATION,
        evidence_status="needs-repair",
        reason="synthetic digest mismatch",
    )

    assert status["development_evidence_validity"] == {
        "reason": "synthetic digest mismatch",
        "status": "needs-repair",
        "validated": False,
    }
    assert status["candidate_freeze_eligibility"]["eligible"] is False
    assert status["candidate_freeze_eligibility"]["reasons"] == [
        "development_evidence_needs-repair"
    ]
