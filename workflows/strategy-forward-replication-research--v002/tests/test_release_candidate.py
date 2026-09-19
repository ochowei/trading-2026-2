from __future__ import annotations

from validator.canonical_yaml import canonical_digest, load_canonical
from validator.release import validate_release_manifest, validate_release_record
from validator.schema_validation import SchemaStore


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


def test_release_package_is_reproducible_and_approved(workflow_root) -> None:
    report = load_canonical(workflow_root / "release-test-report.yml")
    SchemaStore(workflow_root / "schemas").validate(
        "release-test-report.schema.yml", report
    )
    manifest = validate_release_manifest(workflow_root)
    assert all(not item["path"].startswith("studies/") for item in manifest["files"])
    release = validate_release_record(workflow_root)
    assert release["workflow_digest"] == manifest["workflow_digest"]
