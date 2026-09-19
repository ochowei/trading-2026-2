"""Evaluation 角色的固定輸入、一次執行入口；結果僅寫專用 store。"""

from __future__ import annotations

import csv
import io
import shutil

from validator.approvals import approval
from validator.artifacts import evaluate_historical
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
    with StudyLock(service.study_root(study_id) / ".writer.lock"):
        service.recover(study_id)
        state = projection(service, study_id)
        if not state.candidate:
            raise ValidationError("Historical Evaluation 必須已有 candidate freeze")
        if plan["actor"] != state.identity["historical_evaluation_operator"]:
            raise ValidationError("操作者與 Study 指定的 Evaluation operator 不一致")
        approval(
            plan["authorization"],
            plan["authorization"]["actor_id"],
            "historical-evaluation-only",
            study_id=study_id,
            source_digest=state.bindings["source_bundle_digest"],
            prereg_digest=state.preregistration_digest,
        )
        if (
            plan["authorization"].get("candidate_freeze_digest")
            != state.evidence["candidate-freeze"]
        ):
            raise IntegrityError("Evaluation 核准未綁定此次 candidate freeze")
        directory = remember(service, study_id, "historical-evaluation", plan)
        # 固定 Study 層級單次 operation；不同 plan 不可啟動第二次 Evaluation。
        atomic_create(
            service.study_root(study_id) / "manifests/evaluation-operation.yml",
            canonical_bytes({"operation_id": directory.name}),
        )
        store = service.rules.historical_evaluation_artifacts_root / study_id
        workspace = store / "runtime"
        output = workspace / "run/evidence.yml"
        if state.effective_event_type == "candidate-frozen" and not output.exists():
            if (directory / "started.yml").exists():
                raise IntegrityError(
                    "Evaluation 已開始且輸出不完整；禁止自動重跑，需判定 exposure 與不可恢復路徑"
                )
            if plan["data_digest"] != state.candidate["evaluation_snapshot_digest"]:
                raise IntegrityError("Evaluation 資料不是 candidate freeze 的 snapshot")
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
            atomic_create(
                directory / "started.yml",
                canonical_bytes({"request_digest": canonical_digest(request), "runner": runner}),
            )
            launch(workspace, package, runner, workspace / "run/request.yml", output)
        if state.effective_event_type == "candidate-frozen":
            evidence = load_canonical(output)
            service.rules.schema_store.validate("historical-evaluation.schema.yml", evidence)
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
            proof_path, proof_digest = service.publish_historical_evaluation_artifact(
                study_id, "evidence/authorization.yml", plan["authorization"]
            )
            service.append_event(
                study_id,
                "historical-evaluation-completed",
                plan["actor"],
                {
                    "evidence_path": path,
                    "evidence_digest": digest,
                    "disposition": "fail" if failures else "pass",
                    "authorization_path": proof_path,
                    "authorization_digest": proof_digest,
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
