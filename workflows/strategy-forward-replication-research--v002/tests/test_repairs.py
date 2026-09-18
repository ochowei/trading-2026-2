import subprocess
import sys
from pathlib import Path

import pytest
from operations.lifecycle import freeze_readiness, resume
from operations.service import create_authorize
from repair_helpers import cli, freeze_plan, full_repository, prepared_service, publish_trial
from test_operations import fixture_repository, passed_report, plan_for, write
from validator.canonical_yaml import canonical_bytes, canonical_digest, load_canonical
from validator.errors import EvidenceUnavailable, IntegrityError, ValidationError
from validator.qualification import validate_supported
from validator.study import validate_study
from writer.lock import StudyLock
from writer.service import StudyService


def test_cli_prepare_to_freeze_same_engine_without_guard_bypass(tmp_path):
    repository, package, study_id, authority, research = full_repository(tmp_path)
    report_path = tmp_path / "prepare.yml"
    cli(package, repository, authority, "prepare", study_id, "--report", report_path)
    create_plan = tmp_path / "create.yml"
    write(create_plan, plan_for(study_id, research))
    cli(
        package,
        repository,
        authority,
        "create-authorize",
        "--plan",
        create_plan,
        "--report",
        report_path,
    )
    inputs = load_canonical(research / "development-trial-inputs.yml")
    trial_plan = tmp_path / "trial.yml"
    write(
        trial_plan,
        {
            "actor": "fixture-owner",
            "trial_inputs": inputs,
            "data_path": inputs["data_bindings"]["development_path"],
            "data_digest": inputs["data_bindings"]["development_digest"],
        },
    )
    result = cli(package, repository, authority, "development", study_id, "--plan", trial_plan)
    assert result["result"]["assessment"]["candidate_freeze_eligibility"]["eligible"]
    service = StudyService(package, authority, repository_root=repository, allow_draft=True)
    plan_path = tmp_path / "freeze.yml"
    write(plan_path, freeze_plan(service))
    before = list((service.study_root(study_id) / "events").glob("*.yml"))
    cli(package, repository, authority, "freeze-readiness", study_id, "--plan", plan_path)
    assert list((service.study_root(study_id) / "events").glob("*.yml")) == before
    cli(package, repository, authority, "freeze", study_id, "--plan", plan_path)
    result = cli(package, repository, authority, "validate", study_id)
    assert result["result"]["projection"]["lifecycle"]["current_event"] == "candidate-frozen"
    cli(package, repository, authority, "resume", study_id)
    assert len(list((service.study_root(study_id) / "events").glob("*.yml"))) == 7


@pytest.mark.parametrize(
    "name",
    [
        "manifests/prepare-report.yml",
        "evidence/preregistration-approval.yml",
        "evidence/development-authorization.yml",
        "manifests/create-plan.yml",
    ],
)
@pytest.mark.parametrize("fault", ["missing", "changed"])
def test_bound_proofs_rechecked_on_validate_append_and_recover(tmp_path, name, fault):
    service, study_id, _, _ = prepared_service(tmp_path)
    path = service.study_root(study_id) / name
    if fault == "missing":
        path.unlink()
    else:
        value = load_canonical(path)
        value["study_id"] = "different-study"
        path.write_bytes(canonical_bytes(value))
    for operation in (
        lambda: service.validate(study_id),
        lambda: service.recover(study_id),
        lambda: service.append_event(
            study_id,
            "study-paused",
            "owner",
            {"reason": "test", "frozen_operation_digest": "1" * 64},
        ),
    ):
        with pytest.raises((ValidationError, IntegrityError, EvidenceUnavailable)):
            operation()
    assert len(service.authority.checkpoints(study_id)) == 3


@pytest.mark.parametrize("mode", ["no-trades", "gate-fail", "target-only"])
def test_valid_unsuccessful_trials_cannot_freeze(tmp_path, mode):
    targets = {"base_return": {"operator": ">", "value": "100"}} if mode == "target-only" else None
    service, study_id, research, _ = prepared_service(
        tmp_path, eligible=mode != "gate-fail", targets=targets
    )
    publish_trial(service, study_id, research, no_trades=mode == "no-trades")
    state = validate_study(service.study_root(study_id), service.rules)
    assessment = state.trial_assessments["trial-1"]
    assert state.trials["trial-1"]["status"] == "completed"
    assert assessment["development_evidence_validity"]["status"] == "valid"
    assert not assessment["candidate_freeze_eligibility"]["eligible"]
    if mode == "target-only":
        assert assessment["formal_development_gates"]["status"] == "passed"
        assert assessment["research_targets"]["status"] == "failed"
    plan = freeze_plan(service)
    with pytest.raises(ValidationError, match="沒有可凍結"):
        freeze_readiness(service, study_id, plan)
    with pytest.raises(ValidationError, match="candidate_available"):
        service.append_event(
            study_id,
            "trial-registry-frozen",
            "owner",
            {
                "maximum_trials": 1,
                "recorded_trial_count": 1,
                "complete_family_trial_ids": ["trial-1"],
                "trial_registry_digest": canonical_digest({"trials": [state.trials["trial-1"]]}),
                "candidate_available": True,
            },
        )
    assert len(state.events) == 4


