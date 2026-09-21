"""派工只記錄已存在的指令，不宣稱驗證指派者身分。"""

from pathlib import Path

from .canonical_yaml import canonical_digest
from .errors import ValidationError
from .schema_validation import SchemaStore

DEVELOPER = "study 開發者"
EVALUATOR = "Study 歷史評估執行者"
SCOPES = {DEVELOPER: "development-to-freeze", EVALUATOR: "historical-evaluation-to-terminal"}
LEGACY = {
    "preregistration_actor",
    "preregistration_approval",
    "development_authorization",
    "authorization",
    "approval_path",
    "approval_digest",
    "authorization_path",
    "authorization_digest",
    "approved_by",
    "approved_at",
    "decision",
}


class AssignmentError(ValidationError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def reject_legacy(value):
    if isinstance(value, dict):
        if LEGACY.intersection(value):
            raise ValidationError("新版本拒絕 Study 核准欄位")
        for item in value.values():
            reject_legacy(item)
    elif isinstance(value, list):
        for item in value:
            reject_legacy(item)


def validate_assignment(value, study_id, actor, role):
    if value is None:
        raise AssignmentError("assignment-missing", "缺少既有明確派工紀錄")
    reject_legacy(value)
    if not isinstance(value, dict):
        raise AssignmentError("assignment-missing", "派工必須是完整紀錄")
    if role not in SCOPES or value.get("role") != role or value.get("assignee") != actor:
        raise AssignmentError("role-mismatch", "派工受派者／角色與執行者不一致")
    if (
        value.get("study_id") != study_id
        or value.get("workflow_version") != "v004"
        or value.get("scope") != SCOPES[role]
    ):
        raise AssignmentError("binding-mismatch", "派工未指定同一 Study、版本與工作範圍")
    SchemaStore(Path(__file__).resolve().parents[1] / "schemas").validate(
        "assignment.schema.yml", value
    )
    return canonical_digest(value)


def safe_path(path, repository, role):
    path = Path(path)
    restricted = {".super-admin", ".project-manager"}
    if role == DEVELOPER:
        restricted.add("historical-evaluation-artifacts")
    if restricted.intersection(path.parts) or restricted.intersection(path.resolve().parts):
        raise AssignmentError("scope-boundary", "輸入路徑超出角色範圍")
    return path


def validate_context(event, projection, rules, root):
    from .artifacts import verified_artifact

    context = event["execution"]
    _, assignment = verified_artifact(
        root,
        context["assignment_path"],
        context["assignment_digest"],
        repository_root=rules.repository_root,
        historical_evaluation_artifacts_path=rules.historical_evaluation_artifacts_path,
    )
    role = context["role"]
    validate_assignment(assignment, event["study_id"], event["actor_id"], role)
    evaluating = (
        event["event_type"].startswith("historical-evaluation-")
        or projection.evaluation_operation is not None
    )
    if role != (EVALUATOR if evaluating else DEVELOPER):
        raise AssignmentError("role-mismatch", "事件不在受派角色的執行範圍")
    if evaluating and event["actor_id"] != projection.identity["historical_evaluation_operator"]:
        raise AssignmentError("role-mismatch", "評估者不是 Study 指定的執行者")
    if (
        evaluating
        and projection.evaluation_operation
        and context["assignment_digest"] != projection.evaluation_operation["assignment_digest"]
    ):
        raise AssignmentError("binding-mismatch", "不能變更已啟動評估的派工")
    if (
        not evaluating
        and projection.development_assignment
        and context["assignment_digest"] != projection.development_assignment
    ):
        raise AssignmentError("binding-mismatch", "不能變更已登記的 Development 派工")
    if not evaluating:
        projection.development_assignment = context["assignment_digest"]
    reject_legacy(event["payload"])
