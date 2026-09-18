"""核准範圍必須綁定具體研究，歷史驗證不依賴現行環境。"""

from pathlib import Path

from .canonical_yaml import canonical_digest
from .errors import IntegrityError, ValidationError
from .schema_validation import SchemaStore


def approval(value, actor, kind, *, study_id=None, source_digest=None, prereg_digest=None):
    try:
        SchemaStore(Path(__file__).resolve().parents[1] / "schemas").validate(
            "approval.schema.yml", value
        )
    except ValidationError as exc:
        raise ValidationError(f"{kind} 核准格式不合法：{exc}") from exc
    if (
        value.get("decision") != "approved"
        or value.get("actor_id") != actor
        or value.get("scope") != kind
        or not value.get("basis")
        or not value.get("approved_at")
        or value.get("role") not in {"trusted-approver", "超級管理者"}
    ):
        raise ValidationError(f"{kind} 缺少有效且明確的核准依據")
    if study_id is not None:
        expected = {
            "study_id": study_id,
            "workflow_version": "v002",
            "source_bundle_digest": source_digest,
            "preregistration_digest": prereg_digest,
        }
        if value.get("bindings") != expected:
            raise IntegrityError("核准依據未綁定同一 Study、source、preregistration", expected=expected, actual=value.get("bindings"))


def historical_report(report, event, rules):
    rules.schema_store.validate("runner-report.schema.yml", report)
    bound = report["binding"]
    if (
        report.get("prepare_checks") != "passed"
        or bound["study_id"] != event["study_id"]
        or bound["workflow_digest"] != event["bindings"]["workflow_digest"]
        or canonical_digest(bound["source_bundle"]) != event["bindings"]["source_bundle_digest"]
    ):
        raise IntegrityError("prepare 報告與建立事件綁定不一致")
    for stage in ("development", "historical-evaluation"):
        if not {"trades", "no-trades"}.issubset(
            {c["expect"] for c in report["cases"] if c["stage"] == stage}
        ):
            raise ValidationError("prepare 報告缺少必要案例")
