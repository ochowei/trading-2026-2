"""TSM 動能趨勢 v001 的候選凍結後 Historical Evaluation runner。

本程式是 candidate freeze 後才可呼叫的凍結程序。它不在建立 Study、
Development 或盲檢討階段執行；本 TASK 只把程序與輸入綁入 Source Bundle，
不讀取、不產生、不發布正式 Historical Evaluation 結果。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from trading_2026_2 import tsm_momentum_trend_volume_lead_confirmation_v001 as strategy

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import (  # noqa: E402
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)

CANDIDATE_ID = "tsm-momentum-trend-volume-lead-confirmation-v001"
ENGINE_PATH = "src/trading_2026_2/tsm_momentum_trend_volume_lead_confirmation_v001.py"
RUNNER_PATH = "research/tsm-momentum-trend-volume-lead-confirmation--v001/run_historical_evaluation.py"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="候選凍結後產生 TSM 動能趨勢 Historical Evaluation raw evidence")
    result.add_argument("--evaluation", type=Path, required=True)
    result.add_argument("--candidate-definition", type=Path, required=True)
    result.add_argument("--preregistration", type=Path, required=True)
    result.add_argument("--qualification-spec", type=Path, required=True)
    result.add_argument("--snapshot-set", type=Path, required=True)
    result.add_argument("--source-bundle", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    return result


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(value: float) -> str:
    return str(float(value))


def source_bundle_entries(source_bundle: dict[str, Any]) -> dict[str, str]:
    return {item["path"]: item["digest"] for item in source_bundle["files"]}


def validate_frozen_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate = load_canonical(args.candidate_definition)
    preregistration = load_canonical(args.preregistration)
    qualification = load_canonical(args.qualification_spec)
    snapshot_set = load_canonical(args.snapshot_set)
    source_bundle = load_canonical(args.source_bundle)
    if candidate.get("candidate_id") != CANDIDATE_ID:
        raise RuntimeError("candidate-definition 不是已凍結的 candidate")
    if preregistration["complete_candidate_family"] != [CANDIDATE_ID]:
        raise RuntimeError("preregistration candidate family 不是單一凍結 candidate")
    if qualification.get("selected_candidate_id") != CANDIDATE_ID:
        raise RuntimeError("qualification 沒有選定本 candidate")
    if not isinstance(snapshot_set, dict) or "historical-evaluation" not in snapshot_set:
        raise RuntimeError("snapshot set 缺少 Historical Evaluation role metadata")
    if not isinstance(source_bundle, dict):
        raise RuntimeError("Source Bundle 必須是 mapping")
    entries = source_bundle_entries(source_bundle)
    if entries.get(ENGINE_PATH) != raw_digest(REPOSITORY_ROOT / ENGINE_PATH):
        raise RuntimeError("Source Bundle 的 strategy engine binding 不一致")
    if RUNNER_PATH not in entries or entries[RUNNER_PATH] != raw_digest(REPOSITORY_ROOT / RUNNER_PATH):
        raise RuntimeError("Source Bundle 的 Historical Evaluation runner binding 不一致")
    if canonical_digest(args.preregistration.read_bytes()) != qualification["preregistration_digest"]:
        raise RuntimeError("qualification 的 preregistration digest 不一致")
    if args.evaluation.resolve() == args.output.resolve():
        raise RuntimeError("evaluation input 與 output 不得是同一路徑")
    return preregistration, snapshot_set


def read_evaluation_view(path: Path) -> pd.DataFrame:
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, parse_dates=["Date"], chunksize=512):
        chunk = chunk.set_index("Date").sort_index()
        selected = chunk.loc[(chunk.index >= "2020-01-01") & (chunk.index <= "2024-12-31")]
        if not selected.empty:
            chunks.append(selected)
        if not chunk.empty and chunk.index.max() >= pd.Timestamp("2024-12-31"):
            break
    if not chunks:
        raise RuntimeError("Evaluation input 沒有 2020--2024 session")
    return pd.concat(chunks).sort_index()


def detail(trade: Any, equity: float) -> tuple[dict[str, Any], float]:
    return (
        {
            "base_pnl": text(trade.pnl),
            "stress_pnl": text(trade.pnl),
        },
        equity + trade.pnl,
    )


def build_evidence(
    bars: pd.DataFrame, preregistration: dict[str, Any], candidate_definition: dict[str, Any]
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    initial_cash = float(preregistration["initial_cash"])
    for year in range(2020, 2025):
        year_bars = bars.loc[f"{year}-01-01":f"{year}-12-31"]
        result = strategy.backtest(year_bars, reset_at_start=True, cost=strategy.BASE_COST)
        stress_result = strategy.backtest(year_bars, reset_at_start=True, cost=strategy.STRESS_COST)
        if len(result.trades) != len(stress_result.trades):
            raise RuntimeError(f"{year} base/stress 交易數不同")
        equity = initial_cash
        for index, (base, stress) in enumerate(zip(result.trades, stress_result.trades, strict=True), start=1):
            lifecycle = (base.signal_session, base.entry_session, base.exit_session, base.exit_reason)
            stress_lifecycle = (stress.signal_session, stress.entry_session, stress.exit_session, stress.exit_reason)
            if lifecycle != stress_lifecycle:
                raise RuntimeError(f"{year} 第 {index} 筆 base/stress 生命週期不同")
            pnl_detail, equity = detail(base, equity)
            records.append(
                {
                    "base_pnl": pnl_detail["base_pnl"],
                    "exit_date": str(pd.Timestamp(base.exit_session).date()),
                    "fold": year,
                    "order_type": "MARKET",
                    "signal_date": str(pd.Timestamp(base.signal_session).date()),
                    "stress_pnl": text(stress.pnl),
                    "trade_id": f"{candidate_definition['candidate_id']}-evaluation-{year}-{index:03d}",
                }
            )
    return {
        "family_wise_confidence": preregistration["evaluation_gates"]["family_wise_confidence"]["value"],
        "initial_cash": preregistration["initial_cash"],
        "schema_version": 1,
        "stage": "historical-evaluation",
        "stress_drawdown_limit": preregistration["evaluation_gates"]["stress_max_drawdown"]["value"],
        "trades": records,
    }


def main() -> int:
    args = parser().parse_args()
    try:
        candidate = load_canonical(args.candidate_definition)
        preregistration, _snapshot_set = validate_frozen_inputs(args)
        bars = read_evaluation_view(args.evaluation.resolve())
        evidence = build_evidence(bars, preregistration, candidate)
        atomic_create(args.output, canonical_bytes(evidence))
        print(json.dumps({"output": str(args.output), "status": "written"}, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc), "status": "blocked"}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
