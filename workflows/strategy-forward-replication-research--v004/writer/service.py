"""唯一正式 Study 寫入服務。"""

from __future__ import annotations

import base64
import shutil
import tempfile
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from validator.assignments import (
    DEVELOPER,
    AssignmentError,
    safe_path,
    validate_assignment,
)
from validator.canonical_yaml import (
    atomic_create,
    atomic_replace,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.errors import IntegrityError, ValidationError
from validator.paths import (
    is_within_repository_path,
    resolve_historical_evaluation_artifact,
    resolve_inside,
    validate_repository_relative_path,
)
from validator.release import policy_set_digest, validate_release_record, workflow_digest
from validator.study import WorkflowRules, apply_event, validate_study

from .authority import AuthorityStore
from .journal import JournalPublisher
from .lock import StudyLock


class StudyService:
    def __init__(
        self,
        workflow_root: Path | str,
        authority_root: Path | str,
        *,
        repository_root: Path | str | None = None,
        allow_draft: bool = False,
        actor: str | None = None,
        role: str | None = None,
        assignment: dict | None = None,
    ):
        safe_path(workflow_root, repository_root, role)
        safe_path(authority_root, repository_root, role)
        if repository_root is not None:
            safe_path(repository_root, repository_root, role)
        self.workflow_root = Path(workflow_root).resolve()
        self.authority = AuthorityStore(authority_root)
        self.allow_draft = allow_draft
        self.actor, self.role, self.assignment = actor, role, assignment
        self.rules = WorkflowRules(
            self.workflow_root,
            repository_root=repository_root,
            allow_draft=allow_draft,
        )
        self.repository_root = self.rules.repository_root
        self.workflow_digest = workflow_digest(self.workflow_root, allow_draft=allow_draft)
        self.policy_set_digest = policy_set_digest(self.workflow_root)
        self.workflow_reference = self.rules.workflow_reference
        self.workflow_reference_digest = self.rules.workflow_reference_digest
        if not allow_draft:
            validate_release_record(self.workflow_root)

    def require_context(self, study_id, actor=None):
        validate_assignment(self.assignment, study_id, actor or self.actor, self.role)
        if actor is not None and actor != self.actor:
            raise AssignmentError("role-mismatch", "writer actor 與派工受派者不一致")
        record_name = (
            "create-operation.yml" if self.role == DEVELOPER else "evaluation-operation.yml"
        )
        record_path = resolve_inside(
            self.study_root(study_id), f"manifests/{record_name}", must_exist=False
        )
        safe_path(record_path, self.repository_root, self.role)
        if record_path.exists() and load_canonical(record_path)[
            "assignment_digest"
        ] != canonical_digest(self.assignment):
            raise AssignmentError("binding-mismatch", "不能更換已保存 operation 的派工")
        if self.role == DEVELOPER:
            from operations.lifecycle import assert_development_scope

            assert_development_scope(self, study_id)

    def execution(self, study_id):
        self.require_context(study_id)
        path, digest = self.publish_artifact(
            study_id,
            f"manifests/assignments/{canonical_digest(self.assignment)}.yml",
            self.assignment,
        )
        return {"role": self.role, "assignment_path": path, "assignment_digest": digest}

    def study_root(self, study_id: str) -> Path:
        if not study_id or "/" in study_id or ".." in study_id:
            raise ValidationError("不安全的 study_id")
        return safe_path(self.workflow_root / "studies" / study_id, self.repository_root, self.role)

    def _artifact_destination(self, study_id: str, relative_path: str) -> tuple[str, Path]:
        root = self.study_root(study_id)
        normalized = validate_repository_relative_path(relative_path).as_posix()
        if is_within_repository_path(normalized, self.rules.historical_evaluation_artifacts_path):
            destination = resolve_historical_evaluation_artifact(
                root,
                self.repository_root,
                self.rules.historical_evaluation_artifacts_path,
                normalized,
                must_exist=False,
            )
        else:
            destination = resolve_inside(root, normalized, must_exist=False)
        return normalized, destination

    def publish_artifact(self, study_id: str, relative_path: str, value: Any) -> tuple[str, str]:
        normalized, destination = self._artifact_destination(study_id, relative_path)
        self.require_context(study_id)
        safe_path(destination, self.repository_root, self.role)
        if is_within_repository_path(normalized, self.rules.historical_evaluation_artifacts_path):
            projection = validate_study(self.study_root(study_id), self.rules)
            self.authority.verify(study_id, projection.events)
            if self.role != "Study 歷史評估執行者" or projection.evaluation_operation is None:
                raise AssignmentError(
                    "scope-boundary", "評估結果只能在 started 與 checkpoint 完成後發布"
                )
        data = canonical_bytes(value)
        atomic_create(destination, data)
        return normalized, canonical_digest(data)

    def publish_historical_evaluation_artifact(
        self, study_id: str, relative_path: str, value: Any
    ) -> tuple[str, str]:
        """將正式 Historical Evaluation 相關 artifact 發布到 repository store。"""

        artifact_path = validate_repository_relative_path(relative_path)
        if is_within_repository_path(
            artifact_path.as_posix(), self.rules.historical_evaluation_artifacts_path
        ):
            raise ValidationError(
                "publish_historical_evaluation_artifact 只接受 store 內的檔案相對路徑"
            )
        store_path = validate_repository_relative_path(
            self.rules.historical_evaluation_artifacts_path
        )
        full_path = "/".join(
            (*store_path.parts, self.study_root(study_id).name, *artifact_path.parts)
        )
        return self.publish_artifact(study_id, full_path, value)

    def _verify_prepared(self, study_id: str, report: dict | None) -> None:
        from operations.preflight import verify_report

        if report is None:
            raise ValidationError("第一個 Event 前必須提供 prepare 報告")
        verify_report(
            report, self.repository_root, study_id, self.authority.root, self.workflow_root
        )

    def create_study(
        self,
        study_id: str,
        actor_id: str,
        *,
        research_round_id: str,
        experiment_family: str,
        research_owner: str,
        source_bundle: dict[str, Any],
        historical_evaluation_operator: str | None = None,
        replay_operator: str | None = None,
        prepare_report: dict | None = None,
        create_plan: dict | None = None,
        occurred_at: str | None = None,
    ) -> str:
        self.require_context(study_id, actor_id)
        self._verify_prepared(study_id, prepare_report)
        if create_plan is None:
            raise ValidationError("create 必須提供固定計畫")
        self.rules.schema_store.validate("create-plan.schema.yml", create_plan)
        self.rules.schema_store.validate("source-bundle.schema.yml", source_bundle)
        if (
            prepare_report is not None
            and source_bundle != prepare_report["binding"]["source_bundle"]
        ):
            raise IntegrityError("create Source Bundle 與 prepare 不一致")
        workflow_reference_path, workflow_reference_digest = self.publish_artifact(
            study_id,
            "manifests/workflow-reference.yml",
            self.workflow_reference,
        )
        if workflow_reference_digest != self.workflow_reference_digest:
            raise IntegrityError("Workflow reference digest 建立不一致")
        source_bundle_path, source_bundle_digest = self.publish_artifact(
            study_id,
            "manifests/source-bundle.yml",
            source_bundle,
        )
        operator = historical_evaluation_operator or replay_operator
        if not operator:
            raise ValidationError("Study identity 必須指定 Historical Evaluation 執行者")
        payload = {
            "research_round_id": research_round_id,
            "experiment_family": experiment_family,
            "research_owner": research_owner,
            "historical_evaluation_operator": operator,
            "source_bundle_path": source_bundle_path,
            "source_bundle_digest": source_bundle_digest,
            "workflow_reference_path": workflow_reference_path,
            "workflow_reference_digest": workflow_reference_digest,
        }
        if create_plan is not None:
            path, digest = self.publish_artifact(study_id, "manifests/create-plan.yml", create_plan)
            payload.update(create_plan_path=path, create_plan_digest=digest)
        return self.append_event(
            study_id,
            "study-created",
            actor_id,
            payload,
            source_bundle_digest=source_bundle_digest,
            prepare_report=prepare_report,
            occurred_at=occurred_at,
        )

    def append_event(
        self,
        study_id: str,
        event_type: str,
        actor_id: str,
        payload: dict[str, Any],
        *,
        source_bundle_digest: str | None = None,
        occurred_at: str | None = None,
        prepare_report: dict | None = None,
    ) -> str:
        self.require_context(study_id, actor_id)
        execution = self.execution(study_id)
        if event_type == "study-created":
            self._verify_prepared(study_id, prepare_report)
            if prepare_report is not None:
                if (
                    canonical_digest(prepare_report["binding"]["source_bundle"])
                    != source_bundle_digest
                ):
                    raise IntegrityError("prepare 與建立事件 Source Bundle 不一致")
                report_path, report_digest = self.publish_artifact(
                    study_id, "manifests/prepare-report.yml", prepare_report
                )
                payload = dict(
                    payload, prepare_report_path=report_path, prepare_report_digest=report_digest
                )
        root = self.study_root(study_id)
        root.mkdir(parents=True, exist_ok=True)
        with StudyLock(root / ".writer.lock"):
            if event_type == "study-created":
                if (root / "events").exists() and list((root / "events").glob("*.yml")):
                    raise ValidationError("Study 已存在")
                projection = validate_study(root, self.rules, check_projection=False)
                assert source_bundle_digest is not None
                bindings = {
                    "workflow_digest": self.workflow_digest,
                    "policy_set_digest": self.policy_set_digest,
                    "source_bundle_digest": source_bundle_digest,
                    "workflow_reference_path": "manifests/workflow-reference.yml",
                    "workflow_reference_digest": self.workflow_reference_digest,
                }
            else:
                projection = validate_study(root, self.rules, check_projection=False)
                if not projection.events:
                    raise ValidationError("Study 尚未建立")
                self.authority.verify(study_id, projection.events)
                bindings = dict(projection.bindings)
                if (
                    source_bundle_digest
                    and source_bundle_digest != bindings["source_bundle_digest"]
                ):
                    raise IntegrityError("不得更換 Study Source Bundle")
            sequence = len(projection.events) + 1
            timestamp = occurred_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
            event = {
                "schema_version": 1,
                "execution": execution,
                "study_id": study_id,
                "sequence": sequence,
                "previous_event_digest": projection.head_digest,
                "event_type": event_type,
                "occurred_at": timestamp,
                "actor_id": actor_id,
                "bindings": bindings,
                "payload": payload,
            }
            self.rules.schema_store.validate("event.schema.yml", event)
            simulated = deepcopy(projection)
            apply_event(simulated, event, self.rules, root)
            event_bytes = canonical_bytes(event)
            event_digest = canonical_digest(event_bytes)
            event_path = root / "events" / f"{sequence:06d}-{event_type}.yml"
            checkpoint_path, checkpoint_bytes = self.authority.prepare_checkpoint(
                study_id,
                sequence,
                event_digest,
                created_at=timestamp,
            )
            JournalPublisher(root, self.authority.root).publish(
                event_path,
                event_bytes,
                checkpoint_path,
                checkpoint_bytes,
            )
            rebuilt = validate_study(root, self.rules, check_projection=False)
            self.authority.verify(study_id, rebuilt.events)
            atomic_replace(root / "study.yml", canonical_bytes(rebuilt.to_dict()))
            return event_digest

    def recover(self, study_id: str) -> list[str]:
        self.require_context(study_id)
        root = self.study_root(study_id)
        with StudyLock(root / ".writer.lock"):

            def validate_pending(journal):
                # 先在隔離副本驗證原 bytes；任何佐證損壞都不得先補發正式 Event。
                with tempfile.TemporaryDirectory(prefix="study-recover-") as temp:
                    staged = Path(temp) / study_id
                    shutil.copytree(root, staged, symlinks=True)
                    authority = Path(temp) / "authority"
                    checkpoints = self.authority.root / study_id
                    if checkpoints.exists():
                        shutil.copytree(checkpoints, authority / study_id)
                    pending = []
                    for path in (root / "journals").glob("*.prepared.yml"):
                        if path.with_name(
                            path.name.replace(".prepared.yml", ".completed.yml")
                        ).exists():
                            continue
                        value = load_canonical(path)
                        from validator.canonical_yaml import parse_yaml

                        pending_event = parse_yaml(
                            base64.b64decode(value["event_bytes_base64"], validate=True)
                        )
                        if pending_event["execution"]["role"] != self.role or pending_event[
                            "execution"
                        ]["assignment_digest"] != canonical_digest(self.assignment):
                            raise AssignmentError("role-mismatch", "只能恢復受派角色的原 journal")
                        if canonical_digest(value) != path.name.removesuffix(".prepared.yml"):
                            raise IntegrityError("Prepared journal identity 不正確")
                        pending.append(value)
                    for value in pending:
                        if not value["event_path"].startswith("events/") or not value[
                            "checkpoint_path"
                        ].startswith(f"{study_id}/checkpoints/"):
                            raise IntegrityError("Journal 目的地不屬於原 Study")
                        event_bytes = base64.b64decode(value["event_bytes_base64"], validate=True)
                        checkpoint_bytes = base64.b64decode(
                            value["checkpoint_bytes_base64"], validate=True
                        )
                        atomic_create(
                            resolve_inside(staged, value["event_path"], must_exist=False),
                            event_bytes,
                        )
                        atomic_create(
                            resolve_inside(authority, value["checkpoint_path"], must_exist=False),
                            checkpoint_bytes,
                        )
                    projected = validate_study(staged, self.rules, check_projection=False)
                    AuthorityStore(authority).verify(study_id, projected.events)

            recovered = JournalPublisher(root, self.authority.root).recover(
                validate_pending=validate_pending
            )
            projection = validate_study(root, self.rules, check_projection=False)
            self.authority.verify(study_id, projection.events)
            atomic_replace(root / "study.yml", canonical_bytes(projection.to_dict()))
            return recovered

    def validate(self, study_id: str) -> dict[str, Any]:
        self.require_context(study_id)
        root = self.study_root(study_id)
        if not root.is_dir():
            raise ValidationError(f"找不到 Study 目錄：{root}")
        projection = validate_study(root, self.rules)
        if projection.study_id:
            self.authority.verify(study_id, projection.events)
        return projection.to_dict()
