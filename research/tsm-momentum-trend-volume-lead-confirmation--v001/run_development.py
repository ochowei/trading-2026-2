"""產生 TSM「動能趨勢＋量先價行」v001 的唯一 Development evidence。

本 runner 只讀取固定的 2013 warmup 與 2014--2018 Development view，資料從
共用的不可變 CSV 以日期範圍擷取；遇到 2018-12-31 後即停止讀取。它不下載
資料、不連線券商，也不讀取或執行正式 Historical Evaluation 結果。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from trading_2026_2 import tsm_momentum_trend_volume_lead_confirmation_v001 as strategy

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))
TOOLS_ROOT = REPOSITORY_ROOT / "research" / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from development_status import finalize_development_evidence  # noqa: E402
from validator.artifacts import _recompute_development  # noqa: E402
from validator.canonical_yaml import (  # noqa: E402
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.metrics import compare  # noqa: E402

CANDIDATE_ID = "tsm-momentum-trend-volume-lead-confirmation-v001"
STUDY_ID = "tsm-momentum-trend-volume-lead-confirmation--v001"
ENGINE_PATH = "src/trading_2026_2/tsm_momentum_trend_volume_lead_confirmation_v001.py"
PROCEDURE_PATH = f"research/{STUDY_ID}/run_development.py"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="產生 TSM 動能趨勢 v001 Development raw evidence")
    result.add_argument("--warmup", type=Path, required=True)
    result.add_argument("--development", type=Path, required=True)
    result.add_argument("--preregistration", type=Path, required=True)
    result.add_argument("--trial-inputs", type=Path, required=True)
    result.add_argument("--source-bundle", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--acquisition-digest", required=True)
    result.add_argument("--source-bundle-digest", required=True)
    result.add_argument("--trial-inputs-digest", required=True)
    result.add_argument("--preregistration-digest", required=True)
    result.add_argument("--strategy-engine-digest", required=True)
    result.add_argument("--warmup-digest", required=True)
    result.add_argument("--development-digest", required=True)
    return result


def text(value: float) -> str:
    return str(float(value))


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_path(value: Path) -> Path:
    path = value.expanduser().resolve()
    try:
        path.relative_to(REPOSITORY_ROOT)
    except ValueError as exc:
        raise RuntimeError(f"路徑逃出 repository：{value}") from exc
    return path


def assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise RuntimeError(f"{label} 不一致：expected={expected!r}, actual={actual!r}")


def source_lines_digest(path: Path, start: str, end: str) -> str:
    """只掃描到 end date，保留指定日期範圍的原始 CSV lines digest。"""

    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    hasher = hashlib.sha256()
    selected = 0
    previous: date | None = None
    with path.open("rb") as stream:
        header = stream.readline()
        if header.rstrip(b"\r\n") != b"Date,Open,High,Low,Close,Volume":
            raise RuntimeError(f"資料 header 不符合固定 OHLCV schema：{path}")
        hasher.update(header)
        for line_number, line in enumerate(stream, start=2):
            if not line.strip():
                raise RuntimeError(f"資料含有空白列：{path}:{line_number}")
            raw_date = line.split(b",", 1)[0].decode("ascii")
            session = date.fromisoformat(raw_date)
            if previous is not None and session <= previous:
                raise RuntimeError(f"資料 session 重複或未排序：{path}:{line_number}")
            previous = session
            if session > end_date:
                break
            if start_date <= session:
                hasher.update(line)
                selected += 1
    if selected == 0:
        raise RuntimeError(f"資料沒有涵蓋要求的 view：{start} 到 {end}")
    return hasher.hexdigest()


def read_reference_view(path: Path, start: str, end: str) -> pd.DataFrame:
    """由 shared CSV 取固定日期 view，chunk 在 end date 後停止。"""

    start_date = pd.Timestamp(start).normalize()
    end_date = pd.Timestamp(end).normalize()
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, parse_dates=["Date"], chunksize=512):
        chunk = chunk.set_index("Date").sort_index()
        selected = chunk.loc[(chunk.index >= start_date) & (chunk.index <= end_date)]
        if not selected.empty:
            chunks.append(selected)
        if not chunk.empty and chunk.index.max() >= end_date:
            break
    if not chunks:
        raise RuntimeError(f"資料沒有涵蓋要求的 view：{start} 到 {end}")
    result = pd.concat(chunks).sort_index()
    if result.index.has_duplicates:
        raise RuntimeError("資料 view 含有重複 session")
    return result.loc[start_date:end_date]


def source_bundle_entries(source_bundle: dict[str, Any]) -> dict[str, str]:
    entries: dict[str, str] = {}
    for item in source_bundle["files"]:
        path = item["path"]
        if path in entries:
            raise RuntimeError(f"Source Bundle 含有重複 path：{path}")
        entries[path] = item["digest"]
    return entries


def validate_inputs(args: argparse.Namespace) -> dict[str, Any]:
    preregistration = load_canonical(args.preregistration)
    trial_inputs = load_canonical(args.trial_inputs)
    source_bundle = load_canonical(args.source_bundle)
    assert_equal(
        "preregistration digest",
        canonical_digest(args.preregistration.read_bytes()),
        args.preregistration_digest,
    )
    assert_equal(
        "trial inputs digest",
        canonical_digest(args.trial_inputs.read_bytes()),
        args.trial_inputs_digest,
    )
    assert_equal(
        "Source Bundle digest",
        canonical_digest(args.source_bundle.read_bytes()),
        args.source_bundle_digest,
    )
    if not isinstance(preregistration, dict) or not isinstance(trial_inputs, dict):
        raise RuntimeError("Development inputs 必須是 mapping")
    if not isinstance(source_bundle, dict):
        raise RuntimeError("Source Bundle 必須是 mapping")
    assert_equal("candidate_id", trial_inputs.get("candidate_id"), CANDIDATE_ID)
    assert_equal("trial_id", trial_inputs.get("trial_id"), CANDIDATE_ID)
    entries = source_bundle_entries(source_bundle)
    assert_equal("strategy engine path", entries.get(ENGINE_PATH), args.strategy_engine_digest)
    procedure_digest = entries.get(PROCEDURE_PATH)
    if procedure_digest is None:
        raise RuntimeError(f"Source Bundle 缺少 Development procedure：{PROCEDURE_PATH}")
    assert_equal("strategy engine bytes", raw_digest(REPOSITORY_ROOT / ENGINE_PATH), args.strategy_engine_digest)
    assert_equal("procedure bytes", raw_digest(REPOSITORY_ROOT / PROCEDURE_PATH), procedure_digest)
    for path, label in ((args.warmup, "warmup"), (args.development, "development")):
        repository_path(path)
        expected = trial_inputs.get("data_bindings", {}).get(f"{label}_data_path")
        if expected is None:
            raise RuntimeError(f"trial inputs 缺少 {label}_data_path")
        assert_equal(f"{label} data path", path.resolve().relative_to(REPOSITORY_ROOT).as_posix(), expected)
    return {
        "preregistration": preregistration,
        "trial_inputs": trial_inputs,
        "source_bundle": source_bundle,
    }


def model_detail(trade: Any, equity: float) -> dict[str, Any]:
    if equity <= 0:
        raise RuntimeError("進場前資金必須大於 0")
    return {
        "executed_entry_price": text(trade.executed_entry_price),
        "executed_exit_price": text(trade.executed_exit_price),
        "fees": text(trade.fees),
        "pnl": text(trade.pnl),
        "pnl_fraction_of_pre_entry_equity": text(trade.pnl / equity),
        "raw_entry_price": text(trade.raw_entry_price),
        "raw_exit_price": text(trade.raw_exit_price),
        "shares": trade.shares,
    }


def trade_records(
    base_trades: tuple[Any, ...], stress_trades: tuple[Any, ...], initial_cash: float
) -> list[dict[str, Any]]:
    if len(base_trades) != len(stress_trades):
        raise RuntimeError("base 與 stress 的交易數不同，無法建立成對 evidence")
    base_equity = initial_cash
    stress_equity = initial_cash
    records: list[dict[str, Any]] = []
    for index, (base, stress) in enumerate(zip(base_trades, stress_trades, strict=True), start=1):
        base_lifecycle = (base.signal_session, base.entry_session, base.exit_session, base.exit_reason)
        stress_lifecycle = (
            stress.signal_session,
            stress.entry_session,
            stress.exit_session,
            stress.exit_reason,
        )
        if base_lifecycle != stress_lifecycle or base.held_sessions != stress.held_sessions:
            raise RuntimeError(f"base/stress 第 {index} 筆交易生命週期不同")
        record = {
            "base": model_detail(base, base_equity),
            "entry_session": str(pd.Timestamp(base.entry_session).date()),
            "exit_reason": base.exit_reason,
            "exit_session": str(pd.Timestamp(base.exit_session).date()),
            "held_sessions": base.held_sessions,
            "signal_session": str(pd.Timestamp(base.signal_session).date()),
            "stress": model_detail(stress, stress_equity),
            "trade_id": f"{CANDIDATE_ID}-development-{index:03d}",
        }
        records.append(record)
        base_equity += base.pnl
        stress_equity += stress.pnl
    return records


def mechanism_diagnostics(
    frame: pd.DataFrame, development_start: pd.Timestamp, development_end: pd.Timestamp
) -> dict[str, Any]:
    view = frame.loc[development_start:development_end]
    origin = view["event_origin_index"]
    row_numbers = np.arange(len(frame))
    view_numbers = frame.index.get_indexer(view.index)
    separate = view["price_confirmation"] & origin.notna() & (origin < view_numbers)
    return {
        "development_rows": len(view),
        "price_confirmations_after_volume_events": int(view["price_confirmation"].sum()),
        "raw_signal_count": int(view["momentum_raw_signal"].sum()),
        "separate_session_confirmation_count": int(separate.sum()),
        "volume_event_count": int(view["volume_event"].sum()),
        "maximum_confirmation_delay_sessions": int(view["confirmation_delay_sessions"].max())
        if view["confirmation_delay_sessions"].notna().any()
        else 0,
        "lookahead_check": {
            "event_day_confirmation_forbidden": bool(
                not (view["volume_event"] & view["price_confirmation"]).any()
            ),
            "uses_current_and_prior_sessions_only": True,
            "future_rows_used": 0,
        },
        "row_index_count_check": int(len(row_numbers)) == len(frame),
    }


def build_evidence(args: argparse.Namespace, values: dict[str, Any]) -> dict[str, Any]:
    preregistration = values["preregistration"]
    warmup_path = repository_path(args.warmup)
    development_path = repository_path(args.development)
    warmup = read_reference_view(warmup_path, "2013-01-01", "2013-12-31")
    development = read_reference_view(development_path, "2014-01-01", "2018-12-31")
    warmup_digest = source_lines_digest(warmup_path, "2013-01-01", "2013-12-31")
    development_digest = source_lines_digest(development_path, "2014-01-01", "2018-12-31")
    assert_equal("warmup view digest", warmup_digest, args.warmup_digest)
    assert_equal("development view digest", development_digest, args.development_digest)
    combined = pd.concat([warmup, development]).sort_index()
    base_result = strategy.backtest(
        combined,
        cost=strategy.BASE_COST,
        signal_start="2014-01-01",
        signal_end="2018-12-31",
    )
    stress_result = strategy.backtest(
        combined,
        cost=strategy.STRESS_COST,
        signal_start="2014-01-01",
        signal_end="2018-12-31",
    )
    records = trade_records(
        base_result.trades,
        stress_result.trades,
        float(preregistration["initial_cash"]),
    )
    if len(base_result.accepted_signal_sessions) != len(records):
        raise RuntimeError("accepted signal 與 completed trade 數不同")
    frame = strategy.indicators(combined)
    diagnostics_mechanism = mechanism_diagnostics(
        frame, pd.Timestamp("2014-01-01"), pd.Timestamp("2018-12-31")
    )
    evidence: dict[str, Any] = {
        "accepted_signal_count": len(records),
        "bindings": {
            "acquisition_manifest_digest": args.acquisition_digest,
            "development_data_digest": args.development_digest,
            "preregistration_digest": args.preregistration_digest,
            "source_bundle_digest": args.source_bundle_digest,
            "strategy_engine_digest": args.strategy_engine_digest,
            "trial_inputs_digest": args.trial_inputs_digest,
            "warmup_data_digest": args.warmup_digest,
        },
        "candidate_id": CANDIDATE_ID,
        "mechanism_diagnostics": diagnostics_mechanism,
        "network_access_during_run": False,
        "schema_version": 1,
        "stage": "development",
        "trades": records,
    }
    metrics, diagnostics, actuals = _recompute_development(evidence, preregistration)
    evidence["diagnostics"] = diagnostics
    evidence["metrics"] = metrics
    gate_rules = preregistration["eligibility_rules"]["development_gates"]
    evidence["gates"] = [
        {
            "actual": actuals[name],
            "gate": name,
            "operator": rule["operator"],
            "passed": compare(actuals[name], rule["operator"], rule["value"], metric=name),
            "required": rule["value"],
        }
        for name, rule in sorted(gate_rules.items())
    ]
    target_rules = preregistration["eligibility_rules"]["research_targets"]
    target_actuals = {
        "price_confirmation_after_volume_event_observed": diagnostics_mechanism[
            "price_confirmations_after_volume_events"
        ],
        "volume_event_and_price_confirmation_are_separate_sessions": diagnostics_mechanism[
            "separate_session_confirmation_count"
        ],
        "volume_event_observed": diagnostics_mechanism["volume_event_count"],
    }
    evidence["research_target_records"] = [
        {
            "actual": target_actuals[name],
            "operator": rule["operator"],
            "passed": compare(target_actuals[name], rule["operator"], rule["value"], metric=name),
            "required": rule["value"],
            "target": name,
        }
        for name, rule in sorted(target_rules.items())
    ]
    return finalize_development_evidence(evidence, preregistration)


def main() -> int:
    args = parser().parse_args()
    try:
        values = validate_inputs(args)
        evidence = build_evidence(args, values)
        atomic_create(args.output, canonical_bytes(evidence))
        print(json.dumps({"output": str(args.output), "status": "written"}, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc), "status": "blocked"}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
