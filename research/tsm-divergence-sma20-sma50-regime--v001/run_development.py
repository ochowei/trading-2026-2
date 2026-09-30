"""TASK-036 request/output runner for Development and isolated synthetic preflight."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Any
import pandas as pd
ROOT = Path.cwd().resolve()
if (ROOT / "workflow").is_dir():
    WORKFLOW_ROOT = ROOT / "workflow"
else:
    WORKFLOW_ROOT = ROOT / "workflows" / "strategy-forward-replication-research--v005"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))
from validator.artifacts import _recompute_development, empty_development_result
from validator.canonical_yaml import atomic_create, canonical_bytes, canonical_digest, load_canonical
from validator.metrics import compare
from trading_2026_2 import tsm_mean_reversion_two_stage_volume_reversal_sma20_sma50_regime_v001 as candidate_engine
from trading_2026_2 import tsm_mean_reversion_two_stage_volume_reversal_v009 as control_engine
CANDIDATE_ID = "tsm-mr-v009-sma20-over-sma50-regime-v001"
CONTROL_ID = "tsm-mr-v009-two-stage-volume-reversal-control-task036-v001"
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TASK-036 candidate/control evidence runner")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()
def text(value: float) -> str:
    return str(float(value))
def frame_from_request(request: dict[str, Any]) -> pd.DataFrame:
    path = Path(request["data_path"])
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    if canonical_digest(raw) != request["data_digest"]:
        raise RuntimeError("request data digest mismatch")
    return candidate_engine.validate_bars(pd.read_csv(path, parse_dates=["Date"]).set_index("Date"))
def lifecycle_key(trade: Any) -> tuple[str, str, str, str]:
    return (trade.signal_session.date().isoformat(), trade.entry_session.date().isoformat(), trade.exit_session.date().isoformat(), trade.exit_reason)
def trade_detail(trade: Any, *, equity: float) -> tuple[dict[str, Any], float]:
    shares = int(trade.shares)
    entry = float(trade.executed_entry_price)
    exit_price = float(trade.executed_exit_price)
    fees = float(trade.fees)
    pnl = shares * (exit_price - entry) - fees
    if abs(pnl - float(trade.pnl)) > 1e-7:
        raise RuntimeError("engine pnl does not reconcile to fills and fees")
    rate = pnl / equity
    return ({"executed_entry_price": text(entry), "executed_exit_price": text(exit_price), "fees": text(fees), "pnl": text(pnl), "pnl_fraction_of_pre_entry_equity": text(rate), "shares": shares}, equity + pnl)
def paired_trades(base: Any, stress: Any, *, model_id: str, initial_cash: float) -> list[dict[str, Any]]:
    base_by_key = {lifecycle_key(item): item for item in base.trades}
    stress_by_key = {lifecycle_key(item): item for item in stress.trades}
    if set(base_by_key) != set(stress_by_key):
        raise RuntimeError("base/stress lifecycle mismatch")
    values = []
    base_equity = stress_equity = initial_cash
    for number, key in enumerate(sorted(base_by_key), start=1):
        bt, st = base_by_key[key], stress_by_key[key]
        base_detail, base_equity = trade_detail(bt, equity=base_equity)
        stress_detail, stress_equity = trade_detail(st, equity=stress_equity)
        values.append({"base": base_detail, "entry_session": bt.entry_session.date().isoformat(), "exit_reason": bt.exit_reason, "exit_session": bt.exit_session.date().isoformat(), "held_sessions": int(bt.held_sessions), "signal_session": bt.signal_session.date().isoformat(), "stress": stress_detail, "trade_id": f"{model_id}-{number:04d}"})
    return values
def model_evidence(frame: pd.DataFrame, *, module: Any, spec: Any, model_id: str, prereg: dict[str, Any], inputs: dict[str, Any], bundle: dict[str, Any]) -> dict[str, Any]:
    base = module.backtest(frame, spec=spec, cost=module.BASE_COST, signal_start="2014-01-01", signal_end="2018-12-31")
    stress = module.backtest(frame, spec=spec, cost=module.STRESS_COST, signal_start="2014-01-01", signal_end="2018-12-31")
    initial_cash = float(prereg["initial_cash"])
    trades = paired_trades(base, stress, model_id=model_id, initial_cash=initial_cash)
    bindings = {"preregistration_digest": canonical_digest(prereg), "source_bundle_digest": canonical_digest(bundle), "trial_inputs_digest": canonical_digest(inputs)}
    if not trades:
        result = empty_development_result(prereg)
    else:
        draft = {"bindings": bindings, "candidate_id": model_id, "diagnostics": {}, "disposition": "fail", "failed_gates": [], "gates": [], "metrics": {}, "network_access_during_run": False, "schema_version": 1, "stage": "development", "trades": trades}
        metrics, diagnostics, actuals = _recompute_development(draft, prereg)
        gates = []
        for name, rule in prereg["eligibility_rules"]["development_gates"].items():
            actual = actuals[name]
            gates.append({"actual": actual, "gate": name, "operator": rule["operator"], "passed": compare(actual, rule["operator"], rule["value"], metric=name), "required": rule["value"]})
        failures = [item["gate"] for item in gates if item["passed"] is False]
        result = {"accepted_signal_count": len(trades), "diagnostics": diagnostics, "disposition": "fail" if failures else "pass", "failed_gates": failures, "gates": gates, "metrics": metrics}
    result.update({"bindings": bindings, "candidate_id": model_id, "network_access_during_run": False, "schema_version": 1, "stage": "development", "trades": trades})
    return result
def historical_output(frame: pd.DataFrame, *, prereg: dict[str, Any]) -> dict[str, Any]:
    base = candidate_engine.backtest(frame, spec=candidate_engine.DEFAULT_SPEC, cost=candidate_engine.BASE_COST)
    stress = candidate_engine.backtest(frame, spec=candidate_engine.DEFAULT_SPEC, cost=candidate_engine.STRESS_COST)
    rows = paired_trades(base, stress, model_id=CANDIDATE_ID, initial_cash=float(prereg["initial_cash"]))
    trades = [{"base_pnl": item["base"]["pnl"], "exit_date": item["exit_session"], "fold": int(item["signal_session"][:4]), "order_type": "MARKET", "signal_date": item["signal_session"], "stress_pnl": item["stress"]["pnl"], "trade_id": item["trade_id"]} for item in rows]
    return {"family_wise_confidence": prereg["evaluation_gates"]["family_wise_confidence"]["value"], "initial_cash": prereg["initial_cash"], "schema_version": 1, "stage": "historical-evaluation", "stress_drawdown_limit": prereg["evaluation_gates"]["stress_max_drawdown"]["value"], "trades": trades}
def main() -> None:
    args = parse_args()
    if args.output.exists():
        raise RuntimeError("refusing to overwrite evidence")
    request = load_canonical(args.request)
    prereg, inputs, bundle = request["preregistration"], request["trial_inputs"], request["source_bundle"]
    frame = frame_from_request(request)
    if request["stage"] == "historical-evaluation":
        value = historical_output(frame, prereg=prereg)
    elif request["stage"] == "development":
        value = {
            "baseline": model_evidence(frame, module=control_engine, spec=control_engine.DEFAULT_SPEC, model_id=CONTROL_ID, prereg=prereg, inputs=inputs, bundle=bundle),
            "candidate": model_evidence(frame, module=candidate_engine, spec=candidate_engine.DEFAULT_SPEC, model_id=CANDIDATE_ID, prereg=prereg, inputs=inputs, bundle=bundle),
        }
    else:
        raise RuntimeError(f"unsupported stage: {request['stage']}")
    atomic_create(args.output, canonical_bytes(value))
if __name__ == "__main__":
    main()
