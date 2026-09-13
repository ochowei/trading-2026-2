#!/usr/bin/env python3
"""唯讀檢查新 Study 使用的 repository-local authority root。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

WORKFLOW_NAME = "strategy-forward-replication-research--v001"
DEFAULT_AUTHORITY_RELATIVE = Path(".authority")
STUDY_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,62}$")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolve_path(repository: Path, value: Path) -> Path:
    if value.is_absolute():
        return value.resolve()
    return (repository / value).resolve()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _finding(code: str, message: str, *, expected: Any = None, actual: Any = None) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "expected": expected,
        "actual": actual,
    }


def _run_git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )


def _check_git_inclusion(
    repository: Path,
    authority: Path,
    result: dict[str, Any],
) -> None:
    root_check = _run_git(repository, "rev-parse", "--show-toplevel")
    if root_check.returncode != 0:
        result["errors"].append(
            _finding(
                "git-repository-missing",
                "repository-local authority root 必須位於 Git repository 內",
                expected="可由 git rev-parse 辨識的 repository",
                actual=root_check.stderr.strip() or None,
            )
        )
        return

    git_root = Path(root_check.stdout.strip()).resolve()
    if git_root != repository:
        result["errors"].append(
            _finding(
                "repository-root-mismatch",
                "指定的 repository-root 不是目前 Git repository 的根目錄",
                expected=str(git_root),
                actual=str(repository),
            )
        )
        return

    if not _is_within(authority, repository):
        return

    relative = authority.relative_to(repository).as_posix()
    ignored = _run_git(repository, "check-ignore", "--quiet", "--no-index", "--", relative)
    if ignored.returncode == 0:
        result["errors"].append(
            _finding(
                "authority-root-ignored",
                "authority root 被 .gitignore 排除，無法依規範納入 Git",
                expected="not ignored",
                actual=relative,
            )
        )
    elif ignored.returncode != 1:
        result["errors"].append(
            _finding(
                "git-check-failed",
                "無法確認 authority root 是否被 Git 忽略",
                expected="git check-ignore 可正常執行",
                actual=ignored.stderr.strip() or ignored.returncode,
            )
        )

    marker = authority / "README.md"
    if not marker.is_file():
        result["errors"].append(
            _finding(
                "authority-root-marker-missing",
                "authority root 缺少受 Git 追蹤的目錄說明檔",
                expected=str(marker),
                actual="missing",
            )
        )
        return

    marker_relative = marker.relative_to(repository).as_posix()
    marker_ignored = _run_git(
        repository,
        "check-ignore",
        "--quiet",
        "--no-index",
        "--",
        marker_relative,
    )
    if marker_ignored.returncode == 0:
        result["errors"].append(
            _finding(
                "authority-marker-ignored",
                "authority root 說明檔被 .gitignore 排除",
                expected="not ignored",
                actual=marker_relative,
            )
        )

    tracked = _run_git(repository, "ls-files", "--error-unmatch", "--", marker_relative)
    result["details"]["git_tracking"] = (
        "tracked" if tracked.returncode == 0 else "not-yet-tracked"
    )
    if tracked.returncode != 0:
        result["warnings"].append(
            _finding(
                "authority-root-not-yet-tracked",
                "authority root 尚未進入 Git index；完成 Study 前必須加入 commit",
                expected="tracked",
                actual=marker_relative,
            )
        )


def _check_authority_location(
    repository: Path,
    authority: Path,
    study_id: str,
    result: dict[str, Any],
) -> Path:
    expected = (repository / DEFAULT_AUTHORITY_RELATIVE).resolve()
    result["details"]["expected_authority_root"] = str(expected)
    if authority != expected:
        result["errors"].append(
            _finding(
                "authority-root-must-be-repository-local",
                "新 Study 的 authority root 必須固定為 repository/.authority",
                expected=str(expected),
                actual=str(authority),
            )
        )
    if not _is_within(authority, repository) or authority == repository:
        result["errors"].append(
            _finding(
                "authority-root-outside-repository",
                "authority root 必須位於 repository 內",
                expected=str(repository),
                actual=str(authority),
            )
        )

    if not _is_within(authority, repository):
        result["details"]["authority_root_relative"] = None
        return authority / study_id

    workflow_study = repository / "workflows" / WORKFLOW_NAME / "studies" / study_id
    research_study = repository / "research" / study_id
    for label, study_root in (("Workflow Study", workflow_study), ("research Study", research_study)):
        if _is_within(authority, study_root.resolve()):
            result["errors"].append(
                _finding(
                    "authority-root-inside-study",
                    f"authority root 不得位於 {label} 目錄內",
                    expected="Study 目錄之外",
                    actual=str(authority),
                )
            )

    result["details"]["authority_root_relative"] = (
        authority.relative_to(repository).as_posix()
        if _is_within(authority, repository)
        else None
    )
    return authority / study_id


def _check_new_study_state(
    repository: Path,
    authority_study: Path,
    study_id: str,
    result: dict[str, Any],
) -> None:
    workflow_study = repository / "workflows" / WORKFLOW_NAME / "studies" / study_id
    research_study = repository / "research" / study_id
    for label, path in (("Workflow Study", workflow_study), ("research bundle", research_study)):
        if path.exists():
            result["errors"].append(
                _finding(
                    "study-tree-already-exists",
                    f"{label} 已存在；authority preflight 不允許把它當成新 Study",
                    expected="path absent",
                    actual=str(path),
                )
            )

    if authority_study.is_symlink():
        result["errors"].append(
            _finding(
                "study-authority-path-symlink",
                "新 Study 的 authority 子目錄不得是 symlink，避免鏈結到未確認的位置",
                expected="absent or real empty directory",
                actual=str(authority_study),
            )
        )
        return
    if not authority_study.exists():
        result["details"]["study_authority_state"] = "absent"
        return
    if not authority_study.is_dir():
        result["errors"].append(
            _finding(
                "study-authority-path-not-directory",
                "該 Study 的 authority 路徑不是目錄",
                expected="directory",
                actual=str(authority_study),
            )
        )
        return
    entries = sorted(path.name for path in authority_study.iterdir())
    result["details"]["study_authority_state"] = "empty" if not entries else "non-empty"
    if entries:
        result["errors"].append(
            _finding(
                "study-authority-path-not-empty",
                "新 Study 的 authority 子目錄不是空的，不能直接重用",
                expected="empty directory or absent",
                actual=entries,
            )
        )


def _check_staged_study_state(
    repository: Path,
    authority_study: Path,
    study_id: str,
    result: dict[str, Any],
) -> None:
    """檢查 research bundle 已備妥、但 writer 尚未建立任何 Event 的階段。"""

    workflow_study = repository / "workflows" / WORKFLOW_NAME / "studies" / study_id
    research_study = repository / "research" / study_id
    if research_study.is_symlink():
        result["errors"].append(
            _finding(
                "research-bundle-symlink",
                "staged mode 的 research bundle 不得是 symlink",
                expected="real non-empty directory",
                actual=str(research_study),
            )
        )
    elif not research_study.is_dir():
        result["errors"].append(
            _finding(
                "missing-research-bundle",
                "staged mode 要求同名 research bundle 已存在",
                expected=str(research_study),
                actual="missing",
            )
        )
    else:
        entries = sorted(path.name for path in research_study.iterdir())
        result["details"]["research_bundle_state"] = "non-empty" if entries else "empty"
        if not entries:
            result["errors"].append(
                _finding(
                    "empty-research-bundle",
                    "staged mode 不接受空的 research bundle",
                    expected="non-empty directory",
                    actual=entries,
                )
            )

    if workflow_study.is_symlink():
        result["errors"].append(
            _finding(
                "study-tree-symlink",
                "staged mode 的 Workflow Study 路徑不得是 symlink",
                expected="absent or real directory without Events",
                actual=str(workflow_study),
            )
        )
    elif not workflow_study.exists():
        result["details"]["workflow_study_state"] = "absent"
    elif not workflow_study.is_dir():
        result["errors"].append(
            _finding(
                "study-tree-not-directory",
                "staged mode 的 Workflow Study 路徑不是目錄",
                expected="directory without Events",
                actual=str(workflow_study),
            )
        )
    else:
        event_root = workflow_study / "events"
        event_entries = (
            sorted(path.name for path in event_root.iterdir())
            if event_root.is_dir()
            else []
        )
        # staged phase 必須沒有任何 Event；隱藏檔也不能被當成可忽略的
        # checkpoint 或暫存 Event，否則 writer 前的狀態就不是乾淨的 staged。
        event_files = event_entries
        if event_files:
            result["errors"].append(
                _finding(
                    "study-events-already-exist",
                    "staged mode 要求 Workflow Study 尚未有任何 Event",
                    expected="no Event files",
                    actual=event_files,
                )
            )
        unexpected = sorted(
            path.name
            for path in workflow_study.iterdir()
            if path.name != "events" and not path.name.startswith(".")
        )
        if unexpected:
            result["errors"].append(
                _finding(
                    "study-tree-not-staged",
                    "writer 前的 Workflow Study 不應已有 manifest 或 artifact",
                    expected="only optional empty events directory",
                    actual=unexpected,
                )
            )
        result["details"]["workflow_study_state"] = "no-events"

    if authority_study.is_symlink():
        result["errors"].append(
            _finding(
                "study-authority-path-symlink",
                "staged mode 的 authority 子目錄不得是 symlink",
                expected="absent or real empty directory",
                actual=str(authority_study),
            )
        )
    elif not authority_study.exists():
        result["details"]["study_authority_state"] = "absent"
    elif not authority_study.is_dir():
        result["errors"].append(
            _finding(
                "study-authority-path-not-directory",
                "staged mode 的 authority 子目錄不是目錄",
                expected="directory",
                actual=str(authority_study),
            )
        )
    else:
        entries = sorted(path.name for path in authority_study.iterdir())
        result["details"]["study_authority_state"] = "empty" if not entries else "non-empty"
        if entries:
            result["errors"].append(
                _finding(
                    "study-authority-path-not-empty",
                    "staged mode 的 authority 子目錄必須不存在或為空",
                    expected="empty directory or absent",
                    actual=entries,
                )
            )


def _check_existing_study_state(
    repository: Path,
    authority: Path,
    study_id: str,
    result: dict[str, Any],
) -> None:
    workflow_root = repository / "workflows" / WORKFLOW_NAME
    study_root = workflow_root / "studies" / study_id
    if not study_root.is_dir():
        result["errors"].append(
            _finding(
                "missing-study",
                "existing mode 找不到 Workflow Study 目錄",
                expected=str(study_root),
                actual="missing",
            )
        )
        return

    if str(workflow_root) not in sys.path:
        sys.path.insert(0, str(workflow_root))
    try:
        from validator.errors import WorkflowError
        from validator.study import WorkflowRules, validate_study
        from writer.authority import AuthorityStore
    except ImportError as exc:
        result["errors"].append(
            _finding(
                "authority-chain-invalid",
                f"無法載入 Workflow validator 或 authority store：{exc}",
                expected="可載入 Workflow validator 與 authority store",
                actual=str(exc),
            )
        )
        return

    try:
        projection = validate_study(study_root, WorkflowRules(workflow_root))
        if not projection.events:
            raise ValueError("Study 尚未有任何 Event")
        store = AuthorityStore(authority)
        checkpoints = store.checkpoints(study_id)
        store.verify(study_id, projection.events)
    except (KeyError, OSError, ValueError, WorkflowError) as exc:
        result["errors"].append(
            _finding(
                "authority-chain-invalid",
                f"無法用指定 authority root 驗證 Study：{exc}",
                expected="Event chain 與 authority checkpoint chain 相符",
                actual=str(exc),
            )
        )
        return

    result["details"].update(
        {
            "event_count": len(projection.events),
            "event_chain_head_digest": projection.head_digest,
            "checkpoint_count": len(checkpoints),
            "checkpoint_head_digest": checkpoints[-1][2] if checkpoints else None,
            "study_authority_state": "valid",
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="檢查新 Study 的 repository-local authority root；本工具不寫入任何檔案。"
    )
    parser.add_argument("study_id")
    parser.add_argument(
        "--phase",
        choices=("new", "staged", "existing"),
        default="new",
        help=(
            "new 檢查尚未建立 research bundle 的空間；staged 檢查 research bundle 已存在但尚未有 Event；"
            "existing 驗證既有 Event/checkpoint chain。"
        ),
    )
    parser.add_argument("--repository-root", type=Path, default=repository_root())
    parser.add_argument(
        "--authority-root",
        type=Path,
        default=None,
        help="絕對或 repository-relative 路徑；正式新 Study 必須是 repository/.authority。",
    )
    args = parser.parse_args(argv)

    repository = args.repository_root.expanduser().resolve()
    authority = _resolve_path(
        repository,
        args.authority_root
        if args.authority_root is not None
        else DEFAULT_AUTHORITY_RELATIVE,
    )
    result: dict[str, Any] = {
        "command": "check-authority-root",
        "phase": args.phase,
        "study_id": args.study_id,
        "repository_root": str(repository),
        "authority_root": str(authority),
        "status": "rejected",
        "errors": [],
        "warnings": [],
        "details": {},
    }

    if STUDY_ID_PATTERN.fullmatch(args.study_id) is None:
        result["errors"].append(
            _finding(
                "invalid-study-id",
                "Study ID 必須是 3--63 個小寫英數字與連字號",
                expected="safe Study ID",
                actual=args.study_id,
            )
        )
    if not repository.is_dir():
        result["errors"].append(
            _finding(
                "repository-root-missing",
                "找不到 repository root",
                expected="directory",
                actual=str(repository),
            )
        )
    if not authority.exists():
        result["errors"].append(
            _finding(
                "authority-root-missing",
                "找不到 repository-local authority root；先建立並確認 .authority/，不要讓 writer 猜測路徑",
                expected=str(authority),
                actual="missing",
            )
        )
    elif not authority.is_dir():
        result["errors"].append(
            _finding(
                "authority-root-not-directory",
                "authority root 必須是目錄",
                expected="directory",
                actual=str(authority),
            )
        )

    if not result["errors"]:
        authority_study = _check_authority_location(repository, authority, args.study_id, result)
        if args.phase == "new":
            _check_new_study_state(repository, authority_study, args.study_id, result)
        elif args.phase == "staged":
            _check_staged_study_state(repository, authority_study, args.study_id, result)
        else:
            _check_existing_study_state(repository, authority, args.study_id, result)
        _check_git_inclusion(repository, authority, result)

    result["status"] = "passed" if not result["errors"] else "rejected"
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
