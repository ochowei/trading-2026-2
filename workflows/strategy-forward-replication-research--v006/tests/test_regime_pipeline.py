"""交由 workflow 執行者執行：真正 prepare／consumer／create／Trial 的隔離整合。"""

from __future__ import annotations

from copy import deepcopy

import pytest
from operations import legacy_checks as native
from operations import preflight
from operations.service import create, prepare
from regime_pipeline_helpers import context, regime_repository
from repair_helpers import publish_trial
from test_operations import make_service, plan_for, refresh_bundle, write
from validator.canonical_yaml import canonical_digest, load_canonical
from validator.errors import IntegrityError, ValidationError
from validator.synthetic_report import native_report_from_precreate


def test_regime_prepare_consumer_create_trial_and_frozen_source_copy(tmp_path, monkeypatch):
    import pandas as pd

    repo, package, study_id, authority, research = regime_repository(tmp_path)
    candidate = native._load_engine(repo / "src/ready_engine.py", native.CheckResult("candidate"))
    control = native._load_engine(repo / "src/control_engine.py", native.CheckResult("control"))
    # Pipeline 的 baseline 保留 regime、少兩個訊號條件；不是公開 v009 Control。
    assert candidate.BASELINE_SPEC == candidate.DEFAULT_SPEC.with_changes(
        volume_lead_enabled=False, require_close_above_prior_close=False)
    cases = load_canonical(research / "runner-contract.yml")["cases"]
    for case in cases[:2]:
        bars = pd.DataFrame(case["rows"], columns=["Date", "Open", "High", "Low", "Close", "Volume"])
        bars.index = pd.to_datetime(bars.pop("Date"))
        actual = candidate.backtest(bars.astype(float), spec=candidate.DEFAULT_SPEC, cost=candidate.BASE_COST)
        same_prices = control.backtest(bars.astype(float), spec=control.DEFAULT_SPEC, cost=control.BASE_COST)
        assert len(same_prices.trades) == 2
        assert len(actual.trades) == (2 if case["expect"] == "trades" else 0)
    consumer_reports = []
    reports_by_package = {}
    original_report = preflight.native_report_from_precreate

    def observe(precreate, consumer_package):
        # 只觀察真實回傳值，不替換 guard 或接受結果。
        events = consumer_package / "studies" / precreate["study_id"] / "events"
        assert not list(events.glob("*.yml")), "完整重算必須先於第一份事件檔發布"
        report = original_report(precreate, consumer_package)
        consumer_reports.append(report)
        reports_by_package.setdefault(consumer_package.resolve(), []).append(report)
        return report

    monkeypatch.setattr(preflight, "native_report_from_precreate", observe)
    report = prepare(repo, study_id, authority, tmp_path / "prepare.yml", package)
    assert report["prepare_checks"] == "passed"
    assert report["native_synthetic"]["check"]["status"] == "passed"
    consumer_count = sum(case["stage"] == "development" for case in cases)
    # 每個 consumer：建報告一次，再由 operations.create、writer.create_study、
    # writer.append_event(study-created) 三個入口各重驗一次，不減少任何 guard。
    assert len(consumer_reports) == consumer_count * 4
    assert len(reports_by_package) == consumer_count
    assert all(len(values) == 4 for values in reports_by_package.values())
    assert all(value == report["native_synthetic"] for value in consumer_reports)
    assert not (package / "studies").exists()
    assert not authority.exists()

    checks_before_create = []
    original_check = native.run_precreate

    def observe_create(current):
        # writer 可先建立空 events 目錄；真正發布以事件檔存在為準。
        assert not list((current.study_root / "events").glob("*.yml"))
        checks_before_create.append(current.repository_root)
        return original_check(current)

    monkeypatch.setattr(native, "run_precreate", observe_create)
    service = make_service(package, authority, repo, study_id)
    result = create(service, plan_for(study_id, research), report)
    assert result["completed"] == ["study-created", "preregistration-recorded", "development-started"]
    # 外層 create 同樣走上述三個既有驗報入口，全部在第一事件檔之前。
    assert checks_before_create == [repo.resolve()] * 3
    # 既有 frozen document 優先讀取規則：同 bytes 契約副本仍綁研究原來源。
    original_source = research / "implementation-contract.yml"
    frozen = service.study_root(study_id) / "manifests/implementation-contract.yml"
    frozen.write_bytes(original_source.read_bytes())
    synthetic = native.run_synthetic(context(repo, package, study_id))
    assert synthetic.status == "passed", synthetic.errors
    assert synthetic.details["binding"] == report["native_synthetic"]["binding"]
    assert synthetic.details["binding"]["contract_source_digest"] == canonical_digest(frozen.read_bytes())
    payload = publish_trial(service, study_id, research)
    assert payload["trial_id"] == load_canonical(research / "development-trial-inputs.yml")["candidate_id"]
    assert service.validate(study_id)["lifecycle"]["current_event"] == "trial-recorded"
    frozen.write_text(frozen.read_text() + "\n")
    assert native.run_synthetic(context(repo, package, study_id)).status == "failed"


@pytest.mark.parametrize("fault", ["missing", "replacement", "content"])
def test_regime_create_rejects_missing_replaced_or_forged_native_report(tmp_path, fault):
    repo, package, study_id, authority, research = regime_repository(tmp_path / "current")
    report = prepare(repo, study_id, authority, tmp_path / "prepare.yml", package)
    bad = deepcopy(report)
    if fault == "missing":
        bad.pop("native_synthetic")
    elif fault == "replacement":
        other, other_package, other_id, _, other_research = regime_repository(tmp_path / "other")
        prereg = load_canonical(other_research / "preregistration.yml")
        prereg["hypothesis"] += "另一份人造來源，不能代替目前來源。"
        write(other_research / "preregistration.yml", prereg)
        refresh_bundle(other, other_research)
        bad["native_synthetic"] = native_report_from_precreate(
            native.run_precreate(context(other, other_package, other_id)).as_dict(context(other, other_package, other_id)),
            other_package)
    else:
        bad["native_synthetic"]["check"]["details"]["forged_success"] = True
        value = bad["native_synthetic"]
        value["report_digest"] = canonical_digest({k: v for k, v in value.items() if k != "report_digest"})
    with pytest.raises((IntegrityError, ValidationError)):
        create(make_service(package, authority, repo, study_id), plan_for(study_id, research), bad)
    assert not (package / "studies").exists()
    assert not authority.exists()


def test_regime_short_warmup_rejected_before_runner_or_publication(tmp_path, monkeypatch):
    repo, package, study_id, authority, research = regime_repository(tmp_path, ready=False)

    def forbidden(*args, **kwargs):
        raise AssertionError("25 日不足須在 runner／consumer 之前拒絕")

    monkeypatch.setattr("operations.service.runner_preflight", forbidden)
    with pytest.raises(ValidationError, match="fold-warmup-too-short"):
        prepare(repo, study_id, authority, tmp_path / "prepare.yml", package)
    assert not (tmp_path / "prepare.yml").exists()
    assert not (package / "studies").exists()
    assert not authority.exists()
    assert load_canonical(research / "preregistration.yml")["fold_warmup_sessions"] == 25
