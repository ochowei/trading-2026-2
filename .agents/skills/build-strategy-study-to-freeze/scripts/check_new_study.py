#!/usr/bin/env python3
"""在寫入前確認 Study ID 安全、唯一且使用同名 research 目錄。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

STUDY_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,62}$")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("study_id")
    parser.add_argument("--repository-root", type=Path, default=repository_root())
    args = parser.parse_args()

    root = args.repository_root.resolve()
    workflow = root / "workflows" / "strategy-forward-replication-research--v001"
    result: dict[str, object] = {
        "status": "rejected",
        "study_id": args.study_id,
        "workflow": "strategy-forward-replication-research--v001",
    }
    if not STUDY_ID.fullmatch(args.study_id):
        result["reason"] = "study_id 只允許 3--63 個小寫英數字與連字號"
    elif not (workflow / "release.yml").is_file():
        result["reason"] = "找不到已 release 的 v001 workflow"
    else:
        study = workflow / "studies" / args.study_id
        research = root / "research" / args.study_id
        if study.exists():
            result["reason"] = "Study 已存在，不得覆寫或冒充新 Study"
        elif research.exists():
            result["reason"] = "同名 research 目錄已存在，需先釐清其歸屬"
        else:
            result.update(
                {
                    "status": "eligible",
                    "study_root": str(study),
                    "research_root": str(research),
                }
            )
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 0

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
