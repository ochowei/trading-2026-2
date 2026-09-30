"""純合成的 Development 多資產契約；不讀取真實 Study 或評估資料。"""

from __future__ import annotations

from copy import deepcopy

import pytest
from operations.lifecycle import development
from operations.multi_asset import MAX_ASSETS, snapshot_identity, validate_assets
from operations.preflight import runner_preflight, synthetic_csv
from repair_helpers import freeze_plan
from test_operations import (
    fixture_repository,
    make_service,
    passed_report,
    plan_for,
    refresh_bundle,
    write,
)
from validator.artifacts import validate_snapshot_set
from validator.canonical_yaml import canonical_digest, load_canonical
from validator.errors import IntegrityError, ValidationError


def setup_assets(tmp_path, count, *, eligible=False):
    from operations.service import create

    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    if eligible:
        prereg = load_canonical(research / "preregistration.yml")
        prereg["eligibility_rules"]["development_gates"]["completed_trades"]["value"] = 1
        write(research / "preregistration.yml", prereg)
    contract = load_canonical(research / "runner-contract.yml")
    for case in contract["cases"]:
        if case["stage"] == "development":
            rows = case.pop("rows")
            rows.insert(4, ["2014-01-10", *rows[3][1:]])
            case["assets"] = [
                {"asset_id": f"A{n:02d}", "use": "trade" if n == 0 else "reference", "rows": deepcopy(rows)}
                for n in range(count)
            ]
    write(research / "runner-contract.yml", contract)
    refresh_bundle(repository, research)
    source_case = contract["cases"][0]["assets"][0]
    data = synthetic_csv(source_case)
    assets = []
    for n in range(count):
        asset_id = f"A{n:02d}"
        path = research / f"{asset_id}.csv"
        path.write_bytes(data)
        assets.append({
            "asset_id": asset_id,
            "use": "trade" if n == 0 else "reference",
            "provider": "yahoo",
            "symbol": "TSM" if n == 0 else f"SOXX-{n}",
            "data_path": path.relative_to(repository).as_posix(),
            "data_digest": canonical_digest(data),
            "start_date": source_case["rows"][0][0],
            "end_date": source_case["rows"][-1][0],
            "timezone": "America/New_York",
            "available_at": "after-close",
            "interval_role": "warmup-development",
        })
    inputs = load_canonical(research / "development-trial-inputs.yml")
    if eligible:
        inputs["preregistration_digest"] = canonical_digest(prereg)
    inputs["data_bindings"] = {"assets": assets}
    write(research / "development-trial-inputs.yml", inputs)
    report = passed_report(repository, package, study_id, authority)
    service = make_service(package, authority, repository, study_id)
    create(service, plan_for(study_id, research), report)
    return service, study_id, inputs, assets, report


@pytest.mark.parametrize("count", [1, 2, 3])
def test_preflight_and_development_accept_variable_asset_count(tmp_path, count):
    service, study_id, inputs, assets, report = setup_assets(tmp_path, count)
    assert len(report["cases"][0]["data_assets"]) == count
    result = development(service, study_id, {"actor": "fixture-owner", "trial_inputs": inputs, "data_assets": assets})
    operation = service.study_root(study_id) / "operations" / result["operation_id"]
    request = load_canonical(operation / "runtime/request.yml")
    manifest = load_canonical(operation / "runtime/runtime-manifest.yml")
    assert len(request["data_assets"]) == len(manifest["data_assets"]) == count
    assert request["availability_policy"] == "after-close-next-session"
    assert not (operation / "runtime/assets").exists()


@pytest.mark.parametrize("fault", ["duplicate", "missing", "drift", "dates", "gap", "quarantine", "restricted", "limit", "bytes"])
def test_multi_asset_rejects_bad_inputs(tmp_path, monkeypatch, fault):
    service, study_id, inputs, assets, _ = setup_assets(tmp_path, 2)
    bad = deepcopy(assets)
    if fault == "duplicate":
        bad[1]["asset_id"] = bad[0]["asset_id"]
    elif fault == "missing":
        bad[1]["data_path"] = "research/missing.csv"
    elif fault == "drift":
        bad[1]["data_digest"] = "0" * 64
    elif fault == "dates":
        bad[1]["end_date"] = "2014-01-17"
    elif fault == "gap":
        path = service.repository_root / bad[1]["data_path"]
        path.write_bytes(path.read_bytes().replace(b"2014-01-10,", b"2014-01-09,"))
        bad[1]["data_digest"] = canonical_digest(path.read_bytes())
    elif fault == "quarantine":
        path = service.repository_root / bad[1]["data_path"]
        path.write_bytes(path.read_bytes() + b"2019-01-02,100,101,99,100,1000\n")
        bad[1]["data_digest"] = canonical_digest(path.read_bytes())
        bad[1]["end_date"] = "2019-01-02"
    elif fault == "restricted":
        bad[1]["data_path"] = "historical-evaluation-artifacts/forbidden.csv"
    elif fault == "limit":
        bad = [dict(bad[0], asset_id=f"A{n:02d}", use="trade" if n == 0 else "reference") for n in range(MAX_ASSETS + 1)]
    else:
        monkeypatch.setattr("operations.multi_asset.MAX_FILE_BYTES", 1)
    with pytest.raises((ValidationError, IntegrityError, FileNotFoundError)):
        validate_assets(service.repository_root, bad, service.rules.workflow["data_intervals"]["intervals"])


