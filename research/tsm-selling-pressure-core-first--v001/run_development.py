"""v005 request/output runner for the preregistered TSM core-first comparison."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path.cwd().resolve()
WORKFLOW_ROOT = ROOT / "workflows" / "strategy-forward-replication-research--v005"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.artifacts import _recompute_development, empty_development_result  # noqa: E402
from validator.canonical_yaml import atomic_create, canonical_bytes, canonical_digest, load_canonical  # noqa: E402
from validator.metrics import compare  # noqa: E402

CANDIDATE_ENGINE = "src/trading_2026_2/tsm_mean_reversion_selling_pressure_core_first_v001.py"
CONTROL_ENGINE = "src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py"
CANDIDATE_ID = "tsm-mr-selling-pressure-core-first-v001"


def load_engine(relative_path: str, module_name: str):
    path = (ROOT / relative_path).resolve()
    path.relative_to(ROOT)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入已綁定的策略引擎：{relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def request_bars(request: dict[str, Any], inputs: dict[str, Any]) -> tuple[pd.DataFrame, dict]:
    data_assets = request.get("data_assets")
    if not isinstance(data_assets, list):
        raise RuntimeError("Development request 必須提供固定 data_assets")
    trade_assets = [asset for asset in data_assets if asset.get("use") == "trade"]
    if len(trade_assets) != 1:
        raise RuntimeError("TSM Study 必須且只能有一個 trade asset")
    asset = trade_assets[0]
    registered = inputs["data_bindings"]["assets"]
    registered_trade = [item for item in registered if item.get("use") == "trade"]
    if len(registered_trade) != 1:
        raise RuntimeError("Trial inputs 必須且只能登記一個 trade asset")
    if (asset["asset_id"], asset["use"]) != (
        registered_trade[0]["asset_id"], registered_trade[0]["use"]
    ):
        raise RuntimeError("request data asset roster 與 preregistered Trial input 不一致")
    if asset.get("provider") != "synthetic":
        normalise = lambda item: {
            key: value for key, value in item.items() if key != "data_path"
        }
        if normalise(asset) != normalise(registered_trade[0]):
            raise RuntimeError("request data asset 與 preregistered Trial input 不一致")
    relative = Path(asset["data_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError("拒絕讀取 repository 外的 Development asset")
    path = (ROOT / relative).resolve()
    path.relative_to(ROOT)
    data = path.read_bytes()
    if canonical_digest(data) != asset["data_digest"]:
        raise RuntimeError("Development asset digest 不一致")
    bars = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
    if list(bars.columns) != ["Open", "High", "Low", "Close", "Volume"]:
        raise RuntimeError("Development CSV 欄位不符合固定 OHLCV schema")
    if bars.empty or bars.index.has_duplicates or not bars.index.is_monotonic_increasing:
        raise RuntimeError("Development CSV session 空白、重複或未排序")
    if str(bars.index[0].date()) != asset["start_date"] or str(bars.index[-1].date()) != asset["end_date"]:
        raise RuntimeError("Development asset 日期界線與資料不一致")
    if (bars.index < pd.Timestamp("2013-01-01")).any() or (bars.index > pd.Timestamp("2018-12-31")).any():
        raise RuntimeError("Development asset 含有 preregistered 範圍外日期")
    return bars, asset


def pair_trades(base_result, stress_result, initial_cash: float) -> list[dict[str, Any]]:
    base_trades = list(base_result.trades)
    stress_trades = list(stress_result.trades)
    if len(base_trades) != len(stress_trades):
        raise RuntimeError("base 與 stress 的 trade 數不一致")
    records = []
    base_equity = initial_cash
    stress_equity = initial_cash
    for index, (base, stress) in enumerate(zip(base_trades, stress_trades, strict=True), start=1):
        left = (base.signal_session, base.entry_session, base.exit_session, base.exit_reason, base.held_sessions)
        right = (stress.signal_session, stress.entry_session, stress.exit_session, stress.exit_reason, stress.held_sessions)
        if left != right:
            raise RuntimeError("base 與 stress 的 trade lifecycle 不一致")

        def model(trade, pre_entry_equity: float) -> dict[str, Any]:
            return {
                "executed_entry_price": repr(float(trade.executed_entry_price)),
                "executed_exit_price": repr(float(trade.executed_exit_price)),
                "fees": repr(float(trade.fees)),
                "pnl": repr(float(trade.pnl)),
                "pnl_fraction_of_pre_entry_equity": repr(float(trade.pnl) / pre_entry_equity),
                "shares": int(trade.shares),
            }

        records.append(
            {
                "trade_id": f"development-{index:04d}",
                "signal_session": base.signal_session.strftime("%Y-%m-%d"),
                "entry_session": base.entry_session.strftime("%Y-%m-%d"),
                "exit_session": base.exit_session.strftime("%Y-%m-%d"),
                "exit_reason": base.exit_reason,
                "held_sessions": int(base.held_sessions),
                "base": model(base, base_equity),
                "stress": model(stress, stress_equity),
            }
        )
        base_equity += float(base.pnl)
        stress_equity += float(stress.pnl)
    return records


def evidence(
    trades: list[dict[str, Any]],
    *,
    candidate_id: str,
    inputs: dict,
    preregistration: dict,
    source_bundle: dict,
) -> dict[str, Any]:
    bindings = {
        "preregistration_digest": canonical_digest(preregistration),
        "source_bundle_digest": canonical_digest(source_bundle),
        "trial_inputs_digest": canonical_digest(inputs),
        "data_assets_digest": canonical_digest(inputs["data_bindings"]["assets"]),
    }
    if not trades:
        result = empty_development_result(preregistration)
    else:
        metrics, diagnostics, actuals = _recompute_development({"trades": trades}, preregistration)
        rules = preregistration["eligibility_rules"]["development_gates"]
        gates = [
            {
                "gate": name,
                "operator": rule["operator"],
                "required": rule["value"],
                "actual": actuals[name],
                "passed": compare(actuals[name], rule["operator"], rule["value"], metric=name),
            }
            for name, rule in rules.items()
        ]
        failures = [item["gate"] for item in gates if not item["passed"]]
        result = {
            "metrics": metrics,
            "diagnostics": diagnostics,
            "accepted_signal_count": len(trades),
            "gates": gates,
            "failed_gates": failures,
            "disposition": "fail" if failures else "pass",
        }
    return {
        "schema_version": 1,
        "stage": "development",
        "candidate_id": candidate_id,
        "bindings": bindings,
        "trades": trades,
        **result,
        "network_access_during_run": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError("拒絕覆寫 Development output")
    request = load_canonical(args.request)
    if request.get("stage") != "development":
        raise RuntimeError("Development runner 只接受 development stage")
    inputs = request["trial_inputs"]
    preregistration = request["preregistration"]
    source_bundle = request["source_bundle"]
    bars, asset = request_bars(request, inputs)
    start = inputs["date_controls"]["signal_start"]
    end = inputs["date_controls"]["signal_end"]

    candidate = load_engine(CANDIDATE_ENGINE, "_task032_core_first_candidate")
    control = load_engine(CONTROL_ENGINE, "_task032_v009_control")
    candidate_base = candidate.backtest(bars, spec=candidate.DEFAULT_SPEC, cost=candidate.BASE_COST, signal_start=start, signal_end=end)
    candidate_stress = candidate.backtest(bars, spec=candidate.DEFAULT_SPEC, cost=candidate.STRESS_COST, signal_start=start, signal_end=end)
    control_base = control.backtest(bars, spec=control.DEFAULT_SPEC, cost=control.BASE_COST, signal_start=start, signal_end=end)
    control_stress = control.backtest(bars, spec=control.DEFAULT_SPEC, cost=control.STRESS_COST, signal_start=start, signal_end=end)

    # Synthetic preflight fixtures exercise each core-first state rule. These
    # checks stay internal to the runner and do not add attribution to evidence.
    if asset["provider"] == "synthetic":
        signal_frame = candidate.indicators(bars)

        def verify_slot_policy(result, label: str) -> None:
            trades = list(result.trades)
            path_a = signal_frame["path_a_raw_signal"].astype(bool)
            path_b = signal_frame["path_b_raw_signal"].astype(bool)
            overlap = path_a & path_b
            trade_by_signal = {trade.signal_session: trade for trade in trades}
            minimum_signal_index = candidate._required_history_sessions(candidate.DEFAULT_SPEC)

            # At the first simultaneous flat signal, the next-open trade must be core.
            for index, session in enumerate(signal_frame.index):
                if not bool(overlap.loc[session]) or index < minimum_signal_index:
                    continue
                active = any(trade.entry_session <= session < trade.exit_session for trade in trades)
                previous_exits = [trade.exit_session for trade in trades if trade.exit_session <= session]
                cooled = not previous_exits or index - signal_frame.index.get_loc(max(previous_exits)) >= candidate.DEFAULT_SPEC.cooldown_sessions
                enough_time = index + candidate.DEFAULT_SPEC.holding_sessions + 1 < len(signal_frame)
                if active or not cooled or not enough_time:
                    continue
                selected = trade_by_signal.get(session)
                if selected is None or selected.signal_origin != "path_a":
                    raise RuntimeError(f"{label} synthetic simultaneous-signal core-priority guard failed")
                break

            # A raw Path B signal while a core position is open must not create a B trade.
            for core_trade in (trade for trade in trades if trade.signal_origin == "path_a"):
                hidden_b_signals = [
                    session for session in signal_frame.index
                    if bool(path_b.loc[session])
                    and core_trade.entry_session <= session < core_trade.exit_session
                ]
                if any(
                    trade.signal_origin == "path_b" and trade.signal_session in hidden_b_signals
                    for trade in trades
                ):
                    raise RuntimeError(f"{label} synthetic holding-core suppression guard failed")

            # If core appears while B is still held, close B and reopen core at that next open.
            for supplemental in (trade for trade in trades if trade.signal_origin == "path_b"):
                core_signals = [
                    session for session in signal_frame.index
                    if bool(path_a.loc[session])
                    and supplemental.entry_session <= session < supplemental.exit_session
                ]
                if not core_signals:
                    continue
                signal_session = core_signals[0]
                signal_index = signal_frame.index.get_loc(signal_session)
                expected_open = signal_frame.index[signal_index + 1]
                successor = next(
                    (
                        trade for trade in trades
                        if trade.signal_origin == "path_a"
                        and trade.entry_session == expected_open
                        and trade.signal_session == signal_session
                    ),
                    None,
                )
                if (
                    supplemental.exit_reason != "core-priority-switch"
                    or supplemental.exit_session != expected_open
                    or successor is None
                    or supplemental.fees <= 0
                    or successor.fees <= 0
                ):
                    raise RuntimeError(f"{label} synthetic B-to-core handoff/cost guard failed")

        verify_slot_policy(candidate_base, "base")
        verify_slot_policy(candidate_stress, "stress")

    initial_cash = float(preregistration["initial_cash"])
    candidate_trades = pair_trades(candidate_base, candidate_stress, initial_cash)
    baseline_id = preregistration["baseline_definition"]["baseline_id"]
    baseline_trades = pair_trades(control_base, control_stress, initial_cash)
    result = {
        "candidate": evidence(
            candidate_trades,
            candidate_id=inputs["candidate_id"],
            inputs=inputs,
            preregistration=preregistration,
            source_bundle=source_bundle,
        ),
        "baseline": evidence(
            baseline_trades,
            candidate_id=baseline_id,
            inputs=inputs,
            preregistration=preregistration,
            source_bundle=source_bundle,
        ),
    }
    atomic_create(args.output, canonical_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
