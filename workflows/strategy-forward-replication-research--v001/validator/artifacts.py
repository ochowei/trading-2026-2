"""Raw evidence 與 Data Snapshot 的重算和驗證。"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import exchange_calendars as xcals

from .canonical_yaml import canonical_digest, load_canonical
from .errors import EvidenceUnavailable, IntegrityError, ValidationError
from .metrics import compare, decimal_value, evaluate_rules
from .paths import resolve_inside
from .schema_validation import SchemaStore

ALLOWED_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def verified_artifact(
    study_root: Path, relative_path: str, expected_digest: str
) -> tuple[Path, Any]:
    try:
        path = resolve_inside(study_root, relative_path)
    except (FileNotFoundError, ValidationError) as exc:
        raise EvidenceUnavailable(f"無法取得 artifact: {relative_path}") from exc
    data = path.read_bytes()
    actual_digest = canonical_digest(data)
    if actual_digest != expected_digest:
        raise IntegrityError(f"artifact digest mismatch: {relative_path}")
    return path, load_canonical(path)


def _profit_factor(values: Iterable[Decimal]) -> str:
    values = list(values)
    gross_profit = sum((value for value in values if value > 0), Decimal("0"))
    gross_loss = -sum((value for value in values if value < 0), Decimal("0"))
    if gross_loss == 0:
        return "Infinity" if gross_profit > 0 else "0"
    return str(gross_profit / gross_loss)


def _maximum_drawdown(initial_cash: Decimal, pnls: Iterable[Decimal]) -> str:
    equity = initial_cash
    peak = initial_cash
    maximum = Decimal("0")
    for pnl in pnls:
        equity += pnl
        if equity > peak:
            peak = equity
        if peak > 0:
            maximum = max(maximum, (peak - equity) / peak)
    return str(maximum)


def _return(initial_cash: Decimal, pnls: Iterable[Decimal]) -> str:
    return str(sum(pnls, initial_cash) / initial_cash - Decimal("1"))


def _validate_unique(items: list[dict[str, Any]], key: str) -> None:
    values = [item[key] for item in items]
    if len(values) != len(set(values)):
        raise ValidationError(f"{key} 不得重複")


def historical_metrics(value: dict[str, Any]) -> dict[str, Any]:
    trades = value["trades"]
    _validate_unique(trades, "trade_id")
    initial_cash = decimal_value(value["initial_cash"])
    if initial_cash <= 0:
        raise ValidationError("initial_cash 必須大於 0")
    fold_pnls: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    fold_counts: dict[int, int] = defaultdict(int)
    base_pnls: list[Decimal] = []
    stress_pnls: list[Decimal] = []
    for trade in trades:
        signal_year = date.fromisoformat(trade["signal_date"]).year
        exit_year = date.fromisoformat(trade["exit_date"]).year
        if signal_year != trade["fold"] or exit_year != trade["fold"]:
            raise ValidationError(f"trade {trade['trade_id']} 跨越或錯置 Evaluation Fold")
        if trade["order_type"] not in ALLOWED_ORDER_TYPES:
            raise ValidationError(f"不允許的 Proposal Order Type: {trade['order_type']}")
        base_pnl = decimal_value(trade["base_pnl"])
        stress_pnl = decimal_value(trade["stress_pnl"])
        base_pnls.append(base_pnl)
        stress_pnls.append(stress_pnl)
        fold_pnls[trade["fold"]] += base_pnl
        fold_counts[trade["fold"]] += 1
    completed = len(trades)
    traded_folds = len(fold_counts)
    positive_folds = sum(1 for pnl in fold_pnls.values() if pnl > 0)
    positive_ratio = (
        Decimal(positive_folds) / Decimal(traded_folds) if traded_folds else Decimal("0")
    )
    max_trade_concentration = (
        Decimal(max(fold_counts.values())) / Decimal(completed) if completed else Decimal("0")
    )
    total_positive = sum((max(pnl, Decimal("0")) for pnl in fold_pnls.values()), Decimal("0"))
    max_profit_concentration = (
        max((max(pnl, Decimal("0")) for pnl in fold_pnls.values()), default=Decimal("0"))
        / total_positive
        if total_positive
        else Decimal("0")
    )
    stress_drawdown = _maximum_drawdown(initial_cash, stress_pnls)
    return {
        "base_compounded_return": _return(initial_cash, base_pnls),
        "base_profit_factor": _profit_factor(base_pnls),
        "completed_trades": completed,
        "family_wise_confidence": value["family_wise_confidence"],
        "maximum_fold_positive_profit_concentration": str(max_profit_concentration),
        "maximum_fold_trade_concentration": str(max_trade_concentration),
        "positive_traded_fold_ratio": str(positive_ratio),
        "stress_max_drawdown": stress_drawdown,
        "stress_profit_factor": _profit_factor(stress_pnls),
        "stress_return": _return(initial_cash, stress_pnls),
        "traded_folds": traded_folds,
    }


def _validate_historical_trade_boundaries(
    value: dict[str, Any],
    *,
    fold_warmup_sessions: int,
    maximum_holding_sessions: int,
) -> None:
    calendar = xcals.get_calendar("XNYS")
    sessions_by_year = {
        year: [
            timestamp.strftime("%Y-%m-%d")
            for timestamp in calendar.sessions_in_range(f"{year}-01-01", f"{year}-12-31")
        ]
        for year in range(2020, 2025)
    }
    for trade in value["trades"]:
        sessions = sessions_by_year[trade["fold"]]
        try:
            signal_index = sessions.index(trade["signal_date"])
            exit_index = sessions.index(trade["exit_date"])
        except ValueError as exc:
            raise ValidationError(f"trade {trade['trade_id']} 使用非 XNYS session") from exc
        if signal_index < fold_warmup_sessions:
            raise ValidationError(f"trade {trade['trade_id']} 在 Fold Warmup 期間產生 signal")
        if exit_index < signal_index or exit_index - signal_index > maximum_holding_sessions:
            raise ValidationError(f"trade {trade['trade_id']} 違反最大持有期")
        if signal_index + maximum_holding_sessions >= len(sessions):
            raise ValidationError(f"trade {trade['trade_id']} 違反年末 entry cutoff")


def evaluate_historical(
    value: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    *,
    fold_warmup_sessions: int = 1,
    maximum_holding_sessions: int = 1,
) -> tuple[dict[str, Any], list[str]]:
    _validate_historical_trade_boundaries(
        value,
        fold_warmup_sessions=fold_warmup_sessions,
        maximum_holding_sessions=maximum_holding_sessions,
    )
    metrics = historical_metrics(value)
    failures = [failure.metric for failure in evaluate_rules(metrics, rules)]
    if decimal_value(metrics["stress_max_drawdown"]) > decimal_value(
        value["stress_drawdown_limit"]
    ):
        failures.append("stress_max_drawdown")
    return metrics, failures


def replay_metrics(
    value: dict[str, Any],
    *,
    fold_warmup_sessions: int,
    maximum_holding_sessions: int,
) -> dict[str, Any]:
    fills = value["fills"]
    _validate_unique(fills, "fill_id")
    initial_cash = decimal_value(value["initial_cash"])
    base_pnls: list[Decimal] = []
    stress_pnls: list[Decimal] = []
    calendar = xcals.get_calendar("XNYS")
    expected_sessions = [
        timestamp.strftime("%Y-%m-%d")
        for timestamp in calendar.sessions_in_range("2025-01-01", "2025-12-31")
    ]
    if value["expected_sessions"] != expected_sessions:
        raise ValidationError("Replay expected_sessions 必須是完整固定 2025 XNYS inventory")
    for fill in fills:
        if fill["proposal_actionable"] is not False:
            raise ValidationError("Replay proposal 必須是 non-actionable")
        if fill["order_type"] not in ALLOWED_ORDER_TYPES:
            raise ValidationError(f"不允許的 Proposal Order Type: {fill['order_type']}")
        try:
            entry_index = expected_sessions.index(fill["session"])
            exit_index = expected_sessions.index(fill["exit_session"])
        except ValueError as exc:
            raise ValidationError(f"fill {fill['fill_id']} 使用非 XNYS session") from exc
        if entry_index < fold_warmup_sessions:
            raise ValidationError(f"fill {fill['fill_id']} 在 Replay Warmup 期間產生")
        if exit_index < entry_index or exit_index - entry_index > maximum_holding_sessions:
            raise ValidationError(f"fill {fill['fill_id']} 違反最大持有期")
        if entry_index + maximum_holding_sessions >= len(expected_sessions):
            raise ValidationError(f"fill {fill['fill_id']} 違反 2025 entry cutoff")
        base_pnls.append(decimal_value(fill["base_pnl"]))
        stress_pnls.append(decimal_value(fill["stress_pnl"]))
    return {
        "base_profit_factor": _profit_factor(base_pnls),
        "base_return": _return(initial_cash, base_pnls),
        "completed_simulated_fills": len(fills),
        "critical_drift_passed": value["critical_drift_passed"],
        "expected_sessions_covered": value["expected_sessions"] == value["observed_sessions"],
        "stress_max_drawdown": _maximum_drawdown(initial_cash, stress_pnls),
        "stress_profit_factor": _profit_factor(stress_pnls),
        "stress_return": _return(initial_cash, stress_pnls),
    }


def evaluate_replay(
    value: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    *,
    fold_warmup_sessions: int = 1,
    maximum_holding_sessions: int = 1,
) -> tuple[dict[str, Any], list[str]]:
    metrics = replay_metrics(
        value,
        fold_warmup_sessions=fold_warmup_sessions,
        maximum_holding_sessions=maximum_holding_sessions,
    )
    failures = [failure.metric for failure in evaluate_rules(metrics, rules)]
    if decimal_value(metrics["stress_max_drawdown"]) > decimal_value(
        value["stress_drawdown_limit"]
    ):
        failures.append("stress_max_drawdown")
    return metrics, failures


def evaluate_challenges(
    value: dict[str, Any],
    required_ids: list[str],
    seed_required: list[str],
) -> list[str]:
    challenges = value["challenges"]
    ids = [item["challenge_id"] for item in challenges]
    if len(ids) != len(set(ids)) or set(ids) != set(required_ids):
        raise ValidationError("Challenge IDs 必須完整、唯一且剛好等於正式九項")
    binding_sets = {tuple(sorted(item["bindings"].items())) for item in challenges}
    if len(binding_sets) != 1:
        raise IntegrityError("九項 challenges 的 frozen bindings 不一致")
    failures: list[str] = []
    for item in challenges:
        if item["challenge_id"] in seed_required and "seed" not in item:
            raise ValidationError(f"{item['challenge_id']} 缺少 preregistered seed")
        if not compare(
            item["actual"], item["operator"], item["expected"], metric=item["challenge_id"]
        ):
            failures.append(item["challenge_id"])
    return failures


def validate_snapshot(
    value: dict[str, Any],
    schema_store: SchemaStore,
    start_date: str,
    end_date: str,
) -> None:
    schema_store.validate("data-snapshot.schema.yml", value)
    sessions = value["sessions"]
    if sessions != sorted(sessions):
        raise ValidationError("Session Inventory 必須嚴格依日期排序")
    calendar = xcals.get_calendar(value["calendar"])
    expected = [
        timestamp.strftime("%Y-%m-%d")
        for timestamp in calendar.sessions_in_range(start_date, end_date)
    ]
    if sessions != expected:
        raise ValidationError("Session Inventory 有缺漏、額外或順序錯誤")


def validate_snapshot_set(
    value: dict[str, Any],
    workflow: dict[str, Any],
    schema_store: SchemaStore,
) -> dict[str, dict[str, Any]]:
    schema_store.validate("data-snapshot-set.schema.yml", value)
    snapshots = value["snapshots"]
    roles = [snapshot.get("role") for snapshot in snapshots]
    expected_intervals = {
        interval["role"]: interval for interval in workflow["data_intervals"]["intervals"]
    }
    if len(roles) != len(set(roles)) or set(roles) != set(expected_intervals):
        raise ValidationError("Data Snapshot roles 必須完整、唯一且等於固定資料角色")
    occupied_sessions: set[str] = set()
    result: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        interval = expected_intervals[snapshot["role"]]
        validate_snapshot(
            snapshot,
            schema_store,
            interval["start_date"],
            interval["end_date"],
        )
        if occupied_sessions.intersection(snapshot["sessions"]):
            raise ValidationError("Data Snapshot roles 的 sessions 不得重疊")
        occupied_sessions.update(snapshot["sessions"])
        result[snapshot["role"]] = snapshot
    return result
