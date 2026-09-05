from __future__ import annotations

from pathlib import Path

import pytest
from helpers import (
    DIGESTS,
    advance_to_candidate,
    development_evidence,
    development_inputs,
    evaluation_evidence,
    service,
    terminal_evidence,
)
from validator.errors import IntegrityError, TransitionError, ValidationError


def test_historical_evaluation_pass_requires_terminal(workflow_root: Path, tmp_path: Path) -> None:
    study_service = service(workflow_root, tmp_path)
    study_id = "passing-study"
    advance_to_candidate(study_service, study_id)

    evaluation_path, evaluation_digest = study_service.publish_artifact(
        study_id,
        "evidence/historical-evaluation.yml",
        evaluation_evidence(),
    )
    study_service.append_event(
        study_id,
        "historical-evaluation-completed",
        "same-person",
        {
            "evidence_path": evaluation_path,
            "evidence_digest": evaluation_digest,
            "disposition": "pass",
        },
    )
    before_terminal = study_service.validate(study_id)
    assert before_terminal["lifecycle"]["current_event"] == "historical-evaluation-completed"
    assert before_terminal["outcome"]["status"] == "pending"
    assert "robustness-challenges" not in before_terminal["evidence"]
    assert "retrospective-execution-replay" not in before_terminal["evidence"]

    for event_type in (
        "robustness-challenges-completed",
        "retrospective-replay-completed",
        "independent-review-completed",
    ):
        with pytest.raises(ValidationError):
            study_service.append_event(study_id, event_type, "same-person", {})

    terminal_value = terminal_evidence(before_terminal, "pass", [])
    terminal_path, terminal_digest = study_service.publish_artifact(
        study_id,
        "evidence/terminal-evidence.yml",
        terminal_value,
    )
    study_service.append_event(
        study_id,
        "study-terminal",
        "same-person",
        {
            "outcome": "pass",
            "authority": "retrospectively-supported",
            "terminal_evidence_path": terminal_path,
            "terminal_evidence_digest": terminal_digest,
        },
    )
    projection = study_service.validate(study_id)
    assert projection["lifecycle"]["event_count"] == 9
    assert projection["lifecycle"]["current_event"] == "study-terminal"
    assert projection["outcome"] == {
        "status": "pass",
        "authority": "retrospectively-supported",
    }


def test_cannot_skip_candidate_freeze(workflow_root: Path, tmp_path: Path) -> None:
    study_service = service(workflow_root, tmp_path)
    study_service.create_study(
        "skip-study",
        "owner",
        research_round_id="round",
        experiment_family="family",
        research_owner="owner",
        historical_evaluation_operator="owner",
        source_bundle={
            "schema_version": 1,
            "files": [{"path": "runner.py", "digest": DIGESTS["source"]}],
        },
    )
    evidence_path, evidence_digest = study_service.publish_artifact(
        "skip-study",
        "evidence/historical-evaluation.yml",
        evaluation_evidence(),
    )
    with pytest.raises(TransitionError):
        study_service.append_event(
            "skip-study",
            "historical-evaluation-completed",
            "owner",
            {
                "evidence_path": evidence_path,
                "evidence_digest": evidence_digest,
                "disposition": "pass",
            },
        )


def test_registry_count_cannot_be_forged(workflow_root: Path, tmp_path: Path) -> None:
    study_service = service(workflow_root, tmp_path)
    study_id = "registry-study"
    study_service.create_study(
        study_id,
        "owner",
        research_round_id="round",
        experiment_family="family-a",
        research_owner="owner",
        historical_evaluation_operator="owner",
        source_bundle={
            "schema_version": 1,
            "files": [{"path": "runner.py", "digest": DIGESTS["source"]}],
        },
    )
    from helpers import preregistration

    path, digest = study_service.publish_artifact(
        study_id,
        "manifests/preregistration.yml",
        preregistration(),
    )
    study_service.append_event(
        study_id,
        "preregistration-approved",
        "owner",
        {"preregistration_path": path, "preregistration_digest": digest},
    )
    auth_path, auth_digest = study_service.publish_artifact(
        study_id,
        "evidence/auth.yml",
        {"authorized": True},
    )
    study_service.append_event(
        study_id,
        "development-authorized",
        "owner",
        {"evidence_path": auth_path, "evidence_digest": auth_digest},
    )
    source_bundle_digest = study_service.validate(study_id)["workflow_binding"][
        "source_bundle_digest"
    ]
    inputs_path, inputs_digest = study_service.publish_artifact(
        study_id,
        "manifests/development-trial-inputs.yml",
        development_inputs(digest, source_bundle_digest),
    )
    development_path, development_digest = study_service.publish_artifact(
        study_id,
        "evidence/development.yml",
        development_evidence(digest, source_bundle_digest, inputs_digest),
    )
    study_service.append_event(
        study_id,
        "trial-recorded",
        "owner",
        {
            "trial_id": "trial-1",
            "inputs_path": inputs_path,
            "inputs_digest": inputs_digest,
            "development_evidence_path": development_path,
            "development_evidence_digest": development_digest,
            "status": "completed",
        },
    )
    with pytest.raises(ValidationError, match="recorded_trial_count"):
        study_service.append_event(
            study_id,
            "trial-registry-frozen",
            "owner",
            {
                "maximum_trials": 1,
                "recorded_trial_count": 99,
                "complete_family_trial_ids": ["trial-1"],
                "trial_registry_digest": "3" * 64,
                "candidate_available": True,
            },
        )


