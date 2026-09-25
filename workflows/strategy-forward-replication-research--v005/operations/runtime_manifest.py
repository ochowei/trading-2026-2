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
    data_assets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    manifest = {
        "schema_version": 1,
        "workflow_version": "v005",
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
        "evidence": {"path": evidence_path},
    }
    if data_assets is None:
        manifest["data"] = {"path": data_path, "digest": data_digest}
    else:
        manifest["data_assets"] = [
            {
                "asset_id": asset["asset_id"],
                "path": asset["data_path"],
                "digest": asset["data_digest"],
                "use": asset["use"],
                "provider": asset["provider"],
                "symbol": asset["symbol"],
                "start_date": asset["start_date"],
                "end_date": asset["end_date"],
                "timezone": asset["timezone"],
                "available_at": asset["available_at"],
            }
            for asset in data_assets
        ]
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
    request = load_canonical(path.parent / "request.yml")
    service.rules.schema_store.validate("runner-request.schema.yml", request)
    if value["request"]["digest"] != canonical_digest(request):
        raise IntegrityError("runtime manifest 的 request digest 不一致")
    if "data_assets" in value:
        plan = load_canonical(path.parent.parent / "plan.yml")["plan"]
        bound = plan.get("data_assets")
        if bound is None or len(bound) != len(value["data_assets"]):
            raise IntegrityError("runtime manifest 的資產清單與 operation plan 不一致")
        if value["stage"] == "development" and request["trial_inputs"].get("data_bindings", {}).get("assets") != bound:
            raise IntegrityError("runtime manifest 的資產清單與 frozen inputs 不一致")
        for stored, source, staged in zip(value["data_assets"], bound, request["data_assets"], strict=True):
            if any(stored[key] != source["data_digest" if key == "digest" else "data_path" if key == "path" else key]
                   for key in stored):
                raise IntegrityError("runtime manifest 的資產來源綁定不一致")
            if any(staged[key] != source[key] for key in source if key != "data_path"):
                raise IntegrityError("runtime request 的資產綁定不一致")
    return value
