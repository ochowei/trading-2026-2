"""v005 Development runner：只讀請求綁定的 TSM／SOXX 固定快照。"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd
from validator.artifacts import _recompute_development, empty_development_result
from validator.canonical_yaml import (
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.metrics import compare

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_engine as engine  # noqa: E402


def _load_bars(path: Path) -> tuple[pd.DataFrame, bytes]:
    raw = path.read_bytes()
    frame = pd.read_csv(path, parse_dates=["Date"])
    if list(frame.columns) != ["Date", "Open", "High", "Low", "Close", "Volume"]:
        raise ValueError(f"OHLCV 欄位不符：{path.name}")
    frame = frame.set_index("Date")
    frame.index = pd.DatetimeIndex(frame.index).tz_localize(None).normalize()
    return frame.astype(float), raw


def _load_assets(request: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    assets = request.get("data_assets")
    if not isinstance(assets, list) or [(item["asset_id"], item["use"]) for item in assets] != [
        ("SOXX", "reference"),
        ("TSM", "trade"),
    ]:
        raise ValueError("Development runner 僅接受 preregistered SOXX reference + TSM trade roster")
    loaded: dict[str, pd.DataFrame] = {}
    for asset in assets:
        path = Path(asset["data_path"])
        if not path.is_absolute():
            path = Path.cwd() / path
        bars, raw = _load_bars(path)
        if hashlib.sha256(raw).hexdigest() != asset["data_digest"]:
            raise ValueError(f"{asset['asset_id']} raw digest 與 runner request 不一致")
        if bars.index[0].strftime("%Y-%m-%d") != asset["start_date"]:
            raise ValueError(f"{asset['asset_id']} start_date 與 CSV 不一致")
        if bars.index[-1].strftime("%Y-%m-%d") != asset["end_date"]:
            raise ValueError(f"{asset['asset_id']} end_date 與 CSV 不一致")
        loaded[asset["asset_id"]] = bars
    if not loaded["TSM"].index.equals(loaded["SOXX"].index):
        raise ValueError("TSM 與 SOXX sessions 未逐日對齊")
    return loaded["TSM"], loaded["SOXX"]


def _development_evidence(
    trades: list[dict[str, object]],
    *,
    candidate_id: str,
    bindings: dict[str, str],
    preregistration: dict,
) -> dict:
    value = {
        "schema_version": 1,
        "stage": "development",
        "candidate_id": candidate_id,
        "bindings": bindings.copy(),
        "trades": trades,
        "network_access_during_run": False,
    }
    if not trades:
        value.update(empty_development_result(preregistration))
        return value

    metrics, diagnostics, actuals = _recompute_development(value, preregistration)
    gate_rules = preregistration["eligibility_rules"]["development_gates"]
    gates = [
        {
            "gate": name,
            "operator": rule["operator"],
            "required": rule["value"],
            "actual": actuals[name],
            "passed": compare(actuals[name], rule["operator"], rule["value"], metric=name),
        }
        for name, rule in gate_rules.items()
    ]
    failed = [item["gate"] for item in gates if not item["passed"]]
    value.update(
        accepted_signal_count=len(trades),
        metrics=metrics,
        diagnostics=diagnostics,
        gates=gates,
        failed_gates=failed,
        disposition="fail" if failed else "pass",
    )
    return value


def build_envelope(request: dict) -> dict:
    if request.get("stage") != "development":
        raise ValueError("Development runner 收到非 Development request")
    prereg = request["preregistration"]
    inputs = request["trial_inputs"]
    source_bundle = request["source_bundle"]
    tsm, soxx = _load_assets(request)
    controls = inputs["date_controls"]
    signal_start, signal_end = controls["signal_start"], controls["signal_end"]

    candidate_base = engine.combined_backtest(
        tsm, soxx, cost=engine.BASE_COST, signal_start=signal_start, signal_end=signal_end
    )
    candidate_stress = engine.combined_backtest(
        tsm, soxx, cost=engine.STRESS_COST, signal_start=signal_start, signal_end=signal_end
    )
    baseline_base = engine.baseline_trades(
        tsm, cost=engine.BASE_COST, signal_start=signal_start, signal_end=signal_end
    )
    baseline_stress = engine.baseline_trades(
        tsm, cost=engine.STRESS_COST, signal_start=signal_start, signal_end=signal_end
    )
    candidate_rows = engine.serialize_trade_pair(candidate_base, candidate_stress, candidate=True)
    baseline_rows = engine.serialize_trade_pair(baseline_base, baseline_stress, candidate=False)

    source_digest = canonical_digest(source_bundle)
    prereg_digest = canonical_digest(prereg)
    inputs_digest = canonical_digest(inputs)
    asset_digest = canonical_digest(inputs["data_bindings"]["assets"])
    expected_bindings = {
        "source_bundle_digest": source_digest,
        "preregistration_digest": prereg_digest,
        "trial_inputs_digest": inputs_digest,
        "data_assets_digest": asset_digest,
    }
    for field, expected in (
        ("source_bundle_digest", source_digest),
        ("preregistration_digest", prereg_digest),
    ):
        if inputs.get(field) != expected:
            raise ValueError(f"Development inputs 的 {field} 不一致")

    baseline_id = prereg["baseline_definition"]["baseline_id"]
    return {
        "candidate": _development_evidence(
            candidate_rows,
            candidate_id=inputs["candidate_id"],
            bindings=expected_bindings,
            preregistration=prereg,
        ),
        "baseline": _development_evidence(
            baseline_rows,
            candidate_id=baseline_id,
            bindings=expected_bindings,
            preregistration=prereg,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = load_canonical(args.request)
    envelope = build_envelope(request)
    atomic_create(args.output, canonical_bytes(envelope))


if __name__ == "__main__":
    main()
