"""只使用 TSM warmup-only 與 Development 快照產生 v016 candidate evidence。

這個 runner 只開啟 2013 warmup 與 2014--2018 Development。它會保存逐筆交易、
逐年分段、leave-one-signal-year-out、固定 seed 的交易區塊 bootstrap，以及事前
指定的量先／價行機制消融與持倉 Low 估值診斷；門檻直接取自 preregistration，
不接受命令列臨時改值。
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

from trading_2026_2 import (
    tsm_mean_reversion_two_stage_volume_reversal_v009 as v009,
)
from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v016 import (
    BASE_COST,
    BASELINE_SPEC,
    DEFAULT_SPEC,
    STRESS_COST,
    V009_ONLY_SPEC,
    Trade,
    backtest,
    indicators,
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

CANDIDATE_ID = "tsm-mr-two-stage-volume-reversal-retest-v016"
BASELINE_ID = "tsm-mean-reversion-two-stage-baseline-v009"
V009_ID = "tsm-mr-two-stage-calibrated-volume-v009"
STUDY_ID = "tsm-mean-reversion-two-stage-volume-reversal--v016"
ENGINE_PATH = "src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v016.py"
PROCEDURE_PATH = f"research/{STUDY_ID}/run_development.py"
ACQUISITION_PATH = f"research/{STUDY_ID}/data-snapshot-acquisition.yml"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="產生 TSM 放量承接後縮量淺回測 v016 2014--2018 Development raw evidence"
    )
    result.add_argument("--warmup", type=Path, required=True)
    result.add_argument("--development", type=Path, required=True)
    result.add_argument("--preregistration", type=Path, required=True)
    result.add_argument("--trial-inputs", type=Path, required=True)
    result.add_argument("--comparison-evidence", type=Path, required=True)
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


def _session_realized_rates(
    bars: pd.DataFrame, trades: tuple[Trade, ...], *, initial_cash: float
) -> np.ndarray:
    """把已完成交易 PnL 放回其 exit session，保留日期上的交易群聚。"""

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


def maximum_loss_fraction(trades: tuple[Trade, ...], *, initial_cash: float) -> float:
    rates = trade_rates(trades, initial_cash)
    return max((float(-rate) for rate in rates if rate < 0), default=0.0)


def downside_wave_labels(frame: pd.DataFrame) -> dict[pd.Timestamp, str]:
    """以固定的均線下方連續區段標記下跌波段。

    收盤高於 SMA(20) 連續五個 session 才結束波段；這個定義在看結果前
    固定，避免把同一波連續接刀當成多個獨立機會。
    """

    labels: dict[pd.Timestamp, str] = {}
    wave_number = 0
    active_wave: str | None = None
    above_streak = 5
    for session, row in frame.iterrows():
        below_sma = bool(pd.notna(row["sma_20"]) and row["Close"] <= row["sma_20"])
        if below_sma:
            if active_wave is None or above_streak >= 5:
                wave_number += 1
                active_wave = f"wave-{wave_number:03d}"
            above_streak = 0
            labels[session] = active_wave
        else:
            above_streak += 1
            labels[session] = active_wave or "outside-wave"
            if above_streak >= 5:
                active_wave = None
    return labels


def new_trade_concentration(
    comparison: dict[str, object], frame: pd.DataFrame
) -> dict[str, object]:
    labels = downside_wave_labels(frame)
    added_rows = comparison["truly_added"]
    year_counts: dict[str, int] = defaultdict(int)
    wave_counts: dict[str, int] = defaultdict(int)
    for row in added_rows:
        signal = pd.Timestamp(row["signal_session"])
        year_counts[str(signal.year)] += 1
        wave_counts[labels[signal]] += 1
    total = len(added_rows)
    year_shares = {
        year: text(count / total) for year, count in sorted(year_counts.items())
    } if total else {}
    wave_shares = {
        wave: text(count / total) for wave, count in sorted(wave_counts.items())
    } if total else {}
    return {
        "wave_definition": "Close <= SMA(20) 的連續區段；只有 Close > SMA(20) 連續五個 XNYS session 才結束波段。",
        "new_trade_count": total,
        "new_trade_signal_year_counts": dict(sorted(year_counts.items())),
        "new_trade_signal_year_shares": year_shares,
        "new_trade_wave_counts": dict(sorted(wave_counts.items())),
        "new_trade_wave_shares": wave_shares,
        "new_trade_signal_years": len(year_counts),
        "maximum_new_trade_signal_year_share": text(max((float(value) for value in year_shares.values()), default=0.0)),
        "maximum_new_trade_wave_share": text(max((float(value) for value in wave_shares.values()), default=0.0)),
    }


def strategy_summary(
    bars: pd.DataFrame, spec: object, *, initial_cash: float
) -> dict[str, object]:
    """以同一執行與成本規則產生有限機制消融的摘要。"""

    run_args = {
        "signal_start": "2014-01-01",
        "signal_end": "2018-12-31",
        "spec": spec,
    }
    base = backtest(bars, cost=BASE_COST, **run_args)
    stress = backtest(bars, cost=STRESS_COST, **run_args)
    if len(base.trades) != len(stress.trades):
        raise RuntimeError("機制消融的 base 與 stress 交易生命週期數量不一致")
    return {
        "accepted_signal_count": len(base.accepted_signal_sessions),
        "base": {
            key: text(value) if isinstance(value, float) else value
            for key, value in qualification_metrics(base, initial_cash=initial_cash).items()
        },
        "stress": {
            key: text(value) if isinstance(value, float) else value
            for key, value in qualification_metrics(stress, initial_cash=initial_cash).items()
        },
    }


def engine_summary(
    engine: object, bars: pd.DataFrame, spec: object, *, initial_cash: float
) -> dict[str, object]:
    """以指定已允許 engine 產生只供比較的摘要。"""

    run_args = {
        "signal_start": "2014-01-01",
        "signal_end": "2018-12-31",
        "spec": spec,
    }
    base = engine.backtest(bars, cost=engine.BASE_COST, **run_args)
    stress = engine.backtest(bars, cost=engine.STRESS_COST, **run_args)
    if len(base.trades) != len(stress.trades):
        raise RuntimeError("對照組 base 與 stress 交易生命週期數量不一致")
    return {
        "accepted_signal_count": len(base.accepted_signal_sessions),
        "base": {
            key: text(value) if isinstance(value, float) else value
            for key, value in engine.qualification_metrics(
                base, initial_cash=initial_cash
            ).items()
        },
        "stress": {
            key: text(value) if isinstance(value, float) else value
            for key, value in engine.qualification_metrics(
                stress, initial_cash=initial_cash
            ).items()
        },
    }


def trade_record(
    index: int,
    base_trade: Trade,
    stress_trade: Trade,
    base_rate: float,
    stress_rate: float,
    entry_mode: str,
    volume_event_session: pd.Timestamp | None,
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
        "entry_mode": entry_mode,
        "volume_event_session": (
            None if volume_event_session is None else str(volume_event_session.date())
        ),
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


def lifecycle_key(trade: object) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, str]:
    return (
        trade.signal_session,
        trade.entry_session,
        trade.exit_session,
        trade.exit_reason,
    )


def _trade_map(trades: tuple[Trade, ...], label: str) -> dict[tuple, Trade]:
    result: dict[tuple, Trade] = {}
    for trade in trades:
        key = lifecycle_key(trade)
        if key in result:
            raise RuntimeError(f"{label} 含有重複交易生命週期")
        result[key] = trade
    return result


def _paired_trade_map(
    base_trades: tuple[Trade, ...], stress_trades: tuple[Trade, ...], label: str
) -> dict[tuple, tuple[Trade, Trade]]:
    base_map = _trade_map(base_trades, f"{label} base")
    stress_map = _trade_map(stress_trades, f"{label} stress")
    if set(base_map) != set(stress_map):
        raise RuntimeError(f"{label} base 與 stress 的交易生命週期不一致")
    return {key: (base_map[key], stress_map[key]) for key in base_map}


def trade_comparison(
    candidate_base: tuple[Trade, ...],
    candidate_stress: tuple[Trade, ...],
    control_base: tuple[Trade, ...],
    control_stress: tuple[Trade, ...],
    development_sessions: pd.DatetimeIndex,
    cooldown_sessions: int,
) -> dict[str, object]:
    candidate = _paired_trade_map(candidate_base, candidate_stress, "candidate")
    control = _paired_trade_map(control_base, control_stress, "v009 control")
    retained_keys = sorted(set(candidate) & set(control))
    added_keys = sorted(set(candidate) - set(control))
    control_only_keys = sorted(set(control) - set(candidate))
    session_numbers = {session: number for number, session in enumerate(development_sessions)}

    def session_number(session: pd.Timestamp) -> int:
        if session not in session_numbers:
            raise RuntimeError(f"交易 session 不在固定 Development calendar: {session}")
        return session_numbers[session]

    def identity(prefix: str, key: tuple) -> str:
        return f"{prefix}-{key[0].date()}-{key[1].date()}-{key[2].date()}-{key[3]}"

    def row(key: tuple, pair: tuple[Trade, Trade], *, kind: str) -> dict[str, object]:
        base_trade, stress_trade = pair
        return {
            "trade_id": identity("candidate" if kind == "truly_added" else "control", key),
            "classification": kind,
            "signal_session": str(key[0].date()),
            "entry_session": str(key[1].date()),
            "exit_session": str(key[2].date()),
            "exit_reason": key[3],
            "base_pnl": text(base_trade.pnl),
            "stress_pnl": text(stress_trade.pnl),
        }

    added_rows = [row(key, candidate[key], kind="truly_added") for key in added_keys]
    retained_rows = [row(key, candidate[key], kind="retained") for key in retained_keys]
    unmatched_control = set(control_only_keys)
    pairings: list[dict[str, object]] = []
    for added_key in added_keys:
        added_signal = session_number(added_key[0])
        added_exit = session_number(added_key[2])
        eligible = [
            key
            for key in sorted(unmatched_control)
            if added_signal < session_number(key[0])
            <= added_exit + cooldown_sessions
        ]
        if not eligible:
            continue
        displaced_key = eligible[0]
        unmatched_control.remove(displaced_key)
        pairings.append(
            {
                "candidate_trade_id": identity("candidate", added_key),
                "control_trade_id": identity("control", displaced_key),
                "candidate_signal_session": str(added_key[0].date()),
                "control_signal_session": str(displaced_key[0].date()),
                "reason": "control_signal_falls_during_candidate_holding_or_post_exit_cooldown",
            }
        )
    paired_control_keys = [
        next(
            key
            for key in control_only_keys
            if identity("control", key) == pairing["control_trade_id"]
        )
        for pairing in pairings
    ]
    displaced_rows = [
        row(key, control[key], kind="v009_only_displaced") for key in paired_control_keys
    ]
    unpaired_control_rows = [
        row(key, control[key], kind="v009_only_unpaired")
        for key in control_only_keys
        if key not in paired_control_keys
    ]
    retained_base_pnl_delta = sum(
        candidate[key][0].pnl - control[key][0].pnl for key in retained_keys
    )
    retained_stress_pnl_delta = sum(
        candidate[key][1].pnl - control[key][1].pnl for key in retained_keys
    )
    added_base_pnl = sum(float(item["base_pnl"]) for item in added_rows)
    added_stress_pnl = sum(float(item["stress_pnl"]) for item in added_rows)
    displaced_base_pnl = sum(float(item["base_pnl"]) for item in displaced_rows)
    displaced_stress_pnl = sum(float(item["stress_pnl"]) for item in displaced_rows)
    all_control_only_base_pnl = sum(control[key][0].pnl for key in control_only_keys)
    all_control_only_stress_pnl = sum(control[key][1].pnl for key in control_only_keys)
    return {
        "matching_method": "exact-lifecycle-key-then-pre-registered-temporal-pairing",
        "lifecycle_key_fields": [
            "signal_session",
            "entry_session",
            "exit_session",
            "exit_reason",
        ],
        "candidate_trade_count": len(candidate),
        "v009_trade_count": len(control),
        "retained_trade_count": len(retained_rows),
        "truly_added_trade_count": len(added_rows),
        "v009_only_displaced_trade_count": len(displaced_rows),
        "v009_only_unpaired_trade_count": len(unpaired_control_rows),
        "retained": retained_rows,
        "truly_added": added_rows,
        "v009_only_displaced": displaced_rows,
        "v009_only_unpaired": unpaired_control_rows,
        "pairings": pairings,
        "truly_added_aggregate_pnl": {
            "base": text(added_base_pnl),
            "stress": text(added_stress_pnl),
        },
        "paired_displaced_aggregate_pnl": {
            "base": text(displaced_base_pnl),
            "stress": text(displaced_stress_pnl),
        },
        "retained_pnl_delta_after_equity_or_timing_change": {
            "base": text(retained_base_pnl_delta),
            "stress": text(retained_stress_pnl_delta),
        },
        "all_control_only_aggregate_pnl": {
            "base": text(all_control_only_base_pnl),
            "stress": text(all_control_only_stress_pnl),
            "definition": "所有未在 candidate 完成相同生命週期的 v009 completed trade 均保守視為被排擠或時點改變，不因無法配對而忽略。",
        },
        "net_new_minus_displaced": {
            "base": text(
                added_base_pnl
                + retained_base_pnl_delta
                - all_control_only_base_pnl
            ),
            "stress": text(
                added_stress_pnl
                + retained_stress_pnl_delta
                - all_control_only_stress_pnl
            ),
            "base_strictly_positive": (
                added_base_pnl + retained_base_pnl_delta - all_control_only_base_pnl > 0
            ),
            "stress_strictly_positive": (
                added_stress_pnl
                + retained_stress_pnl_delta
                - all_control_only_stress_pnl
                > 0
            ),
            "formula": "candidate-only completed PnL + retained candidate/control PnL delta - all v009-only completed PnL",
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
    comparison_evidence = load_canonical(args.comparison_evidence)
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
    comparison_registration = preregistration["eligibility_rules"]["comparison_control"]
    if args.comparison_evidence.resolve() != _repository_path(
        comparison_registration["development_evidence_path"]
    ):
        raise RuntimeError("comparison control evidence path 與 preregistration 不一致")
    comparison_digest = digest(args.comparison_evidence)
    _assert_equal(
        "comparison control evidence",
        comparison_digest,
        comparison_registration["development_evidence_digest"],
    )
    if comparison_evidence["candidate_id"] != V009_ID:
        raise RuntimeError("comparison control evidence candidate identity 不正確")
    if inputs["data_bindings"]["comparison_control_path"] != comparison_registration[
        "development_evidence_path"
    ]:
        raise RuntimeError("Development inputs comparison control path 不一致")
    if inputs["data_bindings"]["comparison_control_digest"] != comparison_digest:
        raise RuntimeError("Development inputs comparison control digest 不一致")
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
    calendar_registration = preregistration["eligibility_rules"]["development_diagnostics"][
        "calendar_block_bootstrap"
    ]
    calendar_inputs = diagnostics["calendar_block_bootstrap"]
    if calendar_inputs["block_sessions"] != calendar_registration["block_sessions"]:
        raise RuntimeError("calendar bootstrap block sessions 與 preregistration 不一致")
    if calendar_inputs["repetitions"] != calendar_registration["repetitions"]:
        raise RuntimeError("calendar bootstrap repetitions 與 preregistration 不一致")
    if calendar_inputs["bootstrap_seed"] != calendar_registration["seed"]:
        raise RuntimeError("calendar bootstrap seed 與 preregistration 不一致")
    if calendar_inputs["seed_application"] != "exact-same-seed-for-each-block-length":
        raise RuntimeError("calendar bootstrap seed application 不正確")
    return {
        "acquisition_manifest_digest": acquisition_digest,
        "comparison_control_evidence_digest": comparison_digest,
        "comparison_control_evidence_path": comparison_registration[
            "development_evidence_path"
        ],
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
    comparison_evidence = load_canonical(args.comparison_evidence)
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
    v009_base = v009.backtest(
        bars,
        spec=v009.DEFAULT_SPEC,
        cost=v009.BASE_COST,
        signal_start=run_args["signal_start"],
        signal_end=run_args["signal_end"],
    )
    v009_stress = v009.backtest(
        bars,
        spec=v009.DEFAULT_SPEC,
        cost=v009.STRESS_COST,
        signal_start=run_args["signal_start"],
        signal_end=run_args["signal_end"],
    )
    v009_only_base = backtest(
        bars,
        spec=V009_ONLY_SPEC,
        cost=BASE_COST,
        signal_start=run_args["signal_start"],
        signal_end=run_args["signal_end"],
    )
    v009_only_stress = backtest(
        bars,
        spec=V009_ONLY_SPEC,
        cost=STRESS_COST,
        signal_start=run_args["signal_start"],
        signal_end=run_args["signal_end"],
    )

    def lifecycle_signatures(result: object) -> list[tuple[object, ...]]:
        return [
            (
                trade.signal_session,
                trade.entry_session,
                trade.exit_session,
                trade.exit_reason,
            )
            for trade in result.trades
        ]

    if lifecycle_signatures(v009_only_base) != lifecycle_signatures(v009_base):
        raise RuntimeError("v016 關閉補充路徑後，base 原有路徑未逐筆重現 v009")
    if lifecycle_signatures(v009_only_stress) != lifecycle_signatures(v009_stress):
        raise RuntimeError("v016 關閉補充路徑後，stress 原有路徑未逐筆重現 v009")
    if v009_only_base.accepted_signal_sessions != v009_base.accepted_signal_sessions:
        raise RuntimeError("v016 關閉補充路徑後，base accepted signals 未逐筆重現 v009")
    if v009_only_stress.accepted_signal_sessions != v009_stress.accepted_signal_sessions:
        raise RuntimeError("v016 關閉補充路徑後，stress accepted signals 未逐筆重現 v009")
    initial_cash = float(preregistration["initial_cash"])
    base_metrics = qualification_metrics(base, initial_cash=initial_cash)
    stress_metrics = qualification_metrics(stress, initial_cash=initial_cash)
    control_evidence_metrics = comparison_evidence["metrics"]
    for label, metrics, expected in (
        ("base", qualification_metrics(v009_base, initial_cash=initial_cash), control_evidence_metrics["base"]),
        ("stress", qualification_metrics(v009_stress, initial_cash=initial_cash), control_evidence_metrics["stress"]),
    ):
        for key in ("completed_trades", "return", "profit_factor", "maximum_drawdown", "traded_years"):
            if Decimal(str(metrics[key])) != Decimal(str(expected[key])):
                raise RuntimeError(
                    f"v009 control {label}.{key} 與原始 Development evidence 不一致"
                )
    baseline_base_metrics = qualification_metrics(baseline_base, initial_cash=initial_cash)
    baseline_stress_metrics = qualification_metrics(baseline_stress, initial_cash=initial_cash)
    mechanism_ablation = {
        "v016_combined_path": strategy_summary(
            bars, DEFAULT_SPEC, initial_cash=initial_cash
        ),
        "v009_original_path_only": strategy_summary(
            bars, V009_ONLY_SPEC, initial_cash=initial_cash
        ),
        "simple_baseline": strategy_summary(
            bars, BASELINE_SPEC, initial_cash=initial_cash
        ),
        "v009_frozen_control_engine": engine_summary(
            v009, bars, v009.DEFAULT_SPEC, initial_cash=initial_cash
        ),
        "interpretation": "事前固定的描述性比較，不參與 candidate selection；v016 與固定 v009 使用同一份 Development 資料、相同成本與執行規則，唯一機制變更是補充的縮量淺回測路徑。",
    }
    trade_comparison_evidence = trade_comparison(
        base.trades,
        stress.trades,
        v009_base.trades,
        v009_stress.trades,
        development.index,
        DEFAULT_SPEC.cooldown_sessions,
    )
    control_comparison = {
        "v009": engine_summary(v009, bars, v009.DEFAULT_SPEC, initial_cash=initial_cash),
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
    control_mtm = {
        "base_maximum_drawdown": text(
            v009.mark_to_market_drawdown(
                bars, v009_base, cost=v009.BASE_COST, initial_cash=initial_cash
            )
        ),
        "stress_maximum_drawdown": text(
            v009.mark_to_market_drawdown(
                bars, v009_stress, cost=v009.STRESS_COST, initial_cash=initial_cash
            )
        ),
    }
    expected_control_mtm = comparison_evidence["risk_diagnostics"][
        "candidate_mark_to_market"
    ]
    for key in ("base_maximum_drawdown", "stress_maximum_drawdown"):
        if Decimal(str(control_mtm[key])) != Decimal(str(expected_control_mtm[key])):
            raise RuntimeError(f"v009 control mark-to-market {key} 與原始 evidence 不一致")
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
    gates, failures = gate_records(
        actuals, preregistration["eligibility_rules"]["development_gates"]
    )
    candidate_frame = indicators(bars, DEFAULT_SPEC)
    if [trade.signal_origin for trade in base.trades] != [
        trade.signal_origin for trade in stress.trades
    ]:
        raise RuntimeError("candidate base 與 stress 的 signal origin 不一致")
    if base.supplemental_event_sessions != stress.supplemental_event_sessions:
        raise RuntimeError("candidate base 與 stress 的 volume event 不一致")
    if base.supplemental_diagnostics != stress.supplemental_diagnostics:
        raise RuntimeError("candidate base 與 stress 的 event lifecycle 不一致")
    entry_mode_counts = dict(
        sorted(
            {
                origin: sum(
                    1 for trade in base.trades if trade.signal_origin == origin
                )
                for origin in {trade.signal_origin for trade in base.trades}
            }.items()
        )
    )
    concentration = new_trade_concentration(trade_comparison_evidence, candidate_frame)
    net_new_minus_displaced = trade_comparison_evidence["net_new_minus_displaced"]

    research_target_actuals: dict[str, str | int | float] = {
        "base_mark_to_market_drawdown_not_above_v009": float(
            candidate_mtm["base_maximum_drawdown"]
        ),
        "base_profit_factor_not_below_v009": base_metrics["profit_factor"],
        "base_realized_drawdown_not_above_v009": base_metrics["maximum_drawdown"],
        "base_return_not_below_v009": base_metrics["return"],
        "completed_trades_at_least_30": base_metrics["completed_trades"],
        "completed_trades_more_than_v009": trade_comparison_evidence[
            "candidate_trade_count"
        ],
        "max_new_trade_signal_year_share": float(
            concentration["maximum_new_trade_signal_year_share"]
        ),
        "max_new_trade_wave_share": float(
            concentration["maximum_new_trade_wave_share"]
        ),
        "net_new_minus_displaced_base_pnl_positive": float(
            net_new_minus_displaced["base"]
        ),
        "net_new_minus_displaced_stress_pnl_positive": float(
            net_new_minus_displaced["stress"]
        ),
        "new_trade_count_at_least_one": trade_comparison_evidence[
            "truly_added_trade_count"
        ],
        "new_trade_signal_years_at_least_three": concentration[
            "new_trade_signal_years"
        ],
        "stress_mark_to_market_drawdown_not_above_v009": float(
            candidate_mtm["stress_maximum_drawdown"]
        ),
        "stress_profit_factor_not_below_v009": stress_metrics["profit_factor"],
        "stress_realized_drawdown_not_above_v009": stress_metrics[
            "maximum_drawdown"
        ],
        "stress_return_at_least_30_40_percent": stress_metrics["return"],
        "stress_return_not_below_v009": stress_metrics["return"],
    }
    target_rules = preregistration["eligibility_rules"]["research_targets"]
    if set(research_target_actuals) != set(target_rules):
        raise RuntimeError("research target actuals 與 preregistration 不一致")
    research_target_records = []
    for name, rule in target_rules.items():
        actual = research_target_actuals[name]
        research_target_records.append(
            {
                "target": name,
                "actual": actual if isinstance(actual, int) else text(float(actual)),
                "operator": rule["operator"],
                "required": rule["value"],
                "passed": compare(actual, rule["operator"], rule["value"]),
            }
        )
    target_failures = [
        record["target"] for record in research_target_records if not record["passed"]
    ]
    candidate_selection_eligible = not failures and not target_failures

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
        "research_target_records": research_target_records,
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
            "entry_mode_counts": entry_mode_counts,
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
        "reference_controls": control_comparison,
        "trade_comparison": trade_comparison_evidence,
        "signal_path_diagnostics": {
            "definition": "原有路徑與補充路徑在收盤確認時分辨；補充事件先於價格確認，事件於第一次確認即消耗，無法成交也不重用。",
            "base_event_lifecycle": base.supplemental_diagnostics,
            "stress_event_lifecycle": stress.supplemental_diagnostics,
            "completed_trade_origin_counts": entry_mode_counts,
            "completed_supplemental_trade_signal_sessions": [
                str(trade.signal_session.date())
                for trade in base.trades
                if trade.signal_origin == "supplemental"
            ],
            "completed_supplemental_event_sessions": [
                None if event is None else str(event.date())
                for event in base.supplemental_event_sessions
                if event is not None
            ],
            "primary_path_lifecycle_matches_v009": True,
        },
        "candidate_selection": {
            "eligible_after_formal_gates_and_pre_registered_added_trade_target": candidate_selection_eligible,
            "formal_gate_failures": failures,
            "research_target_failures": target_failures,
            "entry_mode_counts": entry_mode_counts,
            "new_trade_concentration": concentration,
            "requirements": {
                "minimum_completed_trades": 30,
                "stress_return_at_least_30_40_percent": "0.3040",
                "stress_return_at_least_v009": "0.2652316915038563",
                "stress_profit_factor_at_least_v009": "4.204178313326042",
                "net_new_minus_displaced_base_pnl": "> 0",
                "net_new_minus_displaced_stress_pnl": "> 0",
            },
        },
        "risk_diagnostics": {
            "realized_drawdown_gate_definition": "正式 gate 的 maximum_drawdown 只由已完成交易 PnL 資金曲線重算。",
            "candidate_mark_to_market": candidate_mtm,
            "calendar_block_bootstrap": calendar_block_bootstrap_evidence,
        },
        "trades": [
            trade_record(
                index,
                base_trade,
                stress_trade,
                base_rate,
                stress_rate,
                base_trade.signal_origin,
                base.supplemental_event_sessions[index - 1],
            )
            for index, (base_trade, stress_trade, base_rate, stress_rate) in enumerate(
                zip(base.trades, stress.trades, base_rates, stress_rates, strict=True), start=1
            )
        ],
    }
    evidence = finalize_development_evidence(evidence, preregistration)
    atomic_create(args.output, canonical_bytes(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
