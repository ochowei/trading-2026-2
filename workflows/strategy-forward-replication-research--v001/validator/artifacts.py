"""Raw evidence 與 Data Snapshot 的重算和驗證。"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from math import inf, isclose, isfinite
from pathlib import Path
from typing import Any

import exchange_calendars as xcals
import numpy as np

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
    fold_equity: dict[tuple[int, str], Decimal] = defaultdict(lambda: initial_cash)
    maximum_realized_loss_fraction = Decimal("0")
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
        for model, pnl in (("base", base_pnl), ("stress", stress_pnl)):
            key = (trade["fold"], model)
            equity = fold_equity[key]
            if pnl < 0 and equity > 0:
                maximum_realized_loss_fraction = max(
                    maximum_realized_loss_fraction, -pnl / equity
                )
            fold_equity[key] = equity + pnl
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
        "maximum_realized_trade_loss_fraction": str(maximum_realized_loss_fraction),
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
    base_equity = initial_cash
    stress_equity = initial_cash
    maximum_realized_loss_fraction = Decimal("0")
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
        base_pnl = decimal_value(fill["base_pnl"])
        stress_pnl = decimal_value(fill["stress_pnl"])
        base_pnls.append(base_pnl)
        stress_pnls.append(stress_pnl)
        if base_pnl < 0 and base_equity > 0:
            maximum_realized_loss_fraction = max(
                maximum_realized_loss_fraction, -base_pnl / base_equity
            )
        if stress_pnl < 0 and stress_equity > 0:
            maximum_realized_loss_fraction = max(
                maximum_realized_loss_fraction, -stress_pnl / stress_equity
            )
        base_equity += base_pnl
        stress_equity += stress_pnl
    return {
        "base_max_drawdown": _maximum_drawdown(initial_cash, base_pnls),
        "base_profit_factor": _profit_factor(base_pnls),
        "base_return": _return(initial_cash, base_pnls),
        "completed_simulated_fills": len(fills),
        "critical_drift_passed": value["critical_drift_passed"],
        "expected_sessions_covered": value["expected_sessions"] == value["observed_sessions"],
        "maximum_realized_trade_loss_fraction": str(maximum_realized_loss_fraction),
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


def _development_text(value: float) -> str:
    return str(float(value))


def _development_path_metrics(rates: np.ndarray) -> dict[str, float]:
    equity = 100_000.0
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
        "return": equity / 100_000.0 - 1.0,
        "profit_factor": gross_profit / gross_loss if gross_loss else inf,
        "maximum_drawdown": maximum_drawdown,
    }


def _development_bootstrap(
    rates: np.ndarray,
    block_length: int,
    *,
    repetitions: int,
    seed: int,
) -> dict[str, object]:
    if len(rates) == 0:
        raise ValidationError("Development bootstrap 至少需要一筆交易")
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
        "return_q05_q50_q95": [
            _development_text(value)
            for value in np.quantile(returns, [0.05, 0.5, 0.95])
        ],
        "profit_factor_q05_q50_q95": [
            _development_text(value)
            for value in np.quantile(profit_factors, [0.05, 0.5, 0.95])
        ],
        "maximum_drawdown_q05_q50_q95": [
            _development_text(value)
            for value in np.quantile(maximum_drawdown, [0.05, 0.5, 0.95])
        ],
        "positive_return_ratio": _development_text(np.mean(returns > 0)),
        "profit_factor_above_one_ratio": _development_text(
            np.mean(profit_factors > 1)
        ),
        "drawdown_above_10pct_ratio": _development_text(
            np.mean(maximum_drawdown > 0.10)
        ),
    }


def _development_numeric_equal(actual: Any, expected: Any) -> bool:
    try:
        left = float(actual)
        right = float(expected)
    except (TypeError, ValueError):
        return False
    if not isfinite(left) or not isfinite(right):
        return left == right
    return isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def _assert_development_equal(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise IntegrityError(f"Development {label} 欄位與 raw trades 重算結果不一致")
        for key, value in expected.items():
            _assert_development_equal(actual[key], value, f"{label}.{key}")
        return
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise IntegrityError(f"Development {label} 與 raw trades 重算結果不一致")
        for index, value in enumerate(expected):
            _assert_development_equal(actual[index], value, f"{label}[{index}]")
        return
    if isinstance(expected, bool):
        if actual is not expected:
            raise IntegrityError(f"Development {label} 與 raw trades 重算結果不一致")
        return
    if isinstance(expected, int):
        if isinstance(actual, bool) or actual != expected:
            raise IntegrityError(f"Development {label} 與 raw trades 重算結果不一致")
        return
    if isinstance(expected, float) or (
        isinstance(expected, str) and _development_numeric_equal(expected, expected)
    ):
        if not _development_numeric_equal(actual, expected):
            raise IntegrityError(f"Development {label} 與 raw trades 重算結果不一致")
        return
    if actual != expected:
        raise IntegrityError(f"Development {label} 與 raw trades 重算結果不一致")


def _development_model_metrics(
    trades: list[dict[str, Any]], model: str, initial_cash: float
) -> tuple[dict[str, Any], np.ndarray, list[float]]:
    equity = initial_cash
    peak = equity
    pnls: list[float] = []
    rates: list[float] = []
    gross_profit = 0.0
    gross_loss = 0.0
    maximum_drawdown = 0.0
    for trade in trades:
        detail = trade[model]
        required = {
            "executed_entry_price",
            "executed_exit_price",
            "fees",
            "pnl",
            "pnl_fraction_of_pre_entry_equity",
            "shares",
        }
        if not isinstance(detail, dict) or not required.issubset(detail):
            raise ValidationError(f"Development trade {trade['trade_id']} 缺少 {model} 原始欄位")
        shares = detail["shares"]
        if isinstance(shares, bool) or not isinstance(shares, int) or shares <= 0:
            raise ValidationError(f"Development trade {trade['trade_id']} shares 不合法")
        executed_entry = float(decimal_value(detail["executed_entry_price"]))
        executed_exit = float(decimal_value(detail["executed_exit_price"]))
        fees = float(decimal_value(detail["fees"]))
        pnl = float(decimal_value(detail["pnl"]))
        expected_pnl = shares * (executed_exit - executed_entry) - fees
        if not _development_numeric_equal(pnl, expected_pnl):
            raise IntegrityError(
                f"Development trade {trade['trade_id']} {model} PnL 無法由成交與費用重算"
            )
        if equity <= 0:
            raise ValidationError("Development equity 不得小於或等於 0")
        rate = pnl / equity
        if not _development_numeric_equal(
            detail["pnl_fraction_of_pre_entry_equity"], rate
        ):
            raise IntegrityError(
                f"Development trade {trade['trade_id']} {model} 進場前資金損益比例不正確"
            )
        pnls.append(pnl)
        rates.append(rate)
        if pnl > 0:
            gross_profit += pnl
        elif pnl < 0:
            gross_loss -= pnl
        equity += pnl
        peak = max(peak, equity)
        maximum_drawdown = max(maximum_drawdown, (peak - equity) / peak)
    traded_years = len({date.fromisoformat(trade["signal_session"]).year for trade in trades})
    metrics = {
        "completed_trades": len(trades),
        "maximum_drawdown": _development_text(maximum_drawdown),
        "maximum_realized_trade_loss_fraction": _development_text(
            max((-rate for rate in rates if rate < 0), default=0.0)
        ),
        "profit_factor": _development_text(
            gross_profit / gross_loss if gross_loss else inf
        ),
        "return": _development_text(sum(pnls) / initial_cash),
        "traded_years": traded_years,
    }
    return metrics, np.asarray(rates), pnls


def _recompute_development(
    value: dict[str, Any], preregistration: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    trades = value["trades"]
    if not isinstance(trades, list) or not trades:
        raise ValidationError("Development trades 必須是非空 list")
    _validate_unique(trades, "trade_id")
    required_trade_fields = {
        "base",
        "entry_session",
        "exit_reason",
        "exit_session",
        "held_sessions",
        "signal_session",
        "stress",
        "trade_id",
    }
    signal_years: list[int] = []
    for trade in trades:
        if not isinstance(trade, dict) or not required_trade_fields.issubset(trade):
            raise ValidationError("Development trade 缺少生命週期或 base/stress 欄位")
        signal = date.fromisoformat(trade["signal_session"])
        entry = date.fromisoformat(trade["entry_session"])
        exit_session = date.fromisoformat(trade["exit_session"])
        if not date(2014, 1, 1) <= signal <= date(2018, 12, 31):
            raise ValidationError(f"Development trade {trade['trade_id']} signal 超出期間")
        if not signal < entry <= exit_session <= date(2018, 12, 31):
            raise ValidationError(f"Development trade {trade['trade_id']} 生命週期日期不合法")
        if (
            isinstance(trade["held_sessions"], bool)
            or not isinstance(trade["held_sessions"], int)
            or trade["held_sessions"] <= 0
        ):
            raise ValidationError(f"Development trade {trade['trade_id']} held_sessions 不合法")
        signal_years.append(signal.year)

    initial_cash = float(decimal_value(preregistration["initial_cash"]))
    if initial_cash <= 0:
        raise ValidationError("Development initial_cash 必須大於 0")
    base_metrics, base_rates, base_pnls = _development_model_metrics(
        trades, "base", initial_cash
    )
    stress_metrics, stress_rates, stress_pnls = _development_model_metrics(
        trades, "stress", initial_cash
    )

    year_values: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"trades": 0, "base_pnl": 0.0, "stress_pnl": 0.0}
    )
    for year, base_pnl, stress_pnl in zip(
        signal_years, base_pnls, stress_pnls, strict=True
    ):
        values = year_values[str(year)]
        values["trades"] += 1
        values["base_pnl"] += base_pnl
        values["stress_pnl"] += stress_pnl

    def leave_one_year_out(rates: np.ndarray) -> dict[str, dict[str, Any]]:
        years = np.asarray(signal_years)
        result: dict[str, dict[str, Any]] = {}
        for year in sorted(set(signal_years)):
            kept = rates[years != year]
            metrics = _development_path_metrics(kept)
            result[str(year)] = {
                "omitted_trades": int(np.sum(years == year)),
                "remaining_trades": int(np.sum(years != year)),
                "return": _development_text(metrics["return"]),
                "profit_factor": _development_text(metrics["profit_factor"]),
                "maximum_drawdown": _development_text(metrics["maximum_drawdown"]),
            }
        return result

    registration = preregistration["eligibility_rules"]["development_diagnostics"][
        "block_bootstrap"
    ]
    base_bootstrap = [
        _development_bootstrap(
            base_rates,
            length,
            repetitions=registration["repetitions"],
            seed=registration["seed"],
        )
        for length in registration["block_lengths"]
    ]
    stress_bootstrap = [
        _development_bootstrap(
            stress_rates,
            length,
            repetitions=registration["repetitions"],
            seed=registration["seed"],
        )
        for length in registration["block_lengths"]
    ]
    base_loyo = leave_one_year_out(base_rates)
    stress_loyo = leave_one_year_out(stress_rates)
    metrics = {
        "base": base_metrics,
        "stress": stress_metrics,
        "trade_count_by_signal_year": {
            year: values["trades"] for year, values in sorted(year_values.items())
        },
    }
    diagnostics = {
        "by_signal_year": {
            year: {
                "trades": values["trades"],
                "base_pnl": _development_text(values["base_pnl"]),
                "stress_pnl": _development_text(values["stress_pnl"]),
            }
            for year, values in sorted(year_values.items())
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
    }
    actuals = {
        "completed_trades": base_metrics["completed_trades"],
        "traded_years": base_metrics["traded_years"],
        "base_return": base_metrics["return"],
        "stress_return": stress_metrics["return"],
        "base_profit_factor": base_metrics["profit_factor"],
        "stress_profit_factor": stress_metrics["profit_factor"],
        "stress_maximum_drawdown": stress_metrics["maximum_drawdown"],
        "maximum_realized_trade_loss_fraction": _development_text(
            max(
                float(base_metrics["maximum_realized_trade_loss_fraction"]),
                float(stress_metrics["maximum_realized_trade_loss_fraction"]),
            )
        ),
        "minimum_stress_block_bootstrap_positive_return_ratio": _development_text(
            min(float(item["positive_return_ratio"]) for item in stress_bootstrap)
        ),
        "maximum_stress_block_bootstrap_drawdown_above_10pct_ratio": _development_text(
            max(float(item["drawdown_above_10pct_ratio"]) for item in stress_bootstrap)
        ),
        "minimum_stress_leave_one_year_out_return": _development_text(
            min(float(item["return"]) for item in stress_loyo.values())
        ),
        "minimum_stress_leave_one_year_out_profit_factor": _development_text(
            min(float(item["profit_factor"]) for item in stress_loyo.values())
        ),
        "maximum_stress_leave_one_year_out_drawdown": _development_text(
            max(float(item["maximum_drawdown"]) for item in stress_loyo.values())
        ),
    }
    return metrics, diagnostics, actuals


def validate_development_trial(
    value: dict[str, Any],
    inputs: dict[str, Any],
    preregistration: dict[str, Any],
    *,
    trial_id: str,
    trial_inputs_digest: str,
    preregistration_digest: str,
    source_bundle_digest: str,
) -> list[str]:
    """從 raw trades 重算 Development evidence，再核對 frozen inputs 與 gates。"""

    required = {
        "bindings",
        "candidate_id",
        "diagnostics",
        "disposition",
        "failed_gates",
        "gates",
        "metrics",
        "network_access_during_run",
        "schema_version",
        "stage",
        "trades",
    }
    missing = sorted(required.difference(value))
    if missing:
        raise ValidationError(f"Development evidence 缺少欄位: {', '.join(missing)}")
    if value["schema_version"] != 1 or value["stage"] != "development":
        raise ValidationError("Development evidence identity 不正確")
    if value["network_access_during_run"] is not False:
        raise ValidationError("Development formal run 不得使用網路")
    if inputs.get("candidate_id") != trial_id or value["candidate_id"] != trial_id:
        raise IntegrityError("Trial、inputs 與 Development evidence candidate_id 不一致")

    expected_bindings = {
        "preregistration_digest": preregistration_digest,
        "source_bundle_digest": source_bundle_digest,
        "trial_inputs_digest": trial_inputs_digest,
    }
    for name, expected in expected_bindings.items():
        if value["bindings"].get(name) != expected:
            raise IntegrityError(f"Development evidence {name} binding 不一致")

    registered = preregistration["eligibility_rules"]["development_diagnostics"][
        "block_bootstrap"
    ]
    input_diagnostics = inputs.get("development_diagnostics", {})
    registered_seed = registered["seed"]
    registered_lengths = registered["block_lengths"]
    if input_diagnostics.get("bootstrap_seed") != registered_seed:
        raise IntegrityError("Development inputs bootstrap seed 與 preregistration 不一致")
    if input_diagnostics.get("block_lengths") != registered_lengths:
        raise IntegrityError("Development inputs block lengths 與 preregistration 不一致")
    if input_diagnostics.get("repetitions") != registered["repetitions"]:
        raise IntegrityError("Development inputs bootstrap repetitions 與 preregistration 不一致")
    if input_diagnostics.get("seed_application") != "exact-same-seed-for-each-block-length":
        raise ValidationError("Development inputs 必須明示每個 block length 使用同一登記 seed")

    metrics, diagnostics, recomputed_actuals = _recompute_development(
        value, preregistration
    )
    _assert_development_equal(value["metrics"], metrics, "metrics")
    if value.get("accepted_signal_count") != len(value["trades"]):
        raise IntegrityError("Development accepted_signal_count 與 raw trades 不一致")

    bootstrap = value["diagnostics"].get("block_bootstrap", {})
    for cost_model in ("base", "stress"):
        records = bootstrap.get(cost_model)
        if not isinstance(records, list):
            raise ValidationError(f"Development evidence 缺少 {cost_model} bootstrap")
        lengths = [item.get("block_length") for item in records]
        if lengths != registered_lengths:
            raise IntegrityError(f"{cost_model} bootstrap block lengths 與登記不一致")
        for item in records:
            if item.get("seed") != registered_seed:
                raise IntegrityError(
                    f"{cost_model} block length {item.get('block_length')} 未使用登記 seed"
                )
            if item.get("repetitions") != registered["repetitions"]:
                raise IntegrityError(f"{cost_model} bootstrap repetitions 與登記不一致")
    _assert_development_equal(value["diagnostics"], diagnostics, "diagnostics")

    gate_rules = preregistration["eligibility_rules"]["development_gates"]
    gate_records = value["gates"]
    if not isinstance(gate_records, list):
        raise ValidationError("Development gates 必須是 list")
    names = [item.get("gate") for item in gate_records]
    if len(names) != len(set(names)) or set(names) != set(gate_rules):
        raise IntegrityError("Development evidence gates 與 preregistration 不完整一致")
    failures: list[str] = []
    for item in gate_records:
        name = item["gate"]
        rule = gate_rules[name]
        if item.get("operator") != rule["operator"] or item.get("required") != rule["value"]:
            raise IntegrityError(f"Development gate {name} 的 operator 或門檻不一致")
        if name not in recomputed_actuals:
            raise ValidationError(f"Development validator 無法重算 gate: {name}")
        _assert_development_equal(
            item.get("actual"), recomputed_actuals[name], f"gate.{name}.actual"
        )
        passed = compare(
            recomputed_actuals[name], rule["operator"], rule["value"], metric=name
        )
        if item.get("passed") is not passed:
            raise IntegrityError(f"Development gate {name} 的 passed 與重算結果不一致")
        if not passed:
            failures.append(name)
    if value["failed_gates"] != failures:
        raise IntegrityError("Development failed_gates 與重算結果不一致")
    expected_disposition = "fail" if failures else "pass"
    if value["disposition"] != expected_disposition:
        raise IntegrityError("Development disposition 與重算 gates 不一致")
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
