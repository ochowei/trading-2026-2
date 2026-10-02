"""只在 Repo 外建立人造設定；不建立 Study、authority 或 Release。"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(PACKAGE / "tests"))
from synthetic_helpers import make_context  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="建立可重現的 v006 人造診斷設定")
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument(
        "--original-warmup",
        action="store_true",
        help="保留原公開候選的 25 日暖機，展示原生契約拒絕",
    )
    args = parser.parse_args()
    directory = args.directory.resolve()
    repository = PACKAGE.parents[1]
    if directory == repository or repository in directory.parents or directory.exists():
        parser.error("請使用 Repo 外、尚不存在的人造暫存目錄")
    context = make_context(directory, ready=not args.original_warmup)
    # 只複製明列的公開定義目錄，不帶 runtime、Study 或 Workflow Release。
    package_copy = directory / "workflows" / PACKAGE.name
    for name in (
        "rules",
        "schemas",
        "validator",
        "writer",
        "operations",
        "tests",
        "examples",
        "reference",
        "policies",
        "tools",
    ):
        for source in (PACKAGE / name).rglob("*"):
            if not source.is_file() or "__pycache__" in source.parts or source.suffix == ".pyc":
                continue
            destination = package_copy / source.relative_to(PACKAGE)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    for name in ("README.md", "workflow.yml", "IMPLEMENTATION-PLAN.md"):
        if (PACKAGE / name).exists():
            shutil.copyfile(PACKAGE / name, package_copy / name)
    print(
        json.dumps(
            {
                "repository_root": str(directory),
                "setting_id": context.study_id,
                "synthetic_only": True,
                "study_created": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
