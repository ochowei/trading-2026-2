from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from helpers import DIGESTS, service
from validator.canonical_yaml import canonical_bytes
from validator.errors import IntegrityError, ValidationError
from validator.study import PROVENANCE_DISPOSITIONS
from writer.service import StudyService

WRITER_CLI = Path(__file__).resolve().parents[1] / "writer" / "cli.py"


def _create(study_service: StudyService, study_id: str) -> None:
    study_service.create_study(
        study_id,
        "same-person",
        research_round_id="round-1",
        experiment_family="family-a",
        research_owner="same-person",
        historical_evaluation_operator="same-person",
        source_bundle={
            "schema_version": 1,
            "files": [{"path": "runner.py", "digest": DIGESTS["source"]}],
        },
    )


def test_provenance_dispositions_are_fail_closed() -> None:
    assert PROVENANCE_DISPOSITIONS == {
        "verified-clean": None,
        "known-contaminated": "fail",
        "provenance-unknown": "indeterminate",
    }


def test_pause_resume_requires_same_frozen_operation(workflow_root: Path, tmp_path: Path) -> None:
    study_service = service(workflow_root, tmp_path)
    _create(study_service, "paused-study")
    study_service.append_event(
        "paused-study",
        "study-paused",
        "same-person",
        {"reason": "recoverable interruption", "frozen_operation_digest": "1" * 64},
    )
    with pytest.raises(IntegrityError, match="相同 frozen operation"):
        study_service.append_event(
            "paused-study",
            "study-resumed",
            "same-person",
            {"frozen_operation_digest": "2" * 64},
        )
    study_service.append_event(
        "paused-study",
        "study-resumed",
        "same-person",
        {"frozen_operation_digest": "1" * 64},
    )
    assert study_service.validate("paused-study")["lifecycle"]["status"] == "active"


def test_authority_tail_rollback_is_detected(workflow_root: Path, tmp_path: Path) -> None:
    study_service = service(workflow_root, tmp_path)
    _create(study_service, "rollback-study")
    checkpoint = study_service.authority.checkpoints("rollback-study")[-1][0]
    checkpoint.unlink()
    with pytest.raises(IntegrityError, match="數量不一致"):
        study_service.validate("rollback-study")


def test_validate_rejects_missing_study(workflow_root: Path, tmp_path: Path) -> None:
    study_service = service(workflow_root, tmp_path)

    with pytest.raises(ValidationError, match="找不到 Study 目錄"):
        study_service.validate("missing-study")


def test_writer_cli_serializes_integrity_error(
    workflow_root: Path, tmp_path: Path
) -> None:
    study_service = service(workflow_root, tmp_path)
    _create(study_service, "cli-integrity-study")
    study_service.authority.checkpoints("cli-integrity-study")[-1][0].unlink()

    completed = subprocess.run(
        [
            sys.executable,
            str(WRITER_CLI),
            "--workflow-root",
            str(workflow_root),
            "--authority-root",
            str(tmp_path / "authority"),
            "validate",
            "--study-id",
            "cli-integrity-study",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert output == {
        "command": "validate",
        "error": {
            "code": "integrity-error",
            "message": "Authority checkpoints 與 Study Events 數量不一致",
            "type": "IntegrityError",
        },
        "status": "error",
        "study_id": "cli-integrity-study",
    }


def test_writer_cli_returns_nonzero_structured_error_for_missing_study(
    workflow_root: Path, tmp_path: Path
) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(WRITER_CLI),
            "--workflow-root",
            str(workflow_root),
            "--authority-root",
            str(tmp_path / "authority"),
            "validate",
            "--study-id",
            "missing-study",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert output["command"] == "validate"
    assert output["status"] == "error"
    assert output["study_id"] == "missing-study"
    assert output["error"]["code"] == "validation-error"
    assert output["error"]["type"] == "ValidationError"
    assert "找不到 Study 目錄" in output["error"]["message"]


def test_incomplete_journal_recovers_exact_bytes(workflow_root: Path, tmp_path: Path) -> None:
    study_service = service(workflow_root, tmp_path)
    _create(study_service, "recovery-study")
    study_root = study_service.study_root("recovery-study")
    completed = next((study_root / "journals").glob("*.completed.yml"))
    checkpoint = study_service.authority.checkpoints("recovery-study")[-1][0]
    completed.unlink()
    checkpoint.unlink()
    recovered = study_service.recover("recovery-study")
    assert len(recovered) == 1
    assert study_service.validate("recovery-study")["lifecycle"]["event_count"] == 1


def test_formal_writer_requires_release(workflow_root: Path, tmp_path: Path) -> None:
    (workflow_root / "release.yml").unlink()
    with pytest.raises(ValidationError, match="release"):
        StudyService(workflow_root, tmp_path / "authority")


def test_formal_writer_accepts_approved_release(
    workflow_root: Path, tmp_path: Path
) -> None:
    study_service = StudyService(workflow_root, tmp_path / "authority")
    assert study_service.workflow_digest


def test_projection_cannot_be_used_to_forge_pass(workflow_root: Path, tmp_path: Path) -> None:
    study_service = service(workflow_root, tmp_path)
    _create(study_service, "forged-projection-study")
    projection_path = study_service.study_root("forged-projection-study") / "study.yml"
    forged = study_service.validate("forged-projection-study")
    forged["outcome"] = {
        "status": "pass",
        "authority": "retrospectively-supported",
    }
    projection_path.write_bytes(canonical_bytes(forged))
    with pytest.raises(IntegrityError, match="projection"):
        study_service.validate("forged-projection-study")


def test_artifact_path_cannot_escape_study(workflow_root: Path, tmp_path: Path) -> None:
    study_service = service(workflow_root, tmp_path)
    with pytest.raises(ValidationError, match="Study 目錄"):
        study_service.publish_artifact("path-study", "../outside.yml", {"unsafe": True})
