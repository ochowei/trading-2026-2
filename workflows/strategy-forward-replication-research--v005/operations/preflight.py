"""隔離執行 frozen runner，驗證 raw evidence；報告不具有研究或授權效力。"""

from __future__ import annotations

import csv
import importlib.metadata
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from validator.artifacts import evaluate_historical
from validator.assignments import DEVELOPER, safe_path
from validator.canonical_yaml import (
    atomic_create,
    canonical_bytes,
    canonical_digest,
    load_canonical,
)
from validator.errors import IntegrityError, ValidationError
from validator.paths import resolve_inside
from validator.schema_validation import SchemaStore
from validator.workflow_reference import build_workflow_reference, reference_digest

from operations.multi_asset import validate_assets

FORBIDDEN = {".super-admin", ".project-manager", "historical-evaluation-artifacts", "studies"}
PACKAGE = Path(__file__).resolve().parents[1]


def source_files(repository: Path, bundle: dict) -> dict[str, Path]:
    result = {}
    for item in bundle["files"]:
        relative = item["path"]
        if FORBIDDEN.intersection(Path(relative).parts) or Path(relative).suffix not in {
            ".py",
            ".yml",
            ".yaml",
            ".toml",
            ".txt",
            ".lock",
        }:
            raise ValidationError(f"preflight 不接受資料或受限來源：{relative}")
        path = resolve_inside(repository, relative)
        if FORBIDDEN.intersection(path.relative_to(repository.resolve()).parts):
            raise ValidationError("Source Bundle 解析到受限路徑")
        if canonical_digest(path.read_bytes()) != item["digest"]:
            raise IntegrityError(
                f"Source Bundle drift：{relative}",
                path=path,
                expected=item["digest"],
                actual=canonical_digest(path.read_bytes()),
            )
        if relative in result:
            raise ValidationError("Source Bundle 路徑重複")
        result[relative] = path
    return result


def environment_identity() -> dict:
    return {
        "python": sys.version,
        "executable": str(Path(sys.executable).resolve()),
        "executable_digest": canonical_digest(Path(sys.executable).read_bytes()),
        "packages": sorted(
            f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()
        ),
    }


def binding(repository: Path, study_id: str, authority: Path, package: Path = PACKAGE) -> dict:
    if re.fullmatch(r"[a-z0-9][a-z0-9-]{2,62}", study_id) is None:
        raise ValidationError("不安全的 Study ID")
    research = safe_path(repository / "research" / study_id, repository, DEVELOPER)
    reference = build_workflow_reference(package, repository, allow_draft=True)
    bundle = load_canonical(safe_path(research / "source-bundle.yml", repository, DEVELOPER))
    files = source_files(repository, bundle)
    settings = {}
    for name in (
        "source-bundle.yml",
        "preregistration.yml",
        "qualification-spec.yml",
        "candidate-definition.yml",
        "development-trial-inputs.yml",
        "implementation-contract.yml",
        "runner-contract.yml",
    ):
        path = safe_path(research / name, repository, DEVELOPER)
        settings[name] = canonical_digest(path.read_bytes())
    for path in sorted((research / "trial-inputs").glob("*.yml")):
        safe_path(path, repository, DEVELOPER)
        settings[path.relative_to(research).as_posix()] = canonical_digest(path.read_bytes())
    contract_path = f"research/{study_id}/runner-contract.yml"
    if contract_path not in files:
        raise ValidationError("runner-contract 必須被 Source Bundle 綁定")
    return {
        "study_id": study_id,
        "repository": str(repository.resolve()),
        "authority_root": str(authority.resolve()),
        "settings": settings,
        "source_bundle": bundle,
        "environment": environment_identity(),
        "workflow_digest": reference["workflow_digest"],
        "workflow_reference": reference,
        "workflow_reference_digest": reference_digest(reference),
    }


def synthetic_csv(recipe: dict) -> bytes:
    """只由明列的合成數列產生資料；不開啟資料來源或既有市場檔案。"""
    rows = recipe["rows"]
    if not isinstance(rows, list) or not rows:
        raise ValidationError("合成案例必須有 OHLCV rows")
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["Date", "Open", "High", "Low", "Close", "Volume"])
    for row in rows:
        if not isinstance(row, list) or len(row) != 6:
            raise ValidationError("合成 row 必須包含日期與五個 OHLCV 數值")
        writer.writerow(row)
    return stream.getvalue().encode()


def launch(repository: Path, package: Path, runner: str, request: Path, output: Path) -> None:
    """正式與 preflight 必須使用同一函式、argv、cwd 與 Python 環境。"""
    env = {
        "PATH": os.defpath,
        "PYTHONPATH": os.pathsep.join(map(str, (package, repository, repository / "src"))),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "HOME": str(output.parent),
        "TMPDIR": str(output.parent),
    }
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "operations.launch",
            runner,
            "--request",
            str(request),
            "--output",
            str(output),
        ],
        cwd=repository,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if process.returncode:
        raise ValidationError(f"runner 執行失敗 ({process.returncode})：{process.stderr[-6000:]}")
    if not output.is_file():
        raise ValidationError("runner 未產生 evidence")


