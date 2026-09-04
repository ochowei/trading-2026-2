"""Guarded writer 的簡單 CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKFLOW_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_PACKAGE_ROOT))

from validator.canonical_yaml import load_canonical  # noqa: E402
from validator.errors import (  # noqa: E402
    IntegrityError,
    TransitionError,
    ValidationError,
    WorkflowError,
)

from writer.service import StudyService  # noqa: E402


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="strategy-forward-replication-research v001")
    result.add_argument("--workflow-root", type=Path, default=WORKFLOW_PACKAGE_ROOT)
    result.add_argument("--authority-root", type=Path, required=True)
    result.add_argument("--allow-draft", action="store_true")
    commands = result.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create")
    create.add_argument("--study-id", required=True)
    create.add_argument("--actor", required=True)
    create.add_argument("--research-round", required=True)
    create.add_argument("--experiment-family", required=True)
    create.add_argument("--research-owner", required=True)
    create.add_argument("--replay-operator", required=True)
    create.add_argument("--source-bundle", type=Path, required=True)

    append = commands.add_parser("append")
    append.add_argument("--study-id", required=True)
    append.add_argument("--actor", required=True)
    append.add_argument("--event-type", required=True)
    append.add_argument("--payload", type=Path, required=True)

    publish = commands.add_parser("publish-artifact")
    publish.add_argument("--study-id", required=True)
    publish.add_argument("--path", required=True)
    publish.add_argument("--source", type=Path, required=True)

    validate = commands.add_parser("validate")
    validate.add_argument("--study-id", required=True)

    recover = commands.add_parser("recover")
    recover.add_argument("--study-id", required=True)
    return result


def _error_code(error: WorkflowError) -> str:
    if isinstance(error, IntegrityError):
        return "integrity-error"
    if isinstance(error, TransitionError):
        return "transition-error"
    if isinstance(error, ValidationError):
        return "validation-error"
    return "workflow-error"


def _error_payload(args: argparse.Namespace, error: WorkflowError) -> dict[str, object]:
    return {
        "command": args.command,
        "error": {
            "code": _error_code(error),
            "message": str(error),
            "type": type(error).__name__,
        },
        "status": "error",
        "study_id": getattr(args, "study_id", None),
    }


def main() -> int:
    args = parser().parse_args()
    try:
        service = StudyService(args.workflow_root, args.authority_root, allow_draft=args.allow_draft)
        if args.command == "create":
            digest = service.create_study(
                args.study_id,
                args.actor,
                research_round_id=args.research_round,
                experiment_family=args.experiment_family,
                research_owner=args.research_owner,
                replay_operator=args.replay_operator,
                source_bundle=load_canonical(args.source_bundle),
            )
            print(digest)
        elif args.command == "append":
            payload = load_canonical(args.payload)
            print(service.append_event(args.study_id, args.event_type, args.actor, payload))
        elif args.command == "publish-artifact":
            value = load_canonical(args.source)
            path, digest = service.publish_artifact(args.study_id, args.path, value)
            print(json.dumps({"path": path, "digest": digest}, sort_keys=True))
        elif args.command == "validate":
            print(json.dumps(service.validate(args.study_id), ensure_ascii=False, sort_keys=True))
        elif args.command == "recover":
            print(json.dumps(service.recover(args.study_id), sort_keys=True))
        return 0
    except WorkflowError as error:
        print(json.dumps(_error_payload(args, error), ensure_ascii=False, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
