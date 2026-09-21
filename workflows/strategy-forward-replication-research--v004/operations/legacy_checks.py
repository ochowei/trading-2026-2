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
    python research/tools/studyctl.py --repository-root . diagnose <study-id>
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

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_NAME = "strategy-forward-replication-research--v004"
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


class SyntheticFixtureInvalid(SyntheticFailure):
    """工具夾具無法依 frozen contract 建立可判讀的候選情境。"""

    def __init__(self, message: str, *, classification: str = "fixture-invalid") -> None:
        super().__init__(message)
        self.classification = classification


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
    value["path"] = None if path is None else str(path)
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


def _iter_keyed_strings(
    value: Any, keys: tuple[str, ...] = ()
) -> Iterable[tuple[tuple[str, ...], str]]:
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
        if any(
            part in {".super-admin", ".project-manager", "historical-evaluation-artifacts"}
            for part in path.parts
        ):
            continue
        if path.is_file() and path.suffix in suffixes:
            yield path


def _study_event_files(event_root: Path) -> list[Path]:
    """列出 Study events 目錄內的所有檔案，避免漏掉非 .yml 或隱藏檔。"""

    if not event_root.is_dir():
        return []
    return sorted(path for path in event_root.iterdir() if path.is_file() or path.is_symlink())


def _is_forbidden_read_path(path: Path) -> bool:
    """角色治理邊界：studyctl 不讀正式 Evaluation store 或超級管理者資料。"""

    return any(
        part in {".super-admin", ".project-manager", "historical-evaluation-artifacts"}
        for part in path.parts
    )


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
            result.error(
                "missing-artifact",
                f"找不到必要檔案：{name}",
                path=context.display_path(context.research_root / name),
                expected="file",
                actual="missing",
            )
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
                expected="repository-canonical YAML mapping",
                actual=str(exc),
            )
            continue
        if not isinstance(value, dict):
            result.error(
                "invalid-artifact-shape",
                "artifact 最上層必須是 mapping",
                path=path,
                expected="mapping",
                actual=type(value).__name__,
            )
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
                expected=primary,
                actual=value,
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
        result.error(
            "missing-research-bundle", f"找不到同名 research 目錄：{context.research_root}"
        )

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
        if isinstance(eligibility, dict) and isinstance(
            eligibility.get("indicator_contract"), dict
        ):
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
        if (
            isinstance(item, dict)
            and isinstance(item.get("path"), str)
            and isinstance(item.get("digest"), str)
        ):
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
    candidate_direction = _get_path(candidate_signal, "price_direction_confirmation", {})
    registered_direction = _get_path(signal, "price_direction_confirmation", {})
    candidate_supplemental = _get_path(candidate_signal, "supplemental_path", {})
    registered_supplemental = _get_path(signal, "supplemental_path", {})
    candidate_execution = _get_path(candidate, "execution", {})
    registered_execution = _get_path(preregistration, "eligibility_rules.execution", {})
    return {
        "sma_lookback": _get_path(candidate_mean, "sma_length"),
        "rsi_lookback": _get_path(candidate_mean, "rsi_length"),
        "rsi_max": _get_path(candidate_mean, "rsi_maximum"),
        "mean_reversion_gap": _get_path(candidate_mean, "close_vs_sma20_gap_minimum"),
        "volume_lookback": _get_path(candidate_volume, "volume_average_length"),
        "volume_lead_window": _get_path(candidate_volume, "prior_session_window"),
        "volume_spike_ratio": _get_path(candidate_volume, "volume_ratio_minimum"),
        "volume_lead_enabled": _get_path(candidate_volume, "enabled"),
        "cooldown_sessions": _get_path(candidate_cooldown, "completed_session_steps_after_exit"),
        "decision_time": _get_path(candidate_signal, "decision_time"),
        "target_return": _get_path(candidate, "execution.target.level_from_raw_entry_open"),
        "stop_return": _get_path(candidate, "execution.stop.level_from_raw_entry_open"),
        "holding_sessions": _get_path(candidate, "execution.held_complete_sessions"),
        "holding_span": _get_path(
            candidate, "execution.maximum_holding_session_span_for_validator"
        ),
        "entry": _get_path(candidate_execution, "entry"),
        "gap_fill": _get_path(candidate_execution, "gap_fill"),
        "intrabar_ambiguity": _get_path(candidate_execution, "intrabar_ambiguity"),
        "fold_warmup_sessions": _get_path(candidate, "fold_policy.evaluation_fold_warmup_sessions"),
        "risk_fraction": _get_path(
            candidate, "execution.position_sizing.risk_fraction_of_pre_entry_equity"
        ),
        "price_direction_above": _get_path(candidate_direction, "close_above_prior_close"),
        "price_direction_below": _get_path(candidate_direction, "close_below_prior_close"),
        "supplemental_enabled": _get_path(candidate_supplemental, "enabled"),
        "supplemental_atr_lookback": _get_path(candidate_supplemental, "atr_lookback"),
        "supplemental_atr_distance_multiplier": _get_path(
            candidate_supplemental, "atr_distance_multiplier"
        ),
        "supplemental_bollinger_lookback": _get_path(candidate_supplemental, "bollinger_lookback"),
        "supplemental_pullback_low_lookback": _get_path(
            candidate_supplemental, "pullback_low_lookback"
        ),
        "registered_sma_lookback": _get_path(registered_mean, "sma_length"),
        "registered_rsi_lookback": _get_path(registered_mean, "rsi_length"),
        "registered_rsi_max": _get_path(registered_mean, "rsi_value"),
        "registered_mean_reversion_gap": _get_path(registered_mean, "close_vs_sma20_gap_minimum"),
        "registered_volume_lookback": _get_path(registered_volume, "volume_average_length"),
        "registered_volume_lead_window": _get_path(registered_volume, "prior_session_window"),
        "registered_volume_spike_ratio": _get_path(registered_volume, "volume_ratio_value"),
        "registered_volume_lead_enabled": _get_path(registered_volume, "enabled"),
        "registered_cooldown_sessions": _get_path(
            registered_cooldown, "minimum_completed_session_steps_after_exit"
        ),
        "registered_decision_time": _get_path(signal, "decision_time"),
        "registered_price_direction_above": _get_path(
            registered_direction, "close_above_prior_close"
        ),
        "registered_price_direction_below": _get_path(
            registered_direction, "close_below_prior_close"
        ),
        "registered_supplemental_enabled": _get_path(registered_supplemental, "enabled"),
        "registered_supplemental_atr_lookback": _get_path(registered_supplemental, "atr_lookback"),
        "registered_supplemental_atr_distance_multiplier": _get_path(
            registered_supplemental, "atr_distance_multiplier"
        ),
        "registered_supplemental_bollinger_lookback": _get_path(
            registered_supplemental, "bollinger_lookback"
        ),
        "registered_supplemental_pullback_low_lookback": _get_path(
            registered_supplemental, "pullback_low_lookback"
        ),
        "registered_target_return": _get_path(
            preregistration, "eligibility_rules.execution.target.level_from_raw_entry_open"
        ),
        "registered_stop_return": _get_path(
            preregistration, "eligibility_rules.execution.stop.level_from_raw_entry_open"
        ),
        "registered_entry": _get_path(registered_execution, "entry"),
        "registered_gap_fill": _get_path(registered_execution, "gap_fill"),
        "registered_intrabar_ambiguity": _get_path(registered_execution, "intrabar_ambiguity"),
        "registered_holding_sessions": _get_path(
            preregistration, "maximum_holding_sessions", default=MISSING
        ),
        "registered_fold_warmup_sessions": preregistration.get("fold_warmup_sessions"),
        "registered_risk_fraction": _get_path(
            preregistration,
            "eligibility_rules.execution.position_sizing.risk_fraction_of_pre_entry_equity",
        ),
        "initial_cash": candidate.get("initial_cash", MISSING),
        "registered_initial_cash": preregistration.get("initial_cash", MISSING),
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

    rolling window 包含當日，所以 SMA、Bollinger、ATR 與回檔低點的零起始
    index 是 ``min_periods - 1``；RSI 先計算 price change，再對 change 做
    rolling，所以最早是 ``min_periods``；成交量平均量再往前取 lead window，
    最早是兩個 ready 邊界相加。不同策略不一定使用全部指標，因此遺漏的
    optional window 不會在這裡被硬湊成 RSI/SMA；真正需要的欄位會由 contract
    檢查回報。
    """

    boundaries: list[int] = []

    def add_boundary(value: Any, label: str, *, subtract_one: bool = False) -> None:
        if value is MISSING or value is None:
            return
        parsed = _int_value(value, label)
        boundaries.append(parsed - 1 if subtract_one else parsed)

    indicator = indicator if isinstance(indicator, dict) else {}
    sma_length = values.get("sma_lookback", MISSING)
    rsi_length = values.get("rsi_lookback", MISSING)
    volume_length = values.get("volume_lookback", MISSING)
    lead_window = values.get("volume_lead_window", MISSING)

    if sma_length is not MISSING:
        add_boundary(
            _get_path(indicator, "sma.min_periods", sma_length),
            "SMA min_periods",
            subtract_one=True,
        )
    if rsi_length is not MISSING:
        add_boundary(
            _get_path(indicator, "rsi.min_periods", rsi_length),
            "RSI min_periods",
        )
    if volume_length is not MISSING and lead_window is not MISSING:
        volume_min = _int_value(
            _get_path(indicator, "volume_lead.average_min_periods", volume_length),
            "Volume average min_periods",
        )
        lead_min = _int_value(
            _get_path(indicator, "volume_lead.lead_min_periods", lead_window),
            "Volume lead min_periods",
        )
        boundaries.append(volume_min + lead_min)

    # ATR-like candidates often keep these settings under supplemental_path while
    # simpler candidates use a top-level atr block.  Accept both spellings but
    # still require the implementation contract to declare the chosen one.
    supplemental = indicator.get("supplemental_path", {})
    if not isinstance(supplemental, dict):
        supplemental = {}
    atr_lookback = values.get("supplemental_atr_lookback", MISSING)
    atr_min_default = _get_path(supplemental, "atr_min_periods", atr_lookback)
    atr_min = _get_path(indicator, "atr.min_periods", atr_min_default)
    if atr_min is not MISSING and atr_min is not None:
        add_boundary(atr_min, "ATR min_periods", subtract_one=True)

    bollinger_lookback = values.get("supplemental_bollinger_lookback", MISSING)
    bollinger_min = _get_path(
        indicator,
        "bollinger.min_periods",
        _get_path(supplemental, "bollinger_min_periods", bollinger_lookback),
    )
    if bollinger_min is not MISSING and bollinger_min is not None:
        add_boundary(bollinger_min, "Bollinger min_periods", subtract_one=True)

    pullback_lookback = values.get("supplemental_pullback_low_lookback", MISSING)
    pullback_min = _get_path(
        indicator,
        "pullback_low.min_periods",
        _get_path(supplemental, "pullback_low_min_periods", pullback_lookback),
    )
    if pullback_min is not MISSING and pullback_min is not None:
        add_boundary(pullback_min, "pullback_low min_periods", subtract_one=True)

    return max(boundaries, default=0)


def _holding_period_conversion(
    result: CheckResult,
    values: dict[str, Any],
    *,
    candidate_path: Path | None,
    engine_holding: Any = MISSING,
) -> dict[str, Any]:
    """驗證三種持有期欄位，並把 signal-to-exit 轉換完整輸出。"""

    candidate_value = values.get("holding_sessions", MISSING)
    engine_value = engine_holding
    prereg_value = values.get("registered_holding_sessions", MISSING)
    conversion: dict[str, Any] = {
        "paths": {
            "execution.held_complete_sessions": "candidate-definition.yml",
            "engine.holding_sessions": "implementation contract engine spec",
            "preregistration.maximum_holding_sessions": "preregistration.yml",
        },
        "values": {
            "execution.held_complete_sessions": None
            if candidate_value is MISSING
            else candidate_value,
            "engine.holding_sessions": None if engine_value is MISSING else engine_value,
            "preregistration.maximum_holding_sessions": None
            if prereg_value is MISSING
            else prereg_value,
        },
        "relation": None,
        "status": "incomplete",
    }

    for label, value in (
        (
            "execution.held_complete_sessions",
            candidate_value,
        ),
        ("engine.holding_sessions", engine_value),
        (
            "preregistration.maximum_holding_sessions",
            prereg_value,
        ),
    ):
        if value is MISSING:
            result.error(
                "missing-contract-field",
                f"缺少必要持有期欄位：{label}",
                path=candidate_path,
                expected=label,
                actual=None,
            )

    if candidate_value is MISSING or prereg_value is MISSING:
        return conversion

    try:
        held = _int_value(candidate_value, "execution.held_complete_sessions")
        maximum = _int_value(prereg_value, "preregistration.maximum_holding_sessions")
    except ValueError as exc:
        result.error("invalid-execution-contract", str(exc), path=candidate_path)
        return conversion

    engine: int | None = None
    if engine_value is not MISSING:
        try:
            engine = _int_value(engine_value, "engine.holding_sessions")
        except ValueError as exc:
            result.error("invalid-engine-contract", str(exc), path=candidate_path)
            return conversion

    expected_span = held + 1
    relation = {
        "signal_to_entry_sessions": 1,
        "entry_to_exit_complete_sessions": held,
        "signal_to_exit_session_span": expected_span,
        "execution.held_complete_sessions": held,
        "engine.holding_sessions": engine,
        "preregistration.maximum_holding_sessions": maximum,
        "formula": {
            "engine.holding_sessions": "execution.held_complete_sessions",
            "signal_to_exit_session_span": "1 + execution.held_complete_sessions",
            "preregistration.maximum_holding_sessions": "signal_to_exit_session_span",
        },
    }
    conversion["relation"] = relation
    conversion["status"] = "complete"

    if engine is not None and engine != held:
        result.error(
            "holding-period-mismatch",
            "engine.holding_sessions 必須等於 execution.held_complete_sessions",
            path=candidate_path,
            expected=held,
            actual=engine,
        )
    if maximum != expected_span:
        result.error(
            "holding-period-mismatch",
            "preregistration.maximum_holding_sessions 必須等於 signal-to-exit span（held + 1）",
            path=candidate_path,
            expected=expected_span,
            actual=maximum,
        )

    declared_span = values.get("holding_span", MISSING)
    if declared_span is not MISSING:
        try:
            declared = _int_value(
                declared_span, "execution.maximum_holding_session_span_for_validator"
            )
        except ValueError as exc:
            result.error("invalid-execution-contract", str(exc), path=candidate_path)
        else:
            if declared != expected_span:
                result.error(
                    "holding-period-mismatch",
                    "candidate 宣告的 maximum holding span 與 signal-to-exit span 不一致",
                    path=candidate_path,
                    expected=expected_span,
                    actual=declared,
                )
    return conversion


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
        (
            "evaluation",
            preregistration.get("evaluation_gates", {}),
            qualification.get("evaluation", {}),
        ),
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


def _normalise_execution_value(label: str, value: Any) -> Any:
    """把文件中的白話描述轉成可比較的 execution 語意。"""

    if value is MISSING or value is None:
        return value
    text = str(value).casefold().replace("_", "-")
    if label == "gap_fill":
        has_stop = "stop" in text and "gap" in text
        has_target = "target" in text and "gap" in text
        if has_stop and has_target:
            return "stop-gap-at-open-target-gap-at-open"
    if label == "entry":
        if ("next" in text or "下一" in text) and "open" in text:
            return "next-session-open"
    if label == "intrabar_ambiguity":
        if "stop" in text and ("first" in text or "adverse" in text or "先" in text):
            return "adverse-stop-first"
    return value


def _record_binding(
    result: CheckResult,
    *,
    label: str,
    expected_path: str,
    actual_path: str,
    expected: Any,
    actual: Any,
    normalise: str | None = None,
    required: bool = False,
) -> None:
    """比較跨文件 outcome binding，同時保留雙方路徑供診斷。"""

    expected_value = _normalise_execution_value(normalise, expected) if normalise else expected
    actual_value = _normalise_execution_value(normalise, actual) if normalise else actual
    entry = {
        "label": label,
        "expected_path": expected_path,
        "actual_path": actual_path,
        "expected": None if expected_value is MISSING else expected_value,
        "actual": None if actual_value is MISSING else actual_value,
    }
    result.details.setdefault("outcome_relevant_parameters", []).append(entry)
    if not required and expected is MISSING and actual is MISSING:
        return
    if expected is MISSING or actual is MISSING:
        result.error(
            "missing-outcome-parameter",
            f"{label} 缺少候選或 preregistration 欄位",
            path=actual_path,
            expected=expected_value,
            actual=actual_value,
        )
    elif not _semantic_equal(expected_value, actual_value):
        result.error(
            "outcome-parameter-mismatch",
            f"{label} 不一致",
            path=actual_path,
            expected=expected_value,
            actual=actual_value,
        )


def _check_outcome_relevant_bindings(
    result: CheckResult,
    values: dict[str, Any],
    *,
    candidate_path: Path | None,
    preregistration_path: Path | None,
) -> None:
    """核對候選、預先登記與執行邊界中會改變結果的欄位。"""

    candidate_name = str(candidate_path or "candidate-definition.yml")
    prereg_name = str(preregistration_path or "preregistration.yml")
    pairs = (
        ("SMA length", "sma_lookback", "registered_sma_lookback", None, True),
        ("RSI length", "rsi_lookback", "registered_rsi_lookback", None, True),
        ("RSI threshold", "rsi_max", "registered_rsi_max", None, True),
        (
            "mean-reversion gap",
            "mean_reversion_gap",
            "registered_mean_reversion_gap",
            None,
            False,
        ),
        ("Volume average length", "volume_lookback", "registered_volume_lookback", None, True),
        ("Volume lead window", "volume_lead_window", "registered_volume_lead_window", None, True),
        ("Volume spike ratio", "volume_spike_ratio", "registered_volume_spike_ratio", None, True),
        ("Cooldown", "cooldown_sessions", "registered_cooldown_sessions", None, True),
        ("Signal decision time", "decision_time", "registered_decision_time", None, True),
        ("Target return", "target_return", "registered_target_return", None, True),
        ("Stop return", "stop_return", "registered_stop_return", None, True),
        ("Entry timing", "entry", "registered_entry", "entry", False),
        ("Gap fill", "gap_fill", "registered_gap_fill", "gap_fill", False),
        (
            "Intrabar ambiguity",
            "intrabar_ambiguity",
            "registered_intrabar_ambiguity",
            "intrabar_ambiguity",
            False,
        ),
        ("Fold warmup", "fold_warmup_sessions", "registered_fold_warmup_sessions", None, True),
        ("Risk fraction", "risk_fraction", "registered_risk_fraction", None, True),
        (
            "Close direction confirmation",
            "price_direction_above",
            "registered_price_direction_above",
            None,
            False,
        ),
        (
            "Close-below direction confirmation",
            "price_direction_below",
            "registered_price_direction_below",
            None,
            False,
        ),
        (
            "Supplemental path enabled",
            "supplemental_enabled",
            "registered_supplemental_enabled",
            None,
            False,
        ),
        (
            "ATR lookback",
            "supplemental_atr_lookback",
            "registered_supplemental_atr_lookback",
            None,
            False,
        ),
        (
            "ATR distance multiplier",
            "supplemental_atr_distance_multiplier",
            "registered_supplemental_atr_distance_multiplier",
            None,
            False,
        ),
        (
            "Bollinger lookback",
            "supplemental_bollinger_lookback",
            "registered_supplemental_bollinger_lookback",
            None,
            False,
        ),
        (
            "Pullback low lookback",
            "supplemental_pullback_low_lookback",
            "registered_supplemental_pullback_low_lookback",
            None,
            False,
        ),
    )
    for label, candidate_key, registered_key, normalise, required in pairs:
        _record_binding(
            result,
            label=label,
            expected_path=f"{prereg_name}:{registered_key}",
            actual_path=f"{candidate_name}:{candidate_key}",
            expected=values.get(registered_key, MISSING),
            actual=values.get(candidate_key, MISSING),
            normalise=normalise,
            required=required,
        )


def _check_contract_execution_bindings(
    result: CheckResult,
    values: dict[str, Any],
    contract: dict[str, Any] | None,
    *,
    contract_path: Path | None,
    candidate_path: Path | None,
) -> None:
    """把 implementation contract 的 execution 邊界綁回候選與 preregistration。"""

    if not isinstance(contract, dict):
        return
    exits = _get_path(contract, "execution.exits", {})
    cooldown = _get_path(contract, "execution.cooldown", {})
    if not isinstance(exits, dict):
        exits = {}
    if not isinstance(cooldown, dict):
        cooldown = {}
    contract_name = str(contract_path or "implementation-contract.yml")
    candidate_name = str(candidate_path or "candidate-definition.yml")
    decision = _get_path(contract, "execution.decision", {})
    if not isinstance(decision, dict):
        decision = {}
    for label, contract_value, candidate_value, normalise in (
        (
            "Contract cooldown",
            _get_path(cooldown, "minimum_completed_session_steps_after_exit"),
            values.get("cooldown_sessions", MISSING),
            None,
        ),
        (
            "Contract target",
            _get_path(exits, "target_return"),
            values.get("target_return", MISSING),
            None,
        ),
        (
            "Contract stop",
            _get_path(exits, "stop_return"),
            values.get("stop_return", MISSING),
            None,
        ),
        (
            "Contract entry",
            _get_path(decision, "entry"),
            values.get("entry", MISSING),
            "entry",
        ),
        (
            "Contract signal decision time",
            _get_path(decision, "signal"),
            values.get("decision_time", MISSING),
            None,
        ),
        (
            "Contract gap fill",
            _get_path(exits, "gap_fill"),
            values.get("gap_fill", MISSING),
            "gap_fill",
        ),
        (
            "Contract same-session ambiguity",
            _get_path(exits, "same_session_ambiguity"),
            values.get("intrabar_ambiguity", MISSING),
            "intrabar_ambiguity",
        ),
    ):
        if contract_value is MISSING and candidate_value is MISSING:
            continue
        _record_binding(
            result,
            label=label,
            expected_path=f"{contract_name}:{label}",
            actual_path=f"{candidate_name}:{label}",
            expected=contract_value,
            actual=candidate_value,
            normalise=normalise,
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
        (
            "development",
            set(_get_path(preregistration, "eligibility_rules.development_gates", {})),
            development,
        ),
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
        expected_digest = canonical_digest(prereg_path.read_bytes()) if prereg_path else None
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
    _check_outcome_relevant_bindings(
        result,
        values,
        candidate_path=candidate_path,
        preregistration_path=prereg_path,
    )

    contract, contract_path, contract_source = _find_contract(
        context, result, candidate, preregistration
    )
    result.details["contract_source"] = (
        context.display_path(contract_path) if contract_path else contract_source
    )
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
        result.error(
            "invalid-indicator-contract",
            f"無法計算指標就緒邊界：{exc}",
            path=contract_path or candidate_path,
        )

    if indicator is not None:
        contract_error_path = contract_path or candidate_path
        section_fields = {
            "sma": ("lookback", "min_periods", "not_ready"),
            "rsi": (
                "length",
                "formula",
                "min_periods",
                "not_ready",
                "zero_gain_and_loss",
                "zero_loss_only",
                "zero_gain_only",
            ),
            "volume_lead": (
                "volume_average_length",
                "prior_session_window",
                "uses_prior_sessions_only",
            ),
        }
        # ATR/bollinger/supplemental candidates may not use the legacy RSI or
        # volume-lead path.  A declared section is always strict; an absent
        # section is reported only when the candidate/preregistration declares
        # parameters that need it.
        needed_sections = {
            "sma": values["sma_lookback"] is not MISSING,
            "rsi": values["rsi_lookback"] is not MISSING,
            "volume_lead": (
                values["volume_lookback"] is not MISSING
                or values["volume_lead_window"] is not MISSING
            ),
        }
        for section, fields in section_fields.items():
            section_value = indicator.get(section, MISSING)
            if section_value is MISSING:
                if needed_sections[section]:
                    result.error(
                        "missing-indicator-section",
                        f"indicator contract 缺少 {section} 區塊",
                        path=contract_error_path,
                        expected=section,
                        actual=None,
                    )
                continue
            if not isinstance(section_value, dict):
                result.error(
                    "invalid-indicator-contract",
                    f"indicator contract 的 {section} 必須是 mapping",
                    path=contract_error_path,
                    expected="mapping",
                    actual=type(section_value).__name__,
                )
                continue
            for key in fields:
                if _get_path(section_value, key, MISSING) is MISSING:
                    result.error(
                        "missing-contract-field",
                        f"indicator contract 缺少 {section}.{key}",
                        path=contract_error_path,
                        expected=f"{section}.{key}",
                        actual=None,
                    )

        _check_equal(
            result,
            "contract.sma.lookback",
            _get_path(indicator, "sma.lookback"),
            values["sma_lookback"],
            path=contract_error_path,
        )
        _check_equal(
            result,
            "contract.rsi.length",
            _get_path(indicator, "rsi.length"),
            values["rsi_lookback"],
            path=contract_error_path,
        )
        _check_equal(
            result,
            "contract.volume_lead.volume_average_length",
            _get_path(indicator, "volume_lead.volume_average_length"),
            values["volume_lookback"],
            path=contract_error_path,
        )
        _check_equal(
            result,
            "contract.volume_lead.prior_session_window",
            _get_path(indicator, "volume_lead.prior_session_window"),
            values["volume_lead_window"],
            path=contract_error_path,
        )
        formula = _get_path(indicator, "rsi.formula", MISSING)
        if formula is not MISSING and formula not in {"simple-rolling-mean", "wilder"}:
            result.error(
                "unsupported-rsi-formula",
                f"CLI 尚未支援 RSI formula：{formula!r}",
                path=contract_error_path,
            )
        volume_prior_only = _get_path(indicator, "volume_lead.uses_prior_sessions_only", MISSING)
        if volume_prior_only is not MISSING and volume_prior_only is not True:
            result.error(
                "volume-lead-lookahead",
                "volume_lead.uses_prior_sessions_only 必須明確為 true",
                path=contract_error_path,
                expected=True,
                actual=volume_prior_only,
            )

        # ATR-like readiness is part of the same contract, not a special-case
        # warning.  Compare the declared lookback/min_periods when either the
        # candidate or the implementation contract exposes an ATR section.
        atr_section = indicator.get("atr", MISSING)
        supplemental_section = indicator.get("supplemental_path", MISSING)
        if atr_section is MISSING:
            atr_section = supplemental_section
        atr_needed = (
            values.get("supplemental_atr_lookback", MISSING) is not MISSING
            or atr_section is not MISSING
        )
        if atr_needed:
            if not isinstance(atr_section, dict):
                result.error(
                    "missing-indicator-section",
                    "ATR-like candidate 缺少 indicator contract 的 atr/supplemental_path mapping",
                    path=contract_error_path,
                    expected="atr or supplemental_path mapping",
                    actual=atr_section,
                )
            else:
                atr_lookback = _get_path(atr_section, "lookback", MISSING)
                if atr_lookback is MISSING:
                    atr_lookback = _get_path(atr_section, "atr_lookback", MISSING)
                atr_min = _get_path(atr_section, "min_periods", MISSING)
                if atr_min is MISSING:
                    atr_min = _get_path(atr_section, "atr_min_periods", MISSING)
                _check_equal(
                    result,
                    "contract.atr.lookback",
                    atr_lookback,
                    values.get("supplemental_atr_lookback", MISSING),
                    path=contract_error_path,
                )
                if atr_min is MISSING:
                    result.error(
                        "missing-contract-field",
                        "indicator contract 缺少 ATR min_periods",
                        path=contract_error_path,
                        expected="atr.min_periods or supplemental_path.atr_min_periods",
                        actual=None,
                    )

    _check_contract_execution_bindings(
        result,
        values,
        contract,
        contract_path=contract_path,
        candidate_path=candidate_path,
    )

    if isinstance(qualification, dict):
        _check_validator_gate_support(result, preregistration, qualification)

    engine_path = _engine_path(context, source_bundle, contract, result)
    if engine_path is not None:
        module = _load_engine(engine_path, result)
        if module is not None:
            engine = contract.get("engine", {}) if isinstance(contract, dict) else {}
            spec_name = (
                engine.get("spec_constant", "DEFAULT_SPEC")
                if isinstance(engine, dict)
                else "DEFAULT_SPEC"
            )
            strategy_spec = getattr(module, spec_name, MISSING)
            if strategy_spec is MISSING:
                result.error(
                    "missing-engine-spec",
                    f"策略引擎沒有 {spec_name}：{engine_path}",
                    path=engine_path,
                )
            else:
                engine_fields = (
                    ("sma_lookback", values.get("sma_lookback", MISSING)),
                    (
                        "sma_min_periods",
                        _get_path(indicator, "sma.min_periods", MISSING)
                        if isinstance(indicator, dict)
                        else MISSING,
                    ),
                    ("rsi_lookback", values.get("rsi_lookback", MISSING)),
                    (
                        "rsi_min_periods",
                        _get_path(indicator, "rsi.min_periods", MISSING)
                        if isinstance(indicator, dict)
                        else MISSING,
                    ),
                    ("rsi_max", values.get("rsi_max", MISSING)),
                    ("mean_reversion_min", values.get("mean_reversion_gap", MISSING)),
                    ("volume_lookback", values.get("volume_lookback", MISSING)),
                    (
                        "volume_average_min_periods",
                        _get_path(indicator, "volume_lead.average_min_periods", MISSING)
                        if isinstance(indicator, dict)
                        else MISSING,
                    ),
                    ("volume_lead_window", values.get("volume_lead_window", MISSING)),
                    (
                        "volume_lead_min_periods",
                        _get_path(indicator, "volume_lead.lead_min_periods", MISSING)
                        if isinstance(indicator, dict)
                        else MISSING,
                    ),
                    ("volume_spike_ratio", values.get("volume_spike_ratio", MISSING)),
                    ("volume_lead_enabled", values.get("volume_lead_enabled", MISSING)),
                    ("cooldown_sessions", values.get("cooldown_sessions", MISSING)),
                    ("holding_sessions", values.get("holding_sessions", MISSING)),
                    ("target_return", values.get("target_return", MISSING)),
                    ("stop_return", values.get("stop_return", MISSING)),
                    ("fold_warmup_sessions", values.get("fold_warmup_sessions", MISSING)),
                    ("risk_fraction", values.get("risk_fraction", MISSING)),
                    ("initial_cash", values.get("registered_initial_cash", MISSING)),
                    (
                        "require_close_above_prior_close",
                        values.get("price_direction_above", MISSING),
                    ),
                    (
                        "require_close_below_prior_close",
                        values.get("price_direction_below", MISSING),
                    ),
                    (
                        "supplemental_path_enabled",
                        values.get("supplemental_enabled", MISSING),
                    ),
                    ("atr_lookback", values.get("supplemental_atr_lookback", MISSING)),
                    (
                        "atr_distance_multiplier",
                        values.get("supplemental_atr_distance_multiplier", MISSING),
                    ),
                    (
                        "bollinger_lookback",
                        values.get("supplemental_bollinger_lookback", MISSING),
                    ),
                    (
                        "pullback_low_lookback",
                        values.get("supplemental_pullback_low_lookback", MISSING),
                    ),
                )
                for field_name, expected in engine_fields:
                    if expected is MISSING:
                        continue
                    actual = getattr(strategy_spec, field_name, MISSING)
                    if actual is MISSING:
                        result.error(
                            "missing-engine-outcome-parameter",
                            f"策略引擎沒有可核對的 outcome parameter：{field_name}",
                            path=engine_path,
                            expected=expected,
                            actual=None,
                        )
                    else:
                        _check_equal(
                            result,
                            f"engine.{field_name}",
                            actual,
                            expected,
                            path=engine_path,
                        )
                result.details["holding_period"] = _holding_period_conversion(
                    result,
                    values,
                    candidate_path=candidate_path,
                    engine_holding=getattr(strategy_spec, "holding_sessions", MISSING),
                )
                result.details["engine_spec_fields_checked"] = [
                    field_name for field_name, expected in engine_fields if expected is not MISSING
                ]
                cost_name = (
                    engine.get("cost_constant", "BASE_COST")
                    if isinstance(engine, dict)
                    else "BASE_COST"
                )
                cost_value = getattr(module, cost_name, MISSING)
                if cost_value is MISSING:
                    result.error(
                        "missing-engine-cost-constant",
                        f"策略引擎沒有 {cost_name}",
                        path=engine_path,
                        expected=cost_name,
                        actual=None,
                    )
                else:
                    for field_name, expected in (
                        (
                            "slippage_bps",
                            _get_path(candidate, "costs.base.slippage_per_side_bps", MISSING),
                        ),
                        (
                            "fee_bps",
                            _get_path(candidate, "costs.base.fee_per_side_bps", MISSING),
                        ),
                    ):
                        if expected is MISSING:
                            continue
                        actual = getattr(cost_value, field_name, MISSING)
                        if actual is MISSING:
                            result.error(
                                "missing-engine-cost-parameter",
                                f"成本常數缺少 {field_name}",
                                path=engine_path,
                                expected=expected,
                                actual=None,
                            )
                        else:
                            _check_equal(
                                result,
                                f"engine.{cost_name}.{field_name}",
                                actual,
                                expected,
                                path=engine_path,
                            )
            result.details["engine_spec_constant"] = spec_name

    if isinstance(source_bundle, dict):
        entries = _source_bundle_entries(source_bundle)
        if contract_source == "external" and contract_path is not None:
            try:
                relative_contract = (
                    contract_path.resolve().relative_to(context.repository_root).as_posix()
                )
            except ValueError:
                relative_contract = str(contract_path)
            if relative_contract not in entries:
                result.error(
                    "contract-not-frozen",
                    "implementation contract 沒有被 Source Bundle 綁定",
                    path=contract_path,
                    expected=relative_contract,
                    actual=sorted(entries),
                )
            elif contract_path.is_file():
                actual_digest = hashlib.sha256(contract_path.read_bytes()).hexdigest()
                if actual_digest != entries[relative_contract]:
                    result.error(
                        "contract-digest-mismatch",
                        "implementation contract 的 Source Bundle digest 不一致",
                        path=contract_path,
                        expected=entries[relative_contract],
                        actual=actual_digest,
                    )
        result.details["source_bundle_file_count"] = len(entries)
        result.details["source_bundle_path"] = (
            context.display_path(source_bundle_path) if source_bundle_path else None
        )
        _check_source_bundle(context, result, source_bundle, source_bundle_path)

    # 即使策略引擎無法載入，也要把三段欄位的缺漏先明確列出；這是
    # precreate 需要在 study-created 前攔截的 setup error。
    if "holding_period" not in result.details:
        result.details["holding_period"] = _holding_period_conversion(
            result,
            values,
            candidate_path=candidate_path,
            engine_holding=MISSING,
        )

    return result


def _make_bars(
    rows: int,
    signal_indices: Iterable[int] = (),
    *,
    close_direction: str | None = None,
    volume_lead_window: int = 5,
    vary_prices: bool = False,
) -> pd.DataFrame:
    """建立 deterministic seed bars；呼叫方仍必須以 engine 實際驗證訊號。

    ``signal_indices`` 只是候選情境的建構提示，不代表那些 index 必然是
    訊號。每個提示會建立「前一日急跌、當日反彈」的候選形狀，之後由
    ``indicators`` 回傳的 raw signal 決定是否真的成立。
    """

    if close_direction not in {None, "above", "below"}:
        raise SyntheticFailure(f"不支援的 synthetic 收盤方向：{close_direction!r}")
    signals = list(signal_indices)
    index = pd.date_range("2020-01-02", periods=rows, freq="B")
    if vary_prices:
        baseline = 100.0 + 0.25 * np.sin(np.arange(rows, dtype=float) / 3.0)
        close = baseline.copy()
        open_price = baseline.copy()
        high = baseline + 1.0
        low = baseline - 1.0
    else:
        close = np.full(rows, 100.0)
        open_price = np.full(rows, 100.0)
        high = np.full(rows, 101.0)
        low = np.full(rows, 99.0)
    volume = np.full(rows, 1_000_000.0)
    try:
        lead_window = max(1, int(volume_lead_window))
    except (TypeError, ValueError) as exc:
        raise SyntheticFailure("synthetic volume lead window 不是整數") from exc
    for signal_index in signals:
        if not 1 <= signal_index < rows:
            continue
        # 把前一日設成更低或更高的價格，確保 direction 是資料的結果，
        # 而不是 synthetic runner 對 index 的假設。
        if close_direction == "above":
            open_price[signal_index - 1] = 90.0
            close[signal_index - 1] = 90.0
            high[signal_index - 1] = 91.0
            low[signal_index - 1] = 89.5
            open_price[signal_index] = 95.0
            close[signal_index] = 95.0
        elif close_direction == "below":
            open_price[signal_index - 1] = 100.0
            close[signal_index - 1] = 100.0
            high[signal_index - 1] = 101.0
            low[signal_index - 1] = 99.0
            open_price[signal_index] = 90.0
            close[signal_index] = 90.0
        else:
            open_price[signal_index - 1] = 100.0
            close[signal_index - 1] = 100.0
            high[signal_index - 1] = 101.0
            low[signal_index - 1] = 99.0
            open_price[signal_index] = 90.0
            close[signal_index] = 90.0
        high[signal_index] = max(100.0, close[signal_index])
        low[signal_index] = min(99.0, close[signal_index] - 0.5)
        volume_index = signal_index - lead_window
        if volume_index >= 0:
            volume[volume_index] = 5_000_000.0
    return pd.DataFrame(
        {"Open": open_price, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=index,
    )


def _make_atr_like_bars(
    rows: int,
    *,
    event_index: int,
    variant: int = 0,
) -> pd.DataFrame:
    """建立符合 ATR-like 超跌／反彈機制的候選資料，而不是指定訊號 index。

    這個 fixture 的事件會由 engine 的 indicators/backtest 真正判定：先做出
    Bollinger/ATR 可就緒的回檔，再用成交量加權位置分數製造負轉正，最後以
    低量守低且收盤回升作為確認。若實作 contract 的條件不同，呼叫端會把
    情境標成 ``synthetic-fixture-invalid``，不會把交易數量錯誤偽裝成策略結果。
    """

    if not 20 <= event_index < rows - 3:
        raise SyntheticFixtureInvalid("ATR-like event index 沒有足夠的前後 session")
    index = pd.date_range("2020-01-02", periods=rows, freq="B")
    close = np.full(rows, 100.0)
    open_price = np.full(rows, 100.0)
    high = np.full(rows, 101.0)
    low = np.full(rows, 99.0)
    volume = np.full(rows, 1_000_000.0)

    # 下跌後反彈的輪廓：不同 variant 只改變幅度，讓 fixture 可以尋找
    # 真正成立的 raw signal，而不把一組硬編的 index 當答案。
    pattern = {
        -8: 97.0,
        -7: 95.0,
        -6: 93.0,
        -5: 92.0,
        -4: 92.5,
        -3: 92.0,
        -2: 91.5,
        -1: 91.0,
        0: 92.5,
        1: 93.5,
        2: 94.0,
    }
    for offset, value in pattern.items():
        position = event_index + offset
        if 0 <= position < rows:
            close[position] = value
            open_price[position] = value
            high[position] = value + 1.0
            low[position] = max(1.0, value - 1.0)

    # 事件前三日的 CLV*volume 為負，事件日以較高 close、窄幅與高量
    # 讓三日累積分數真正由非正轉正。下一日是低量守住 ref_low 的回測。
    for offset in (-3, -2, -1):
        position = event_index + offset
        if position >= 0:
            close[position] = min(close[position], 92.0 - 0.1 * variant)
            high[position] = close[position] + 2.0
            low[position] = close[position] - 0.1
            volume[position] = 1_000_000.0
    event = event_index
    close[event] = 92.5 - 0.1 * variant
    open_price[event] = close[event]
    high[event] = close[event] + 0.1
    low[event] = close[event] - 2.0
    volume[event] = 10_000_000.0
    retest = event_index + 1
    close[retest] = close[event] + 1.0
    open_price[retest] = close[retest]
    high[retest] = close[retest] + 0.5
    low[retest] = close[retest] - 0.5
    volume[retest] = 200_000.0

    return pd.DataFrame(
        {"Open": open_price, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=index,
    )


def _signal_columns(frame: pd.DataFrame, indicator: dict[str, Any]) -> list[str]:
    columns = _get_path(indicator, "columns.raw_signal", MISSING)
    declared: list[str] = []
    if isinstance(columns, str):
        declared = [columns]
    elif isinstance(columns, list) and all(isinstance(item, str) for item in columns):
        declared = list(columns)
    candidates = [
        name
        for name in frame.columns
        if name in {"raw_signal", "signal"}
        or name.endswith("_raw_signal")
        or name.endswith("_signal")
    ]
    ordered: list[str] = []
    for name in [*declared, *candidates]:
        if name in frame.columns and name not in ordered:
            values = frame[name].dropna()
            if values.empty or values.map(lambda value: isinstance(value, (bool, np.bool_))).all():
                ordered.append(name)
    return ordered


def _raw_signal_mask(
    frame: pd.DataFrame,
    indicator: dict[str, Any],
    spec: Any = None,
) -> tuple[list[str], pd.Series]:
    columns = _signal_columns(frame, indicator)
    mask = pd.Series(False, index=frame.index)
    for column in columns:
        values = frame[column].fillna(False)
        try:
            mask = mask | values.astype(bool)
        except (TypeError, ValueError) as exc:
            raise SyntheticFixtureInvalid(
                f"raw signal 欄位 {column} 不是可判讀的 boolean",
                classification="strategy-implementation",
            ) from exc

    supplemental_mask = _supplemental_raw_signal_mask(frame, spec)
    if supplemental_mask is not None:
        columns.append("supplemental_signal")
        mask = mask | supplemental_mask
    if not columns:
        raise SyntheticFixtureInvalid(
            "策略引擎沒有可供 synthetic audit 的 raw_signal/signal 欄位",
            classification="strategy-implementation",
        )
    return columns, mask


def _supplemental_raw_signal_mask(
    frame: pd.DataFrame,
    spec: Any,
) -> pd.Series | None:
    """依 implementation contract 還原補充路徑的 raw signal 狀態機。

    某些既有 engine 只把無狀態的 v009 raw signal 放進 ``indicators``，
    補充路徑則在 ``backtest`` 內維護 event state。Synthetic audit 仍需能
    觀察「候選條件成立、但尚未套用 position/cooldown」的 raw signal，因此
    在 fixture 端依 engine 已輸出的欄位重播同一段 contract state machine。
    若 engine 沒有這些欄位，回傳 None，讓 caller 將問題歸類為實作缺漏。
    """

    required_columns = {
        "volume_turnaround_event",
        "price_near_pullback_low",
        "Close",
        "Low",
        "Volume",
        "prior_volume_average",
        "sma_20",
        "recent_bollinger_oversold",
    }
    if spec is None or not required_columns.issubset(frame.columns):
        return None
    if getattr(spec, "supplemental_path_enabled", False) is not True:
        return None

    volume_lead_enabled = getattr(spec, "supplemental_volume_lead_enabled", False)
    observation_window = _int_value(
        getattr(spec, "observation_window_sessions", 0),
        "supplemental observation_window_sessions",
    )
    score_window = _int_value(
        getattr(spec, "volume_score_window", 0),
        "supplemental volume_score_window",
    )
    mask = pd.Series(False, index=frame.index)
    active_event: dict[str, Any] | None = None
    for index, (_, bar) in enumerate(frame.iterrows()):
        if volume_lead_enabled and bool(bar["volume_turnaround_event"]):
            if bool(bar["price_near_pullback_low"]):
                window_start = max(0, index - score_window + 1)
                active_event = {
                    "event_index": index,
                    "ref_low": float(frame["Low"].iloc[window_start : index + 1].min()),
                    "retest_seen": False,
                }
        if active_event is None:
            continue
        event_index = int(active_event["event_index"])
        reference_low = float(active_event["ref_low"])
        if index <= event_index or index > event_index + observation_window:
            if index > event_index + observation_window:
                active_event = None
            continue
        close = float(bar["Close"])
        if close < reference_low:
            active_event = None
            continue
        if float(bar["Volume"]) < float(bar["prior_volume_average"]):
            active_event["retest_seen"] = True
        price_confirm = (
            close > float(frame["Close"].iloc[index - 1])
            and close < float(bar["sma_20"])
            and bool(bar["recent_bollinger_oversold"])
        )
        if active_event["retest_seen"] and price_confirm:
            mask.iloc[index] = True
            active_event = None
    return mask


def _serialise_synthetic_value(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _serialise_trade(trade: Any) -> dict[str, Any]:
    fields = (
        "signal_session",
        "entry_session",
        "exit_session",
        "raw_entry_price",
        "raw_exit_price",
        "executed_entry_price",
        "executed_exit_price",
        "shares",
        "fees",
        "pnl",
        "exit_reason",
        "held_sessions",
        "signal_origin",
    )
    return {
        field_name: _serialise_synthetic_value(getattr(trade, field_name))
        for field_name in fields
        if hasattr(trade, field_name)
    }


def _rejection_reason(
    index: int,
    *,
    accepted_indexes: set[int],
    frame_length: int,
    holding: int,
    cooldown: int,
    first_ready: int,
) -> str:
    if index < first_ready:
        return "indicator-not-ready-or-fold-warmup"
    if index + holding + 1 >= frame_length:
        return "insufficient-tail-for-holding-span"
    if accepted_indexes:
        for accepted in sorted(accepted_indexes):
            exit_index = accepted + 1 + holding
            if accepted < index <= exit_index:
                return "position-open-or-pending-entry"
            if exit_index < index < exit_index + cooldown:
                return "cooldown-not-complete"
    return "engine-state-rejected"


def _signal_audit(
    frame: pd.DataFrame,
    raw_mask: pd.Series,
    backtest_result: Any,
    *,
    holding: int,
    cooldown: int,
    first_ready: int,
) -> dict[str, Any]:
    raw_indexes = [index for index, value in enumerate(raw_mask.tolist()) if bool(value)]
    raw_sessions = [frame.index[index].isoformat() for index in raw_indexes]
    accepted_sessions = [
        pd.Timestamp(session).isoformat()
        for session in getattr(backtest_result, "accepted_signal_sessions", ())
    ]
    accepted_set = set(accepted_sessions)
    rejected = [
        {
            "session": frame.index[index].isoformat(),
            "reason": _rejection_reason(
                index,
                accepted_indexes={
                    int(frame.index.get_loc(pd.Timestamp(session)))
                    for session in getattr(backtest_result, "accepted_signal_sessions", ())
                    if pd.Timestamp(session) in frame.index
                },
                frame_length=len(frame),
                holding=holding,
                cooldown=cooldown,
                first_ready=first_ready,
            ),
        }
        for index in raw_indexes
        if frame.index[index].isoformat() not in accepted_set
    ]
    return {
        "raw_signals": raw_sessions,
        "accepted_signals": accepted_sessions,
        "rejected_signals": rejected,
        "rejection_reasons": {item["session"]: item["reason"] for item in rejected},
        "trades": [_serialise_trade(trade) for trade in getattr(backtest_result, "trades", ())],
    }


def _assert_close(actual: Any, expected: Any, label: str) -> None:
    if pd.isna(expected):
        if not pd.isna(actual):
            raise SyntheticFailure(f"{label} 應為 not-ready NaN，實際是 {actual!r}")
        return
    if pd.isna(actual) or not np.isclose(float(actual), float(expected), rtol=1e-10, atol=1e-10):
        raise SyntheticFailure(f"{label} 不一致：實際 {actual!r}，預期 {expected!r}")


def _expected_simple_rsi(
    close: pd.Series, length: int, min_periods: int, contract: dict[str, Any]
) -> pd.Series:
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
    required_history = _int_value(
        indicator["required_history_sessions"], "required_history_sessions"
    )
    columns = _get_path(indicator, "columns", {})
    if not isinstance(columns, dict):
        columns = {}
    bars = _make_bars(
        required_history + 12,
        vary_prices=any(
            isinstance(columns.get(label), str) for label in ("bollinger", "atr", "pullback_low")
        ),
    )
    frame = _call_indicators(module, bars, spec)
    expected_columns: dict[str, str] = {}
    if values.get("sma_lookback", MISSING) is not MISSING:
        expected_columns["sma"] = columns.get(
            "sma", f"sma_{_int_value(values['sma_lookback'], 'SMA length')}"
        )
    if values.get("rsi_lookback", MISSING) is not MISSING:
        expected_columns["rsi"] = columns.get(
            "rsi", f"rsi_{_int_value(values['rsi_lookback'], 'RSI length')}"
        )
    if values.get("volume_lookback", MISSING) is not MISSING:
        expected_columns["volume_lead"] = columns.get("volume_lead", "prior_volume_spike_ratio")
    for label in (
        "atr",
        "bollinger",
        "pullback_low",
        "supplemental_signal",
    ):
        declared = columns.get(label)
        if isinstance(declared, str):
            expected_columns[label] = declared
    if not expected_columns:
        raise SyntheticFixtureInvalid(
            "indicator contract 沒有可驗證的 output columns",
            classification="strategy-implementation",
        )
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


def _run_signal_case(
    result: CheckResult,
    module: ModuleType,
    spec: Any,
    cost: Any,
    contract: dict[str, Any],
    indicator: dict[str, Any],
    values: dict[str, Any],
) -> None:
    """先以 indicators 找到真實 raw signal，再交給 backtest 做接受判定。"""

    required_history = _int_value(
        _get_path(indicator, "required_history_sessions", 0),
        "required_history_sessions",
    )
    direction = _synthetic_close_direction(contract, spec)
    atr_like = (
        values.get("supplemental_atr_lookback", MISSING) is not MISSING
        or "atr" in indicator
        or "supplemental_path" in indicator
    )
    attempts: list[dict[str, Any]] = []
    candidates: list[tuple[str, pd.DataFrame]] = []
    best_audit: dict[str, Any] | None = None
    result.details.setdefault("raw_signals", [])
    result.details.setdefault("accepted_signals", [])
    result.details.setdefault("rejected_signals", [])
    result.details.setdefault("rejection_reasons", {})
    result.details.setdefault("trades", [])
    result.details.setdefault("signal_audit", {})
    if atr_like:
        for variant in range(8):
            event_index = max(required_history + 8, 36 + variant * 3)
            rows = max(180, event_index + 50)
            try:
                candidates.append(
                    (
                        "atr-like",
                        _make_atr_like_bars(rows, event_index=event_index, variant=variant),
                    )
                )
            except SyntheticFixtureInvalid as exc:
                attempts.append({"kind": "atr-like", "variant": variant, "error": str(exc)})
    # 即使是 ATR-like candidate，也保留單純的 indicator signal case；這能
    # 把「ATR 狀態機沒有 raw_signal 輸出」與「一般 indicator 已能成立」分開。
    for variant in range(8):
        seed = max(required_history + 8, 36 + variant * 3)
        candidates.append(
            (
                "indicator",
                _make_bars(
                    max(180, seed + 50),
                    [seed],
                    close_direction=direction,
                    volume_lead_window=getattr(spec, "volume_lead_window", 5),
                ),
            )
        )

    implementation_failure: str | None = None
    implementation_classification: str | None = None
    raw_signal_observed = False
    accepted_signal_observed = False
    for kind, bars in candidates:
        try:
            frame = _call_indicators(module, bars, spec)
            signal_columns, raw_mask = _raw_signal_mask(frame, indicator, spec)
            raw_indexes = [
                index
                for index, value in enumerate(raw_mask.tolist())
                if bool(value) and index >= required_history
            ]
            backtest_result = _call_backtest(module, bars, spec, cost)
            accepted = getattr(backtest_result, "accepted_signal_sessions", ())
        except SyntheticFixtureInvalid as exc:
            implementation_failure = str(exc)
            implementation_classification = exc.classification
            attempts.append({"kind": kind, "error": str(exc), "classification": exc.classification})
            if exc.classification == "strategy-implementation":
                # 沒有可觀察 raw signal 時，換資料不能修好 implementation。
                break
            continue
        except (KeyError, TypeError, ValueError, AttributeError, SyntheticFailure) as exc:
            implementation_failure = str(exc)
            implementation_classification = "strategy-implementation"
            attempts.append(
                {"kind": kind, "error": str(exc), "classification": "strategy-implementation"}
            )
            continue

        raw_signal_observed = raw_signal_observed or bool(raw_indexes)
        accepted_signal_observed = accepted_signal_observed or bool(accepted)
        holding = _int_value(spec.holding_sessions, "engine holding_sessions")
        cooldown = _int_value(getattr(spec, "cooldown_sessions", 0), "engine cooldown_sessions")
        audit = _signal_audit(
            frame,
            raw_mask,
            backtest_result,
            holding=holding,
            cooldown=cooldown,
            first_ready=required_history,
        )
        result.details["signal_audit"][kind] = audit
        if best_audit is None or (
            len(audit["raw_signals"]),
            len(audit["accepted_signals"]),
            len(audit["trades"]),
        ) > (
            len(best_audit["raw_signals"]),
            len(best_audit["accepted_signals"]),
            len(best_audit["trades"]),
        ):
            best_audit = audit
        attempts.append(
            {
                "kind": kind,
                "raw_signal_columns": signal_columns,
                "raw_signal_count": len(raw_indexes),
                "accepted_signal_count": len(accepted),
            }
        )
        if raw_indexes and accepted:
            result.details["raw_signals"] = audit["raw_signals"]
            result.details["accepted_signals"] = audit["accepted_signals"]
            result.details["rejected_signals"] = audit["rejected_signals"]
            result.details["rejection_reasons"] = audit["rejection_reasons"]
            result.details["trades"] = audit["trades"]
            result.details["signal_case"] = {
                "kind": kind,
                "raw_signal_columns": signal_columns,
                "fixture_search_attempts": len(attempts),
            }
            return

    result.details["signal_case_attempts"] = attempts
    if best_audit is not None:
        result.details["raw_signals"] = best_audit["raw_signals"]
        result.details["accepted_signals"] = best_audit["accepted_signals"]
        result.details["rejected_signals"] = best_audit["rejected_signals"]
        result.details["rejection_reasons"] = best_audit["rejection_reasons"]
        result.details["trades"] = best_audit["trades"]
    if implementation_classification == "strategy-implementation":
        raise SyntheticFixtureInvalid(
            f"synthetic signal case 無法執行：{implementation_failure}",
            classification="strategy-implementation",
        )
    if raw_signal_observed and not accepted_signal_observed:
        raise SyntheticFixtureInvalid(
            "indicators 已產生 raw signal，但 backtest 沒有接受任何 signal；"
            "這表示策略實作或接受狀態機與 contract 不一致",
            classification="strategy-implementation",
        )
    raise SyntheticFixtureInvalid(
        "synthetic fixture 無法依 implementation contract 產生可接受的 raw signal；"
        "這是 fixture-invalid，不能只用交易數量不符帶過",
        classification="fixture-invalid",
    )


def _run_holding_cooldown_case(
    result: CheckResult,
    module: ModuleType,
    spec: Any,
    cost: Any,
    contract: dict[str, Any],
) -> None:
    holding = _int_value(spec.holding_sessions, "engine holding_sessions")
    cooldown = _int_value(spec.cooldown_sessions, "engine cooldown_sessions")
    direction = _synthetic_close_direction(contract, spec)
    first_signal_start = 40
    attempts: list[dict[str, Any]] = []
    selected: tuple[pd.DataFrame, Any, int, int | None, int] | None = None
    raw_signal_observed = False
    raw_required_observed = False
    state_machine_mismatch = False
    best_audit: dict[str, Any] | None = None
    # signal index 只是 episode 的 seed。每一次候選資料都必須先經過
    # indicators 的 raw signal，再以 backtest 驗證 state machine。
    for first_signal in range(first_signal_start, first_signal_start + 20):
        first_entry = first_signal + 1
        first_exit = first_entry + holding
        rejected_signal = first_exit + cooldown - 1 if cooldown else None
        accepted_start = first_exit + cooldown + 1 if cooldown else first_exit + 2
        for accepted_signal in range(accepted_start, accepted_start + 8):
            seeds = [first_signal]
            if rejected_signal is not None and rejected_signal > first_signal:
                seeds.append(rejected_signal)
            if accepted_signal not in seeds:
                seeds.append(accepted_signal)
            rows = max(180, accepted_signal + holding + 8)
            bars = _make_bars(
                rows,
                seeds,
                close_direction=direction,
                volume_lead_window=getattr(spec, "volume_lead_window", 5),
            )
            try:
                frame = _call_indicators(module, bars, spec)
                signal_columns, raw_mask = _raw_signal_mask(
                    frame, contract.get("indicator_contract", contract), spec
                )
                raw_indexes = {
                    int(index) for index, value in enumerate(raw_mask.tolist()) if bool(value)
                }
                backtest_result = _call_backtest(module, bars, spec, cost)
            except SyntheticFixtureInvalid as exc:
                attempts.append(
                    {
                        "first_signal_seed": first_signal,
                        "accepted_signal_seed": accepted_signal,
                        "error": str(exc),
                        "classification": exc.classification,
                    }
                )
                if exc.classification == "strategy-implementation":
                    state_machine_mismatch = True
                    break
                continue
            except (KeyError, TypeError, ValueError, AttributeError, SyntheticFailure) as exc:
                attempts.append(
                    {
                        "first_signal_seed": first_signal,
                        "accepted_signal_seed": accepted_signal,
                        "error": str(exc),
                        "classification": "strategy-implementation",
                    }
                )
                state_machine_mismatch = True
                continue
            raw_required = {first_signal, accepted_signal}
            if rejected_signal is not None:
                raw_required.add(rejected_signal)
            raw_signal_observed = raw_signal_observed or bool(raw_indexes)
            raw_required_observed = raw_required_observed or raw_required.issubset(raw_indexes)
            accepted_sessions = set(getattr(backtest_result, "accepted_signal_sessions", ()))
            accepted_session = bars.index[accepted_signal]
            trades = getattr(backtest_result, "trades", ())
            audit = _signal_audit(
                frame,
                raw_mask,
                backtest_result,
                holding=holding,
                cooldown=cooldown,
                first_ready=_int_value(
                    _get_path(contract, "indicator_contract.required_history_sessions", 0),
                    "required_history_sessions",
                ),
            )
            if best_audit is None or (
                len(audit["raw_signals"]),
                len(audit["accepted_signals"]),
                len(audit["trades"]),
            ) > (
                len(best_audit["raw_signals"]),
                len(best_audit["accepted_signals"]),
                len(best_audit["trades"]),
            ):
                best_audit = audit
            is_valid = (
                raw_required.issubset(raw_indexes)
                and len(trades) == 2
                and trades[0].exit_reason == "time"
                and trades[0].held_sessions == holding
                and trades[1].signal_session == accepted_session
                and trades[1].entry_session == bars.index[accepted_signal + 1]
                and (
                    rejected_signal is None or bars.index[rejected_signal] not in accepted_sessions
                )
            )
            attempts.append(
                {
                    "first_signal_seed": first_signal,
                    "rejected_signal_seed": rejected_signal,
                    "accepted_signal_seed": accepted_signal,
                    "raw_signal_columns": signal_columns,
                    "raw_signal_count": len(raw_indexes),
                    "trade_count": len(trades),
                }
            )
            if raw_required.issubset(raw_indexes) and len(trades) != 2:
                state_machine_mismatch = True
            if is_valid:
                selected = (bars, backtest_result, accepted_signal, rejected_signal, first_signal)
                break
        if selected is not None:
            break
    if selected is None:
        result.details["holding_cooldown_attempts"] = attempts
        if best_audit is not None:
            result.details["holding_cooldown_case"] = {
                **best_audit,
                "fixture_search_attempts": len(attempts),
            }
        if state_machine_mismatch or raw_required_observed:
            classification = "strategy-implementation"
        else:
            classification = "fixture-invalid"
        raise SyntheticFixtureInvalid(
            "holding/cooldown fixture 無法同時形成兩個 raw signal 與兩筆合法交易；"
            "請先區分 fixture 無法滿足條件，或策略實作沒有按 contract 接受 signal",
            classification=classification,
        )

    bars, backtest_result, accepted_signal, rejected_signal, first_signal = selected
    frame = _call_indicators(module, bars, spec)
    _, raw_mask = _raw_signal_mask(frame, contract.get("indicator_contract", contract), spec)
    audit = _signal_audit(
        frame,
        raw_mask,
        backtest_result,
        holding=holding,
        cooldown=cooldown,
        first_ready=_int_value(
            _get_path(contract, "indicator_contract.required_history_sessions", 0),
            "required_history_sessions",
        ),
    )
    if rejected_signal is not None:
        rejected_session = bars.index[rejected_signal].isoformat()
        for item in audit["rejected_signals"]:
            if item["session"] == rejected_session:
                item["reason"] = "cooldown-not-complete"
                audit["rejection_reasons"][rejected_session] = "cooldown-not-complete"
    trades = getattr(backtest_result, "trades", ())
    first, second = trades
    if first.exit_reason != "time" or first.held_sessions != holding:
        raise SyntheticFailure(
            f"第一筆交易沒有按 holding_sessions 結束：reason={first.exit_reason!r}, held={first.held_sessions!r}"
        )
    if second.signal_session != bars.index[accepted_signal]:
        raise SyntheticFailure("第二筆交易沒有在 cooldown 完成後的 signal 進場")
    if rejected_signal is not None and bars.index[rejected_signal] in getattr(
        backtest_result, "accepted_signal_sessions", ()
    ):
        raise SyntheticFailure("cooldown 尚未完成時錯誤接受 signal")
    if second.entry_session != bars.index[accepted_signal + 1]:
        raise SyntheticFailure("第二筆交易沒有使用 signal 後下一個 session 的 open")
    result.details["holding_sessions"] = holding
    result.details["cooldown_sessions"] = cooldown
    result.details["accepted_signal_count"] = len(
        getattr(backtest_result, "accepted_signal_sessions", ())
    )
    result.details["holding_cooldown_case"] = {
        **audit,
        "first_signal_seed": bars.index[first_signal].isoformat(),
        "accepted_signal_seed": bars.index[accepted_signal].isoformat(),
        "rejected_signal_seed": (
            bars.index[rejected_signal].isoformat() if rejected_signal is not None else None
        ),
        "fixture_search_attempts": len(attempts),
    }


def run_synthetic(context: StudyContext) -> CheckResult:
    """使用不含正式市場資料的合成 bars 執行 contract 邊界測試。"""

    result = CheckResult("synthetic")
    result.details.update(
        {
            "raw_signals": [],
            "accepted_signals": [],
            "rejected_signals": [],
            "rejection_reasons": {},
            "trades": [],
        }
    )
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
        (
            "signal",
            lambda: _run_signal_case(result, module, spec, cost, contract, indicator, values),
        ),
        ("intraday-exit", lambda: _run_exit_cases(result, module)),
        (
            "holding-cooldown",
            lambda: _run_holding_cooldown_case(result, module, spec, cost, contract),
        ),
    ]
    passed: list[str] = []
    passed_signal_cases: list[str] = []
    for name, case in cases:
        try:
            case()
        except SyntheticFixtureInvalid as exc:
            code = (
                "synthetic-fixture-invalid"
                if exc.classification == "fixture-invalid"
                else "synthetic-implementation-invalid"
            )
            result.error(
                code,
                f"{name} case 失敗：{exc}",
                path=engine_path,
                expected="contract-satisfying synthetic case",
                actual=exc.classification,
            )
            result.details.setdefault("synthetic_failure_classifications", {})[name] = (
                exc.classification
            )
        except (KeyError, TypeError, ValueError, AttributeError, SyntheticFailure) as exc:
            result.error("synthetic-case-failed", f"{name} case 失敗：{exc}", path=engine_path)
        else:
            if name == "signal":
                passed_signal_cases.append(name)
            else:
                passed.append(name)
    result.details["passed_cases"] = passed
    result.details["passed_signal_cases"] = passed_signal_cases
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
        if _is_forbidden_read_path(Path(relative)):
            result.error(
                "forbidden-source-path",
                "Source Bundle 不得要求目前角色讀取 Historical Evaluation 或 .super-admin 路徑",
                path=source_bundle_path,
                expected="outcome-relevant source outside forbidden stores",
                actual=relative,
            )
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
        if _is_forbidden_read_path(source):
            # The finding above is enough; do not open forbidden content.
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
    return (
        _display_path(context, path)
        if path is not None
        else Path(context.display_path(context.research_root))
    )


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
    if (
        not isinstance(complete_family, list)
        or not complete_family
        or not all(isinstance(item, str) for item in complete_family)
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

    result.details["identity"] = {
        "study_id": context.study_id,
        "candidate_id": None if expected_candidate is MISSING else expected_candidate,
        "trial_id": trial_id_values[0][2] if trial_id_values else None,
        "candidate_family": complete_family,
        "candidate_definition_has_explicit_candidate_id": bool(
            _collect_keyed_values(candidate, {"candidate_id"})
        ),
    }


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
    if not all(isinstance(value, dict) for value in (trial_inputs, preregistration, source_bundle)):
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
        if isinstance(eligibility, dict) and isinstance(
            eligibility.get("indicator_contract"), dict
        ):
            return {"indicator_contract": eligibility["indicator_contract"]}, None, label
    return None, None, None


def _check_precreate_artifact_shapes(
    context: StudyContext,
    result: CheckResult,
    documents: dict[str, dict[str, Any] | None],
    paths: dict[str, Path | None],
) -> None:
    """在沒有 Event 時先驗證 writer 會用到的 artifact 基本 shape。"""

    required: dict[str, tuple[str, ...]] = {
        "preregistration.yml": (
            "hypothesis",
            "complete_candidate_family",
            "maximum_trials",
            "eligibility_rules",
            "selection_rule",
            "tie_handling",
            "baseline_definition",
            "maximum_holding_sessions",
            "fold_warmup_sessions",
            "initial_cash",
            "evaluation_gates",
        ),
        "candidate-definition.yml": (
            "signal",
            "execution",
            "fold_policy",
        ),
        "qualification-spec.yml": (
            "preregistration_digest",
            "development",
            "evaluation",
        ),
        "development-trial-inputs.yml": (
            "trial_id",
            "candidate_id",
            "preregistration_digest",
            "source_bundle_digest",
            "strategy_engine_digest",
            "study_procedure_digest",
        ),
        "source-bundle.yml": ("schema_version", "files"),
    }
    for name, fields in required.items():
        document = documents.get(name)
        if not isinstance(document, dict):
            continue
        path = _display_path(context, paths[name] or context.research_root / name)
        for field_name in fields:
            value = _get_path(document, field_name, MISSING)
            if value is MISSING:
                result.error(
                    "invalid-artifact-shape",
                    f"{name} 缺少 writer 所需欄位：{field_name}",
                    path=path,
                    expected=field_name,
                    actual=None,
                )
        if name == "source-bundle.yml" and not isinstance(document.get("files"), list):
            result.error(
                "invalid-artifact-shape",
                "source-bundle.yml 的 files 必須是 list",
                path=path,
                expected="list",
                actual=type(document.get("files")).__name__,
            )
        if name == "preregistration.yml" and not isinstance(
            document.get("complete_candidate_family"), list
        ):
            result.error(
                "invalid-artifact-shape",
                "preregistration.yml 的 complete_candidate_family 必須是 list",
                path=path,
                expected="list",
                actual=type(document.get("complete_candidate_family")).__name__,
            )


def _check_precreate_contract_identity(
    context: StudyContext,
    result: CheckResult,
    contract: dict[str, Any] | None,
    contract_path: Path | None,
    contract_source: str | None,
    source_bundle: dict[str, Any] | None,
) -> None:
    """新 Study 強制使用唯一的 research implementation contract。"""

    expected_path = context.research_root / "implementation-contract.yml"
    expected_display = context.display_path(expected_path)
    if contract_source != "external" or contract_path is None:
        result.error(
            "contract-path-mismatch",
            "新 Study 必須使用 research/<study-id>/implementation-contract.yml 作為唯一 contract",
            path=_display_path(context, expected_path),
            expected=expected_display,
            actual=contract_source,
        )
        return
    actual_display = context.display_path(contract_path)
    if contract_path.resolve() != expected_path.resolve():
        result.error(
            "contract-path-mismatch",
            "implementation contract 路徑不是同名 research bundle 的 canonical path",
            path=_display_path(context, contract_path),
            expected=expected_display,
            actual=actual_display,
        )
    entries = _source_bundle_entries(source_bundle)
    expected_digest = entries.get(expected_display, MISSING)
    if expected_digest is MISSING:
        result.error(
            "contract-not-frozen",
            "Source Bundle 沒有綁定唯一的 research implementation contract",
            path=_display_path(context, context.research_root / "source-bundle.yml"),
            expected=expected_display,
            actual=sorted(entries),
        )
    elif contract_path.is_file():
        actual_digest = hashlib.sha256(contract_path.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            result.error(
                "contract-digest-mismatch",
                "Source Bundle 綁定的 implementation contract digest 不一致",
                path=_display_path(context, contract_path),
                expected=expected_digest,
                actual=actual_digest,
            )

    manifest_contract = context.study_root / "manifests" / "implementation-contract.yml"
    if manifest_contract.exists():
        result.error(
            "duplicate-implementation-contract",
            "Study manifest 不得另存第二份 implementation contract",
            path=_display_path(context, manifest_contract),
            expected="absent",
            actual="exists",
        )


def run_precreate(context: StudyContext) -> CheckResult:
    """在第一個 study-created Event 前完成完整、唯讀的建立前 contract。"""

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
    existing_events = _study_event_files(event_dir)
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
    _check_precreate_contract_identity(
        context,
        result,
        contract,
        contract_path,
        contract_source,
        documents.get("source-bundle.yml"),
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

    _check_precreate_artifact_shapes(context, result, documents, paths)

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
                    path=_display_path(
                        context,
                        qualification_path or context.research_root / "qualification-spec.yml",
                    ),
                    expected=expected_digest,
                    actual=None if actual_digest is MISSING else actual_digest,
                )
        _check_gate_maps(
            result,
            preregistration,
            qualification,
            path=_display_path(
                context, qualification_path or context.research_root / "qualification-spec.yml"
            ),
            exact=True,
        )

    if isinstance(source_bundle, dict):
        _check_source_bundle(
            context,
            result,
            source_bundle,
            source_bundle_path or context.research_root / "source-bundle.yml",
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

    # precreate 必須承擔原本在 study-created 後才執行的完整 contract 與
    # synthetic hard guard。這裡只合併唯讀結果，不會建立 Study 目錄、Event
    # 或任何 artifact。
    subchecks: list[dict[str, Any]] = []
    for check in (
        run_contract(context),
        run_synthetic(context),
    ):
        subchecks.append(check.as_dict(context))
        result.errors.extend(check.errors)
        result.warnings.extend(check.warnings)
    result.details["subchecks"] = subchecks
    result.details["precreate_guards"] = [
        "canonical-yaml-and-artifact-shape",
        "study-candidate-trial-family-identity",
        "preregistration-qualification-trial-source-digests",
        "implementation-contract",
        "outcome-relevant-parameters",
        "holding-cooldown-stop-target-gap-indicator-readiness",
        "synthetic-contract",
        "source-bundle-path-and-sha256",
    ]
    return result


def _digest_entry(
    context: StudyContext,
    result: CheckResult,
    *,
    label: str,
    path: Path,
    expected: Any,
    can_fix_before_study_created: bool,
) -> dict[str, Any]:
    """建立 expected/actual digest 診斷，不會覆寫任何檔案。"""

    display = context.display_path(path)
    entry: dict[str, Any] = {
        "label": label,
        "path": display,
        "expected": None if expected is MISSING else expected,
        "actual": None,
        "needs_update": False,
        "can_fix_before_study_created": can_fix_before_study_created,
    }
    if not path.is_file():
        entry["actual"] = "missing"
        if expected is not MISSING:
            result.error(
                "digest-source-missing",
                f"digest 綁定的檔案不存在：{display}",
                path=_display_path(context, path),
                expected="file",
                actual="missing",
            )
        return entry
    if _is_forbidden_read_path(path):
        entry["actual"] = "not-read-by-role"
        result.error(
            "forbidden-diagnostic-path",
            "目前角色不得讀取此路徑的內容",
            path=_display_path(context, path),
            expected="non-Evaluation, non-super-admin path",
            actual=display,
        )
        return entry
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    entry["actual"] = actual
    if expected is not MISSING and actual != expected:
        entry["needs_update"] = True
        result.error(
            "digest-drift",
            f"{label} digest drift：{display}",
            path=_display_path(context, path),
            expected=expected,
            actual=actual,
        )
    return entry


def _digest_field_entry(
    context: StudyContext,
    result: CheckResult,
    *,
    label: str,
    path: Path,
    field: str,
    expected: str,
    actual: Any,
    can_fix_before_study_created: bool,
) -> dict[str, Any]:
    """報告下游欄位的 expected/actual digest，不修改來源或 artifact。"""

    entry = {
        "label": label,
        "path": context.display_path(path),
        "field": field,
        "expected": expected,
        "actual": None if actual is MISSING else actual,
        "needs_update": actual != expected,
        "can_fix_before_study_created": can_fix_before_study_created,
    }
    if actual != expected:
        result.error(
            "digest-drift",
            f"{label} digest drift：{context.display_path(path)}",
            path=_display_path(context, path),
            expected=expected,
            actual=None if actual is MISSING else actual,
        )
    return entry


def run_diagnose(context: StudyContext) -> CheckResult:
    """唯讀列出 canonical drift、下游 digest 更新與 immutable 邊界。"""

    result = CheckResult("diagnose")
    event_paths = _study_event_files(context.study_root / "events")
    has_events = bool(event_paths)
    research_yaml = list(_walk_files(context.research_root, (".yml", ".yaml")))
    # 有 Event 後，Study 內的所有檔案都只列為 immutable，不再載入其 YAML
    # 內容；這避免診斷工具意外讀取正式結果或把 immutable 檔案當成可修復檔。
    study_yaml = [] if has_events else list(_walk_files(context.study_root, (".yml", ".yaml")))
    non_canonical: list[dict[str, Any]] = []
    for path in [*research_yaml, *study_yaml]:
        try:
            load_canonical(path)
        except Exception as exc:
            finding = {
                "path": context.display_path(path),
                "error": str(exc),
                "expected": "repository-canonical YAML",
            }
            non_canonical.append(finding)
            result.error(
                "non-canonical-yaml",
                f"YAML 不是 canonical：{context.display_path(path)}",
                path=_display_path(context, path),
                expected="repository-canonical YAML",
                actual=str(exc),
            )
    result.details["non_canonical_yaml"] = non_canonical

    fixable: list[str] = []
    if not has_events:
        fixable = [
            context.display_path(path)
            for path in _walk_files(
                context.research_root,
                (".yml", ".yaml", ".py", ".md", ".json", ".toml", ".txt"),
            )
        ]
    immutable: list[str] = [context.display_path(path) for path in event_paths]
    if has_events:
        # Event 一旦存在，Study 目錄內的 manifest、evidence、journal 及其他
        # 檔案都屬於既有鏈的一部分；只列名，不讀取內容，也不會嘗試覆寫。
        immutable.extend(
            context.display_path(path)
            for path in sorted(context.study_root.rglob("*"))
            if path.is_file() and not _is_forbidden_read_path(path)
        )
    authority_root = context.repository_root / ".authority" / context.study_id
    if authority_root.is_dir():
        immutable.extend(
            context.display_path(path)
            for path in sorted(authority_root.rglob("*"))
            if path.is_file()
        )
    result.details["study_has_event"] = has_events
    result.details["fixable_before_study_created"] = sorted(set(fixable))
    result.details["immutable_artifacts"] = sorted(set(immutable))
    result.details["immutable_policy"] = (
        "既有 Event、Study manifest/artifact 與 authority checkpoint 只能保留；"
        "診斷不會覆寫或刪除它們。"
    )

    preregistration, prereg_path = _load_research_document(
        context, result, "preregistration.yml", required=False, compare_manifest=False
    )
    qualification, qualification_path = _load_research_document(
        context, result, "qualification-spec.yml", required=False, compare_manifest=False
    )
    trial_inputs, trial_path = _load_research_document(
        context, result, "development-trial-inputs.yml", required=False, compare_manifest=False
    )
    source_bundle, source_bundle_path = _load_research_document(
        context, result, "source-bundle.yml", required=False, compare_manifest=False
    )
    candidate, _ = _load_research_document(
        context, result, "candidate-definition.yml", required=False, compare_manifest=False
    )
    contract, contract_path, contract_source = _find_research_contract(
        context, result, candidate, preregistration
    )
    digest_checks: list[dict[str, Any]] = []
    if isinstance(preregistration, dict) and prereg_path is not None:
        prereg_digest = canonical_digest(prereg_path.read_bytes())
        if isinstance(qualification, dict) and qualification_path is not None:
            digest_checks.append(
                _digest_field_entry(
                    context,
                    result,
                    label="qualification.preregistration_digest",
                    path=qualification_path,
                    field="preregistration_digest",
                    expected=prereg_digest,
                    actual=qualification.get("preregistration_digest", MISSING),
                    can_fix_before_study_created=not has_events,
                )
            )
        if isinstance(trial_inputs, dict) and trial_path is not None:
            trial_actual = trial_inputs.get("preregistration_digest", MISSING)
            digest_checks.append(
                {
                    "label": "development-trial-inputs.preregistration_digest",
                    "path": context.display_path(trial_path),
                    "field": "preregistration_digest",
                    "expected": prereg_digest,
                    "actual": None if trial_actual is MISSING else trial_actual,
                    "needs_update": trial_actual != prereg_digest,
                    "can_fix_before_study_created": not has_events,
                }
            )
            if trial_actual != prereg_digest:
                result.error(
                    "digest-drift",
                    "development-trial-inputs 的 preregistration digest 需要更新",
                    path=_display_path(context, trial_path),
                    expected=prereg_digest,
                    actual=None if trial_actual is MISSING else trial_actual,
                )
        if isinstance(source_bundle, dict):
            prereg_relative = context.display_path(prereg_path)
            source_expected = _source_bundle_entries(source_bundle).get(prereg_relative, MISSING)
            if source_expected != prereg_digest:
                result.error(
                    "digest-drift",
                    "Source Bundle 的 preregistration entry 需要更新",
                    path=_display_path(
                        context, source_bundle_path or context.research_root / "source-bundle.yml"
                    ),
                    expected=prereg_digest,
                    actual=None if source_expected is MISSING else source_expected,
                )
            digest_checks.append(
                {
                    "label": "source-bundle.preregistration-entry",
                    "path": context.display_path(
                        source_bundle_path or context.research_root / "source-bundle.yml"
                    ),
                    "field": prereg_relative,
                    "expected": prereg_digest,
                    "actual": None if source_expected is MISSING else source_expected,
                    "needs_update": source_expected != prereg_digest,
                    "can_fix_before_study_created": not has_events,
                }
            )

    if isinstance(source_bundle, dict) and source_bundle_path is not None:
        source_digest = canonical_digest(source_bundle_path.read_bytes())
        if isinstance(trial_inputs, dict) and trial_path is not None:
            trial_source_actual = trial_inputs.get("source_bundle_digest", MISSING)
            digest_checks.append(
                {
                    "label": "development-trial-inputs.source_bundle_digest",
                    "path": context.display_path(trial_path),
                    "field": "source_bundle_digest",
                    "expected": source_digest,
                    "actual": None if trial_source_actual is MISSING else trial_source_actual,
                    "needs_update": trial_source_actual != source_digest,
                    "can_fix_before_study_created": not has_events,
                }
            )
            if trial_source_actual != source_digest:
                result.error(
                    "digest-drift",
                    "development-trial-inputs 的 Source Bundle digest 需要更新",
                    path=_display_path(context, trial_path),
                    expected=source_digest,
                    actual=None if trial_source_actual is MISSING else trial_source_actual,
                )
        entries = _source_bundle_entries(source_bundle)
        for relative, expected in sorted(entries.items()):
            source = _resolve_inside(context.repository_root, relative)
            if source is None or _is_forbidden_read_path(source):
                continue
            digest_checks.append(
                _digest_entry(
                    context,
                    result,
                    label=f"source-bundle:{relative}",
                    path=source,
                    expected=expected,
                    can_fix_before_study_created=not has_events,
                )
            )

    result.details["digest_checks"] = digest_checks
    result.details["digest_updates_required"] = [
        entry for entry in digest_checks if entry.get("needs_update")
    ]
    result.details["contract_source"] = (
        context.display_path(contract_path) if contract_path else contract_source
    )
    return result


def _check_canonical_study_tree(context: StudyContext, result: CheckResult) -> None:
    checked = 0
    for path in _walk_files(context.study_root, (".yml",)):
        checked += 1
        try:
            load_canonical(path)
        except Exception as exc:
            result.error(
                "non-canonical-study-yaml",
                f"Study YAML 不是可驗證的 canonical YAML：{exc}",
                path=path,
            )
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
            result.error(
                "invalid-source-bundle",
                f"無法讀取 research Source Bundle：{exc}",
                path=research_source_path,
            )
    elif not research_source_path.is_file():
        result.warning(
            "missing-research-source-bundle",
            "找不到 research/source-bundle.yml",
            path=research_source_path,
        )

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
        result.error(
            "past-candidate-freeze",
            "Study 已經進入 candidate freeze 後的正式評估或終止階段，不能再當作 freeze 前檢查",
        )
    elif state == "terminal-without-candidate":
        result.details["candidate_freeze_required"] = False
        result.warning(
            "candidate-freeze-not-applicable",
            "Study 已依失敗或不可判定規則合法 terminal，且沒有 candidate；不把缺少 provenance/selection evidence 當成缺陷",
        )
    else:
        result.details["candidate_freeze_required"] = True

    if authority_root is None:
        result.warning(
            "authority-not-checked",
            "沒有提供 --authority-root；本次未核對本機 authority checkpoints",
        )
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
    elif command in {"diagnose", "diagnostic"}:
        checks = [run_diagnose(context)]
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
    for name in (
        "precreate",
        "diagnose",
        "identity",
        "contract",
        "synthetic",
        "freeze",
        "all",
    ):
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
