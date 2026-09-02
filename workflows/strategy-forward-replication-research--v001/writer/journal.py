"""以 prepared journal 發布 event 與 authority checkpoint。"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from validator.canonical_yaml import (
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.errors import IntegrityError


class JournalPublisher:
    def __init__(self, study_root: Path | str, authority_root: Path | str):
        self.study_root = Path(study_root)
        self.authority_root = Path(authority_root).resolve()

    def _journal_value(
        self,
        event_path: Path,
        event_bytes: bytes,
        checkpoint_path: Path,
        checkpoint_bytes: bytes,
    ) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "event_path": event_path.relative_to(self.study_root).as_posix(),
            "event_bytes_base64": base64.b64encode(event_bytes).decode("ascii"),
            "checkpoint_path": checkpoint_path.relative_to(self.authority_root).as_posix(),
            "checkpoint_bytes_base64": base64.b64encode(checkpoint_bytes).decode("ascii"),
        }

    def publish(
        self,
        event_path: Path,
        event_bytes: bytes,
        checkpoint_path: Path,
        checkpoint_bytes: bytes,
    ) -> str:
        journal = self._journal_value(event_path, event_bytes, checkpoint_path, checkpoint_bytes)
        operation_id = canonical_digest(journal)
        journal_dir = self.study_root / "journals"
        prepared_path = journal_dir / f"{operation_id}.prepared.yml"
        completed_path = journal_dir / f"{operation_id}.completed.yml"
        atomic_create(prepared_path, canonical_bytes(journal))
        self._complete(journal)
        atomic_create(
            completed_path,
            canonical_bytes({"schema_version": 1, "operation_id": operation_id}),
        )
        return operation_id

    def _complete(self, journal: dict[str, Any]) -> None:
        event_path = self.study_root / journal["event_path"]
        checkpoint_path = self.authority_root / journal["checkpoint_path"]
        event_bytes = base64.b64decode(journal["event_bytes_base64"], validate=True)
        checkpoint_bytes = base64.b64decode(journal["checkpoint_bytes_base64"], validate=True)
        atomic_create(event_path, event_bytes)
        atomic_create(checkpoint_path, checkpoint_bytes)

    def recover(self) -> list[str]:
        recovered: list[str] = []
        journal_dir = self.study_root / "journals"
        if not journal_dir.exists():
            return recovered
        for prepared_path in sorted(journal_dir.glob("*.prepared.yml")):
            operation_id = prepared_path.name.removesuffix(".prepared.yml")
            completed_path = journal_dir / f"{operation_id}.completed.yml"
            if completed_path.exists():
                continue
            journal = load_canonical(prepared_path)
            if canonical_digest(journal) != operation_id:
                raise IntegrityError("Prepared journal identity 不正確")
            self._complete(journal)
            atomic_create(
                completed_path,
                canonical_bytes({"schema_version": 1, "operation_id": operation_id}),
            )
            recovered.append(operation_id)
        return recovered
