"""產生 TSM Bollinger 事件反彈 v002 的 2014--2018 Development raw evidence。

這個 runner 只讀取已固定的 2013 warmup 與 2014--2018 Development view，不讀取
quarantine 或 Historical Evaluation 內容，也不連線資料提供者。候選規則、比較組、
機制消融、成本情境與 bootstrap 設定均由 preregistration 與 trial inputs 綁定；
不接受命令列臨時調整門檻。output 已存在時一律拒絕覆寫。
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

from trading_2026_2.tsm_mean_reversion_bollinger_rebound_v001 import (
    DEFAULT_SPEC as BOLLINGER_V001_SPEC,
)
from trading_2026_2.tsm_mean_reversion_bollinger_rebound_v001 import (
    backtest as bollinger_v001_backtest,
)
from trading_2026_2.tsm_mean_reversion_bollinger_rebound_v001 import (
    qualification_metrics as bollinger_v001_metrics,
)
from trading_2026_2.tsm_mean_reversion_bollinger_rebound_v002 import (
    BASE_COST,
    BASELINE_SPEC,
    DEFAULT_SPEC,
    REMEMBERED_EVENT_NO_QUIET_SPEC,
    SAME_DAY_EVENT_NO_MEMORY_SPEC,
    STRESS_COST,
    Trade,
    backtest,
    mark_to_market_drawdown,
    qualification_metrics,
)
from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v009 import (
    DEFAULT_SPEC as V009_SPEC,
)
from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v009 import (
    backtest as v009_backtest,
)
from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v009 import (
    qualification_metrics as v009_metrics,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import atomic_create, canonical_bytes, load_canonical  # noqa: E402

CANDIDATE_ID = "tsm-mr-bollinger-event-rebound-v002"
BASELINE_ID = "tsm-mr-bollinger-simple-baseline-v002"
STUDY_ID = "tsm-mean-reversion-bollinger-rebound--v002"
ENGINE_PATH = "src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v002.py"
V009_ENGINE_PATH = "src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py"
BOLLINGER_V001_ENGINE_PATH = "src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v001.py"
PROCEDURE_PATH = f"research/{STUDY_ID}/run_development.py"
ACQUISITION_PATH = f"research/{STUDY_ID}/data-snapshot-acquisition.yml"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="產生 TSM Bollinger event rebound v002 2014--2018 Development raw evidence"
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


def repository_path(relative_path: str) -> Path:
    path = (REPOSITORY_ROOT / relative_path).resolve()
    try:
        path.relative_to(REPOSITORY_ROOT)
    except ValueError as exc:
        raise RuntimeError(f"路徑逃出 repository: {relative_path}") from exc
    return path


def source_lines_digest(path: Path, start: str, end: str) -> str:
    """保留原始 CSV 行 bytes，計算指定日期 view 的內容定址 digest。"""

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


def read_reference_view(path: Path, start: str, end: str) -> pd.DataFrame:
    """從同一份 immutable snapshot 只保留指定日期 view。"""

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
        path = item["path"]
        if path in entries:
            raise RuntimeError(f"Source Bundle 含有重複 path: {path}")
        entries[path] = item["digest"]
    return entries


def assert_equal(label: str, actual: str, expected: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label} digest 不一致: expected={expected}, actual={actual}")


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
    assert_equal("Source Bundle", args.source_bundle_digest, source_bundle_digest)
    assert_equal("acquisition manifest", args.acquisition_digest, acquisition_digest)
    assert_equal("preregistration", args.preregistration_digest, preregistration_digest)
    assert_equal("trial inputs", args.trial_inputs_digest, trial_inputs_digest)

    entries = source_bundle_entries(source_bundle)
    for relative_path, expected_digest in entries.items():
        path = repository_path(relative_path)
        if not path.is_file():
            raise RuntimeError(f"Source Bundle file 不存在: {relative_path}")
        assert_equal(f"Source Bundle {relative_path}", digest(path), expected_digest)
    engine_digest = digest(repository_path(ENGINE_PATH))
    assert_equal("strategy engine", args.strategy_engine_digest, engine_digest)
    assert_equal("strategy engine 與 Source Bundle", engine_digest, entries[ENGINE_PATH])
    assert_equal(
        "study procedure 與 Source Bundle",
        digest(repository_path(PROCEDURE_PATH)),
        entries[PROCEDURE_PATH],
    )
    for reference_path in (V009_ENGINE_PATH, BOLLINGER_V001_ENGINE_PATH):
        assert_equal(
            f"reference engine {reference_path}",
            digest(repository_path(reference_path)),
            entries[reference_path],
        )

    if preregistration["selection_rule"]["selected_candidate_id"] != CANDIDATE_ID:
        raise RuntimeError("preregistration 的 candidate identity 不正確")
    if inputs["candidate_id"] != CANDIDATE_ID:
        raise RuntimeError("Development inputs 的 candidate identity 不正確")
    if inputs["preregistration_digest"] != args.preregistration_digest:
        raise RuntimeError("Development inputs 未綁定同一份 preregistration")
    if inputs["source_bundle_digest"] != args.source_bundle_digest:
        raise RuntimeError("Development inputs 未綁定同一份 Source Bundle")

    data_bindings = inputs["data_bindings"]
    warmup_path = repository_path(data_bindings["warmup_path"])
    development_path = repository_path(data_bindings["development_path"])
    if args.warmup.resolve() != warmup_path:
        raise RuntimeError("warmup path 與 Development inputs 不一致")
    if args.development.resolve() != development_path:
        raise RuntimeError("Development path 與 Development inputs 不一致")
    roles = acquisition["roles"]
    if data_bindings["warmup_path"] != roles["warmup-only"]["source_path"]:
        raise RuntimeError("warmup path 與 acquisition manifest 不一致")
    if data_bindings["development_path"] != roles["development"]["source_path"]:
        raise RuntimeError("Development path 與 acquisition manifest 不一致")
    warmup_digest = source_lines_digest(args.warmup, "2013-01-01", "2013-12-31")
    development_digest = source_lines_digest(args.development, "2014-01-01", "2018-12-31")
    assert_equal("warmup data", warmup_digest, data_bindings["warmup_digest"])
    assert_equal("Development data", development_digest, data_bindings["development_digest"])
    assert_equal("warmup data 與 acquisition", warmup_digest, roles["warmup-only"]["data_digest"])
    assert_equal(
        "Development data 與 acquisition",
        development_digest,
        roles["development"]["data_digest"],
    )
    full_snapshot = acquisition["full_snapshot"]
    full_path = repository_path(full_snapshot["path"])
    assert_equal("full market-data snapshot", digest(full_path), full_snapshot["digest"])
    assert_equal("acquisition 與 Source Bundle", acquisition_digest, entries[ACQUISITION_PATH])

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
        "return_q05_q50_q95": [text(value) for value in np.quantile(returns, [0.05, 0.5, 0.95])],
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


def lifecycle_key(trade: Any) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, str]:
    return (
        trade.signal_session,
        trade.entry_session,
        trade.exit_session,
        trade.exit_reason,
    )


def precise_return(trades: tuple[Any, ...], initial_cash: float) -> Decimal:
    total = sum((Decimal(str(trade.pnl)) for trade in trades), Decimal("0"))
    return total / Decimal(str(initial_cash))


def decimal_text(value: Decimal) -> str:
    return format(value, "f")


def metric_texts(values: dict[str, Any]) -> dict[str, Any]:
    return {
        key: text(value) if isinstance(value, float) else value
        for key, value in values.items()
    }


def strategy_summary(bars: pd.DataFrame, spec: object, *, initial_cash: float) -> dict[str, object]:
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
        "accepted_signal_count": len(base.trades),
        "event_audit": event_audit_summary(base.event_audit),
        "base": metric_texts(qualification_metrics(base, initial_cash=initial_cash)),
        "stress": metric_texts(qualification_metrics(stress, initial_cash=initial_cash)),
    }


def event_audit_summary(audit: Any) -> dict[str, object]:
    records = list(audit.records)
    outcomes: dict[str, int] = defaultdict(int)
    for record in records:
        outcomes[str(record.get("outcome"))] += 1
    return {
        "volume_drop_events": audit.volume_drop_events,
        "quiet_hold_events": audit.quiet_hold_events,
        "rebound_confirmations": audit.rebound_confirmations,
        "invalidated_events": audit.invalidated_events,
        "expired_events": audit.expired_events,
        "actual_entries": audit.actual_entries,
        "ignored_events_while_active": audit.ignored_events_while_active,
        "ignored_events_while_unavailable": audit.ignored_events_while_unavailable,
        "event_outcomes": dict(sorted(outcomes.items())),
        "definitions": {
            "volume_drop_events": "符合 Bollinger %B <= 0.25 且當日量 >= 前 20 日均量 1.05 倍、且在空手且冷卻完成時建立的事件。",
            "quiet_hold_events": "事件後五個 session 內，量嚴格小於事件日且收盤不低於事件日 Low 的事件數。",
            "rebound_confirmations": "完成守低後，第一次收盤高於前日且低於 SMA20 至少 1.5% 的確認數；確認不再要求 %B 或 RSI。",
            "invalidated_events": "觀察期內任一天收盤低於事件日 Low；失效優先於同日其他狀態。",
            "actual_entries": "確認後下一個 XNYS open 實際取得正整數股數的成交數。",
            "ignored_events_while_unavailable": "持倉、待進場、冷卻或非正式訊號日期時未建立記憶的放量條件數；不把它們當成獨立交易機會。",
        },
    }


def trade_record(
    index: int,
    base_trade: Trade,
    stress_trade: Trade,
    base_rate: float,
    stress_rate: float,
) -> dict[str, object]:
    if lifecycle_key(base_trade) != lifecycle_key(stress_trade):
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
        "event_session": (
            str(base_trade.event_session.date()) if base_trade.event_session is not None else None
        ),
        "quiet_hold_session": (
            str(base_trade.quiet_hold_session.date())
            if base_trade.quiet_hold_session is not None
            else None
        ),
        "confirmation_type": base_trade.confirmation_type,
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


def compact_trade_record(base_trade: Any, stress_trade: Any) -> dict[str, object]:
    if lifecycle_key(base_trade) != lifecycle_key(stress_trade):
        raise RuntimeError("比較組 base 與 stress 的交易生命週期不一致")
    result: dict[str, object] = {
        "signal_session": str(base_trade.signal_session.date()),
        "entry_session": str(base_trade.entry_session.date()),
        "exit_session": str(base_trade.exit_session.date()),
        "exit_reason": base_trade.exit_reason,
        "base_pnl": text(base_trade.pnl),
        "stress_pnl": text(stress_trade.pnl),
    }
    if hasattr(base_trade, "event_session"):
        result.update(
            {
                "event_session": (
                    str(base_trade.event_session.date())
                    if base_trade.event_session is not None
                    else None
                ),
                "quiet_hold_session": (
                    str(base_trade.quiet_hold_session.date())
                    if base_trade.quiet_hold_session is not None
                    else None
                ),
                "confirmation_type": base_trade.confirmation_type,
            }
        )
    return result


def session_distance(sessions: pd.Index, left: pd.Timestamp, right: pd.Timestamp) -> int:
    indexes = {value: index for index, value in enumerate(sessions)}
    if left not in indexes or right not in indexes:
        return 10_000
    return indexes[right] - indexes[left]


def trade_comparison(
    candidate_base: tuple[Trade, ...],
    candidate_stress: tuple[Trade, ...],
    v009_base: tuple[Any, ...],
    v009_stress: tuple[Any, ...],
    *,
    development_sessions: pd.Index,
) -> dict[str, object]:
    """以完整生命週期 key 區分保留、新增、被取代及排擠原因。"""

    candidate_stress_by_key = {lifecycle_key(trade): trade for trade in candidate_stress}
    v009_stress_by_key = {lifecycle_key(trade): trade for trade in v009_stress}
    candidate_by_key = {lifecycle_key(trade): trade for trade in candidate_base}
    v009_by_key = {lifecycle_key(trade): trade for trade in v009_base}
    if len(candidate_by_key) != len(candidate_base) or len(v009_by_key) != len(v009_base):
        raise RuntimeError("交易生命週期 key 不唯一，無法建立比較分類")

    retained: list[dict[str, object]] = []
    added: list[dict[str, object]] = []
    displaced: list[dict[str, object]] = []
    for trade in candidate_base:
        key = lifecycle_key(trade)
        item = compact_trade_record(trade, candidate_stress_by_key[key])
        (retained if key in v009_by_key else added).append(item)

    displacement_reason_counts: dict[str, int] = defaultdict(int)
    for trade in v009_base:
        key = lifecycle_key(trade)
        if key in candidate_by_key:
            continue
        item = compact_trade_record(trade, v009_stress_by_key[key])
        reasons: set[str] = set()
        for candidate_trade in candidate_base:
            if (
                candidate_trade.entry_session <= trade.signal_session
                <= candidate_trade.exit_session
            ):
                reasons.add("candidate_holding")
            if (
                candidate_trade.exit_session < trade.signal_session
                and 0
                <= session_distance(development_sessions, candidate_trade.exit_session, trade.signal_session)
                <= DEFAULT_SPEC.cooldown_sessions
            ):
                reasons.add("candidate_cooldown")
        if not reasons:
            reasons.add("different_signal_state_or_rule")
        item["displacement_reasons"] = sorted(reasons)
        for reason in sorted(reasons):
            displacement_reason_counts[reason] += 1
        displaced.append(item)

    added_base = sum((Decimal(str(item["base_pnl"])) for item in added), Decimal("0"))
    added_stress = sum((Decimal(str(item["stress_pnl"])) for item in added), Decimal("0"))
    return {
        "matching_key": "signal_session, entry_session, exit_session, exit_reason",
        "date_only_matching_is_not_used": True,
        "retained_count": len(retained),
        "added_count": len(added),
        "displaced_count": len(displaced),
        "retained": retained,
        "added": added,
        "displaced": displaced,
        "displaced_reason_counts": dict(sorted(displacement_reason_counts.items())),
        "added_post_cost_contribution": {
            "base_aggregate_pnl": decimal_text(added_base),
            "stress_aggregate_pnl": decimal_text(added_stress),
            "positive_in_both_cost_models": added_base > 0 and added_stress > 0,
            "definition": "所有候選相對 v009 完整生命週期 key 的新增交易，使用已扣除 base/stress 交易成本的實現 PnL；不把日期不同直接視為獨立新機會。",
        },
    }


def annual_diagnostics(
    trades: tuple[Trade, ...], *, initial_cash: float
) -> dict[str, object]:
    years: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"trades": 0, "base_pnl": 0.0}
    )
    for trade in trades:
        year = str(trade.signal_session.year)
        years[year]["trades"] = int(years[year]["trades"]) + 1
        years[year]["base_pnl"] = float(years[year]["base_pnl"]) + trade.pnl
    positive_total = sum(max(float(item["base_pnl"]), 0.0) for item in years.values())
    annual = {}
    for year, values in sorted(years.items()):
        pnl = float(values["base_pnl"])
        annual[year] = {
            "trades": values["trades"],
            "base_pnl": text(pnl),
            "positive_pnl_share": text(max(pnl, 0.0) / positive_total) if positive_total else "0.0",
        }
    pnls = sorted((trade.pnl for trade in trades), reverse=True)
    total_positive = sum(value for value in pnls if value > 0)
    return {
        "by_signal_year": annual,
        "positive_pnl_total": text(total_positive),
        "largest_positive_trade_share": text(pnls[0] / total_positive) if pnls and total_positive else "0.0",
        "top_three_positive_trade_share": text(sum(value for value in pnls[:3] if value > 0) / total_positive)
        if total_positive
        else "0.0",
        "interpretation": "逐年與逐筆集中度是品質診斷，不取代 Workflow gate；若少數年份或交易貢獻大部分正 PnL，標示為可能的品質下降。",
    }


def gate_records(
    actuals: dict[str, str | int | float], rules: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    if set(actuals) != set(rules):
        raise RuntimeError("Development actuals 與 preregistered gates 不一致")
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    for name, rule in rules.items():
        actual = actuals[name]
        if rule["operator"] == ">":
            passed = Decimal(str(actual)) > Decimal(str(rule["value"]))
        elif rule["operator"] == ">=":
            passed = Decimal(str(actual)) >= Decimal(str(rule["value"]))
        elif rule["operator"] == "<=":
            passed = Decimal(str(actual)) <= Decimal(str(rule["value"]))
        else:
            raise RuntimeError(f"不支援的 gate operator: {rule['operator']}")
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


def research_targets(
    base_metrics: dict[str, Any],
    stress_metrics: dict[str, Any],
    v009_base_metrics: dict[str, Any],
    v009_stress_metrics: dict[str, Any],
    comparison: dict[str, object],
    preregistration: dict[str, Any],
) -> dict[str, dict[str, object]]:
    targets = preregistration["eligibility_rules"]["research_targets"]
    count = len(comparison["retained"]) + len(comparison["added"])
    added = comparison["added_post_cost_contribution"]
    return {
        "minimum_completed_trades": {
            "candidate": count,
            "operator": targets["minimum_completed_trades"]["operator"],
            "required": targets["minimum_completed_trades"]["value"],
            "passed": count >= targets["minimum_completed_trades"]["value"],
        },
        "more_completed_trades_than_v009": {
            "candidate": count,
            "reference": v009_base_metrics["completed_trades"],
            "operator": targets["more_completed_trades_than_v009"]["operator"],
            "passed": count > v009_base_metrics["completed_trades"],
        },
        "base_return_not_below_v009": {
            "candidate": text(float(base_metrics["return"])),
            "reference": text(float(v009_base_metrics["return"])),
            "operator": targets["base_return_not_below_v009"]["operator"],
            "passed": Decimal(str(base_metrics["return"])) >= Decimal(str(v009_base_metrics["return"])),
        },
        "stress_return_not_below_v009": {
            "candidate": text(float(stress_metrics["return"])),
            "reference": text(float(v009_stress_metrics["return"])),
            "operator": targets["stress_return_not_below_v009"]["operator"],
            "passed": Decimal(str(stress_metrics["return"])) >= Decimal(str(v009_stress_metrics["return"])),
        },
        "base_drawdown_not_above_v009": {
            "candidate": text(float(base_metrics["maximum_drawdown"])),
            "reference": text(float(v009_base_metrics["maximum_drawdown"])),
            "operator": targets["base_drawdown_not_above_v009"]["operator"],
            "passed": Decimal(str(base_metrics["maximum_drawdown"])) <= Decimal(str(v009_base_metrics["maximum_drawdown"])),
        },
        "stress_drawdown_not_above_v009": {
            "candidate": text(float(stress_metrics["maximum_drawdown"])),
            "reference": text(float(v009_stress_metrics["maximum_drawdown"])),
            "operator": targets["stress_drawdown_not_above_v009"]["operator"],
            "passed": Decimal(str(stress_metrics["maximum_drawdown"])) <= Decimal(str(v009_stress_metrics["maximum_drawdown"])),
        },
        "added_post_cost_positive": {
            "base_aggregate_pnl": added["base_aggregate_pnl"],
            "stress_aggregate_pnl": added["stress_aggregate_pnl"],
            "passed": added["positive_in_both_cost_models"],
            "selection_use": "diagnostic-only; not a replacement for Workflow gates",
        },
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
    }
    base = backtest(bars, spec=DEFAULT_SPEC, cost=BASE_COST, **run_args)
    stress = backtest(bars, spec=DEFAULT_SPEC, cost=STRESS_COST, **run_args)
    if len(base.trades) != len(stress.trades):
        raise RuntimeError("candidate base 與 stress 交易生命週期數量不一致")
    baseline_base = backtest(bars, spec=BASELINE_SPEC, cost=BASE_COST, **run_args)
    baseline_stress = backtest(bars, spec=BASELINE_SPEC, cost=STRESS_COST, **run_args)
    v009_base = v009_backtest(bars, spec=V009_SPEC, cost=BASE_COST, **run_args)
    v009_stress = v009_backtest(bars, spec=V009_SPEC, cost=STRESS_COST, **run_args)
    bollinger_v001_base = bollinger_v001_backtest(
        bars, spec=BOLLINGER_V001_SPEC, cost=BASE_COST, **run_args
    )
    bollinger_v001_stress = bollinger_v001_backtest(
        bars, spec=BOLLINGER_V001_SPEC, cost=STRESS_COST, **run_args
    )

    initial_cash = float(preregistration["initial_cash"])
    base_metrics = qualification_metrics(base, initial_cash=initial_cash)
    stress_metrics = qualification_metrics(stress, initial_cash=initial_cash)
    baseline_base_metrics = qualification_metrics(baseline_base, initial_cash=initial_cash)
    baseline_stress_metrics = qualification_metrics(baseline_stress, initial_cash=initial_cash)
    v009_base_metrics = v009_metrics(v009_base, initial_cash=initial_cash)
    v009_stress_metrics = v009_metrics(v009_stress, initial_cash=initial_cash)
    bollinger_v001_base_metrics = bollinger_v001_metrics(
        bollinger_v001_base, initial_cash=initial_cash
    )
    bollinger_v001_stress_metrics = bollinger_v001_metrics(
        bollinger_v001_stress, initial_cash=initial_cash
    )

    development_sessions = development.index
    comparison = trade_comparison(
        base.trades,
        stress.trades,
        v009_base.trades,
        v009_stress.trades,
        development_sessions=development_sessions,
    )
    target_records = research_targets(
        base_metrics,
        stress_metrics,
        v009_base_metrics,
        v009_stress_metrics,
        comparison,
        preregistration,
    )
    target_failures = [name for name, record in target_records.items() if not record["passed"]]

    candidate_rates_base = trade_rates(base.trades, initial_cash)
    candidate_rates_stress = trade_rates(stress.trades, initial_cash)
    registered_bootstrap = preregistration["eligibility_rules"]["development_diagnostics"][
        "block_bootstrap"
    ]
    base_bootstrap = [
        bootstrap(
            candidate_rates_base,
            block_length,
            repetitions=registered_bootstrap["repetitions"],
            seed=registered_bootstrap["seed"],
            initial_cash=initial_cash,
        )
        for block_length in registered_bootstrap["block_lengths"]
    ]
    stress_bootstrap = [
        bootstrap(
            candidate_rates_stress,
            block_length,
            repetitions=registered_bootstrap["repetitions"],
            seed=registered_bootstrap["seed"],
            initial_cash=initial_cash,
        )
        for block_length in registered_bootstrap["block_lengths"]
    ]
    base_loyo = leave_one_signal_year_out(base.trades, initial_cash=initial_cash)
    stress_loyo = leave_one_signal_year_out(stress.trades, initial_cash=initial_cash)
    actuals: dict[str, str | int | float] = {
        "base_profit_factor": base_metrics["profit_factor"],
        "base_return": base_metrics["return"],
        "completed_trades": base_metrics["completed_trades"],
        "maximum_realized_trade_loss_fraction": max(
            maximum_loss_fraction(base.trades, initial_cash=initial_cash),
            maximum_loss_fraction(stress.trades, initial_cash=initial_cash),
        ),
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
    gates, failed_gates = gate_records(
        actuals, preregistration["eligibility_rules"]["development_gates"]
    )
    candidate_selection_eligible = not failed_gates and not target_failures

    years: dict[str, dict[str, object]] = defaultdict(
        lambda: {"trades": 0, "base_pnl": 0.0, "stress_pnl": 0.0}
    )
    for base_trade, stress_trade in zip(base.trades, stress.trades, strict=True):
        year = str(base_trade.signal_session.year)
        years[year]["trades"] = int(years[year]["trades"]) + 1
        years[year]["base_pnl"] = float(years[year]["base_pnl"]) + base_trade.pnl
        years[year]["stress_pnl"] = float(years[year]["stress_pnl"]) + stress_trade.pnl

    candidate_mtm = {
        "definition": "持倉 session 以當日 Low 的成本後可清算價估值；stop/target 成交前先記錄，time exit 於下一個 open 成交。",
        "base_maximum_drawdown": text(
            mark_to_market_drawdown(bars, base, cost=BASE_COST, initial_cash=initial_cash)
        ),
        "stress_maximum_drawdown": text(
            mark_to_market_drawdown(bars, stress, cost=STRESS_COST, initial_cash=initial_cash)
        ),
    }
    mechanism_ablation = {
        "remembered_event_without_quiet_hold": strategy_summary(
            bars, REMEMBERED_EVENT_NO_QUIET_SPEC, initial_cash=initial_cash
        ),
        "same_day_event_without_memory": strategy_summary(
            bars, SAME_DAY_EVENT_NO_MEMORY_SPEC, initial_cash=initial_cash
        ),
        "simple_bollinger_baseline": strategy_summary(
            bars, BASELINE_SPEC, initial_cash=initial_cash
        ),
        "interpretation": "事前固定的診斷：完整候選與 remembered_event_without_quiet_hold 的差異看縮量守低；remembered_event_without_quiet_hold 與 same_day_event_without_memory 的差異看是否記住先前事件。這些比較不參與候選選擇，也不把 RSI 加回確認條件。",
    }

    evidence = {
        "schema_version": 1,
        "stage": "development",
        "candidate_id": CANDIDATE_ID,
        "disposition": "fail" if failed_gates else "pass",
        "failed_gates": failed_gates,
        "network_access_during_run": False,
        "accepted_signal_count": len(base.trades),
        "bindings": bindings,
        "gates": gates,
        "metrics": {
            "base": {
                **metric_texts(base_metrics),
                "maximum_realized_trade_loss_fraction": text(
                    maximum_loss_fraction(base.trades, initial_cash=initial_cash)
                ),
            },
            "stress": {
                **metric_texts(stress_metrics),
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
        "event_audit": event_audit_summary(base.event_audit),
        "baseline_comparison": {
            "baseline_id": BASELINE_ID,
            "candidate_id": CANDIDATE_ID,
            "execution_is_identical": True,
            "baseline_is_excluded_from_candidate_family": True,
            "candidate": {"base": metric_texts(base_metrics), "stress": metric_texts(stress_metrics)},
            "baseline": {
                "base": metric_texts(baseline_base_metrics),
                "stress": metric_texts(baseline_stress_metrics),
            },
        },
        "mechanism_ablation": mechanism_ablation,
        "risk_diagnostics": {
            "candidate_mark_to_market": candidate_mtm,
            "annual_concentration": annual_diagnostics(base.trades, initial_cash=initial_cash),
            "quality_decline_checks": {
                "profit_factor_reported_for_base_and_stress": True,
                "holding_period_drawdown_reported": True,
                "concentration_is_diagnostic_only": True,
            },
        },
        "reference_controls": {
            "v009": {
                "study_id": "tsm-mean-reversion-two-stage-volume-reversal--v009",
                "development_evidence_digest": "d8f51a7a1f2f5024d1a778fd5c0d42a70b549aa258723869b2a4567cfee4a618",
                "execution_is_identical": True,
                "base": metric_texts(v009_base_metrics),
                "stress": metric_texts(v009_stress_metrics),
            },
            "bollinger_rebound_v001": {
                "study_id": "tsm-mean-reversion-bollinger-rebound--v001",
                "development_evidence_digest": "79d40459e7376dbcf29b97cde9a4beb62c8585166187f2ed532312d2e74a30d4",
                "execution_is_identical": True,
                "base": metric_texts(bollinger_v001_base_metrics),
                "stress": metric_texts(bollinger_v001_stress_metrics),
            },
        },
        "research_targets": target_records,
        "candidate_selection_eligible": candidate_selection_eligible,
        "candidate_selection_ineligibility_reasons": [*failed_gates, *target_failures],
        "trade_comparison": comparison,
        "trades": [
            trade_record(index, base_trade, stress_trade, base_rate, stress_rate)
            for index, (base_trade, stress_trade, base_rate, stress_rate) in enumerate(
                zip(base.trades, stress.trades, candidate_rates_base, candidate_rates_stress, strict=True),
                start=1,
            )
        ],
    }
    atomic_create(args.output, canonical_bytes(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
