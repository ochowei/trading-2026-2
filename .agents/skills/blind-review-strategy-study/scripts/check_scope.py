#!/usr/bin/env python3
"""驗證 blind-review-strategy-study 的目標是否位於唯一允許的 workflow。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WORKFLOW_DIRECTORY = "strategy-forward-replication-research--v001"
STUDY_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")


def repository_root() -> Path:
    start = Path(__file__).resolve()
    for candidate in start.parents:
        workflow = candidate / "workflows" / WORKFLOW_DIRECTORY
        if (candidate / "AGENTS.md").is_file() and workflow.is_dir():
            return candidate
    raise RuntimeError("找不到包含指定 v001 workflow 的 repository 根目錄")


def reject(reason: str) -> int:
    print(json.dumps({"reason": reason, "status": "rejected"}, ensure_ascii=False))
    return 2


def resolve_study(reference: str, root: Path, studies_root: Path) -> Path:
    if STUDY_ID_PATTERN.fullmatch(reference):
        return (studies_root / reference).resolve(strict=True)
    supplied = Path(reference)
    if not supplied.is_absolute():
        supplied = root / supplied
    return supplied.resolve(strict=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="確認指定目標是 strategy-forward-replication-research--v001 的 Study"
    )
    parser.add_argument("study", help="Study ID 或 Study 目錄")
    args = parser.parse_args()

    try:
        root = repository_root()
    except RuntimeError as exc:
        return reject(str(exc))

    studies_root = (root / "workflows" / WORKFLOW_DIRECTORY / "studies").resolve()
    try:
        study = resolve_study(args.study, root, studies_root)
    except FileNotFoundError:
        return reject("指定的 Study 不存在")
    except OSError as exc:
        return reject(f"無法解析指定路徑：{exc}")

    if not study.is_dir():
        return reject("目標必須是 Study 目錄，不能是單一檔案")
    if study.parent != studies_root:
        return reject("目標不是指定 v001 workflow 之 studies/ 的直接子目錄")
    if not STUDY_ID_PATTERN.fullmatch(study.name):
        return reject("Study ID 格式不合法")

    required = (
        study / "manifests" / "preregistration.yml",
        study / "manifests" / "candidate-definition.yml",
        study / "evidence" / "development.yml",
    )
    missing = [path.relative_to(study).as_posix() for path in required if not path.is_file()]
    if missing:
        return reject("缺少封存式檢討必要檔案：" + ", ".join(missing))

    print(
        json.dumps(
            {
                "status": "eligible",
                "study_id": study.name,
                "study_root": str(study),
                "workflow": "strategy-forward-replication-research",
                "workflow_root": str(studies_root.parent),
                "workflow_version": "v001",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
