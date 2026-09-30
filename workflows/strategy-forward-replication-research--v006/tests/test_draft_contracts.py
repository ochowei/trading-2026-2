"""Draft 與既有資料／Policy 契約的靜態及人造檔案檢查。"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from operations.multi_asset import validate_assets
from operations.preflight import synthetic_csv
from synthetic_helpers import PACKAGE
from validator.canonical_yaml import canonical_digest, load_canonical
from validator.errors import ValidationError
from validator.release import policy_set_digest, validate_release_record

V005 = PACKAGE.with_name("strategy-forward-replication-research--v005")


def test_v005_published_definitions_and_release_are_unchanged():
    manifest = load_canonical(V005 / "release-manifest.yml")
    assert (
        manifest["workflow_digest"]
        == "2441c16d2c477afef9d4d9ca159e3a8bff150080b8552991d5da5fbcc9daf2c2"
    )
    assert len(manifest["files"]) == 102
    for item in manifest["files"]:
        assert not {"studies", "runtime", "evidence", "authority"}.intersection(
            Path(item["path"]).parts
        )
        assert canonical_digest((V005 / item["path"]).read_bytes()) == item["digest"]
    assert (
        canonical_digest((V005 / "release.yml").read_bytes())
        == "92c2c35d15e371378c189f60de69093220ab1ee74c256208c36be31534f9aeb8"
    )


def test_policy_and_immutable_policy_releases_are_preserved():
    workflow = load_canonical(PACKAGE / "workflow.yml")
    for binding in workflow["bindings"]["policy_releases"]:
        relative = Path(binding["path"])
        for path in (relative, relative.with_name("policy.yml")):
            assert (PACKAGE / path).read_bytes() == (V005 / path).read_bytes()
    assert policy_set_digest(PACKAGE) == policy_set_digest(V005)


def test_fixed_rules_and_intervals_preserve_v005_semantics():
    previous = load_canonical(V005 / "workflow.yml")
    current = load_canonical(PACKAGE / "workflow.yml")
    previous["workflow_version"] = "v006"
    assert previous == current
    for name in (
        "state-machine.yml",
        "evidence-requirements.yml",
        "failure-and-recovery.yml",
        "workflow-floors.yml",
    ):
        assert (V005 / "rules" / name).read_bytes() == (PACKAGE / "rules" / name).read_bytes()
    for name in (
        "data-snapshot.schema.yml",
        "data-snapshot-set.schema.yml",
        "runner-contract.schema.yml",
        "runner-request.schema.yml",
        "preregistration.schema.yml",
        "historical-evaluation.schema.yml",
    ):
        assert (V005 / "schemas" / name).read_bytes() == (PACKAGE / "schemas" / name).read_bytes()


def test_draft_contains_no_workflow_release_or_lifecycle_state(tmp_path):
    # 只複製公開定義，測 Draft 副本；不假設來源 Package 永遠未發布。
    draft = tmp_path / "isolated-draft"
    draft.mkdir()
    for name in (
        "rules",
        "schemas",
        "validator",
        "writer",
        "operations",
        "tests",
        "examples",
        "reference",
        "policies",
        "tools",
    ):
        shutil.copytree(
            PACKAGE / name, draft / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
    for name in ("README.md", "workflow.yml"):
        shutil.copyfile(PACKAGE / name, draft / name)
    for name in (
        "release-manifest.yml",
        "release-test-report.yml",
        "release.yml",
        "studies",
        "runtime",
        "evidence",
        "authority",
    ):
        assert not (draft / name).exists()
    with pytest.raises(ValidationError, match="尚未"):
        validate_release_record(draft)


def test_all_draft_yaml_is_canonical_and_schema_definitions_are_valid():
    paths = [PACKAGE / "workflow.yml"]
    for name in ("rules", "schemas", "tests/fixtures", "examples", "policies"):
        paths.extend((PACKAGE / name).rglob("*.yml"))
    for path in paths:
        value = load_canonical(path)
        if path.parent.name == "schemas":
            Draft202012Validator.check_schema(value)


def test_legacy_single_csv_protocol_still_generates_synthetic_bytes():
    rows = [["2014-01-02", "100", "101", "99", "100", "1000000"]]
    assert (
        synthetic_csv({"rows": rows})
        == b"Date,Open,High,Low,Close,Volume\n2014-01-02,100,101,99,100,1000000\n"
    )


@pytest.mark.parametrize("count", [1, 2, 16])
def test_one_to_sixteen_assets_accept_only_aligned_synthetic_files(tmp_path, count):
    data = b"Date,Open,High,Low,Close,Volume\n2014-01-02,100,101,99,100,1000000\n2014-01-03,100,101,99,100,1000000\n"
    assets = []
    for index in range(count):
        name = f"SYN{index:02d}"
        (tmp_path / f"{name}.csv").write_bytes(data)
        assets.append(
            {
                "asset_id": name,
                "use": "trade" if index == 0 else "reference",
                "interval_role": "warmup-development",
                "data_path": f"{name}.csv",
                "data_digest": canonical_digest(data),
                "start_date": "2014-01-02",
                "end_date": "2014-01-03",
            }
        )
    intervals = [{"role": "development", "start_date": "2014-01-01", "end_date": "2018-12-31"}]
    assert len(validate_assets(tmp_path, assets, intervals)) == count


@pytest.mark.parametrize("count", [0, 17])
def test_unsupported_asset_counts_still_rejected(tmp_path, count):
    with pytest.raises(ValidationError, match="1 至 16"):
        validate_assets(tmp_path, [{}] * count, [])