def test_trial_rejects_unregistered_bootstrap_seed(
    workflow_root: Path, tmp_path: Path
) -> None:
    study_service = service(workflow_root, tmp_path)
    study_id = "wrong-development-seed"
    study_service.create_study(
        study_id,
        "owner",
        research_round_id="round",
        experiment_family="family-a",
        research_owner="owner",
        historical_evaluation_operator="owner",
        source_bundle={
            "schema_version": 1,
            "files": [{"path": "runner.py", "digest": DIGESTS["source"]}],
        },
    )
    from helpers import preregistration

    prereg_path, prereg_digest = study_service.publish_artifact(
        study_id, "manifests/preregistration.yml", preregistration()
    )
    study_service.append_event(
        study_id,
        "preregistration-approved",
        "owner",
        {"preregistration_path": prereg_path, "preregistration_digest": prereg_digest},
    )
    auth_path, auth_digest = study_service.publish_artifact(
        study_id, "evidence/auth.yml", {"authorized": True}
    )
    study_service.append_event(
        study_id,
        "development-authorized",
        "owner",
        {"evidence_path": auth_path, "evidence_digest": auth_digest},
    )
    source_digest = study_service.validate(study_id)["workflow_binding"][
        "source_bundle_digest"
    ]
    inputs_path, inputs_digest = study_service.publish_artifact(
        study_id,
        "manifests/development-trial-inputs.yml",
        development_inputs(prereg_digest, source_digest),
    )
    evidence_path, evidence_digest = study_service.publish_artifact(
        study_id,
        "evidence/development.yml",
        development_evidence(prereg_digest, source_digest, inputs_digest, seed=45),
    )
    with pytest.raises(IntegrityError, match="未使用登記 seed"):
        study_service.append_event(
            study_id,
            "trial-recorded",
            "owner",
            {
                "trial_id": "trial-1",
                "inputs_path": inputs_path,
                "inputs_digest": inputs_digest,
                "development_evidence_path": evidence_path,
                "development_evidence_digest": evidence_digest,
                "status": "completed",
            },
        )


@pytest.mark.parametrize(
    "tampering",
    [
        "missing-metrics",
        "missing-trades",
        "changed-pnl",
        "changed-year-breakdown",
        "changed-leave-one-year-out",
        "changed-bootstrap-statistic",
    ],
)
def test_trial_rejects_tampered_development_raw_evidence(
    workflow_root: Path, tmp_path: Path, tampering: str
) -> None:
    study_service = service(workflow_root, tmp_path)
    study_id = f"tampered-development-{tampering}"
    study_service.create_study(
        study_id,
        "owner",
        research_round_id="round",
        experiment_family="family-a",
        research_owner="owner",
        historical_evaluation_operator="owner",
        source_bundle={
            "schema_version": 1,
            "files": [{"path": "runner.py", "digest": DIGESTS["source"]}],
        },
    )
    from helpers import preregistration

    prereg_path, prereg_digest = study_service.publish_artifact(
        study_id, "manifests/preregistration.yml", preregistration()
    )
    study_service.append_event(
        study_id,
        "preregistration-approved",
        "owner",
        {"preregistration_path": prereg_path, "preregistration_digest": prereg_digest},
    )
    auth_path, auth_digest = study_service.publish_artifact(
        study_id, "evidence/auth.yml", {"authorized": True}
    )
    study_service.append_event(
        study_id,
        "development-authorized",
        "owner",
        {"evidence_path": auth_path, "evidence_digest": auth_digest},
    )
    source_digest = study_service.validate(study_id)["workflow_binding"][
        "source_bundle_digest"
    ]
    inputs_path, inputs_digest = study_service.publish_artifact(
        study_id,
        "manifests/development-trial-inputs.yml",
        development_inputs(prereg_digest, source_digest),
    )
    evidence = development_evidence(prereg_digest, source_digest, inputs_digest)
    if tampering == "missing-metrics":
        del evidence["metrics"]
    elif tampering == "missing-trades":
        del evidence["trades"]
    elif tampering == "changed-pnl":
        evidence["trades"][0]["base"]["pnl"] = "101"
    elif tampering == "changed-year-breakdown":
        evidence["diagnostics"]["by_signal_year"]["2014"]["base_pnl"] = "101"
    elif tampering == "changed-leave-one-year-out":
        evidence["diagnostics"]["leave_one_signal_year_out"]["stress"]["2014"][
            "return"
        ] = "0.1"
    elif tampering == "changed-bootstrap-statistic":
        evidence["diagnostics"]["block_bootstrap"]["stress"][0][
            "positive_return_ratio"
        ] = "0.5"
    evidence_path, evidence_digest = study_service.publish_artifact(
        study_id, "evidence/development.yml", evidence
    )
    with pytest.raises((IntegrityError, ValidationError)):
        study_service.append_event(
            study_id,
            "trial-recorded",
            "owner",
            {
                "trial_id": "trial-1",
                "inputs_path": inputs_path,
                "inputs_digest": inputs_digest,
                "development_evidence_path": evidence_path,
                "development_evidence_digest": evidence_digest,
                "status": "completed",
            },
        )


