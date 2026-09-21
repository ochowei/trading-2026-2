"""離線驗證 Package 定義與 Release Candidate，完全不存取 Study/store。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
from jsonschema import Draft202012Validator  # noqa: E402
from validator.canonical_yaml import load_canonical  # noqa: E402
from validator.release import (  # noqa: E402
    definition_files,
    policy_set_digest,
    validate_release_manifest,
)
from validator.schema_validation import SchemaStore  # noqa: E402


def verify(package=PACKAGE, *, candidate=False):
    schemas = SchemaStore(package / "schemas")
    files = definition_files(package)
    for path in files:
        if path.suffix == ".yml":
            value = load_canonical(path)
            if path.parent == package / "schemas":
                Draft202012Validator.check_schema(value)
    schemas.validate("workflow.schema.yml", load_canonical(package / "workflow.yml"))
    policy_set_digest(package)
    if candidate:
        manifest = validate_release_manifest(package)
        schemas.validate(
            "release-test-report.schema.yml", load_canonical(package / "release-test-report.yml")
        )
        if (package / "release.yml").exists():
            raise ValueError("本次交付不得建立正式 release.yml")
        return {
            "status": "release-candidate",
            "workflow_digest": manifest["workflow_digest"],
            "files": len(files),
            "release_record_created": False,
        }
    return {"status": "definitions-passed", "files": len(files)}


def main():
    parser = argparse.ArgumentParser(description="v004 定義／Release Candidate 驗證")
    parser.add_argument("--candidate", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(candidate=args.candidate), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
