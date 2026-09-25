from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from helpers import development_inputs, preregistration
from operations.preflight import binding, runner_preflight, verify_report
from operations.service import create, prepare
from validator.canonical_yaml import canonical_bytes, canonical_digest, load_canonical
from validator.errors import IntegrityError, ValidationError
from writer.journal import JournalPublisher
from writer.service import StudyService

PACKAGE = Path(__file__).resolve().parents[1]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def fixture_repository(tmp_path):
    repository = tmp_path / "repository"
    package = repository / "workflows" / PACKAGE.name
    shutil.copytree(
        PACKAGE,
        package,
        ignore=shutil.ignore_patterns(
            "studies", "__pycache__", "release-manifest.yml", "release-test-report.yml"
        ),
    )
    study_id = "runner-fixture"
    research = repository / "research" / study_id
    research.mkdir(parents=True)
    runner = research / "runner.py"
    shutil.copyfile(PACKAGE / "tests/fixtures/runner.py", runner)
    prereg = preregistration()
    prereg["eligibility_rules"]["development_gates"]["completed_trades"]["value"] = 100
    write(research / "preregistration.yml", prereg)
    for name in ("qualification-spec", "candidate-definition", "implementation-contract"):
        write(research / f"{name}.yml", {"schema_version": 1})
    write(
        research / "development-trial-inputs.yml",
        development_inputs(canonical_digest(prereg), "a" * 64),
    )
    cases = []
    for stage, year in (("development", 2014), ("historical-evaluation", 2020)):
        for expectation in ("trades", "no-trades"):
            prices = (
                [100, 101, 103, 101, 100, 101, 99, 101] if expectation == "trades" else [100] * 8
            )
            days = ["01-06", "01-07", "01-08", "01-09", "01-13", "01-14", "01-15", "01-16"]
            if stage == "historical-evaluation":
                days = ["03-02", "03-03", "03-04", "03-05", "03-09", "03-10", "03-11", "03-12"]
            rows = [
                [f"{year}-{day}", price, price + 1, price - 1, price, 1000]
                for day, price in zip(days, prices, strict=True)
            ]
            cases.append({"stage": stage, "expect": expectation, "rows": rows})
    relative = runner.relative_to(repository).as_posix()
    write(
        research / "runner-contract.yml",
        {
            "protocol": "request-output-v1",
            "synthetic_only": True,
            "runners": {"development": relative, "historical-evaluation": relative},
            "cases": cases,
        },
    )
    refresh_bundle(repository, research)
    return repository, package, study_id, tmp_path / "authority", research


def refresh_bundle(repository, research):
    files = [
        {
            "path": path.relative_to(repository).as_posix(),
            "digest": canonical_digest(path.read_bytes()),
        }
        for path in sorted(research.iterdir())
        if path.name not in {"source-bundle.yml", "development-trial-inputs.yml"}
    ]
    write(research / "source-bundle.yml", {"schema_version": 1, "files": files})


def passed_report(repository, package, study_id, authority):
    report = runner_preflight(repository, study_id, authority, package)
    # These tests isolate runner/writer integration; prepare's contract checks have separate cases.
    report["prepare_checks"] = "passed"
    return report


def assignment_for(study_id, actor="fixture-owner", role="study 開發者"):
    return {
        "schema_version": 1,
        "source_id": "synthetic-test-case",
        "instruction": "隔離測試派工，不代表正式 Study 指令",
        "assigner": "test-harness",
        "assignee": actor,
        "role": role,
        "study_id": study_id,
        "workflow_version": "v005",
        "scope": "development-to-freeze"
        if role == "study 開發者"
        else "historical-evaluation-to-terminal",
    }


def make_service(package, authority, repository, study_id, *, evaluation=False):
    actor = "fixture-evaluator" if evaluation else "fixture-owner"
    role = "Study 歷史評估執行者" if evaluation else "study 開發者"
    return StudyService(
        package,
        authority,
        repository_root=repository,
        allow_draft=True,
        actor=actor,
        role=role,
        assignment=assignment_for(study_id, actor, role),
    )


def plan_for(study_id, research):
    return {
        "study_id": study_id,
        "creator": "fixture-owner",
        "identity": {
            "research_round_id": "round-1",
            "experiment_family": "family-1",
            "research_owner": "fixture-owner",
            "historical_evaluation_operator": "fixture-evaluator",
        },
        "preregistration": load_canonical(research / "preregistration.yml"),
        "development_actor": "fixture-owner",
    }


def test_real_cli_runs_both_stages_and_accepts_gate_fail_and_no_trades(tmp_path):
    repository, package, study_id, authority, _ = fixture_repository(tmp_path)
    report = passed_report(repository, package, study_id, authority)
    assert len(report["cases"]) == 4
    assert report["cases"][0]["validation"]["candidate"]["failed_gates"] == ["completed_trades"]
    assert report["cases"][1]["validation"]["candidate"]["trades"] == 0
    assert not (package / "studies").exists()
    assert not authority.exists()


