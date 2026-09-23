"""v004 離線 Development／runner-preflight 程式。"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from validator.artifacts import _recompute_development, empty_development_result
from validator.canonical_yaml import atomic_create, canonical_bytes, canonical_digest, load_canonical
from validator.metrics import compare


def _backtest(rows, *, model: str, cost_bps: tuple[float, float], inputs: dict):
    import pandas as pd

    from trading_2026_2.tsm_momentum_trend_volume_gap_retention_v001 import (
        BASE_COST,
        BASELINE_SPEC,
        DEFAULT_SPEC,
        STRESS_COST,
        backtest as engine_backtest,
    )

    frame = pd.DataFrame(rows)
    frame.index = pd.to_datetime(frame.pop("Date"))
    frame = frame.astype(float)
    spec = DEFAULT_SPEC if model == "candidate" else BASELINE_SPEC
    cost = BASE_COST if cost_bps == (5.0, 1.0) else STRESS_COST
    controls = inputs.get("date_controls", {})
    result = engine_backtest(
        frame,
        spec=spec,
        cost=cost,
        signal_start=controls.get("signal_start") if inputs else None,
        signal_end=controls.get("signal_end") if inputs else None,
    )
    trades = []
    equity = spec.initial_cash
    for index, trade in enumerate(result.trades):
        trades.append(
            {
                "signal_session": trade.signal_session.strftime("%Y-%m-%d"),
                "entry_session": trade.entry_session.strftime("%Y-%m-%d"),
                "exit_session": trade.exit_session.strftime("%Y-%m-%d"),
                "exit_reason": trade.exit_reason,
                "held_sessions": trade.held_sessions,
                "trade_id": f"trade-{index}",
                "detail": {
                    "executed_entry_price": str(trade.executed_entry_price),
                    "executed_exit_price": str(trade.executed_exit_price),
                    "fees": str(trade.fees),
                    "shares": trade.shares,
                    "pnl": str(trade.pnl),
                    "pnl_fraction_of_pre_entry_equity": str(trade.pnl / equity),
                },
            }
        )
        equity += trade.pnl
    return trades


def _development(rows, request: dict) -> dict:
    prereg = request["preregistration"]
    inputs = request["trial_inputs"]
    bundle_digest = canonical_digest(request["source_bundle"])
    result = {}
    for model in ("candidate", "baseline"):
        base = _backtest(rows, model=model, cost_bps=(5.0, 1.0), inputs=inputs)
        stress = _backtest(rows, model=model, cost_bps=(20.0, 2.0), inputs=inputs)
        if [trade["signal_session"] for trade in base] != [
            trade["signal_session"] for trade in stress
        ]:
            raise ValueError("base 與 stress 的訊號日不一致")
        trades = []
        for first, second in zip(base, stress, strict=True):
            base_detail = first.pop("detail")
            stress_detail = second["detail"]
            trades.append(dict(first, base=base_detail, stress=stress_detail))
        value = {
            "schema_version": 1,
            "stage": "development",
            "network_access_during_run": False,
            "candidate_id": (
                inputs["candidate_id"]
                if model == "candidate"
                else prereg["baseline_definition"]["baseline_id"]
            ),
            "bindings": {
                "source_bundle_digest": bundle_digest,
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
            failures = [gate["gate"] for gate in gates if not gate["passed"]]
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
    return result


def _historical_fixture(rows, request: dict) -> dict:
    """僅供 v004 runner-preflight 的隔離合成 fixture，沒有實際市場輸入。"""

    prereg = request["preregistration"]
    inputs = request["trial_inputs"]
    base = _backtest(rows, model="candidate", cost_bps=(5.0, 1.0), inputs={})
    stress = _backtest(rows, model="candidate", cost_bps=(20.0, 2.0), inputs={})
    if [trade["signal_session"] for trade in base] != [
        trade["signal_session"] for trade in stress
    ]:
        raise ValueError("合成 base／stress fixture 的訊號日不一致")
    return {
        "schema_version": 1,
        "stage": "historical-evaluation",
        "initial_cash": prereg["initial_cash"],
        "family_wise_confidence": "0.95",
        "stress_drawdown_limit": "0.10",
        "trades": [
            {
                "trade_id": trade["trade_id"],
                "fold": int(trade["signal_session"][:4]),
                "signal_date": trade["signal_session"],
                "exit_date": trade["exit_session"],
                "order_type": "MARKET",
                "base_pnl": trade["detail"]["pnl"],
                "stress_pnl": stressed["detail"]["pnl"],
            }
            for trade, stressed in zip(base, stress, strict=True)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = load_canonical(args.request)
    data_path = Path(request["data_path"])
    data_bytes = data_path.read_bytes()
    if canonical_digest(data_bytes) != request["data_digest"]:
        raise ValueError("runner 輸入資料 digest 不一致")
    with data_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("runner 沒有收到資料列")
    if request["stage"] == "development":
        controls = request["trial_inputs"]["date_controls"]
        start, end = controls["warmup_start"], controls["signal_end"]
        dates = [row["Date"] for row in rows]
        if any(day < start or day > end or day >= "2019-01-01" for day in dates):
            raise ValueError("Development runner 收到 warmup／development 區間外的資料")
        value = _development(rows, request)
    elif request["stage"] == "historical-evaluation":
        value = _historical_fixture(rows, request)
    else:
        raise ValueError(f"不支援的 runner stage: {request['stage']}")
    atomic_create(args.output, canonical_bytes(value))


if __name__ == "__main__":
    main()
