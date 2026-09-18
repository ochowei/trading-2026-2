"""v002 日常入口；JSON 回應不把研究失敗當成 runner 故障。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
from validator.canonical_yaml import load_canonical  # noqa: E402
from writer.service import StudyService  # noqa: E402

from operations import lifecycle  # noqa: E402
from operations.preflight import runner_preflight, save_report  # noqa: E402
from operations.service import create_authorize, prepare  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="v002 Study 日常操作")
    parser.add_argument("--repository-root", type=Path, default=PACKAGE.parents[1])
    parser.add_argument("--authority-root", type=Path)
    parser.add_argument("--allow-draft", action="store_true", help="只供隔離 fixture")
    parser.add_argument(
        "--role", choices=["study 開發者", "Study 歷史評估執行者"], default="study 開發者"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "runner-preflight"):
        command = commands.add_parser(name)
        command.add_argument("study_id")
        command.add_argument("--report", type=Path, required=True)
    command = commands.add_parser("create-authorize")
    command.add_argument("--plan", type=Path, required=True)
    command.add_argument("--report", type=Path, required=True)
    for name in ("development", "freeze", "freeze-readiness", "terminate", "historical-evaluation"):
        command = commands.add_parser(name)
        command.add_argument("study_id")
        command.add_argument("--plan", type=Path, required=True)
    for name in ("status", "validate", "resume"):
        command = commands.add_parser(name)
        command.add_argument("study_id")
    args = parser.parse_args()
    repository = args.repository_root.resolve()
    authority = (args.authority_root or repository / ".authority").resolve()
    study_id = getattr(args, "study_id", None)
    context = {
        "schema_version": 1,
        "workflow_version": "v002",
        "authority_root": str(authority),
        "command": args.command,
        "study_id": study_id,
    }
    try:
        if args.role == "Study 歷史評估執行者" and args.command not in {
            "status",
            "validate",
            "resume",
            "historical-evaluation",
        }:
            raise ValueError("Evaluation 角色不得建立或開發 Study")
        if args.command in {"prepare", "runner-preflight"}:
            if args.command == "prepare":
                result = prepare(repository, study_id, authority, args.report)
            else:
                result = runner_preflight(repository, study_id, authority)
                save_report(args.report, result)
        else:
            service = StudyService(
                PACKAGE, authority, repository_root=repository, allow_draft=args.allow_draft
            )
            if study_id is not None:
                report_file = service.study_root(study_id) / "manifests/prepare-report.yml"
                if report_file.exists() and load_canonical(report_file)["binding"][
                    "authority_root"
                ] != str(authority):
                    raise ValueError("不得更換既有 Study 的 authority root")
            if args.command == "create-authorize":
                plan = load_canonical(args.plan)
                context["study_id"] = study_id = plan["study_id"]
                result = create_authorize(service, plan, load_canonical(args.report))
            elif args.command in {"status", "validate"}:
                result = lifecycle.status(service, study_id, role=args.role)
            elif args.command == "resume":
                if args.role == "study 開發者":
                    lifecycle.assert_development_scope(service, study_id)
                result = lifecycle.resume(service, study_id)
            elif args.command == "historical-evaluation":
                if args.role != "Study 歷史評估執行者":
                    raise ValueError("Historical Evaluation 限獨立評估角色與明確授權")
                from operations.evaluation import historical_evaluation

                result = historical_evaluation(service, study_id, load_canonical(args.plan))
            else:
                if args.role != "study 開發者":
                    raise ValueError("此入口限 study 開發者；Evaluation 必須使用獨立角色與程序")
                lifecycle.assert_development_scope(service, study_id)
                result = getattr(lifecycle, args.command.replace("-", "_"))(
                    service, study_id, load_canonical(args.plan)
                )
        print(
            json.dumps(
                {**context, "status": "completed", "result": result},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except Exception as error:
        root = PACKAGE / "studies" / str(study_id)
        progress = {
            "published_events": sorted(p.name for p in (root / "events").glob("*.yml")),
            "pending_journals": sorted(
                p.name
                for p in (root / "journals").glob("*.prepared.yml")
                if not p.with_name(p.name.replace(".prepared.yml", ".completed.yml")).exists()
            ),
        }
        print(
            json.dumps(
                {
                    **context,
                    "status": "failed",
                    "error": {
                        "code": {
                            "IntegrityError": "integrity-error",
                            "ValidationError": "validation-error",
                            "TransitionError": "transition-error",
                            "EvidenceUnavailable": "evidence-unavailable",
                            "ValueError": "invalid-operation",
                        }.get(type(error).__name__, "operation-error"),
                        "message": str(error),
                        "path": getattr(error, "path", None) or str(root),
                        "expected": getattr(error, "expected", None),
                        "actual": getattr(error, "actual", None),
                    },
                    "progress": progress,
                    "next_action": "inspect_then_resume_same_operation",
                    "required_approval": None,
                },
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