def test_baseline_and_publication_are_independently_verified(tmp_path):
    service, study_id, research, _ = prepared_service(tmp_path, eligible=True)
    payload = publish_trial(service, study_id, research)
    state = service.validate(study_id)
    assert state["trial_registry"]["assessments"]["trial-1"]["candidate_freeze_eligibility"][
        "eligible"
    ]
    manifest = load_canonical(service.study_root(study_id) / payload["publication_path"])
    (service.study_root(study_id) / manifest["artifacts"]["baseline"]["path"]).unlink()
    with pytest.raises(EvidenceUnavailable):
        service.validate(study_id)


def test_historical_validation_does_not_require_current_environment(tmp_path, monkeypatch):
    service, study_id, _, _ = prepared_service(tmp_path)
    monkeypatch.setattr("operations.preflight.environment_identity", lambda: {"changed": True})
    assert service.validate(study_id)["lifecycle"]["event_count"] == 3


@pytest.mark.parametrize(
    "field", ["study_id", "source_bundle_digest", "preregistration_digest", "workflow_version"]
)
def test_cross_study_approval_rejected_before_first_event(tmp_path, field):
    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    report = passed_report(repository, package, study_id, authority)
    plan = plan_for(study_id, research)
    plan["preregistration_approval"]["bindings"][field] = "wrong"
    service = StudyService(package, authority, repository_root=repository, allow_draft=True)
    with pytest.raises((IntegrityError, ValidationError)):
        create_authorize(service, plan, report)
    assert not (package / "studies").exists()
    assert not authority.exists()


def test_rejects_unknown_selection_and_targets_before_prepare(tmp_path):
    from helpers import preregistration

    prereg = preregistration()
    prereg["eligibility_rules"]["research_targets"] = {"invented": {"operator": ">", "value": "1"}}
    with pytest.raises(ValidationError, match="不支援"):
        validate_supported(prereg)
    prereg = preregistration()
    prereg["selection_rule"]["metric"] = "invented"
    with pytest.raises(ValidationError, match="不支援"):
        validate_supported(prereg)


@pytest.mark.parametrize(
    "boundary", ["artifact", "prepared", "event", "checkpoint", "between-events"]
)
def test_hard_exit_batch_resumes_original_journal(tmp_path, boundary):
    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    report = passed_report(repository, package, study_id, authority)
    plan = plan_for(study_id, research)
    write(tmp_path / "report.yml", report)
    write(tmp_path / "plan.yml", plan)
    script = r"""
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import writer.service as service_module
import writer.journal as journal_module
from writer.service import StudyService
from operations.service import create_authorize
from validator.canonical_yaml import load_canonical
package, repo, authority, temp, boundary = map(str, sys.argv[1:])
service = StudyService(package, authority, repository_root=repo, allow_draft=True)
original = journal_module.atomic_create

def journal_create(path, data):
    result = original(path, data)
    name = str(path)
    if (boundary == "prepared" and name.endswith(".prepared.yml")) or (boundary == "event" and "/events/" in name) or (boundary == "checkpoint" and "/checkpoints/" in name):
        os._exit(71)
    return result
journal_module.atomic_create = journal_create
original_artifact = service_module.atomic_create

def artifact(path, data):
    result = original_artifact(path, data)
    if boundary == "artifact" and str(path).endswith("manifests/source-bundle.yml"):
        os._exit(71)
    return result
service_module.atomic_create = artifact
original_append = service.append_event

def append(*args, **kwargs):
    result = original_append(*args, **kwargs)
    if boundary == "between-events":
        os._exit(71)
    return result
service.append_event = append
create_authorize(service, load_canonical(Path(temp)/"plan.yml"), load_canonical(Path(temp)/"report.yml"))
"""
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(package),
            str(repository),
            str(authority),
            str(tmp_path),
            boundary,
        ],
        capture_output=True,
        text=True,
    )
    assert process.returncode == 71, process.stderr
    service = StudyService(package, authority, repository_root=repository, allow_draft=True)
    before = {
        p.name: p.read_bytes() for p in (service.study_root(study_id) / "events").glob("*.yml")
    }
    cli(package, repository, authority, "resume", study_id)
    assert service.validate(study_id)["lifecycle"]["event_count"] == 3
    for name, data in before.items():
        assert (service.study_root(study_id) / "events" / name).read_bytes() == data
    resume(service, study_id)
    assert len(service.authority.checkpoints(study_id)) == 3


