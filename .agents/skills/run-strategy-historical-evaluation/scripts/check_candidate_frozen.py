#!/usr/bin/env python3
"""確認指定 Study 恰停在 candidate-frozen 且有 frozen Evaluation runner。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def reject(study_id: str, reason: str) -> int:
    print(
        json.dumps(
            {"status": "rejected", "study_id": study_id, "reason": reason},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 2


def source_files(source_bundle: Path) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    digest: str | None = None
    for raw_line in source_bundle.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- digest:"):
            digest = line.split(":", 1)[1].strip()
        elif line.startswith("digest:"):
            digest = line.split(":", 1)[1].strip()
        elif line.startswith("path:") and digest:
            result.append((line.split(":", 1)[1].strip(), digest))
            digest = None
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("study")
    parser.add_argument("--repository-root", type=Path, default=repository_root())
    args = parser.parse_args()

    root = args.repository_root.resolve()
    studies = root / "workflows" / "strategy-forward-replication-research--v001" / "studies"
    candidate = Path(args.study)
    if "/" not in args.study and "\\" not in args.study:
        candidate = studies / args.study
    elif not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    study_id = resolved.name
    if resolved.parent != studies.resolve() or not resolved.is_dir():
        return reject(study_id, "只接受 v001 studies 下的直接 Study 目錄")

    events = sorted((resolved / "events").glob("*.yml"))
    if len(events) != 7 or events[-1].name != "000007-candidate-frozen.yml":
        return reject(study_id, "Study 必須恰停在 000007-candidate-frozen，且不得已有正式結果事件")

    source_bundle = resolved / "manifests" / "source-bundle.yml"
    required = [
        source_bundle,
        resolved / "manifests" / "preregistration.yml",
        resolved / "manifests" / "candidate-definition.yml",
        resolved / "manifests" / "qualification-spec.yml",
        resolved / "manifests" / "data-snapshot-set.yml",
    ]
    if not all(path.is_file() for path in required):
        return reject(study_id, "缺少 candidate freeze 所需 manifest")

    runners: list[str] = []
    for relative, expected_digest in source_files(source_bundle):
        source = (root / relative).resolve()
        try:
            source.relative_to(root)
        except ValueError:
            return reject(study_id, f"Source Bundle 路徑逃出 repository: {relative}")
        if not source.is_file():
            return reject(study_id, f"Source Bundle 檔案不存在: {relative}")
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != expected_digest:
            return reject(study_id, f"Source Bundle digest 不一致: {relative}")
        if source.name == "run_historical_evaluation.py":
            runners.append(relative)

    if len(runners) > 1:
        return reject(study_id, "Source Bundle 不得同時凍結多個 run_historical_evaluation.py")

    runner = runners[0] if runners else None
    runner_status = "frozen" if runner else "adapter-required"

    print(
        json.dumps(
            {
                "status": "eligible",
                "study_id": study_id,
                "study_root": str(resolved),
                "evaluation_runner": runner,
                "runner_status": runner_status,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
