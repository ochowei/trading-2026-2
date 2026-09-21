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
        ignore=shutil.ignore_patterns(
            "studies",
            "__pycache__",
            "*.pyc",
            "release-manifest.yml",
            "release-test-report.yml",
        ),
    )
    from validator.canonical_yaml import canonical_bytes
    from validator.release import build_release_manifest

    manifest = build_release_manifest(destination)
    report = {
        "schema_version": 1,
        "workflow": "strategy-forward-replication-research",
        "workflow_version": "v004",
        "generated_at": "2000-01-01T00:00:00.000000Z",
        "status": "release-candidate",
        "release_record_created": False,
        "checks": [{"command": "isolated fixture", "result": "passed", "summary": "僅測試用"}],
    }
    (destination / "release-manifest.yml").write_bytes(canonical_bytes(manifest))
    (destination / "release-test-report.yml").write_bytes(canonical_bytes(report))
    return destination
