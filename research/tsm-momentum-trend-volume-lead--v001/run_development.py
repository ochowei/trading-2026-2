"""TSM v001 的 Development runner。

runner 只接受 Lifecycle 提供的 request，讀取 request 指定的固定 OHLCV，
並輸出單一 canonical YAML。Historical Evaluation 分支只為 v003 runner
preflight 的隔離合成案例提供介面驗證；本檔不執行正式 Evaluation。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPOSITORY_ROOT = Path.cwd().resolve()
if (REPOSITORY_ROOT / "workflow").is_dir():
    WORKFLOW_ROOT = REPOSITORY_ROOT / "workflow"
else:
    WORKFLOW_ROOT = (
        REPOSITORY_ROOT
        / "workflows"
        / "strategy-forward-replication-research--v003"
    )
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.artifacts import _recompute_development, empty_development_result  # noqa: E402
from validator.canonical_yaml import (  # noqa: E402
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.metrics import compare  # noqa: E402

from trading_2026_2 import tsm_momentum_trend_volume_lead_v001 as engine  # noqa: E402


CANDIDATE_ID = "tsm-momentum-trend-volume-lead-v001"
BASELINE_ID = "tsm-momentum-trend-volume-lead-baseline-v001"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TSM v001 Development runner")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def frame_from_request(request: dict[str, Any]) -> pd.DataFrame:
    path = Path(request["data_path"])
    if not path.is_absolute():
        path = REPOSITORY_ROOT / path
    data = path.read_bytes()
    if canonical_digest(data) != request["data_digest"]:
        raise RuntimeError("request data digest 不一致")
    frame = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")
    return engine.validate_bars(frame)


def text(value: float) -> str:
    return str(float(value))


def lifecycle_key(trade: engine.Trade) -> tuple[str, str, str, str]:
    return (
        trade.signal_session.date().isoformat(),
        trade.entry_session.date().isoformat(),
        trade.exit_session.date().isoformat(),
        trade.exit_reason,
    )


def model_detail(
    trade: engine.Trade,
    *,
    equity: float,
) -> tuple[dict[str, Any], float]:
    shares = int(trade.shares)
    entry = float(trade.executed_entry_price)
    exit_price = float(trade.executed_exit_price)
    fees = float(trade.fees)
    pnl = shares * (exit_price - entry) - fees
    rate = pnl / equity
    return (
        {
            "executed_entry_price": text(entry),
            "executed_exit_price": text(exit_price),
            "fees": text(fees),
            "pnl": text(pnl),
            "pnl_fraction_of_pre_entry_equity": text(rate),
            "shares": shares,
        },
        equity + pnl,
    )


def paired_trades(
    base: engine.BacktestResult,
    stress: engine.BacktestResult,
    *,
    trade_prefix: str,
) -> list[dict[str, Any]]:
    base_by_key = {lifecycle_key(item): item for item in base.trades}
    stress_by_key = {lifecycle_key(item): item for item in stress.trades}
    if set(base_by_key) != set(stress_by_key):
        raise RuntimeError("base 與 stress 交易生命週期不一致")
    base_equity = 100_000.0
    stress_equity = 100_000.0
    values: list[dict[str, Any]] = []
    for number, key in enumerate(sorted(base_by_key), start=1):
        base_trade = base_by_key[key]
        stress_trade = stress_by_key[key]
        base_detail, base_equity = model_detail(base_trade, equity=base_equity)
        stress_detail, stress_equity = model_detail(stress_trade, equity=stress_equity)
        values.append(
            {
                "base": base_detail,
                "entry_session": base_trade.entry_session.date().isoformat(),
                "exit_reason": base_trade.exit_reason,
                "exit_session": base_trade.exit_session.date().isoformat(),
                "held_sessions": int(base_trade.held_sessions),
                "signal_session": base_trade.signal_session.date().isoformat(),
                "stress": stress_detail,
                "trade_id": f"{trade_prefix}-{number:04d}",
            }
        )
    return values


def gate_records(
    value: dict[str, Any],
    preregistration: dict[str, Any],
    actuals: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    records = []
    for name, rule in preregistration["eligibility_rules"]["development_gates"].items():
        actual = actuals[name]
        passed = compare(actual, rule["operator"], rule["value"], metric=name)
        records.append(
            {
                "actual": actual,
                "gate": name,
                "operator": rule["operator"],
                "passed": passed,
                "required": rule["value"],
            }
        )
    failures = [item["gate"] for item in records if not item["passed"]]
    return records, failures


def development_model(
    frame: pd.DataFrame,
    *,
    spec: engine.StrategySpec,
    candidate_id: str,
    preregistration: dict[str, Any],
    inputs: dict[str, Any],
    source_bundle: dict[str, Any],
) -> dict[str, Any]:
    base = engine.backtest(
        frame,
        spec=spec,
        cost=engine.BASE_COST,
        signal_start="2014-01-01",
        signal_end="2018-12-31",
    )
    stress = engine.backtest(
        frame,
        spec=spec,
        cost=engine.STRESS_COST,
        signal_start="2014-01-01",
        signal_end="2018-12-31",
    )
    trades = paired_trades(base, stress, trade_prefix=candidate_id)
    bindings = {
        "preregistration_digest": canonical_digest(preregistration),
        "source_bundle_digest": canonical_digest(source_bundle),
        "trial_inputs_digest": canonical_digest(inputs),
    }
    if not trades:
        result = empty_development_result(preregistration)
    else:
        draft = {
            "bindings": bindings,
            "candidate_id": candidate_id,
            "diagnostics": {},
            "disposition": "fail",
            "failed_gates": [],
            "gates": [],
            "metrics": {},
            "network_access_during_run": False,
            "schema_version": 1,
            "stage": "development",
            "trades": trades,
        }
        metrics, diagnostics, actuals = _recompute_development(draft, preregistration)
        gates, failures = gate_records(draft, preregistration, actuals)
        result = {
            "accepted_signal_count": len(trades),
            "diagnostics": diagnostics,
            "disposition": "fail" if failures else "pass",
            "failed_gates": failures,
            "gates": gates,
            "metrics": metrics,
        }
    result.update(
        {
            "bindings": bindings,
            "candidate_id": candidate_id,
            "network_access_during_run": False,
            "schema_version": 1,
            "stage": "development",
            "trades": trades,
        }
    )
    return result


def historical_output(
    frame: pd.DataFrame,
    *,
    preregistration: dict[str, Any],
    inputs: dict[str, Any],
) -> dict[str, Any]:
    spec = engine.DEFAULT_SPEC
    base = engine.backtest(frame, spec=spec, cost=engine.BASE_COST)
    stress = engine.backtest(frame, spec=spec, cost=engine.STRESS_COST)
    values = paired_trades(base, stress, trade_prefix=CANDIDATE_ID)
    trades = [
        {
            "base_pnl": item["base"]["pnl"],
            "exit_date": item["exit_session"],
            "fold": int(item["signal_session"][:4]),
            "order_type": "MARKET",
            "signal_date": item["signal_session"],
            "stress_pnl": item["stress"]["pnl"],
            "trade_id": item["trade_id"],
        }
        for item in values
    ]
    return {
        "family_wise_confidence": "0.90",
        "initial_cash": preregistration["initial_cash"],
        "schema_version": 1,
        "stage": "historical-evaluation",
        "stress_drawdown_limit": "0.10",
        "trades": trades,
    }


def main() -> None:
    args = parse_args()
    request = load_canonical(args.request)
    preregistration = request["preregistration"]
    inputs = request["trial_inputs"]
    source_bundle = request["source_bundle"]
    frame = frame_from_request(request)
    if request["stage"] == "historical-evaluation":
        value = historical_output(
            frame,
            preregistration=preregistration,
            inputs=inputs,
        )
    elif request["stage"] == "development":
        value = {
            "baseline": development_model(
                frame,
                spec=engine.BASELINE_SPEC,
                candidate_id=BASELINE_ID,
                preregistration=preregistration,
                inputs=inputs,
                source_bundle=source_bundle,
            ),
            "candidate": development_model(
                frame,
                spec=engine.DEFAULT_SPEC,
                candidate_id=CANDIDATE_ID,
                preregistration=preregistration,
                inputs=inputs,
                source_bundle=source_bundle,
            ),
        }
    else:
        raise RuntimeError(f"不支援的 runner stage: {request['stage']}")
    atomic_create(args.output, canonical_bytes(value))


if __name__ == "__main__":
    main()
