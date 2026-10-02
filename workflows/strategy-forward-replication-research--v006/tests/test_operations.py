from __future__ import annotations

import shutil
from pathlib import Path

import pytest
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
    """完整人造研究來源；runner 與原生 guard 呼叫同一份 frozen engine。"""
    from copy import deepcopy

    import exchange_calendars as xcals
    from operations.legacy_checks import _make_bars
    from operations.preflight import synthetic_csv

    repository = tmp_path / "repository"
    package = repository / "workflows" / PACKAGE.name
    package.mkdir(parents=True)
    # 只複製公開定義，不讀取現有 Study、runtime、authority 或根層發布 artifacts。
    for name in ("rules", "schemas", "validator", "writer", "operations", "tests",
                 "examples", "reference", "policies", "tools"):
        shutil.copytree(PACKAGE / name, package / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("README.md", "workflow.yml"):
        shutil.copyfile(PACKAGE / name, package / name)
    study_id = "runner-fixture"
    research = repository / "research" / study_id
    research.mkdir(parents=True)
    fixture = PACKAGE / "tests/fixtures/contract"
    for name in ("preregistration", "qualification-spec", "candidate-definition",
                 "implementation-contract", "development-trial-inputs"):
        write(research / f"{name}.yml", load_canonical(fixture / f"{name}.yml"))
    engine = repository / "src/trading_2026_2/tsm_mean_reversion_reversal_trigger_v001.py"
    engine.parent.mkdir(parents=True)
    shutil.copyfile(fixture / "engine.py", engine)
    (engine.parent / "__init__.py").write_text("# 隔離人造來源 package\n")
    runner = research / "runner.py"
    shutil.copyfile(PACKAGE / "tests/fixtures/contract_runner.py", runner)
    prereg = load_canonical(research / "preregistration.yml")
    # 保留舊 writer 測試目的：少量合法交易會被 completed_trades=100 拒絕。
    # 只改人造研究門檻；Workflow／Policy 的固定門檻與執行規則不變。
    prereg["eligibility_rules"]["development_gates"] = {
        "completed_trades": {"operator": ">=", "value": 100}
    }
    prereg["eligibility_rules"]["development_diagnostics"]["block_bootstrap"]["repetitions"] = 100
    prereg["evaluation_gates"] = {}
    write(research / "preregistration.yml", prereg)
    cases = []
    calendar = xcals.get_calendar("XNYS")
    for stage, year in (("development", 2014), ("historical-evaluation", 2020)):
        dates = calendar.sessions_in_range(f"{year}-01-02", f"{year}-12-31")[:180]
        for expectation in ("trades", "no-trades"):
            frame = _make_bars(180, [36, 90] if expectation == "trades" else [],
                               close_direction="above")
            rows = [[day.strftime("%Y-%m-%d"), *map(str, row)]
                    for day, row in zip(dates, frame.to_numpy(), strict=True)]
            cases.append({"stage": stage, "expect": expectation, "rows": rows})
    relative = runner.relative_to(repository).as_posix()
    write(research / "runner-contract.yml", {
        "protocol": "request-output-v1", "synthetic_only": True,
        "runners": {"development": relative, "historical-evaluation": relative},
        "cases": cases,
    })
    (research / "development.csv").write_bytes(synthetic_csv(cases[0]))
    inputs = load_canonical(research / "development-trial-inputs.yml")
    inputs["trial_id"] = inputs["candidate_id"]
    inputs["development_runner_path"] = relative
    inputs["development_diagnostics"] = deepcopy({
        "block_lengths": [3, 5], "bootstrap_seed": 20260902, "repetitions": 100,
        "leave_one_signal_year_out": True,
        "seed_application": "exact-same-seed-for-each-block-length",
    })
    for role in ("warmup", "development"):
        inputs["data_bindings"][f"{role}_path"] = f"research/{study_id}/development.csv"
        inputs["data_bindings"][f"{role}_digest"] = canonical_digest(
            (research / "development.csv").read_bytes())
    write(research / "development-trial-inputs.yml", inputs)
    refresh_bundle(repository, research)
    return repository, package, study_id, tmp_path / "authority", research


def refresh_bundle(repository, research):
    """一起重綁資格、事前登記、來源、engine／procedure 與 Trial；資料不入程式 bundle。"""
    from copy import deepcopy

    prereg = load_canonical(research / "preregistration.yml")
    prereg_digest = canonical_digest((research / "preregistration.yml").read_bytes())
    qualification = load_canonical(research / "qualification-spec.yml")
    qualification["preregistration_digest"] = prereg_digest
    qualification["development"] = deepcopy(prereg["eligibility_rules"]["development_gates"])
    qualification["evaluation"] = deepcopy(prereg.get("evaluation_gates", {}))
    qualification["replay"] = deepcopy(prereg.get("replay_gates", {}))
    write(research / "qualification-spec.yml", qualification)
    files = [path for path in sorted(research.iterdir())
             if path.suffix in {".yml", ".py"}
             and path.name not in {"source-bundle.yml", "development-trial-inputs.yml"}]
    files.extend(sorted((repository / "src").rglob("*.py")))
    bundle = {"schema_version": 1, "files": [
        {"path": path.relative_to(repository).as_posix(),
         "digest": canonical_digest(path.read_bytes())} for path in files
    ]}
    write(research / "source-bundle.yml", bundle)
    inputs = load_canonical(research / "development-trial-inputs.yml")
    contract = load_canonical(research / "implementation-contract.yml")
    inputs["preregistration_digest"] = prereg_digest
    inputs["source_bundle_digest"] = canonical_digest(bundle)
    inputs["strategy_engine_digest"] = canonical_digest(
        (repository / contract["engine"]["path"]).read_bytes())
    runner = inputs["development_runner_path"]
    inputs["study_procedure_digest"] = canonical_digest((repository / runner).read_bytes())
    write(research / "development-trial-inputs.yml", inputs)


def passed_report(repository, package, study_id, authority):
    # 取得真正的完整 prepare，不自行填 passed，也不取代原生 guard。
    return prepare(repository, study_id, authority, repository / "prepared.yml", package)


def assignment_for(study_id, actor="fixture-owner", role="study 開發者"):
    return {
        "schema_version": 1,
        "source_id": "synthetic-test-case",
        "instruction": "隔離測試派工，不代表正式 Study 指令",
        "assigner": "test-harness",
        "assignee": actor,
        "role": role,
        "study_id": study_id,
        "workflow_version": "v006",
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
        assert "spec=model, cost=0.1" in text
        text = text.replace("spec=model, cost=0.1", 'spec=model, **{"spec": model}, cost=0.1')
        assert 'spec=model, **{"spec": model}, cost=0.1' in text
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
    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    contract = load_canonical(research / "implementation-contract.yml")
    contract["indicator_contract"]["rsi"]["min_periods"] = 1
    write(research / "implementation-contract.yml", contract)
    refresh_bundle(repository, research)
    with pytest.raises(ValidationError, match="prepare 規格／策略檢查失敗"):
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
    from repair_helpers import full_repository

    repository, package, study_id, authority, research = full_repository(tmp_path)
    report = prepare(repository, study_id, authority, tmp_path / "prepared.yml", package)
    assert report["prepare_checks"] == "passed"
    assert report["native_synthetic"]["check"]["status"] == "passed"
    result = create(
        make_service(package, authority, repository, study_id), plan_for(study_id, research), report
    )
    assert result["completed"][-1] == "development-started"
