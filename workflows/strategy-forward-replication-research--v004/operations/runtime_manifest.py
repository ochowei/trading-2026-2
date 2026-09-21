"""Operation runtime manifest；只保存 digest 與暫存執行的查找資訊。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from validator.canonical_yaml import (
    atomic_create,
    atomic_replace,
    canonical_bytes,
    canonical_digest,
)
from validator.errors import IntegrityError, ValidationError


def runner_digest(source_bundle: dict[str, Any], runner: str) -> str:
    for item in source_bundle["files"]:
        if item["path"] == runner:
            return item["digest"]
    raise ValidationError("runner 必須被 Source Bundle 綁定")


def make_runtime_manifest(
    service,
    study_id: str,
    operation_id: str,
    stage: str,
    source_bundle: dict[str, Any],
    runner: str,
    request: dict[str, Any],
    data_path: str,
    data_digest: str,
    evidence_path: str,
    evidence_digest: str | None = None,
) -> dict[str, Any]:
    manifest = {
        "schema_version": 1,
        "workflow_version": "v004",
        "study_id": study_id,
        "operation_id": operation_id,
        "stage": stage,
        "resolver_version": service.workflow_reference.get("resolver_version", 1),
        "execution_contract": "request-output-v1",
        "execution_workspace": "temporary",
        "workflow_reference": {
            "path": "manifests/workflow-reference.yml",
            "digest": service.workflow_reference_digest,
        },
        "source_bundle": {
            "path": "manifests/source-bundle.yml",
            "digest": canonical_digest(source_bundle),
        },
        "runner": {"path": runner, "digest": runner_digest(source_bundle, runner)},
        "request": {
            "path": "runtime/request.yml",
            "digest": canonical_digest(request),
        },
        "data": {"path": data_path, "digest": data_digest},
        "evidence": {"path": evidence_path},
    }
    if evidence_digest is not None:
        manifest["evidence"]["digest"] = evidence_digest
    service.rules.schema_store.validate("runtime-manifest.schema.yml", manifest)
    return manifest


def publish_runtime_manifest(path: Path, value: dict[str, Any], *, replace: bool = False) -> None:
    data = canonical_bytes(value)
    if replace:
        atomic_replace(path, data)
    elif path.exists():
        if path.read_bytes() != data:
            raise IntegrityError("runtime-manifest.yml 已存在但內容不一致")
    else:
        atomic_create(path, data)


def create_if_same(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() != data:
            raise IntegrityError(f"固定輸出已存在但內容不一致：{path.name}")
        return
    atomic_create(path, data)


def load_runtime_manifest(path: Path, service) -> dict[str, Any]:
    from validator.canonical_yaml import load_canonical

    if not path.is_file():
        raise ValidationError("缺少 runtime-manifest.yml")
    value = load_canonical(path)
    service.rules.schema_store.validate("runtime-manifest.schema.yml", value)
    if value["workflow_reference"]["digest"] != service.workflow_reference_digest:
        raise IntegrityError("runtime manifest 的 Workflow reference digest 不一致")
    return value
