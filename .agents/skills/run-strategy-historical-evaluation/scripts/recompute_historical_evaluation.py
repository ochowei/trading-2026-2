#!/usr/bin/env python3
"""使用 workflow validator 從 canonical raw evidence 重算 Historical Evaluation。"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [plain(item) for item in value]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("study_id")
    parser.add_argument("evidence", type=Path, nargs="?")
    parser.add_argument("--check-gates-only", action="store_true")
    parser.add_argument("--repository-root", type=Path, default=repository_root())
    args = parser.parse_args()

    root = args.repository_root.resolve()
    workflow = root / "workflows" / "strategy-forward-replication-research--v001"
    sys.path.insert(0, str(workflow))

    from validator.artifacts import evaluate_historical, historical_metrics  # noqa: PLC0415
    from validator.canonical_yaml import load_canonical  # noqa: PLC0415
    from validator.study import WorkflowRules  # noqa: PLC0415

    study = workflow / "studies" / args.study_id
    rules = WorkflowRules(workflow)
    preregistration = load_canonical(study / "manifests" / "preregistration.yml")
    gates = dict(rules.floors["historical_evaluation"])
    gates.update(preregistration["evaluation_gates"])
    synthetic = {
        "schema_version": 1,
        "stage": "historical-evaluation",
        "initial_cash": preregistration["initial_cash"],
        "family_wise_confidence": "0.90",
        "stress_drawdown_limit": "1.0",
        "trades": [],
    }
    supported = set(historical_metrics(synthetic))
    unsupported = sorted(set(gates) - supported)
    if args.check_gates_only:
        print(
            json.dumps(
                {
                    "status": "rejected" if unsupported else "eligible",
                    "study_id": args.study_id,
                    "unsupported_gates": unsupported,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2 if unsupported else 0
    if unsupported:
        raise SystemExit(f"unsupported Evaluation gates: {', '.join(unsupported)}")
    if args.evidence is None:
        parser.error("未使用 --check-gates-only 時必須提供 evidence")
    evidence = load_canonical(args.evidence)
    rules.schema_store.validate("historical-evaluation.schema.yml", evidence)
    metrics, failures = evaluate_historical(
        evidence,
        gates,
        fold_warmup_sessions=preregistration["fold_warmup_sessions"],
        maximum_holding_sessions=preregistration["maximum_holding_sessions"],
    )
    print(
        json.dumps(
            {
                "disposition": "fail" if failures else "pass",
                "failures": failures,
                "metrics": plain(metrics),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
