"""v003 派工、資格與隔離邊界；全部使用 tmp_path 合成資料。"""

from pathlib import Path

import pytest
from operations.evaluation import historical_evaluation
from operations.lifecycle import freeze, freeze_readiness, resume, status, terminate
from operations.service import create
from repair_helpers import cli, freeze_plan, full_repository, prepared_service, publish_trial
from test_operations import (
    fixture_repository,
    make_service,
    plan_for,
    write,
)
from validator.assignments import AssignmentError
from validator.canonical_yaml import canonical_bytes, canonical_digest, load_canonical
from validator.errors import WorkflowError
from validator.study import validate_study
from writer.service import StudyService


def evaluation_fixture(tmp_path, *, passing=False):
    import exchange_calendars as xcals
    from operations.preflight import synthetic_csv

    service, study_id, research, report = prepared_service(tmp_path, eligible=True)
    publish_trial(service, study_id, research)
    days = xcals.get_calendar("XNYS").sessions_in_range("2020-01-01", "2024-12-31")
    rows = [[day.strftime("%Y-%m-%d"), 100, 101, 99, 100, 1000] for day in days]
    if passing:
        for offset in range(4, len(rows) - 3, 4):
            if (
                rows[offset][0][:4] != rows[offset + 2][0][:4]
                or not "02-01" <= rows[offset][0][5:] <= "11-30"
            ):
                continue
            rows[offset + 1][1:5] = [101, 102, 100, 101]
            rows[offset + 2][1:5] = [103, 104, 102, 103]
    data = synthetic_csv({"rows": rows})
    (research / "synthetic-evaluation.csv").write_bytes(data)
    plan = freeze_plan(service)
    for snap in plan["snapshot_set"]["snapshots"]:
        if snap["role"] == "historical-evaluation":
            snap["data_digest"] = canonical_digest(data)
    freeze(service, study_id, plan)
    evaluator = make_service(
        service.workflow_root,
        service.authority.root,
        service.repository_root,
        study_id,
        evaluation=True,
    )
    return (
        service,
        evaluator,
        study_id,
        {
            "actor": "fixture-evaluator",
            "data_path": f"research/{study_id}/synthetic-evaluation.csv",
            "data_digest": canonical_digest(data),
        },
    )


def test_cli_continuous_without_approval(tmp_path):
    repo, package, study_id, authority, research = full_repository(tmp_path)
    service = make_service(package, authority, repo, study_id)
    inputs = load_canonical(research / "development-trial-inputs.yml")
    plan = {
        "create": plan_for(study_id, research),
        "development": [
            {
                "actor": "fixture-owner",
                "trial_inputs": inputs,
                "data_path": inputs["data_bindings"]["development_path"],
                "data_digest": inputs["data_bindings"]["development_digest"],
            }
        ],
        "freeze": freeze_plan(service),
    }
    path = tmp_path / "continuous.yml"
    write(path, plan)
    result = cli(package, repo, authority, "develop-to-freeze", study_id, "--plan", path)
    assert result["result"]["scope_boundary"] == "development-to-freeze"
    assert (
        cli(package, repo, authority, "develop-to-freeze", study_id, "--plan", path)["result"]
        == result["result"]
    )
    assert service.validate(study_id)["lifecycle"]["current_event"] == "candidate-frozen"
    assert not (repo / "historical-evaluation-artifacts").exists()


def test_evaluation_once_and_developer_no_store_reads(tmp_path, monkeypatch):
    developer, evaluator, study_id, plan = evaluation_fixture(tmp_path)
    result = historical_evaluation(evaluator, study_id, plan)
    assert result["outcome"] == "fail"
    assert historical_evaluation(evaluator, study_id, plan) == result
    assert evaluator.validate(study_id)["lifecycle"]["event_count"] == 10
    store = evaluator.rules.historical_evaluation_artifacts_root
    original = Path.open

    def guarded(path, *args, **kwargs):
        if store == path or store in path.resolve().parents:
            raise AssertionError("開發角色不得開啟假評估 store")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    assert status(developer, study_id, role="study 開發者")["later_stage"] == "not_inspected"
    for operation in (
        lambda: resume(developer, study_id),
        lambda: developer.validate(study_id),
        lambda: historical_evaluation(developer, study_id, plan),
    ):
        with pytest.raises(WorkflowError):
            operation()


