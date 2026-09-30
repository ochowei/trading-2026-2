"""來源、契約與報告不可互換；全部使用隔離人造設定。"""

from __future__ import annotations

import os
import subprocess
import sys
from copy import deepcopy
from types import SimpleNamespace

import pytest
from operations import legacy_checks as native
from synthetic_helpers import PACKAGE, make_context, refresh_bundle, write
from validator.canonical_yaml import canonical_digest, load_canonical
from validator.errors import IntegrityError, ValidationError
from validator.schema_validation import SchemaStore
from validator.synthetic_report import (
    build_synthetic_report,
    native_report_from_precreate,
    validate_synthetic_report,
)


def test_native_synthetic_report_is_schema_and_digest_bound(tmp_path):
    context = make_context(tmp_path)
    check = native.run_synthetic(context)
    assert check.status == "passed", check.errors
    report = build_synthetic_report(check.as_dict(context), check.details["binding"], PACKAGE)
    validate_synthetic_report(report, check.details["binding"], PACKAGE)
    assert report["synthetic_only"] is True
    assert report["binding"]["implementation_contract_digest"] == canonical_digest(
        load_canonical(context.research_root / "implementation-contract.yml")
    )
    assert report["binding"]["source_bundle_digest"] == canonical_digest(
        load_canonical(context.research_root / "source-bundle.yml")
    )
    assert check.warnings == []


def test_prepare_cannot_use_candidate_success_or_short_warmup_report(tmp_path):
    context = make_context(tmp_path / "good")
    precreate = native.run_precreate(context).as_dict(context)
    report = native_report_from_precreate(precreate, PACKAGE)
    assert report["check"]["name"] == "synthetic"
    with pytest.raises(ValidationError):
        native_report_from_precreate(
            {"status": "passed", "errors": [], "details": {"subchecks": []}}, PACKAGE
        )
    short = make_context(tmp_path / "short", ready=False)
    with pytest.raises(ValidationError, match="precreate 未通過"):
        native_report_from_precreate(native.run_precreate(short).as_dict(short), PACKAGE)


def test_prepare_schema_requires_native_report_even_when_flag_says_passed(tmp_path):
    context = make_context(tmp_path)
    native_report = native_report_from_precreate(
        native.run_precreate(context).as_dict(context), PACKAGE
    )
    runner_report = {
        "schema_version": 1,
        "status": "passed",
        "prepare_checks": "passed",
        "binding": {
            "study_id": context.study_id,
            "repository": str(tmp_path),
            "authority_root": "synthetic-only",
            "settings": {},
            "source_bundle": {},
            "environment": {},
            "workflow_digest": "0" * 64,
            "workflow_reference": {},
            "workflow_reference_digest": "0" * 64,
        },
        "cases": [
            {
                "case": i,
                "stage": "development",
                "expect": "trades",
                "data_digest": "0" * 64,
                "request_digest": "0" * 64,
                "evidence_digest": "0" * 64,
                "validation": {},
            }
            for i in range(4)
        ],
    }
    # 只驗證報告格式；以上佔位證據不會交給 writer 或執行程序。
    with pytest.raises(ValidationError, match="native_synthetic"):
        SchemaStore(PACKAGE / "schemas").validate("runner-report.schema.yml", runner_report)
    runner_report["native_synthetic"] = native_report
    SchemaStore(PACKAGE / "schemas").validate("runner-report.schema.yml", runner_report)


@pytest.mark.parametrize(
    "name",
    [
        "source_bundle_digest",
        "implementation_contract_digest",
        "engine_digest",
        "contract_source_digest",
        "workflow_digest",
        "spec_constant",
    ],
)
def test_report_cannot_replace_binding(tmp_path, name):
    context = make_context(tmp_path)
    check = native.run_synthetic(context)
    report = build_synthetic_report(check.as_dict(context), check.details["binding"], PACKAGE)
    changed = deepcopy(check.details["binding"])
    changed[name] = "another-spec" if name == "spec_constant" else "0" * 64
    with pytest.raises(IntegrityError):
        validate_synthetic_report(report, changed, PACKAGE)


