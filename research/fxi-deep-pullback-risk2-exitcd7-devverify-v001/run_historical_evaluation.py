"""產生 frozen FXI Historical Evaluation raw evidence，但不發布 Study Event。

正式用法：
python run_historical_evaluation.py \
  --evaluation <frozen-2020-2024.csv> \
  --candidate-definition <candidate-definition.yml> \
  --preregistration <preregistration.yml> \
  --qualification-spec <qualification-spec.yml> \
  --snapshot-set <data-snapshot-set.yml> \
  --source-bundle <source-bundle.yml> \
  --output <new-nonexistent-output.json>

本 runner 只接受不可覆寫的 output path；Study 建立階段只能用合成資料測試，
不得對正式 Evaluation snapshot 執行。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml

from trading_2026_2.fxi_risk2_seedfix import historical_evidence


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="產生 FXI 2020--2024 frozen raw evidence")
    result.add_argument("--evaluation", type=Path, required=True)
    result.add_argument("--candidate-definition", type=Path, required=True)
    result.add_argument("--preregistration", type=Path, required=True)
    result.add_argument("--qualification-spec", type=Path, required=True)
    result.add_argument("--snapshot-set", type=Path, required=True)
    result.add_argument("--source-bundle", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"預期 YAML mapping: {path}")
    return value


def validate_frozen_inputs(args: argparse.Namespace) -> tuple[dict, dict]:
    candidate = load(args.candidate_definition)
    preregistration = load(args.preregistration)
    qualification = load(args.qualification_spec)
    snapshot_set = load(args.snapshot_set)
    source_bundle = load(args.source_bundle)
    if candidate["candidate_id"] != preregistration["selection_rule"]["selected_candidate_id"]:
        raise RuntimeError("Candidate identity 與 preregistration 不一致")
    if qualification["development"] != preregistration["eligibility_rules"][
        "development_gates"
    ]:
        raise RuntimeError("Development gates 不是單一來源")
    if qualification["evaluation"] != preregistration["evaluation_gates"]:
        raise RuntimeError("Evaluation gates 不是單一來源")
    if qualification["replay"] != preregistration["replay_gates"]:
        raise RuntimeError("Replay gates 不是單一來源")
    evaluation_snapshot = next(
        item for item in snapshot_set["snapshots"] if item["role"] == "historical-evaluation"
    )
    if digest(args.evaluation) != evaluation_snapshot["data_digest"]:
        raise RuntimeError("Evaluation snapshot digest 與 frozen snapshot set 不一致")
    repository_root = Path(__file__).resolve().parents[2]
    for item in source_bundle["files"]:
        path = (repository_root / item["path"]).resolve()
        if repository_root not in path.parents or not path.is_file():
            raise RuntimeError(f"Source Bundle 路徑無效: {item['path']}")
        if digest(path) != item["digest"]:
            raise RuntimeError(f"Source Bundle digest drift: {item['path']}")
    return preregistration, qualification


def main() -> int:
    args = parser().parse_args()
    if args.output.exists():
        raise RuntimeError("拒絕覆寫既有 Historical Evaluation output")
    preregistration, _qualification = validate_frozen_inputs(args)
    bars = pd.read_csv(args.evaluation, parse_dates=["Date"], index_col="Date")
    confidence = preregistration["evaluation_gates"]["family_wise_confidence"]["value"]
    evidence = historical_evidence(bars, family_wise_confidence=confidence)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