def test_os_lock_is_exclusive_and_released_after_kill(tmp_path):
    package = Path(__file__).resolve().parents[1]
    path = tmp_path / ".writer.lock"
    script = 'import sys,time; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from writer.lock import StudyLock; lock=StudyLock(Path(sys.argv[2])); lock.__enter__(); print("held",flush=True); time.sleep(30)'
    child = subprocess.Popen(
        [sys.executable, "-c", script, str(package), str(path)], stdout=subprocess.PIPE, text=True
    )
    try:
        assert child.stdout.readline().strip() == "held"
        inode = path.stat().st_ino
        with pytest.raises(IntegrityError, match="鎖定"):
            with StudyLock(path):
                pass
        child.kill()
        child.wait(timeout=5)
        with StudyLock(path):
            with StudyLock(path):
                assert path.stat().st_ino == inode
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)


def test_pending_journal_missing_proof_does_not_publish_event(tmp_path, monkeypatch):
    from writer.journal import JournalPublisher

    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    report = passed_report(repository, package, study_id, authority)
    service = StudyService(package, authority, repository_root=repository, allow_draft=True)
    original = JournalPublisher._complete

    def interrupt(self, journal):
        raise RuntimeError("after prepared")

    monkeypatch.setattr(JournalPublisher, "_complete", interrupt)
    with pytest.raises(RuntimeError):
        create_authorize(service, plan_for(study_id, research), report)
    monkeypatch.setattr(JournalPublisher, "_complete", original)
    (service.study_root(study_id) / "manifests/prepare-report.yml").unlink()
    with pytest.raises(EvidenceUnavailable):
        service.recover(study_id)
    assert not list((service.study_root(study_id) / "events").glob("*.yml"))
    assert service.authority.checkpoints(study_id) == []


@pytest.mark.parametrize("reason", ["unavailable", "no-eligible-candidate"])
def test_high_level_early_terminal_and_repeat_resume(tmp_path, reason):
    from operations.lifecycle import terminate

    service, study_id, research, _ = prepared_service(tmp_path)
    if reason == "no-eligible-candidate":
        publish_trial(service, study_id, research)
    plan = {
        "actor": "fixture-owner",
        "reason_kind": reason,
        "evidence_unavailable": {
            "stage": "development",
            "unavailable_path": "evidence/missing.yml",
            "reason": "隔離 fixture 模擬不可恢復",
        },
        "terminal_evidence": {
            "schema_version": 1,
            "outcome": "fail" if reason == "no-eligible-candidate" else "indeterminate",
            "authority": "none",
            "recomputed": True,
            "reasons": ["fixture"],
        },
    }
    terminate(service, study_id, plan)
    resume(service, study_id)
    terminate(service, study_id, plan)
    assert service.validate(study_id)["outcome"]["status"] == plan["terminal_evidence"]["outcome"]


def test_synthetic_evaluation_and_developer_status_read_boundary(tmp_path, monkeypatch):
    import exchange_calendars as xcals
    from operations.evaluation import historical_evaluation
    from operations.lifecycle import freeze, status
    from operations.preflight import synthetic_csv

    service, study_id, research, _ = prepared_service(tmp_path, eligible=True)
    publish_trial(service, study_id, research)
    days = xcals.get_calendar("XNYS").sessions_in_range("2020-01-01", "2024-12-31")
    data = synthetic_csv(
        {"rows": [[day.strftime("%Y-%m-%d"), 100, 101, 99, 100, 1000] for day in days]}
    )
    (research / "synthetic-evaluation.csv").write_bytes(data)
    plan = freeze_plan(service)
    for snap in plan["snapshot_set"]["snapshots"]:
        if snap["role"] == "historical-evaluation":
            snap["data_digest"] = canonical_digest(data)
    freeze(service, study_id, plan)
    state = validate_study(service.study_root(study_id), service.rules)
    proof = {
        "decision": "approved",
        "actor_id": "fixture-approver",
        "role": "trusted-approver",
        "approved_at": "2000-01-01T00:00:00Z",
        "basis": "synthetic only",
        "scope": "historical-evaluation-only",
        "bindings": {
            "study_id": study_id,
            "workflow_version": "v002",
            "source_bundle_digest": state.bindings["source_bundle_digest"],
            "preregistration_digest": state.preregistration_digest,
        },
        "candidate_freeze_digest": state.evidence["candidate-freeze"],
    }
    evaluation_plan = {
        "actor": "fixture-evaluator",
        "authorization": proof,
        "data_path": f"research/{study_id}/synthetic-evaluation.csv",
        "data_digest": canonical_digest(data),
    }
    result = historical_evaluation(service, study_id, evaluation_plan)
    assert result["outcome"] == "fail"
    assert historical_evaluation(service, study_id, evaluation_plan) == result
    original = Path.open
    store = service.rules.historical_evaluation_artifacts_root

    def guarded(self, *args, **kwargs):
        if store in self.parents:
            raise AssertionError("developer status opened Evaluation store")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    view = status(service, study_id)
    assert not view["full_semantic_validation"]
    assert view["later_stage"] == "not_inspected"
    assert view["projection"]["lifecycle"]["current_event"] == "candidate-frozen"


