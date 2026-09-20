"""唯一評估 reservation 的可重建綁定。"""

from .canonical_yaml import canonical_digest, load_canonical
from .errors import IntegrityError
from .paths import resolve_inside


def verify_reservation(root, state, event, rules):
    from .assignments import reject_legacy

    reservation = load_canonical(resolve_inside(root, "manifests/evaluation-operation.yml"))
    operation = reservation["operation_id"]
    plan = load_canonical(resolve_inside(root, f"operations/{operation}/plan.yml"))
    report = load_canonical(resolve_inside(root, state.identity["prepare_report_path"]))
    reject_legacy(plan)
    expected = {
        "operation_id": operation,
        "assignment_digest": event["execution"]["assignment_digest"],
        "workflow_digest": state.bindings["workflow_digest"],
        "study_id": state.study_id,
        "authority_root": report["binding"]["authority_root"],
        "source_bundle_digest": state.bindings["source_bundle_digest"],
        "preregistration_digest": state.preregistration_digest,
        "candidate_freeze_digest": state.evidence["candidate-freeze"],
        "data_digest": state.candidate["evaluation_snapshot_digest"],
        "runner_digest": report["binding"]["settings"]["runner-contract.yml"],
        "plan_digest": canonical_digest(plan["plan"]),
    }
    if reservation != expected or event["payload"] != {
        "operation_id": operation,
        "reservation_digest": canonical_digest(reservation),
    }:
        raise IntegrityError("評估 reservation 與凍結內容不一致")
    identity = {
        "kind": "historical-evaluation",
        "plan": plan["plan"],
        "authority_root": expected["authority_root"],
    }
    if canonical_digest(identity) != operation or plan != identity:
        raise IntegrityError("評估 operation identity 不一致")
    if (
        plan["plan"]["data_digest"] != expected["data_digest"]
        or plan["plan"]["actor"] != event["actor_id"]
    ):
        raise IntegrityError("評估 plan 與啟動事件不一致")
    return reservation


def verify_completed(root, state, payload, rules):
    """completed 不能只用手填結果旁路 started 與原 runner 輸出。"""
    from .paths import resolve_historical_evaluation_artifact

    operation = state.evaluation_operation
    directory = resolve_inside(root, f"operations/{operation['operation_id']}")
    marker = load_canonical(resolve_inside(directory, "launch-marker.yml"))
    authority = load_canonical(
        resolve_inside(operation["authority_root"], f"{state.study_id}/evaluation-launch.yml")
    )
    if marker != authority or marker.get("operation_id") != operation["operation_id"]:
        raise IntegrityError("launch marker 與 authority 不一致")
    prefix = f"{rules.historical_evaluation_artifacts_path}/{state.study_id}/runtime/run"

    def artifact(name):
        return load_canonical(
            resolve_historical_evaluation_artifact(
                root,
                rules.repository_root,
                rules.historical_evaluation_artifacts_path,
                f"{prefix}/{name}",
            )
        )

    request = artifact("request.yml")
    if (
        marker["request_digest"] != canonical_digest(request)
        or request["data_digest"] != operation["data_digest"]
        or request["preregistration"] != state.preregistration
    ):
        raise IntegrityError("runner request 與啟動內容不一致")
    if payload["evidence_digest"] != canonical_digest(artifact("evidence.yml")):
        raise IntegrityError("completed 結果不是原 runner 輸出")