@pytest.mark.parametrize(
    "field,value",
    [
        ("study_id", "another-study"),
        ("workflow_version", "v002"),
        ("assignee", "other"),
        ("role", "Study 歷史評估執行者"),
        ("scope", "historical-evaluation-to-terminal"),
    ],
)
def test_wrong_assignment_before_writes(tmp_path, field, value):
    repo, package, study_id, authority, research = fixture_repository(tmp_path)
    service = make_service(package, authority, repo, study_id)
    service.assignment[field] = value
    with pytest.raises(WorkflowError):
        service.publish_artifact(study_id, "evidence/x.yml", {})
    assert not (package / "studies").exists()


@pytest.mark.parametrize("method", ["publish", "create", "append", "recover"])
def test_public_writer_requires_context(tmp_path, method):
    repo, package, study_id, authority, _ = fixture_repository(tmp_path)
    service = StudyService(package, authority, repository_root=repo, allow_draft=True)
    calls = {
        "publish": lambda: service.publish_artifact(study_id, "x.yml", {}),
        "create": lambda: service.create_study(
            study_id,
            "owner",
            research_round_id="r",
            experiment_family="f",
            research_owner="owner",
            source_bundle={},
        ),
        "append": lambda: service.append_event(study_id, "study-created", "owner", {}),
        "recover": lambda: service.recover(study_id),
    }
    with pytest.raises(AssignmentError, match="派工"):
        calls[method]()
    assert not (package / "studies").exists()


@pytest.mark.parametrize(
    "field",
    [
        "preregistration_actor",
        "preregistration_approval",
        "development_authorization",
        "authorization",
    ],
)
def test_legacy_plan_rejected(tmp_path, field):
    repo, package, study_id, authority, research = fixture_repository(tmp_path)
    service = make_service(package, authority, repo, study_id)
    plan = plan_for(study_id, research)
    plan[field] = {}
    with pytest.raises(WorkflowError, match="核准"):
        create(service, plan, {})
    assert not (package / "studies").exists()


@pytest.mark.parametrize("kind", ["preregistration-approved", "development-authorized"])
def test_legacy_events_rejected(tmp_path, kind):
    service, study_id, _, _ = prepared_service(tmp_path)
    with pytest.raises(WorkflowError):
        service.append_event(study_id, kind, "fixture-owner", {})


@pytest.mark.parametrize(
    "name",
    [
        "manifests/create-plan.yml",
        "manifests/prepare-report.yml",
        "manifests/create-operation.yml",
        "manifests/preregistration.yml",
        "assignment",
    ],
)
@pytest.mark.parametrize("fault", ["missing", "changed"])
def test_historical_proofs_not_cache(tmp_path, name, fault):
    service, study_id, _, _ = prepared_service(tmp_path)
    root = service.study_root(study_id)
    path = (
        next((root / "manifests/assignments").glob("*.yml"))
        if name == "assignment"
        else root / name
    )
    if fault == "missing":
        path.unlink()
    else:
        value = load_canonical(path)
        value["tampered"] = True
        path.write_bytes(canonical_bytes(value))
    for operation in (lambda: service.validate(study_id), lambda: service.recover(study_id)):
        with pytest.raises((WorkflowError, FileNotFoundError)):
            operation()


@pytest.mark.parametrize("mode", ["no-trades", "gate-fail", "target-only"])
def test_unsuccessful_trials_do_not_freeze(tmp_path, mode):
    service, study_id, research, _ = prepared_service(
        tmp_path,
        eligible=mode != "gate-fail",
        targets={"base_return": {"operator": ">", "value": "100"}}
        if mode == "target-only"
        else None,
    )
    publish_trial(service, study_id, research, no_trades=mode == "no-trades")
    with pytest.raises(WorkflowError):
        freeze_readiness(service, study_id, freeze_plan(service))
    assert validate_study(service.study_root(study_id), service.rules).candidate is None