def test_modified_or_incomplete_report_is_rejected(tmp_path):
    context = make_context(tmp_path)
    check = native.run_synthetic(context)
    report = build_synthetic_report(check.as_dict(context), check.details["binding"], PACKAGE)
    modified = deepcopy(report)
    modified["check"]["details"]["holding_sessions"] = 11
    with pytest.raises(IntegrityError):
        validate_synthetic_report(modified, check.details["binding"], PACKAGE)
    modified = deepcopy(report)
    del modified["binding"]["implementation_contract_digest"]
    with pytest.raises(ValidationError):
        SchemaStore(PACKAGE / "schemas").validate("synthetic-report.schema.yml", modified)
    modified = deepcopy(report)
    modified["binding"]["engine_digest"] = "not-sha256"
    with pytest.raises(ValidationError):
        validate_synthetic_report(modified, check.details["binding"], PACKAGE)


def test_source_drift_stops_before_engine_import(tmp_path):
    context = make_context(tmp_path)
    with (context.repository_root / "src/ready_engine.py").open("a") as file:
        file.write('\nraise AssertionError("漂移來源不應執行")\n')
    check = native.run_synthetic(context)
    assert check.status == "failed"
    assert {error["code"] for error in check.errors} == {"synthetic-binding-invalid"}
    assert "drift" in check.errors[0]["message"]


def test_contract_must_be_in_source_bundle(tmp_path):
    context = make_context(tmp_path)
    bundle = load_canonical(context.research_root / "source-bundle.yml")
    bundle["files"] = [
        item for item in bundle["files"] if not item["path"].endswith("implementation-contract.yml")
    ]
    write(context.research_root, "source-bundle.yml", bundle)
    check = native.run_synthetic(context)
    assert check.status == "failed"
    assert "契約與引擎必須納入" in check.errors[0]["message"]


def test_missing_regime_is_native_contract_unsupported(tmp_path):
    context = make_context(tmp_path)
    contract = load_canonical(context.research_root / "implementation-contract.yml")
    contract["indicator_contract"].pop("regime")
    write(context.research_root, "implementation-contract.yml", contract)
    refresh_bundle(context.repository_root, context.research_root)
    check = native.run_synthetic(context)
    assert check.status == "failed"
    assert {error["code"] for error in check.errors} == {"synthetic-contract-unsupported"}


def test_unsupported_regime_is_native_contract_unsupported(tmp_path):
    context = make_context(tmp_path)
    contract = load_canonical(context.research_root / "implementation-contract.yml")
    contract["indicator_contract"]["regime"]["operator"] = "<="
    write(context.research_root, "implementation-contract.yml", contract)
    refresh_bundle(context.repository_root, context.research_root)
    check = native.run_synthetic(context)
    assert check.status == "failed"
    assert {error["code"] for error in check.errors} == {"synthetic-contract-unsupported"}


def test_wrong_regime_lookback_is_native_implementation_invalid(tmp_path):
    context = make_context(tmp_path)
    contract = load_canonical(context.research_root / "implementation-contract.yml")
    contract["indicator_contract"]["regime"]["slow"].update(lookback=60, min_periods=60)
    contract["indicator_contract"]["required_history_sessions"] = 59
    write(context.research_root, "implementation-contract.yml", contract)
    refresh_bundle(context.repository_root, context.research_root)
    check = native.run_synthetic(context)
    assert check.status == "failed"
    assert any(error["code"] == "synthetic-implementation-invalid" for error in check.errors)


