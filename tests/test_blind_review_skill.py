from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCOPE_CHECKER = (
    REPOSITORY_ROOT
    / ".agents"
    / "skills"
    / "blind-review-strategy-study"
    / "scripts"
    / "check_scope.py"
)
STUDY_ID = "fxi-deep-pullback-no-closepos-cd7-v001"


def check(reference: str, *arguments: str) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, str(SCOPE_CHECKER), reference, *arguments],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, json.loads(completed.stdout)


def test_scope_checker_accepts_direct_v001_study() -> None:
    returncode, result = check(STUDY_ID)

    assert returncode == 0
    assert result["status"] == "eligible"
    assert result["workflow_version"] == "v001"
    assert result["study_id"] == STUDY_ID


def test_scope_checker_rejects_research_copy() -> None:
    returncode, result = check(f"research/{STUDY_ID}")

    assert returncode == 2
    assert result["status"] == "rejected"


def test_scope_checker_rejects_study_file() -> None:
    reference = (
        "workflows/strategy-forward-replication-research--v001/"
        f"studies/{STUDY_ID}/study.yml"
    )
    returncode, result = check(reference)

    assert returncode == 2
    assert result["status"] == "rejected"


def test_scope_checker_rejects_other_directory() -> None:
    returncode, result = check("workflows/strategy-forward-replication-research--v001")

    assert returncode == 2
    assert result["status"] == "rejected"


def _synthetic_study(tmp_path: Path, *, development_evidence: bool = False) -> Path:
    workflow = tmp_path / "workflows" / "strategy-forward-replication-research--v001"
    study = workflow / "studies" / "synthetic-blind-review-v001"
    (study / "manifests").mkdir(parents=True)
    (study / "manifests" / "preregistration.yml").write_text("schema_version: v001\n")
    (study / "manifests" / "candidate-definition.yml").write_text("schema_version: v001\n")
    if development_evidence:
        (study / "evidence").mkdir()
        (study / "evidence" / "development.yml").write_text("stage: Development\n")
    return study


def test_scope_checker_allows_blind_review_without_development_evidence(
    tmp_path: Path,
) -> None:
    study = _synthetic_study(tmp_path)

    returncode, result = check(
        str(study),
        "--repository-root",
        str(tmp_path),
    )

    assert returncode == 0
    assert result["blind_review_eligible"] is True
    assert result["blind_review_status"] == "eligible-with-development-evidence-unavailable"
    assert result["development_evidence_status"] == "unavailable"
    assert result["historical_evaluation_status"] == "not_inspected"
    assert result["study_terminal_status"] == "not_inspected"


def test_scope_checker_does_not_read_terminal_or_historical_status(tmp_path: Path) -> None:
    study = _synthetic_study(tmp_path, development_evidence=True)
    (study / "study.yml").write_text("lifecycle: terminal\nhistorical_evaluation_status: not_started\n")
    (study / "events").mkdir()
    (study / "events" / "000001.yml").write_text("event_type: study-terminal\n")

    returncode, result = check(
        str(study),
        "--repository-root",
        str(tmp_path),
    )

    assert returncode == 0
    assert result["blind_review_eligible"] is True
    assert result["historical_evaluation_status"] == "not_inspected"
    assert result["study_terminal_status"] == "not_inspected"


def test_scope_checker_blocks_only_explicit_outcome_exposure(tmp_path: Path) -> None:
    study = _synthetic_study(tmp_path)

    returncode, result = check(
        str(study),
        "--repository-root",
        str(tmp_path),
        "--outcome-bearing-terminal-exposed",
    )

    assert returncode == 2
    assert result["status"] == "rejected"
    assert result["blind_review_eligible"] is False
    assert result["blind_review_status"] == "blocked-by-exposed-outcome"
    assert result["historical_evaluation_status"] == "not_inspected"
    assert result["study_terminal_status"] == "not_inspected"
    assert result["blind_review_eligibility_basis"] == "explicit-outcome-exposure-only"
