"""Artifact path 邊界檢查。"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from .errors import ValidationError


def validate_repository_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValidationError(f"不安全的 repository-relative path: {value!r}")
    if "latest" in {part.lower() for part in path.parts}:
        raise ValidationError(f"禁止 mutable latest pointer: {value!r}")
    return path


def is_within_repository_path(value: str, root: str) -> bool:
    """判斷一個 repository-relative path 是否位於指定根目錄下。"""

    path = validate_repository_relative_path(value)
    base = validate_repository_relative_path(root)
    return path.parts[: len(base.parts)] == base.parts


def resolve_inside(root: Path | str, value: str, *, must_exist: bool = True) -> Path:
    relative = validate_repository_relative_path(value)
    base = Path(root).resolve()
    candidate = (base / Path(*relative.parts)).resolve(strict=must_exist)
    if candidate != base and base not in candidate.parents:
        raise ValidationError(f"路徑逃逸 repository root: {value!r}")
    return candidate


def resolve_historical_evaluation_artifact(
    study_root: Path | str,
    repository_root: Path | str,
    store_relative_path: str,
    value: str,
    *,
    must_exist: bool = True,
) -> Path:
    """解析位於 repository 根目錄 Historical Evaluation store 的 artifact。

    外部 store 的路徑仍以 repository-relative path 記錄，但只能指向目前 Study
    的子目錄，避免某個 Study 引用另一個 Study 的正式結果。
    """

    relative = validate_repository_relative_path(value)
    store = validate_repository_relative_path(store_relative_path)
    if relative.parts[: len(store.parts)] != store.parts:
        raise ValidationError(
            f"Historical Evaluation artifact 必須位於 {store.as_posix()}/ 下: {value!r}"
        )

    study_id = Path(study_root).name
    study_prefix = store.parts + (study_id,)
    if (
        len(relative.parts) <= len(study_prefix)
        or relative.parts[: len(study_prefix)] != study_prefix
    ):
        raise ValidationError(
            "Historical Evaluation artifact 必須位於目前 Study 的 store 子目錄內"
        )

    return resolve_inside(repository_root, relative.as_posix(), must_exist=must_exist)
