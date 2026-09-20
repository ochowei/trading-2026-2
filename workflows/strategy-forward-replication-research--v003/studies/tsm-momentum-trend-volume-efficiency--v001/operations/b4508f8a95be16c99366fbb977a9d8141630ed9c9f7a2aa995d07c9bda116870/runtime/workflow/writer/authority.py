"""簡化的本機 append-only authority store。"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from validator.canonical_yaml import canonical_bytes, canonical_digest, load_canonical
from validator.errors import IntegrityError, ValidationError
from validator.study import EventRecord


class AuthorityStore:
    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()

    def checkpoint_directory(self, study_id: str) -> Path:
        if not study_id or "/" in study_id or ".." in study_id:
            raise ValidationError("不安全的 study_id")
        return self.root / study_id / "checkpoints"

    def checkpoints(self, study_id: str) -> list[tuple[Path, dict[str, Any], str]]:
        directory = self.checkpoint_directory(study_id)
        paths = sorted(directory.glob("*.yml")) if directory.exists() else []
        results = []
        previous_digest = None
        for expected_sequence, path in enumerate(paths, start=1):
            value = load_canonical(path)
            if value["sequence"] != expected_sequence:
                raise IntegrityError("Authority checkpoint sequence 中斷")
            if value["previous_checkpoint_digest"] != previous_digest:
                raise IntegrityError("Authority checkpoint digest chain 中斷")
            digest = canonical_digest(path.read_bytes())
            results.append((path, value, digest))
            previous_digest = digest
        return results

    def prepare_checkpoint(
        self,
        study_id: str,
        sequence: int,
        event_digest: str,
        *,
        created_at: str | None = None,
    ) -> tuple[Path, bytes]:
        checkpoints = self.checkpoints(study_id)
        if len(checkpoints) != sequence - 1:
            raise IntegrityError("Authority head 與預期 event sequence 不一致")
        previous = checkpoints[-1][2] if checkpoints else None
        value = {
            "schema_version": 1,
            "study_id": study_id,
            "sequence": sequence,
            "event_digest": event_digest,
            "previous_checkpoint_digest": previous,
            "created_at": created_at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        path = self.checkpoint_directory(study_id) / f"{sequence:06d}-{event_digest}.yml"
        return path, canonical_bytes(value)

    def verify(self, study_id: str, events: list[EventRecord]) -> None:
        checkpoints = self.checkpoints(study_id)
        if len(checkpoints) != len(events):
            raise IntegrityError("Authority checkpoints 與 Study Events 數量不一致")
        for event, (_, checkpoint, _) in zip(events, checkpoints, strict=True):
            if checkpoint["event_digest"] != event.digest:
                raise IntegrityError("Authority checkpoint 與 Event digest 不一致")