@pytest.mark.parametrize("fault", ["baseline", "registry", "provenance", "selection", "threshold"])
def test_qualification_and_evidence_tampering(tmp_path, fault):
    from operations.lifecycle import freeze_steps

    service, study_id, research, _ = prepared_service(tmp_path, eligible=True)
    payload = publish_trial(service, study_id, research)
    plan = freeze_plan(service)
    if fault == "baseline":
        publication = load_canonical(service.study_root(study_id) / payload["publication_path"])
        (service.study_root(study_id) / publication["artifacts"]["baseline"]["path"]).unlink()
        with pytest.raises(WorkflowError):
            freeze(service, study_id, plan)
    elif fault == "provenance":
        plan["provenance"]["status"] = "provenance-unknown"
        with pytest.raises(WorkflowError):
            freeze(service, study_id, plan)
    elif fault == "threshold":
        path = service.study_root(study_id) / "manifests/preregistration.yml"
        value = load_canonical(path)
        value["evaluation_gates"] = {"total_return": "-100"}
        write(path, value)
        with pytest.raises(WorkflowError):
            freeze(service, study_id, plan)
    else:
        stages = freeze_steps(service, study_id, plan)
        if fault == "registry":
            kind, actor, value = stages[0]
            value["recorded_trial_count"] = 0
            with pytest.raises(WorkflowError):
                service.append_event(study_id, kind, actor, value)
        else:
            for kind, actor, value in stages[:2]:
                service.append_event(study_id, kind, actor, value)
            kind, actor, value = stages[-1]
            value["selected_candidate_id"] = "forged"
            with pytest.raises(WorkflowError):
                service.append_event(study_id, kind, actor, value)


@pytest.mark.parametrize("reason", ["unavailable", "no-eligible-candidate"])
def test_early_terminal(tmp_path, reason):
    service, study_id, research, _ = prepared_service(tmp_path)
    if reason == "no-eligible-candidate":
        publish_trial(service, study_id, research)
    outcome = "fail" if reason == "no-eligible-candidate" else "indeterminate"
    plan = {
        "actor": "fixture-owner",
        "reason_kind": reason,
        "evidence_unavailable": {
            "stage": "development",
            "unavailable_path": "evidence/missing.yml",
            "reason": "隔離測試",
        },
        "terminal_evidence": {
            "schema_version": 1,
            "outcome": outcome,
            "authority": "none",
            "recomputed": True,
            "reasons": ["隔離測試"],
        },
    }
    terminate(service, study_id, plan)
    resume(service, study_id)
    assert service.validate(study_id)["outcome"]["status"] == outcome


def test_pause_retains_evaluation_operation(tmp_path, monkeypatch):
    _, service, study_id, plan = evaluation_fixture(tmp_path)
    import operations.evaluation as operation

    original = operation.atomic_create

    def stop(path, data):
        original(path, data)
        if path.name == "data-access.yml":
            raise RuntimeError("啟動前中斷")

    monkeypatch.setattr(operation, "atomic_create", stop)
    with pytest.raises(RuntimeError):
        historical_evaluation(service, study_id, plan)
    monkeypatch.setattr(operation, "atomic_create", original)
    state = validate_study(service.study_root(study_id), service.rules)
    op = state.evaluation_operation["operation_id"]
    with pytest.raises(WorkflowError):
        service.append_event(
            study_id,
            "study-paused",
            service.actor,
            {"reason": "測試", "frozen_operation_digest": "a" * 64},
        )
    service.append_event(
        study_id, "study-paused", service.actor, {"reason": "測試", "frozen_operation_digest": op}
    )
    service.append_event(study_id, "study-resumed", service.actor, {"frozen_operation_digest": op})
    assert historical_evaluation(service, study_id, plan)["outcome"] == "fail"