def validate_output(
    value: dict, stage: str, prereg: dict, inputs: dict, bundle: dict, package: Path
) -> dict:
    if stage == "development":
        from operations.publication import validate_envelope

        return validate_envelope(value, inputs, prereg, canonical_digest(bundle))
    SchemaStore(package / "schemas").validate("historical-evaluation.schema.yml", value)
    if value["initial_cash"] != prereg["initial_cash"]:
        raise IntegrityError("Historical runner initial_cash 與事前登記不一致")
    _, failures = evaluate_historical(
        value,
        prereg["evaluation_gates"],
        fold_warmup_sessions=prereg["fold_warmup_sessions"],
        maximum_holding_sessions=prereg["maximum_holding_sessions"],
    )
    return {"candidate": {"trades": len(value["trades"]), "failed_gates": failures}}


def runner_preflight(
    repository: Path, study_id: str, authority: Path, package: Path = PACKAGE
) -> dict:
    before = binding(repository, study_id, authority, package)
    research = repository / "research" / study_id
    contract = load_canonical(research / "runner-contract.yml")
    SchemaStore(package / "schemas").validate("runner-contract.schema.yml", contract)
    if (
        contract.get("protocol") != "request-output-v1"
        or contract.get("synthetic_only") is not True
    ):
        raise ValidationError("runner contract 必須明示固定介面與純合成資料")
    cases = contract["cases"]
    if {c["stage"] for c in cases} != {"development", "historical-evaluation"}:
        raise ValidationError("必須驗證兩種正式 runner")
    for stage in ("development", "historical-evaluation"):
        if not {"trades", "no-trades"}.issubset(
            {c["expect"] for c in cases if c["stage"] == stage}
        ):
            raise ValidationError("每個 runner 都必須涵蓋有交易與無交易")
    files = source_files(repository, before["source_bundle"])
    for runner in contract["runners"].values():
        if runner not in files or Path(runner).suffix != ".py":
            raise ValidationError("正式 runner 必須綁定於 Source Bundle")
    records = []
    development_outputs = []
    with tempfile.TemporaryDirectory(prefix="runner-preflight-") as temp:
        isolated = Path(temp) / "repository"
        isolated.mkdir()
        staged_package = isolated / "workflows" / package.name
        shutil.copytree(
            package,
            staged_package,
            ignore=shutil.ignore_patterns(
                "studies", "__pycache__", "release-manifest.yml", "release-test-report.yml"
            ),
        )
        for relative, source in files.items():
            destination = isolated / relative
            if destination.exists():
                raise ValidationError("Source Bundle 不得覆蓋 Workflow Package")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        prereg = load_canonical(research / "preregistration.yml")
        all_inputs = [
            load_canonical(research / "development-trial-inputs.yml"),
            *[load_canonical(path) for path in sorted((research / "trial-inputs").glob("*.yml"))],
        ]
        ids = [inputs["candidate_id"] for inputs in all_inputs]
        if len(ids) != len(set(ids)) or set(ids) != set(prereg["complete_candidate_family"]):
            raise ValidationError("prepare inputs 必須完整且唯一對應預先登記 Candidate Family")
        for inputs in all_inputs:
            assets = inputs.get("data_bindings", {}).get("assets")
            if assets is None:
                continue
            roster = [(asset["asset_id"], asset["use"]) for asset in assets]
            covered = {
                case["expect"] for case in cases
                if case["stage"] == "development" and "assets" in case
                and [(asset["asset_id"], asset["use"]) for asset in case["assets"]] == roster
            }
            if covered != {"trades", "no-trades"}:
                raise ValidationError("多資產 runner preflight 須以相同資產清單涵蓋有交易與無交易")
        runs = [(case, inputs) for inputs in all_inputs for case in cases]
        for index, (case, inputs) in enumerate(runs):
            output_root = isolated / "runs" / str(index)
            output_root.mkdir(parents=True)
            request = {
                "stage": case["stage"],
                "preregistration": prereg,
                "trial_inputs": inputs,
                "source_bundle": before["source_bundle"],
            }
            if "assets" in case:
                if case["stage"] != "development":
                    raise ValidationError("多資產合成案例只用於 Development")
                asset_dir = output_root / "assets"
                asset_dir.mkdir()
                assets = []
                for item in case["assets"]:
                    data = synthetic_csv(item)
                    path = asset_dir / f"{item['asset_id']}.csv"
                    path.write_bytes(data)
                    assets.append({
                        "asset_id": item["asset_id"], "use": item["use"],
                        "provider": "synthetic", "symbol": item["asset_id"],
                        "data_path": path.relative_to(isolated).as_posix(),
                        "data_digest": canonical_digest(data),
                        "start_date": item["rows"][0][0],
                        "end_date": item["rows"][-1][0],
                        "timezone": "America/New_York",
                        "available_at": "after-close",
                        "interval_role": "warmup-development",
                    })
                validate_assets(isolated, assets, load_canonical(staged_package / "workflow.yml")["data_intervals"]["intervals"])
                request["data_assets"] = assets
                request["availability_policy"] = "after-close-next-session"
                data_digest = canonical_digest(
                    [{"asset_id": asset["asset_id"], "digest": asset["data_digest"]} for asset in assets]
                )
            else:
                data = synthetic_csv(case)
                data_path = output_root / "bars.csv"
                data_path.write_bytes(data)
                request["data_path"] = str(data_path.relative_to(isolated))
                request["data_digest"] = canonical_digest(data)
                data_digest = canonical_digest(data)
            SchemaStore(staged_package / "schemas").validate("runner-request.schema.yml", request)
            request_path = output_root / "request.yml"
            request_path.write_bytes(canonical_bytes(request))
            output = output_root / "evidence.yml"
            launch(
                isolated, staged_package, contract["runners"][case["stage"]], request_path, output
            )
            value = load_canonical(output)
            result = validate_output(
                value, case["stage"], prereg, inputs, before["source_bundle"], staged_package
            )
            if case["stage"] == "development":
                development_outputs.append((value, inputs))
            count = result["candidate"]["trades"]
            if (case["expect"] == "no-trades" and count != 0) or (
                case["expect"] == "trades" and count == 0
            ):
                raise ValidationError("合成案例未觸發要求的交易分支")
            for key in case.get("required_output_keys", []):
                current = value
                for part in key.split("."):
                    current = current[part]
            records.append(
                {
                    "case": index,
                    "stage": case["stage"],
                    "expect": case["expect"],
                    "data_digest": data_digest,
                    **({"data_assets": [
                        {"asset_id": asset["asset_id"], "digest": asset["data_digest"]}
                        for asset in assets
                    ]} if "assets" in case else {}),
                    "request_digest": canonical_digest(request),
                    "evidence_digest": canonical_digest(value),
                    "validation": result,
                }
            )
        # 合成執行也走正式建立／發布／Trial validator，僅存在 TemporaryDirectory。
        from writer.service import StudyService

        from operations.publication import consume
        from operations.service import create

        for number, (envelope, inputs) in enumerate(development_outputs):
            consumer_repository = isolated / "consumer" / str(number)
            consumer_package = consumer_repository / "workflows" / package.name
            consumer_package.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(staged_package, consumer_package)
            for name in before["settings"]:
                destination = consumer_repository / "research" / study_id / name
                if not destination.exists():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes((research / name).read_bytes())
            for relative, source in source_files(repository, before["source_bundle"]).items():
                destination = consumer_repository / relative
                if destination.exists():
                    if destination.read_bytes() != source.read_bytes():
                        raise IntegrityError("Source Bundle 在 consumer 中內容不一致")
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
            consumer_authority = consumer_repository / ".authority"
            service = StudyService(
                consumer_package,
                consumer_authority,
                repository_root=consumer_repository,
                allow_draft=True,
                actor="synthetic-fixture",
                role=DEVELOPER,
                assignment={
                    "schema_version": 1,
                    "source_id": "prepare-synthetic-consumer",
                    "instruction": "僅驗證合成 fixture 的登記與 Trial 發布",
                    "assigner": "preflight-test-harness",
                    "assignee": "synthetic-fixture",
                    "role": DEVELOPER,
                    "study_id": study_id,
                    "workflow_version": "v005",
                    "scope": "development-to-freeze",
                },
            )
            report = {
                "schema_version": 1,
                "status": "passed",
                "prepare_checks": "passed",
                "binding": binding(
                    consumer_repository, study_id, consumer_authority, consumer_package
                ),
                "cases": records,
            }

            plan = {
                "study_id": study_id,
                "creator": "synthetic-fixture",
                "identity": {
                    "research_round_id": "synthetic-only",
                    "experiment_family": "synthetic-candidate",
                    "research_owner": "synthetic-fixture",
                    "historical_evaluation_operator": "synthetic-fixture",
                },
                "preregistration": prereg,
                "development_actor": "synthetic-fixture",
            }
            create(service, plan, report)
            payload = consume(
                service,
                study_id,
                envelope,
                inputs,
                prereg,
                canonical_digest(before["source_bundle"]),
            )
            service.append_event(study_id, "trial-recorded", "synthetic-fixture", payload)
            service.validate(study_id)
    if binding(repository, study_id, authority, package) != before:
        raise IntegrityError("preflight 執行期間 source、設定或環境發生變化")
    return {"schema_version": 1, "status": "passed", "binding": before, "cases": records}


def verify_report(
    report: dict, repository: Path, study_id: str, authority: Path, package: Path = PACKAGE
) -> None:
    SchemaStore(package / "schemas").validate("runner-report.schema.yml", report)
    if report.get("status") != "passed" or report.get("prepare_checks") != "passed":
        raise ValidationError("create 需要完整 prepare 通過報告")
    current = binding(repository, study_id, authority, package)
    if report["binding"] != current:
        raise IntegrityError(
            "prepare 報告已過期；source、設定、工具或環境改變",
            path=repository / "research" / study_id,
            expected=report["binding"],
            actual=current,
        )
    if not report.get("cases"):
        raise ValidationError("prepare 報告缺少 runner evidence 驗證")


def save_report(path: Path, report: dict) -> None:
    atomic_create(path, canonical_bytes(report))
