from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_2026_2.tsm_mean_reversion_divergence_sma20_exit_v001 import (
    BASE_COST,
    CONTROL_SPEC,
    SMA20_REENTRY_EXIT_SPEC,
    STRESS_COST,
    backtest,
)
from validator.artifacts import _recompute_development, empty_development_result
from validator.canonical_yaml import canonical_digest, load_canonical, write_canonical
from validator.metrics import compare


def bars_from_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["Date"])
    if list(frame.columns) != ["Date", "Open", "High", "Low", "Close", "Volume"]:
        raise ValueError("Development CSV 欄位必須固定為 Date 與五個 OHLCV 欄")
    return frame.set_index("Date")


def text(value: float) -> str:
    return repr(float(value))


def trade_records(base_trades, stress_trades, prefix: str, initial_cash: float):
    if len(base_trades) != len(stress_trades):
        raise ValueError(f"{prefix} base/stress 交易數不同")
    output = []
    equity = {"base": initial_cash, "stress": initial_cash}
    for index, (base, stress) in enumerate(zip(base_trades, stress_trades, strict=True), start=1):
        lifecycle = (base.signal_session, base.entry_session, base.exit_session, base.exit_reason)
        stress_lifecycle = (
            stress.signal_session,
            stress.entry_session,
            stress.exit_session,
            stress.exit_reason,
        )
        if lifecycle != stress_lifecycle:
            raise ValueError(f"{prefix} base/stress 交易生命週期不同")
        row = {
            "trade_id": f"{prefix}-{index:04d}",
            "signal_session": base.signal_session.date().isoformat(),
            "entry_session": base.entry_session.date().isoformat(),
            "exit_session": base.exit_session.date().isoformat(),
            "exit_reason": base.exit_reason,
            "held_sessions": int(base.held_sessions),
        }
        for label, trade in (("base", base), ("stress", stress)):
            pre_entry_equity = equity[label]
            row[label] = {
                "executed_entry_price": text(trade.executed_entry_price),
                "executed_exit_price": text(trade.executed_exit_price),
                "fees": text(trade.fees),
                "pnl": text(trade.pnl),
                "pnl_fraction_of_pre_entry_equity": text(trade.pnl / pre_entry_equity),
                "shares": int(trade.shares),
            }
            equity[label] += trade.pnl
        output.append(row)
    return output


def run_arm(bars, spec, inputs, prereg, source_bundle, model_id: str, prefix: str):
    initial_cash = float(prereg["initial_cash"])
    spec = spec.with_changes(
        mean_reversion_min=0.015,
        rsi_max=50.0,
        volume_spike_ratio=1.05,
        holding_sessions=10,
        cooldown_sessions=5,
        stop_return=-0.04,
        target_return=0.04,
        risk_fraction=0.02,
        initial_cash=initial_cash,
    )
    controls = inputs["date_controls"]
    base = backtest(
        bars,
        spec=spec,
        cost=BASE_COST,
        signal_start=controls["signal_start"],
        signal_end=controls["signal_end"],
    )
    stress = backtest(
        bars,
        spec=spec,
        cost=STRESS_COST,
        signal_start=controls["signal_start"],
        signal_end=controls["signal_end"],
    )
    trades = trade_records(base.trades, stress.trades, prefix, initial_cash)
    evidence = {
        "schema_version": 1,
        "stage": "development",
        "candidate_id": model_id,
        "bindings": {
            "preregistration_digest": canonical_digest(prereg),
            "source_bundle_digest": canonical_digest(source_bundle),
            "trial_inputs_digest": canonical_digest(inputs),
        },
        "trades": trades,
        "network_access_during_run": False,
    }
    if not trades:
        return {**evidence, **empty_development_result(prereg)}

    evidence["accepted_signal_count"] = len(trades)
    metrics, diagnostics, actuals = _recompute_development(evidence, prereg)
    gates = []
    for name, rule in prereg["eligibility_rules"]["development_gates"].items():
        actual = actuals[name]
        passed = compare(actual, rule["operator"], rule["value"], metric=name)
        gates.append(
            {
                "gate": name,
                "operator": rule["operator"],
                "required": rule["value"],
                "actual": actual,
                "passed": passed,
            }
        )
    failed = [item["gate"] for item in gates if not item["passed"]]
    return {
        **evidence,
        "metrics": metrics,
        "diagnostics": diagnostics,
        "gates": gates,
        "failed_gates": failed,
        "disposition": "fail" if failed else "pass",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    request = load_canonical(args.request)
    if request["stage"] != "development":
        raise ValueError("本 runner 僅接受 Development request")
    bars = bars_from_csv(Path(request["data_path"]))
    inputs = request["trial_inputs"]
    prereg = request["preregistration"]
    source_bundle = request["source_bundle"]
    candidate = run_arm(
        bars,
        SMA20_REENTRY_EXIT_SPEC,
        inputs,
        prereg,
        source_bundle,
        inputs["candidate_id"],
        "candidate",
    )
    control = run_arm(
        bars,
        CONTROL_SPEC,
        inputs,
        prereg,
        source_bundle,
        prereg["baseline_definition"]["baseline_id"],
        "baseline",
    )
    write_canonical(args.output, {"candidate": candidate, "baseline": control})


if __name__ == "__main__":
    main()
