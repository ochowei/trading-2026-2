"""v003 從 raw Development evidence 重算候選資格與排序。"""

from .artifacts import _recompute_development
from .errors import ValidationError
from .metrics import compare, decimal_value

METRICS = {
    "completed_trades",
    "traded_years",
    "base_return",
    "stress_return",
    "base_profit_factor",
    "stress_profit_factor",
    "stress_maximum_drawdown",
    "maximum_realized_trade_loss_fraction",
    "minimum_stress_block_bootstrap_positive_return_ratio",
    "maximum_stress_block_bootstrap_drawdown_above_10pct_ratio",
    "minimum_stress_leave_one_year_out_return",
    "minimum_stress_leave_one_year_out_profit_factor",
    "maximum_stress_leave_one_year_out_drawdown",
}


def validate_supported(prereg):
    for section in ("development_gates", "research_targets"):
        for metric, rule in prereg["eligibility_rules"].get(section, {}).items():
            if metric not in METRICS:
                raise ValidationError(f"不支援 {section} metric: {metric}")
            if rule.get("operator") not in {">", ">=", "<", "<=", "equals"}:
                raise ValidationError(f"不支援 operator: {rule}")
            decimal_value(rule["value"])
    rule, tie = prereg["selection_rule"], prereg["tie_handling"]
    if rule.get("method") == "fixed-single-candidate-no-outcome-ranking":
        if (
            prereg["complete_candidate_family"] != [rule.get("selected_candidate_id")]
            or tie.get("method") != "not-applicable-single-candidate"
        ):
            raise ValidationError("固定候選規則必須對應唯一預先登記候選")
    elif (
        rule.get("metric") not in METRICS
        or rule.get("order") not in {"ascending", "descending"}
        or tie.get("method") != "stable-trial-id"
    ):
        raise ValidationError("不支援的候選排序／同分規則")


def assess(evidence, prereg):
    validate_supported(prereg)
    actuals = (
        _recompute_development(evidence, prereg)[2]
        if evidence["trades"]
        else {"completed_trades": 0, "traded_years": 0}
    )

    def failures(section):
        return [
            name
            for name, rule in prereg["eligibility_rules"].get(section, {}).items()
            if name not in actuals
            or not compare(actuals[name], rule["operator"], rule["value"], metric=name)
        ]

    formal, targets = failures("development_gates"), failures("research_targets")
    reasons = formal + targets + ([] if evidence["trades"] else ["no-trades"])
    registered = bool(prereg["eligibility_rules"].get("research_targets"))
    return {
        "formal_development_gates": {"status": "failed" if formal else "passed", "failed": formal},
        "research_targets": {
            "status": ("failed" if targets else "passed") if registered else "not_registered",
            "failed": targets,
        },
        "development_evidence_validity": {"status": "valid", "validated": True},
        "candidate_freeze_eligibility": {"eligible": not reasons, "reasons": reasons},
        "actuals": actuals,
    }


def ordered_eligible(projection):
    rule = projection.preregistration["selection_rule"]
    ids = sorted(
        key
        for key, trial in projection.trials.items()
        if trial["status"] == "completed"
        and projection.trial_assessments[key]["candidate_freeze_eligibility"]["eligible"]
    )
    if "metric" in rule:
        metric = rule["metric"]
        ids.sort(
            key=lambda key: decimal_value(
                projection.trial_assessments[key]["actuals"][metric],
                allow_positive_infinity="profit_factor" in metric,
            ),
            reverse=rule["order"] == "descending",
        )
    return ids
