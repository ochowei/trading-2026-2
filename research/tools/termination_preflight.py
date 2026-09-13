#!/usr/bin/env python3
"""Study termination payload 的唯讀 preflight。

這支工具只驗證送進既有 workflow writer 前的 payload、路徑、authority
與 terminal evidence。它不呼叫 writer、不發布 artifact，也不宣稱
termination 是跨 Event 與 artifact 的 atomic transaction；writer 若失敗，
仍應使用 writer CLI 已定義的 JSON error contract 與 recover 流程。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_NAME = "strategy-forward-replication-research--v001"
STUDY_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,62}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / WORKFLOW_NAME
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import canonical_digest, load_canonical  # noqa: E402
from validator.errors import WorkflowError  # noqa: E402
from validator.paths import resolve_inside  # noqa: E402
from validator.study import (  # noqa: E402
    WorkflowRules,
    _expected_terminal_bindings,
    validate_study,
)
from writer.authority import AuthorityStore  # noqa: E402


def _finding(
    code: str,
    message: str,
    *,
    path: Path | None = None,
    expected: Any = None,
    actual: Any = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "code": code,
        "severity": "error",
        "message": message,
        "expected": expected,
        "actual": actual,
    }
    if path is not None:
        value["path"] = str(path)
    return value


def _display(repository: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repository.resolve()).as_posix()
    except ValueError:
        return str(path)


def _inside_path(study_root: Path, value: Any) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, "path 必須是非空 repository-relative 字串"
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        return None, "path 不得是絕對路徑，也不得包含 . 或 .."
    try:
        resolved = resolve_inside(study_root, value, must_exist=False)
    except (ValueError, WorkflowError) as exc:
        return None, str(exc)
    if any(part in {"historical-evaluation-artifacts", ".super-admin"} for part in path.parts):
        return None, "termination preflight 不接受 Historical Evaluation 或 .super-admin 路徑"
    if any(part == "research" for part in path.parts):
        return None, "termination payload path 必須相對於目前 Study，不得再嵌入 research 路徑"
    return resolved, None


def _authority_preflight(
    repository: Path,
    authority: Path,
    study_id: str,
) -> dict[str, Any]:
    checker = (
        repository
        / ".agents"
        / "skills"
        / "build-strategy-study-to-freeze"
        / "scripts"
        / "check_authority_root.py"
    )
    command = [
        sys.executable,
        str(checker),
        study_id,
        "--repository-root",
        str(repository),
        "--authority-root",
        str(authority),
        "--phase",
        "existing",
    ]
    if not checker.is_file():
        return {
            "status": "failed",
            "errors": [
                _finding(
                    "authority-checker-missing",
                    "找不到 authority root checker",
                    path=checker,
                    expected="file",
                    actual="missing",
                )
            ],
            "command": command,
        }
    completed = subprocess.run(
        command,
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        output = json.loads(completed.stdout)
    except json.JSONDecodeError:
        output = {
            "status": "rejected",
            "raw_stdout": completed.stdout,
            "raw_stderr": completed.stderr,
            "returncode": completed.returncode,
        }
    if completed.returncode != 0 or output.get("status") != "passed":
        return {
            "status": "failed",
            "errors": [
                _finding(
                    "authority-root-preflight-failed",
                    "termination 執行前 authority existing preflight 未通過",
                    path=authority,
                    expected={"phase": "existing", "status": "passed"},
                    actual=output,
                )
            ],
            "checker": output,
            "command": command,
        }
    return {"status": "passed", "checker": output, "command": command, "errors": []}


def _load_projection(
    repository: Path,
    authority: Path,
    study_id: str,
) -> tuple[Any | None, list[dict[str, Any]]]:
    study_root = repository / "workflows" / WORKFLOW_NAME / "studies" / study_id
    errors: list[dict[str, Any]] = []
    event_root = study_root / "events"
    event_names = sorted(path.name for path in event_root.glob("*.yml")) if event_root.is_dir() else []
    if any("historical-evaluation" in name for name in event_names):
        errors.append(
            _finding(
                "historical-evaluation-scope-blocked",
                "termination preflight 不讀取已進入 Historical Evaluation 的 Study",
                path=event_root,
                expected="setup termination before Historical Evaluation",
                actual=event_names,
            )
        )
        return None, errors
    if not study_root.is_dir():
        errors.append(
            _finding(
                "missing-study",
                "找不到要終止的 Workflow Study",
                path=study_root,
                expected="directory with existing Event chain",
                actual="missing",
            )
        )
        return None, errors
    try:
        projection = validate_study(
            study_root,
            WorkflowRules(repository / "workflows" / WORKFLOW_NAME, repository_root=repository),
        )
        if not projection.events:
            raise ValueError("Study 尚未有任何 Event")
        AuthorityStore(authority).verify(study_id, projection.events)
    except (OSError, ValueError, KeyError, WorkflowError) as exc:
        errors.append(
            _finding(
                "study-or-authority-invalid",
                "無法驗證目前 Study chain 與 authority checkpoint",
                path=study_root,
                expected="valid Study chain and authority chain",
                actual=str(exc),
            )
        )
        return None, errors
    return projection, errors


def _writer_error_result(
    returncode: int,
    stdout: str,
    stderr: str,
    *,
    command: str,
    study_id: str,
) -> dict[str, Any]:
    """將 writer CLI 的輸出正規化；不執行 writer。"""

    try:
        value = json.loads(stdout)
    except json.JSONDecodeError:
        value = None
    if isinstance(value, dict) and value.get("status") == "error" and isinstance(
        value.get("error"), dict
    ):
        return value
    return {
        "command": command,
        "study_id": study_id,
        "status": "error",
        "error": {
            "code": "writer-unstructured-output",
            "message": "writer 沒有回傳既定 JSON error payload",
            "type": "WriterOutputError",
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        },
    }


def run_preflight(
    repository_root: Path | str,
    study_id: str,
    event_type: str,
    payload_path: Path | str,
    authority_root: Path | str,
) -> dict[str, Any]:
    repository = Path(repository_root).expanduser().resolve()
    authority = Path(authority_root).expanduser()
    if not authority.is_absolute():
        authority = (repository / authority).resolve()
    else:
        authority = authority.resolve()
    payload = Path(payload_path).expanduser()
    if not payload.is_absolute():
        payload = (repository / payload).resolve()
    else:
        payload = payload.resolve()

    result: dict[str, Any] = {
        "command": "termination-preflight",
        "study_id": study_id,
        "event_type": event_type,
        "payload_path": _display(repository, payload),
        "status": "failed",
        "errors": [],
        "warnings": [],
        "details": {
            "writer_handoff": {
                "structured_error_contract": True,
                "writer_error_shape": {
                    "status": "error",
                    "command": "append",
                    "study_id": study_id,
                    "error": {"code": "string", "message": "string", "type": "string"},
                },
                "atomic": False,
                "limitation": (
                    "payload preflight、artifact publish 與 writer append 是分開操作；"
                    "既有 writer 未被修改，因此本工具不宣稱 termination 具備跨步驟 atomicity。"
                ),
            }
        },
    }
    if STUDY_ID_PATTERN.fullmatch(study_id) is None:
        result["errors"].append(
            _finding(
                "invalid-study-id",
                "Study ID 格式不安全",
                expected="3--63 個小寫英數字與連字號",
                actual=study_id,
            )
        )
    expected_authority = (repository / ".authority").resolve()
    if authority != expected_authority:
        result["errors"].append(
            _finding(
                "authority-root-must-be-repository-local",
                "termination 必須使用 repository/.authority",
                expected=str(expected_authority),
                actual=str(authority),
            )
        )
    authority_result = _authority_preflight(repository, authority, study_id)
    result["details"]["authority_preflight"] = authority_result
    result["errors"].extend(authority_result.get("errors", []))
    projection, projection_errors = _load_projection(repository, authority, study_id)
    result["errors"].extend(projection_errors)

    payload_value: Any = None
    if not payload.is_file():
        result["errors"].append(
            _finding(
                "missing-payload",
                "找不到 termination payload",
                path=payload,
                expected="canonical YAML file",
                actual="missing",
            )
        )
    else:
        try:
            payload_value = load_canonical(payload)
        except Exception as exc:
            result["errors"].append(
                _finding(
                    "non-canonical-payload",
                    "termination payload 不是 canonical YAML",
                    path=payload,
                    expected="repository-canonical YAML",
                    actual=str(exc),
                )
            )
        if payload_value is not None and not isinstance(payload_value, dict):
            result["errors"].append(
                _finding(
                    "invalid-payload-shape",
                    "termination payload 最上層必須是 mapping",
                    path=payload,
                    expected="mapping",
                    actual=type(payload_value).__name__,
                )
            )

    if isinstance(payload_value, dict):
        declared_study = payload_value.get("study_id")
        if declared_study is not None and declared_study != study_id:
            result["errors"].append(
                _finding(
                    "payload-study-id-mismatch",
                    "payload 內的 Study ID 與 CLI Study ID 不一致",
                    path=payload,
                    expected=study_id,
                    actual=declared_study,
                )
            )
        declared_event = payload_value.get("event_type")
        if declared_event is not None and declared_event != event_type:
            result["errors"].append(
                _finding(
                    "payload-event-type-mismatch",
                    "payload 內的 event type 與 CLI event type 不一致",
                    path=payload,
                    expected=event_type,
                    actual=declared_event,
                )
            )
        if event_type not in {"evidence-unavailable", "study-terminal"}:
            result["errors"].append(
                _finding(
                    "unsupported-termination-event",
                    "termination preflight 只接受 evidence-unavailable 或 study-terminal",
                    path=payload,
                    expected=["evidence-unavailable", "study-terminal"],
                    actual=event_type,
                )
            )
        study_root = repository / "workflows" / WORKFLOW_NAME / "studies" / study_id
        if event_type == "evidence-unavailable":
            if payload_value.get("stage") != "development":
                result["errors"].append(
                    _finding(
                        "invalid-termination-stage",
                        "setup termination 的 evidence-unavailable stage 必須是 development",
                        path=payload,
                        expected="development",
                        actual=payload_value.get("stage"),
                    )
                )
            for field_name in ("stage", "unavailable_path", "reason"):
                if field_name not in payload_value:
                    result["errors"].append(
                        _finding(
                            "missing-termination-field",
                            f"evidence-unavailable 缺少 {field_name}",
                            path=payload,
                            expected=field_name,
                            actual=None,
                        )
                    )
            missing_path, path_error = _inside_path(
                study_root, payload_value.get("unavailable_path")
            )
            if path_error:
                result["errors"].append(
                    _finding(
                        "termination-path-invalid",
                        f"unavailable_path 不合法：{path_error}",
                        path=payload,
                        expected="absent path relative to current Study",
                        actual=payload_value.get("unavailable_path"),
                    )
                )
            elif missing_path is not None:
                exists = missing_path.exists() or missing_path.is_symlink() or os.path.lexists(missing_path)
                result["details"]["unavailable_path"] = {
                    "path": _display(repository, missing_path),
                    "exists": exists,
                }
                if exists:
                    result["errors"].append(
                        _finding(
                            "unavailable-path-exists",
                            "unavailable_path 指向已存在的檔案或目錄",
                            path=missing_path,
                            expected="path absent",
                            actual=_display(repository, missing_path),
                        )
                    )
            if projection is not None and getattr(projection, "pending_terminal_outcome", None):
                result["errors"].append(
                    _finding(
                        "termination-transition-invalid",
                        "Study 已有 pending terminal disposition，不能再追加 evidence-unavailable",
                        path=payload,
                        expected=None,
                        actual=projection.pending_terminal_outcome,
                    )
                )
        elif event_type == "study-terminal":
            required = (
                "outcome",
                "authority",
                "terminal_evidence_path",
                "terminal_evidence_digest",
            )
            for field_name in required:
                if field_name not in payload_value:
                    result["errors"].append(
                        _finding(
                            "missing-termination-field",
                            f"study-terminal 缺少 {field_name}",
                            path=payload,
                            expected=field_name,
                            actual=None,
                        )
                    )
            expected_authority = (
                "retrospectively-supported"
                if payload_value.get("outcome") == "pass"
                else "none"
            )
            if payload_value.get("authority") != expected_authority:
                result["errors"].append(
                    _finding(
                        "terminal-authority-mismatch",
                        "terminal payload 的 authority 與 outcome 不一致",
                        path=payload,
                        expected=expected_authority,
                        actual=payload_value.get("authority"),
                    )
                )
            expected_digest = payload_value.get("terminal_evidence_digest")
            if not isinstance(expected_digest, str) or SHA256_PATTERN.fullmatch(expected_digest) is None:
                result["errors"].append(
                    _finding(
                        "invalid-terminal-evidence-digest",
                        "terminal_evidence_digest 必須是 64 位小寫 SHA-256",
                        path=payload,
                        expected="64 lowercase hex characters",
                        actual=expected_digest,
                    )
                )
            evidence_path, path_error = _inside_path(
                study_root, payload_value.get("terminal_evidence_path")
            )
            if path_error:
                result["errors"].append(
                    _finding(
                        "termination-path-invalid",
                        f"terminal_evidence_path 不合法：{path_error}",
                        path=payload,
                        expected="path relative to current Study",
                        actual=payload_value.get("terminal_evidence_path"),
                    )
                )
            elif evidence_path is not None:
                if payload_value.get("outcome") == "indeterminate" and not (
                    Path(payload_value["terminal_evidence_path"]).parts[:1] == ("evidence",)
                ):
                    result["errors"].append(
                        _finding(
                            "terminal-evidence-path-mismatch",
                            "indeterminate termination 的 terminal evidence 必須位於 Study evidence/",
                            path=evidence_path,
                            expected="evidence/terminal-evidence.yml",
                            actual=payload_value.get("terminal_evidence_path"),
                        )
                    )
                if not evidence_path.is_file():
                    result["errors"].append(
                        _finding(
                            "missing-terminal-evidence",
                            "找不到 terminal evidence artifact",
                            path=evidence_path,
                            expected="canonical YAML file",
                            actual="missing",
                        )
                    )
                else:
                    try:
                        terminal = load_canonical(evidence_path)
                        actual_digest = canonical_digest(evidence_path.read_bytes())
                        result["details"]["terminal_evidence"] = {
                            "path": _display(repository, evidence_path),
                            "expected_digest": expected_digest,
                            "actual_digest": actual_digest,
                        }
                        if expected_digest != actual_digest:
                            result["errors"].append(
                                _finding(
                                    "terminal-evidence-digest-mismatch",
                                    "terminal evidence digest 不一致",
                                    path=evidence_path,
                                    expected=expected_digest,
                                    actual=actual_digest,
                                )
                            )
                        if not isinstance(terminal, dict):
                            result["errors"].append(
                                _finding(
                                    "invalid-terminal-evidence-shape",
                                    "terminal evidence 最上層必須是 mapping",
                                    path=evidence_path,
                                    expected="mapping",
                                    actual=type(terminal).__name__,
                                    )
                                )
                        else:
                            try:
                                rules = WorkflowRules(
                                    repository / "workflows" / WORKFLOW_NAME,
                                    repository_root=repository,
                                )
                                rules.schema_store.validate(
                                    "terminal-evidence.schema.yml", terminal
                                )
                            except (OSError, KeyError, ValueError, WorkflowError) as exc:
                                result["errors"].append(
                                    _finding(
                                        "invalid-terminal-evidence",
                                        "terminal evidence 不符合 workflow schema",
                                        path=evidence_path,
                                        expected="terminal-evidence.schema.yml",
                                        actual=str(exc),
                                    )
                                )
                            if terminal.get("outcome") != payload_value.get("outcome"):
                                result["errors"].append(
                                    _finding(
                                        "terminal-evidence-outcome-mismatch",
                                        "terminal evidence outcome 與 payload 不一致",
                                        path=evidence_path,
                                        expected=payload_value.get("outcome"),
                                        actual=terminal.get("outcome"),
                                    )
                                )
                            if terminal.get("authority") != expected_authority:
                                result["errors"].append(
                                    _finding(
                                        "terminal-evidence-authority-mismatch",
                                        "terminal evidence authority 與 outcome 不一致",
                                        path=evidence_path,
                                        expected=expected_authority,
                                        actual=terminal.get("authority"),
                                    )
                                )
                            if terminal.get("recomputed") is not True:
                                result["errors"].append(
                                    _finding(
                                        "terminal-evidence-not-recomputed",
                                        "terminal evidence 必須明示 recomputed: true",
                                        path=evidence_path,
                                        expected=True,
                                        actual=terminal.get("recomputed"),
                                    )
                                )
                            if projection is not None:
                                expected_bindings = _expected_terminal_bindings(projection)
                                if terminal.get("bindings") != expected_bindings:
                                    result["errors"].append(
                                        _finding(
                                            "terminal-evidence-binding-mismatch",
                                            "terminal evidence bindings 與目前 Event chain 不一致",
                                            path=evidence_path,
                                            expected=expected_bindings,
                                            actual=terminal.get("bindings"),
                                        )
                                    )
                    except Exception as exc:
                        result["errors"].append(
                            _finding(
                                "non-canonical-terminal-evidence",
                                "terminal evidence 不是可讀取的 canonical YAML",
                                path=evidence_path,
                                expected="canonical YAML",
                                actual=str(exc),
                            )
                        )
            if projection is not None:
                pending = getattr(projection, "pending_terminal_outcome", None)
                if pending is None:
                    result["errors"].append(
                        _finding(
                            "terminal-transition-invalid",
                            "Study 目前沒有可完成的 pending terminal disposition",
                            path=payload,
                            expected="pending terminal outcome",
                            actual=None,
                        )
                    )
                elif payload_value.get("outcome") != pending:
                    result["errors"].append(
                        _finding(
                            "terminal-outcome-mismatch",
                            "terminal outcome 與前一個 Event 的 disposition 不一致",
                            path=payload,
                            expected=pending,
                            actual=payload_value.get("outcome"),
                        )
                    )
    result["status"] = "passed" if not result["errors"] else "failed"
    result["error_count"] = len(result["errors"])
    result["warning_count"] = len(result["warnings"])
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="唯讀驗證 Study termination payload")
    parser.add_argument("study_id")
    parser.add_argument("--event-type", required=True, choices=("evidence-unavailable", "study-terminal"))
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--authority-root", type=Path, required=True)
    args = parser.parse_args(argv)
    output = run_preflight(
        args.repository_root,
        args.study_id,
        args.event_type,
        args.payload,
        args.authority_root,
    )
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if output["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
