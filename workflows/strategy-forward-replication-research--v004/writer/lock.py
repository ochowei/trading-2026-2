"""OS 持鎖；固定 inode，同執行緒巢狀 writer 共用一把鎖。"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from validator.errors import IntegrityError

_state = threading.local()


class StudyLock:
    def __init__(self, path: Path | str):
        self.path = Path(path).resolve()
        self.key = str(self.path)

    def __enter__(self):
        import fcntl

        if getattr(_state, "pid", None) != os.getpid():
            _state.pid, _state.held = os.getpid(), {}
        held = _state.held
        if self.key in held:
            held[self.key][1] += 1
            return self
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(fd)
            raise IntegrityError(f"Study 已被另一個 writer 鎖定: {self.path}") from exc
        os.ftruncate(fd, 0)
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.fsync(fd)
        held[self.key] = [fd, 1]
        return self

    def __exit__(self, exc_type, exc, traceback):
        import fcntl

        entry = _state.held[self.key]
        entry[1] -= 1
        if entry[1] == 0:
            fcntl.flock(entry[0], fcntl.LOCK_UN)
            os.close(entry[0])
            del _state.held[self.key]
        # 不 unlink：所有競爭者必須鎖定同一 inode。
