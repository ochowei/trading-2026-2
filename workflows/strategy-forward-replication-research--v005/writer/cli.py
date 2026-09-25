"""writer CLI 共用派工與角色檢查入口。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from operations.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
