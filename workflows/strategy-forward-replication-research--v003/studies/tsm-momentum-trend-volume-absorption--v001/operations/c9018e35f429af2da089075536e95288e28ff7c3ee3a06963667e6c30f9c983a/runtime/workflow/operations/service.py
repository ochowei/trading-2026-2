"""prepare、freeze-readiness 與明確派工三事件建立。"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from validator.assignments import reject_legacy
from validator.canonical_yaml import (
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.errors import IntegrityError, ValidationError
from validator.qualification import validate_supported
from validator.study import apply_event, validate_study
from writer.lock import StudyLock
from writer.service import StudyService

from operations.legacy_checks import StudyContext, run_precreate
from operations.preflight import PACKAGE, binding, runner_preflight, save_report, verify_report


def prepare(
    repository: Path, study_id: str, authority: Path, report_path: Path, package: Path = PACKAGE
) -> dict:
    if (
        authority.resolve() == repository.resolve()
        or repository.resolve() in authority.resolve().parents
        and "studies" in authority.parts
    ):
        raise ValidationError("authority root 必須獨立於 Study")
    checkpoint_root = authority / study_id
    if checkpoint_root.exists() and any(checkpoint_root.iterdir()):
        raise ValidationError("新 Study ID 已有 authority checkpoint")
    from validator.assignments import DEVELOPER, safe_path

    safe_path(repository / "research" / study_id / "preregistration.yml", repository, DEVELOPER)
    validate_supported(load_canonical(repository / "research" / study_id / "preregistration.yml"))
    binding(repository, study_id, authority, package)
    check = run_precreate(StudyContext(repository, package, study_id))
    if check.status != "passed":
        raise ValidationError(f"prepare 規格／策略檢查失敗：{check.errors}")
    contract = load_canonical(repository / "research" / study_id / "runner-contract.yml")
    if (
        contract["runners"]["development"]
        != check.details["development_trial_bindings"]["procedure_path"]
    ):
        raise ValidationError("runner contract 與正式 Development procedure 不一致")
    report = runner_preflight(repository, study_id, authority, package)
    report["prepare_checks"] = "passed"

    def canonical_details(value):
        if isinstance(value, float):
            return str(value)
        if isinstance(value, dict):
            return {key: canonical_details(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [canonical_details(item) for item in value]
        return value

    report["checks"] = canonical_details(check.details)
    save_report(report_path, report)
    return report


def create(service: StudyService, plan: dict, report: dict) -> dict:
    study_id = plan["study_id"]
    service.require_context(study_id, plan["creator"])
    reject_legacy(plan)
    if not (service.study_root(study_id) / "events").exists():
        verify_report(
            report, service.repository_root, study_id, service.authority.root, service.workflow_root
        )
    if report["binding"]["authority_root"] != str(service.authority.root):
        raise IntegrityError("不得更換建立報告綁定的 authority root")
    prereg = plan["preregistration"]
    service.require_context(study_id, plan["creator"])
    service.require_context(study_id, plan["development_actor"])
    reject_legacy(plan)
    service.rules.schema_store.validate("create-plan.schema.yml", plan)
    if canonical_digest(prereg) != report["binding"]["settings"]["preregistration.yml"]:
        raise IntegrityError("建立預先登記與 prepare 不一致")
    root = service.study_root(study_id)
    # 此鎖只序列化批次重試；每一 Event 仍由既有 writer lock/journal 發布。
    root.mkdir(parents=True, exist_ok=True)
    with StudyLock(root / ".writer.lock"):
        atomic_create(root / "manifests/create-plan.yml", canonical_bytes(plan))
        atomic_create(root / "manifests/prepare-report.yml", canonical_bytes(report))
        timefile = root / "manifests/create-timestamp.yml"
        if not timefile.exists():
            atomic_create(
                timefile,
                canonical_bytes({"value": datetime.now(UTC).isoformat().replace("+00:00", "Z")}),
            )
        service.recover(study_id)
        source = report["binding"]["source_bundle"]
        prereg_path, prereg_digest = service.publish_artifact(
            study_id, "manifests/preregistration.yml", prereg
        )
        operation = {
            "plan_digest": canonical_digest(plan),
            "report_digest": canonical_digest(report),
            "assignment_digest": canonical_digest(service.assignment),
            "authority_root": str(service.authority.root),
            "workflow_digest": service.workflow_digest,
            "study_id": study_id,
            "source_bundle_digest": canonical_digest(source),
            "preregistration_digest": prereg_digest,
        }
        atomic_create(root / "manifests/create-operation.yml", canonical_bytes(operation))
        stages = [
            ("study-created", plan["creator"], None),
            (
                "preregistration-recorded",
                plan["development_actor"],
                {"preregistration_path": prereg_path, "preregistration_digest": prereg_digest},
            ),
            (
                "development-started",
                plan["development_actor"],
                {"operation_id": canonical_digest(operation)},
            ),
        ]
        completed = []
        for index, (kind, actor, payload) in enumerate(stages):
            projection = validate_study(root, service.rules)
            if len(projection.events) > index:
                event = projection.events[index].value
                if event["event_type"] != kind or event["actor_id"] != actor:
                    raise IntegrityError("既有 Event 與原批次計畫不一致")
                if index == 0:
                    if event["bindings"]["source_bundle_digest"] != canonical_digest(source):
                        raise IntegrityError("不得更換既有 Source Bundle")
                    for key, value in plan["identity"].items():
                        if event["payload"].get(key) != value:
                            raise IntegrityError("不得更換既有 Study identity")
                if payload is not None and event["payload"] != payload:
                    raise IntegrityError("不得以不同派工或輸入接續批次")
            elif kind == "study-created":
                service.create_study(
                    study_id,
                    actor,
                    source_bundle=source,
                    prepare_report=report,
                    create_plan=plan,
                    occurred_at=load_canonical(timefile)["value"],
                    **plan["identity"],
                )
            else:
                service.append_event(
                    study_id, kind, actor, payload, occurred_at=load_canonical(timefile)["value"]
                )
            completed.append(kind)
        return {
            "study_id": study_id,
            "operation_id": canonical_digest(operation),
            "completed": completed,
            "cross_event_atomic": False,
        }


def freeze_readiness(service: StudyService, study_id: str, payload: dict, actor: str) -> dict:
    """模擬真正 candidate-frozen Event，讓全部 freeze 規則共同驗證。"""
    projection = validate_study(service.study_root(study_id), service.rules)
    service.authority.verify(study_id, projection.events)
    event = {
        "schema_version": 1,
        "execution": service.execution(study_id),
        "study_id": study_id,
        "sequence": len(projection.events) + 1,
        "previous_event_digest": projection.head_digest,
        "event_type": "candidate-frozen",
        "occurred_at": "2000-01-01T00:00:00.000000Z",
        "actor_id": actor,
        "bindings": dict(projection.bindings),
        "payload": payload,
    }
    service.rules.schema_store.validate("event.schema.yml", event)
    apply_event(projection, event, service.rules, service.study_root(study_id))
    return {"status": "passed", "study_id": study_id, "candidate_freeze_written": False}
