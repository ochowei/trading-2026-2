"""固定整體計畫的連續入口；各事件依自己的 journal 提交。"""

from validator.assignments import reject_legacy
from validator.canonical_yaml import (
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.errors import IntegrityError
from writer.lock import StudyLock

from operations import lifecycle
from operations.service import create, prepare


def develop_to_freeze(service, study_id, plan):
    service.require_context(study_id)
    reject_legacy(plan)
    service.rules.schema_store.validate("continuous-plan.schema.yml", plan)
    if plan["create"]["study_id"] != study_id:
        raise IntegrityError("連續計畫必須指定同一 Study")
    root = service.study_root(study_id)
    with StudyLock(root / ".writer.lock"):
        record = {
            "plan": plan,
            "assignment_digest": canonical_digest(service.assignment),
            "authority_root": str(service.authority.root),
            "workflow_digest": service.workflow_digest,
        }
        atomic_create(root / "manifests/continuous-plan.yml", canonical_bytes(record))
        report_path = root / "manifests/continuous-prepare.yml"
        if not report_path.exists():
            prepare(
                service.repository_root,
                study_id,
                service.authority.root,
                report_path,
                service.workflow_root,
            )
        create(service, plan["create"], load_canonical(report_path))
        for trial in plan["development"]:
            lifecycle.development(service, study_id, trial)
        result = lifecycle.freeze(service, study_id, plan["freeze"])
        return {
            **result,
            "scope_boundary": "development-to-freeze",
            "continuous_operation_id": canonical_digest(record),
        }
