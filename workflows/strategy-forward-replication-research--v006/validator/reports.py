"""歷史 prepare 報告驗證，不依賴目前環境。"""

from .canonical_yaml import canonical_digest
from .errors import IntegrityError, ValidationError


def historical_report(report, event, rules):
    rules.schema_store.validate("runner-report.schema.yml", report)
    bound = report["binding"]
    if (
        report.get("prepare_checks") != "passed"
        or bound["study_id"] != event["study_id"]
        or bound["workflow_digest"] != event["bindings"]["workflow_digest"]
        or bound["workflow_reference_digest"]
        != event["bindings"]["workflow_reference_digest"]
        or canonical_digest(bound["source_bundle"]) != event["bindings"]["source_bundle_digest"]
    ):
        raise IntegrityError("prepare 報告與建立事件綁定不一致")
    for stage in ("development", "historical-evaluation"):
        if not {"trades", "no-trades"}.issubset(
            {c["expect"] for c in report["cases"] if c["stage"] == stage}
        ):
            raise ValidationError("prepare 報告缺少必要案例")