@pytest.mark.parametrize("fault", ["import", "spec", "evidence", "network", "external-read"])
def test_runner_fault_precedes_first_event(tmp_path, fault):
    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    runner = research / "runner.py"
    text = runner.read_text()
    if fault == "import":
        text = text.replace("import argparse", "import research.missing_module")
    elif fault == "spec":
        text = text.replace("spec=model, cost=0.1", 'spec=model, **{"spec": model}, cost=0.1')
    elif fault == "evidence":
        text = text.replace("canonical_bytes(result)", 'canonical_bytes({"invalid": True})')
    elif fault == "network":
        text = text.replace(
            "request = load_canonical(args.request)",
            'import socket\n    socket.create_connection(("127.0.0.1", 9))\n    request = load_canonical(args.request)',
        )
    else:
        text = text.replace(
            "request = load_canonical(args.request)",
            'Path("/etc/passwd").read_text()\n    request = load_canonical(args.request)',
        )
    runner.write_text(text)
    refresh_bundle(repository, research)
    with pytest.raises((ValidationError, IntegrityError)):
        runner_preflight(repository, study_id, authority, package)
    assert not (package / "studies").exists()
    assert not authority.exists()


@pytest.mark.parametrize("target", ["runner.py", "qualification-spec.yml"])
def test_create_rejects_stale_report_before_any_event(tmp_path, target):
    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    report = passed_report(repository, package, study_id, authority)
    (research / target).write_text((research / target).read_text() + "\n")
    with pytest.raises(IntegrityError):
        create(
            make_service(package, authority, repository, study_id),
            plan_for(study_id, research),
            report,
        )
    assert not (package / "studies").exists()
    assert not authority.exists()


def test_prepare_failure_does_not_publish(tmp_path):
    repository, package, study_id, authority, _ = fixture_repository(tmp_path)
    with pytest.raises(ValidationError):
        prepare(repository, study_id, authority, tmp_path / "report.yml", package)
    assert not (package / "studies").exists()
    assert not authority.exists()
    assert not (tmp_path / "report.yml").exists()


@pytest.mark.parametrize("interrupt_at", [1, 2, 3])
def test_batch_recovers_exact_events_without_duplicates(tmp_path, monkeypatch, interrupt_at):
    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    report = passed_report(repository, package, study_id, authority)
    service = make_service(package, authority, repository, study_id)
    plan = plan_for(study_id, research)
    original = JournalPublisher._complete
    count = 0

    def interrupt(self, journal):
        nonlocal count
        count += 1
        if count == interrupt_at:
            raise RuntimeError("fixture interruption after prepare")
        original(self, journal)

    monkeypatch.setattr(JournalPublisher, "_complete", interrupt)
    with pytest.raises(RuntimeError):
        create(service, plan, report)
    monkeypatch.setattr(JournalPublisher, "_complete", original)
    result = create(service, plan, report)
    assert len(result["completed"]) == 3
    assert result["operation_id"] == canonical_digest(
        load_canonical(service.study_root(study_id) / "manifests/create-operation.yml")
    )
    assert service.validate(study_id)["lifecycle"]["event_count"] == 3
    assert create(service, plan, report) == result
    assert len(service.authority.checkpoints(study_id)) == 3
    changed = dict(plan, creator="another-actor")
    with pytest.raises(ValidationError):
        create(service, changed, report)


def test_runner_only_report_is_not_authorization(tmp_path):
    repository, package, study_id, authority, _ = fixture_repository(tmp_path)
    with pytest.raises(ValidationError):
        verify_report(
            {"status": "passed", "binding": binding(repository, study_id, authority, package)},
            repository,
            study_id,
            authority,
            package,
        )


def test_complete_prepare_then_create_without_skipping_contract(tmp_path):
    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    fixture = PACKAGE / "tests/fixtures/contract"
    for name in (
        "preregistration.yml",
        "qualification-spec.yml",
        "candidate-definition.yml",
        "implementation-contract.yml",
        "development-trial-inputs.yml",
    ):
        write(research / name, load_canonical(fixture / name))
    engine = repository / "src/trading_2026_2/tsm_mean_reversion_reversal_trigger_v001.py"
    engine.parent.mkdir(parents=True)
    shutil.copyfile(fixture / "engine.py", engine)
    # 保留策略合約；測試 runner 使用同一初始資金，資料只取合成 rows。
    text = (research / "runner.py").read_text().replace("equity = 10000.0", "equity = 100000.0")
    (research / "runner.py").write_text(text)
    inputs = load_canonical(research / "development-trial-inputs.yml")
    inputs["trial_id"] = "fixture-trial"
    inputs["development_runner_path"] = f"research/{study_id}/runner.py"
    inputs["study_procedure_digest"] = canonical_digest((research / "runner.py").read_bytes())
    inputs["strategy_engine_digest"] = canonical_digest(engine.read_bytes())
    refresh_bundle(repository, research)
    bundle = load_canonical(research / "source-bundle.yml")
    bundle["files"].append(
        {
            "path": engine.relative_to(repository).as_posix(),
            "digest": inputs["strategy_engine_digest"],
        }
    )
    write(research / "source-bundle.yml", bundle)
    inputs["source_bundle_digest"] = canonical_digest(bundle)
    write(research / "development-trial-inputs.yml", inputs)
    report = prepare(repository, study_id, authority, tmp_path / "prepared.yml", package)
    assert report["prepare_checks"] == "passed"
    result = create(
        make_service(package, authority, repository, study_id), plan_for(study_id, research), report
    )
    assert result["completed"][-1] == "development-started"
