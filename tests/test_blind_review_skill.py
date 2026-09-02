from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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


def check(reference: str) -> tuple[int, dict[str, str]]:
    completed = subprocess.run(
        [sys.executable, str(SCOPE_CHECKER), reference],
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