def test_development_requires_exact_frozen_asset_list(tmp_path):
    service, study_id, inputs, assets, _ = setup_assets(tmp_path, 2)
    altered = deepcopy(assets)
    altered[1]["symbol"] = "different"
    with pytest.raises(IntegrityError, match="frozen"):
        development(service, study_id, {"actor": "fixture-owner", "trial_inputs": inputs, "data_assets": altered})


def test_multi_asset_runner_contract_must_cover_same_roster(tmp_path):
    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    inputs = load_canonical(research / "development-trial-inputs.yml")
    inputs["data_bindings"] = {"assets": [{"asset_id": "TSM", "use": "trade"}]}
    write(research / "development-trial-inputs.yml", inputs)
    with pytest.raises(ValidationError, match="preflight"):
        runner_preflight(repository, study_id, authority, package)


def test_snapshot_and_evaluation_plan_bind_each_asset(tmp_path):
    repository, package, study_id, authority, _ = fixture_repository(tmp_path)
    service = make_service(package, authority, repository, study_id)
    snapshot_set = freeze_plan(service)["snapshot_set"]
    for snapshot in snapshot_set["snapshots"]:
        start, end = snapshot["sessions"][0], snapshot["sessions"][-1]
        snapshot["symbols"] = ["TSM", "SOXX"]
        snapshot["assets"] = [
            {"asset_id": asset_id, "use": use, "provider": "yahoo", "symbol": symbol,
             "data_digest": digest, "start_date": start, "end_date": end,
             "timezone": "America/New_York", "available_at": "after-close"}
            for asset_id, use, symbol, digest in (
                ("A00", "trade", "TSM", "a" * 64),
                ("A01", "reference", "SOXX", "b" * 64),
            )
        ]
        snapshot["data_digest"] = canonical_digest(snapshot["assets"])
    result = validate_snapshot_set(snapshot_set, service.rules.workflow, service.rules.schema_store)
    frozen = result["historical-evaluation"]
    assets = [dict(asset, data_path=f"research/{study_id}/{asset['asset_id']}.csv", interval_role="historical-evaluation") for asset in frozen["assets"]]
    evaluation_plan = {"actor": "fixture-evaluator", "data_digest": frozen["data_digest"], "data_assets": assets}
    service.rules.schema_store.validate("evaluation-plan.schema.yml", evaluation_plan)
    assert canonical_digest([snapshot_identity(asset) for asset in assets]) == frozen["data_digest"]


@pytest.mark.parametrize("count", [2, 3])
def test_multi_asset_synthetic_evaluation_reaches_terminal(tmp_path, count):
    import exchange_calendars as xcals
    from operations.evaluation import historical_evaluation
    from operations.lifecycle import freeze

    service, study_id, inputs, assets, _ = setup_assets(tmp_path, count, eligible=True)
    development(service, study_id, {"actor": "fixture-owner", "trial_inputs": inputs, "data_assets": assets})
    calendar = xcals.get_calendar("XNYS")
    dates = [day.strftime("%Y-%m-%d") for day in calendar.sessions_in_range("2020-01-01", "2024-12-31")]
    rows = [[day, 100, 101, 99, 100, 1000] for day in dates]
    data = synthetic_csv({"rows": rows})
    research = service.repository_root / "research" / study_id
    evaluation_assets = []
    for asset in assets:
        path = research / f"{asset['asset_id']}-evaluation.csv"
        path.write_bytes(data)
        evaluation_assets.append(dict(asset, data_path=path.relative_to(service.repository_root).as_posix(),
                                      data_digest=canonical_digest(data), start_date=dates[0],
                                      end_date=dates[-1], interval_role="historical-evaluation"))
    plan = freeze_plan(service)
    for snapshot in plan["snapshot_set"]["snapshots"]:
        start, end = snapshot["sessions"][0], snapshot["sessions"][-1]
        snapshot["symbols"] = sorted(asset["symbol"] for asset in assets)
        snapshot["assets"] = [
            dict(snapshot_identity(asset), start_date=start, end_date=end,
                 data_digest=canonical_digest(data) if snapshot["role"] == "historical-evaluation" else "d" * 64)
            for asset in assets
        ]
        snapshot["data_digest"] = canonical_digest(snapshot["assets"])
    freeze(service, study_id, plan)
    evaluator = make_service(service.workflow_root, service.authority.root,
                             service.repository_root, study_id, evaluation=True)
    result = historical_evaluation(evaluator, study_id, {
        "actor": "fixture-evaluator",
        "data_digest": canonical_digest([snapshot_identity(asset) for asset in evaluation_assets]),
        "data_assets": evaluation_assets,
    })
    assert result["status"] == "completed"
    assert result["outcome"] in {"pass", "fail", "indeterminate"}