def test_forged_selection_order_rejected_by_low_level_writer(tmp_path):
    from copy import deepcopy

    from operations.lifecycle import freeze_steps

    service, study_id, research, _ = prepared_service(tmp_path, eligible=True)
    publish_trial(service, study_id, research)
    stages = freeze_steps(service, study_id, freeze_plan(service))
    for kind, actor, payload in stages[:2]:
        service.append_event(study_id, kind, actor, payload)
    kind, actor, payload = stages[-1]
    value = load_canonical(service.study_root(study_id) / payload["selection_evidence_path"])
    value["ordered_eligible_trial_ids"] = ["trial-1", "forged-trial"]
    path, digest = service.publish_artifact(study_id, "evidence/forged-selection.yml", value)
    payload = deepcopy(payload)
    payload.update(selection_evidence_path=path, selection_evidence_digest=digest)
    with pytest.raises(ValidationError, match="重算"):
        service.append_event(study_id, kind, actor, payload)


def test_multiple_trials_preflight_ranking_and_stable_tie(tmp_path):
    from copy import deepcopy

    from operations.lifecycle import freeze, projection
    from operations.publication import consume

    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    prereg = load_canonical(research / "preregistration.yml")
    prereg["complete_candidate_family"] = ["trial-1", "trial-2"]
    prereg["maximum_trials"] = 2
    prereg["eligibility_rules"]["development_gates"]["completed_trades"]["value"] = 1
    write(research / "preregistration.yml", prereg)
    first = load_canonical(research / "development-trial-inputs.yml")
    second = dict(first, candidate_id="trial-2")
    write(research / "trial-inputs/trial-2.yml", second)
    # Source 是程式；個別 trial inputs 由 prepare settings 綁定，避免 digest 自我參照。
    files = [
        {
            "path": path.relative_to(repository).as_posix(),
            "digest": canonical_digest(path.read_bytes()),
        }
        for path in sorted(research.iterdir())
        if path.is_file() and path.name not in {"source-bundle.yml", "development-trial-inputs.yml"}
    ]
    write(research / "source-bundle.yml", {"schema_version": 1, "files": files})
    report = passed_report(repository, package, study_id, authority)
    assert len(report["cases"]) == 8
    service = StudyService(package, authority, repository_root=repository, allow_draft=True)
    create_authorize(service, plan_for(study_id, research), report)
    publish_trial(service, study_id, research)
    envelope = load_canonical(repository / "synthetic-run/output.yml")
    other = deepcopy(envelope)
    other["candidate"]["candidate_id"] = "trial-2"
    for item in other.values():
        item["bindings"]["trial_inputs_digest"] = canonical_digest(second)
    payload = consume(
        service,
        study_id,
        other,
        second,
        prereg,
        canonical_digest(load_canonical(research / "source-bundle.yml")),
    )
    service.append_event(study_id, "trial-recorded", "fixture-owner", payload)
    from validator.qualification import ordered_eligible

    assert ordered_eligible(projection(service, study_id)) == ["trial-1", "trial-2"]
    freeze(service, study_id, freeze_plan(service))
    assert service.validate(study_id)["candidate_freeze"]["selected_candidate_id"] == "trial-1"


def test_skill_cli_contract_and_role_separation():
    package = Path(__file__).resolve().parents[1]
    developer = (package / "skills/build-strategy-study-v002/SKILL.md").read_text()
    evaluator = (package / "skills/run-strategy-evaluation-v002/SKILL.md").read_text()
    positions = [
        developer.index(f"<repo> {name}")
        for name in ("prepare", "create-authorize", "development", "freeze")
    ]
    assert positions == sorted(positions)
    assert "candidate-frozen 即停止" in developer
    assert "使用者明確要求" in evaluator
    assert "historical-evaluation <id> --plan" in evaluator
    assert "resume <id>" in developer and "resume <id>" in evaluator
    assert "studyctl all" not in developer.split("正常操作")[0]