@pytest.mark.parametrize("command", ["status", "validate", "resume", "development"])
def test_developer_symlinks_rejected_before_restricted_read(tmp_path, monkeypatch, command):
    service, study_id, _, _ = prepared_service(tmp_path)
    store = service.repository_root / "historical-evaluation-artifacts"
    store.mkdir()
    secret = store / "secret.yml"
    secret.write_text("THIS MUST NOT BE READ")
    root = service.study_root(study_id)
    event = next((root / "events").glob("*.yml"))
    event.unlink()
    event.symlink_to(secret)
    original = Path.open

    def guard(path, *args, **kwargs):
        if store in path.resolve().parents:
            raise AssertionError("嘗試讀取禁止 store")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard)
    with pytest.raises(WorkflowError):
        if command in {"status", "validate"}:
            status(service, study_id, role="study 開發者")
        elif command == "resume":
            resume(service, study_id)
        else:
            from operations.lifecycle import development

            development(service, study_id, {"actor": service.actor})


def test_cli_rejects_old_entry_and_requires_role(tmp_path):
    import subprocess
    import sys

    from test_operations import PACKAGE

    for args in (["create-authorize"], ["--role", "study 開發者", "create-authorize"]):
        result = subprocess.run(
            [sys.executable, str(PACKAGE / "operations/cli.py"), *args],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0


def test_changed_authority_and_assignment_cannot_resume(tmp_path):
    service, study_id, _, _ = prepared_service(tmp_path)
    changed = make_service(
        service.workflow_root, tmp_path / "different-authority", service.repository_root, study_id
    )
    with pytest.raises(WorkflowError):
        resume(changed, study_id)
    service.assignment["instruction"] = "不同派工"
    with pytest.raises(WorkflowError):
        service.recover(study_id)
    with pytest.raises(WorkflowError):
        service.append_event(
            study_id,
            "study-paused",
            service.actor,
            {"reason": "測試", "frozen_operation_digest": "a" * 64},
        )


def test_zero_trial_terminal_and_no_development_before_record(tmp_path):
    from operations.lifecycle import development

    repo, package, study_id, authority, _ = fixture_repository(tmp_path)
    service = make_service(package, authority, repo, study_id)
    with pytest.raises(WorkflowError):
        development(
            service, study_id, {"actor": service.actor, "trial_inputs": {"candidate_id": "trial-1"}}
        )
    # Zero-trial failure remains a legal transition from development-started.
    service, study_id, _, _ = prepared_service(tmp_path / "created")
    service.append_event(
        study_id,
        "trial-registry-frozen",
        service.actor,
        {
            "maximum_trials": 1,
            "recorded_trial_count": 0,
            "complete_family_trial_ids": [],
            "trial_registry_digest": canonical_digest({"trials": []}),
            "candidate_available": False,
        },
    )
    assert (
        validate_study(service.study_root(study_id), service.rules).pending_terminal_outcome
        == "fail"
    )


def test_cli_evaluator_pass_to_terminal_without_approval(tmp_path):
    _, service, study_id, plan = evaluation_fixture(tmp_path, passing=True)
    path = tmp_path / "evaluation.yml"
    write(path, plan)
    result = cli(
        service.workflow_root,
        service.repository_root,
        service.authority.root,
        "--role",
        "Study 歷史評估執行者",
        "historical-evaluation",
        study_id,
        "--plan",
        path,
    )
    assert result["result"]["outcome"] == "pass"
    assert service.validate(study_id)["outcome"]["authority"] == "retrospectively-supported"


def test_low_level_store_publication_requires_started(tmp_path):
    repo, package, study_id, authority, _ = fixture_repository(tmp_path)
    service = make_service(package, authority, repo, study_id, evaluation=True)
    with pytest.raises(WorkflowError):
        service.publish_historical_evaluation_artifact(study_id, "evidence/forged.yml", {})
    assert not (repo / "historical-evaluation-artifacts").exists()
