from __future__ import annotations

from pathlib import Path

import pytest
from helpers import DIGESTS, challenge_evidence, service
from validator.artifacts import evaluate_challenges
from validator.canonical_yaml import canonical_bytes
from validator.errors import IntegrityError, ValidationError
from validator.study import PROVENANCE_DISPOSITIONS
from writer.service import StudyService


def _create(study_service: StudyService, study_id: str) -> None:
    study_service.create_study(
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


def test_provenance_dispositions_are_fail_closed() -> None:
    assert PROVENANCE_DISPOSITIONS == {
        "verified-clean": None,
        "known-contaminated": "fail",
        "provenance-unknown": "indeterminate",
    }


def test_challenge_set_cannot_be_partial(workflow_root: Path) -> None:
    from validator.study import WorkflowRules

    rules = WorkflowRules(workflow_root)
    bindings = {
        "candidate_digest": "1" * 64,
        "evaluation_snapshot_digest": "2" * 64,
        "fold_inventory_digest": "3" * 64,
        "policy_set_digest": "4" * 64,
        "qualification_spec_digest": "5" * 64,
        "source_bundle_digest": "6" * 64,
    }
    evidence = challenge_evidence(bindings)
    evidence["challenges"].pop()
    with pytest.raises(ValidationError, match="Challenge IDs"):
        evaluate_challenges(
            evidence,
            rules.evidence_requirements["required_challenges"],
            rules.evidence_requirements["seed_required_challenges"],
        )


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
