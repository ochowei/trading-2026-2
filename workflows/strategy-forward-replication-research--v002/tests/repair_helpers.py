"""完整 CLI fixture：contract 與 runner 共用相同 frozen engine。"""

import json
import shutil
import subprocess
import sys

import exchange_calendars as xcals
from operations.legacy_checks import _make_bars
from operations.preflight import synthetic_csv
from test_operations import PACKAGE, fixture_repository, refresh_bundle, write
from validator.canonical_yaml import canonical_digest, load_canonical


def full_repository(tmp_path):
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
    (engine.parent / "__init__.py").write_text("# 隔離 fixture package\n")
    shutil.copyfile(PACKAGE / "tests/fixtures/contract_runner.py", research / "runner.py")
    prereg = load_canonical(research / "preregistration.yml")
    # 此案例只驗證執行鏈：降低 fixture 本身門檻，不改 Workflow Floors 或正式研究。
    prereg["eligibility_rules"]["development_gates"] = {
        "completed_trades": {"operator": ">=", "value": 1}
    }
    prereg["eligibility_rules"].pop("research_targets", None)
    prereg["eligibility_rules"]["development_diagnostics"]["block_bootstrap"]["repetitions"] = 100
    write(research / "preregistration.yml", prereg)
    qualification = load_canonical(research / "qualification-spec.yml")
    qualification["development"] = prereg["eligibility_rules"]["development_gates"]
    qualification["preregistration_digest"] = canonical_digest(prereg)

    # 舊合約名稱依文件的真正路徑同步。
    def sync(value):
        if isinstance(value, dict):
            for key in value:
                if key == "development_gates":
                    value[key] = prereg["eligibility_rules"]["development_gates"]
                elif key == "repetitions":
                    value[key] = 100
                else:
                    sync(value[key])
        elif isinstance(value, list):
            for item in value:
                sync(item)

    sync(qualification)
    write(research / "qualification-spec.yml", qualification)
    contract = load_canonical(research / "runner-contract.yml")
    cases = []
    calendar = xcals.get_calendar("XNYS")
    for stage, year in (("development", 2014), ("historical-evaluation", 2020)):
        for expect in ("trades", "no-trades"):
            frame = _make_bars(180, [36, 90] if expect == "trades" else [], close_direction="above")
            dates = calendar.sessions_in_range(f"{year}-01-02", f"{year}-12-31")[:180]
            rows = [
                [day.strftime("%Y-%m-%d"), *[str(v) for v in row]]
                for day, row in zip(dates, frame.to_numpy(), strict=True)
            ]
            cases.append({"stage": stage, "expect": expect, "rows": rows})
    contract["cases"] = cases
    write(research / "runner-contract.yml", contract)
    data = synthetic_csv(cases[0])
    (research / "development.csv").write_bytes(data)
    inputs = load_canonical(research / "development-trial-inputs.yml")
    inputs["trial_id"] = inputs["candidate_id"]
    inputs["preregistration_digest"] = canonical_digest(prereg)
    inputs["development_diagnostics"]["repetitions"] = 100
    inputs["development_runner_path"] = f"research/{study_id}/runner.py"
    inputs["study_procedure_digest"] = canonical_digest((research / "runner.py").read_bytes())
    inputs["strategy_engine_digest"] = canonical_digest(engine.read_bytes())
    inputs["data_bindings"]["development_path"] = f"research/{study_id}/development.csv"
    inputs["data_bindings"]["development_digest"] = canonical_digest(data)
    refresh_bundle(repository, research)
    bundle = load_canonical(research / "source-bundle.yml")
    bundle["files"] = [f for f in bundle["files"] if not f["path"].endswith(".csv")]
    bundle["files"].append(
        {
            "path": engine.relative_to(repository).as_posix(),
            "digest": inputs["strategy_engine_digest"],
        }
    )
    write(research / "source-bundle.yml", bundle)
    bundle["files"].append(
        {
            "path": (engine.parent / "__init__.py").relative_to(repository).as_posix(),
            "digest": canonical_digest((engine.parent / "__init__.py").read_bytes()),
        }
    )
    write(research / "source-bundle.yml", bundle)
    inputs["source_bundle_digest"] = canonical_digest(bundle)
    write(research / "development-trial-inputs.yml", inputs)
    return repository, package, study_id, authority, research


def cli(package, repository, authority, *arguments):
    process = subprocess.run(
        [
            sys.executable,
            str(package / "operations/cli.py"),
            "--repository-root",
            str(repository),
            "--authority-root",
            str(authority),
            "--allow-draft",
            *map(str, arguments),
        ],
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    return json.loads(process.stdout)


def freeze_plan(service):
    calendar = xcals.get_calendar("XNYS")
    snapshots = []
    for interval in service.rules.workflow["data_intervals"]["intervals"]:
        snapshots.append(
            {
                "schema_version": 1,
                "role": interval["role"],
                "provider": "yahoo",
                "symbols": ["TEST"],
                "timezone": "America/New_York",
                "calendar": "XNYS",
                "interval": "1d",
                "adjustment_policy": "auto_adjusted",
                "fields": ["open", "high", "low", "close", "volume"],
                "data_digest": "d" * 64,
                "sessions": [
                    day.strftime("%Y-%m-%d")
                    for day in calendar.sessions_in_range(
                        interval["start_date"], interval["end_date"]
                    )
                ],
            }
        )
    return {
        "actor": "fixture-owner",
        "provenance": {
            "status": "verified-clean",
            "sources": ["isolated-synthetic-only"],
            "outcome_exposure": "none",
        },
        "snapshot_set": {"schema_version": 1, "snapshots": snapshots},
    }


def prepared_service(tmp_path, *, eligible=False, targets=None):
    from operations.service import create_authorize
    from test_operations import passed_report, plan_for
    from writer.service import StudyService

    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    prereg = load_canonical(research / "preregistration.yml")
    if eligible:
        prereg["eligibility_rules"]["development_gates"]["completed_trades"]["value"] = 1
    if targets:
        prereg["eligibility_rules"]["research_targets"] = targets
    write(research / "preregistration.yml", prereg)
    refresh_bundle(repository, research)
    report = passed_report(repository, package, study_id, authority)
    service = StudyService(package, authority, repository_root=repository, allow_draft=True)
    plan = plan_for(study_id, research)
    create_authorize(service, plan, report)
    return service, study_id, research, report


def publish_trial(service, study_id, research, *, no_trades=False):
    from operations.preflight import launch
    from operations.publication import consume

    prereg = load_canonical(research / "preregistration.yml")
    inputs = load_canonical(research / "development-trial-inputs.yml")
    bundle = load_canonical(research / "source-bundle.yml")
    contract = load_canonical(research / "runner-contract.yml")
    run = service.repository_root / "synthetic-run"
    run.mkdir()
    data = synthetic_csv(contract["cases"][1 if no_trades else 0])
    (run / "bars.csv").write_bytes(data)
    request = {
        "stage": "development",
        "data_path": "synthetic-run/bars.csv",
        "data_digest": canonical_digest(data),
        "preregistration": prereg,
        "trial_inputs": inputs,
        "source_bundle": bundle,
    }
    write(run / "request.yml", request)
    launch(
        service.repository_root,
        service.workflow_root,
        contract["runners"]["development"],
        run / "request.yml",
        run / "output.yml",
    )
    envelope = load_canonical(run / "output.yml")
    payload = consume(service, study_id, envelope, inputs, prereg, canonical_digest(bundle))
    service.append_event(study_id, "trial-recorded", "fixture-owner", payload)
    return payload
