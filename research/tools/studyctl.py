#!/usr/bin/env python3
"""Study 建立與 candidate freeze 前的單一入口檢查工具。

這支工具是 preflight（前置檢查），不是另一個 Study writer。它只讀取檔案，
把容易在 copy-forward 或人工填寫時遺漏的問題提早報出來：

* Study ID、research 目錄和所有資料路徑是否仍指向同一個版本；
* preregistration、qualification spec、candidate definition 與策略引擎是否
  使用同一組參數，且明確寫出指標的就緒條件；
* 策略引擎在 RSI 初始值、指標最早可用日、停損／停利歧義、持有期和 cooldown
  等邊界情境是否符合 contract；
* Source Bundle digest、Workflow Event chain 與 validator 支援的 gate 是否
  足以安全進入 candidate freeze。

使用方式（全域參數要放在子命令前）：

    python research/tools/studyctl.py --repository-root . precreate <study-id>
    python research/tools/studyctl.py --repository-root . all <study-id>
    python research/tools/studyctl.py --repository-root . identity <study-id>
    python research/tools/studyctl.py --repository-root . contract <study-id>
    python research/tools/studyctl.py --repository-root . synthetic <study-id>
    python research/tools/studyctl.py --repository-root . freeze <study-id>

輸出固定是 JSON。exit code 0 表示檢查通過（terminal 且沒有 candidate 的
Study 會標成 not-applicable，但不會被當成缺陷），1 表示找到檢查問題，2
表示命令或環境本身無法執行。
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import inspect
import json
import re
import sys
import textwrap
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_NAME = "strategy-forward-replication-research--v001"
STUDY_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,62}$")
RESEARCH_PATH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_-])research/(?P<name>[a-z0-9][a-z0-9-]{2,62})(?:/|$)"
)
SHARED_RESEARCH_ROOTS = {"market-data", "tools"}
MISSING = object()
PRECREATE_REQUIRED_DOCUMENTS = (
    "preregistration.yml",
    "candidate-definition.yml",
    "qualification-spec.yml",
    "development-trial-inputs.yml",
    "source-bundle.yml",
)

WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / WORKFLOW_NAME
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import canonical_digest, load_canonical  # noqa: E402
from validator.errors import WorkflowError  # noqa: E402
from validator.release import validate_release_record  # noqa: E402
from validator.study import WorkflowRules, validate_study  # noqa: E402
from writer.authority import AuthorityStore  # noqa: E402


@dataclass(frozen=True)
class StudyContext:
    """CLI 執行期間固定使用的 repository 與 Study 路徑。"""

    repository_root: Path
    workflow_root: Path
    study_id: str

    @property
    def study_root(self) -> Path:
        return self.workflow_root / "studies" / self.study_id

    @property
    def research_root(self) -> Path:
        return self.repository_root / "research" / self.study_id

    def display_path(self, path: Path) -> str:
        """輸出相對 repository 的路徑，讓結果可直接放進 CI log。"""

        try:
            return path.resolve().relative_to(self.repository_root).as_posix()
        except ValueError:
            return str(path)


@dataclass
class CheckResult:
    """一個子命令的機器可讀檢查結果。"""

    name: str
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "failed" if self.errors else "passed"

    def error(
        self,
        code: str,
        message: str,
        *,
        path: Path | None = None,
        expected: Any = MISSING,
        actual: Any = MISSING,
    ) -> None:
        self.errors.append(
            _finding(
                code,
                message,
                path=path,
                expected=expected,
                actual=actual,
            )
        )

    def warning(self, code: str, message: str, *, path: Path | None = None) -> None:
        self.warnings.append(_finding(code, message, severity="warning", path=path))

    def as_dict(self, context: StudyContext) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "study_id": context.study_id,
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details,
        }


class SyntheticFailure(RuntimeError):
    """Synthetic contract case 不符合預期。"""


class CliArgumentError(RuntimeError):
    """把 argparse 的使用錯誤轉成可供 CI 消費的結果。"""


class JsonArgumentParser(argparse.ArgumentParser):
    """保留 --help，同時讓其他 CLI 解析錯誤交給 main 輸出 JSON。"""

    def error(self, message: str) -> None:
        raise CliArgumentError(message)


def _finding(
    code: str,
    message: str,
    *,
    severity: str = "error",
    path: Path | None = None,
    expected: Any = MISSING,
    actual: Any = MISSING,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
    }
    if path is not None:
        value["path"] = str(path)
    # precreate 的結果會直接交給 CI 或其他工具消費；沒有單一可比較值
    # 的錯誤也保留欄位，並以 null 表示缺漏或未知。
    value["expected"] = None if expected is MISSING else expected
    value["actual"] = None if actual is MISSING else actual
    return value


def context_for(repository_root: Path | str, study_id: str) -> StudyContext:
    """建立不會穿越到其他 Study 的固定 context。"""

    return StudyContext(
        repository_root=Path(repository_root).expanduser().resolve(),
        workflow_root=(Path(repository_root).expanduser().resolve() / "workflows" / WORKFLOW_NAME),
        study_id=study_id,
    )


def _iter_keyed_strings(value: Any, keys: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            next_keys = (*keys, str(key))
            if isinstance(item, str):
                yield next_keys, item
            else:
                yield from _iter_keyed_strings(item, next_keys)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_keyed_strings(item, (*keys, str(index)))


def _walk_files(root: Path, suffixes: tuple[str, ...]) -> Iterable[Path]:
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in suffixes:
            yield path


def _load_document(
    context: StudyContext,
    result: CheckResult,
    name: str,
    *,
    required: bool = True,
) -> tuple[dict[str, Any] | None, Path | None]:
    """優先讀 Study manifest，並核對 research copy-forward 副本。"""

    candidates = [
        context.study_root / "manifests" / name,
        context.research_root / name,
    ]
    existing = [path for path in candidates if path.is_file()]
    if not existing:
        if required:
            result.error("missing-artifact", f"找不到必要檔案：{name}")
        return None, None

    loaded: list[tuple[Path, dict[str, Any]]] = []
    for path in existing:
        try:
            value = load_canonical(path)
        except Exception as exc:  # canonical loader 的例外包含 YAML parser 錯誤
            result.error(
                "invalid-canonical-yaml",
                f"無法讀取 canonical YAML：{exc}",
                path=path,
            )
            continue
        if not isinstance(value, dict):
            result.error("invalid-artifact-shape", "artifact 最上層必須是 mapping", path=path)
            continue
        loaded.append((path, value))

    if not loaded:
        return None, existing[0]
    primary_path, primary = loaded[0]
    for path, value in loaded[1:]:
        if value != primary:
            result.error(
                "copy-forward-artifact-drift",
                f"Study manifest 與 research 副本內容不一致：{name}",
                path=path,
            )
    return primary, primary_path


def _display_path(context: StudyContext, path: Path) -> Path:
    """把檢查結果中的路徑固定成 repository-relative 形式。"""

    return Path(context.display_path(path))


def _load_research_document(
    context: StudyContext,
    result: CheckResult,
    name: str,
    *,
    required: bool = True,
    compare_manifest: bool = True,
) -> tuple[dict[str, Any] | None, Path | None]:
    """只從同名 research bundle 載入文件，並核對已存在的 Study copy。"""

    research_path = context.research_root / name
    displayed_research_path = _display_path(context, research_path)
    if not research_path.is_file():
        if required:
            result.error(
                "missing-artifact",
                f"找不到必要檔案：{name}",
                path=displayed_research_path,
                expected="file",
                actual="missing",
            )
        return None, None

    try:
        value = load_canonical(research_path)
    except Exception as exc:
        result.error(
            "invalid-canonical-yaml",
            f"無法讀取 canonical YAML：{exc}",
            path=displayed_research_path,
            expected="repository-canonical YAML mapping",
            actual=str(exc),
        )
        return None, research_path
    if not isinstance(value, dict):
        result.error(
            "invalid-artifact-shape",
            "artifact 最上層必須是 mapping",
            path=displayed_research_path,
            expected="mapping",
            actual=type(value).__name__,
        )
        return None, research_path

    if compare_manifest:
        manifest_path = context.study_root / "manifests" / name
        if manifest_path.is_file():
            try:
                manifest_value = load_canonical(manifest_path)
            except Exception as exc:
                result.error(
                    "invalid-canonical-yaml",
                    f"無法讀取同名 Study manifest：{exc}",
                    path=_display_path(context, manifest_path),
                    expected="repository-canonical YAML mapping",
                    actual=str(exc),
                )
            else:
                if manifest_value != value:
                    result.error(
                        "copy-forward-artifact-drift",
                        f"同名 Study manifest 與 research 副本內容不一致：{name}",
                        path=_display_path(context, manifest_path),
                        expected=value,
                        actual=manifest_value,
                    )

    return value, research_path


def _get_path(value: Any, path: str | Iterable[str], default: Any = MISSING) -> Any:
    parts = path.split(".") if isinstance(path, str) else list(path)
    current = value
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def _numeric_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, (int, float, str)) and isinstance(right, (int, float, str)):
        try:
            return Decimal(str(left)) == Decimal(str(right))
        except (InvalidOperation, ValueError):
            pass
    return left == right


def _semantic_equal(left: Any, right: Any) -> bool:
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(
            _semantic_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _semantic_equal(item_left, item_right)
            for item_left, item_right in zip(left, right, strict=True)
        )
    return _numeric_equal(left, right)


def _int_value(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} 不得是 boolean")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} 必須是整數") from exc
    if str(parsed) != str(value) and not isinstance(value, int):
        # 接受 YAML 的 "20"，但拒絕 20.5 或其他會被截斷的值。
        try:
            if Decimal(str(value)) != Decimal(parsed):
                raise ValueError(f"{label} 必須是整數")
        except InvalidOperation as exc:
            raise ValueError(f"{label} 必須是整數") from exc
    return parsed


def _path_has_other_study(
    context: StudyContext,
    value: str,
) -> str | None:
    match = re.search(r"(?:^|/)research/([^/]+)(?:/|$)", value)
    if match is None:
        return None
    name = match.group(1)
    if name == context.study_id:
        return None
    # 共用 market-data/tools 目錄可以被引用；其他 research/<name> 都必須是本 Study。
    if name not in SHARED_RESEARCH_ROOTS:
        return name
    return None


def run_identity(context: StudyContext) -> CheckResult:
    """檢查 Study、research 與其中的路徑是否使用同一個 Study ID。"""

    result = CheckResult("identity")
    if STUDY_ID_PATTERN.fullmatch(context.study_id) is None:
        result.error(
            "invalid-study-id",
            "Study ID 必須是 3--63 個小寫英數字與連字號，且不能以連字號開頭",
        )
        return result

    if not context.workflow_root.is_dir():
        result.error("missing-workflow", f"找不到 Workflow：{context.workflow_root}")
    if not context.study_root.is_dir():
        result.error("missing-study", f"找不到 Study 目錄：{context.study_root}")
    if not context.research_root.is_dir():
        result.error("missing-research-bundle", f"找不到同名 research 目錄：{context.research_root}")

    checked_files = 0
    for path in [
        *_walk_files(context.study_root, (".yml",)),
        *_walk_files(context.research_root, (".yml", ".py")),
    ]:
        checked_files += 1
        if path.suffix == ".yml":
            try:
                value = load_canonical(path)
            except Exception as exc:
                result.error("invalid-canonical-yaml", f"無法讀取 canonical YAML：{exc}", path=path)
                continue
            for key_path, string in _iter_keyed_strings(value):
                if key_path[-1] == "study_id" and string != context.study_id:
                    result.error(
                        "study-id-mismatch",
                        f"欄位 study_id 寫成 {string!r}，應為 {context.study_id!r}",
                        path=path,
                    )
                other = _path_has_other_study(context, string)
                if other is not None:
                    result.error(
                        "stale-research-path",
                        f"路徑仍指向另一個 Study research 目錄：research/{other}",
                        path=path,
                    )
        else:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for match in RESEARCH_PATH_PATTERN.finditer(text):
                other = match.group("name")
                if other != context.study_id and other not in SHARED_RESEARCH_ROOTS:
                    result.error(
                        "stale-research-path",
                        f"程式碼仍包含另一個 Study research 路徑：research/{other}",
                        path=path,
                    )

    result.details.update(
        {
            "study_root": context.display_path(context.study_root),
            "research_root": context.display_path(context.research_root),
            "checked_files": checked_files,
        }
    )
    return result


def _find_contract(
    context: StudyContext,
    result: CheckResult,
    candidate: dict[str, Any] | None,
    preregistration: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, Path | None, str | None]:
    """找出明確的 implementation contract。

    新 Study 可以把 contract 放在獨立的 implementation-contract.yml，或放在
    candidate-definition 的 indicator_contract。後者會跟著 candidate manifest
    一起被 Source Bundle 綁定，不會變成未追蹤的旁路設定。
    """

    external, external_path = _load_document(
        context, result, "implementation-contract.yml", required=False
    )
    if external_path is not None:
        if isinstance(external, dict):
            return external, external_path, "external"
        result.error(
            "invalid-implementation-contract",
            "implementation contract 必須是 mapping",
            path=external_path,
        )
        return None, external_path, "external"

    for label, document in (
        ("candidate-definition", candidate),
        ("preregistration", preregistration),
    ):
        if not isinstance(document, dict):
            continue
        if isinstance(document.get("implementation_contract"), dict):
            return document["implementation_contract"], None, label
        if isinstance(document.get("indicator_contract"), dict):
            return {"indicator_contract": document["indicator_contract"]}, None, label
        eligibility = document.get("eligibility_rules")
        if isinstance(eligibility, dict) and isinstance(eligibility.get("indicator_contract"), dict):
            return {"indicator_contract": eligibility["indicator_contract"]}, None, label

    return None, None, None


def _indicator_section(contract: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("indicator_contract", "indicators"):
        value = contract.get(key)
        if isinstance(value, dict):
            return value
    if any(key in contract for key in ("sma", "rsi", "volume_lead")):
        return contract
    return None


def _source_bundle_entries(source_bundle: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(source_bundle, dict) or not isinstance(source_bundle.get("files"), list):
        return {}
    entries: dict[str, str] = {}
    for item in source_bundle["files"]:
        if isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("digest"), str):
            entries[item["path"]] = item["digest"]
    return entries


def _resolve_inside(root: Path, relative: str) -> Path | None:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _engine_path(
    context: StudyContext,
    source_bundle: dict[str, Any] | None,
    contract: dict[str, Any] | None,
    result: CheckResult,
) -> Path | None:
    entries = _source_bundle_entries(source_bundle)
    engine = contract.get("engine", {}) if isinstance(contract, dict) else {}
    declared = engine.get("path") if isinstance(engine, dict) else None
    candidates: list[str] = []
    if isinstance(declared, str):
        candidates = [declared]
    else:
        candidates = [
            path
            for path in entries
            if path.startswith("src/")
            and path.endswith(".py")
            and not path.endswith("/__init__.py")
            and "/tests/" not in path
        ]
        preferred = [path for path in candidates if "mean_reversion" in path or "strategy" in path]
        if len(preferred) == 1:
            candidates = preferred

    if len(candidates) != 1:
        result.error(
            "engine-path-ambiguous",
            "無法從 Source Bundle 唯一找出策略引擎；請在 implementation contract 明寫 engine.path",
            path=_display_path(context, context.research_root / "implementation-contract.yml"),
            expected="one strategy engine path",
            actual=candidates,
        )
        return None
    relative = candidates[0]
    if relative not in entries:
        result.error(
            "engine-not-in-source-bundle",
            f"策略引擎不在 Source Bundle：{relative}",
            path=_display_path(context, context.research_root / "source-bundle.yml"),
            expected=relative,
            actual=sorted(entries),
        )
    path = _resolve_inside(context.repository_root, relative)
    if path is None:
        result.error(
            "engine-path-escapes-repository",
            f"策略引擎路徑逃出 repository：{relative}",
            path=_display_path(context, context.research_root / "implementation-contract.yml"),
            expected="repository-relative path",
            actual=relative,
        )
        return None
    if not path.is_file():
        result.error("missing-engine", f"找不到策略引擎：{relative}", path=path)
        return None
    result.details["engine_path"] = context.display_path(path)
    return path


def _load_engine(path: Path, result: CheckResult) -> ModuleType | None:
    module_name = f"_studyctl_engine_{hashlib.sha256(str(path).encode()).hexdigest()[:16]}"
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError("找不到 Python loader")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as exc:
        result.error("engine-import-failed", f"無法載入策略引擎：{exc}", path=path)
        return None


def _call_indicators(module: ModuleType, bars: pd.DataFrame, spec: Any) -> pd.DataFrame:
    function = getattr(module, "indicators", None)
    if not callable(function):
        raise SyntheticFailure("策略引擎沒有可呼叫的 indicators 函式")
    parameters = inspect.signature(function).parameters
    kwargs = {"spec": spec} if "spec" in parameters else {}
    value = function(bars, **kwargs)
    if not isinstance(value, pd.DataFrame):
        raise SyntheticFailure("indicators 沒有回傳 DataFrame")
    return value


def _call_backtest(
    module: ModuleType,
    bars: pd.DataFrame,
    spec: Any,
    cost: Any,
) -> Any:
    function = getattr(module, "backtest", None)
    if not callable(function):
        raise SyntheticFailure("策略引擎沒有可呼叫的 backtest 函式")
    parameters = inspect.signature(function).parameters
    kwargs: dict[str, Any] = {}
    if "spec" in parameters:
        kwargs["spec"] = spec
    if "cost" in parameters and cost is not None:
        kwargs["cost"] = cost
    return function(bars, **kwargs)


def _registered_values(
    candidate: dict[str, Any], preregistration: dict[str, Any]
) -> dict[str, Any]:
    signal = _get_path(preregistration, "eligibility_rules.accepted_signal", {})
    candidate_signal = candidate.get("signal", {})
    candidate_mean = _get_path(candidate_signal, "mean_reversion", {})
    registered_mean = _get_path(signal, "mean_reversion", {})
    candidate_volume = _get_path(candidate_signal, "volume_leads_price", {})
    registered_volume = _get_path(signal, "volume_leads_price", {})
    candidate_cooldown = _get_path(candidate_signal, "cooldown", {})
    registered_cooldown = _get_path(signal, "cooldown", {})
    return {
        "sma_lookback": _get_path(candidate_mean, "sma_length"),
        "rsi_lookback": _get_path(candidate_mean, "rsi_length"),
        "rsi_max": _get_path(candidate_mean, "rsi_maximum"),
        "volume_lookback": _get_path(candidate_volume, "volume_average_length"),
        "volume_lead_window": _get_path(candidate_volume, "prior_session_window"),
        "volume_spike_ratio": _get_path(candidate_volume, "volume_ratio_minimum"),
        "cooldown_sessions": _get_path(candidate_cooldown, "completed_session_steps_after_exit"),
        "target_return": _get_path(candidate, "execution.target.level_from_raw_entry_open"),
        "stop_return": _get_path(candidate, "execution.stop.level_from_raw_entry_open"),
        "holding_sessions": _get_path(candidate, "execution.held_complete_sessions"),
        "fold_warmup_sessions": _get_path(candidate, "fold_policy.evaluation_fold_warmup_sessions"),
        "risk_fraction": _get_path(candidate, "execution.position_sizing.risk_fraction_of_pre_entry_equity"),
        "registered_sma_lookback": _get_path(registered_mean, "sma_length"),
        "registered_rsi_lookback": _get_path(registered_mean, "rsi_length"),
        "registered_rsi_max": _get_path(registered_mean, "rsi_value"),
        "registered_volume_lookback": _get_path(registered_volume, "volume_average_length"),
        "registered_volume_lead_window": _get_path(registered_volume, "prior_session_window"),
        "registered_volume_spike_ratio": _get_path(registered_volume, "volume_ratio_value"),
        "registered_cooldown_sessions": _get_path(
            registered_cooldown, "minimum_completed_session_steps_after_exit"
        ),
        "registered_target_return": _get_path(
            preregistration, "eligibility_rules.execution.target.level_from_raw_entry_open"
        ),
        "registered_stop_return": _get_path(
            preregistration, "eligibility_rules.execution.stop.level_from_raw_entry_open"
        ),
        "registered_holding_sessions": _get_path(
            preregistration, "maximum_holding_sessions", default=MISSING
        ),
        "registered_fold_warmup_sessions": preregistration.get("fold_warmup_sessions"),
        "registered_risk_fraction": _get_path(
            preregistration, "eligibility_rules.execution.position_sizing.risk_fraction_of_pre_entry_equity"
        ),
    }


def _check_equal(
    result: CheckResult,
    label: str,
    left: Any,
    right: Any,
    *,
    path: Path | None = None,
) -> None:
    if left is MISSING or right is MISSING:
        result.error(
            "missing-contract-field",
            f"無法比較 {label}：缺少必要欄位",
            path=path,
            expected=None if right is MISSING else right,
            actual=None if left is MISSING else left,
        )
    elif not _semantic_equal(left, right):
        result.error(
            "contract-value-mismatch",
            f"{label} 不一致：{left!r} != {right!r}",
            path=path,
            expected=right,
            actual=left,
        )


def _derived_history_sessions(values: dict[str, Any], indicator: dict[str, Any] | None) -> int:
    """計算「訊號日前至少已有幾個 session」的最早就緒邊界。

    rolling window 包含當日，所以 SMA(n) 的零起始 index 是 n-1；RSI 先
    計算 price change，再對 change 做 n 筆 rolling，所以最早是 n；成交量
    平均量再往前取 lead window，最早是 volume_average + lead_window。
    """

    sma_length = _int_value(values["sma_lookback"], "SMA length")
    rsi_length = _int_value(values["rsi_lookback"], "RSI length")
    volume_length = _int_value(values["volume_lookback"], "Volume average length")
    lead_window = _int_value(values["volume_lead_window"], "Volume lead window")
    sma_min = _int_value(_get_path(indicator, "sma.min_periods", sma_length), "SMA min_periods")
    rsi_min = _int_value(_get_path(indicator, "rsi.min_periods", rsi_length), "RSI min_periods")
    volume_min = _int_value(
        _get_path(indicator, "volume_lead.average_min_periods", volume_length),
        "Volume average min_periods",
    )
    lead_min = _int_value(
        _get_path(indicator, "volume_lead.lead_min_periods", lead_window),
        "Volume lead min_periods",
    )
    return max(sma_min - 1, rsi_min, volume_min + lead_min)


def _check_gate_maps(
    result: CheckResult,
    preregistration: dict[str, Any],
    qualification: dict[str, Any],
    *,
    path: Path | None = None,
    exact: bool = False,
) -> None:
    pairs = (
        (
            "development",
            _get_path(preregistration, "eligibility_rules.development_gates", {}),
            qualification.get("development", {}),
        ),
        ("evaluation", preregistration.get("evaluation_gates", {}), qualification.get("evaluation", {})),
    )
    for stage, registered, qualified in pairs:
        equal = registered == qualified if exact else _semantic_equal(registered, qualified)
        if not equal:
            result.error(
                "gate-source-drift",
                f"{stage} gates 沒有和 preregistration 完全一致",
                path=path,
                expected=registered,
                actual=qualified,
            )


def _function_dict_keys(function: Callable[..., Any], *, assignment: str | None = None) -> set[str]:
    source = textwrap.dedent(inspect.getsource(function))
    tree = ast.parse(source)
    found: set[str] = set()

    def add_dict(node: ast.Dict) -> None:
        for key in node.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                found.add(key.value)

    for node in ast.walk(tree):
        if assignment is not None:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
                targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
                if assignment in targets:
                    add_dict(node.value)
        elif isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            add_dict(node.value)
    return found


def _validator_metric_names() -> tuple[set[str], set[str]]:
    from validator.artifacts import _recompute_development, historical_metrics

    return (
        _function_dict_keys(_recompute_development, assignment="actuals"),
        _function_dict_keys(historical_metrics),
    )


def _check_validator_gate_support(
    result: CheckResult,
    preregistration: dict[str, Any],
    qualification: dict[str, Any],
) -> None:
    try:
        development, evaluation = _validator_metric_names()
    except (OSError, SyntaxError, TypeError) as exc:
        result.error("validator-introspection-failed", f"無法讀取 validator 的 gate metric：{exc}")
        return
    configured = (
        ("development", set(_get_path(preregistration, "eligibility_rules.development_gates", {})), development),
        ("evaluation", set(preregistration.get("evaluation_gates", {})), evaluation),
    )
    for stage, names, supported in configured:
        unsupported = sorted(names - supported)
        if unsupported:
            result.error(
                "unsupported-gates",
                f"{stage} gates 使用 validator 不會產生的 metric：{unsupported}",
            )
    result.details["validator_metrics"] = {
        "development": sorted(development),
        "evaluation": sorted(evaluation),
    }


def run_contract(context: StudyContext) -> CheckResult:
    """檢查規格、實作參數、就緒邊界和 explicit indicator contract。"""

    result = CheckResult("contract")
    preregistration, prereg_path = _load_document(context, result, "preregistration.yml")
    candidate, candidate_path = _load_document(context, result, "candidate-definition.yml")
    qualification, qualification_path = _load_document(context, result, "qualification-spec.yml")
    source_bundle, source_bundle_path = _load_document(context, result, "source-bundle.yml")
    if not all(isinstance(value, dict) for value in (preregistration, candidate, qualification)):
        return result

    if isinstance(qualification, dict):
        expected_digest = canonical_digest((prereg_path or Path()).read_bytes()) if prereg_path else None
        if expected_digest is not None:
            _check_equal(
                result,
                "qualification.preregistration_digest",
                qualification.get("preregistration_digest"),
                expected_digest,
                path=qualification_path,
            )
        _check_gate_maps(result, preregistration, qualification)

    values = _registered_values(candidate, preregistration)
    signal_pairs = (
        ("SMA length", values["sma_lookback"], values["registered_sma_lookback"]),
        ("RSI length", values["rsi_lookback"], values["registered_rsi_lookback"]),
        ("RSI threshold", values["rsi_max"], values["registered_rsi_max"]),
        ("Volume average length", values["volume_lookback"], values["registered_volume_lookback"]),
        ("Volume lead window", values["volume_lead_window"], values["registered_volume_lead_window"]),
        ("Volume spike ratio", values["volume_spike_ratio"], values["registered_volume_spike_ratio"]),
        ("Cooldown", values["cooldown_sessions"], values["registered_cooldown_sessions"]),
        ("Target return", values["target_return"], values["registered_target_return"]),
        ("Stop return", values["stop_return"], values["registered_stop_return"]),
        ("Fold warmup", values["fold_warmup_sessions"], values["registered_fold_warmup_sessions"]),
        ("Risk fraction", values["risk_fraction"], values["registered_risk_fraction"]),
    )
    for label, candidate_value, registered_value in signal_pairs:
        _check_equal(result, f"candidate/preregistration {label}", candidate_value, registered_value, path=candidate_path)
    if values["holding_sessions"] is MISSING or values["registered_holding_sessions"] is MISSING:
        result.error(
            "missing-contract-field",
            "無法比較 candidate/preregistration Maximum holding span：缺少必要欄位",
            path=candidate_path,
        )
    else:
        try:
            _check_equal(
                result,
                "candidate/preregistration Maximum holding span",
                _int_value(values["holding_sessions"], "candidate holding sessions") + 1,
                values["registered_holding_sessions"],
                path=candidate_path,
            )
        except ValueError as exc:
            result.error("invalid-execution-contract", str(exc), path=candidate_path)

    contract, contract_path, contract_source = _find_contract(
        context, result, candidate, preregistration
    )
    result.details["contract_source"] = context.display_path(contract_path) if contract_path else contract_source
    if contract is None:
        result.error(
            "indicator-contract-missing",
            "沒有明確的 indicator contract；至少要登記 RSI formula、min_periods、not-ready、zero-gain/loss 規則與有效 warmup",
            path=candidate_path,
        )
        indicator: dict[str, Any] | None = None
    else:
        indicator = _indicator_section(contract)
        if indicator is None:
            result.error(
                "invalid-indicator-contract",
                "indicator contract 缺少 sma、rsi 或 volume_lead 區塊",
                path=contract_path or candidate_path,
            )

    # 即使 contract 遺漏，也計算可由已登記 window 得出的下限，避免 20/25
    # 這種會造成 silent not-ready 的錯誤被 contract 遺漏掩蓋。
    try:
        derived_history = _derived_history_sessions(values, indicator)
        result.details["derived_required_history_sessions"] = derived_history
        declared_warmup = _int_value(values["fold_warmup_sessions"], "fold warmup sessions")
        if declared_warmup < derived_history:
            result.error(
                "fold-warmup-too-short",
                f"fold warmup 只有 {declared_warmup} 個 session，但指標最早要到第 {derived_history} 個 session 才全部 ready",
                path=candidate_path,
            )
        if indicator is not None:
            required_history = _get_path(indicator, "required_history_sessions", MISSING)
            _check_equal(
                result,
                "indicator_contract.required_history_sessions",
                required_history,
                derived_history,
                path=contract_path or candidate_path,
            )
    except (KeyError, TypeError, ValueError) as exc:
        result.error("invalid-indicator-contract", f"無法計算指標就緒邊界：{exc}", path=contract_path or candidate_path)

    if indicator is not None:
        required_fields = (
            ("sma", "lookback"),
            ("sma", "min_periods"),
            ("sma", "not_ready"),
            ("rsi", "length"),
            ("rsi", "formula"),
            ("rsi", "min_periods"),
            ("rsi", "not_ready"),
            ("rsi", "zero_gain_and_loss"),
            ("rsi", "zero_loss_only"),
            ("rsi", "zero_gain_only"),
            ("volume_lead", "volume_average_length"),
            ("volume_lead", "prior_session_window"),
            ("volume_lead", "uses_prior_sessions_only"),
        )
        for section, key in required_fields:
            if _get_path(indicator, (section, key), MISSING) is MISSING:
                result.error(
                    "missing-contract-field",
                    f"indicator contract 缺少 {section}.{key}",
                    path=contract_path or candidate_path,
                )
        _check_equal(result, "contract.sma.lookback", _get_path(indicator, "sma.lookback"), values["sma_lookback"], path=contract_path or candidate_path)
        _check_equal(result, "contract.rsi.length", _get_path(indicator, "rsi.length"), values["rsi_lookback"], path=contract_path or candidate_path)
        _check_equal(result, "contract.volume_lead.volume_average_length", _get_path(indicator, "volume_lead.volume_average_length"), values["volume_lookback"], path=contract_path or candidate_path)
        _check_equal(result, "contract.volume_lead.prior_session_window", _get_path(indicator, "volume_lead.prior_session_window"), values["volume_lead_window"], path=contract_path or candidate_path)
        formula = _get_path(indicator, "rsi.formula", MISSING)
        if formula is not MISSING and formula not in {"simple-rolling-mean", "wilder"}:
            result.error("unsupported-rsi-formula", f"CLI 尚未支援 RSI formula：{formula!r}", path=contract_path or candidate_path)
        if _get_path(indicator, "volume_lead.uses_prior_sessions_only", MISSING) is not True:
            result.error(
                "volume-lead-lookahead",
                "volume_lead.uses_prior_sessions_only 必須明確為 true",
                path=contract_path or candidate_path,
            )

    if isinstance(qualification, dict):
        _check_validator_gate_support(result, preregistration, qualification)

    engine_path = _engine_path(context, source_bundle, contract, result)
    if engine_path is not None:
        module = _load_engine(engine_path, result)
        if module is not None:
            engine = contract.get("engine", {}) if isinstance(contract, dict) else {}
            spec_name = engine.get("spec_constant", "DEFAULT_SPEC") if isinstance(engine, dict) else "DEFAULT_SPEC"
            strategy_spec = getattr(module, spec_name, MISSING)
            if strategy_spec is MISSING:
                result.error("missing-engine-spec", f"策略引擎沒有 {spec_name}：{engine_path}", path=engine_path)
            else:
                for field_name, expected in (
                    ("sma_lookback", values["sma_lookback"]),
                    ("rsi_lookback", values["rsi_lookback"]),
                    ("rsi_max", values["rsi_max"]),
                    ("volume_lookback", values["volume_lookback"]),
                    ("volume_lead_window", values["volume_lead_window"]),
                    ("volume_spike_ratio", values["volume_spike_ratio"]),
                    ("cooldown_sessions", values["cooldown_sessions"]),
                    ("holding_sessions", values["holding_sessions"]),
                    ("fold_warmup_sessions", values["fold_warmup_sessions"]),
                    ("risk_fraction", values["risk_fraction"]),
                ):
                    actual = getattr(strategy_spec, field_name, MISSING)
                    if actual is not MISSING:
                        _check_equal(result, f"engine.{field_name}", actual, expected, path=engine_path)
                    else:
                        result.warning("engine-field-not-exposed", f"策略引擎沒有可直接核對的欄位：{field_name}", path=engine_path)
            result.details["engine_spec_constant"] = spec_name

    if isinstance(source_bundle, dict):
        entries = _source_bundle_entries(source_bundle)
        if contract_source == "external" and contract_path is not None:
            relative_contract = contract_path.resolve().relative_to(context.repository_root).as_posix()
            if relative_contract not in entries:
                result.error("contract-not-frozen", "implementation contract 沒有被 Source Bundle 綁定", path=contract_path)
        result.details["source_bundle_file_count"] = len(entries)
        result.details["source_bundle_path"] = context.display_path(source_bundle_path) if source_bundle_path else None

    return result


def _make_bars(
    rows: int,
    signal_indices: Iterable[int] = (),
    *,
    close_direction: str | None = None,
) -> pd.DataFrame:
    if close_direction not in {None, "above", "below"}:
        raise SyntheticFailure(f"不支援的 synthetic 收盤方向：{close_direction!r}")
    signals = list(signal_indices)
    index = pd.date_range("2020-01-02", periods=rows, freq="B")
    close = np.full(rows, 100.0)
    open_price = np.full(rows, 100.0)
    high = np.full(rows, 101.0)
    low = np.full(rows, 99.0)
    volume = np.full(rows, 1_000_000.0)
    for order, signal_index in enumerate(signals):
        if close_direction == "above":
            # 訊號日前一日先下跌，訊號日小幅反彈；如此同時滿足
            # close > prior close 與仍低於平滑均線，並保留 RSI 超賣。
            # 兩個相鄰測試訊號時，後一個訊號會把前一個訊號日當成
            # prior close；保留原本的 100，讓後一個訊號仍有 RSI loss。
            if signal_index + 1 not in signals:
                close[signal_index - 1] = 96.0
                high[signal_index - 1] = 100.0
                low[signal_index - 1] = 95.5
            close[signal_index] = 97.0
        else:
            close[signal_index] = 97.0 - order
        high[signal_index] = 100.0
        low[signal_index] = close[signal_index] - 0.5
        if signal_index >= 5:
            volume[signal_index - 5] = 2_000_000.0
    return pd.DataFrame(
        {"Open": open_price, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=index,
    )


def _assert_close(actual: Any, expected: Any, label: str) -> None:
    if pd.isna(expected):
        if not pd.isna(actual):
            raise SyntheticFailure(f"{label} 應為 not-ready NaN，實際是 {actual!r}")
        return
    if pd.isna(actual) or not np.isclose(float(actual), float(expected), rtol=1e-10, atol=1e-10):
        raise SyntheticFailure(f"{label} 不一致：實際 {actual!r}，預期 {expected!r}")


def _expected_simple_rsi(close: pd.Series, length: int, min_periods: int, contract: dict[str, Any]) -> pd.Series:
    change = close.diff()
    gain = change.clip(lower=0).rolling(length, min_periods=min_periods).mean()
    loss = (-change.clip(upper=0)).rolling(length, min_periods=min_periods).mean()
    raw = 100.0 - 100.0 / (1.0 + gain / loss)
    rsi_contract = contract["rsi"]
    not_ready = rsi_contract["not_ready"]
    if not_ready is None or not (isinstance(not_ready, str) and not_ready.casefold() == "nan"):
        raw = raw.where(loss.notna(), not_ready)
    raw = raw.where(loss != 0, rsi_contract["zero_loss_only"])
    raw = raw.where(gain != 0, rsi_contract["zero_gain_only"])
    raw = raw.where(~((gain == 0) & (loss == 0)), rsi_contract["zero_gain_and_loss"])
    return raw


def _run_rsi_case(
    result: CheckResult,
    module: ModuleType,
    spec: Any,
    indicator: dict[str, Any],
) -> None:
    rsi_contract = indicator.get("rsi")
    if not isinstance(rsi_contract, dict):
        raise SyntheticFailure("indicator contract 缺少 rsi mapping")
    formula = rsi_contract.get("formula")
    if formula != "simple-rolling-mean":
        raise SyntheticFailure(f"synthetic RSI case 尚未支援 formula={formula!r}")
    length = _int_value(rsi_contract["length"], "RSI contract length")
    min_periods = _int_value(rsi_contract["min_periods"], "RSI contract min_periods")
    close = pd.Series([100.0, 100.0, 100.0, 101.0, 100.0, 100.0])
    expected = _expected_simple_rsi(close, length, min_periods, indicator)
    private_rsi = getattr(module, "_rsi", None)
    if callable(private_rsi):
        actual = private_rsi(close, length)
    else:
        bars = _make_bars(len(close))
        bars["Close"] = close.to_numpy()
        actual_frame = _call_indicators(module, bars, spec)
        column = _get_path(indicator, "columns.rsi", f"rsi_{length}")
        if not isinstance(column, str) or column not in actual_frame:
            raise SyntheticFailure(f"找不到 RSI 輸出欄位：{column!r}")
        actual = actual_frame[column].reset_index(drop=True)
    if len(actual) != len(expected):
        raise SyntheticFailure("RSI 輸出長度不一致")
    for index, (actual_value, expected_value) in enumerate(zip(actual, expected, strict=True)):
        _assert_close(actual_value, expected_value, f"RSI index {index}")
    result.details["rsi_case"] = "passed"


def _run_readiness_case(
    result: CheckResult,
    module: ModuleType,
    spec: Any,
    values: dict[str, Any],
    indicator: dict[str, Any],
) -> None:
    required_history = _int_value(indicator["required_history_sessions"], "required_history_sessions")
    bars = _make_bars(required_history + 12)
    frame = _call_indicators(module, bars, spec)
    columns = _get_path(indicator, "columns", {})
    if not isinstance(columns, dict):
        columns = {}
    expected_columns = {
        "sma": columns.get("sma", f"sma_{_int_value(values['sma_lookback'], 'SMA length') }"),
        "rsi": columns.get("rsi", f"rsi_{_int_value(values['rsi_lookback'], 'RSI length') }"),
        "volume_lead": columns.get("volume_lead", "prior_volume_spike_ratio"),
    }
    missing = [column for column in expected_columns.values() if column not in frame]
    if missing:
        raise SyntheticFailure(f"indicators 缺少 contract 指定欄位：{missing}")
    ready = frame.loc[:, list(expected_columns.values())].notna().all(axis=1)
    indexes = np.flatnonzero(ready.to_numpy())
    if len(indexes) == 0:
        raise SyntheticFailure("synthetic data 上沒有任何一列指標同時 ready")
    first_ready = int(indexes[0])
    if first_ready != required_history:
        raise SyntheticFailure(
            f"第一個完整 ready row 是 index {first_ready}，contract 宣告 {required_history}"
        )
    result.details["first_ready_index"] = first_ready
    result.details["indicator_columns"] = expected_columns


def _run_exit_cases(result: CheckResult, module: ModuleType) -> None:
    exit_function = getattr(module, "_intraday_exit", None)
    if not callable(exit_function):
        raise SyntheticFailure("策略引擎沒有可檢查 gap／同日歧義的 _intraday_exit 函式")
    target = 104.0
    stop = 96.0
    cases = (
        (pd.Series({"Open": 95.0, "High": 100.0, "Low": 94.0}), (95.0, "stop-gap")),
        (pd.Series({"Open": 105.0, "High": 106.0, "Low": 104.0}), (105.0, "target-gap")),
        (pd.Series({"Open": 100.0, "High": 105.0, "Low": 95.0}), (96.0, "stop-same-session")),
        (pd.Series({"Open": 100.0, "High": 103.0, "Low": 97.0}), None),
    )
    for bar, expected in cases:
        actual = exit_function(bar, target, stop)
        if actual != expected:
            raise SyntheticFailure(f"intraday exit 結果不一致：實際 {actual!r}，預期 {expected!r}")
    result.details["intraday_exit_cases"] = len(cases)


def _synthetic_close_direction(contract: dict[str, Any], spec: Any) -> str | None:
    """從 contract 或 frozen engine 決定 holding case 的訊號日方向。"""

    direction_values: list[str] = []
    price_direction = contract.get("price_direction_confirmation", {})
    if isinstance(price_direction, dict):
        if price_direction.get("close_above_prior_close") is True:
            direction_values.append("above")
        if price_direction.get("close_below_prior_close") is True:
            direction_values.append("below")
        rule = price_direction.get("rule")
        if isinstance(rule, str):
            if "above" in rule:
                direction_values.append("above")
            if "below" in rule:
                direction_values.append("below")

    if not direction_values:
        if getattr(spec, "require_close_above_prior_close", False) is True:
            direction_values.append("above")
        if getattr(spec, "require_close_below_prior_close", False) is True:
            direction_values.append("below")
    unique = set(direction_values)
    if len(unique) > 1:
        raise SyntheticFailure(
            "implementation contract 必須明示唯一的 close-above-prior-close "
            "或 close-below-prior-close 方向"
        )
    # 沒有方向條件的舊引擎仍可用一般均值回歸訊號測 holding/cooldown；
    # 這不替它假定 above 或 below contract。
    return next(iter(unique), None)


def _run_holding_cooldown_case(
    result: CheckResult,
    module: ModuleType,
    spec: Any,
    cost: Any,
    contract: dict[str, Any],
) -> None:
    holding = _int_value(spec.holding_sessions, "engine holding_sessions")
    cooldown = _int_value(spec.cooldown_sessions, "engine cooldown_sessions")
    first_signal = 40
    first_entry = first_signal + 1
    first_exit = first_entry + holding
    rejected_signal = first_exit + cooldown - 1 if cooldown else None
    accepted_signal = first_exit + cooldown
    signal_indices = [first_signal]
    if rejected_signal is not None and rejected_signal != first_signal:
        signal_indices.append(rejected_signal)
    if accepted_signal not in signal_indices:
        signal_indices.append(accepted_signal)
    rows = max(180, accepted_signal + holding + 5)
    bars = _make_bars(
        rows,
        signal_indices,
        close_direction=_synthetic_close_direction(contract, spec),
    )
    backtest_result = _call_backtest(module, bars, spec, cost)
    trades = getattr(backtest_result, "trades", ())
    accepted = getattr(backtest_result, "accepted_signal_sessions", ())
    if len(trades) != 2:
        raise SyntheticFailure(f"holding/cooldown synthetic 預期 2 筆交易，實際 {len(trades)} 筆")
    first, second = trades
    if first.exit_reason != "time" or first.held_sessions != holding:
        raise SyntheticFailure(
            f"第一筆交易沒有按 holding_sessions 結束：reason={first.exit_reason!r}, held={first.held_sessions!r}"
        )
    if second.signal_session != bars.index[accepted_signal]:
        raise SyntheticFailure("第二筆交易沒有在 cooldown 完成後的 signal 進場")
    if rejected_signal is not None and bars.index[rejected_signal] in accepted:
        raise SyntheticFailure("cooldown 尚未完成時錯誤接受 signal")
    if second.entry_session != bars.index[accepted_signal + 1]:
        raise SyntheticFailure("第二筆交易沒有使用 signal 後下一個 session 的 open")
    result.details["holding_sessions"] = holding
    result.details["cooldown_sessions"] = cooldown
    result.details["accepted_signal_count"] = len(accepted)


def run_synthetic(context: StudyContext) -> CheckResult:
    """使用不含正式市場資料的合成 bars 執行 contract 邊界測試。"""

    result = CheckResult("synthetic")
    preregistration, _ = _load_document(context, result, "preregistration.yml")
    candidate, candidate_path = _load_document(context, result, "candidate-definition.yml")
    source_bundle, _ = _load_document(context, result, "source-bundle.yml")
    if not isinstance(preregistration, dict) or not isinstance(candidate, dict):
        return result
    contract, contract_path, _ = _find_contract(context, result, candidate, preregistration)
    indicator = _indicator_section(contract) if isinstance(contract, dict) else None
    if indicator is None:
        result.error(
            "indicator-contract-required",
            "synthetic checks 必須先有明確的 indicator contract，不能從模糊的 RSI(2) 猜測語意",
            path=contract_path or candidate_path,
        )
        return result
    engine_path = _engine_path(context, source_bundle, contract, result)
    if engine_path is None:
        return result
    module = _load_engine(engine_path, result)
    if module is None:
        return result
    spec_name = _get_path(contract, "engine.spec_constant", "DEFAULT_SPEC")
    spec = getattr(module, spec_name, MISSING)
    if spec is MISSING:
        result.error("missing-engine-spec", f"策略引擎沒有 {spec_name}", path=engine_path)
        return result
    cost_name = _get_path(contract, "engine.cost_constant", "BASE_COST")
    cost = getattr(module, cost_name, None)
    values = _registered_values(candidate, preregistration)
    cases: list[tuple[str, Callable[[], None]]] = [
        ("rsi", lambda: _run_rsi_case(result, module, spec, indicator)),
        ("readiness", lambda: _run_readiness_case(result, module, spec, values, indicator)),
        ("intraday-exit", lambda: _run_exit_cases(result, module)),
        (
            "holding-cooldown",
            lambda: _run_holding_cooldown_case(result, module, spec, cost, contract),
        ),
    ]
    passed: list[str] = []
    for name, case in cases:
        try:
            case()
        except (KeyError, TypeError, ValueError, AttributeError, SyntheticFailure) as exc:
            result.error("synthetic-case-failed", f"{name} case 失敗：{exc}", path=engine_path)
        else:
            passed.append(name)
    result.details["passed_cases"] = passed
    return result


def _check_source_bundle(
    context: StudyContext,
    result: CheckResult,
    source_bundle: dict[str, Any] | None,
    source_bundle_path: Path | None,
) -> None:
    if not isinstance(source_bundle, dict):
        return
    raw_files = source_bundle.get("files")
    if not isinstance(raw_files, list):
        result.error(
            "invalid-source-bundle",
            "Source Bundle 的 files 必須是 list",
            path=source_bundle_path,
            expected="list",
            actual=raw_files,
        )
        return
    seen_paths: set[str] = set()
    for index, item in enumerate(raw_files):
        if not isinstance(item, dict):
            result.error(
                "invalid-source-bundle-entry",
                f"Source Bundle 第 {index} 筆不是 mapping",
                path=source_bundle_path,
                expected={"path": "string", "digest": "sha256"},
                actual=item,
            )
            continue
        relative = item.get("path")
        digest = item.get("digest")
        if (
            not isinstance(relative, str)
            or not relative
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            result.error(
                "invalid-source-bundle-entry",
                f"Source Bundle 第 {index} 筆缺少有效 path 或 SHA-256 digest",
                path=source_bundle_path,
                expected={"path": "non-empty string", "digest": "64 lowercase hex characters"},
                actual=item,
            )
            continue
        if relative in seen_paths:
            result.error(
                "duplicate-source-bundle-path",
                f"Source Bundle 重複列出檔案：{relative}",
                path=source_bundle_path,
                expected="unique paths",
                actual=relative,
            )
        seen_paths.add(relative)
    entries = _source_bundle_entries(source_bundle)
    if not entries:
        result.error(
            "empty-source-bundle",
            "Source Bundle 沒有任何檔案",
            path=source_bundle_path,
            expected="at least one file entry",
            actual=source_bundle.get("files"),
        )
        return
    verified = 0
    for relative, expected_digest in sorted(entries.items()):
        source = _resolve_inside(context.repository_root, relative)
        if source is None:
            result.error(
                "source-path-escapes-repository",
                f"Source Bundle 路徑逃出 repository：{relative}",
                path=source_bundle_path,
                expected="repository-relative path",
                actual=relative,
            )
            continue
        if not source.is_file():
            result.error(
                "missing-source-file",
                f"Source Bundle 檔案不存在：{relative}",
                path=_display_path(context, source),
                expected="file",
                actual="missing",
            )
            continue
        actual_digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            result.error(
                "source-digest-mismatch",
                f"Source Bundle digest 不一致：{relative}",
                path=_display_path(context, source),
                expected=expected_digest,
                actual=actual_digest,
            )
            continue
        if source.suffix in {".yml", ".yaml"}:
            try:
                load_canonical(source)
            except Exception as exc:
                result.error(
                    "non-canonical-source-yaml",
                    f"Source Bundle 內的 YAML 不是 canonical：{relative}；{exc}",
                    path=_display_path(context, source),
                    expected="repository-canonical YAML",
                    actual=str(exc),
                )
                continue
        verified += 1
    result.details["source_bundle_file_count"] = len(entries)
    result.details["source_bundle_verified_file_count"] = verified


def _collect_keyed_values(
    value: Any,
    keys: set[str],
    path: tuple[str, ...] = (),
) -> list[tuple[tuple[str, ...], Any]]:
    found: list[tuple[tuple[str, ...], Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = (*path, str(key))
            if str(key) in keys:
                found.append((next_path, item))
            found.extend(_collect_keyed_values(item, keys, next_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_collect_keyed_values(item, keys, (*path, str(index))))
    return found


def _identity_path(context: StudyContext, path: Path | None) -> Path:
    return _display_path(context, path) if path is not None else Path(context.display_path(context.research_root))


def _check_precreate_identities(
    context: StudyContext,
    result: CheckResult,
    documents: dict[str, dict[str, Any] | None],
    paths: dict[str, Path | None],
) -> None:
    """核對尚未建立 Event 時仍可確定的 Study、family 與 Trial identity。"""

    preregistration = documents.get("preregistration.yml")
    candidate = documents.get("candidate-definition.yml")
    qualification = documents.get("qualification-spec.yml")
    trial_inputs = documents.get("development-trial-inputs.yml")
    if not all(
        isinstance(value, dict)
        for value in (preregistration, candidate, qualification, trial_inputs)
    ):
        return

    identity_documents = (
        ("candidate-definition.yml", candidate),
        ("preregistration.yml", preregistration),
        ("qualification-spec.yml", qualification),
        ("development-trial-inputs.yml", trial_inputs),
    )
    for name, document in identity_documents:
        assert isinstance(document, dict)
        document_path = _identity_path(context, paths.get(name))
        for key_path, actual in _collect_keyed_values(document, {"study_id"}):
            if actual != context.study_id:
                result.error(
                    "study-id-mismatch",
                    f"{name} 的 {'.'.join(key_path)} 不是目前 Study ID",
                    path=document_path,
                    expected=context.study_id,
                    actual=actual,
                )

    complete_family = preregistration.get("complete_candidate_family")
    if not isinstance(complete_family, list) or not complete_family or not all(
        isinstance(item, str) for item in complete_family
    ):
        result.error(
            "candidate-family-mismatch",
            "preregistration 沒有可用的 complete candidate family",
            path=_identity_path(context, paths.get("preregistration.yml")),
            expected="非空的 candidate ID list",
            actual=complete_family,
        )
        complete_family = []
    elif len(complete_family) != len(set(complete_family)):
        result.error(
            "candidate-family-mismatch",
            "complete candidate family 含有重複的 candidate ID",
            path=_identity_path(context, paths.get("preregistration.yml")),
            expected="unique candidate IDs",
            actual=complete_family,
        )

    selected = _get_path(preregistration, "selection_rule.selected_candidate_id", MISSING)
    if selected is MISSING:
        result.error(
            "candidate-identity-missing",
            "preregistration 缺少 selected candidate identity",
            path=_identity_path(context, paths.get("preregistration.yml")),
            expected="selection_rule.selected_candidate_id",
            actual=None,
        )
    elif selected not in complete_family:
        result.error(
            "candidate-family-mismatch",
            "selected candidate 不在 preregistered candidate family",
            path=_identity_path(context, paths.get("preregistration.yml")),
            expected=complete_family,
            actual=selected,
        )

    expected_candidate = selected if isinstance(selected, str) else MISSING
    candidate_id_documents = (
        ("candidate-definition.yml", candidate, {"candidate_id", "selected_candidate_id"}),
        ("preregistration.yml", preregistration, {"candidate_id"}),
        ("qualification-spec.yml", qualification, {"candidate_id", "selected_candidate_id"}),
        (
            "development-trial-inputs.yml",
            trial_inputs,
            {"candidate_id", "selected_candidate_id"},
        ),
    )
    for name, document, keys in candidate_id_documents:
        assert isinstance(document, dict)
        document_path = _identity_path(context, paths.get(name))
        for key_path, actual in _collect_keyed_values(document, keys):
            if expected_candidate is not MISSING and actual != expected_candidate:
                code = (
                    "trial-identity-mismatch"
                    if name == "development-trial-inputs.yml"
                    else "candidate-identity-mismatch"
                )
                result.error(
                    code,
                    f"{name} 的 {'.'.join(key_path)} 與 selected candidate 不一致",
                    path=document_path,
                    expected=expected_candidate,
                    actual=actual,
                )

    trial_id_values: list[tuple[str, tuple[str, ...], str]] = []
    for name, document in identity_documents:
        assert isinstance(document, dict)
        document_path = _identity_path(context, paths.get(name))
        for key_path, actual in _collect_keyed_values(document, {"trial_id"}):
            if not isinstance(actual, str) or not actual:
                result.error(
                    "invalid-trial-identity",
                    f"{name} 的 {'.'.join(key_path)} 必須是非空 trial ID",
                    path=document_path,
                    expected="non-empty trial ID",
                    actual=actual,
                )
                continue
            trial_id_values.append((name, key_path, actual))
    if trial_id_values:
        expected_trial_id = trial_id_values[0][2]
        for name, key_path, actual in trial_id_values[1:]:
            if actual != expected_trial_id:
                result.error(
                    "trial-identity-mismatch",
                    f"{name} 的 {'.'.join(key_path)} 與其他文件的 trial identity 不一致",
                    path=_identity_path(context, paths.get(name)),
                    expected=expected_trial_id,
                    actual=actual,
                )

    trial_candidate = trial_inputs.get("candidate_id", MISSING)
    if trial_candidate is MISSING:
        result.error(
            "missing-trial-identity",
            "development-trial-inputs 缺少 candidate_id，無法辨識 Trial",
            path=_identity_path(context, paths.get("development-trial-inputs.yml")),
            expected=expected_candidate if expected_candidate is not MISSING else "candidate ID",
            actual=None,
        )
    elif trial_candidate not in complete_family:
        result.error(
            "trial-identity-mismatch",
            "development Trial 的 candidate_id 不在 preregistered candidate family",
            path=_identity_path(context, paths.get("development-trial-inputs.yml")),
            expected=complete_family,
            actual=trial_candidate,
        )

    prereg_families = _collect_keyed_values(preregistration, {"candidate_family"})
    expected_family = prereg_families[0][1] if prereg_families else MISSING
    family_documents = (
        ("candidate-definition.yml", candidate),
        ("qualification-spec.yml", qualification),
        ("development-trial-inputs.yml", trial_inputs),
    )
    if expected_family is not MISSING:
        for name, document in family_documents:
            assert isinstance(document, dict)
            document_path = _identity_path(context, paths.get(name))
            for key_path, actual in _collect_keyed_values(document, {"candidate_family"}):
                if actual != expected_family:
                    result.error(
                        "candidate-family-mismatch",
                        f"{name} 的 {'.'.join(key_path)} 與 preregistration family 不一致",
                        path=document_path,
                        expected=expected_family,
                        actual=actual,
                    )

    for name, document in (
        ("candidate-definition.yml", candidate),
        ("qualification-spec.yml", qualification),
    ):
        assert isinstance(document, dict)
        document_path = _identity_path(context, paths.get(name))
        for key_path, actual in _collect_keyed_values(document, {"complete_candidate_family"}):
            if actual != complete_family:
                result.error(
                    "candidate-family-mismatch",
                    f"{name} 的 {'.'.join(key_path)} 與 preregistered family 不一致",
                    path=document_path,
                    expected=complete_family,
                    actual=actual,
                )


def _check_precreate_research_paths(context: StudyContext, result: CheckResult) -> None:
    """掃描 research bundle 文字，避免 copy-forward 留下另一個 Study 路徑。"""

    for path in _walk_files(
        context.research_root,
        (".yml", ".yaml", ".py", ".md", ".json", ".toml", ".txt"),
    ):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in RESEARCH_PATH_PATTERN.finditer(text):
            other = match.group("name")
            if other != context.study_id and other not in SHARED_RESEARCH_ROOTS:
                result.error(
                    "stale-research-path",
                    f"research bundle 仍指向另一個 Study：research/{other}",
                    path=_display_path(context, path),
                    expected=f"research/{context.study_id}",
                    actual=f"research/{other}",
                )


def _check_precreate_manifest_copies(
    context: StudyContext,
    result: CheckResult,
    already_loaded: set[str],
) -> None:
    """核對 research 內所有已有同名 manifest 的 canonical YAML 副本。"""

    for path in _walk_files(context.research_root, (".yml", ".yaml")):
        name = path.relative_to(context.research_root).as_posix()
        if name in already_loaded:
            continue
        _load_research_document(context, result, name, required=False)


def _research_procedure_path(
    context: StudyContext,
    result: CheckResult,
    trial_inputs: dict[str, Any],
    contract: dict[str, Any] | None,
    entries: dict[str, str],
) -> str | None:
    declared_values = (
        _get_path(trial_inputs, "study_procedure_path", MISSING),
        _get_path(trial_inputs, "procedure_path", MISSING),
        _get_path(trial_inputs, "development_runner_path", MISSING),
        _get_path(contract, "procedure.path", MISSING) if isinstance(contract, dict) else MISSING,
    )
    for declared in declared_values:
        if declared is MISSING:
            continue
        if not isinstance(declared, str) or not declared:
            result.error(
                "invalid-procedure-path",
                "Development procedure path 必須是非空 repository-relative 字串",
                path=_display_path(context, context.research_root / "development-trial-inputs.yml"),
                expected="repository-relative path",
                actual=declared,
            )
            return None
        return Path(declared).as_posix()

    conventional = f"research/{context.study_id}/run_development.py"
    if conventional in entries:
        return conventional
    candidates = sorted(
        path
        for path in entries
        if path.startswith(f"research/{context.study_id}/")
        and Path(path).name == "run_development.py"
    )
    if len(candidates) == 1:
        return candidates[0]
    result.error(
        "procedure-not-in-source-bundle",
        "Source Bundle 無法唯一找出 Development procedure",
        path=_display_path(context, context.research_root / "source-bundle.yml"),
        expected=conventional,
        actual=candidates,
    )
    return None


def _check_precreate_trial_bindings(
    context: StudyContext,
    result: CheckResult,
    trial_inputs: dict[str, Any] | None,
    trial_path: Path | None,
    preregistration: dict[str, Any] | None,
    preregistration_path: Path | None,
    source_bundle: dict[str, Any] | None,
    source_bundle_path: Path | None,
    contract: dict[str, Any] | None,
) -> None:
    if not all(
        isinstance(value, dict)
        for value in (trial_inputs, preregistration, source_bundle)
    ):
        return
    assert trial_path is not None
    assert preregistration_path is not None
    assert source_bundle_path is not None

    trial_error_path = _display_path(context, trial_path)
    expected_preregistration = canonical_digest(preregistration_path.read_bytes())
    expected_source_bundle = canonical_digest(source_bundle_path.read_bytes())

    bindings = (
        (
            "preregistration_digest",
            "trial-preregistration-binding-mismatch",
            "Development trial inputs 的 preregistration digest 不一致",
            expected_preregistration,
        ),
        (
            "source_bundle_digest",
            "trial-source-bundle-binding-mismatch",
            "Development trial inputs 的 Source Bundle digest 不一致",
            expected_source_bundle,
        ),
    )
    for field_name, code, message, expected in bindings:
        actual = trial_inputs.get(field_name, MISSING)
        if actual != expected:
            result.error(
                code,
                message,
                path=trial_error_path,
                expected=expected,
                actual=None if actual is MISSING else actual,
            )

    entries = _source_bundle_entries(source_bundle)
    engine_path = _engine_path(context, source_bundle, contract, result) if contract else None
    if engine_path is not None:
        engine_relative = engine_path.relative_to(context.repository_root).as_posix()
        expected_engine = entries.get(engine_relative, MISSING)
        actual_engine = trial_inputs.get("strategy_engine_digest", MISSING)
        if expected_engine is MISSING:
            result.error(
                "engine-not-in-source-bundle",
                f"策略引擎不在 Source Bundle：{engine_relative}",
                path=trial_error_path,
                expected=engine_relative,
                actual=sorted(entries),
            )
        elif actual_engine != expected_engine:
            result.error(
                "trial-strategy-engine-binding-mismatch",
                "Development trial inputs 的 strategy engine digest 不一致",
                path=trial_error_path,
                expected=expected_engine,
                actual=None if actual_engine is MISSING else actual_engine,
            )

    procedure_relative = _research_procedure_path(
        context,
        result,
        trial_inputs,
        contract,
        entries,
    )
    if procedure_relative is not None:
        expected_procedure = entries.get(procedure_relative, MISSING)
        actual_procedure = trial_inputs.get("study_procedure_digest", MISSING)
        if expected_procedure is MISSING:
            result.error(
                "procedure-not-in-source-bundle",
                f"Development procedure 不在 Source Bundle：{procedure_relative}",
                path=trial_error_path,
                expected=procedure_relative,
                actual=sorted(entries),
            )
        elif actual_procedure != expected_procedure:
            result.error(
                "trial-procedure-binding-mismatch",
                "Development trial inputs 的 study procedure digest 不一致",
                path=trial_error_path,
                expected=expected_procedure,
                actual=None if actual_procedure is MISSING else actual_procedure,
            )

    result.details["development_trial_inputs_path"] = context.display_path(trial_path)
    result.details["development_trial_bindings"] = {
        "preregistration_digest": expected_preregistration,
        "source_bundle_digest": expected_source_bundle,
        "strategy_engine_path": (
            engine_path.relative_to(context.repository_root).as_posix()
            if engine_path is not None
            else None
        ),
        "procedure_path": procedure_relative,
    }


def _find_research_contract(
    context: StudyContext,
    result: CheckResult,
    candidate: dict[str, Any] | None,
    preregistration: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, Path | None, str | None]:
    """找 contract 時只接受 research bundle 或文件內嵌設定。"""

    external, external_path = _load_research_document(
        context,
        result,
        "implementation-contract.yml",
        required=False,
    )
    if external_path is not None:
        if isinstance(external, dict):
            return external, external_path, "external"
        result.error(
            "invalid-implementation-contract",
            "implementation contract 必須是 mapping",
            path=_display_path(context, external_path),
            expected="mapping",
            actual=type(external).__name__ if external is not None else None,
        )
        return None, external_path, "external"

    for label, document in (
        ("candidate-definition", candidate),
        ("preregistration", preregistration),
    ):
        if not isinstance(document, dict):
            continue
        if isinstance(document.get("implementation_contract"), dict):
            return document["implementation_contract"], None, label
        if isinstance(document.get("indicator_contract"), dict):
            return {"indicator_contract": document["indicator_contract"]}, None, label
        eligibility = document.get("eligibility_rules")
        if isinstance(eligibility, dict) and isinstance(eligibility.get("indicator_contract"), dict):
            return {"indicator_contract": eligibility["indicator_contract"]}, None, label
    return None, None, None


def run_precreate(context: StudyContext) -> CheckResult:
    """在第一個 study-created Event 前，只以 research bundle 檢查跨文件 binding。"""

    result = CheckResult("precreate")
    if STUDY_ID_PATTERN.fullmatch(context.study_id) is None:
        result.error(
            "invalid-study-id",
            "Study ID 必須是 3--63 個小寫英數字與連字號，且不能以連字號開頭",
            path=_display_path(context, context.research_root),
            expected="safe Study ID",
            actual=context.study_id,
        )
        return result
    event_dir = context.study_root / "events"
    existing_events = sorted(event_dir.glob("*.yml")) if event_dir.is_dir() else []
    if existing_events:
        result.error(
            "precreate-after-study-created",
            "Study 已經存在 Event；precreate 只能在第一個 study-created Event 前執行",
            path=_display_path(context, existing_events[0]),
            expected="no Study Event",
            actual=[path.name for path in existing_events],
        )
        result.details.update(
            {
                "research_root": context.display_path(context.research_root),
                "study_event_required": False,
                "existing_event_count": len(existing_events),
            }
        )
        return result
    if not context.research_root.is_dir():
        result.error(
            "missing-research-bundle",
            f"找不到同名 research 目錄：{context.research_root}",
            path=_display_path(context, context.research_root),
            expected="directory",
            actual="missing",
        )

    documents: dict[str, dict[str, Any] | None] = {}
    paths: dict[str, Path | None] = {}
    for name in PRECREATE_REQUIRED_DOCUMENTS:
        documents[name], paths[name] = _load_research_document(context, result, name)
    contract, contract_path, contract_source = _find_research_contract(
        context,
        result,
        documents.get("candidate-definition.yml"),
        documents.get("preregistration.yml"),
    )
    if contract is None:
        result.error(
            "implementation-contract-missing",
            "沒有明確的 implementation contract，無法綁定 strategy engine",
            path=_display_path(context, context.research_root / "implementation-contract.yml"),
            expected="external implementation-contract.yml 或文件內嵌 contract",
            actual=None,
        )
    result.details.update(
        {
            "research_root": context.display_path(context.research_root),
            "study_event_required": False,
            "required_documents": list(PRECREATE_REQUIRED_DOCUMENTS),
            "contract_source": (
                context.display_path(contract_path) if contract_path else contract_source
            ),
        }
    )

    _check_precreate_research_paths(context, result)
    _check_precreate_manifest_copies(
        context,
        result,
        set(PRECREATE_REQUIRED_DOCUMENTS) | {"implementation-contract.yml"},
    )
    preregistration = documents.get("preregistration.yml")
    qualification = documents.get("qualification-spec.yml")
    source_bundle = documents.get("source-bundle.yml")
    preregistration_path = paths.get("preregistration.yml")
    qualification_path = paths.get("qualification-spec.yml")
    source_bundle_path = paths.get("source-bundle.yml")
    if isinstance(preregistration, dict) and isinstance(qualification, dict):
        if preregistration_path is not None:
            expected_digest = canonical_digest(preregistration_path.read_bytes())
            actual_digest = qualification.get("preregistration_digest", MISSING)
            if actual_digest != expected_digest:
                result.error(
                    "stale-preregistration-binding",
                    "qualification-spec.yml 的 preregistration digest 與目前 preregistration 不一致",
                    path=_display_path(context, qualification_path or context.research_root / "qualification-spec.yml"),
                    expected=expected_digest,
                    actual=None if actual_digest is MISSING else actual_digest,
                )
        _check_gate_maps(
            result,
            preregistration,
            qualification,
            path=_display_path(context, qualification_path or context.research_root / "qualification-spec.yml"),
            exact=True,
        )

    if isinstance(source_bundle, dict):
        _check_source_bundle(
            context,
            result,
            source_bundle,
            _display_path(context, source_bundle_path or context.research_root / "source-bundle.yml"),
        )
    _check_precreate_identities(context, result, documents, paths)
    _check_precreate_trial_bindings(
        context,
        result,
        documents.get("development-trial-inputs.yml"),
        paths.get("development-trial-inputs.yml"),
        preregistration,
        preregistration_path,
        source_bundle,
        source_bundle_path,
        contract,
    )
    return result


def _check_canonical_study_tree(context: StudyContext, result: CheckResult) -> None:
    checked = 0
    for path in _walk_files(context.study_root, (".yml",)):
        checked += 1
        try:
            load_canonical(path)
        except Exception as exc:
            result.error("non-canonical-study-yaml", f"Study YAML 不是可驗證的 canonical YAML：{exc}", path=path)
    result.details["canonical_yaml_file_count"] = checked


def _state_for_freeze(projection: Any) -> str:
    events = [record.value["event_type"] for record in projection.events]
    if "candidate-frozen" in events:
        return "frozen" if events[-1] == "candidate-frozen" else "past-freeze"
    if projection.terminal_outcome is not None:
        return "terminal-without-candidate"
    return "ready-to-freeze"


def run_freeze(context: StudyContext, authority_root: Path | None = None) -> CheckResult:
    """檢查正式 writer 進入 candidate freeze 前的 artifact 與 state readiness。"""

    result = CheckResult("freeze")
    source_bundle, source_bundle_path = _load_document(context, result, "source-bundle.yml")
    preregistration, _ = _load_document(context, result, "preregistration.yml")
    qualification, _ = _load_document(context, result, "qualification-spec.yml")
    _check_source_bundle(context, result, source_bundle, source_bundle_path)
    _check_canonical_study_tree(context, result)
    if isinstance(preregistration, dict) and isinstance(qualification, dict):
        _check_gate_maps(result, preregistration, qualification)
        _check_validator_gate_support(result, preregistration, qualification)

    research_source_path = context.research_root / "source-bundle.yml"
    if source_bundle_path is not None and research_source_path.is_file():
        try:
            research_source = load_canonical(research_source_path)
            if research_source != source_bundle:
                result.error(
                    "source-bundle-copy-drift",
                    "Study manifest 與 research/source-bundle.yml 不一致",
                    path=research_source_path,
                )
        except Exception as exc:
            result.error("invalid-source-bundle", f"無法讀取 research Source Bundle：{exc}", path=research_source_path)
    elif not research_source_path.is_file():
        result.warning("missing-research-source-bundle", "找不到 research/source-bundle.yml", path=research_source_path)

    try:
        validate_release_record(context.workflow_root)
        rules = WorkflowRules(context.workflow_root)
        projection = validate_study(context.study_root, rules)
    except (OSError, WorkflowError, ValueError, KeyError) as exc:
        result.error("workflow-validation-failed", f"Workflow validator 拒絕此 Study：{exc}")
        return result

    state = _state_for_freeze(projection)
    result.details.update(
        {
            "workflow_validation": "passed",
            "workflow_release": "passed",
            "event_count": len(projection.events),
            "current_event": projection.effective_event_type,
            "state": state,
        }
    )
    if state == "past-freeze":
        result.error("past-candidate-freeze", "Study 已經進入 candidate freeze 後的正式評估或終止階段，不能再當作 freeze 前檢查")
    elif state == "terminal-without-candidate":
        result.details["candidate_freeze_required"] = False
        result.warning(
            "candidate-freeze-not-applicable",
            "Study 已依失敗或不可判定規則合法 terminal，且沒有 candidate；不把缺少 provenance/selection evidence 當成缺陷",
        )
    else:
        result.details["candidate_freeze_required"] = True

    if authority_root is None:
        result.warning("authority-not-checked", "沒有提供 --authority-root；本次未核對本機 authority checkpoints")
    else:
        try:
            AuthorityStore(authority_root).verify(context.study_id, projection.events)
        except (OSError, WorkflowError, ValueError, KeyError) as exc:
            result.error("authority-validation-failed", f"Authority checkpoint 驗證失敗：{exc}")
        else:
            result.details["authority_validation"] = "passed"
    return result


def _run_command(
    command: str,
    context: StudyContext,
    authority_root: Path | None,
) -> dict[str, Any]:
    if command == "precreate":
        checks = [run_precreate(context)]
    elif command == "identity":
        checks = [run_identity(context)]
    elif command == "contract":
        checks = [run_contract(context)]
    elif command == "synthetic":
        checks = [run_synthetic(context)]
    elif command == "freeze":
        checks = [run_freeze(context, authority_root)]
    elif command == "all":
        checks = [
            run_identity(context),
            run_contract(context),
            run_synthetic(context),
            run_freeze(context, authority_root),
        ]
    else:  # argparse 已經擋住；保留防禦性錯誤讓 library call 也安全。
        raise ValueError(f"未知命令：{command}")

    serialized = [check.as_dict(context) for check in checks]
    errors = [finding for check in serialized for finding in check["errors"]]
    warnings = [finding for check in serialized for finding in check["warnings"]]
    return {
        "command": command,
        "study_id": context.study_id,
        "status": "failed" if errors else "passed",
        "checks": serialized,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Study preflight 與 candidate freeze readiness checks")
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--authority-root", type=Path, default=None)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("precreate", "identity", "contract", "synthetic", "freeze", "all"):
        subparser = commands.add_parser(name)
        subparser.add_argument("study_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except CliArgumentError as exc:
        output = {
            "command": None,
            "study_id": None,
            "status": "error",
            "error_count": 1,
            "warning_count": 0,
            "errors": [
                _finding(
                    "cli-error",
                    str(exc),
                    expected="valid studyctl command and arguments",
                    actual=None,
                )
            ],
        }
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
        return 2
    context = context_for(args.repository_root, args.study_id)
    try:
        output = _run_command(args.command, context, args.authority_root)
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
        return 1 if output["status"] == "failed" else 0
    except (OSError, WorkflowError, ValueError, KeyError) as exc:
        output = {
            "command": args.command,
            "study_id": args.study_id,
            "status": "error",
            "error_count": 1,
            "warning_count": 0,
            "errors": [_finding("cli-error", str(exc))],
        }
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
