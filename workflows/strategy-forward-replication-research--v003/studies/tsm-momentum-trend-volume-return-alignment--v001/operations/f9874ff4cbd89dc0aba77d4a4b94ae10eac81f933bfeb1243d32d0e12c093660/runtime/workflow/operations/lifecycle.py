"""可接續的日常操作；operation 保存原始計畫，事件仍各自 commit。"""

from __future__ import annotations

import csv
import io
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from validator.canonical_yaml import (
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.errors import IntegrityError, ValidationError
from validator.paths import resolve_inside
from validator.qualification import ordered_eligible
from validator.study import (
    StudyProjection,
    _expected_terminal_bindings,
    apply_event,
    load_event_records,
    validate_study,
)
from writer.lock import StudyLock
from writer.service import StudyService

from operations.preflight import launch, source_files
from operations.publication import consume


def projection(service, study_id):
    value = validate_study(service.study_root(study_id), service.rules)
    service.authority.verify(study_id, value.events)
    return value


def assert_development_scope(service, study_id):
    """恢復前僅檢查事件／operation 類型，不要求尚待補齊的 checkpoint 已一致。"""
    import base64

    import yaml

    root = service.study_root(study_id)
    from validator.assignments import safe_path

    for directory in ("events", "journals", "operations"):
        safe_path(root / directory, service.repository_root, service.role)

    def read(path):
        safe_path(path, service.repository_root, service.role)
        return load_canonical(path)

    values = [read(path) for path in (root / "events").glob("*.yml")]
    for path in (root / "journals").glob("*.prepared.yml"):
        journal = read(path)
        values.append(
            yaml.safe_load(base64.b64decode(journal["event_bytes_base64"], validate=True))
        )
    if any(
        value["event_type"] in {"historical-evaluation-started", "historical-evaluation-completed"}
        for value in values
    ):
        raise ValidationError("後續階段超出開發者讀取範圍，請交接 Evaluation 執行者")
    for path in (root / "operations").glob("*/plan.yml"):
        if read(path)["kind"] == "historical-evaluation":
            raise ValidationError("已有 Evaluation operation，開發者不得恢復評估")


def status(service, study_id, *, role):
    """開發者只重建 Development prefix，不開啟 Evaluation artifact。"""
    root = service.study_root(study_id)
    if not root.exists():
        raise ValidationError("找不到 Study")
    from validator.assignments import safe_path

    for path in [root / "events", *(root / "events").glob("*.yml")]:
        safe_path(path, service.repository_root, role)
    records = load_event_records(root, service.rules)
    service.authority.verify(study_id, records)
    state = StudyProjection()
    unverified = False
    for record in records:
        if role != "Study 歷史評估執行者" and record.value["event_type"] in {
            "historical-evaluation-started",
            "historical-evaluation-completed",
            "study-terminal",
        }:
            unverified = True
            break
        apply_event(state, record.value, service.rules, root)
        state.events.append(record)
    return {
        "status": "passed",
        "projection": state.to_dict(),
        "later_stage": "not_inspected" if unverified else "not_present",
        "chain_integrity_verified": True,
        "full_semantic_validation": not unverified,
        "operations": [
            p.parent.name
            for p in (root / "operations").glob("*/plan.yml")
            if not (p.parent / "completed.yml").exists()
        ],
        "blind_review": {"status": "requires_explicit_exposure_facts"},
        "next_action": "later-stage-handoff"
        if unverified
        else (
            "terminate"
            if state.pending_terminal_outcome
            else ("handoff" if state.candidate else "resume_or_development")
        ),
    }


def _operation_directory(service, study_id, kind, plan):
    identity = canonical_digest(
        {"kind": kind, "plan": plan, "authority_root": str(service.authority.root)}
    )
    root = service.study_root(study_id)
    for saved in (root / "operations").glob("*/plan.yml"):
        existing = load_canonical(saved)
        if (
            existing["kind"] == kind
            and (
                kind != "development"
                or existing["plan"]["trial_inputs"]["candidate_id"]
                == plan["trial_inputs"]["candidate_id"]
            )
            and saved.parent.name != identity
        ):
            raise IntegrityError("同一步驟不能更換原 operation plan")
    from validator.assignments import safe_path

    return safe_path(root / "operations" / identity, service.repository_root, service.role)


def remember(service, study_id, kind, plan):
    from validator.assignments import reject_legacy

    reject_legacy(plan)
    service.require_context(study_id, plan["actor"])
    directory = _operation_directory(service, study_id, kind, plan)
    atomic_create(
        directory / "plan.yml",
        canonical_bytes(
            {"kind": kind, "plan": plan, "authority_root": str(service.authority.root)}
        ),
    )
    return directory


def development(service, study_id, plan):
    service.rules.schema_store.validate("development-plan.schema.yml", plan)
    service.require_context(study_id, plan["actor"])
    root = service.study_root(study_id)
    with StudyLock(root / ".writer.lock"):
        service.recover(study_id)
        state = projection(service, study_id)
        if state.preregistration is None:
            raise ValidationError("尚未完成預先登記，不能執行 Development")
        inputs = plan["trial_inputs"]
        trial = inputs["candidate_id"]
        if trial not in state.preregistration["complete_candidate_family"]:
            raise ValidationError("Trial 未預先登記")
        report = load_canonical(root / state.identity["prepare_report_path"])
        digest = canonical_digest(inputs)
        frozen_digests = set(report["binding"]["settings"].values()) | {
            item["digest"] for item in report["binding"]["source_bundle"]["files"]
        }
        if digest not in frozen_digests:
            raise IntegrityError("Trial inputs 未被 prepare／Source Bundle 凍結")
        directory = remember(service, study_id, "development", plan)
        if trial in state.trials:
            if (
                not (directory / "published-payload.yml").exists()
                or load_canonical(directory / "published-payload.yml") != state.trials[trial]
            ):
                raise IntegrityError("已登錄 Trial 不可用其他 operation 重跑")
            atomic_create(
                directory / "completed.yml", canonical_bytes({"operation_id": directory.name})
            )
            return {
                "status": "completed",
                "operation_id": directory.name,
                "assessment": state.trial_assessments[trial],
            }
        if state.effective_event_type not in {"development-started", "trial-recorded"}:
            raise ValidationError("目前階段不能執行 Development")
        workspace = directory / "runtime"
        output = workspace / "run/evidence.yml"
        if not output.exists():
            if (directory / "started.yml").exists():
                raise IntegrityError(
                    "runner 已開始但沒有完整輸出；需要人工判定 exposure 與原 operation 恢復，不得自動重跑"
                )
            bundle = report["binding"]["source_bundle"]
            files = source_files(service.repository_root, bundle)
            data_path = resolve_inside(service.repository_root, plan["data_path"])
            if {"historical-evaluation-artifacts", ".super-admin", ".project-manager"}.intersection(
                data_path.relative_to(service.repository_root).parts
            ):
                raise ValidationError("Development 不接受受限資料")
            atomic_create(
                directory / "data-access.yml",
                canonical_bytes(
                    {"path": plan["data_path"], "expected_digest": plan["data_digest"]}
                ),
            )
            data = data_path.read_bytes()
            if canonical_digest(data) != plan["data_digest"]:
                raise IntegrityError("Development 資料 digest 漂移")
            dates = [row["Date"] for row in csv.DictReader(io.StringIO(data.decode()))]
            controls = inputs.get("date_controls", {})
            intervals = [
                part
                for part in service.rules.workflow["data_intervals"]["intervals"]
                if part["role"] in {"warmup-only", "development"}
            ]
            start = controls.get("warmup_start", min(part["start_date"] for part in intervals))
            end = controls.get("signal_end", max(part["end_date"] for part in intervals))
            if any(
                not any(part["start_date"] <= day <= part["end_date"] for part in intervals)
                for day in dates
            ):
                raise ValidationError("Development 不接受 quarantine／Evaluation 或其他區間資料")
            if not dates or any(day < start or day > end or day >= "2020-01-01" for day in dates):
                raise ValidationError(
                    "Development 輸入超出 frozen 日期範圍，不能包含 Evaluation rows"
                )
            bound_data = inputs.get("data_bindings", {}).get("development_digest")
            if bound_data is not None and bound_data != plan["data_digest"]:
                raise IntegrityError("資料與 frozen trial inputs 不一致")
            for relative, source in files.items():
                atomic_create(workspace / relative, source.read_bytes())
            staged_package = workspace / "workflow"
            if not staged_package.exists():
                shutil.copytree(
                    service.workflow_root,
                    staged_package,
                    ignore=shutil.ignore_patterns(
                        "studies",
                        "__pycache__",
                        "release-manifest.yml",
                        "release-test-report.yml",
                        "release.yml",
                    ),
                )
            run = workspace / "run"
            atomic_create(run / "bars.csv", data)
            request = {
                "stage": "development",
                "data_path": "run/bars.csv",
                "data_digest": plan["data_digest"],
                "preregistration": state.preregistration,
                "trial_inputs": inputs,
                "source_bundle": bundle,
            }
            atomic_create(run / "request.yml", canonical_bytes(request))
            runner = load_canonical(workspace / f"research/{study_id}/runner-contract.yml")[
                "runners"
            ]["development"]
            atomic_create(
                directory / "started.yml",
                canonical_bytes({"request_digest": canonical_digest(request), "runner": runner}),
            )
            launch(workspace, staged_package, runner, run / "request.yml", output)
        payload = consume(
            service,
            study_id,
            load_canonical(output),
            inputs,
            state.preregistration,
            state.bindings["source_bundle_digest"],
        )
        atomic_create(directory / "published-payload.yml", canonical_bytes(payload))
        service.append_event(study_id, "trial-recorded", plan["actor"], payload)
        atomic_create(
            directory / "completed.yml", canonical_bytes({"operation_id": directory.name})
        )
        state = projection(service, study_id)
        return {
            "status": "completed",
            "operation_id": directory.name,
            "assessment": state.trial_assessments[trial],
        }


def freeze_steps(service, study_id, plan):
    service.rules.schema_store.validate("freeze-plan.schema.yml", plan)
    state = projection(service, study_id)
    ids = ordered_eligible(state)
    if not ids:
        raise ValidationError("沒有可凍結候選；績效失敗仍是有效 evidence")
    actor = plan["actor"]
    selected = ids[0]
    registry = {
        "maximum_trials": state.preregistration["maximum_trials"],
        "recorded_trial_count": len(state.trials),
        "complete_family_trial_ids": sorted(state.trials),
        "trial_registry_digest": canonical_digest(
            {"trials": [state.trials[key] for key in sorted(state.trials)]}
        ),
        "candidate_available": True,
    }
    prov = plan["provenance"]
    if not prov.get("sources") or prov.get("status") != "verified-clean":
        raise ValidationError("freeze 需要實際 verified-clean provenance；不能自動推定")
    pp, pd = service.publish_artifact(study_id, "evidence/provenance.yml", prov)
    provenance = {"status": prov["status"], "artifact_path": pp, "artifact_digest": pd}
    selection = {
        "schema_version": 1,
        "ordered_eligible_trial_ids": ids,
        "selected_candidate_id": selected,
        "rule_digest": canonical_digest(
            {
                key: state.preregistration[key]
                for key in ("eligibility_rules", "selection_rule", "tie_handling")
            }
        ),
    }
    sp, sd = service.publish_artifact(study_id, "evidence/selection.yml", selection)
    snapshot = plan["snapshot_set"]
    snap_path, snap_digest = service.publish_artifact(
        study_id, "manifests/snapshot-set.yml", snapshot
    )
    # Snapshot metadata 與 session inventory 可檢查，但不讀 Evaluation 價格或結果。
    from validator.artifacts import validate_snapshot_set

    snapshots = validate_snapshot_set(snapshot, service.rules.workflow, service.rules.schema_store)
    report = load_canonical(service.study_root(study_id) / state.identity["prepare_report_path"])
    baseline = state.preregistration["baseline_definition"]
    candidate = {
        "selected_candidate_id": selected,
        "baseline_id": baseline["baseline_id"],
        "baseline_family": baseline["family"],
        "baseline_objectively_simpler": True,
        "candidate_digest": report["binding"]["settings"]["candidate-definition.yml"],
        "qualification_spec_digest": report["binding"]["settings"]["qualification-spec.yml"],
        "trial_registry_digest": registry["trial_registry_digest"],
        "development_evidence_digest": state.trials[selected]["development_evidence_digest"],
        "evaluation_snapshot_digest": snapshots["historical-evaluation"]["data_digest"],
        "fold_inventory_digest": canonical_digest(
            {"sessions": snapshots["historical-evaluation"]["sessions"]}
        ),
        "snapshot_set_path": snap_path,
        "snapshot_set_digest": snap_digest,
        "selection_evidence_path": sp,
        "selection_evidence_digest": sd,
    }
    return [
        ("trial-registry-frozen", actor, registry),
        ("provenance-audited", actor, provenance),
        ("candidate-frozen", actor, candidate),
    ]


def complete_steps(service, study_id, stages, timestamp):
    for kind, actor, payload in stages:
        state = projection(service, study_id)
        existing = [r.value for r in state.events if r.value["event_type"] == kind]
        if existing:
            if (
                len(existing) != 1
                or existing[0]["actor_id"] != actor
                or existing[0]["payload"] != payload
            ):
                raise IntegrityError("既有 Event 與原 operation 不一致")
            continue
        service.append_event(study_id, kind, actor, payload, occurred_at=timestamp)


def freeze_readiness(service, study_id, plan):
    service.require_context(study_id, plan["actor"])
    from validator.assignments import reject_legacy

    reject_legacy(plan)
    with tempfile.TemporaryDirectory(prefix="freeze-readiness-") as temp:
        package = Path(temp) / "workflow"
        shutil.copytree(
            service.workflow_root, package, ignore=shutil.ignore_patterns("studies", "__pycache__")
        )
        shutil.copytree(service.study_root(study_id), package / "studies" / study_id, symlinks=True)
        authority = Path(temp) / "authority"
        shutil.copytree(service.authority.root / study_id, authority / study_id)
        staged = StudyService(
            package,
            authority,
            repository_root=service.repository_root,
            allow_draft=service.allow_draft,
            actor=service.actor,
            role=service.role,
            assignment=service.assignment,
        )
        stages = freeze_steps(staged, study_id, plan)
        complete_steps(staged, study_id, stages, "2000-01-01T00:00:00.000000Z")
        staged.validate(study_id)
    return {"status": "passed", "candidate_freeze_written": False}


def freeze(service, study_id, plan):
    with StudyLock(service.study_root(study_id) / ".writer.lock"):
        service.recover(study_id)
        directory = _operation_directory(service, study_id, "freeze", plan)
        if (directory / "completed.yml").exists():
            projection(service, study_id)
            return {"status": "completed", "operation_id": directory.name}
        freeze_readiness(service, study_id, plan)
        remember(service, study_id, "freeze", plan)
        stages = freeze_steps(service, study_id, plan)
        timefile = directory / "timestamp.yml"
        if not timefile.exists():
            atomic_create(
                timefile,
                canonical_bytes({"value": datetime.now(UTC).isoformat().replace("+00:00", "Z")}),
            )
        complete_steps(service, study_id, stages, load_canonical(timefile)["value"])
        atomic_create(
            directory / "completed.yml", canonical_bytes({"operation_id": directory.name})
        )
        return {"status": "completed", "operation_id": directory.name}


def terminate(service, study_id, plan):
    with StudyLock(service.study_root(study_id) / ".writer.lock"):
        service.recover(study_id)
        state = projection(service, study_id)
        expected = (
            state.terminal_outcome
            or state.pending_terminal_outcome
            or ("fail" if plan.get("reason_kind") == "no-eligible-candidate" else "indeterminate")
        )
        template = dict(plan["terminal_evidence"], bindings={})
        service.rules.schema_store.validate("terminal-evidence.schema.yml", template)
        if template["outcome"] != expected or template["authority"] != (
            "retrospectively-supported" if expected == "pass" else "none"
        ):
            raise ValidationError("Terminal plan 必須符合已知 disposition")
        directory = remember(service, study_id, "terminate", plan)
        if (directory / "completed.yml").exists():
            return {"status": "completed", "operation_id": directory.name}
        if state.terminal_outcome is not None:
            event = state.events[-1].value
            if event["event_type"] != "study-terminal" or event["actor_id"] != plan["actor"]:
                raise IntegrityError("Terminal 不屬於原 operation")
            atomic_create(
                directory / "completed.yml", canonical_bytes({"operation_id": directory.name})
            )
            return {"status": "completed", "operation_id": directory.name}
        if (
            state.pending_terminal_outcome is None
            and plan.get("reason_kind") == "no-eligible-candidate"
        ):
            registry = {
                "maximum_trials": state.preregistration["maximum_trials"],
                "recorded_trial_count": len(state.trials),
                "complete_family_trial_ids": sorted(state.trials),
                "trial_registry_digest": canonical_digest(
                    {"trials": [state.trials[key] for key in sorted(state.trials)]}
                ),
                "candidate_available": False,
            }
            service.append_event(study_id, "trial-registry-frozen", plan["actor"], registry)
            state = projection(service, study_id)
        if state.pending_terminal_outcome is None:
            payload = plan["evidence_unavailable"]
            service.append_event(study_id, "evidence-unavailable", plan["actor"], payload)
            state = projection(service, study_id)
        terminal = dict(plan["terminal_evidence"], bindings=_expected_terminal_bindings(state))
        path, digest = service.publish_artifact(study_id, "evidence/terminal.yml", terminal)
        if state.terminal_outcome is None:
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
        atomic_create(
            directory / "completed.yml", canonical_bytes({"operation_id": directory.name})
        )
        return {"status": "completed", "operation_id": directory.name}


def resume(service, study_id):
    with StudyLock(service.study_root(study_id) / ".writer.lock"):
        service.recover(study_id)
        root = service.study_root(study_id)
        from operations.service import create

        continuous = root / "manifests/continuous-plan.yml"
        if service.role == "study 開發者" and continuous.exists():
            from operations.continuous import develop_to_freeze

            return develop_to_freeze(service, study_id, load_canonical(continuous)["plan"])

        create_plan = root / "manifests/create-plan.yml"
        if create_plan.exists() and len(load_event_records(root, service.rules)) < 3:
            create(
                service,
                load_canonical(create_plan),
                load_canonical(root / "manifests/prepare-report.yml"),
            )
        from operations.evaluation import historical_evaluation

        results = []
        for path in sorted((root / "operations").glob("*/plan.yml")):
            if (path.parent / "completed.yml").exists():
                continue
            operation = load_canonical(path)
            if operation["authority_root"] != str(service.authority.root):
                raise IntegrityError("恢復不能更換 authority root")
            results.append(
                {
                    "development": development,
                    "freeze": freeze,
                    "terminate": terminate,
                    "historical-evaluation": historical_evaluation,
                }[operation["kind"]](service, study_id, operation["plan"])
            )
        return {"status": "completed", "resumed": results}
