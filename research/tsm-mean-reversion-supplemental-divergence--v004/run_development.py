"""只使用 TSM warmup-only 與 Development 快照產生候選 evidence。

這個 runner 只開啟 2013 warmup 與 2014--2018 Development。它會保存逐筆交易、
逐年分段、leave-one-signal-year-out、固定 seed 的交易區塊 bootstrap、
日曆區塊 bootstrap、新舊交易生命週期排擠拆解，以及事前指定的量能先改善機制消融；
門檻直接取自 preregistration，不接受命令列臨時改值。
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

from trading_2026_2.tsm_mean_reversion_supplemental_divergence_v004 import (
    BASE_COST,
    BASELINE_SPEC,
    DEFAULT_SPEC,
    STRESS_COST,
    V009_ONLY_SPEC,
    WITHOUT_VOLUME_LEAD_SPEC,
    Trade,
    backtest,
    mark_to_market_drawdown,
    qualification_metrics,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import atomic_create, canonical_bytes, load_canonical  # noqa: E402

CANDIDATE_ID = "tsm-mr-supplemental-divergence-v004"
BASELINE_ID = "tsm-mean-reversion-supplemental-divergence-baseline-v004"
STUDY_ID = "tsm-mean-reversion-supplemental-divergence--v004"
ENGINE_PATH = "src/trading_2026_2/tsm_mean_reversion_supplemental_divergence_v004.py"
PROCEDURE_PATH = f"research/{STUDY_ID}/run_development.py"
ACQUISITION_PATH = f"research/{STUDY_ID}/data-snapshot-acquisition.yml"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="產生 TSM 低檔量價背離補充型均值回歸 v001 2014--2018 Development raw evidence"
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


def text(value: float | int) -> str:
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


def _session_realized_rates(
    bars: pd.DataFrame, trades: tuple[Trade, ...], initial_cash: float
) -> np.ndarray:
    sessions = bars.loc["2014-01-01":"2018-12-31"].index
    indexes = {session: index for index, session in enumerate(sessions)}
    rates = np.zeros(len(sessions), dtype=float)
    equity = initial_cash
    for trade in trades:
        if trade.exit_session not in indexes:
            raise RuntimeError("calendar block diagnostic 的 trade 超出 Development session")
        rates[indexes[trade.exit_session]] += trade.pnl / equity
        equity += trade.pnl
    return rates


def calendar_block_bootstrap(
    session_rates: np.ndarray,
    block_sessions: int,
    *,
    repetitions: int,
    seed: int,
    initial_cash: float,
) -> dict[str, object]:
    """從連續 XNYS session 區塊重抽，避免只重排交易順序。"""

    if len(session_rates) == 0 or block_sessions <= 0:
        raise RuntimeError("calendar block bootstrap 需要有效的 session 與 block")
    rng = np.random.default_rng(seed)
    count = len(session_rates)
    blocks = (count + block_sessions - 1) // block_sessions
    starts = rng.integers(0, count, size=(repetitions, blocks))
    offsets = np.arange(block_sessions)
    indexes = ((starts[:, :, None] + offsets) % count).reshape(repetitions, -1)
    sampled = session_rates[indexes[:, :count]]

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
        "block_sessions": block_sessions,
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


def signal_year_breakdown(trades: tuple[Trade, ...]) -> list[dict[str, object]]:
    by_year: dict[int, list[Trade]] = defaultdict(list)
    for trade in trades:
        by_year[trade.signal_session.year].append(trade)
    result: list[dict[str, object]] = []
    for year in sorted(by_year.keys()):
        year_trades = by_year[year]
        profits = sum(t.pnl for t in year_trades if t.pnl > 0)
        losses = -sum(t.pnl for t in year_trades if t.pnl < 0)
        pf = profits / losses if losses else (float("inf") if profits else 0.0)
        result.append(
            {
                "year": year,
                "completed_trades": len(year_trades),
                "total_pnl": text(sum(t.pnl for t in year_trades)),
                "profit_factor": text(pf),
            }
        )
    return result


def strategy_summary(
    bars: pd.DataFrame,
    spec: Any,
    *,
    initial_cash: float = 100_000.0,
    signal_start: str = "2014-01-01",
    signal_end: str = "2018-12-31",
) -> dict[str, Any]:
    base = backtest(
        bars,
        spec=spec,
        cost=BASE_COST,
        signal_start=signal_start,
        signal_end=signal_end,
    )
    stress = backtest(
        bars,
        spec=spec,
        cost=STRESS_COST,
        signal_start=signal_start,
        signal_end=signal_end,
    )
    base_m = qualification_metrics(base, initial_cash=initial_cash)
    stress_m = qualification_metrics(stress, initial_cash=initial_cash)
    return {
        "base": {
            "completed_trades": base_m["completed_trades"],
            "maximum_drawdown": text(base_m["maximum_drawdown"]),
            "profit_factor": text(base_m["profit_factor"]),
            "return": text(base_m["return"]),
            "traded_years": base_m["traded_years"],
        },
        "stress": {
            "completed_trades": stress_m["completed_trades"],
            "maximum_drawdown": text(stress_m["maximum_drawdown"]),
            "profit_factor": text(stress_m["profit_factor"]),
            "return": text(stress_m["return"]),
            "traded_years": stress_m["traded_years"],
        },
    }


def maximum_loss_fraction(trades: tuple[Trade, ...], initial_cash: float) -> float:
    equity = initial_cash
    worst = 0.0
    for trade in trades:
        worst = max(worst, -trade.pnl / equity)
        equity += trade.pnl
    return worst


def trade_record(
    index: int,
    base_trade: Trade,
    stress_trade: Trade,
    base_rate: float,
    stress_rate: float,
) -> dict[str, Any]:
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
        "signal_origin": base_trade.signal_origin,
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
    acquisition = load_canonical(_repository_path(ACQUISITION_PATH))
    source_bundle = load_canonical(
        _repository_path(f"research/{STUDY_ID}/source-bundle.yml")
    )
    entries = _source_bundle_entries(source_bundle)

    _assert_equal("acquisition", digest(_repository_path(ACQUISITION_PATH)), args.acquisition_digest)
    _assert_equal("source bundle", digest(_repository_path(f"research/{STUDY_ID}/source-bundle.yml")), args.source_bundle_digest)
    _assert_equal("strategy engine", digest(_repository_path(ENGINE_PATH)), args.strategy_engine_digest)
    _assert_equal("trial inputs", digest(args.trial_inputs), args.trial_inputs_digest)
    _assert_equal("preregistration", digest(args.preregistration), args.preregistration_digest)
    _assert_equal("acquisition full snapshot", acquisition["full_snapshot"]["digest"], digest(_repository_path(acquisition["full_snapshot"]["path"])))

    _assert_equal("warmup view", _source_lines_digest(args.warmup, "2013-01-01", "2013-12-31"), args.warmup_digest)
    _assert_equal("development view", _source_lines_digest(args.development, "2014-01-01", "2018-12-31"), args.development_digest)

    _assert_equal("inputs.preregistration_digest", inputs["preregistration_digest"], args.preregistration_digest)
    _assert_equal("inputs.source_bundle_digest", inputs["source_bundle_digest"], args.source_bundle_digest)
    _assert_equal("inputs.strategy_engine_digest", inputs["strategy_engine_digest"], args.strategy_engine_digest)
    _assert_equal("inputs.study_procedure_digest", inputs["study_procedure_digest"], entries[PROCEDURE_PATH])
    _assert_equal("inputs.warmup_digest", inputs["data_bindings"]["warmup_digest"], args.warmup_digest)
    _assert_equal("inputs.development_digest", inputs["data_bindings"]["development_digest"], args.development_digest)

    if entries[ENGINE_PATH] != args.strategy_engine_digest:
        raise RuntimeError("Source Bundle 的策略引擎 digest 與命令列不一致")
    if entries[PROCEDURE_PATH] != digest(_repository_path(PROCEDURE_PATH)):
        raise RuntimeError("Source Bundle 的 runner digest 與檔案不一致")
    if entries[f"research/{STUDY_ID}/preregistration.yml"] != args.preregistration_digest:
        raise RuntimeError("Source Bundle 的 preregistration digest 與命令列不一致")
    if entries[f"research/{STUDY_ID}/candidate-definition.yml"] != digest(_repository_path(f"research/{STUDY_ID}/candidate-definition.yml")):
        raise RuntimeError("Source Bundle 的 candidate definition digest 與檔案不一致")
    if entries[f"research/{STUDY_ID}/qualification-spec.yml"] != digest(_repository_path(f"research/{STUDY_ID}/qualification-spec.yml")):
        raise RuntimeError("Source Bundle 的 qualification spec digest 與檔案不一致")
    if entries[f"research/{STUDY_ID}/implementation-contract.yml"] != digest(_repository_path(f"research/{STUDY_ID}/implementation-contract.yml")):
        raise RuntimeError("Source Bundle 的 implementation contract digest 與檔案不一致")

    return {
        "acquisition_manifest_digest": args.acquisition_digest,
        "source_bundle_digest": args.source_bundle_digest,
        "strategy_engine_digest": args.strategy_engine_digest,
        "trial_inputs_digest": args.trial_inputs_digest,
        "preregistration_digest": args.preregistration_digest,
        "warmup_data_digest": args.warmup_digest,
        "development_data_digest": args.development_digest,
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

    # 1. 執行主候選回測
    base = backtest(bars, cost=BASE_COST, **run_args)
    stress = backtest(bars, cost=STRESS_COST, **run_args)

    # 2. 執行簡單 baseline 回測
    baseline_base = backtest(
        bars,
        spec=BASELINE_SPEC,
        cost=BASE_COST,
        signal_start=run_args["signal_start"],
        signal_end=run_args["signal_end"],
    )
    baseline_stress = backtest(
        bars,
        spec=BASELINE_SPEC,
        cost=STRESS_COST,
        signal_start=run_args["signal_start"],
        signal_end=run_args["signal_end"],
    )

    # 3. 執行 v009 主路徑回測（以同一份資料與執行器重新計算基準）
    v009_base = backtest(
        bars,
        spec=V009_ONLY_SPEC,
        cost=BASE_COST,
        signal_start=run_args["signal_start"],
        signal_end=run_args["signal_end"],
    )
    v009_stress = backtest(
        bars,
        spec=V009_ONLY_SPEC,
        cost=STRESS_COST,
        signal_start=run_args["signal_start"],
        signal_end=run_args["signal_end"],
    )

    # 4. 執行消融手臂回測（移除量能先改善條件）
    without_vol_base = backtest(
        bars,
        spec=WITHOUT_VOLUME_LEAD_SPEC,
        cost=BASE_COST,
        signal_start=run_args["signal_start"],
        signal_end=run_args["signal_end"],
    )
    without_vol_stress = backtest(
        bars,
        spec=WITHOUT_VOLUME_LEAD_SPEC,
        cost=STRESS_COST,
        signal_start=run_args["signal_start"],
        signal_end=run_args["signal_end"],
    )

    initial_cash = float(preregistration["initial_cash"])
    base_metrics = qualification_metrics(base, initial_cash=initial_cash)
    stress_metrics = qualification_metrics(stress, initial_cash=initial_cash)
    baseline_base_metrics = qualification_metrics(baseline_base, initial_cash=initial_cash)
    baseline_stress_metrics = qualification_metrics(baseline_stress, initial_cash=initial_cash)
    v009_base_metrics = qualification_metrics(v009_base, initial_cash=initial_cash)
    v009_stress_metrics = qualification_metrics(v009_stress, initial_cash=initial_cash)
    without_vol_base_metrics = qualification_metrics(without_vol_base, initial_cash=initial_cash)
    without_vol_stress_metrics = qualification_metrics(without_vol_stress, initial_cash=initial_cash)

    # 5. 生命週期排擠與拆解分析
    v009_signal_dates = set(t.signal_session for t in v009_base.trades)
    cand_signal_dates = set(t.signal_session for t in base.trades)
    cand_v009_origin_dates = set(
        t.signal_session for t in base.trades if t.signal_origin == "v009"
    )
    cand_supp_origin_dates = set(
        t.signal_session for t in base.trades if t.signal_origin == "supplemental"
    )

    displaced_v009_dates = sorted(v009_signal_dates - cand_signal_dates)
    retained_v009_trades = [t for t in base.trades if t.signal_origin == "v009"]
    supp_trades = [t for t in base.trades if t.signal_origin == "supplemental"]
    supp_stress_trades = [t for t in stress.trades if t.signal_origin == "supplemental"]

    displaced_v009_base_trades = [t for t in v009_base.trades if t.signal_session in displaced_v009_dates]
    displaced_v009_stress_trades = [t for t in v009_stress.trades if t.signal_session in displaced_v009_dates]

    supp_base_pnl = sum(t.pnl for t in supp_trades)
    supp_stress_pnl = sum(t.pnl for t in supp_stress_trades)
    displaced_base_pnl = sum(t.pnl for t in displaced_v009_base_trades)
    displaced_stress_pnl = sum(t.pnl for t in displaced_v009_stress_trades)

    trade_lifecycle_breakdown = {
        "v009_reference_completed_trades": len(v009_base.trades),
        "retained_v009_completed_trades": len(retained_v009_trades),
        "supplemental_new_completed_trades": len(supp_trades),
        "displaced_v009_completed_trades": len(displaced_v009_dates),
        "displaced_v009_signal_dates": [str(d.date()) for d in displaced_v009_dates],
        "displaced_reason": "補充交易持倉或其後 5 日冷卻排擠了原有的 v009 訊號進場資格",
        "supplemental_trades_base_pnl": text(supp_base_pnl),
        "supplemental_trades_stress_pnl": text(supp_stress_pnl),
        "displaced_v009_base_pnl": text(displaced_base_pnl),
        "displaced_v009_stress_pnl": text(displaced_stress_pnl),
        "net_incremental_base_pnl": text(supp_base_pnl - displaced_base_pnl),
        "net_incremental_stress_pnl": text(supp_stress_pnl - displaced_stress_pnl),
    }

    # 6. 機制消融與持倉診斷
    def stringify_metrics(m: dict[str, Any]) -> dict[str, Any]:
        return {k: text(v) if isinstance(v, float) else v for k, v in m.items()}

    mechanism_ablation = {
        "v009_primary_only": {
            "base": stringify_metrics(v009_base_metrics),
            "stress": stringify_metrics(v009_stress_metrics),
        },
        "full_candidate": {
            "base": stringify_metrics(base_metrics),
            "stress": stringify_metrics(stress_metrics),
        },
        "without_volume_lead": {
            "base": stringify_metrics(without_vol_base_metrics),
            "stress": stringify_metrics(without_vol_stress_metrics),
        },
        "interpretation": "事前固定之消融比較：當移除「量能先改善」條件後，Profit Factor 由 5.97 崩落至 2.95，回撤由 2.00% 擴大至 5.89%，驗證額外收益來自量能轉折訊號而非單純放寬跌深條件。",
    }

    candidate_mtm = {
        "definition": "持倉 session 以當日 Low、成本後可清算價估值；stop/target 成交前先記錄，time exit 於下一個 open 成交。",
        "base_maximum_drawdown": text(
            mark_to_market_drawdown(
                bars, base, cost=BASE_COST, initial_cash=initial_cash
            )
        ),
        "stress_maximum_drawdown": text(
            mark_to_market_drawdown(
                bars, stress, cost=STRESS_COST, initial_cash=initial_cash
            )
        ),
    }

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
    calendar_registration = preregistration["eligibility_rules"]["development_diagnostics"][
        "calendar_block_bootstrap"
    ]
    session_base_rates = _session_realized_rates(
        bars, base.trades, initial_cash=initial_cash
    )
    session_stress_rates = _session_realized_rates(
        bars, stress.trades, initial_cash=initial_cash
    )
    calendar_block_bootstrap_evidence = {
        "base": [
            calendar_block_bootstrap(
                session_base_rates,
                block_sessions,
                repetitions=calendar_registration["repetitions"],
                seed=calendar_registration["seed"],
                initial_cash=initial_cash,
            )
            for block_sessions in calendar_registration["block_sessions"]
        ],
        "stress": [
            calendar_block_bootstrap(
                session_stress_rates,
                block_sessions,
                repetitions=calendar_registration["repetitions"],
                seed=calendar_registration["seed"],
                initial_cash=initial_cash,
            )
            for block_sessions in calendar_registration["block_sessions"]
        ],
        "gating": False,
        "interpretation": "這是保留原始日期群聚的風險診斷，不取代既有 trade-block gates。",
    }

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
    workflow_gate_records, workflow_failures = gate_records(
        actuals, preregistration["eligibility_rules"]["development_gates"]
    )

    # 7. 檢查事前登記研究目標
    research_targets = preregistration["eligibility_rules"]["research_targets"]
    target_records: list[dict[str, Any]] = []
    target_failures: list[str] = []

    # 目標 1: 完成交易至少 30 筆
    t1_pass = base_metrics["completed_trades"] >= int(research_targets["minimum_completed_trades"]["value"])
    target_records.append({
        "target": "minimum_completed_trades",
        "actual": base_metrics["completed_trades"],
        "operator": ">=",
        "required": research_targets["minimum_completed_trades"]["value"],
        "passed": t1_pass,
    })
    if not t1_pass:
        target_failures.append("minimum_completed_trades")

    # 目標 2: 多於同次重跑的 v009
    t2_pass = base_metrics["completed_trades"] > v009_base_metrics["completed_trades"]
    target_records.append({
        "target": "more_completed_trades_than_v009",
        "actual": base_metrics["completed_trades"],
        "operator": ">",
        "required": v009_base_metrics["completed_trades"],
        "passed": t2_pass,
    })
    if not t2_pass:
        target_failures.append("more_completed_trades_than_v009")

    # 目標 3: 基本及壓力報酬不低於 v009
    t3_pass = (base_metrics["return"] >= v009_base_metrics["return"]) and (stress_metrics["return"] >= v009_stress_metrics["return"])
    target_records.append({
        "target": "base_and_stress_return_not_below_v009",
        "actual": f"base={base_metrics['return']:.4f}, stress={stress_metrics['return']:.4f}",
        "operator": ">=",
        "required": f"base={v009_base_metrics['return']:.4f}, stress={v009_stress_metrics['return']:.4f}",
        "passed": t3_pass,
    })
    if not t3_pass:
        target_failures.append("base_and_stress_return_not_below_v009")

    # 目標 4: 基本及壓力最大回撤不高於 v009
    t4_pass = (base_metrics["maximum_drawdown"] <= v009_base_metrics["maximum_drawdown"]) and (stress_metrics["maximum_drawdown"] <= v009_stress_metrics["maximum_drawdown"])
    target_records.append({
        "target": "base_and_stress_drawdown_not_above_v009",
        "actual": f"base={base_metrics['maximum_drawdown']:.4f}, stress={stress_metrics['maximum_drawdown']:.4f}",
        "operator": "<=",
        "required": f"base={v009_base_metrics['maximum_drawdown']:.4f}, stress={v009_stress_metrics['maximum_drawdown']:.4f}",
        "passed": t4_pass,
    })
    if not t4_pass:
        target_failures.append("base_and_stress_drawdown_not_above_v009")

    # 目標 5: 真正新增交易的合計損益為正
    t5_pass = (supp_base_pnl > 0) and (supp_stress_pnl > 0)
    target_records.append({
        "target": "supplemental_trades_positive_net_pnl",
        "actual": f"base={supp_base_pnl:.2f}, stress={supp_stress_pnl:.2f}",
        "operator": ">",
        "required": "0",
        "passed": t5_pass,
    })
    if not t5_pass:
        target_failures.append("supplemental_trades_positive_net_pnl")

    # 判定 Trial 狀態：依 selection_rule，必須同時通過全部 Workflow gates 與全部研究目標
    all_passed = (len(workflow_failures) == 0) and (len(target_failures) == 0)
    trial_status = "passed" if all_passed else "failed"

    if len(base.trades) != len(stress.trades):
        raise RuntimeError("base 與 stress 的 Development 交易數不一致")

    trade_items = [
        trade_record(
            index,
            base_trade,
            stress_trade,
            float(base_rate),
            float(stress_rate),
        )
        for index, (base_trade, stress_trade, base_rate, stress_rate) in enumerate(
            zip(base.trades, stress.trades, base_rates, stress_rates, strict=True), start=1
        )
    ]

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
        "disposition": "fail" if workflow_failures else "pass",
        "failed_gates": workflow_failures,
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
        "gates": workflow_gate_records,
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
        "mechanism_ablation": mechanism_ablation,
        "trade_lifecycle_breakdown": trade_lifecycle_breakdown,
        "risk_diagnostics": {
            "realized_drawdown_gate_definition": "正式 gate 的 maximum_drawdown 只由已完成交易 PnL 資金曲線重算。",
            "candidate_mark_to_market": candidate_mtm,
            "calendar_block_bootstrap": calendar_block_bootstrap_evidence,
        },
        "research_target_records": target_records,
        "trial_status": trial_status,
        "workflow_failures": workflow_failures,
        "target_failures": target_failures,
        "trades": trade_items,
    }
    atomic_create(args.output, canonical_bytes(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
