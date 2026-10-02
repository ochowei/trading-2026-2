"""只做原生人造案例診斷與輸出，不建立 Study 或執行其生命週期。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validator.canonical_yaml import atomic_create, canonical_bytes
from validator.synthetic_report import build_synthetic_report

from operations.legacy_checks import StudyContext, run_synthetic

PACKAGE = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="v006 合成指標與成交契約診斷")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--study-id", required=True, help="人造 research 設定資料夾名稱")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        from operations.legacy_checks import STUDY_ID_PATTERN

        if STUDY_ID_PATTERN.fullmatch(args.study_id) is None:
            raise ValueError("診斷設定名稱不合法")
        report_path = args.report.resolve()
        if PACKAGE == report_path or PACKAGE in report_path.parents:
            raise ValueError("診斷報告須存於 Package 外，不能混入 Draft 定義")
        check = run_synthetic(StudyContext(args.repository_root.resolve(), PACKAGE, args.study_id))
        if "binding" not in check.details:
            print(
                json.dumps(
                    check.as_dict(
                        StudyContext(args.repository_root.resolve(), PACKAGE, args.study_id)
                    ),
                    ensure_ascii=False,
                )
            )
            return 1
        report = build_synthetic_report(
            check.as_dict(StudyContext(args.repository_root.resolve(), PACKAGE, args.study_id)),
            check.details["binding"],
            PACKAGE,
        )
        atomic_create(report_path, canonical_bytes(report))
        print(
            json.dumps(
                {
                    "status": check.status,
                    "report": str(report_path),
                    "report_digest": report["report_digest"],
                    "warnings": check.warnings,
                },
                ensure_ascii=False,
            )
        )
        return 0 if check.status == "passed" else 1
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
