from __future__ import annotations

import pytest
from conftest import WORKFLOW_ROOT
from operations.release_candidate import verify
from validator.canonical_yaml import canonical_bytes, canonical_digest, load_canonical
from validator.errors import IntegrityError, ValidationError
from validator.release import (
    build_release_manifest,
    validate_release_manifest,
    validate_release_record,
    workflow_digest,
)
from validator.schema_validation import SchemaStore


def release_state(package):
    """依實際檔案判定 Draft／RC／Active，拒絕只有一半的發行證據。"""
    manifest_path = package / "release-manifest.yml"
    report_path = package / "release-test-report.yml"
    release_path = package / "release.yml"
    if manifest_path.exists() != report_path.exists():
        raise AssertionError("release manifest 與 test report 必須同時存在")
    if not manifest_path.exists():
        if release_path.exists():
            raise AssertionError("沒有候選版證據不能有 release record")
        expected = build_release_manifest(
            package, generated_at="2000-01-01T00:00:00.000000Z"
        )
        assert workflow_digest(package, allow_draft=True) == expected["workflow_digest"]
        return "draft"
    manifest = validate_release_manifest(package)
    report = load_canonical(report_path)
    SchemaStore(package / "schemas").validate("release-test-report.schema.yml", report)
    assert manifest["workflow_digest"] == workflow_digest(package)
    assert canonical_digest(manifest_path.read_bytes()) == canonical_digest(manifest)
    assert canonical_digest(report_path.read_bytes()) == canonical_digest(report)
    if release_path.exists():
        validate_release_record(package)
        return "active"
    return "release-candidate"


def test_vendored_policy_releases_are_self_contained(workflow_root) -> None:
    workflow = load_canonical(workflow_root / "workflow.yml")
    schemas = SchemaStore(workflow_root / "schemas")
    for binding in workflow["bindings"]["policy_releases"]:
        release_path = workflow_root / binding["path"]
        release = load_canonical(release_path)
        schemas.validate("policy-release.schema.yml", release)
        assert release["policy"] == binding["policy"]
        assert release["version"] == binding["version"]
        assert release["policy_digest"] == canonical_digest(
            (release_path.parent / "policy.yml").read_bytes()
        )
        for conformance in release["conformance"]:
            assert conformance["digest"] == canonical_digest(
                (workflow_root / conformance["path"]).read_bytes()
            )


def test_real_package_is_in_a_complete_release_state() -> None:
    assert release_state(WORKFLOW_ROOT) in {"draft", "release-candidate", "active"}


def test_readme_describes_release_states_without_hardcoding_current_artifacts() -> None:
    readme = (WORKFLOW_ROOT / "README.md").read_text(encoding="utf-8")
    introduction = readme.split("\n\n", maxsplit=2)[1]

    assert "目前是 Draft" not in introduction
    assert "沒有 `release-manifest.yml`" not in introduction
    assert "只有 Active 可用來建立正式 Study" in introduction
    assert "Draft 與 Release Candidate 都不得供正式 Study 使用" in introduction


def test_draft_has_reproducible_digest_and_no_release_artifacts(draft_workflow_root) -> None:
    assert release_state(draft_workflow_root) == "draft"
    assert verify(draft_workflow_root)["status"] == "definitions-passed"
    assert not any(
        (draft_workflow_root / name).exists()
        for name in ("release-manifest.yml", "release-test-report.yml", "release.yml")
    )


def test_release_candidate_requires_reproducible_manifest_and_valid_report(workflow_root) -> None:
    assert release_state(workflow_root) == "release-candidate"
    manifest = validate_release_manifest(workflow_root)
    assert verify(workflow_root, candidate=True)["workflow_digest"] == manifest["workflow_digest"]
    assert all(not item["path"].startswith("studies/") for item in manifest["files"])
    assert not (workflow_root / "release.yml").exists()


@pytest.mark.parametrize("missing", ["release-manifest.yml", "release-test-report.yml"])
def test_partial_release_candidate_is_rejected(workflow_root, missing) -> None:
    (workflow_root / missing).unlink()
    with pytest.raises(AssertionError, match="同時存在"):
        release_state(workflow_root)


def test_release_candidate_rejects_definition_drift(workflow_root) -> None:
    workflow_path = workflow_root / "workflow.yml"
    workflow = load_canonical(workflow_path)
    workflow["title"] = "遭到修改的合成測試版本"
    workflow_path.write_bytes(canonical_bytes(workflow))
    with pytest.raises(IntegrityError):
        release_state(workflow_root)


def test_release_candidate_rejects_invalid_report(workflow_root) -> None:
    report_path = workflow_root / "release-test-report.yml"
    report = load_canonical(report_path)
    report["status"] = "draft"
    report_path.write_bytes(canonical_bytes(report))
    with pytest.raises(ValidationError):
        release_state(workflow_root)
