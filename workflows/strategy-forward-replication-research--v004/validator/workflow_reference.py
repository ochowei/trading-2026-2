"""v004 Workflow reference 的建立、解析與完整性驗證。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical_yaml import canonical_digest, load_canonical
from .errors import IntegrityError, ValidationError
from .paths import resolve_inside, validate_repository_relative_path
from .release import (
    build_release_manifest,
    policy_set_digest,
    validate_release_manifest,
    validate_release_record,
    workflow_digest,
)
from .schema_validation import SchemaStore

REFERENCE_SCHEMA = "workflow-reference.schema.yml"
REFERENCE_MODE = "repository-workflow-package"
RESOLVER_VERSION = 1


def repository_root_for(workflow_root: Path | str, repository_root: Path | str | None = None) -> Path:
    root = Path(workflow_root).resolve()
    if repository_root is not None:
        return Path(repository_root).resolve()
    return root.parent.parent if root.parent.name == "workflows" else root.parent


def _relative_package_path(workflow_root: Path, repository_root: Path) -> str:
    try:
        relative = workflow_root.relative_to(repository_root)
    except ValueError as exc:
        raise ValidationError("Workflow Package 必須位於 repository 內") from exc
    value = validate_repository_relative_path(relative.as_posix()).as_posix()
    if not value.startswith("workflows/"):
        raise ValidationError("Workflow Package 必須位於 workflows/ 下")
    return value


def _assert_no_symlink_escape(workflow_root: Path, repository_root: Path) -> None:
    current = repository_root
    for part in workflow_root.relative_to(repository_root).parts:
        current = current / part
        if current.is_symlink():
            raise ValidationError("Workflow reference 不接受 symlink Package")


def _manifest_digest(root: Path, *, allow_draft: bool) -> str:
    path = root / "release-manifest.yml"
    if path.exists():
        validate_release_manifest(root)
        return canonical_digest(path.read_bytes())
    if not allow_draft:
        raise ValidationError("Workflow 尚無 release manifest；正式 reference 被拒絕")
    # Draft 的暫存 workspace 可能只攜帶 Workflow 內容；正式 Study 仍必須有實體
    # release-manifest.yml。固定時間只用於讓 draft resolver 可重現，不得當成 release。
    manifest = build_release_manifest(root, generated_at="2000-01-01T00:00:00.000000Z")
    return canonical_digest(manifest)


def build_workflow_reference(
    workflow_root: Path | str,
    repository_root: Path | str | None = None,
    *,
    allow_draft: bool = False,
) -> dict[str, Any]:
    root = Path(workflow_root).resolve()
    repository = repository_root_for(root, repository_root)
    if not root.is_dir():
        raise ValidationError("找不到 Workflow Package")
    _assert_no_symlink_escape(root, repository)
    workflow = load_canonical(root / "workflow.yml")
    package_path = _relative_package_path(root, repository)
    manifest_path = f"{package_path}/release-manifest.yml"
    result = {
        "schema_version": 1,
        "reference_mode": REFERENCE_MODE,
        "workflow_id": workflow["workflow"],
        "workflow_version": workflow["workflow_version"],
        "workflow_package_path": package_path,
        "workflow_digest": workflow_digest(root, allow_draft=allow_draft),
        "release_manifest_path": manifest_path,
        "release_manifest_digest": _manifest_digest(root, allow_draft=allow_draft),
        "policy_set_digest": policy_set_digest(root),
        "resolver_version": RESOLVER_VERSION,
    }
    SchemaStore(root / "schemas").validate(REFERENCE_SCHEMA, result)
    return result


def validate_workflow_reference(
    reference: dict[str, Any],
    repository_root: Path | str,
    *,
    expected_workflow_root: Path | str | None = None,
    allow_draft: bool = False,
) -> dict[str, Any]:
    """先驗證 reference，再驗證它指向的 Package、release 與 policy digest。"""

    repository = Path(repository_root).resolve()
    package_value = reference.get("workflow_package_path")
    manifest_value = reference.get("release_manifest_path")
    if not isinstance(package_value, str) or not isinstance(manifest_value, str):
        raise ValidationError("Workflow reference 缺少 Package 或 manifest path")
    package_relative = validate_repository_relative_path(package_value).as_posix()
    manifest_relative = validate_repository_relative_path(manifest_value).as_posix()
    if manifest_relative != f"{package_relative}/release-manifest.yml":
        raise IntegrityError("Workflow reference 的 release manifest path 不一致")
    if any(
        part in {"studies", "historical-evaluation-artifacts", ".super-admin", ".project-manager"}
        for part in Path(package_relative).parts
    ):
        raise ValidationError("Workflow reference 指向受限目錄")
    package = resolve_inside(repository, package_relative)
    _assert_no_symlink_escape(package, repository)
    if expected_workflow_root is not None and package != Path(expected_workflow_root).resolve():
        raise IntegrityError("Workflow reference 未指向目前固定的 Workflow Package")
    SchemaStore(package / "schemas").validate(REFERENCE_SCHEMA, reference)
    workflow = load_canonical(package / "workflow.yml")
    if reference["workflow_id"] != workflow["workflow"]:
        raise IntegrityError("Workflow reference workflow_id 不一致")
    if reference["workflow_version"] != workflow["workflow_version"]:
        raise IntegrityError("Workflow reference workflow_version 不一致")
    if reference["workflow_version"] != "v004":
        raise ValidationError("v004 reference 不接受其他 Workflow version")
    actual_workflow_digest = workflow_digest(package, allow_draft=allow_draft)
    if reference["workflow_digest"] != actual_workflow_digest:
        raise IntegrityError("Workflow reference workflow digest mismatch")
    manifest_path = package / "release-manifest.yml"
    if manifest_path.exists():
        actual_manifest = validate_release_manifest(package)
        if reference["release_manifest_digest"] != canonical_digest(manifest_path.read_bytes()):
            raise IntegrityError("Workflow reference release manifest digest mismatch")
        if actual_manifest["workflow_digest"] != reference["workflow_digest"]:
            raise IntegrityError("release manifest 與 Workflow reference digest 不一致")
    elif allow_draft:
        if reference["release_manifest_digest"] != _manifest_digest(package, allow_draft=True):
            raise IntegrityError("Draft Workflow reference release manifest digest mismatch")
    else:
        raise ValidationError("正式 Workflow reference 必須有 release manifest")
    if not allow_draft:
        release = validate_release_record(package)
        if release["workflow_digest"] != reference["workflow_digest"]:
            raise IntegrityError("Workflow release record 與 reference digest 不一致")
    actual_policy_digest = policy_set_digest(package)
    if reference["policy_set_digest"] != actual_policy_digest:
        raise IntegrityError("Workflow reference policy set digest mismatch")
    return reference


def reference_digest(reference: dict[str, Any]) -> str:
    return canonical_digest(reference)


def load_and_validate_study_reference(
    study_root: Path,
    repository_root: Path | str,
    relative_path: str,
    expected_digest: str,
    *,
    expected_workflow_root: Path | str,
    allow_draft: bool = False,
) -> tuple[Path, dict[str, Any]]:
    path = resolve_inside(study_root, relative_path)
    data = load_canonical(path)
    if canonical_digest(path.read_bytes()) != expected_digest:
        raise IntegrityError("Study Workflow reference digest mismatch")
    validate_workflow_reference(
        data,
        repository_root,
        expected_workflow_root=expected_workflow_root,
        allow_draft=allow_draft,
    )
    return path, data
