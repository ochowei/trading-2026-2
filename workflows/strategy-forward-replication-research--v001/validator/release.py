"""Workflow release candidate 與 content-based identity。"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .canonical_yaml import canonical_digest, load_canonical
from .errors import IntegrityError, ValidationError
from .paths import resolve_inside
from .schema_validation import SchemaStore

EXCLUDED_NAMES = {
    "IMPLEMENTATION-PLAN.md",
    "release-manifest.yml",
    "release-test-report.yml",
    "release.yml",
}
EXCLUDED_PARTS = {"__pycache__", "studies"}


def definition_files(workflow_root: Path | str) -> list[Path]:
    root = Path(workflow_root)
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.name in EXCLUDED_NAMES:
            continue
        relative = path.relative_to(root)
        if EXCLUDED_PARTS.intersection(relative.parts) or path.suffix == ".pyc":
            continue
        if path.suffix not in {".yml", ".py", ".md"}:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def build_release_manifest(
    workflow_root: Path | str,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(workflow_root)
    workflow = load_canonical(root / "workflow.yml")
    entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "digest": canonical_digest(path.read_bytes()),
        }
        for path in definition_files(root)
    ]
    identity = {
        "files": entries,
        "workflow": workflow["workflow"],
        "workflow_version": workflow["workflow_version"],
    }
    return {
        "schema_version": 1,
        "workflow": workflow["workflow"],
        "workflow_version": workflow["workflow_version"],
        "generated_at": generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "files": entries,
        "workflow_digest": canonical_digest(identity),
    }


def validate_release_manifest(workflow_root: Path | str) -> dict[str, Any]:
    root = Path(workflow_root)
    stored = load_canonical(root / "release-manifest.yml")
    SchemaStore(root / "schemas").validate("release-manifest.schema.yml", stored)
    rebuilt = build_release_manifest(root, generated_at=stored["generated_at"])
    if stored != rebuilt:
        raise IntegrityError("release-manifest.yml 與目前 Workflow Package 不一致")
    return stored


def workflow_digest(workflow_root: Path | str, *, allow_draft: bool = False) -> str:
    root = Path(workflow_root)
    manifest_path = root / "release-manifest.yml"
    if manifest_path.exists():
        return validate_release_manifest(root)["workflow_digest"]
    if not allow_draft:
        raise ValidationError("Workflow 尚無 release manifest；正式寫入被拒絕")
    workflow = load_canonical(root / "workflow.yml")
    identity = {
        "files": [
            {
                "path": path.relative_to(root).as_posix(),
                "digest": canonical_digest(path.read_bytes()),
            }
            for path in definition_files(root)
        ],
        "workflow": workflow["workflow"],
        "workflow_version": workflow["workflow_version"],
    }
    return canonical_digest(identity)


def policy_set_digest(workflow_root: Path | str) -> str:
    root = Path(workflow_root)
    workflow = load_canonical(root / "workflow.yml")
    schemas = SchemaStore(root / "schemas")
    policies = []
    for binding in workflow["bindings"]["policy_releases"]:
        release_path = root / binding["path"]
        policy_path = release_path.parent / "policy.yml"
        if release_path.exists():
            release = load_canonical(release_path)
            schemas.validate("policy-release.schema.yml", release)
            if (
                release["policy"] != binding["policy"]
                or release["version"] != binding["version"]
            ):
                raise IntegrityError(f"Policy release identity drift: {binding['policy']}")
            digest = release["policy_digest"]
            if digest != canonical_digest(policy_path.read_bytes()):
                raise IntegrityError(f"Policy release digest drift: {binding['policy']}")
            for conformance in release["conformance"]:
                conformance_path = resolve_inside(root, conformance["path"])
                if conformance["digest"] != canonical_digest(conformance_path.read_bytes()):
                    raise IntegrityError(
                        f"Policy conformance digest drift: {binding['policy']}"
                    )
        else:
            digest = canonical_digest(policy_path.read_bytes())
        policies.append(
            {
                "digest": digest,
                "policy": binding["policy"],
                "version": binding["version"],
            }
        )
    return canonical_digest({"policies": policies})


def validate_release_record(workflow_root: Path | str) -> dict[str, Any]:
    root = Path(workflow_root)
    release_path = root / "release.yml"
    if not release_path.exists():
        raise ValidationError("Workflow 尚未由 trusted approver 建立 release.yml")
    release = load_canonical(release_path)
    SchemaStore(root / "schemas").validate("release.schema.yml", release)
    manifest = validate_release_manifest(root)
    if release["workflow_digest"] != manifest["workflow_digest"]:
        raise IntegrityError("Release record 與 release manifest workflow digest 不一致")
    if release["release_manifest_digest"] != canonical_digest(
        (root / "release-manifest.yml").read_bytes()
    ):
        raise IntegrityError("Release record 沒有綁定 exact release manifest")
    report_path = root / release["test_report_path"]
    if not report_path.exists():
        raise IntegrityError("Release record 指向不存在的 test report")
    report = load_canonical(report_path)
    SchemaStore(root / "schemas").validate("release-test-report.schema.yml", report)
    if release["test_report_digest"] != canonical_digest(report_path.read_bytes()):
        raise IntegrityError("Release record 沒有綁定 exact test report")
    return release
