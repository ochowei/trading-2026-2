"""產生 TSM v021 唯一一次 Development evidence。

本 runner 只讀取 2013 warmup 與 2014--2018 Development view，並把 v009
Development 的完整精度作為事前固定 control。它不接受臨時參數、不下載資料，
也不讀取 Historical Evaluation 結果；所有比較口徑在結果查看前已寫入
preregistration。
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from trading_2026_2 import tsm_mean_reversion_two_stage_volume_atr_distance_v021 as v021
from trading_2026_2 import tsm_mean_reversion_two_stage_volume_reversal_v009 as v009
from trading_2026_2.tsm_mean_reversion_two_stage_volume_atr_distance_v021 import (
    BASE_COST,
    BASELINE_SPEC,
    DEFAULT_SPEC,
    STRESS_COST,
    V009_ONLY_SPEC,
    Trade,
    backtest,
    mark_to_market_drawdown,
    qualification_metrics,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))
TOOLS_ROOT = REPOSITORY_ROOT / "research" / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from development_status import finalize_development_evidence  # noqa: E402
from validator.canonical_yaml import atomic_create, canonical_bytes, load_canonical  # noqa: E402

CANDIDATE_ID = "tsm-mr-two-stage-volume-atr-distance-v021"
BASELINE_ID = "tsm-mean-reversion-two-stage-baseline-v009"
V009_ID = "tsm-mr-two-stage-calibrated-volume-v009"
STUDY_ID = "tsm-mean-reversion-two-stage-volume-reversal--v021"
ENGINE_PATH = "src/trading_2026_2/tsm_mean_reversion_two_stage_volume_atr_distance_v021.py"
PROCEDURE_PATH = f"research/{STUDY_ID}/run_development.py"
ACQUISITION_PATH = f"research/{STUDY_ID}/data-snapshot-acquisition.yml"
COMPARISON_PATH = f"research/{STUDY_ID}/comparison-control-development.yml"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="產生 TSM v021 Development raw evidence")
    result.add_argument("--warmup", type=Path, required=True)
    result.add_argument("--development", type=Path, required=True)
    result.add_argument("--preregistration", type=Path, required=True)
    result.add_argument("--trial-inputs", type=Path, required=True)
    result.add_argument("--comparison-control", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--acquisition-digest", required=True)
    result.add_argument("--comparison-control-digest", required=True)
    result.add_argument("--source-bundle-digest", required=True)
    result.add_argument("--strategy-engine-digest", required=True)
    result.add_argument("--trial-inputs-digest", required=True)
    result.add_argument("--preregistration-digest", required=True)
    result.add_argument("--warmup-digest", required=True)
    result.add_argument("--development-digest", required=True)
    return result


def text(value: float) -> str:
    return str(float(value))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_path(relative_path: str) -> Path:
    path = (REPOSITORY_ROOT / relative_path).resolve()
    try:
        path.relative_to(REPOSITORY_ROOT)
    except ValueError as exc:
        raise RuntimeError(f"路徑逃出 repository: {relative_path}") from exc
    return path


def source_lines_digest(path: Path, start: str, end: str) -> str:
    """保留原始 CSV bytes，計算指定日期 view 的 digest。"""

    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    hasher = hashlib.sha256()
    selected = 0
    previous: date | None = None
    with path.open("rb") as stream:
        header = stream.readline()
        if header.rstrip(b"\r\n") != b"Date,Open,High,Low,Close,Volume":
            raise RuntimeError(f"資料 header 不符合固定 OHLCV schema: {path}")
        hasher.update(header)
        for line_number, line in enumerate(stream, start=2):
            if not line.strip():
                raise RuntimeError(f"資料含有空白列: {path}:{line_number}")
            raw_date = line.split(b",", 1)[0].decode("ascii")
            session = date.fromisoformat(raw_date)
            if previous is not None and session <= previous:
                raise RuntimeError(f"資料 session 重複或未排序: {path}:{line_number}")
            previous = session
            if start_date <= session <= end_date:
                hasher.update(line)
                selected += 1
    if selected == 0:
        raise RuntimeError(f"資料沒有涵蓋要求的 view: {start} 到 {end}")
    return hasher.hexdigest()


def read_reference_view(path: Path, start: str, end: str) -> pd.DataFrame:
    """從同一份 content-addressed CSV 取固定日期 view。"""

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
        raise RuntimeError(f"資料沒有涵蓋要求的 view: {start} 到 {end}")
    result = pd.concat(chunks).sort_index()
    if result.index.has_duplicates:
        raise RuntimeError("資料 view 含有重複 session")
    return result.loc[start_date:end_date]


def source_bundle_entries(source_bundle: dict[str, Any]) -> dict[str, str]:
    entries: dict[str, str] = {}
    for item in source_bundle["files"]:
        if item["path"] in entries:
            raise RuntimeError(f"Source Bundle 含有重複 path: {item['path']}")
        entries[item["path"]] = item["digest"]
    return entries


def assert_equal(label: str, actual: str, expected: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label} digest 不一致: expected={expected}, actual={actual}")


def lifecycle(trade: Any) -> tuple[Any, ...]:
    return (
        trade.signal_session,
        trade.entry_session,
        trade.exit_session,
        trade.exit_reason,
    )


def trade_rates(trades: tuple[Trade, ...], initial_cash: float) -> np.ndarray:
    equity = initial_cash
    rates: list[float] = []
    for trade in trades:
        rates.append(trade.pnl / equity)
        equity += trade.pnl
    return np.asarray(rates)


def path_metrics(rates: np.ndarray, initial_cash: float) -> dict[str, float]:
    equity = initial_cash
    peak = equity
    gross_profit = 0.0
    gross_loss = 0.0
    maximum_drawdown = 0.0
    for rate in rates:
        pnl = equity * float(rate)
        if pnl > 0:
            gross_profit += pnl
        elif pnl < 0:
            gross_loss -= pnl
        equity += pnl
        peak = max(peak, equity)
        maximum_drawdown = max(maximum_drawdown, (peak - equity) / peak)
    return {
        "return": equity / initial_cash - 1.0,
        "profit_factor": gross_profit / gross_loss if gross_loss else float("inf"),
        "maximum_drawdown": maximum_drawdown,
    }


def bootstrap(
    rates: np.ndarray,
    block_length: int,
    *,
    repetitions: int,
    seed: int,
) -> dict[str, object]:
    """每個 block length 都直接使用同一個事前登記 seed。"""

    if len(rates) == 0:
        raise RuntimeError("Development bootstrap 至少需要一筆交易")
    rng = np.random.default_rng(seed)
    count = len(rates)
    blocks = (count + block_length - 1) // block_length
    starts = rng.integers(0, count, size=(repetitions, blocks))
    offsets = np.arange(block_length)
    indexes = ((starts[:, :, None] + offsets) % count).reshape(repetitions, -1)
    sampled = rates[indexes[:, :count]]
    equity = np.full(repetitions, 100_000.0)
    peak = equity.copy()
    gross_profit = np.zeros(repetitions)
    gross_loss = np.zeros(repetitions)
    maximum_drawdown = np.zeros(repetitions)
    for column in range(count):
        pnl = equity * sampled[:, column]
        gross_profit += np.where(pnl > 0, pnl, 0.0)
        gross_loss += np.where(pnl < 0, -pnl, 0.0)
        equity += pnl
        peak = np.maximum(peak, equity)
        maximum_drawdown = np.maximum(maximum_drawdown, (peak - equity) / peak)
    returns = equity / 100_000.0 - 1.0
    profit_factors = np.divide(
        gross_profit,
        gross_loss,
        out=np.full(repetitions, np.inf),
        where=gross_loss != 0,
    )
    return {
        "block_length": block_length,
        "repetitions": repetitions,
        "seed": seed,
        "return_q05_q50_q95": [text(value) for value in np.quantile(returns, [0.05, 0.5, 0.95])],
        "profit_factor_q05_q50_q95": [text(value) for value in np.quantile(profit_factors, [0.05, 0.5, 0.95])],
        "maximum_drawdown_q05_q50_q95": [text(value) for value in np.quantile(maximum_drawdown, [0.05, 0.5, 0.95])],
        "positive_return_ratio": text(np.mean(returns > 0)),
        "profit_factor_above_one_ratio": text(np.mean(profit_factors > 1)),
        "drawdown_above_10pct_ratio": text(np.mean(maximum_drawdown > 0.10)),
    }


def leave_one_signal_year_out(
    trades: tuple[Trade, ...], *, initial_cash: float
) -> dict[str, dict[str, str | int]]:
    rates = trade_rates(trades, initial_cash)
    years = np.asarray([trade.signal_session.year for trade in trades])
    result: dict[str, dict[str, str | int]] = {}
    for year in sorted(set(years)):
        values = path_metrics(rates[years != year], initial_cash)
        result[str(year)] = {
            "omitted_trades": int(np.sum(years == year)),
            "remaining_trades": int(np.sum(years != year)),
            "return": text(values["return"]),
            "profit_factor": text(values["profit_factor"]),
            "maximum_drawdown": text(values["maximum_drawdown"]),
        }
    return result


def maximum_loss_fraction(trades: tuple[Trade, ...], *, initial_cash: float) -> float:
    rates = trade_rates(trades, initial_cash)
    return max((float(-rate) for rate in rates if rate < 0), default=0.0)


def paired_trade_map(
    base_trades: tuple[Any, ...], stress_trades: tuple[Any, ...], label: str
) -> dict[tuple[Any, ...], tuple[Any, Any]]:
    base = {lifecycle(trade): trade for trade in base_trades}
    stress = {lifecycle(trade): trade for trade in stress_trades}
    if len(base) != len(base_trades) or len(stress) != len(stress_trades):
        raise RuntimeError(f"{label} 含有重複交易生命週期")
    if set(base) != set(stress):
        raise RuntimeError(f"{label} base 與 stress 的交易生命週期不一致")
    return {key: (base[key], stress[key]) for key in base}


def trade_identity(prefix: str, key: tuple[Any, ...]) -> str:
    return f"{prefix}-{key[0].date()}-{key[1].date()}-{key[2].date()}-{key[3]}"


def trade_row(
    key: tuple[Any, ...], pair: tuple[Any, Any], *, classification: str
) -> dict[str, object]:
    base_trade, stress_trade = pair
    prefix = "candidate" if classification in {"retained", "truly_added"} else "control"
    return {
        "trade_id": trade_identity(prefix, key),
        "classification": classification,
        "signal_session": str(key[0].date()),
        "entry_session": str(key[1].date()),
        "exit_session": str(key[2].date()),
        "exit_reason": key[3],
        "base_pnl": text(base_trade.pnl),
        "stress_pnl": text(stress_trade.pnl),
    }


def trade_comparison(
    candidate_base: tuple[Trade, ...],
    candidate_stress: tuple[Trade, ...],
    control_base: tuple[Any, ...],
    control_stress: tuple[Any, ...],
    development_sessions: pd.DatetimeIndex,
    cooldown_sessions: int,
) -> dict[str, object]:
    candidate = paired_trade_map(candidate_base, candidate_stress, "candidate")
    control = paired_trade_map(control_base, control_stress, "v009 control")
    retained_keys = sorted(set(candidate) & set(control))
    added_keys = sorted(set(candidate) - set(control))
    control_only_keys = sorted(set(control) - set(candidate))
    session_numbers = {session: number for number, session in enumerate(development_sessions)}

    def number(session: pd.Timestamp) -> int:
        if session not in session_numbers:
            raise RuntimeError(f"交易 session 不在固定 Development calendar: {session}")
        return session_numbers[session]

    added_rows = [trade_row(key, candidate[key], classification="truly_added") for key in added_keys]
    retained_rows = [trade_row(key, candidate[key], classification="retained") for key in retained_keys]
    unmatched = set(control_only_keys)
    pairings: list[dict[str, object]] = []
    for key in added_keys:
        eligible = [
            control_key
            for control_key in sorted(unmatched)
            if number(key[0]) < number(control_key[0]) <= number(key[2]) + cooldown_sessions
        ]
        if eligible:
            displaced = eligible[0]
            unmatched.remove(displaced)
            pairings.append(
                {
                    "candidate_trade_id": trade_identity("candidate", key),
                    "control_trade_id": trade_identity("control", displaced),
                    "candidate_signal_session": str(key[0].date()),
                    "control_signal_session": str(displaced[0].date()),
                    "reason": "control_signal_falls_during_candidate_holding_or_post_exit_cooldown",
                }
            )
    paired_control_keys = {
        next(key for key in control_only_keys if trade_identity("control", key) == item["control_trade_id"])
        for item in pairings
    }
    displaced_rows = [
        trade_row(key, control[key], classification="v009_only_displaced")
        for key in sorted(paired_control_keys)
    ]
    unpaired_rows = [
        trade_row(key, control[key], classification="v009_only_unpaired")
        for key in control_only_keys
        if key not in paired_control_keys
    ]
    retained_base_delta = sum(candidate[key][0].pnl - control[key][0].pnl for key in retained_keys)
    retained_stress_delta = sum(candidate[key][1].pnl - control[key][1].pnl for key in retained_keys)
    added_base = sum(float(row["base_pnl"]) for row in added_rows)
    added_stress = sum(float(row["stress_pnl"]) for row in added_rows)
    all_control_base = sum(control[key][0].pnl for key in control_only_keys)
    all_control_stress = sum(control[key][1].pnl for key in control_only_keys)
    displaced_base = sum(float(row["base_pnl"]) for row in displaced_rows)
    displaced_stress = sum(float(row["stress_pnl"]) for row in displaced_rows)
    net_base = added_base + retained_base_delta - all_control_base
    net_stress = added_stress + retained_stress_delta - all_control_stress

    annual: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {
            "candidate_only_trades": 0,
            "retained_trades": 0,
            "v009_only_trades": 0,
            "candidate_only_base_pnl": 0.0,
            "candidate_only_stress_pnl": 0.0,
            "retained_base_pnl_delta": 0.0,
            "retained_stress_pnl_delta": 0.0,
            "v009_only_base_pnl": 0.0,
            "v009_only_stress_pnl": 0.0,
        }
    )
    for key in added_keys:
        year = str(key[0].year)
        annual[year]["candidate_only_trades"] += 1
        annual[year]["candidate_only_base_pnl"] += candidate[key][0].pnl
        annual[year]["candidate_only_stress_pnl"] += candidate[key][1].pnl
    for key in retained_keys:
        year = str(key[0].year)
        annual[year]["retained_trades"] += 1
        annual[year]["retained_base_pnl_delta"] += candidate[key][0].pnl - control[key][0].pnl
        annual[year]["retained_stress_pnl_delta"] += candidate[key][1].pnl - control[key][1].pnl
    for key in control_only_keys:
        year = str(key[0].year)
        annual[year]["v009_only_trades"] += 1
        annual[year]["v009_only_base_pnl"] += control[key][0].pnl
        annual[year]["v009_only_stress_pnl"] += control[key][1].pnl
    annual_output: dict[str, dict[str, object]] = {}
    for year, values in sorted(annual.items()):
        annual_output[year] = {
            "candidate_only_trades": int(values["candidate_only_trades"]),
            "retained_trades": int(values["retained_trades"]),
            "v009_only_trades": int(values["v009_only_trades"]),
            "candidate_only_base_pnl": text(float(values["candidate_only_base_pnl"])),
            "candidate_only_stress_pnl": text(float(values["candidate_only_stress_pnl"])),
            "retained_base_pnl_delta": text(float(values["retained_base_pnl_delta"])),
            "retained_stress_pnl_delta": text(float(values["retained_stress_pnl_delta"])),
            "v009_only_base_pnl": text(float(values["v009_only_base_pnl"])),
            "v009_only_stress_pnl": text(float(values["v009_only_stress_pnl"])),
            "net_base_pnl": text(float(values["candidate_only_base_pnl"] + values["retained_base_pnl_delta"] - values["v009_only_base_pnl"])),
            "net_stress_pnl": text(float(values["candidate_only_stress_pnl"] + values["retained_stress_pnl_delta"] - values["v009_only_stress_pnl"])),
        }
    leave_out_stress: dict[str, str] = {}
    for year in sorted(annual_output):
        leave_out_stress[year] = text(
            sum(
                float(values["net_stress_pnl"])
                for other_year, values in annual_output.items()
                if other_year != year
            )
        )
    net_stress_years = sum(float(values["net_stress_pnl"]) > 0 for values in annual_output.values())
    return {
        "matching_method": "exact-lifecycle-key-then-pre-registered-temporal-pairing",
        "lifecycle_key_fields": ["signal_session", "entry_session", "exit_session", "exit_reason"],
        "candidate_trade_count": len(candidate),
        "v009_trade_count": len(control),
        "retained_trade_count": len(retained_rows),
        "truly_added_trade_count": len(added_rows),
        "v009_only_displaced_trade_count": len(displaced_rows),
        "v009_only_unpaired_trade_count": len(unpaired_rows),
        "retained": retained_rows,
        "truly_added": added_rows,
        "v009_only_displaced": displaced_rows,
        "v009_only_unpaired": unpaired_rows,
        "pairings": pairings,
        "truly_added_aggregate_pnl": {"base": text(added_base), "stress": text(added_stress)},
        "paired_displaced_aggregate_pnl": {"base": text(displaced_base), "stress": text(displaced_stress)},
        "retained_pnl_delta_after_equity_or_timing_change": {"base": text(retained_base_delta), "stress": text(retained_stress_delta)},
        "all_control_only_aggregate_pnl": {
            "base": text(all_control_base),
            "stress": text(all_control_stress),
            "definition": "所有未在 candidate 完成相同生命週期的 v009 completed trade 均保守視為被替換或時點改變，不因無法時間配對而忽略。",
        },
        "net_new_minus_replaced": {
            "base": text(net_base),
            "stress": text(net_stress),
            "base_strictly_positive": net_base > 0,
            "stress_strictly_positive": net_stress > 0,
            "formula": "candidate-only completed PnL + retained candidate/control PnL delta - all v009-only completed PnL",
        },
        "net_new_minus_displaced": {
            "base": text(added_base + retained_base_delta - displaced_base),
            "stress": text(added_stress + retained_stress_delta - displaced_stress),
            "base_strictly_positive": added_base + retained_base_delta - displaced_base > 0,
            "stress_strictly_positive": added_stress + retained_stress_delta - displaced_stress > 0,
            "formula": "candidate-only completed PnL + retained candidate/control PnL delta - temporally paired v009-only PnL",
            "eligibility_definition": "研究目標採保守口徑；所有 v009-only completed trade 均納入 net_new_minus_replaced，temporally displaced 僅供解釋。",
        },
        "annual_net_increment": annual_output,
        "net_increment_positive_signal_years": int(net_stress_years),
        "leave_one_signal_year_out_net_stress_pnl": leave_out_stress,
        "minimum_leave_one_signal_year_out_net_stress_pnl": text(
            min((float(value) for value in leave_out_stress.values()), default=0.0)
        ),
    }


def compare(actual: str | int | float, operator: str, required: str | int | float) -> bool:
    if operator == "equals":
        return actual == required
    left = Decimal(str(actual))
    right = Decimal(str(required))
    return {">": left > right, ">=": left >= right, "<": left < right, "<=": left <= right}[operator]


def gate_records(
    actuals: dict[str, str | int | float], rules: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    if set(actuals) != set(rules):
        raise RuntimeError("Development actuals 與 preregistered gates 不一致")
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    for name, rule in rules.items():
        actual = actuals[name]
        passed = compare(actual, rule["operator"], rule["value"])
        records.append(
            {
                "gate": name,
                "actual": actual if isinstance(actual, int) else text(float(actual)),
                "operator": rule["operator"],
                "required": rule["value"],
                "passed": passed,
            }
        )
        if not passed:
            failures.append(name)
    return records, failures


def metric_summary(engine: Any, bars: pd.DataFrame, spec: Any, initial_cash: float) -> dict[str, object]:
    args = {"signal_start": "2014-01-01", "signal_end": "2018-12-31", "spec": spec}
    base = engine.backtest(bars, cost=engine.BASE_COST, **args)
    stress = engine.backtest(bars, cost=engine.STRESS_COST, **args)
    if [lifecycle(trade) for trade in base.trades] != [lifecycle(trade) for trade in stress.trades]:
        raise RuntimeError("比較摘要的 base 與 stress 交易生命週期不一致")
    return {
        "accepted_signal_count": len(base.accepted_signal_sessions),
        "base": {key: text(value) if isinstance(value, float) else value for key, value in engine.qualification_metrics(base, initial_cash=initial_cash).items()},
        "stress": {key: text(value) if isinstance(value, float) else value for key, value in engine.qualification_metrics(stress, initial_cash=initial_cash).items()},
    }


def trade_record(index: int, base_trade: Trade, stress_trade: Trade, base_rate: float, stress_rate: float) -> dict[str, object]:
    if lifecycle(base_trade) != lifecycle(stress_trade):
        raise RuntimeError("candidate base 與 stress 交易生命週期不一致")
    return {
        "trade_id": f"development-{index:03d}",
        "signal_session": str(base_trade.signal_session.date()),
        "entry_session": str(base_trade.entry_session.date()),
        "exit_session": str(base_trade.exit_session.date()),
        "raw_entry_price": text(base_trade.raw_entry_price),
        "raw_exit_price": text(base_trade.raw_exit_price),
        "exit_reason": base_trade.exit_reason,
        "held_sessions": base_trade.held_sessions,
        "entry_mode": base_trade.signal_origin,
        "base": {
            "executed_entry_price": text(base_trade.executed_entry_price),
            "executed_exit_price": text(base_trade.executed_exit_price),
            "shares": base_trade.shares,
            "fees": text(base_trade.fees),
            "pnl": text(base_trade.pnl),
            "pnl_fraction_of_pre_entry_equity": text(base_rate),
        },
        "stress": {
            "executed_entry_price": text(stress_trade.executed_entry_price),
            "executed_exit_price": text(stress_trade.executed_exit_price),
            "shares": stress_trade.shares,
            "fees": text(stress_trade.fees),
            "pnl": text(stress_trade.pnl),
            "pnl_fraction_of_pre_entry_equity": text(stress_rate),
        },
    }


def validate_inputs(args: argparse.Namespace, preregistration: dict[str, Any], inputs: dict[str, Any]) -> dict[str, str]:
    source_bundle_path = args.trial_inputs.parent / "source-bundle.yml"
    acquisition_path = args.trial_inputs.parent / "data-snapshot-acquisition.yml"
    source_bundle = load_canonical(source_bundle_path)
    acquisition = load_canonical(acquisition_path)
    comparison = load_canonical(args.comparison_control)
    source_bundle_digest = digest(source_bundle_path)
    acquisition_digest = digest(acquisition_path)
    comparison_digest = digest(args.comparison_control)
    preregistration_digest = digest(args.preregistration)
    trial_inputs_digest = digest(args.trial_inputs)
    assert_equal("Source Bundle", args.source_bundle_digest, source_bundle_digest)
    assert_equal("acquisition manifest", args.acquisition_digest, acquisition_digest)
    assert_equal("comparison control", args.comparison_control_digest, comparison_digest)
    assert_equal("preregistration", args.preregistration_digest, preregistration_digest)
    assert_equal("trial inputs", args.trial_inputs_digest, trial_inputs_digest)

    entries = source_bundle_entries(source_bundle)
    for relative_path, expected_digest in entries.items():
        path = repository_path(relative_path)
        if not path.is_file():
            raise RuntimeError(f"Source Bundle file 不存在: {relative_path}")
        assert_equal(f"Source Bundle {relative_path}", digest(path), expected_digest)
    engine_digest = digest(repository_path(ENGINE_PATH))
    procedure_digest = digest(repository_path(PROCEDURE_PATH))
    assert_equal("strategy engine", args.strategy_engine_digest, engine_digest)
    assert_equal("strategy engine 與 Source Bundle", engine_digest, entries[ENGINE_PATH])
    assert_equal("study procedure 與 Source Bundle", procedure_digest, entries[PROCEDURE_PATH])
    assert_equal("trial inputs strategy engine", inputs["strategy_engine_digest"], engine_digest)
    assert_equal("trial inputs study procedure", inputs["study_procedure_digest"], procedure_digest)
    if preregistration["selection_rule"]["selected_candidate_id"] != CANDIDATE_ID:
        raise RuntimeError("preregistration 的 candidate identity 不正確")
    if inputs["candidate_id"] != CANDIDATE_ID:
        raise RuntimeError("Development inputs 的 candidate identity 不正確")
    if inputs["preregistration_digest"] != args.preregistration_digest:
        raise RuntimeError("Development inputs 未綁定同一份 preregistration")
    if inputs["source_bundle_digest"] != args.source_bundle_digest:
        raise RuntimeError("Development inputs 未綁定同一份 Source Bundle")
    comparison_registration = preregistration["eligibility_rules"]["comparison_control"]
    if args.comparison_control.resolve() != repository_path(comparison_registration["development_evidence_path"]):
        raise RuntimeError("comparison control path 與 preregistration 不一致")
    assert_equal("comparison control preregistration digest", comparison_digest, comparison_registration["development_evidence_digest"])
    if comparison["candidate_id"] != V009_ID:
        raise RuntimeError("comparison control candidate identity 不正確")
    if inputs["data_bindings"]["comparison_control_path"] != COMPARISON_PATH:
        raise RuntimeError("Development inputs comparison control path 不一致")
    if inputs["data_bindings"]["comparison_control_digest"] != comparison_digest:
        raise RuntimeError("Development inputs comparison control digest 不一致")
    data_bindings = inputs["data_bindings"]
    warmup_path = repository_path(data_bindings["warmup_path"])
    development_path = repository_path(data_bindings["development_path"])
    if args.warmup.resolve() != warmup_path or args.development.resolve() != development_path:
        raise RuntimeError("runner 資料 path 與 Development inputs 不一致")
    roles = acquisition["roles"]
    if data_bindings["warmup_path"] != roles["warmup-only"]["source_path"] or data_bindings["development_path"] != roles["development"]["source_path"]:
        raise RuntimeError("資料 path 與 acquisition manifest 不一致")
    warmup_digest = source_lines_digest(args.warmup, "2013-01-01", "2013-12-31")
    development_digest = source_lines_digest(args.development, "2014-01-01", "2018-12-31")
    assert_equal("warmup data", warmup_digest, data_bindings["warmup_digest"])
    assert_equal("Development data", development_digest, data_bindings["development_digest"])
    assert_equal("warmup data 與 acquisition manifest", warmup_digest, roles["warmup-only"]["data_digest"])
    assert_equal("Development data 與 acquisition manifest", development_digest, roles["development"]["data_digest"])
    full_snapshot = acquisition["full_snapshot"]
    assert_equal("full market-data snapshot", digest(repository_path(full_snapshot["path"])), full_snapshot["digest"])
    assert_equal("acquisition manifest 與 Source Bundle", acquisition_digest, entries[ACQUISITION_PATH])
    assert_equal("comparison control 與 Source Bundle", comparison_digest, entries[COMPARISON_PATH])
    if data_bindings["warmup_digest"] != args.warmup_digest or data_bindings["development_digest"] != args.development_digest:
        raise RuntimeError("資料 digest argument 與 inputs 不一致")
    diagnostics = inputs["development_diagnostics"]
    registered = preregistration["eligibility_rules"]["development_diagnostics"]["block_bootstrap"]
    if diagnostics["block_lengths"] != registered["block_lengths"] or diagnostics["repetitions"] != registered["repetitions"] or diagnostics["bootstrap_seed"] != registered["seed"]:
        raise RuntimeError("bootstrap 設定與 preregistration 不一致")
    if diagnostics["seed_application"] != "exact-same-seed-for-each-block-length":
        raise RuntimeError("bootstrap seed application 不正確")
    return {
        "acquisition_manifest_digest": acquisition_digest,
        "comparison_control_evidence_digest": comparison_digest,
        "comparison_control_evidence_path": COMPARISON_PATH,
        "development_data_digest": development_digest,
        "preregistration_digest": preregistration_digest,
        "source_bundle_digest": source_bundle_digest,
        "strategy_engine_digest": engine_digest,
        "trial_inputs_digest": trial_inputs_digest,
        "warmup_data_digest": warmup_digest,
    }


def main() -> int:
    args = parser().parse_args()
    if args.output.exists():
        raise RuntimeError("拒絕覆寫既有 Development evidence output")
    preregistration = load_canonical(args.preregistration)
    inputs = load_canonical(args.trial_inputs)
    comparison_evidence = load_canonical(args.comparison_control)
    bindings = validate_inputs(args, preregistration, inputs)
    if preregistration["selection_rule"]["selected_candidate_id"] != CANDIDATE_ID:
        raise RuntimeError("candidate identity 不正確")

    warmup = read_reference_view(args.warmup, "2013-01-01", "2013-12-31")
    development = read_reference_view(args.development, "2014-01-01", "2018-12-31")
    bars = pd.concat([warmup, development])
    run_args = {"signal_start": "2014-01-01", "signal_end": "2018-12-31"}
    base = backtest(bars, spec=DEFAULT_SPEC, cost=BASE_COST, **run_args)
    stress = backtest(bars, spec=DEFAULT_SPEC, cost=STRESS_COST, **run_args)
    baseline_base = backtest(bars, spec=BASELINE_SPEC, cost=BASE_COST, **run_args)
    baseline_stress = backtest(bars, spec=BASELINE_SPEC, cost=STRESS_COST, **run_args)
    control_base = v009.backtest(bars, spec=v009.DEFAULT_SPEC, cost=v009.BASE_COST, **run_args)
    control_stress = v009.backtest(bars, spec=v009.DEFAULT_SPEC, cost=v009.STRESS_COST, **run_args)
    v009_replay = backtest(bars, spec=V009_ONLY_SPEC, cost=BASE_COST, **run_args)
    if [lifecycle(trade) for trade in v009_replay.trades] != [lifecycle(trade) for trade in control_base.trades]:
        raise RuntimeError("新引擎 fixed-gap control 未逐筆重現 v009 base")
    if v009_replay.accepted_signal_sessions != control_base.accepted_signal_sessions:
        raise RuntimeError("新引擎 fixed-gap control 未逐筆重現 v009 signals")
    if len(base.trades) != len(base.accepted_signal_sessions):
        raise RuntimeError("candidate accepted signal 與 completed trade 數量不一致")
    if [lifecycle(trade) for trade in base.trades] != [lifecycle(trade) for trade in stress.trades]:
        raise RuntimeError("candidate base 與 stress 交易生命週期不一致")

    initial_cash = float(preregistration["initial_cash"])
    base_metrics = qualification_metrics(base, initial_cash=initial_cash)
    stress_metrics = qualification_metrics(stress, initial_cash=initial_cash)
    control_metrics = comparison_evidence["metrics"]
    for label, result, expected, engine in (
        ("base", control_base, control_metrics["base"], v009),
        ("stress", control_stress, control_metrics["stress"], v009),
    ):
        metrics = engine.qualification_metrics(result, initial_cash=initial_cash)
        for key in ("completed_trades", "return", "profit_factor", "maximum_drawdown", "traded_years"):
            if Decimal(str(metrics[key])) != Decimal(str(expected[key])):
                raise RuntimeError(f"v009 control {label}.{key} 與比較摘要不一致")
    baseline_base_metrics = qualification_metrics(baseline_base, initial_cash=initial_cash)
    baseline_stress_metrics = qualification_metrics(baseline_stress, initial_cash=initial_cash)
    comparison = trade_comparison(
        base.trades, stress.trades, control_base.trades, control_stress.trades,
        development.index, DEFAULT_SPEC.cooldown_sessions,
    )
    base_rates = trade_rates(base.trades, initial_cash)
    stress_rates = trade_rates(stress.trades, initial_cash)
    registered_bootstrap = preregistration["eligibility_rules"]["development_diagnostics"]["block_bootstrap"]
    base_bootstrap = [bootstrap(base_rates, length, repetitions=registered_bootstrap["repetitions"], seed=registered_bootstrap["seed"]) for length in registered_bootstrap["block_lengths"]]
    stress_bootstrap = [bootstrap(stress_rates, length, repetitions=registered_bootstrap["repetitions"], seed=registered_bootstrap["seed"]) for length in registered_bootstrap["block_lengths"]]
    base_loyo = leave_one_signal_year_out(base.trades, initial_cash=initial_cash)
    stress_loyo = leave_one_signal_year_out(stress.trades, initial_cash=initial_cash)
    actuals: dict[str, str | int | float] = {
        "base_profit_factor": base_metrics["profit_factor"],
        "base_return": base_metrics["return"],
        "completed_trades": base_metrics["completed_trades"],
        "maximum_realized_trade_loss_fraction": max(maximum_loss_fraction(base.trades, initial_cash=initial_cash), maximum_loss_fraction(stress.trades, initial_cash=initial_cash)),
        "maximum_stress_block_bootstrap_drawdown_above_10pct_ratio": max(float(item["drawdown_above_10pct_ratio"]) for item in stress_bootstrap),
        "maximum_stress_leave_one_year_out_drawdown": max(float(item["maximum_drawdown"]) for item in stress_loyo.values()),
        "minimum_stress_block_bootstrap_positive_return_ratio": min(float(item["positive_return_ratio"]) for item in stress_bootstrap),
        "minimum_stress_leave_one_year_out_profit_factor": min(float(item["profit_factor"]) for item in stress_loyo.values()),
        "minimum_stress_leave_one_year_out_return": min(float(item["return"]) for item in stress_loyo.values()),
        "stress_maximum_drawdown": stress_metrics["maximum_drawdown"],
        "stress_profit_factor": stress_metrics["profit_factor"],
        "stress_return": stress_metrics["return"],
        "traded_years": base_metrics["traded_years"],
    }
    gates, failures = gate_records(actuals, preregistration["eligibility_rules"]["development_gates"])

    years: dict[str, dict[str, object]] = defaultdict(lambda: {"trades": 0, "base_pnl": 0.0, "stress_pnl": 0.0})
    for base_trade, stress_trade in zip(base.trades, stress.trades, strict=True):
        year = str(base_trade.signal_session.year)
        years[year]["trades"] = int(years[year]["trades"]) + 1
        years[year]["base_pnl"] = float(years[year]["base_pnl"]) + base_trade.pnl
        years[year]["stress_pnl"] = float(years[year]["stress_pnl"]) + stress_trade.pnl
    target_rules = preregistration["eligibility_rules"]["research_targets"]
    target_actuals: dict[str, str | int | float] = {
        "minimum_leave_one_signal_year_out_stress_net_increment_positive": float(comparison["minimum_leave_one_signal_year_out_net_stress_pnl"]),
        "net_increment_positive_signal_years_at_least_three": int(comparison["net_increment_positive_signal_years"]),
        "stress_maximum_drawdown_not_above_v009": stress_metrics["maximum_drawdown"],
        "stress_net_new_minus_v009_pnl_positive": float(comparison["net_new_minus_replaced"]["stress"]),
        "stress_return_strictly_above_v009": stress_metrics["return"],
    }
    if set(target_actuals) != set(target_rules):
        raise RuntimeError("research target actuals 與 preregistration 不一致")
    target_records = [
        {
            "target": name,
            "actual": value if isinstance(value, int) else text(float(value)),
            "operator": target_rules[name]["operator"],
            "required": target_rules[name]["value"],
            "passed": compare(value, target_rules[name]["operator"], target_rules[name]["value"]),
        }
        for name, value in target_actuals.items()
    ]
    trades = [
        trade_record(index, base_trade, stress_trade, base_rate, stress_rate)
        for index, (base_trade, stress_trade, base_rate, stress_rate) in enumerate(zip(base.trades, stress.trades, base_rates, stress_rates, strict=True), start=1)
    ]
    evidence = {
        "accepted_signal_count": len(trades),
        "baseline_comparison": {
            "baseline_id": BASELINE_ID,
            "baseline_is_excluded_from_candidate_family": True,
            "candidate_id": CANDIDATE_ID,
            "execution_is_identical": True,
            "candidate": {
                "base": {key: text(value) if isinstance(value, float) else value for key, value in base_metrics.items()},
                "stress": {key: text(value) if isinstance(value, float) else value for key, value in stress_metrics.items()},
            },
            "baseline": {
                "base": {key: text(value) if isinstance(value, float) else value for key, value in baseline_base_metrics.items()},
                "stress": {key: text(value) if isinstance(value, float) else value for key, value in baseline_stress_metrics.items()},
            },
            "candidate_minus_baseline": {
                "base_return": text(float(base_metrics["return"]) - float(baseline_base_metrics["return"])),
                "stress_return": text(float(stress_metrics["return"]) - float(baseline_stress_metrics["return"])),
            },
        },
        "bindings": bindings,
        "candidate_id": CANDIDATE_ID,
        "diagnostics": {
            "block_bootstrap": {"base": base_bootstrap, "stress": stress_bootstrap, "gating": True},
            "by_signal_year": {
                year: {"trades": values["trades"], "base_pnl": text(float(values["base_pnl"])), "stress_pnl": text(float(values["stress_pnl"]))}
                for year, values in sorted(years.items())
            },
            "leave_one_signal_year_out": {"base": base_loyo, "stress": stress_loyo, "gating": True},
        },
        "gates": gates,
        "mechanism_ablation": {
            "simple_baseline": metric_summary(v021, bars, BASELINE_SPEC, initial_cash),
            "v009_fixed_gap_control_in_new_engine": metric_summary(v021, bars, V009_ONLY_SPEC, initial_cash),
            "v009_frozen_control_engine": metric_summary(v009, bars, v009.DEFAULT_SPEC, initial_cash),
            "candidate": metric_summary(v021, bars, DEFAULT_SPEC, initial_cash),
            "interpretation": "事前固定的描述性比較，不參與 candidate selection；候選只有一條 raw signal 路徑，唯一策略變更是把 v009 固定 1.5% SMA gap 換成前一日 ATR14 正規化距離 1.0。",
        },
        "metrics": {
            "base": {**{key: text(value) if isinstance(value, float) else value for key, value in base_metrics.items()}, "maximum_realized_trade_loss_fraction": text(maximum_loss_fraction(base.trades, initial_cash=initial_cash))},
            "stress": {**{key: text(value) if isinstance(value, float) else value for key, value in stress_metrics.items()}, "maximum_realized_trade_loss_fraction": text(maximum_loss_fraction(stress.trades, initial_cash=initial_cash))},
            "trade_count_by_signal_year": {year: values["trades"] for year, values in sorted(years.items())},
        },
        "network_access_during_run": False,
        "reference_controls": {
            "v009": {
                "candidate_id": V009_ID,
                "registered_development_evidence_digest": comparison_evidence["source_development_evidence_digest"],
                "registered_metrics": control_metrics,
                "live_reproduction": metric_summary(v009, bars, v009.DEFAULT_SPEC, initial_cash),
            }
        },
        "research_target_records": target_records,
        "risk_diagnostics": {
            "realized_drawdown_gate_definition": "正式 gate 的 maximum_drawdown 只由已完成交易 PnL 資金曲線重算。",
            "candidate_mark_to_market": {
                "definition": "持倉 session 以當日 Low、成本後可清算價估值；time exit 於下一個 open 成交。",
                "base_maximum_drawdown": text(mark_to_market_drawdown(bars, base, cost=BASE_COST, initial_cash=initial_cash)),
                "stress_maximum_drawdown": text(mark_to_market_drawdown(bars, stress, cost=STRESS_COST, initial_cash=initial_cash)),
            },
            "v009_control_mark_to_market": {
                "base_maximum_drawdown": text(v009.mark_to_market_drawdown(bars, control_base, cost=v009.BASE_COST, initial_cash=initial_cash)),
                "stress_maximum_drawdown": text(v009.mark_to_market_drawdown(bars, control_stress, cost=v009.STRESS_COST, initial_cash=initial_cash)),
            },
        },
        "signal_path_diagnostics": {
            "definition": "候選只有一條 raw signal 路徑；SMA、RSI、前 5 session 成交量先行、收盤高於前收與 ATR 距離在訊號日一起判斷，raw signal 再受持倉、冷卻與期間 cutoff 限制。",
            "indicator_contract": v021.signal_definition(),
            "accepted_signal_sessions": [str(session.date()) for session in base.accepted_signal_sessions],
            "completed_trade_signal_years": sorted({trade.signal_session.year for trade in base.trades}),
        },
        "stage": "development",
        "trade_comparison": comparison,
        "trades": trades,
        "schema_version": 1,
    }
    evidence = finalize_development_evidence(evidence, preregistration)
    atomic_create(args.output, canonical_bytes(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
