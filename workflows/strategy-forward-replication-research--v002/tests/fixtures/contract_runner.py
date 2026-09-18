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
    import pandas as pd

    from trading_2026_2.tsm_mean_reversion_reversal_trigger_v001 import (
        BASE_COST,
        BASELINE_SPEC,
        DEFAULT_SPEC,
        STRESS_COST,
    )
    from trading_2026_2.tsm_mean_reversion_reversal_trigger_v001 import (
        backtest as engine_backtest,
    )
    frame = pd.DataFrame(rows)
    frame.index = pd.to_datetime(frame.pop("Date"))
    frame = frame.astype(float)
    model = DEFAULT_SPEC if spec == "candidate" else BASELINE_SPEC
    result = engine_backtest(frame, spec=model, cost=BASE_COST if cost == 0.1 else STRESS_COST)
    trades = []
    equity = model.initial_cash
    for i, trade in enumerate(result.trades):
        trades.append({"signal_session": trade.signal_session.strftime("%Y-%m-%d"),
                       "entry_session": trade.entry_session.strftime("%Y-%m-%d"),
                       "exit_session": trade.exit_session.strftime("%Y-%m-%d"),
                       "exit_reason": trade.exit_reason, "held_sessions": trade.held_sessions,
                       "trade_id": f"trade-{i}", "detail": {
                           "executed_entry_price": str(trade.executed_entry_price),
                           "executed_exit_price": str(trade.executed_exit_price),
                           "fees": str(trade.fees), "shares": trade.shares, "pnl": str(trade.pnl),
                           "pnl_fraction_of_pre_entry_equity": str(trade.pnl / equity)}})
        equity += trade.pnl
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
            value = {"schema_version": 1, "stage": "development", "network_access_during_run": False,
                     "candidate_id": inputs["candidate_id"] if model == "candidate" else prereg["baseline_definition"]["baseline_id"],
                     "bindings": {"source_bundle_digest": canonical_digest(request["source_bundle"]),
                                  "preregistration_digest": canonical_digest(prereg),
                                  "trial_inputs_digest": canonical_digest(inputs)},
                     "trades": trades, "accepted_signal_count": len(trades)}
            if trades:
                metrics, diagnostics, actuals = _recompute_development(value, prereg)
                gates = [{"gate": name, "actual": actuals[name], "operator": rule["operator"],
                          "required": rule["value"], "passed": compare(actuals[name], rule["operator"], rule["value"], metric=name)}
                         for name, rule in prereg["eligibility_rules"]["development_gates"].items()]
                failures = [g["gate"] for g in gates if not g["passed"]]
                value.update(metrics=metrics, diagnostics=diagnostics, gates=gates,
                             failed_gates=failures, disposition="fail" if failures else "pass")
            else:
                value.update(empty_development_result(prereg))
            result[model] = value
    else:
        base = backtest(rows, spec="candidate", cost=0.1)
        stress = backtest(rows, spec="candidate", cost=0.2)
        result = {"schema_version": 1, "stage": "historical-evaluation", "initial_cash": prereg["initial_cash"],
                  "family_wise_confidence": "0.95", "stress_drawdown_limit": "0.1",
                  "trades": [{"trade_id": t["trade_id"], "fold": int(t["signal_session"][:4]),
                              "signal_date": t["signal_session"], "exit_date": t["exit_session"],
                              "order_type": "MARKET", "base_pnl": t["detail"]["pnl"],
                              "stress_pnl": s["detail"]["pnl"]} for t, s in zip(base, stress, strict=True)]}
    atomic_create(args.output, canonical_bytes(result))


if __name__ == "__main__":
    main()
