"""唯一正式 Study 寫入服務。"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from validator.canonical_yaml import (
    atomic_create,
    atomic_replace,
    canonical_bytes,
    canonical_digest,
)
from validator.errors import IntegrityError, ValidationError
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
        allow_draft: bool = False,
    ):
        self.workflow_root = Path(workflow_root).resolve()
        self.authority = AuthorityStore(authority_root)
        self.allow_draft = allow_draft
        self.rules = WorkflowRules(self.workflow_root)
        self.workflow_digest = workflow_digest(self.workflow_root, allow_draft=allow_draft)
        self.policy_set_digest = policy_set_digest(self.workflow_root)
        if not allow_draft:
            validate_release_record(self.workflow_root)

    def study_root(self, study_id: str) -> Path:
        if not study_id or "/" in study_id or ".." in study_id:
            raise ValidationError("不安全的 study_id")
        return self.workflow_root / "studies" / study_id

    def publish_artifact(self, study_id: str, relative_path: str, value: Any) -> tuple[str, str]:
        if relative_path.startswith("/") or ".." in Path(relative_path).parts:
            raise ValidationError("Artifact path 必須位於 Study 目錄內")
        root = self.study_root(study_id)
        destination = root / relative_path
        data = canonical_bytes(value)
        atomic_create(destination, data)
        return relative_path, canonical_digest(data)

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
    ) -> str:
        self.rules.schema_store.validate("source-bundle.schema.yml", source_bundle)
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
        }
        return self.append_event(
            study_id,
            "study-created",
            actor_id,
            payload,
            source_bundle_digest=source_bundle_digest,
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
    ) -> str:
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
        root = self.study_root(study_id)
        with StudyLock(root / ".writer.lock"):
            recovered = JournalPublisher(root, self.authority.root).recover()
            projection = validate_study(root, self.rules, check_projection=False)
            self.authority.verify(study_id, projection.events)
            atomic_replace(root / "study.yml", canonical_bytes(projection.to_dict()))
            return recovered

    def validate(self, study_id: str) -> dict[str, Any]:
        root = self.study_root(study_id)
        if not root.is_dir():
            raise ValidationError(f"找不到 Study 目錄：{root}")
        projection = validate_study(root, self.rules)
        if projection.study_id:
            self.authority.verify(study_id, projection.events)
        return projection.to_dict()
