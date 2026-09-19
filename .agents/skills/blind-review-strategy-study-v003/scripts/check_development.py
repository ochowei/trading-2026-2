#!/usr/bin/env python3
"""v003 唯讀 Development 檢查：不讀事件、projection 或正式結果。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WORKFLOW = "strategy-forward-replication-research--v003"
IDENTIFIER = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}\Z")


def safe_file(root, relative):
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("不接受絕對路徑或路徑逃逸")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("不接受 symlink")
    if root not in current.resolve().parents:
        raise ValueError("路徑超出指定範圍")
    return current


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", help="唯一的 v003 Study ID 或直接 Study 目錄")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--role", choices=["study 開發者", "超級管理者"], required=True)
    parser.add_argument("--outcome-exposed", action="store_true")
    parser.add_argument("--formal-evaluation-exposed", action="store_true")
    parser.add_argument("--outcome-bearing-terminal-exposed", action="store_true")
    args = parser.parse_args()
    result = {
        "workflow_version": "v003",
        "historical_evaluation_status": "not_inspected",
        "study_terminal_status": "not_inspected",
        "candidate_freeze_status": "尚不能判斷",
        "read_files": [],
        "attempted_files": [],
        "full_chain_validated": False,
    }
    if (
        args.outcome_exposed
        or args.formal_evaluation_exposed
        or args.outcome_bearing_terminal_exposed
    ):
        print(
            json.dumps(
                {
                    **result,
                    "status": "rejected",
                    "blind_review_status": "blocked-by-exposed-outcome",
                },
                ensure_ascii=False,
            )
        )
        return 2
    try:
        repo = args.repository_root.expanduser().resolve(strict=True)
        package = safe_file(repo, f"workflows/{WORKFLOW}")
        studies = safe_file(repo, f"workflows/{WORKFLOW}/studies")
        supplied = Path(args.study)
        if IDENTIFIER.fullmatch(args.study):
            name = args.study
        else:
            supplied = supplied if supplied.is_absolute() else repo / supplied
            if supplied.parent != studies or ".." in supplied.parts:
                raise ValueError("只接受 v003 studies 的直接子目錄")
            name = supplied.name
        if not IDENTIFIER.fullmatch(name):
            raise ValueError("Study ID 格式不合法")
        study = safe_file(studies, name)
        if not study.is_dir():
            raise ValueError("指定 Study 不存在或不是目錄")
        # 每次獨立 process 僅載入 v003；不 import v001 的共用 status tool。
        sys.path.insert(0, str(package))
        from operations.publication import validate_envelope
        from validator.canonical_yaml import canonical_digest, load_canonical
        from validator.qualification import assess
        from validator.schema_validation import SchemaStore

        def read(relative):
            path = safe_file(study, relative)
            result["attempted_files"].append(path.relative_to(repo).as_posix())
            value = load_canonical(path)
            result["read_files"].append(path.relative_to(repo).as_posix())
            return value

        result.update(
            study_id=name,
            study_root=str(study),
            status="eligible",
            blind_review_status="eligible",
            blind_review_eligibility_basis="explicit-outcome-exposure-only",
        )
        try:
            prereg = read("manifests/preregistration.yml")
            bundle = read("manifests/source-bundle.yml")
            schemas = SchemaStore(package / "schemas")
            schemas.validate("preregistration.schema.yml", prereg)
            schemas.validate("source-bundle.schema.yml", bundle)
        except Exception as error:
            result.update(
                development_evidence_validity="unavailable",
                blind_review_status="eligible-with-development-evidence-unavailable",
                limitation=f"缺少或無法驗證規格：{error}",
                trials={},
            )
        else:
            trials = {}
            for trial in prereg["complete_candidate_family"]:
                if not IDENTIFIER.fullmatch(trial):
                    raise ValueError("不安全的 Trial ID")
                prefix = f"evidence/trials/{trial}"
                try:
                    manifest = read(f"{prefix}/publication.yml")
                    schemas.validate("development-publication.schema.yml", manifest)
                    if (
                        manifest["study_id"] != name
                        or manifest["trial_id"] != trial
                        or manifest["source_bundle_digest"] != canonical_digest(bundle)
                        or manifest["preregistration_digest"] != canonical_digest(prereg)
                    ):
                        raise ValueError("publication 與 Study／規格綁定不一致")
                    values = {}
                    for kind in ("candidate", "baseline", "inputs"):
                        ref = manifest["artifacts"][kind]
                        expected = f"{prefix}/{kind}.yml"
                        if ref["path"] != expected:
                            raise ValueError("publication 引用不在固定的 Development 白名單")
                        values[kind] = read(expected)
                        if canonical_digest(values[kind]) != ref["digest"]:
                            raise ValueError(f"{kind} digest 不一致")
                    envelope = {kind: values[kind] for kind in ("candidate", "baseline")}
                    if canonical_digest(envelope) != manifest["envelope_digest"]:
                        raise ValueError("envelope digest 不一致")
                    if values["inputs"].get("candidate_id") != trial:
                        raise ValueError("Trial inputs identity 不一致")
                    validate_envelope(envelope, values["inputs"], prereg, canonical_digest(bundle))
                    trials[trial] = {
                        "evidence_validity": "valid",
                        "assessment": assess(values["candidate"], prereg),
                    }
                except Exception as error:
                    trials[trial] = {"evidence_validity": "unavailable", "reason": str(error)}
            result["trials"] = trials
            valid = sum(value["evidence_validity"] == "valid" for value in trials.values())
            result["development_evidence_validity"] = (
                "valid"
                if valid == len(trials) and trials
                else "partial"
                if valid
                else "unavailable"
            )
            if not valid:
                result["blind_review_status"] = "eligible-with-development-evidence-unavailable"
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as error:
        print(
            json.dumps({**result, "status": "rejected", "reason": str(error)}, ensure_ascii=False)
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
