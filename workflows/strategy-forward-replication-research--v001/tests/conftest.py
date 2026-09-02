from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))


@pytest.fixture
def workflow_root(tmp_path: Path) -> Path:
    destination = tmp_path / "workflow"
    shutil.copytree(
        WORKFLOW_ROOT,
        destination,
        ignore=shutil.ignore_patterns("studies", "__pycache__", "*.pyc"),
    )
    return destination
