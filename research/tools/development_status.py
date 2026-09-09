#!/usr/bin/env python3
"""Development evidence 的狀態表與 blind-review eligibility 輔助工具。

這個工具只處理 Development evidence 的可驗證狀態。它把 formal gates、
research targets、evidence validity 與 candidate freeze eligibility 分開，
並以明確的 outcome exposure 旗標判定 blind review 是否仍可進行。

它不讀取 Historical Evaluation artifact，也不以 Historical Evaluation 或
Study terminal 狀態推導 blind-review eligibility。
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import load_canonical  # noqa: E402
from validator.errors import WorkflowError  # noqa: E402
from validator.metrics import compare  # noqa: E402

STATUS_SCHEMA_PATH = Path(__file__).with_name("development-status.schema.yml")
VALID_EVIDENCE_STATUSES = {"valid", "invalid", "blocked", "needs-repair", "unavailable"}


class DevelopmentStatusError(ValueError):
    """Development status table 不符合可驗證契約。"""


def _target_records(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """把新舊 runner 的 target 表示法轉成只讀的統一 list。"""

    raw = evidence.get("research_target_records")
    if raw is None:
        raw = evidence.get("research_targets")
    if raw is None:
        return []
    if isinstance(raw, dict):
        records = []
        for name, record in raw.items():
            if not isinstance(record, dict):
                raise DevelopmentStatusError(f"research target {name} 必須是 mapping")
            records.append({**record, "target": name})
        return records
    if isinstance(raw, list):
        return raw
    raise DevelopmentStatusError("research targets 必須是 mapping 或 list")


def _record_names(
    records: list[dict[str, Any]], label: str, *, name_key: str = "target"
) -> list[str]:
    names: list[str] = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get(name_key), str):
            raise DevelopmentStatusError(f"{label} record 缺少 {name_key}")
        name = record[name_key]
        if name in names:
            raise DevelopmentStatusError(f"{label} 不得重複：{name}")
        names.append(name)
    return names


def _validate_rule_records(
    records: list[dict[str, Any]],
    rules: dict[str, Any],
    label: str,
    *,
    name_key: str,
) -> None:
    for record in records:
        name = record[name_key]
        rule = rules.get(name)
        if not isinstance(rule, dict):
            raise DevelopmentStatusError(f"{label} {name} 未登記")
        if (
            record.get("operator") != rule.get("operator")
            or record.get("required") != rule.get("value")
        ):
            raise DevelopmentStatusError(f"{label} {name} 的 operator 或 required 與登記不一致")


def _passed_records(
    records: list[dict[str, Any]],
    label: str,
    *,
    recompute: bool,
) -> list[str]:
    failures: list[str] = []
    for record in records:
        name = record.get("gate") or record.get("target")
        if not isinstance(name, str):
            raise DevelopmentStatusError(f"{label} record 缺少名稱")
        passed = record.get("passed")
        if not isinstance(passed, bool):
            raise DevelopmentStatusError(f"{label} {name} 的 passed 必須是 boolean")
        comparable = {"actual", "operator", "required"}.issubset(record)
        if recompute and comparable:
            try:
                expected = compare(
                    record["actual"],
                    record["operator"],
                    record["required"],
                    metric=name,
                )
            except (TypeError, ValueError, WorkflowError) as exc:
                raise DevelopmentStatusError(
                    f"{label} {name} 的 actual/operator/required 無法重算"
                ) from exc
            if passed != expected:
                raise DevelopmentStatusError(f"{label} {name} 的 passed 與重算結果不一致")
        if not passed:
            failures.append(name)
    return failures


def _declared_failures(
    evidence: dict[str, Any],
    keys: tuple[str, ...],
    expected: list[str],
    label: str,
) -> None:
    for key in keys:
        if key in evidence and evidence[key] != expected:
            raise DevelopmentStatusError(f"{label} 與 {key} 不一致")


def _status_table(
    *,
    formal_failures: list[str],
    target_failures: list[str],
    target_registered: bool,
    target_available: bool,
    evidence_status: str,
) -> dict[str, Any]:
    if evidence_status not in VALID_EVIDENCE_STATUSES:
        raise DevelopmentStatusError(f"未知 Development evidence status：{evidence_status}")

    if not target_registered:
        target_status = "not_registered"
    elif not target_available:
        target_status = "not_available"
    else:
        target_status = "failed" if target_failures else "passed"

    candidate_reasons: list[str] = []
    if evidence_status != "valid":
        candidate_reasons.append(f"development_evidence_{evidence_status}")
    candidate_reasons.extend(formal_failures)
    candidate_reasons.extend(target_failures)
    if target_registered and not target_available:
        candidate_reasons.append("research_targets_unavailable")

    candidate_eligible = not candidate_reasons
    return {
        "formal_development_gates": {
            "failed": formal_failures,
            "status": "failed" if formal_failures else "passed",
        },
        "research_targets": {
            "failed": target_failures,
            "status": target_status,
        },
        "development_evidence_validity": {
            "status": evidence_status,
            "validated": evidence_status == "valid",
        },
        "candidate_freeze_eligibility": {
            "eligible": candidate_eligible,
            "reasons": candidate_reasons,
            "status": "eligible" if candidate_eligible else "ineligible",
        },
    }


def build_development_status(
    evidence: dict[str, Any],
    preregistration: dict[str, Any],
    *,
    evidence_status: str = "valid",
    strict_targets: bool = True,
) -> dict[str, Any]:
    """從 runner 產出的獨立 gate/target records 建立狀態表。

    `strict_targets=True` 是新 runner 的預設：preregistration 登記了
    research targets 時，每一項都必須有可驗證 record。舊 evidence 可用
    `strict_targets=False` 做相容性檢查，但不會把缺失的 target 當成通過。
    """

    gate_records = evidence.get("gates")
    if not isinstance(gate_records, list):
        raise DevelopmentStatusError("Development evidence gates 必須是 list")
    formal_failures = _passed_records(gate_records, "formal gate", recompute=True)
    _declared_failures(evidence, ("failed_gates", "workflow_failures"), formal_failures, "formal gates")

    eligibility_rules = preregistration.get("eligibility_rules", {})
    if not isinstance(eligibility_rules, dict):
        raise DevelopmentStatusError("preregistration eligibility_rules 必須是 mapping")
    formal_rules = eligibility_rules.get("development_gates", {})
    if not isinstance(formal_rules, dict):
        raise DevelopmentStatusError("preregistration development_gates 必須是 mapping")
    gate_names = _record_names(gate_records, "formal gate", name_key="gate")
    if set(gate_names) != set(formal_rules):
        raise DevelopmentStatusError("formal gates records 必須與 preregistration 完整一致")
    _validate_rule_records(
        gate_records,
        formal_rules,
        "formal gate",
        name_key="gate",
    )
    registered = eligibility_rules.get("research_targets", {})
    if not isinstance(registered, dict):
        raise DevelopmentStatusError("preregistration research_targets 必須是 mapping")
    target_records = _target_records(evidence)
    target_names = _record_names(target_records, "research target")
    target_registered = bool(registered)
    target_available = not target_registered or set(target_names) == set(registered)
    if strict_targets and target_registered and not target_available:
        missing = sorted(set(registered).difference(target_names))
        extra = sorted(set(target_names).difference(registered))
        raise DevelopmentStatusError(
            f"research targets records 不完整；missing={missing}, extra={extra}"
        )
    _validate_rule_records(
        target_records,
        registered,
        "research target",
        name_key="target",
    )
    target_failures = _passed_records(
        target_records,
        "research target",
        # 新的統一 record 有 actual/operator/required 時由 validator 重算；
        # 舊 runner 的比較證據可能是多欄位 composite，則核對其 passed flag。
        recompute=True,
    )
    _declared_failures(
        evidence,
        ("research_target_failures", "target_failures"),
        target_failures,
        "research targets",
    )

    if "disposition" in evidence:
        expected_disposition = "fail" if formal_failures else "pass"
        if evidence["disposition"] != expected_disposition:
            raise DevelopmentStatusError(
                "Development disposition 必須只反映 formal Development gates"
            )

    result = _status_table(
        formal_failures=formal_failures,
        target_failures=target_failures,
        target_registered=target_registered,
        target_available=target_available,
        evidence_status=evidence_status,
    )
    if result["development_evidence_validity"]["status"] == "valid":
        result["development_evidence_validity"]["validated"] = True
    return result


def finalize_development_evidence(
    evidence: dict[str, Any],
    preregistration: dict[str, Any],
) -> dict[str, Any]:
    """供未來 Development runner 在 atomic publish 前補上狀態表。

    這個 helper 不會創造交易、改寫門檻或修補缺失 evidence；它只會根據
    runner 已產出的 records 固定欄位語意。若 evidence 本身無法解析，應由
    runner 以 blocked/needs-repair 交接，不能呼叫本函式偽造一份通過檔案。
    """

    output = deepcopy(evidence)
    # 不採信 runner 自報的 disposition；尤其不能讓 target 失敗把它誤寫成 fail。
    # formal gates、failed_gates 與 target records 仍由 build_development_status 驗證。
    output.pop("disposition", None)
    status = build_development_status(output, preregistration)
    formal_failures = status["formal_development_gates"]["failed"]
    target_failures = status["research_targets"]["failed"]
    output["disposition"] = "fail" if formal_failures else "pass"
    output["failed_gates"] = formal_failures
    output["research_target_failures"] = target_failures
    output["candidate_selection_eligible"] = status["candidate_freeze_eligibility"]["eligible"]
    output["candidate_selection_ineligibility_reasons"] = status[
        "candidate_freeze_eligibility"
    ]["reasons"]
    output["development_status"] = status
    return output


def build_development_evidence_failure_status(
    preregistration: dict[str, Any],
    *,
    evidence_status: str,
    reason: str,
) -> dict[str, Any]:
    """在 evidence 不能驗證時建立交接狀態，不宣稱 gates 已通過或失敗。

    這個狀態只表示「目前不能完成 evidence 驗證」。它不會產生
    `development.yml`，也不會把流程直接改成 Study terminal。呼叫方可以用
    `needs-repair` 表示可修復問題，或用 `blocked`／`unavailable` 表示等待
    外部條件或無法取得證據。
    """

    if evidence_status not in VALID_EVIDENCE_STATUSES - {"valid"}:
        raise DevelopmentStatusError(
            f"evidence failure 必須使用非 valid status：{evidence_status}"
        )
    if not isinstance(reason, str) or not reason:
        raise DevelopmentStatusError("evidence failure 必須保存具體 reason")
    eligibility_rules = preregistration.get("eligibility_rules", {})
    if not isinstance(eligibility_rules, dict):
        raise DevelopmentStatusError("preregistration eligibility_rules 必須是 mapping")
    registered = eligibility_rules.get("research_targets", {})
    if not isinstance(registered, dict):
        raise DevelopmentStatusError("preregistration research_targets 必須是 mapping")
    target_status = "not_available" if registered else "not_registered"
    return {
        "formal_development_gates": {
            "failed": [],
            "status": "not_available",
        },
        "research_targets": {
            "failed": [],
            "status": target_status,
        },
        "development_evidence_validity": {
            "reason": reason,
            "status": evidence_status,
            "validated": False,
        },
        "candidate_freeze_eligibility": {
            "eligible": False,
            "reasons": [f"development_evidence_{evidence_status}"],
            "status": "ineligible",
        },
    }


def validate_development_status_table(
    evidence: dict[str, Any], preregistration: dict[str, Any]
) -> dict[str, Any]:
    """驗證 runner 已發布的 status table，並確認 target 失敗不污染 evidence validity。"""

    status = evidence.get("development_status")
    if not isinstance(status, dict):
        raise DevelopmentStatusError("新 Development evidence 必須包含 development_status")
    schema = load_canonical(STATUS_SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(status), key=lambda item: list(item.absolute_path))
    if errors:
        location = ".".join(str(part) for part in errors[0].absolute_path) or "$"
        raise DevelopmentStatusError(f"development_status schema error at {location}: {errors[0].message}")
    expected = build_development_status(evidence, preregistration)
    if status != expected:
        raise DevelopmentStatusError("development_status 與 formal gates／research targets 重算結果不一致")
    if status["research_targets"]["status"] == "failed" and status[
        "development_evidence_validity"
    ]["status"] != "valid":
        raise DevelopmentStatusError("research target 失敗不得把合法 evidence 標成 invalid")
    expected_candidate = status["candidate_freeze_eligibility"]
    if "candidate_selection_eligible" in evidence and evidence[
        "candidate_selection_eligible"
    ] != expected_candidate["eligible"]:
        raise DevelopmentStatusError("candidate_selection_eligible 與 status table 不一致")
    if "candidate_selection_ineligibility_reasons" in evidence and evidence[
        "candidate_selection_ineligibility_reasons"
    ] != expected_candidate["reasons"]:
        raise DevelopmentStatusError(
            "candidate_selection_ineligibility_reasons 與 status table 不一致"
        )
    return status


def blind_review_status(
    *,
    development_evidence_available: bool,
    formal_evaluation_exposed: bool = False,
    outcome_bearing_terminal_exposed: bool = False,
) -> dict[str, Any]:
    """依 outcome exposure 判定 blind review；故意不接收 historical status。"""

    exposed = formal_evaluation_exposed or outcome_bearing_terminal_exposed
    if exposed:
        reasons = []
        if formal_evaluation_exposed:
            reasons.append("formal_evaluation_exposed")
        if outcome_bearing_terminal_exposed:
            reasons.append("outcome_bearing_terminal_exposed")
        return {
            "eligible": False,
            "reasons": reasons,
            "status": "blocked-by-exposed-outcome",
        }
    return {
        "eligible": True,
        "reasons": (
            []
            if development_evidence_available
            else ["development_evidence_unavailable"]
        ),
        "status": (
            "eligible"
            if development_evidence_available
            else "eligible-with-development-evidence-unavailable"
        ),
    }


def independent_stage_status(
    development: dict[str, Any],
    *,
    historical_evaluation_status: str = "not_started",
    study_terminal_status: str = "not_inspected",
    development_evidence_available: bool = True,
    formal_evaluation_exposed: bool = False,
    outcome_bearing_terminal_exposed: bool = False,
) -> dict[str, Any]:
    """輸出一張不把 lifecycle 狀態互相推導的總表。"""

    blind = blind_review_status(
        development_evidence_available=development_evidence_available,
        formal_evaluation_exposed=formal_evaluation_exposed,
        outcome_bearing_terminal_exposed=outcome_bearing_terminal_exposed,
    )
    return {
        "development": development,
        "blind_review": {
            **blind,
            "eligibility_basis": "explicit-outcome-exposure-only",
        },
        "historical_evaluation": {"status": historical_evaluation_status},
        "study_terminal": {"status": study_terminal_status},
        "candidate_freeze": development["candidate_freeze_eligibility"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="驗證 Development evidence 狀態表")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument(
        "--formal-evaluation-exposed",
        action="store_true",
        help="只表示呼叫方已明確確認結果曝光，不會讀取該結果",
    )
    parser.add_argument(
        "--outcome-bearing-terminal-exposed",
        action="store_true",
        help="只表示呼叫方已明確確認帶結果的 terminal 內容曝光",
    )
    return parser


def _print_evidence_failure(
    preregistration: dict[str, Any],
    *,
    evidence_status: str,
    reason: str,
    formal_evaluation_exposed: bool,
    outcome_bearing_terminal_exposed: bool,
) -> None:
    development = build_development_evidence_failure_status(
        preregistration,
        evidence_status=evidence_status,
        reason=reason,
    )
    stage_status = independent_stage_status(
        development,
        development_evidence_available=False,
        formal_evaluation_exposed=formal_evaluation_exposed,
        outcome_bearing_terminal_exposed=outcome_bearing_terminal_exposed,
    )
    print(
        json.dumps(
            {
                "error": reason,
                "stage_status": stage_status,
                "status": "failed",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    preregistration: dict[str, Any] | None = None
    try:
        raw_preregistration = load_canonical(args.preregistration)
        if not isinstance(raw_preregistration, dict):
            raise DevelopmentStatusError("preregistration 必須是 mapping")
        preregistration = raw_preregistration
        evidence = load_canonical(args.evidence)
        if not isinstance(evidence, dict):
            raise DevelopmentStatusError("evidence 必須是 mapping")
        development = validate_development_status_table(evidence, preregistration)
        output = independent_stage_status(
            development,
            development_evidence_available=True,
            formal_evaluation_exposed=args.formal_evaluation_exposed,
            outcome_bearing_terminal_exposed=args.outcome_bearing_terminal_exposed,
        )
        print(json.dumps({"status": "passed", "stage_status": output}, ensure_ascii=False, sort_keys=True))
        return 2 if not output["blind_review"]["eligible"] else 0
    except FileNotFoundError as exc:
        if preregistration is not None:
            _print_evidence_failure(
                preregistration,
                evidence_status="unavailable",
                reason=f"Development evidence 無法取得：{exc}",
                formal_evaluation_exposed=args.formal_evaluation_exposed,
                outcome_bearing_terminal_exposed=args.outcome_bearing_terminal_exposed,
            )
            return 1
        print(
            json.dumps(
                {
                    "status": "failed",
                    "development_evidence_validity": {
                        "status": "unavailable",
                        "validated": False,
                    },
                    "error": str(exc),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1
    except (OSError, WorkflowError, ValueError, KeyError, TypeError) as exc:
        if preregistration is not None:
            _print_evidence_failure(
                preregistration,
                evidence_status="needs-repair",
                reason=str(exc),
                formal_evaluation_exposed=args.formal_evaluation_exposed,
                outcome_bearing_terminal_exposed=args.outcome_bearing_terminal_exposed,
            )
            return 1
        print(
            json.dumps(
                {
                    "status": "failed",
                    "development_evidence_validity": {"status": "invalid", "validated": False},
                    "error": str(exc),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
