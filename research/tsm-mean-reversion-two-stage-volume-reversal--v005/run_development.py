"""只使用 TSM warmup-only 與 Development 快照產生候選 evidence。

這個 runner 只開啟 2013 warmup 與 2014--2018 Development。它會保存逐筆交易、
逐年分段、leave-one-signal-year-out 與固定 seed 的 block bootstrap，門檻則直接
取自 preregistration，不接受命令列臨時改值。
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

from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v005 import (
    BASE_COST,
    BASELINE_SPEC,
    DEFAULT_SPEC,
    STRESS_COST,
    Trade,
    backtest,
    qualification_metrics,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import atomic_create, canonical_bytes, load_canonical  # noqa: E402

CANDIDATE_ID = "tsm-mr-two-stage-time-decay-v005"
BASELINE_ID = "tsm-mean-reversion-two-stage-baseline-v005"
STUDY_ID = "tsm-mean-reversion-two-stage-volume-reversal--v005"
ENGINE_PATH = "src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v005.py"
PROCEDURE_PATH = f"research/{STUDY_ID}/run_development.py"
ACQUISITION_PATH = f"research/{STUDY_ID}/data-snapshot-acquisition.yml"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="產生 TSM two-stage volume reversal v005 2014--2018 Development raw evidence"
    )
    result.add_argument("--warmup", type=Path, required=True)
    result.add_argument("--development", type=Path, required=True)
    result.add_argument("--preregistration", type=Path, required=True)
    result.add_argument("--trial-inputs", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--acquisition-digest", required=True)
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


def _repository_path(relative_path: str) -> Path:
    path = (REPOSITORY_ROOT / relative_path).resolve()
    try:
        path.relative_to(REPOSITORY_ROOT)
    except ValueError as exc:
        raise RuntimeError(f"路徑逃出 repository: {relative_path}") from exc
    return path


def _source_lines_digest(path: Path, start: str, end: str) -> str:
    """以保留原始 CSV 行 bytes 的方式計算指定日期 view digest。"""

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
            try:
                session = date.fromisoformat(raw_date)
            except ValueError as exc:
                raise RuntimeError(f"資料日期不合法: {path}:{line_number}") from exc
            if session.isoformat() != raw_date:
                raise RuntimeError(f"資料日期格式不固定: {path}:{line_number}")
            if previous is not None and session <= previous:
                raise RuntimeError(f"資料 session 重複或未排序: {path}:{line_number}")
            previous = session
            if start_date <= session <= end_date:
                hasher.update(line)
                selected += 1
    if selected == 0:
        raise RuntimeError(f"資料沒有涵蓋要求的 view: {start} 到 {end}")
    return hasher.hexdigest()


def _source_bundle_entries(source_bundle: dict[str, Any]) -> dict[str, str]:
    entries: dict[str, str] = {}
    for item in source_bundle["files"]:
        path = item["path"]
        if path in entries:
            raise RuntimeError(f"Source Bundle 含有重複 path: {path}")
        entries[path] = item["digest"]
    return entries


def _assert_equal(label: str, actual: str, expected: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label} digest 不一致: expected={expected}, actual={actual}")


def read_reference_view(path: Path, start: str, end: str) -> pd.DataFrame:
    """從同一份 content-addressed source 只保留指定日期 view。"""

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
    initial_cash: float,
) -> dict[str, object]:
    """每個 block length 都直接使用同一個 preregistered seed。"""

    if len(rates) == 0:
        raise RuntimeError("Development bootstrap 至少需要一筆交易")
    rng = np.random.default_rng(seed)
    count = len(rates)
    blocks = (count + block_length - 1) // block_length
    starts = rng.integers(0, count, size=(repetitions, blocks))
    offsets = np.arange(block_length)
    indexes = ((starts[:, :, None] + offsets) % count).reshape(repetitions, -1)
    sampled = rates[indexes[:, :count]]

    equity = np.full(repetitions, initial_cash)
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
    returns = equity / initial_cash - 1.0
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
        "return_q05_q50_q95": [
            text(value) for value in np.quantile(returns, [0.05, 0.5, 0.95])
        ],
        "profit_factor_q05_q50_q95": [
            text(value) for value in np.quantile(profit_factors, [0.05, 0.5, 0.95])
        ],
        "maximum_drawdown_q05_q50_q95": [
            text(value) for value in np.quantile(maximum_drawdown, [0.05, 0.5, 0.95])
        ],
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
        kept = rates[years != year]
        values = path_metrics(kept, initial_cash)
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


def trade_record(
    index: int,
    base_trade: Trade,
    stress_trade: Trade,
    base_rate: float,
    stress_rate: float,
) -> dict[str, object]:
    lifecycle = (
        base_trade.signal_session,
        base_trade.entry_session,
        base_trade.exit_session,
        base_trade.exit_reason,
    )
    stress_lifecycle = (
        stress_trade.signal_session,
        stress_trade.entry_session,
        stress_trade.exit_session,
        stress_trade.exit_reason,
    )
    if lifecycle != stress_lifecycle:
        raise RuntimeError("base 與 stress 的交易生命週期不一致")
    return {
        "trade_id": f"development-{index:03d}",
        "signal_session": str(base_trade.signal_session.date()),
        "entry_session": str(base_trade.entry_session.date()),
        "exit_session": str(base_trade.exit_session.date()),
        "raw_entry_price": text(base_trade.raw_entry_price),
        "raw_exit_price": text(base_trade.raw_exit_price),
        "exit_reason": base_trade.exit_reason,
        "held_sessions": base_trade.held_sessions,
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


def compare(actual: str | int | float, operator: str, required: str | int | float) -> bool:
    if operator == "equals":
        return actual == required
    left = Decimal(str(actual))
    right = Decimal(str(required))
    return {
        ">": left > right,
        ">=": left >= right,
        "<": left < right,
        "<=": left <= right,
    }[operator]


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


def validate_inputs(
    args: argparse.Namespace, preregistration: dict[str, Any], inputs: dict[str, Any]
) -> dict[str, str]:
    source_bundle_path = args.trial_inputs.parent / "source-bundle.yml"
    acquisition_path = args.trial_inputs.parent / "data-snapshot-acquisition.yml"
    source_bundle = load_canonical(source_bundle_path)
    acquisition = load_canonical(acquisition_path)
    source_bundle_digest = digest(source_bundle_path)
    acquisition_digest = digest(acquisition_path)
    preregistration_digest = digest(args.preregistration)
    trial_inputs_digest = digest(args.trial_inputs)
    _assert_equal("Source Bundle", args.source_bundle_digest, source_bundle_digest)
    _assert_equal("acquisition manifest", args.acquisition_digest, acquisition_digest)
    _assert_equal("preregistration", args.preregistration_digest, preregistration_digest)
    _assert_equal("trial inputs", args.trial_inputs_digest, trial_inputs_digest)

    entries = _source_bundle_entries(source_bundle)
    for relative_path, expected_digest in entries.items():
        path = _repository_path(relative_path)
        if not path.is_file():
            raise RuntimeError(f"Source Bundle file 不存在: {relative_path}")
        _assert_equal(f"Source Bundle {relative_path}", digest(path), expected_digest)

    engine_digest = digest(_repository_path(ENGINE_PATH))
    procedure_digest = digest(_repository_path(PROCEDURE_PATH))
    _assert_equal("strategy engine", args.strategy_engine_digest, engine_digest)
    _assert_equal("strategy engine 與 Source Bundle", engine_digest, entries[ENGINE_PATH])
    _assert_equal("study procedure 與 Source Bundle", procedure_digest, entries[PROCEDURE_PATH])
    _assert_equal("trial inputs strategy engine", inputs["strategy_engine_digest"], engine_digest)
    _assert_equal("trial inputs study procedure", inputs["study_procedure_digest"], procedure_digest)

    if preregistration["selection_rule"]["selected_candidate_id"] != CANDIDATE_ID:
        raise RuntimeError("preregistration 的 candidate identity 不正確")
    if inputs["candidate_id"] != CANDIDATE_ID:
        raise RuntimeError("Development inputs 的 candidate identity 不正確")
    if inputs["preregistration_digest"] != args.preregistration_digest:
        raise RuntimeError("Development inputs 未綁定同一份 preregistration")
    if inputs["source_bundle_digest"] != args.source_bundle_digest:
        raise RuntimeError("Development inputs 未綁定同一份 Source Bundle")
    data_bindings = inputs["data_bindings"]
    warmup_path = _repository_path(data_bindings["warmup_path"])
    development_path = _repository_path(data_bindings["development_path"])
    if args.warmup.resolve() != warmup_path:
        raise RuntimeError("warmup path 與 Development inputs 不一致")
    if args.development.resolve() != development_path:
        raise RuntimeError("Development path 與 Development inputs 不一致")
    roles = acquisition["roles"]
    if data_bindings["warmup_path"] != roles["warmup-only"]["source_path"]:
        raise RuntimeError("warmup path 與 acquisition manifest 不一致")
    if data_bindings["development_path"] != roles["development"]["source_path"]:
        raise RuntimeError("Development path 與 acquisition manifest 不一致")
    warmup_digest = _source_lines_digest(args.warmup, "2013-01-01", "2013-12-31")
    development_digest = _source_lines_digest(args.development, "2014-01-01", "2018-12-31")
    _assert_equal("warmup data", warmup_digest, data_bindings["warmup_digest"])
    _assert_equal("Development data", development_digest, data_bindings["development_digest"])
    _assert_equal("warmup data 與 acquisition manifest", warmup_digest, roles["warmup-only"]["data_digest"])
    _assert_equal("Development data 與 acquisition manifest", development_digest, roles["development"]["data_digest"])
    full_snapshot = acquisition["full_snapshot"]
    full_path = _repository_path(full_snapshot["path"])
    _assert_equal("full market-data snapshot", digest(full_path), full_snapshot["digest"])
    _assert_equal("acquisition manifest 與 Source Bundle", acquisition_digest, entries[ACQUISITION_PATH])
    _assert_equal("acquisition digest argument", args.acquisition_digest, entries[ACQUISITION_PATH])
    if data_bindings["warmup_digest"] != args.warmup_digest:
        raise RuntimeError("warmup digest 與 inputs 不一致")
    if data_bindings["development_digest"] != args.development_digest:
        raise RuntimeError("Development digest 與 inputs 不一致")
    diagnostics = inputs["development_diagnostics"]
    registered = preregistration["eligibility_rules"]["development_diagnostics"]["block_bootstrap"]
    if diagnostics["block_lengths"] != registered["block_lengths"]:
        raise RuntimeError("bootstrap block lengths 與 preregistration 不一致")
    if diagnostics["repetitions"] != registered["repetitions"]:
        raise RuntimeError("bootstrap repetitions 與 preregistration 不一致")
    if diagnostics["bootstrap_seed"] != registered["seed"]:
        raise RuntimeError("bootstrap seed 與 preregistration 不一致")
    if diagnostics["seed_application"] != "exact-same-seed-for-each-block-length":
        raise RuntimeError("bootstrap seed application 不正確")
    return {
        "acquisition_manifest_digest": acquisition_digest,
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
    bindings = validate_inputs(args, preregistration, inputs)

    warmup = read_reference_view(args.warmup, "2013-01-01", "2013-12-31")
    development = read_reference_view(args.development, "2014-01-01", "2018-12-31")
    bars = pd.concat([warmup, development])
    run_args = {
        "signal_start": "2014-01-01",
        "signal_end": "2018-12-31",
        "spec": DEFAULT_SPEC,
    }
    base = backtest(bars, cost=BASE_COST, **run_args)
    stress = backtest(bars, cost=STRESS_COST, **run_args)
    baseline_base = backtest(
        bars, spec=BASELINE_SPEC, cost=BASE_COST,
        signal_start=run_args["signal_start"], signal_end=run_args["signal_end"]
    )
    baseline_stress = backtest(
        bars, spec=BASELINE_SPEC, cost=STRESS_COST,
        signal_start=run_args["signal_start"], signal_end=run_args["signal_end"]
    )
    initial_cash = float(preregistration["initial_cash"])
    base_metrics = qualification_metrics(base, initial_cash=initial_cash)
    stress_metrics = qualification_metrics(stress, initial_cash=initial_cash)
    baseline_base_metrics = qualification_metrics(baseline_base, initial_cash=initial_cash)
    baseline_stress_metrics = qualification_metrics(baseline_stress, initial_cash=initial_cash)
    base_rates = trade_rates(base.trades, initial_cash)
    stress_rates = trade_rates(stress.trades, initial_cash)
    registered_bootstrap = preregistration["eligibility_rules"]["development_diagnostics"][
        "block_bootstrap"
    ]
    base_bootstrap = [
        bootstrap(
            base_rates,
            length,
            repetitions=registered_bootstrap["repetitions"],
            seed=registered_bootstrap["seed"],
            initial_cash=initial_cash,
        )
        for length in registered_bootstrap["block_lengths"]
    ]
    stress_bootstrap = [
        bootstrap(
            stress_rates,
            length,
            repetitions=registered_bootstrap["repetitions"],
            seed=registered_bootstrap["seed"],
            initial_cash=initial_cash,
        )
        for length in registered_bootstrap["block_lengths"]
    ]
    base_loyo = leave_one_signal_year_out(base.trades, initial_cash=initial_cash)
    stress_loyo = leave_one_signal_year_out(stress.trades, initial_cash=initial_cash)

    max_realized_loss = max(
        maximum_loss_fraction(base.trades, initial_cash=initial_cash),
        maximum_loss_fraction(stress.trades, initial_cash=initial_cash),
    )
    actuals: dict[str, str | int | float] = {
        "base_profit_factor": base_metrics["profit_factor"],
        "base_return": base_metrics["return"],
        "completed_trades": base_metrics["completed_trades"],
        "maximum_realized_trade_loss_fraction": max_realized_loss,
        "maximum_stress_block_bootstrap_drawdown_above_10pct_ratio": max(
            float(item["drawdown_above_10pct_ratio"]) for item in stress_bootstrap
        ),
        "maximum_stress_leave_one_year_out_drawdown": max(
            float(item["maximum_drawdown"]) for item in stress_loyo.values()
        ),
        "minimum_stress_block_bootstrap_positive_return_ratio": min(
            float(item["positive_return_ratio"]) for item in stress_bootstrap
        ),
        "minimum_stress_leave_one_year_out_profit_factor": min(
            float(item["profit_factor"]) for item in stress_loyo.values()
        ),
        "minimum_stress_leave_one_year_out_return": min(
            float(item["return"]) for item in stress_loyo.values()
        ),
        "stress_maximum_drawdown": stress_metrics["maximum_drawdown"],
        "stress_profit_factor": stress_metrics["profit_factor"],
        "stress_return": stress_metrics["return"],
        "traded_years": base_metrics["traded_years"],
    }
    gates, failures = gate_records(
        actuals, preregistration["eligibility_rules"]["development_gates"]
    )

    years: dict[str, dict[str, object]] = defaultdict(
        lambda: {"trades": 0, "base_pnl": 0.0, "stress_pnl": 0.0}
    )
    for base_trade, stress_trade in zip(base.trades, stress.trades, strict=True):
        year = str(base_trade.signal_session.year)
        years[year]["trades"] = int(years[year]["trades"]) + 1
        years[year]["base_pnl"] = float(years[year]["base_pnl"]) + base_trade.pnl
        years[year]["stress_pnl"] = float(years[year]["stress_pnl"]) + stress_trade.pnl

    evidence = {
        "schema_version": 1,
        "stage": "development",
        "candidate_id": CANDIDATE_ID,
        "disposition": "fail" if failures else "pass",
        "failed_gates": failures,
        "network_access_during_run": False,
        "accepted_signal_count": len(base.accepted_signal_sessions),
        "baseline_comparison": {
            "baseline_id": BASELINE_ID,
            "candidate_id": CANDIDATE_ID,
            "execution_is_identical": True,
            "baseline_is_excluded_from_candidate_family": True,
            "candidate": {
                "base": {
                    key: text(value) if isinstance(value, float) else value
                    for key, value in base_metrics.items()
                },
                "stress": {
                    key: text(value) if isinstance(value, float) else value
                    for key, value in stress_metrics.items()
                },
            },
            "baseline": {
                "base": {
                    key: text(value) if isinstance(value, float) else value
                    for key, value in baseline_base_metrics.items()
                },
                "stress": {
                    key: text(value) if isinstance(value, float) else value
                    for key, value in baseline_stress_metrics.items()
                },
            },
            "candidate_minus_baseline": {
                "base_return": text(
                    float(base_metrics["return"]) - float(baseline_base_metrics["return"])
                ),
                "stress_return": text(
                    float(stress_metrics["return"])
                    - float(baseline_stress_metrics["return"])
                ),
            },
        },
        "bindings": bindings,
        "gates": gates,
        "metrics": {
            "base": {
                **{
                    key: text(value) if isinstance(value, float) else value
                    for key, value in base_metrics.items()
                },
                "maximum_realized_trade_loss_fraction": text(
                    maximum_loss_fraction(base.trades, initial_cash=initial_cash)
                ),
            },
            "stress": {
                **{
                    key: text(value) if isinstance(value, float) else value
                    for key, value in stress_metrics.items()
                },
                "maximum_realized_trade_loss_fraction": text(
                    maximum_loss_fraction(stress.trades, initial_cash=initial_cash)
                ),
            },
            "trade_count_by_signal_year": {
                year: values["trades"] for year, values in sorted(years.items())
            },
        },
        "diagnostics": {
            "by_signal_year": {
                year: {
                    "trades": values["trades"],
                    "base_pnl": text(float(values["base_pnl"])),
                    "stress_pnl": text(float(values["stress_pnl"])),
                }
                for year, values in sorted(years.items())
            },
            "leave_one_signal_year_out": {
                "base": base_loyo,
                "stress": stress_loyo,
                "gating": True,
            },
            "block_bootstrap": {
                "base": base_bootstrap,
                "stress": stress_bootstrap,
                "gating": True,
            },
        },
        "trades": [
            trade_record(index, base_trade, stress_trade, base_rate, stress_rate)
            for index, (base_trade, stress_trade, base_rate, stress_rate) in enumerate(
                zip(base.trades, stress.trades, base_rates, stress_rates, strict=True), start=1
            )
        ],
    }
    atomic_create(args.output, canonical_bytes(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
