"""正式與合成執行共用的啟動器；每次只給 runner 一份 request 與輸出位置。"""

from __future__ import annotations

import argparse
import os
import runpy
import sys
import zoneinfo
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("runner")
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    output = Path(args.output).resolve().parent
    runtime = Path(sys.base_prefix).resolve()
    environment = Path(sys.prefix).resolve()
    timezones = tuple(Path(path).resolve() for path in zoneinfo.TZPATH)

    def inside(path: Path, parent: Path) -> bool:
        return path == parent or parent in path.parents

    def audit(event: str, values: tuple) -> None:
        if event.startswith("socket.") or event in {
            "subprocess.Popen",
            "os.system",
            "os.posix_spawn",
        }:
            raise PermissionError("runner 不得連網或啟動外部程序")
        if event == "open" and not isinstance(values[0], int):
            path = Path(os.fsdecode(values[0])).resolve()
            mode, flags = values[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT)
            )
            if writing:
                if not inside(path, output):
                    raise PermissionError(f"runner 只能寫入輸出目錄：{path}")
            elif not any(
                inside(path, parent) for parent in (root, runtime, environment, *timezones)
            ):
                if str(path) not in {"/dev/null", "/dev/urandom", "/etc/localtime"}:
                    raise PermissionError(f"runner 讀取隔離範圍外檔案：{path}")
        if event in {"os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.link", "os.symlink"}:
            for item in (
                values[:2] if event in {"os.rename", "os.link", "os.symlink"} else values[:1]
            ):
                if isinstance(item, (str, bytes)) and not inside(
                    Path(os.fsdecode(item)).resolve(), output
                ):
                    raise PermissionError("runner 不得修改輸出目錄外的檔案")

    sys.addaudithook(audit)
    sys.argv = [args.runner, "--request", args.request, "--output", args.output]
    runpy.run_path(args.runner, run_name="__main__")


if __name__ == "__main__":
    main()
