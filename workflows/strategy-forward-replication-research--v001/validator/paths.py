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


def resolve_inside(root: Path | str, value: str, *, must_exist: bool = True) -> Path:
    relative = validate_repository_relative_path(value)
    base = Path(root).resolve()
    candidate = (base / Path(*relative.parts)).resolve(strict=must_exist)
    if candidate != base and base not in candidate.parents:
        raise ValidationError(f"路徑逃逸 repository root: {value!r}")
    return candidate
