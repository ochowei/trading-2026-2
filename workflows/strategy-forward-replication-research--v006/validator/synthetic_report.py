"""人造案例報告綁定同一份來源與契約，不能當成 Study 資格證據。"""

from __future__ import annotations

from pathlib import Path

from .canonical_yaml import canonical_digest
from .errors import IntegrityError, ValidationError
from .paths import resolve_inside
from .release import workflow_digest
from .schema_validation import SchemaStore

FORBIDDEN = {
    ".super-admin",
    ".project-manager",
    ".study-developer",
    "historical-evaluation-artifacts",
    "studies",
    "runtime",
    "authority",
    ".authority",
}


def synthetic_binding(
    repository: Path,
    package: Path,
    bundle: dict,
    contract: dict,
    contract_source: Path,
    engine: Path,
    *,
    original_source: Path | None = None,
) -> dict:
    schemas = SchemaStore(package / "schemas")
    schemas.validate("source-bundle.schema.yml", bundle)
    schemas.validate("implementation-contract.schema.yml", contract)
    entries = {}
    for item in bundle["files"]:
        relative = item["path"]
        if FORBIDDEN.intersection(Path(relative).parts):
            raise ValidationError("合成檢查不接受受限來源路徑")
        path = resolve_inside(repository, relative)
        if FORBIDDEN.intersection(path.relative_to(repository.resolve()).parts):
            raise ValidationError("合成來源解析至受限路徑")
        if relative in entries:
            raise ValidationError("Source Bundle 路徑重複")
        if path.suffix not in {".py", ".yml", ".yaml", ".toml", ".txt", ".lock"}:
            raise ValidationError("合成檢查只接受程式與設定來源")
        if canonical_digest(path.read_bytes()) != item["digest"]:
            raise IntegrityError(f"合成 Source Bundle drift：{relative}")
        entries[relative] = item["digest"]
    original_source = original_source or contract_source
    for path in (original_source, engine):
        relative = path.resolve().relative_to(repository.resolve()).as_posix()
        if relative not in entries:
            raise IntegrityError(f"合成契約與引擎必須納入 Source Bundle：{relative}")
    # 已凍結 manifest 可是同一研究來源的 byte-identical 副本，不能要求副本
    # 的 studies 路徑出現在 Source Bundle。原來源仍受上述路徑及 digest 檢查。
    source_relative = contract_source.resolve().relative_to(repository.resolve())
    if (FORBIDDEN - {"studies"}).intersection(source_relative.parts):
        raise ValidationError("合成契約副本解析至受限路徑")
    if contract_source.read_bytes() != original_source.read_bytes():
        raise IntegrityError("合成契約副本與 Source Bundle 原來源不一致")
    return {
        "source_bundle_digest": canonical_digest(bundle),
        "implementation_contract_digest": canonical_digest(contract),
        "contract_source_digest": canonical_digest(original_source.read_bytes()),
        "contract_source_path": original_source.relative_to(repository).as_posix(),
        "engine_path": engine.relative_to(repository).as_posix(),
        "engine_digest": canonical_digest(engine.read_bytes()),
        "spec_constant": contract.get("engine", {}).get("spec_constant", "DEFAULT_SPEC"),
        "cost_constant": contract.get("engine", {}).get("cost_constant", "BASE_COST"),
        "workflow_digest": workflow_digest(package, allow_draft=True),
    }


def build_synthetic_report(check: dict, binding: dict, package: Path) -> dict:
    def decimals(value):
        if isinstance(value, float):
            return str(value)
        if isinstance(value, dict):
            return {key: decimals(item) for key, item in value.items()}
        if isinstance(value, list):
            return [decimals(item) for item in value]
        return value

    value = {
        "schema_version": 1,
        "workflow_version": "v006",
        "synthetic_only": True,
        "generator": "deterministic-contract-bars-v2",
        "binding": binding,
        "check": decimals(check),
    }
    value["report_digest"] = canonical_digest(value)
    validate_synthetic_report(value, binding, package)
    return value


def native_report_from_precreate(precreate: dict, package: Path) -> dict:
    """正式 prepare 及隔離 consumer 都須附原生 guard 的完整結果。"""
    if precreate.get("status") != "passed" or precreate.get("errors"):
        raise ValidationError("完整原生 precreate 未通過，不能建立 prepare 原生報告")
    checks = [
        check
        for check in precreate.get("details", {}).get("subchecks", [])
        if check.get("name") == "synthetic"
    ]
    if len(checks) != 1 or checks[0].get("status") != "passed":
        raise ValidationError("prepare 缺少通過的原生 synthetic guard")
    check = checks[0]
    if "binding" not in check.get("details", {}):
        raise ValidationError("原生 synthetic 結果未綁定來源與契約")
    return build_synthetic_report(check, check["details"]["binding"], package)


def validate_synthetic_report(value: dict, expected_binding: dict, package: Path) -> None:
    SchemaStore(package / "schemas").validate("synthetic-report.schema.yml", value)
    if value["binding"] != expected_binding:
        raise IntegrityError("合成報告不屬於目前的來源、契約或 Workflow")
    payload = {key: item for key, item in value.items() if key != "report_digest"}
    if canonical_digest(payload) != value["report_digest"]:
        raise IntegrityError("合成報告內容指紋不一致")
    if (value["check"]["status"] == "passed") != (not value["check"]["errors"]):
        raise IntegrityError("合成報告結果與錯誤清單不一致")
