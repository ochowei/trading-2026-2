"""隔離測試用的最小正式 runner；同一 CLI 不分正式／合成模式。"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from validator.artifacts import _recompute_development, empty_development_result
from validator.canonical_yaml import (
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.metrics import compare


def backtest(rows, *, spec, cost):
    """最小 fixture 策略：每四列一次進出，資料價格相同就沒有訊號。"""
    trades = []
    equity = 10000.0
    for offset in range(0, len(rows) - 3, 4):
        signal, entry, exit_row = rows[offset : offset + 3]
        entry_price, exit_price = float(entry["Close"]), float(exit_row["Close"])
        if float(signal["Close"]) == entry_price:
            continue
        pnl = exit_price - entry_price - cost
        trades.append(
            {
                "signal_session": signal["Date"],
                "entry_session": entry["Date"],
                "exit_session": exit_row["Date"],
                "exit_reason": "fixture-exit",
                "held_sessions": 1,
                "trade_id": f"trade-{offset}",
                "detail": {
                    "executed_entry_price": str(entry_price),
                    "executed_exit_price": str(exit_price),
                    "fees": str(cost),
                    "shares": 1,
                    "pnl": str(pnl),
                    "pnl_fraction_of_pre_entry_equity": str(pnl / equity),
                },
            }
        )
        equity += pnl
    return trades


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = load_canonical(args.request)
    prereg = request["preregistration"]
    inputs = request["trial_inputs"]
    data = Path(request["data_path"])
    assert canonical_digest(data.read_bytes()) == request["data_digest"]
    with data.open() as stream:
        rows = list(csv.DictReader(stream))
    if request["stage"] == "development":
        result = {}
        for model in ("candidate", "baseline"):
            base = backtest(rows, spec=model, cost=0.1)
            stress = backtest(rows, spec=model, cost=0.2)
            trades = []
            for first, second in zip(base, stress, strict=True):
                detail = first.pop("detail")
                trades.append(dict(first, base=detail, stress=second["detail"]))
            value = {
                "schema_version": 1,
                "stage": "development",
                "network_access_during_run": False,
                "candidate_id": inputs["candidate_id"]
                if model == "candidate"
                else prereg["baseline_definition"]["baseline_id"],
                "bindings": {
                    "source_bundle_digest": canonical_digest(request["source_bundle"]),
                    "preregistration_digest": canonical_digest(prereg),
                    "trial_inputs_digest": canonical_digest(inputs),
                },
                "trades": trades,
                "accepted_signal_count": len(trades),
            }
            if trades:
                metrics, diagnostics, actuals = _recompute_development(value, prereg)
                gates = [
                    {
                        "gate": name,
                        "actual": actuals[name],
                        "operator": rule["operator"],
                        "required": rule["value"],
                        "passed": compare(
                            actuals[name], rule["operator"], rule["value"], metric=name
                        ),
                    }
                    for name, rule in prereg["eligibility_rules"]["development_gates"].items()
                ]
                failures = [g["gate"] for g in gates if not g["passed"]]
                value.update(
                    metrics=metrics,
                    diagnostics=diagnostics,
                    gates=gates,
                    failed_gates=failures,
                    disposition="fail" if failures else "pass",
                )
            else:
                value.update(empty_development_result(prereg))
            result[model] = value
    else:
        base = backtest(rows, spec="candidate", cost=0.1)
        stress = backtest(rows, spec="candidate", cost=0.2)
        result = {
            "schema_version": 1,
            "stage": "historical-evaluation",
            "initial_cash": prereg["initial_cash"],
            "family_wise_confidence": "0.95",
            "stress_drawdown_limit": "0.1",
            "trades": [
                {
                    "trade_id": t["trade_id"],
                    "fold": int(t["signal_session"][:4]),
                    "signal_date": t["signal_session"],
                    "exit_date": t["exit_session"],
                    "order_type": "MARKET",
                    "base_pnl": t["detail"]["pnl"],
                    "stress_pnl": s["detail"]["pnl"],
                }
                for t, s in zip(base, stress, strict=True)
            ],
        }
    atomic_create(args.output, canonical_bytes(result))


if __name__ == "__main__":
    main()
