"""Workflow Floors 與 Study Gates 的十進位比較。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from .errors import EvidenceUnavailable, ValidationError


@dataclass(frozen=True)
class GateFailure:
    metric: str
    actual: Any
    operator: str
    expected: Any


def decimal_value(value: Any, *, allow_positive_infinity: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValidationError(f"數值必須是 integer 或十進位字串: {value!r}")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValidationError(f"無效十進位數值: {value!r}") from exc
    if result.is_nan():
        raise ValidationError("禁止 NaN")
    if result.is_infinite() and not (allow_positive_infinity and result > 0):
        raise ValidationError("此欄位禁止 infinity")
    return result


def compare(actual: Any, operator: str, expected: Any, *, metric: str) -> bool:
    if operator == "equals":
        return actual == expected
    allow_infinity = "profit_factor" in metric
    left = decimal_value(actual, allow_positive_infinity=allow_infinity)
    right = decimal_value(expected)
    operations = {
        ">": left > right,
        ">=": left >= right,
        "<": left < right,
        "<=": left <= right,
    }
    if operator not in operations:
        raise ValidationError(f"未知 gate operator: {operator}")
    return operations[operator]


def evaluate_rules(metrics: dict[str, Any], rules: dict[str, dict[str, Any]]) -> list[GateFailure]:
    failures: list[GateFailure] = []
    for metric, rule in rules.items():
        if metric not in metrics:
            raise EvidenceUnavailable(f"缺少必要 metric: {metric}")
        if not compare(metrics[metric], rule["operator"], rule["value"], metric=metric):
            failures.append(GateFailure(metric, metrics[metric], rule["operator"], rule["value"]))
    return failures


def validate_study_gates(
    study_gates: dict[str, dict[str, Any]],
    floors: dict[str, dict[str, Any]],
) -> None:
    for metric, floor in floors.items():
        gate = study_gates.get(metric, floor)
        if gate["operator"] != floor["operator"]:
            raise ValidationError(f"{metric}: Study Gate operator 不得改變 Workflow Floor")
        operator = floor["operator"]
        if operator in {">", ">="} and decimal_value(gate["value"]) < decimal_value(floor["value"]):
            raise ValidationError(f"{metric}: Study Gate 比 Workflow Floor 寬鬆")
        if operator in {"<", "<="} and decimal_value(gate["value"]) > decimal_value(floor["value"]):
            raise ValidationError(f"{metric}: Study Gate 比 Workflow Floor 寬鬆")
        if operator == "equals" and gate["value"] != floor["value"]:
            raise ValidationError(f"{metric}: equals gate 必須等於 Workflow Floor")
