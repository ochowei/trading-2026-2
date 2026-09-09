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


def repository_root(explicit: Path | None = None) -> Path:
    if explicit is not None:
        root = explicit.expanduser().resolve()
        workflow = root / "workflows" / WORKFLOW_DIRECTORY
        if not workflow.is_dir():
            raise RuntimeError("指定的 repository root 找不到唯一允許的 v001 workflow")
        return root
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
    parser.add_argument(
        "--repository-root",
        type=Path,
        help="synthetic fixture 使用的 repository root；省略時由本 script 自動尋找",
    )
    parser.add_argument(
        "--formal-evaluation-exposed",
        action="store_true",
        help="呼叫方明確確認正式 Historical Evaluation 結果已曝光",
    )
    parser.add_argument(
        "--outcome-bearing-terminal-exposed",
        action="store_true",
        help="呼叫方明確確認帶有結果的 Terminal 內容已曝光",
    )
    parser.add_argument(
        "--outcome-exposed",
        action="store_true",
        help="--formal-evaluation-exposed 與 --outcome-bearing-terminal-exposed 的簡寫",
    )
    args = parser.parse_args()

    try:
        root = repository_root(args.repository_root)
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
    )
    missing = [path.relative_to(study).as_posix() for path in required if not path.is_file()]
    if missing:
        return reject("缺少封存式檢討必要檔案：" + ", ".join(missing))

    exposure_reasons = []
    if args.formal_evaluation_exposed or args.outcome_exposed:
        exposure_reasons.append("正式 Historical Evaluation 結果已曝光")
    if args.outcome_bearing_terminal_exposed or args.outcome_exposed:
        exposure_reasons.append("帶有結果的 Terminal 內容已曝光")
    development_evidence = study / "evidence" / "development.yml"
    if exposure_reasons:
        print(
            json.dumps(
                {
                    "blind_review_eligible": False,
                    "blind_review_status": "blocked-by-exposed-outcome",
                    "development_evidence_status": (
                        "available" if development_evidence.is_file() else "unavailable"
                    ),
                    "development_evidence_validity": (
                        "not-validated" if development_evidence.is_file() else "unavailable"
                    ),
                    "historical_evaluation_status": "not_inspected",
                    "study_terminal_status": "not_inspected",
                    "blind_review_eligibility_basis": "explicit-outcome-exposure-only",
                    "reason": "；".join(exposure_reasons),
                    "status": "rejected",
                    "study_id": study.name,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2

    development_status = "available" if development_evidence.is_file() else "unavailable"
    review_status = (
        "eligible" if development_status == "available" else "eligible-with-development-evidence-unavailable"
    )

    print(
        json.dumps(
            {
                "blind_review_eligible": True,
                "blind_review_status": review_status,
                "blind_review_eligibility_rule": (
                    "只在正式 Evaluation 或帶有結果的 Terminal 內容明確曝光時停止；"
                    "不由 historical evaluation status 或 Study terminal status 推導"
                ),
                "development_evidence_status": development_status,
                "development_evidence_validity": (
                    "not-validated" if development_status == "available" else "unavailable"
                ),
                "historical_evaluation_status": "not_inspected",
                "study_terminal_status": "not_inspected",
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
