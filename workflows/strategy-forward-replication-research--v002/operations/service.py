"""prepare、freeze-readiness 與三事件建立；授權由既有核准文件提供。"""
from __future__ import annotations

from pathlib import Path

from validator.canonical_yaml import (
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.errors import IntegrityError, ValidationError
from validator.study import apply_event, validate_study
from writer.lock import StudyLock
from writer.service import StudyService

from operations.legacy_checks import StudyContext, run_precreate
from operations.preflight import PACKAGE, binding, runner_preflight, save_report, verify_report


def prepare(repository: Path, study_id: str, authority: Path, report_path: Path,
            package: Path = PACKAGE) -> dict:
    if authority.resolve() == repository.resolve() or repository.resolve() in authority.resolve().parents and "studies" in authority.parts:
        raise ValidationError("authority root 必須獨立於 Study")
    checkpoint_root = authority / study_id
    if checkpoint_root.exists() and any(checkpoint_root.iterdir()):
        raise ValidationError("新 Study ID 已有 authority checkpoint")
    binding(repository, study_id, authority, package)
    check = run_precreate(StudyContext(repository, package, study_id))
    if check.status != "passed":
        raise ValidationError(f"prepare 規格／策略檢查失敗：{check.errors}")
    contract = load_canonical(repository / "research" / study_id / "runner-contract.yml")
    if contract["runners"]["development"] != check.details["development_trial_bindings"]["procedure_path"]:
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


def approval(value: dict, actor: str, kind: str) -> None:
    if (value.get("decision") != "approved" or value.get("actor_id") != actor
            or value.get("scope") != kind or not value.get("basis")
            or not value.get("approved_at")
            or value.get("role") not in {"trusted-approver", "超級管理者"}):
        raise ValidationError(f"{kind} 缺少有效且明確的核准依據")


def create_authorize(service: StudyService, plan: dict, report: dict) -> dict:
    study_id = plan["study_id"]
    verify_report(report, service.repository_root, study_id, service.authority.root,
                  service.workflow_root)
    prereg = plan["preregistration"]
    authorization = plan["development_authorization"]
    approval(plan["preregistration_approval"], plan["preregistration_actor"], "preregistration")
    approval(authorization, plan["development_actor"], "development-only")
    if canonical_digest(prereg) != report["binding"]["settings"]["preregistration.yml"]:
        raise IntegrityError("批次建立的 preregistration 與 prepare 不一致")
    root = service.study_root(study_id)
    # 此鎖只序列化批次重試；每一 Event 仍由既有 writer lock/journal 發布。
    root.mkdir(parents=True, exist_ok=True)
    with StudyLock(root / ".batch.lock"):
        atomic_create(root / "manifests/create-plan.yml", canonical_bytes(plan))
        service.recover(study_id)
        source = report["binding"]["source_bundle"]
        prereg_path, prereg_digest = service.publish_artifact(study_id, "manifests/preregistration.yml", prereg)
        approval_path, approval_digest = service.publish_artifact(study_id, "evidence/preregistration-approval.yml", plan["preregistration_approval"])
        auth_path, auth_digest = service.publish_artifact(study_id, "evidence/development-authorization.yml", authorization)
        stages = [
            ("study-created", plan["creator"], None),
            ("preregistration-approved", plan["preregistration_actor"], {
                "preregistration_path": prereg_path, "preregistration_digest": prereg_digest,
                "approval_path": approval_path, "approval_digest": approval_digest}),
            ("development-authorized", plan["development_actor"], {
                "evidence_path": auth_path, "evidence_digest": auth_digest}),
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
                    raise IntegrityError("不得以不同核准依據接續批次")
            elif kind == "study-created":
                service.create_study(study_id, actor, source_bundle=source,
                    prepare_report=report, **plan["identity"])
            else:
                service.append_event(study_id, kind, actor, payload)
            completed.append(kind)
        return {"study_id": study_id, "completed": completed, "cross_event_atomic": False}


def freeze_readiness(service: StudyService, study_id: str, payload: dict, actor: str) -> dict:
    """模擬真正 candidate-frozen Event，讓全部 freeze 規則共同驗證。"""
    projection = validate_study(service.study_root(study_id), service.rules)
    service.authority.verify(study_id, projection.events)
    event = {"schema_version": 1, "study_id": study_id,
             "sequence": len(projection.events) + 1,
             "previous_event_digest": projection.head_digest,
             "event_type": "candidate-frozen", "occurred_at": "2000-01-01T00:00:00.000000Z",
             "actor_id": actor, "bindings": dict(projection.bindings), "payload": payload}
    service.rules.schema_store.validate("event.schema.yml", event)
    apply_event(projection, event, service.rules, service.study_root(study_id))
    return {"status": "passed", "study_id": study_id, "candidate_freeze_written": False}
