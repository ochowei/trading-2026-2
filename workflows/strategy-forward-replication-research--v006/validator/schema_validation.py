"""JSON Schema（以 YAML 保存）驗證。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .canonical_yaml import load_canonical
from .errors import ValidationError

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
format_checker = FormatChecker()


@format_checker.checks("sha256")
def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


class SchemaStore:
    def __init__(self, schema_root: Path | str):
        self.schema_root = Path(schema_root)

    def schema(self, name: str) -> dict[str, Any]:
        path = self.schema_root / name
        value = load_canonical(path)
        if not isinstance(value, dict):
            raise ValidationError(f"Schema 必須是 mapping: {path}")
        return value

    def validate(self, name: str, value: Any) -> None:
        validator = Draft202012Validator(self.schema(name), format_checker=format_checker)
        errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
        if not errors:
            return
        details = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "$"
            details.append(f"{location}: {error.message}")
        raise ValidationError("Schema validation failed:\n" + "\n".join(details))
