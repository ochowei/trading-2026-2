"""v002 日常操作入口；預設拒絕未啟用 package 的正式寫入。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))

from validator.canonical_yaml import load_canonical  # noqa: E402
from writer.service import StudyService  # noqa: E402

from operations.preflight import runner_preflight, save_report  # noqa: E402
from operations.service import create_authorize, freeze_readiness, prepare  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="v002 建立與凍結前操作")
    parser.add_argument("--repository-root", type=Path, default=PACKAGE.parents[1])
    parser.add_argument("--authority-root", type=Path, required=True)
    parser.add_argument("--allow-draft", action="store_true", help="只供隔離 fixture 測試")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "runner-preflight"):
        command = commands.add_parser(name)
        command.add_argument("study_id")
        command.add_argument("--report", type=Path, required=True)
    command = commands.add_parser("create-authorize")
    command.add_argument("--plan", type=Path, required=True)
    command.add_argument("--report", type=Path, required=True)
    command = commands.add_parser("freeze-readiness")
    command.add_argument("study_id")
    command.add_argument("--payload", type=Path, required=True)
    command.add_argument("--actor", required=True)
    args = parser.parse_args()
    service = None
    plan = None
    try:
        if args.command == "prepare":
            result = prepare(args.repository_root.resolve(), args.study_id,
                             args.authority_root, args.report)
        elif args.command == "runner-preflight":
            result = runner_preflight(args.repository_root.resolve(), args.study_id,
                                      args.authority_root)
            save_report(args.report, result)
        else:
            service = StudyService(PACKAGE, args.authority_root,
                repository_root=args.repository_root, allow_draft=args.allow_draft)
            if args.command == "create-authorize":
                plan = load_canonical(args.plan)
                result = create_authorize(service, plan, load_canonical(args.report))
            else:
                result = freeze_readiness(service, args.study_id, load_canonical(args.payload), args.actor)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except Exception as error:
        progress = None
        if service is not None and isinstance(plan, dict):
            try:
                root = service.study_root(plan["study_id"])
                progress = {"published_events": sorted(p.name for p in (root / "events").glob("*.yml")),
                            "pending_journals": sorted(p.name for p in (root / "journals").glob("*.prepared.yml")
                                if not p.with_name(p.name.replace(".prepared.yml", ".completed.yml")).exists())}
            except Exception:
                progress = None
        print(json.dumps({"status": "failed", "command": args.command,
                          "error": str(error), "progress": progress, "recovery": "批次失敗後使用相同 plan 與 report 重試；不得重建或換 inputs"}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