def test_freeze_crash_between_events_and_resume(tmp_path):
    from operations.lifecycle import freeze

    service, study_id, research, _ = prepared_service(tmp_path, eligible=True)
    publish_trial(service, study_id, research)
    plan = freeze_plan(service)
    path = tmp_path / "freeze-plan.yml"
    write(path, plan)
    program = r"""
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from writer.service import StudyService
from operations.lifecycle import freeze
from validator.canonical_yaml import load_canonical
service = StudyService(sys.argv[1], sys.argv[3], repository_root=sys.argv[2], allow_draft=True)
original = service.append_event
def append(study_id, kind, *args, **kwargs):
    value = original(study_id, kind, *args, **kwargs)
    if kind == "trial-registry-frozen": os._exit(71)
    return value
service.append_event = append
freeze(service, sys.argv[4], load_canonical(Path(sys.argv[5])))
"""
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            program,
            str(service.workflow_root),
            str(service.repository_root),
            str(service.authority.root),
            study_id,
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    assert process.returncode == 71, process.stderr
    cli(service.workflow_root, service.repository_root, service.authority.root, "resume", study_id)
    assert service.validate(study_id)["lifecycle"]["current_event"] == "candidate-frozen"
    with pytest.raises(IntegrityError, match="operation plan"):
        freeze(service, study_id, dict(plan, actor="other"))


def test_failed_freeze_readiness_does_not_lock_in_invalid_plan(tmp_path):
    from operations.lifecycle import freeze

    service, study_id, research, _ = prepared_service(tmp_path, eligible=True)
    publish_trial(service, study_id, research)
    plan = freeze_plan(service)
    bad = dict(plan, provenance={"status": "verified-clean", "sources": []})
    with pytest.raises(ValidationError):
        freeze(service, study_id, bad)
    assert not list((service.study_root(study_id) / "operations").glob("*/plan.yml"))
    freeze(service, study_id, plan)
    assert service.validate(study_id)["lifecycle"]["current_event"] == "candidate-frozen"


@pytest.mark.parametrize("boundary", ["candidate-artifact", "trial-event"])
def test_development_hard_exit_resumes_output_without_rerunning(tmp_path, boundary):
    from operations.preflight import synthetic_csv
    service, study_id, research, _ = prepared_service(tmp_path, eligible=True)
    contract = load_canonical(research / "runner-contract.yml")
    data = synthetic_csv(contract["cases"][0])
    (research / "development.csv").write_bytes(data)
    plan = {"actor": "fixture-owner", "trial_inputs": load_canonical(research / "development-trial-inputs.yml"), "data_path": f"research/{study_id}/development.csv", "data_digest": canonical_digest(data)}
    path = tmp_path / "trial-plan.yml"
    write(path, plan)
    program = r'''
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from writer.service import StudyService
from operations.lifecycle import development
from validator.canonical_yaml import load_canonical
service = StudyService(sys.argv[1], sys.argv[3], repository_root=sys.argv[2], allow_draft=True)
original_publish, original_append = service.publish_artifact, service.append_event
def publish(study_id, path, value):
    result = original_publish(study_id, path, value)
    if sys.argv[6] == "candidate-artifact" and path.endswith("candidate.yml"): os._exit(71)
    return result
def append(study_id, kind, *args, **kwargs):
    result = original_append(study_id, kind, *args, **kwargs)
    if sys.argv[6] == "trial-event" and kind == "trial-recorded": os._exit(71)
    return result
service.publish_artifact, service.append_event = publish, append
development(service, sys.argv[4], load_canonical(Path(sys.argv[5])))
'''
    child = subprocess.run([sys.executable, "-c", program, str(service.workflow_root), str(service.repository_root), str(service.authority.root), study_id, str(path), boundary], capture_output=True, text=True)
    assert child.returncode == 71, child.stderr
    outputs = list((service.study_root(study_id) / "operations").glob("*/runtime/run/evidence.yml"))
    assert len(outputs) == 1
    original = outputs[0].read_bytes()
    (research / "runner.py").write_text('raise AssertionError("must not rerun")\n')
    cli(service.workflow_root, service.repository_root, service.authority.root, "resume", study_id)
    assert outputs[0].read_bytes() == original
    assert service.validate(study_id)["lifecycle"]["event_count"] == 4
