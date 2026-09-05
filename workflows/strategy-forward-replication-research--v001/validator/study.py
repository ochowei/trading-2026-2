"""Study Event chain 的語意驗證與 projection。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .artifacts import (
    evaluate_historical,
    validate_development_trial,
    validate_snapshot_set,
    verified_artifact,
)
from .canonical_yaml import canonical_bytes, canonical_digest, load_canonical
from .errors import IntegrityError, TransitionError, ValidationError
from .metrics import validate_study_gates
from .paths import resolve_inside
from .schema_validation import SHA256_PATTERN, SchemaStore

EVENT_FILE_PATTERN = re.compile(r"^(?P<sequence>[0-9]{6})-(?P<event>[a-z0-9-]+)\.yml$")
TERMINAL_OUTCOMES = {"pass", "fail", "indeterminate"}
PROVENANCE_DISPOSITIONS = {
    "verified-clean": None,
    "known-contaminated": "fail",
    "provenance-unknown": "indeterminate",
}


@dataclass(frozen=True)
class EventRecord:
    path: Path
    value: dict[str, Any]
    digest: str


@dataclass
class StudyProjection:
    study_id: str | None = None
    bindings: dict[str, str] = field(default_factory=dict)
    identity: dict[str, Any] = field(default_factory=dict)
    events: list[EventRecord] = field(default_factory=list)
    effective_event_type: str | None = None
    paused_from_event_type: str | None = None
    paused_operation_digest: str | None = None
    preregistration: dict[str, Any] | None = None
    preregistration_digest: str | None = None
    trials: dict[str, dict[str, Any]] = field(default_factory=dict)
    trial_registry_digest: str | None = None
    provenance_status: str | None = None
    candidate: dict[str, Any] | None = None
    evidence: dict[str, str] = field(default_factory=dict)
    pending_terminal_outcome: str | None = None
    terminal_outcome: str | None = None
    terminal_authority: str = "none"

    @property
    def head_digest(self) -> str | None:
        return self.events[-1].digest if self.events else None

    @property
    def status(self) -> str:
        if self.terminal_outcome:
            return "terminal"
        if self.paused_from_event_type:
            return "paused"
        return "active" if self.events else "planned"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "study": {
                "identity": self.identity,
                "study_id": self.study_id,
            },
            "workflow_binding": self.bindings,
            "lifecycle": {
                "status": self.status,
                "current_event": self.effective_event_type,
                "event_count": len(self.events),
                "event_chain_head_digest": self.head_digest,
            },
            "trial_registry": {
                "recorded_trial_count": len(self.trials),
                "trial_ids": sorted(self.trials),
                "digest": self.trial_registry_digest,
            },
            "preregistration": {"digest": self.preregistration_digest},
            "provenance": {"status": self.provenance_status},
            "candidate_freeze": self.candidate,
            "evidence": self.evidence,
            "outcome": {
                "status": self.terminal_outcome or "pending",
                "authority": self.terminal_authority,
            },
        }


class WorkflowRules:
    def __init__(self, workflow_root: Path | str):
        self.root = Path(workflow_root)
        self.workflow = load_canonical(self.root / "workflow.yml")
        self.state_machine = load_canonical(self.root / self.workflow["state_machine_path"])
        self.floors = load_canonical(self.root / self.workflow["workflow_floors_path"])
        self.evidence_requirements = load_canonical(
            self.root / self.workflow["evidence_requirements_path"]
        )
        self.schema_store = SchemaStore(self.root / "schemas")
        self.schema_store.validate("workflow.schema.yml", self.workflow)

    def transition_allowed(self, source: str | None, target: str) -> bool:
        if source is None:
            return target == self.state_machine["initial_event"]
        allowed = self.state_machine["normal_transitions"].get(source, [])
        return isinstance(allowed, list) and target in allowed


def _require(payload: dict[str, Any], *names: str) -> None:
    missing = [name for name in names if name not in payload]
    if missing:
        raise ValidationError(f"Event payload 缺少欄位: {', '.join(missing)}")


def _digest(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise ValidationError(f"{field_name} 必須是 SHA-256")
    return value


def _event_source(projection: StudyProjection) -> str | None:
    return projection.effective_event_type


def _expected_registry_digest(projection: StudyProjection) -> str:
    ordered = [projection.trials[trial_id] for trial_id in sorted(projection.trials)]
    return canonical_digest({"trials": ordered})


def _expected_terminal_bindings(projection: StudyProjection) -> dict[str, str]:
    bindings = {
        "event_chain_head_digest": projection.head_digest,
        "workflow_digest": projection.bindings["workflow_digest"],
        "policy_set_digest": projection.bindings["policy_set_digest"],
        "source_bundle_digest": projection.bindings["source_bundle_digest"],
    }
    if projection.preregistration_digest:
        bindings["preregistration_digest"] = projection.preregistration_digest
    if projection.trial_registry_digest:
        bindings["trial_registry_digest"] = projection.trial_registry_digest
    evidence_names = {
        "development": "development_evidence_digest",
        "candidate-freeze": "candidate_freeze_digest",
        "historical-evaluation": "historical_evaluation_digest",
        "evidence-unavailable": "evidence_unavailable_digest",
    }
    for evidence_name, binding_name in evidence_names.items():
        if evidence_name in projection.evidence:
            bindings[binding_name] = projection.evidence[evidence_name]
    return bindings


def _validate_reference(
    study_root: Path,
    payload: dict[str, Any],
    *,
    path_field: str = "evidence_path",
    digest_field: str = "evidence_digest",
) -> tuple[Path, Any]:
    _require(payload, path_field, digest_field)
    return verified_artifact(
        study_root, payload[path_field], _digest(payload[digest_field], digest_field)
    )


def _validate_event_semantics(
    projection: StudyProjection,
    event: dict[str, Any],
    rules: WorkflowRules,
    study_root: Path,
) -> None:
    event_type = event["event_type"]
    payload = event["payload"]

    if projection.pending_terminal_outcome and event_type != "study-terminal":
        raise TransitionError("已形成 terminal disposition，只能追加 study-terminal")

    if event_type == "study-created":
        _require(payload, "research_round_id", "experiment_family", "research_owner")
        if not payload.get("historical_evaluation_operator") and not payload.get(
            "replay_operator"
        ):
            raise ValidationError("Study identity 必須指定 Historical Evaluation 執行者")
        _require(payload, "source_bundle_path", "source_bundle_digest")
        source_path, source_bundle = verified_artifact(
            study_root,
            payload["source_bundle_path"],
            payload["source_bundle_digest"],
        )
        rules.schema_store.validate("source-bundle.schema.yml", source_bundle)
        if canonical_digest(source_path.read_bytes()) != event["bindings"]["source_bundle_digest"]:
            raise IntegrityError("Source Bundle artifact 與 Study binding 不一致")
        projection.study_id = event["study_id"]
        projection.bindings = dict(event["bindings"])
        projection.identity = dict(payload)
        return

    if event["study_id"] != projection.study_id:
        raise IntegrityError("Event study_id 與 chain identity 不一致")
    if event["bindings"] != projection.bindings:
        raise IntegrityError("Event bindings 與 Study frozen bindings 不一致")

    if event_type == "preregistration-approved":
        path, preregistration = _validate_reference(
            study_root,
            payload,
            path_field="preregistration_path",
            digest_field="preregistration_digest",
        )
        rules.schema_store.validate("preregistration.schema.yml", preregistration)
        validate_study_gates(
            preregistration["evaluation_gates"],
            rules.floors["historical_evaluation"],
        )
        projection.preregistration = preregistration
        projection.preregistration_digest = canonical_digest(path.read_bytes())
        return

    if event_type == "development-authorized":
        _validate_reference(study_root, payload)
        return

    if event_type == "trial-recorded":
        _require(payload, "trial_id", "inputs_digest", "status")
        trial_id = payload["trial_id"]
        if trial_id in projection.trials:
            raise ValidationError(f"Trial ID 重複: {trial_id}")
        _digest(payload["inputs_digest"], "inputs_digest")
        if payload["status"] not in {"completed", "failed", "removed", "abandoned"}:
            raise ValidationError("Trial status 不合法")
        if payload["inputs_digest"] in {
            recorded["inputs_digest"] for recorded in projection.trials.values()
        }:
            raise ValidationError("完全相同 inputs 是同一 Trial，不得用新 Trial ID 重複計數")
        legacy_exempt = projection.bindings["workflow_digest"] in rules.evidence_requirements.get(
            "legacy_development_binding_exempt_workflow_digests", []
        )
        if not legacy_exempt:
            _require(
                payload,
                "inputs_path",
                "development_evidence_path",
                "development_evidence_digest",
            )
            inputs_path, inputs = verified_artifact(
                study_root, payload["inputs_path"], payload["inputs_digest"]
            )
            evidence_path, evidence = verified_artifact(
                study_root,
                payload["development_evidence_path"],
                _digest(payload["development_evidence_digest"], "development_evidence_digest"),
            )
            assert projection.preregistration is not None
            assert projection.preregistration_digest is not None
            validate_development_trial(
                evidence,
                inputs,
                projection.preregistration,
                trial_id=trial_id,
                trial_inputs_digest=canonical_digest(inputs_path.read_bytes()),
                preregistration_digest=projection.preregistration_digest,
                source_bundle_digest=projection.bindings["source_bundle_digest"],
            )
            projection.evidence["development"] = canonical_digest(evidence_path.read_bytes())
        projection.trials[trial_id] = dict(payload)
        return

    if event_type == "trial-registry-frozen":
        _require(
            payload,
            "maximum_trials",
            "recorded_trial_count",
            "complete_family_trial_ids",
            "trial_registry_digest",
            "candidate_available",
        )
        assert projection.preregistration is not None
        expected_ids = projection.preregistration["complete_candidate_family"]
        actual_ids = payload["complete_family_trial_ids"]
        if len(actual_ids) != len(set(actual_ids)):
            raise ValidationError("Complete Candidate Family 不得有重複 Trial ID")
        if set(actual_ids) != set(expected_ids) or set(actual_ids) != set(projection.trials):
            raise ValidationError(
                "Frozen registry 必須完整等於 preregistered family 與已記錄 Trials"
            )
        if payload["maximum_trials"] != projection.preregistration["maximum_trials"]:
            raise ValidationError("maximum_trials 與 preregistration 不一致")
        if len(projection.trials) > payload["maximum_trials"]:
            raise ValidationError("Trial budget 已超額")
        if payload["recorded_trial_count"] != len(projection.trials):
            raise ValidationError("recorded_trial_count 不正確")
        expected_digest = _expected_registry_digest(projection)
        if payload["trial_registry_digest"] != expected_digest:
            raise IntegrityError("trial_registry_digest 不正確")
        projection.trial_registry_digest = expected_digest
        if payload["candidate_available"] is False:
            projection.pending_terminal_outcome = "fail"
        elif payload["candidate_available"] is not True:
            raise ValidationError("candidate_available 必須是 boolean")
        return

    if event_type == "provenance-audited":
        _require(payload, "status", "artifact_path", "artifact_digest")
        status = payload["status"]
        if status not in PROVENANCE_DISPOSITIONS:
            raise ValidationError("未知 provenance status")
        verified_artifact(study_root, payload["artifact_path"], payload["artifact_digest"])
        projection.provenance_status = status
        projection.pending_terminal_outcome = PROVENANCE_DISPOSITIONS[status]
        return

    if event_type == "candidate-frozen":
        _require(
            payload,
            "selected_candidate_id",
            "baseline_id",
            "baseline_family",
            "baseline_objectively_simpler",
            "candidate_digest",
            "trial_registry_digest",
            "qualification_spec_digest",
            "evaluation_snapshot_digest",
            "fold_inventory_digest",
            "snapshot_set_path",
            "snapshot_set_digest",
            "selection_evidence_path",
            "selection_evidence_digest",
        )
        assert projection.preregistration is not None
        selected = payload["selected_candidate_id"]
        if selected not in projection.trials:
            raise ValidationError("Selected Candidate 不在完整 Candidate Family")
        if projection.trials[selected]["status"] != "completed":
            raise ValidationError("Selected Candidate 必須是已完成的 Trial")
        selected_trial = projection.trials[selected]
        if "development_evidence_digest" in selected_trial:
            _require(payload, "development_evidence_digest")
            if payload["development_evidence_digest"] != selected_trial[
                "development_evidence_digest"
            ]:
                raise IntegrityError("Candidate Freeze 沒有綁定 selected Trial 的 Development evidence")
        if payload["baseline_id"] in projection.trials:
            raise ValidationError("Baseline 必須位於 Candidate Family 之外")
        if payload["baseline_family"] == projection.identity["experiment_family"]:
            raise ValidationError("Baseline 必須來自不同 strategy family")
        if payload["baseline_objectively_simpler"] is not True:
            raise ValidationError("Baseline 必須符合 preregistered simpler rule")
        if payload["trial_registry_digest"] != projection.trial_registry_digest:
            raise IntegrityError("Candidate Freeze 沒有綁定同一 frozen registry")
        _, selection_evidence = verified_artifact(
            study_root,
            payload["selection_evidence_path"],
            payload["selection_evidence_digest"],
        )
        rules.schema_store.validate("selection-evidence.schema.yml", selection_evidence)
        eligible_ids = selection_evidence["ordered_eligible_trial_ids"]
        if not set(eligible_ids).issubset(projection.trials):
            raise ValidationError("Selection Evidence 包含未登記的 Trial")
        if selection_evidence["selected_candidate_id"] != selected or eligible_ids[0] != selected:
            raise ValidationError("Selected Candidate 必須是依預先規則排序後的第一名")
        expected_rule_digest = canonical_digest(
            {
                "eligibility_rules": projection.preregistration["eligibility_rules"],
                "selection_rule": projection.preregistration["selection_rule"],
                "tie_handling": projection.preregistration["tie_handling"],
            }
        )
        if selection_evidence["rule_digest"] != expected_rule_digest:
            raise IntegrityError("Selection Evidence 沒有綁定 preregistered selection rules")
        for name in (
            "candidate_digest",
            "qualification_spec_digest",
            "evaluation_snapshot_digest",
            "fold_inventory_digest",
        ):
            _digest(payload[name], name)
        _, snapshot_set = verified_artifact(
            study_root,
            payload["snapshot_set_path"],
            payload["snapshot_set_digest"],
        )
        snapshots = validate_snapshot_set(snapshot_set, rules.workflow, rules.schema_store)
        if (
            snapshots["historical-evaluation"]["data_digest"]
            != payload["evaluation_snapshot_digest"]
        ):
            raise IntegrityError("Evaluation snapshot digest 與 Candidate Freeze 不一致")
        expected_inventory_digest = canonical_digest(
            {"sessions": snapshots["historical-evaluation"]["sessions"]}
        )
        if payload["fold_inventory_digest"] != expected_inventory_digest:
            raise IntegrityError("Evaluation fold inventory digest 不正確")
        projection.candidate = dict(payload)
        projection.evidence["candidate-freeze"] = canonical_digest(payload)
        return

    if event_type == "historical-evaluation-completed":
        path, evidence = _validate_reference(study_root, payload)
        rules.schema_store.validate("historical-evaluation.schema.yml", evidence)
        assert projection.preregistration is not None
        gates = dict(rules.floors["historical_evaluation"])
        gates.update(projection.preregistration["evaluation_gates"])
        metrics, failures = evaluate_historical(
            evidence,
            gates,
            fold_warmup_sessions=projection.preregistration["fold_warmup_sessions"],
            maximum_holding_sessions=projection.preregistration["maximum_holding_sessions"],
        )
        if projection.bindings["workflow_digest"] in rules.evidence_requirements.get(
            "legacy_metric_shape_workflow_digests", []
        ):
            metrics.pop("maximum_realized_trade_loss_fraction", None)
        expected = "fail" if failures else "pass"
        if payload.get("disposition") != expected:
            raise ValidationError("Historical Evaluation disposition 與重算 gates 不一致")
        projection.evidence["historical-evaluation"] = canonical_digest(path.read_bytes())
        projection.evidence["historical-evaluation-metrics"] = canonical_digest(metrics)
        projection.pending_terminal_outcome = expected
        return

    if event_type == "evidence-unavailable":
        _require(payload, "stage", "unavailable_path", "reason")
        missing = resolve_inside(study_root, payload["unavailable_path"], must_exist=False)
        if missing.exists():
            raise ValidationError("evidence-unavailable 只能指向目前無法取得的 artifact")
        projection.evidence["evidence-unavailable"] = canonical_digest(payload)
        projection.pending_terminal_outcome = "indeterminate"
        return

    if event_type == "study-paused":
        _require(payload, "reason", "frozen_operation_digest")
        projection.paused_from_event_type = projection.effective_event_type
        projection.paused_operation_digest = _digest(
            payload["frozen_operation_digest"], "frozen_operation_digest"
        )
        return

    if event_type == "study-resumed":
        _require(payload, "frozen_operation_digest")
        if projection.paused_from_event_type is None:
            raise TransitionError("Study 未 paused，不能 resume")
        if payload["frozen_operation_digest"] != projection.paused_operation_digest:
            raise IntegrityError("Recovery 必須使用相同 frozen operation")
        projection.effective_event_type = projection.paused_from_event_type
        projection.paused_from_event_type = None
        projection.paused_operation_digest = None
        return

    if event_type == "study-terminal":
        _require(
            payload,
            "outcome",
            "authority",
            "terminal_evidence_path",
            "terminal_evidence_digest",
        )
        outcome = payload["outcome"]
        if outcome not in TERMINAL_OUTCOMES:
            raise ValidationError("Terminal outcome 不合法")
        if projection.pending_terminal_outcome != outcome:
            raise ValidationError("Terminal outcome 與前一階段重算 disposition 不一致")
        _, terminal = verified_artifact(
            study_root,
            payload["terminal_evidence_path"],
            payload["terminal_evidence_digest"],
        )
        rules.schema_store.validate("terminal-evidence.schema.yml", terminal)
        if terminal["outcome"] != outcome:
            raise IntegrityError("Terminal event 與 Terminal Evidence outcome 不一致")
        if terminal["bindings"] != _expected_terminal_bindings(projection):
            raise IntegrityError("Terminal Evidence bindings 不完整或與目前 Study 不一致")
        expected_authority = "retrospectively-supported" if outcome == "pass" else "none"
        if (
            payload["authority"] != expected_authority
            or terminal["authority"] != expected_authority
        ):
            raise ValidationError("Terminal authority 不正確")
        projection.terminal_outcome = outcome
        projection.terminal_authority = expected_authority
        projection.pending_terminal_outcome = None
        return

    raise ValidationError(f"未實作的 event type: {event_type}")


def apply_event(
    projection: StudyProjection,
    event: dict[str, Any],
    rules: WorkflowRules,
    study_root: Path,
) -> None:
    target = event["event_type"]
    source = _event_source(projection)
    if target == "study-resumed":
        if projection.paused_from_event_type is None:
            raise TransitionError("Study 未 paused，不能 resume")
    elif not rules.transition_allowed(source, target):
        raise TransitionError(f"不合法的 Study Event transition: {source} -> {target}")
    _validate_event_semantics(projection, event, rules, study_root)
    if target not in {"study-paused", "study-resumed"}:
        projection.effective_event_type = target


def load_event_records(study_root: Path | str, rules: WorkflowRules) -> list[EventRecord]:
    root = Path(study_root)
    event_dir = root / "events"
    paths = sorted(event_dir.glob("*.yml")) if event_dir.exists() else []
    records: list[EventRecord] = []
    previous_digest: str | None = None
    for expected_sequence, path in enumerate(paths, start=1):
        match = EVENT_FILE_PATTERN.fullmatch(path.name)
        if match is None:
            raise IntegrityError(f"不合法的 event filename: {path.name}")
        value = load_canonical(path)
        rules.schema_store.validate("event.schema.yml", value)
        if (
            int(match.group("sequence")) != expected_sequence
            or value["sequence"] != expected_sequence
        ):
            raise IntegrityError("Event sequence 中斷或與 filename 不一致")
        if match.group("event") != value["event_type"]:
            raise IntegrityError("Event type 與 filename 不一致")
        if value["previous_event_digest"] != previous_digest:
            raise IntegrityError("previous_event_digest chain 不連續")
        digest = canonical_digest(path.read_bytes())
        records.append(EventRecord(path, value, digest))
        previous_digest = digest
    return records


def validate_study(
    study_root: Path | str,
    rules: WorkflowRules,
    *,
    check_projection: bool = True,
) -> StudyProjection:
    root = Path(study_root)
    projection = StudyProjection()
    for record in load_event_records(root, rules):
        if record.value["previous_event_digest"] != projection.head_digest:
            raise IntegrityError("Event chain head 不一致")
        apply_event(projection, record.value, rules, root)
        projection.events.append(record)
    projection_path = root / "study.yml"
    if check_projection and projection_path.exists():
        stored = load_canonical(projection_path)
        if canonical_bytes(stored) != canonical_bytes(projection.to_dict()):
            raise IntegrityError("study.yml projection 與 event chain 不一致")
    return projection
