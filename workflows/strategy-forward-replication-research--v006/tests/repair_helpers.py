"""完整 CLI fixture：contract 與 runner 共用相同 frozen engine。"""

import json
import subprocess
import sys

import exchange_calendars as xcals
from operations.preflight import synthetic_csv
from test_operations import (
    assignment_for,
    fixture_repository,
    make_service,
    refresh_bundle,
    write,
)
from validator.canonical_yaml import canonical_digest, load_canonical


def full_repository(tmp_path):
    # 完整 engine、runner、Source Bundle 已由共用 fixture 準備，所有衍生修改一致重綁。
    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    prereg = load_canonical(research / "preregistration.yml")
    prereg["eligibility_rules"]["development_gates"]["completed_trades"]["value"] = 1
    write(research / "preregistration.yml", prereg)
    refresh_bundle(repository, research)
    return repository, package, study_id, authority, research


def cli(package, repository, authority, *arguments):
    args = list(map(str, arguments))
    role = "study 開發者"
    if "--role" in args:
        i = args.index("--role")
        role = args[i + 1]
        del args[i : i + 2]
    if (
        args[0] not in {"prepare", "runner-preflight", "status", "validate"}
        and "--assignment" not in args
    ):
        assignment = repository / (
            "evaluation-assignment.yml" if role != "study 開發者" else "assignment.yml"
        )
        write(
            assignment,
            assignment_for(
                "runner-fixture",
                "fixture-evaluator" if role != "study 開發者" else "fixture-owner",
                role,
            ),
        )
        args.extend(["--assignment", str(assignment)])
    process = subprocess.run(
        [
            sys.executable,
            str(package / "operations/cli.py"),
            "--repository-root",
            str(repository),
            "--authority-root",
            str(authority),
            "--allow-draft",
            "--role",
            role,
            *args,
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
    from operations.service import create
    from test_operations import passed_report, plan_for

    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    prereg = load_canonical(research / "preregistration.yml")
    if eligible:
        prereg["eligibility_rules"]["development_gates"]["completed_trades"]["value"] = 1
    if targets:
        prereg["eligibility_rules"]["research_targets"] = targets
    write(research / "preregistration.yml", prereg)
    refresh_bundle(repository, research)
    report = passed_report(repository, package, study_id, authority)
    service = make_service(package, authority, repository, study_id)
    plan = plan_for(study_id, research)
    create(service, plan, report)
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
