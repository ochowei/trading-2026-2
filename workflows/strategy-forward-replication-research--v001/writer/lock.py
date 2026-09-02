"""每個 Study 一把簡單 filesystem lock。"""

from __future__ import annotations

import os
from pathlib import Path

from validator.errors import IntegrityError


class StudyLock:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.fd: int | None = None

    def __enter__(self) -> StudyLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise IntegrityError(f"Study 已被另一個 writer 鎖定: {self.path}") from exc
        os.write(self.fd, str(os.getpid()).encode("ascii"))
        os.fsync(self.fd)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        self.path.unlink(missing_ok=True)
