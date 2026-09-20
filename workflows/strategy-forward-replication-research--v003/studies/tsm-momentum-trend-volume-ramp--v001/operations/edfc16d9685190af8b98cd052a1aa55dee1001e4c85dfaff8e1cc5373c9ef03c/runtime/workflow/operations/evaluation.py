"""Evaluation 角色的固定輸入、一次執行入口；結果僅寫專用 store。"""

from __future__ import annotations

import csv
import io
import shutil

from validator.artifacts import evaluate_historical
from validator.assignments import EVALUATOR, AssignmentError, reject_legacy, safe_path
from validator.canonical_yaml import (
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.errors import IntegrityError, ValidationError
from validator.paths import resolve_inside
from validator.study import _expected_terminal_bindings
from writer.lock import StudyLock

from operations.lifecycle import projection, remember
from operations.preflight import launch, source_files


def historical_evaluation(service, study_id, plan):
    service.require_context(study_id, plan["actor"])
    if service.role != EVALUATOR:
        raise AssignmentError("role-mismatch", "Historical Evaluation 限評估角色")
    reject_legacy(plan)
    service.rules.schema_store.validate("evaluation-plan.schema.yml", plan)
    with StudyLock(service.study_root(study_id) / ".writer.lock"):
        service.recover(study_id)
        state = projection(service, study_id)
        if not state.candidate:
            raise ValidationError("Historical Evaluation 必須已有 candidate freeze")
        if plan["actor"] != state.identity["historical_evaluation_operator"]:
            raise AssignmentError(
                "role-mismatch", "操作者與 Study 指定的 Evaluation operator 不一致"
            )
        if plan["data_digest"] != state.candidate["evaluation_snapshot_digest"]:
            raise AssignmentError("binding-mismatch", "評估資料未綁定 candidate freeze")
        try:
            directory = remember(service, study_id, "historical-evaluation", plan)
        except IntegrityError as exc:
            raise AssignmentError("evaluation-already-started", "只能恢復原評估 operation") from exc
        report = load_canonical(
            service.study_root(study_id) / state.identity["prepare_report_path"]
        )
        reservation = {
            "operation_id": directory.name,
            "assignment_digest": canonical_digest(service.assignment),
            "workflow_digest": state.bindings["workflow_digest"],
            "study_id": study_id,
            "authority_root": str(service.authority.root),
            "source_bundle_digest": state.bindings["source_bundle_digest"],
            "preregistration_digest": state.preregistration_digest,
            "candidate_freeze_digest": state.evidence["candidate-freeze"],
            "data_digest": plan["data_digest"],
            "runner_digest": report["binding"]["settings"]["runner-contract.yml"],
            "plan_digest": canonical_digest(plan),
        }
        atomic_create(
            service.study_root(study_id) / "manifests/evaluation-operation.yml",
            canonical_bytes(reservation),
        )
        if state.effective_event_type == "candidate-frozen":
            service.append_event(
                study_id,
                "historical-evaluation-started",
                plan["actor"],
                {
                    "operation_id": directory.name,
                    "reservation_digest": canonical_digest(reservation),
                },
            )
            state = projection(service, study_id)
        if state.paused_from_event_type:
            raise AssignmentError("recovery-required", "先恢復同一暫停 operation")
        if state.effective_event_type == "evidence-unavailable":
            return unavailable(service, study_id, plan, directory)
        store = safe_path(
            service.rules.historical_evaluation_artifacts_root / study_id,
            service.repository_root,
            service.role,
        )
        workspace = store / "runtime"
        output = workspace / "run/evidence.yml"
        authority_marker = service.authority.root / study_id / "evaluation-launch.yml"
        local_marker = directory / "launch-marker.yml"
        if (
            state.effective_event_type == "historical-evaluation-started"
            and output.exists()
            and not (local_marker.exists() and authority_marker.exists())
        ):
            raise IntegrityError("缺少評估 launch marker，不能接受既有輸出")
        if state.effective_event_type == "historical-evaluation-started" and not output.exists():
            if local_marker.exists() or authority_marker.exists():
                return unavailable(service, study_id, plan, directory)
            if plan["data_digest"] != state.candidate["evaluation_snapshot_digest"]:
                raise IntegrityError("Evaluation 資料不是 candidate freeze 的 snapshot")
            safe_path(
                service.repository_root / plan["data_path"], service.repository_root, service.role
            )
            data_path = resolve_inside(service.repository_root, plan["data_path"])
            if {".super-admin", ".project-manager"}.intersection(
                data_path.relative_to(service.repository_root).parts
            ):
                raise ValidationError("Evaluation 不接受管理者專屬內容")
            atomic_create(
                directory / "data-access.yml",
                canonical_bytes(
                    {"path": plan["data_path"], "expected_digest": plan["data_digest"]}
                ),
            )
            data = data_path.read_bytes()
            if canonical_digest(data) != plan["data_digest"]:
                raise IntegrityError("Evaluation 資料 digest 漂移")
            dates = [row["Date"] for row in csv.DictReader(io.StringIO(data.decode()))]
            snapshot = load_canonical(
                service.study_root(study_id) / state.candidate["snapshot_set_path"]
            )
            expected_dates = next(
                item["sessions"]
                for item in snapshot["snapshots"]
                if item["role"] == "historical-evaluation"
            )
            if dates != expected_dates:
                raise IntegrityError("Evaluation rows 與 frozen session inventory 不一致")
            if not dates or any(day < "2020-01-01" or day > "2024-12-31" for day in dates):
                raise ValidationError("Evaluation 資料超出 frozen 2020–2024 區間")
            report = load_canonical(
                service.study_root(study_id) / state.identity["prepare_report_path"]
            )
            bundle = report["binding"]["source_bundle"]
            for relative, source in source_files(service.repository_root, bundle).items():
                atomic_create(workspace / relative, source.read_bytes())
            package = workspace / "workflow"
            if not package.exists():
                shutil.copytree(
                    service.workflow_root,
                    package,
                    ignore=shutil.ignore_patterns(
                        "studies",
                        "__pycache__",
                        "release-manifest.yml",
                        "release-test-report.yml",
                        "release.yml",
                    ),
                )
            trial = state.trials[state.candidate["selected_candidate_id"]]
            inputs = load_canonical(service.study_root(study_id) / trial["inputs_path"])
            request = {
                "stage": "historical-evaluation",
                "data_path": "run/bars.csv",
                "data_digest": plan["data_digest"],
                "preregistration": state.preregistration,
                "trial_inputs": inputs,
                "source_bundle": bundle,
            }
            atomic_create(workspace / "run/bars.csv", data)
            atomic_create(workspace / "run/request.yml", canonical_bytes(request))
            runner = load_canonical(workspace / f"research/{study_id}/runner-contract.yml")[
                "runners"
            ]["historical-evaluation"]
            marker = canonical_bytes(
                {
                    "operation_id": directory.name,
                    "request_digest": canonical_digest(request),
                    "runner": runner,
                }
            )
            atomic_create(authority_marker, marker)
            atomic_create(local_marker, marker)
            launch(workspace, package, runner, workspace / "run/request.yml", output)
        if state.effective_event_type == "historical-evaluation-started":
            try:
                evidence = load_canonical(output)
                service.rules.schema_store.validate("historical-evaluation.schema.yml", evidence)
            except Exception:
                return unavailable(service, study_id, plan, directory)
            gates = dict(service.rules.floors["historical_evaluation"])
            gates.update(state.preregistration["evaluation_gates"])
            _, failures = evaluate_historical(
                evidence,
                gates,
                fold_warmup_sessions=state.preregistration["fold_warmup_sessions"],
                maximum_holding_sessions=state.preregistration["maximum_holding_sessions"],
            )
            path, digest = service.publish_historical_evaluation_artifact(
                study_id, "evidence/historical-evaluation.yml", evidence
            )
            service.append_event(
                study_id,
                "historical-evaluation-completed",
                plan["actor"],
                {
                    "evidence_path": path,
                    "evidence_digest": digest,
                    "disposition": "fail" if failures else "pass",
                    "operation_id": directory.name,
                },
            )
            state = projection(service, study_id)
        if state.effective_event_type == "historical-evaluation-completed":
            terminal = {
                "schema_version": 1,
                "outcome": state.pending_terminal_outcome,
                "authority": "retrospectively-supported"
                if state.pending_terminal_outcome == "pass"
                else "none",
                "bindings": _expected_terminal_bindings(state),
                "recomputed": True,
                "reasons": ["依 frozen gates 與 raw evidence 重算"],
            }
            path, digest = service.publish_historical_evaluation_artifact(
                study_id, "evidence/terminal.yml", terminal
            )
            service.append_event(
                study_id,
                "study-terminal",
                plan["actor"],
                {
                    "outcome": terminal["outcome"],
                    "authority": terminal["authority"],
                    "terminal_evidence_path": path,
                    "terminal_evidence_digest": digest,
                },
            )
        state = projection(service, study_id)
        if state.terminal_outcome is None:
            raise ValidationError("Evaluation operation 未完成至 terminal")
        atomic_create(
            directory / "completed.yml", canonical_bytes({"operation_id": directory.name})
        )
        return {
            "status": "completed",
            "operation_id": directory.name,
            "outcome": state.terminal_outcome,
        }


def unavailable(service, study_id, plan, directory):
    """啟動狀態無法確定時保守終止；只保存控制資訊與 store 內證據。"""
    state = projection(service, study_id)
    if state.effective_event_type == "historical-evaluation-started":
        service.append_event(
            study_id,
            "evidence-unavailable",
            plan["actor"],
            {
                "stage": "historical-evaluation",
                "unavailable_path": "evidence/evaluation-output-not-certifiable.yml",
                "reason": "launch marker 已持久保存，但無法取得可重驗完整輸出；禁止重跑",
            },
        )
        state = projection(service, study_id)
    terminal = {
        "schema_version": 1,
        "outcome": "indeterminate",
        "authority": "none",
        "bindings": _expected_terminal_bindings(state),
        "recomputed": True,
        "reasons": ["評估啟動後輸出缺失或不完整，無法證明尚未執行"],
    }
    path, digest = service.publish_historical_evaluation_artifact(
        study_id, "evidence/terminal.yml", terminal
    )
    if state.terminal_outcome is None:
        service.append_event(
            study_id,
            "study-terminal",
            plan["actor"],
            {
                "outcome": "indeterminate",
                "authority": "none",
                "terminal_evidence_path": path,
                "terminal_evidence_digest": digest,
            },
        )
    atomic_create(directory / "completed.yml", canonical_bytes({"operation_id": directory.name}))
    return {"status": "completed", "operation_id": directory.name, "outcome": "indeterminate"}
