from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
NEW_STUDY_CHECKER = (
    REPOSITORY_ROOT
    / ".agents"
    / "skills"
    / "build-strategy-study-to-freeze"
    / "scripts"
    / "check_new_study.py"
)
FROZEN_CHECKER = (
    REPOSITORY_ROOT
    / ".agents"
    / "skills"
    / "run-strategy-historical-evaluation"
    / "scripts"
    / "check_candidate_frozen.py"
)
RECOMPUTE_EVALUATION = (
    REPOSITORY_ROOT
    / ".agents"
    / "skills"
    / "run-strategy-historical-evaluation"
    / "scripts"
    / "recompute_historical_evaluation.py"
)


def run(script: Path, *arguments: str) -> tuple[int, dict[str, object]]:
    completed = subprocess.run(
        [sys.executable, str(script), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, json.loads(completed.stdout)


def minimal_repository(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    workflow = root / "workflows" / "strategy-forward-replication-research--v001"
    workflow.mkdir(parents=True)
    (workflow / "release.yml").write_text("schema_version: 1\n", encoding="utf-8")
    return root


def frozen_study(root: Path, study_id: str = "demo-study-v001") -> Path:
    workflow = root / "workflows" / "strategy-forward-replication-research--v001"
    study = workflow / "studies" / study_id
    events = study / "events"
    manifests = study / "manifests"
    events.mkdir(parents=True)
    manifests.mkdir()
    event_types = [
        "study-created",
        "preregistration-approved",
        "development-authorized",
        "trial-recorded",
        "trial-registry-frozen",
        "provenance-audited",
        "candidate-frozen",
    ]
    for index, event_type in enumerate(event_types, start=1):
        (events / f"{index:06d}-{event_type}.yml").write_text("schema_version: 1\n")

    runner = root / "research" / study_id / "run_historical_evaluation.py"
    runner.parent.mkdir(parents=True)
    runner.write_text("print('synthetic runner')\n", encoding="utf-8")
    digest = hashlib.sha256(runner.read_bytes()).hexdigest()
    (manifests / "source-bundle.yml").write_text(
        f"files:\n  - digest: {digest}\n    path: research/{study_id}/run_historical_evaluation.py\n"
        "schema_version: 1\n",
        encoding="utf-8",
    )
    for name in (
        "preregistration.yml",
        "candidate-definition.yml",
        "qualification-spec.yml",
        "data-snapshot-set.yml",
    ):
        (manifests / name).write_text("schema_version: 1\n", encoding="utf-8")
    return study


def test_new_study_checker_accepts_unused_id(tmp_path: Path) -> None:
    root = minimal_repository(tmp_path)
    returncode, result = run(
        NEW_STUDY_CHECKER,
        "new-study-v001",
        "--repository-root",
        str(root),
    )
    assert returncode == 0
    assert result["status"] == "eligible"


def test_new_study_checker_rejects_existing_research(tmp_path: Path) -> None:
    root = minimal_repository(tmp_path)
    (root / "research" / "new-study-v001").mkdir(parents=True)
    returncode, result = run(
        NEW_STUDY_CHECKER,
        "new-study-v001",
        "--repository-root",
        str(root),
    )
    assert returncode == 2
    assert result["status"] == "rejected"


def test_frozen_checker_accepts_exact_candidate_freeze(tmp_path: Path) -> None:
    root = minimal_repository(tmp_path)
    frozen_study(root)
    returncode, result = run(
        FROZEN_CHECKER,
        "demo-study-v001",
        "--repository-root",
        str(root),
    )
    assert returncode == 0
    assert result["status"] == "eligible"
    assert result["runner_status"] == "frozen"
    assert result["evaluation_runner"].endswith("run_historical_evaluation.py")


def test_frozen_checker_marks_missing_runner_as_adapter_required(tmp_path: Path) -> None:
    root = minimal_repository(tmp_path)
    study = frozen_study(root)
    source_bundle = study / "manifests" / "source-bundle.yml"
    source_bundle.write_text("files: []\nschema_version: 1\n", encoding="utf-8")
    returncode, result = run(
        FROZEN_CHECKER,
        "demo-study-v001",
        "--repository-root",
        str(root),
    )
    assert returncode == 0
    assert result["status"] == "eligible"
    assert result["runner_status"] == "adapter-required"
    assert result["evaluation_runner"] is None


def test_frozen_checker_rejects_event_after_candidate_freeze(tmp_path: Path) -> None:
    root = minimal_repository(tmp_path)
    study = frozen_study(root)
    (study / "events" / "000008-historical-evaluation-completed.yml").write_text(
        "schema_version: 1\n",
        encoding="utf-8",
    )
    returncode, result = run(
        FROZEN_CHECKER,
        "demo-study-v001",
        "--repository-root",
        str(root),
    )
    assert returncode == 2
    assert result["status"] == "rejected"


def test_frozen_checker_rejects_modified_runner(tmp_path: Path) -> None:
    root = minimal_repository(tmp_path)
    frozen_study(root)
    runner = root / "research" / "demo-study-v001" / "run_historical_evaluation.py"
    runner.write_text("print('modified')\n", encoding="utf-8")
    returncode, result = run(
        FROZEN_CHECKER,
        "demo-study-v001",
        "--repository-root",
        str(root),
    )
    assert returncode == 2
    assert result["status"] == "rejected"


def test_gate_preflight_accepts_validator_supported_study() -> None:
    returncode, result = run(
        RECOMPUTE_EVALUATION,
        "fxi-deep-pullback-no-closepos-exitcd7-v001",
        "--check-gates-only",
    )
    assert returncode == 0
    assert result["status"] == "eligible"
    assert result["unsupported_gates"] == []


def test_gate_preflight_rejects_unsupported_frozen_gates() -> None:
    returncode, result = run(
        RECOMPUTE_EVALUATION,
        "fxi-deep-pullback-risk2-exitcd7-v001",
        "--check-gates-only",
    )
    assert returncode == 2
    assert result["status"] == "rejected"
    assert result["unsupported_gates"] == ["stress_maximum_drawdown"]
