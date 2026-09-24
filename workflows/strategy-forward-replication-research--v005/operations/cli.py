"""v005 明確派工入口；JSON 回傳實際缺件、範圍與恢復資訊。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
from validator.assignments import DEVELOPER, EVALUATOR, AssignmentError, safe_path  # noqa: E402
from validator.canonical_yaml import load_canonical  # noqa: E402
from writer.service import StudyService  # noqa: E402

from operations import lifecycle  # noqa: E402
from operations.preflight import runner_preflight, save_report  # noqa: E402
from operations.service import create, prepare  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="v005 明確派工 Study 操作")
    parser.add_argument("--repository-root", type=Path, default=PACKAGE.parents[1])
    parser.add_argument("--authority-root", type=Path)
    parser.add_argument("--allow-draft", action="store_true", help="只供隔離 fixture")
    parser.add_argument("--role", choices=[DEVELOPER, EVALUATOR], required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "runner-preflight"):
        command = commands.add_parser(name)
        command.add_argument("study_id")
        command.add_argument("--report", type=Path, required=True)
    command = commands.add_parser("create")
    command.add_argument("--plan", type=Path, required=True)
    command.add_argument("--report", type=Path, required=True)
    command.add_argument("--assignment", type=Path)
    for name in (
        "development",
        "freeze",
        "freeze-readiness",
        "terminate",
        "historical-evaluation",
        "develop-to-freeze",
    ):
        command = commands.add_parser(name)
        command.add_argument("study_id")
        command.add_argument("--plan", type=Path, required=True)
        command.add_argument("--assignment", type=Path)
    for name in ("status", "validate", "resume"):
        command = commands.add_parser(name)
        command.add_argument("study_id")
        command.add_argument("--assignment", type=Path)
    args = parser.parse_args()
    repository = args.repository_root.resolve()
    authority = (args.authority_root or repository / ".authority").resolve()
    study_id = getattr(args, "study_id", None)
    context = {
        "schema_version": 1,
        "workflow_version": "v005",
        "authority_root": str(authority),
        "command": args.command,
        "study_id": study_id,
    }
    try:
        safe_path(repository, repository, args.role)
        safe_path(authority, repository, args.role)
        if args.role == EVALUATOR and args.command not in {
            "status",
            "validate",
            "resume",
            "historical-evaluation",
        }:
            raise AssignmentError("role-mismatch", "評估角色不得建立或開發 Study")
        if args.role != EVALUATOR and args.command == "historical-evaluation":
            raise AssignmentError("role-mismatch", "Historical Evaluation 限評估角色")
        # 在讀取任何使用者提供的檔案前，先檢查詞面及符號連結解析後的路徑。
        for name in ("plan", "report", "assignment"):
            path = getattr(args, name, None)
            if path is not None:
                safe_path(path, repository, args.role)
        if args.command in {"prepare", "runner-preflight"}:
            if args.command == "prepare":
                result = prepare(repository, study_id, authority, args.report)
            else:
                result = runner_preflight(repository, study_id, authority)
                save_report(args.report, result)
        else:
            assignment_path = getattr(args, "assignment", None)
            if assignment_path is None and args.command not in {"status", "validate"}:
                raise AssignmentError("assignment-missing", "寫入或恢復需要既有明確派工紀錄")
            assignment = load_canonical(assignment_path) if assignment_path else None
            service = StudyService(
                PACKAGE,
                authority,
                repository_root=repository,
                allow_draft=args.allow_draft,
                role=args.role,
                actor=assignment["assignee"] if assignment else None,
                assignment=assignment,
            )
            plan = load_canonical(args.plan) if hasattr(args, "plan") else None
            if args.command == "create":
                context["study_id"] = study_id = plan["study_id"]
            if args.command not in {"status", "validate"}:
                service.require_context(study_id)
            report_file = service.study_root(study_id) / "manifests/prepare-report.yml"
            safe_path(report_file, repository, args.role)
            if report_file.exists() and load_canonical(report_file)["binding"][
                "authority_root"
            ] != str(authority):
                raise AssignmentError("binding-mismatch", "不得更換既有 Study 的 authority root")
            if args.command == "create":
                result = create(service, plan, load_canonical(args.report))
            elif args.command == "develop-to-freeze":
                from operations.continuous import develop_to_freeze

                result = develop_to_freeze(service, study_id, plan)
            elif args.command in {"status", "validate"}:
                result = lifecycle.status(service, study_id, role=args.role)
            elif args.command == "resume":
                result = lifecycle.resume(service, study_id)
            elif args.command == "historical-evaluation":
                from operations.evaluation import historical_evaluation

                result = historical_evaluation(service, study_id, plan)
            else:
                lifecycle.assert_development_scope(service, study_id)
                result = getattr(lifecycle, args.command.replace("-", "_"))(service, study_id, plan)
        print(
            json.dumps(
                {**context, "status": "completed", "result": result},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except Exception as error:
        code = getattr(
            error,
            "code",
            {
                "IntegrityError": "binding-mismatch",
                "ValidationError": "qualification-failed",
                "TransitionError": "qualification-failed",
                "FileNotFoundError": "missing-inputs",
            }.get(type(error).__name__, "recovery-required"),
        )
        progress = {"published_events": [], "pending_journals": [], "operation_id": None}
        try:
            root = service.study_root(study_id)
            for name in ("events", "journals", "operations"):
                safe_path(root / name, repository, args.role)
            progress["published_events"] = sorted(
                path.name for path in (root / "events").glob("*.yml")
            )
            progress["pending_journals"] = sorted(
                path.name
                for path in (root / "journals").glob("*.prepared.yml")
                if not path.with_name(path.name.replace(".prepared.yml", ".completed.yml")).exists()
            )
            pending = (
                sorted(
                    path.name
                    for path in (root / "operations").iterdir()
                    if path.is_dir() and not (path / "completed.yml").exists()
                )
                if (root / "operations").exists()
                else []
            )
            progress["operation_id"] = pending[0] if len(pending) == 1 else None
        except Exception:
            pass
        # 不回傳不可信路徑、例外內容或 artifact 值，避免錯誤訊息洩漏受限資料。
        print(
            json.dumps(
                {
                    **context,
                    "status": "failed",
                    "error": {
                        "code": code,
                        "message": "操作未完成，請核對派工、固定輸入與原 operation",
                    },
                    "progress": progress,
                    "missing_inputs": ["assignment"] if code == "assignment-missing" else [],
                    "scope_boundary": args.role,
                    "next_action": "resume_same_operation"
                    if code == "recovery-required"
                    else "inspect_inputs",
                },
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