def test_actual_diagnostics_cli_writes_only_external_report(tmp_path):
    context = make_context(tmp_path / "repository")
    report_path = tmp_path / "diagnostic.yml"
    env = {**os.environ, "PYTHONPATH": str(PACKAGE), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "operations.synthetic_diagnostics",
            "--repository-root",
            str(context.repository_root),
            "--study-id",
            context.study_id,
            "--report",
            str(report_path),
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    report = load_canonical(report_path)
    assert report["check"]["status"] == "passed"
    assert not context.study_root.exists()
    assert not (context.repository_root / ".authority").exists()


@pytest.mark.parametrize(
    ("document", "form"),
    [
        ("candidate-definition.yml", "implementation_contract"),
        ("preregistration.yml", "implementation_contract"),
        ("candidate-definition.yml", "indicator_contract"),
        ("preregistration.yml", "indicator_contract"),
        ("candidate-definition.yml", "eligibility_rules"),
        ("preregistration.yml", "eligibility_rules"),
    ],
)
def test_embedded_contract_uses_returned_source_label(tmp_path, document, form):
    context = make_context(tmp_path)
    external = context.research_root / "implementation-contract.yml"
    contract = load_canonical(external)
    value = load_canonical(context.research_root / document)
    if form == "implementation_contract":
        value[form] = contract
    elif form == "indicator_contract":
        value[form] = contract["indicator_contract"]
    else:
        value.setdefault(form, {})["indicator_contract"] = contract["indicator_contract"]
    write(context.research_root, document, value)
    external.unlink()  # 只刪除此測試建立、可修改的人造設定。
    bundle = load_canonical(context.research_root / "source-bundle.yml")
    bundle["files"] = [
        item for item in bundle["files"] if not item["path"].endswith("implementation-contract.yml")
    ]
    if form != "implementation_contract":
        # 沒有 engine 宣告時，舊契約仍依唯一的 Source Bundle 策略來源解析。
        bundle["files"] = [
            item
            for item in bundle["files"]
            if item["path"] not in {"src/ready_engine.py", "src/control_engine.py"}
        ]
    for item in bundle["files"]:
        item["digest"] = canonical_digest((context.repository_root / item["path"]).read_bytes())
    write(context.research_root, "source-bundle.yml", bundle)
    result = native.run_synthetic(context)
    assert result.status == "passed", result.errors
    assert (
        result.details["binding"]["contract_source_path"]
        == f"research/{context.study_id}/{document}"
    )


def test_identical_manifest_copy_binds_original_research_source(tmp_path):
    context = make_context(tmp_path)
    # 純人造副本目錄；不建 Study、不產生 event、不呼叫任何 Lifecycle。
    copies = tmp_path / "human-copies" / "manifests"
    copies.mkdir(parents=True)
    original = context.research_root / "implementation-contract.yml"
    (copies / original.name).write_bytes(original.read_bytes())
    view = SimpleNamespace(
        repository_root=context.repository_root,
        workflow_root=PACKAGE,
        research_root=context.research_root,
        study_id=context.study_id,
        study_root=copies.parent,
        display_path=context.display_path,
    )
    result = native.run_synthetic(view)
    assert result.status == "passed", result.errors
    assert (
        result.details["binding"]["contract_source_path"]
        == f"research/{context.study_id}/implementation-contract.yml"
    )
    assert result.details["binding"]["contract_source_digest"] == canonical_digest(
        original.read_bytes()
    )


def test_drifting_manifest_copy_is_rejected(tmp_path):
    context = make_context(tmp_path)
    copies = tmp_path / "human-copies" / "manifests"
    copies.mkdir(parents=True)
    value = load_canonical(context.research_root / "implementation-contract.yml")
    value["indicator_contract"]["regime"]["slow"].update(lookback=60, min_periods=60)
    write(copies, "implementation-contract.yml", value)
    view = SimpleNamespace(
        repository_root=context.repository_root,
        workflow_root=PACKAGE,
        research_root=context.research_root,
        study_id=context.study_id,
        study_root=copies.parent,
        display_path=context.display_path,
    )
    result = native.run_synthetic(view)
    assert result.status == "failed"
    assert any(error["code"] == "copy-forward-artifact-drift" for error in result.errors)
    assert any("副本與 Source Bundle" in error["message"] for error in result.errors)


@pytest.mark.parametrize("original_warmup", [False, True])
def test_demo_cli_and_native_precreate_reproduce_draft_boundaries(tmp_path, original_warmup):
    directory = tmp_path / "demo"
    args = [
        sys.executable,
        str(PACKAGE / "tools/build_synthetic_demo.py"),
        "--directory",
        str(directory),
    ]
    if original_warmup:
        args.append("--original-warmup")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    built = subprocess.run(args, env=env, capture_output=True, text=True, timeout=30)
    assert built.returncode == 0, built.stdout + built.stderr
    assert built.stderr == ""
    package_copy = directory / "workflows" / PACKAGE.name
    env["PYTHONPATH"] = str(package_copy)
    checked = subprocess.run(
        [
            sys.executable,
            "-m",
            "operations.legacy_checks",
            "--repository-root",
            str(directory),
            "precreate",
            "synthetic-regime",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert checked.returncode == (1 if original_warmup else 0), checked.stdout + checked.stderr
    assert checked.stderr == ""
    if original_warmup:
        assert "fold-warmup-too-short" in checked.stdout
    for name in (
        "release.yml",
        "release-manifest.yml",
        "release-test-report.yml",
        "studies",
        "runtime",
        "authority",
    ):
        assert not (package_copy / name).exists()