def test_known_gate_failure_terminates_as_fail(workflow_root: Path, tmp_path: Path) -> None:
    study_service = service(workflow_root, tmp_path)
    study_id = "failed-study"
    advance_to_candidate(study_service, study_id)
    evidence = evaluation_evidence()
    evidence["trades"] = evidence["trades"][:19]
    evidence_path, evidence_digest = study_service.publish_artifact(
        study_id, "evidence/historical-failure.yml", evidence
    )
    study_service.append_event(
        study_id,
        "historical-evaluation-completed",
        "same-person",
        {
            "evidence_path": evidence_path,
            "evidence_digest": evidence_digest,
            "disposition": "fail",
        },
    )
    terminal = terminal_evidence(
        study_service.validate(study_id), "fail", ["completed_trades 未達門檻"]
    )
    terminal_path, terminal_digest = study_service.publish_artifact(
        study_id, "evidence/terminal-evidence.yml", terminal
    )
    study_service.append_event(
        study_id,
        "study-terminal",
        "same-person",
        {
            "outcome": "fail",
            "authority": "none",
            "terminal_evidence_path": terminal_path,
            "terminal_evidence_digest": terminal_digest,
        },
    )
    assert study_service.validate(study_id)["outcome"]["status"] == "fail"


def test_missing_evidence_terminates_as_indeterminate(
    workflow_root: Path, tmp_path: Path
) -> None:
    study_service = service(workflow_root, tmp_path)
    study_id = "indeterminate-study"
    study_service.create_study(
        study_id,
        "same-person",
        research_round_id="round",
        experiment_family="family",
        research_owner="same-person",
        historical_evaluation_operator="same-person",
        source_bundle={
            "schema_version": 1,
            "files": [{"path": "runner.py", "digest": DIGESTS["source"]}],
        },
    )
    study_service.append_event(
        study_id,
        "evidence-unavailable",
        "same-person",
        {
            "stage": "preregistration",
            "unavailable_path": "evidence/missing-preregistration.yml",
            "reason": "來源檔無法取得",
        },
    )
    terminal = terminal_evidence(
        study_service.validate(study_id), "indeterminate", ["必要 evidence 無法取得"]
    )
    terminal_path, terminal_digest = study_service.publish_artifact(
        study_id, "evidence/terminal-evidence.yml", terminal
    )
    study_service.append_event(
        study_id,
        "study-terminal",
        "same-person",
        {
            "outcome": "indeterminate",
            "authority": "none",
            "terminal_evidence_path": terminal_path,
            "terminal_evidence_digest": terminal_digest,
        },
    )
    assert study_service.validate(study_id)["outcome"]["status"] == "indeterminate"


def test_candidate_selection_must_bind_preregistered_rules(
    workflow_root: Path, tmp_path: Path
) -> None:
    study_service = service(workflow_root, tmp_path)
    with pytest.raises(IntegrityError, match="selection rules"):
        advance_to_candidate(
            study_service,
            "wrong-selection-study",
            selection_rule_digest="f" * 64,
        )
