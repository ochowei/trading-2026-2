from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "tsm-mean-reversion-volume-leads--v002"
PRECREATE_STUDY_ID = "tsm-mean-reversion-reversal-trigger--v002"
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import canonical_bytes, canonical_digest, load_canonical  # noqa: E402

from research.tools.studyctl import (  # noqa: E402
    _derived_history_sessions,
    context_for,
    run_contract,
    run_diagnose,
    run_identity,
    run_precreate,
    run_synthetic,
)


def test_identity_detects_copy_forwarded_research_path() -> None:
    result = run_identity(context_for(REPOSITORY_ROOT, STUDY_ID))

    assert result.status == "failed"
    assert any(item["code"] == "stale-research-path" for item in result.errors)


def test_contract_detects_missing_indicator_contract_and_short_warmup() -> None:
    result = run_contract(context_for(REPOSITORY_ROOT, STUDY_ID))
    codes = {item["code"] for item in result.errors}

    assert "indicator-contract-missing" in codes
    assert "fold-warmup-too-short" in codes
    assert result.details["derived_required_history_sessions"] == 25


def test_history_boundary_uses_prior_volume_window() -> None:
    values = {
        "sma_lookback": 20,
        "rsi_lookback": 2,
        "volume_lookback": 20,
        "volume_lead_window": 5,
    }

    assert _derived_history_sessions(values, None) == 25


def _precreate_repository(tmp_path: Path) -> tuple[Path, Path]:
    """建立沒有 Study Event、但含有完整 research/source fixture 的暫存 repository。"""

    research_root = tmp_path / "research" / PRECREATE_STUDY_ID
    shutil.copytree(
        REPOSITORY_ROOT / "research" / "tsm-mean-reversion-reversal-trigger--v002",
        research_root,
    )
    # precreate 現在把 Trial identity 視為建立前的必要 binding；這個舊 fixture
    # 原本沒有 trial_id，測試先補成完整的 staged research bundle。
    trial_path = research_root / "development-trial-inputs.yml"
    trial_inputs = load_canonical(trial_path)
    trial_inputs["trial_id"] = "trial-tsm-mr-volume-lead-upclose-v002"
    _write_yaml(trial_path, trial_inputs)
    source_bundle = load_canonical(research_root / "source-bundle.yml")
    for item in source_bundle["files"]:
        source = REPOSITORY_ROOT / item["path"]
        destination = tmp_path / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return tmp_path, research_root


def _write_yaml(path: Path, value: dict[str, object]) -> None:
    path.write_bytes(canonical_bytes(value))


def test_precreate_passes_without_a_study_event(tmp_path: Path) -> None:
    repository_root, research_root = _precreate_repository(tmp_path)

    result = run_precreate(context_for(repository_root, PRECREATE_STUDY_ID))

    assert result.status == "passed"
    assert result.details["study_event_required"] is False
    assert not (
        repository_root
        / "workflows"
        / "strategy-forward-replication-research--v001"
        / "studies"
        / PRECREATE_STUDY_ID
        / "events"
    ).exists()
    assert (research_root / "qualification-spec.yml").is_file()


def test_precreate_rejects_existing_study_event(tmp_path: Path) -> None:
    repository_root, _ = _precreate_repository(tmp_path)
    events_root = (
        repository_root
        / "workflows"
        / "strategy-forward-replication-research--v001"
        / "studies"
        / PRECREATE_STUDY_ID
        / "events"
    )
    events_root.mkdir(parents=True)
    _write_yaml(events_root / "000001-study-created.yml", {"schema_version": 1})

    result = run_precreate(context_for(repository_root, PRECREATE_STUDY_ID))

    assert result.status == "failed"
    assert result.errors[0]["code"] == "precreate-after-study-created"
    assert result.details["existing_event_count"] == 1


def test_precreate_rejects_stale_preregistration_binding_with_details(tmp_path: Path) -> None:
    repository_root, research_root = _precreate_repository(tmp_path)
    preregistration_path = research_root / "preregistration.yml"
    preregistration = load_canonical(preregistration_path)
    preregistration["hypothesis"] = f"{preregistration['hypothesis']}；測試變更"
    _write_yaml(preregistration_path, preregistration)

    result = run_precreate(context_for(repository_root, PRECREATE_STUDY_ID))

    finding = next(
        item for item in result.errors if item["code"] == "stale-preregistration-binding"
    )
    assert result.status == "failed"
    assert finding["expected"] == canonical_digest(preregistration)
    assert finding["actual"] == load_canonical(research_root / "qualification-spec.yml")[
        "preregistration_digest"
    ]
    assert finding["path"] == f"research/{PRECREATE_STUDY_ID}/qualification-spec.yml"


def test_precreate_rejects_missing_held_complete_sessions_before_event(tmp_path: Path) -> None:
    repository_root, research_root = _precreate_repository(tmp_path)
    candidate_path = research_root / "candidate-definition.yml"
    candidate = load_canonical(candidate_path)
    del candidate["execution"]["held_complete_sessions"]
    _write_yaml(candidate_path, candidate)

    result = run_precreate(context_for(repository_root, PRECREATE_STUDY_ID))

    assert result.status == "failed"
    holding_error = next(
        item
        for item in result.errors
        if item["code"] == "missing-contract-field"
        and item["expected"] == "execution.held_complete_sessions"
    )
    assert holding_error["path"].endswith("candidate-definition.yml")
    assert holding_error["actual"] is None
    assert not (
        repository_root
        / "workflows"
        / "strategy-forward-replication-research--v001"
        / "studies"
        / PRECREATE_STUDY_ID
        / "events"
        / "000001-study-created.yml"
    ).exists()


def test_diagnose_reports_digest_drift_and_precreate_fix_boundary(tmp_path: Path) -> None:
    repository_root, research_root = _precreate_repository(tmp_path)
    preregistration_path = research_root / "preregistration.yml"
    preregistration = load_canonical(preregistration_path)
    preregistration["hypothesis"] = f"{preregistration['hypothesis']}；診斷 drift"
    _write_yaml(preregistration_path, preregistration)

    context = context_for(repository_root, PRECREATE_STUDY_ID)
    result = run_diagnose(context)

    assert result.status == "failed"
    assert result.details["study_has_event"] is False
    updates = result.details["digest_updates_required"]
    assert updates
    qualification_update = next(
        item for item in updates if item.get("label") == "qualification.preregistration_digest"
    )
    assert qualification_update["expected"] == canonical_digest(preregistration)
    assert qualification_update["actual"] == load_canonical(
        research_root / "qualification-spec.yml"
    )["preregistration_digest"]
    assert qualification_update["can_fix_before_study_created"] is True
    assert any(item["code"] == "digest-drift" for item in result.errors)


def test_diagnose_reports_non_canonical_yaml(tmp_path: Path) -> None:
    repository_root, research_root = _precreate_repository(tmp_path)
    (research_root / "candidate-definition.yml").write_text(
        "unavailable_path: evidence/other.yml\nstage: development\nreason: bad\n",
        encoding="utf-8",
    )

    result = run_diagnose(context_for(repository_root, PRECREATE_STUDY_ID))

    assert result.status == "failed"
    finding = next(item for item in result.errors if item["code"] == "non-canonical-yaml")
    assert finding["path"].endswith("candidate-definition.yml")
    assert result.details["non_canonical_yaml"]


def test_precreate_rejects_drifted_same_name_study_manifest(tmp_path: Path) -> None:
    repository_root, research_root = _precreate_repository(tmp_path)
    manifest_root = (
        repository_root
        / "workflows"
        / "strategy-forward-replication-research--v001"
        / "studies"
        / PRECREATE_STUDY_ID
        / "manifests"
    )
    manifest_root.mkdir(parents=True)
    preregistration = load_canonical(research_root / "preregistration.yml")
    preregistration["hypothesis"] = f"{preregistration['hypothesis']}；manifest drift"
    _write_yaml(manifest_root / "preregistration.yml", preregistration)

    result = run_precreate(context_for(repository_root, PRECREATE_STUDY_ID))

    finding = next(
        item for item in result.errors if item["code"] == "copy-forward-artifact-drift"
    )
    assert finding["path"] == (
        "workflows/strategy-forward-replication-research--v001/"
        f"studies/{PRECREATE_STUDY_ID}/manifests/preregistration.yml"
    )
    assert finding["expected"] != finding["actual"]


def test_precreate_cli_emits_json_and_exit_code_one_for_stale_binding(tmp_path: Path) -> None:
    repository_root, research_root = _precreate_repository(tmp_path)
    preregistration_path = research_root / "preregistration.yml"
    preregistration = load_canonical(preregistration_path)
    preregistration["hypothesis"] = f"{preregistration['hypothesis']}；CLI 測試變更"
    _write_yaml(preregistration_path, preregistration)
    studyctl = REPOSITORY_ROOT / "research" / "tools" / "studyctl.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(studyctl),
            "--repository-root",
            str(repository_root),
            "precreate",
            PRECREATE_STUDY_ID,
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert output["status"] == "failed"
    assert any(
        item["code"] == "stale-preregistration-binding"
        and item["expected"]
        and item["actual"]
        and item["path"].endswith("qualification-spec.yml")
        for check in output["checks"]
        for item in check["errors"]
    )


def test_precreate_cli_rejects_existing_study_event(tmp_path: Path) -> None:
    repository_root, _ = _precreate_repository(tmp_path)
    events_root = (
        repository_root
        / "workflows"
        / "strategy-forward-replication-research--v001"
        / "studies"
        / PRECREATE_STUDY_ID
        / "events"
    )
    events_root.mkdir(parents=True)
    _write_yaml(events_root / "000001-study-created.yml", {"schema_version": 1})
    studyctl = REPOSITORY_ROOT / "research" / "tools" / "studyctl.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(studyctl),
            "--repository-root",
            str(repository_root),
            "precreate",
            PRECREATE_STUDY_ID,
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert output["status"] == "failed"
    assert any(
        item["code"] == "precreate-after-study-created"
        for check in output["checks"]
        for item in check["errors"]
    )


def test_synthetic_runs_against_frozen_engine_and_contract(tmp_path: Path) -> None:
    study_id = "synthetic-study-v001"
    research_root = tmp_path / "research" / study_id
    engine_relative = "src/trading_2026_2/tsm_mean_reversion_volume_leads.py"
    engine_path = tmp_path / engine_relative
    engine_path.parent.mkdir(parents=True)
    shutil.copyfile(
        REPOSITORY_ROOT / "src/trading_2026_2/tsm_mean_reversion_volume_leads.py",
        engine_path,
    )
    research_root.mkdir(parents=True)

    preregistration = {
        "eligibility_rules": {
            "accepted_signal": {
                "cooldown": {"minimum_completed_session_steps_after_exit": 5},
                "mean_reversion": {"rsi_length": 2, "rsi_value": "35", "sma_length": 20},
                "volume_leads_price": {
                    "prior_session_window": 5,
                    "volume_average_length": 20,
                    "volume_ratio_value": "1.25",
                },
            },
            "execution": {
                "position_sizing": {"risk_fraction_of_pre_entry_equity": "0.02"}
            },
        },
        "fold_warmup_sessions": 20,
    }
    candidate = {
        "signal": {
            "cooldown": {"completed_session_steps_after_exit": 5},
            "mean_reversion": {"rsi_length": 2, "rsi_maximum": "35", "sma_length": 20},
            "volume_leads_price": {
                "prior_session_window": 5,
                "volume_average_length": 20,
                "volume_ratio_minimum": "1.25",
            },
        },
        "execution": {
            "held_complete_sessions": 15,
            "position_sizing": {"risk_fraction_of_pre_entry_equity": "0.02"},
            "stop": {"level_from_raw_entry_open": "-0.04"},
            "target": {"level_from_raw_entry_open": "0.04"},
        },
        "fold_policy": {"evaluation_fold_warmup_sessions": 20},
    }
    contract = {
        "schema_version": 1,
        "engine": {
            "path": engine_relative,
            "spec_constant": "DEFAULT_SPEC",
            "cost_constant": "BASE_COST",
        },
        "indicator_contract": {
            "required_history_sessions": 25,
            "columns": {
                "sma": "sma_20",
                "rsi": "rsi_2",
                "volume_lead": "prior_volume_spike_ratio",
            },
            "sma": {"lookback": 20, "min_periods": 20, "not_ready": None},
            "rsi": {
                "length": 2,
                "formula": "simple-rolling-mean",
                "min_periods": 2,
                # 只為測試 plumbing；正式 contract 應登記 null 並讓測試抓出現有 bug。
                "not_ready": 100,
                "zero_gain_and_loss": 50,
                "zero_loss_only": 100,
                "zero_gain_only": 0,
            },
            "volume_lead": {
                "volume_average_length": 20,
                "average_min_periods": 20,
                "prior_session_window": 5,
                "lead_min_periods": 5,
                "uses_prior_sessions_only": True,
            },
        },
    }
    source_bundle = {
        "schema_version": 1,
        "files": [
            {"path": engine_relative, "digest": hashlib.sha256(engine_path.read_bytes()).hexdigest()}
        ],
    }

    def write_yaml(path: Path, value: dict[str, object]) -> None:
        path.write_bytes(canonical_bytes(value))

    write_yaml(research_root / "preregistration.yml", preregistration)
    write_yaml(research_root / "candidate-definition.yml", candidate)
    write_yaml(research_root / "source-bundle.yml", source_bundle)
    write_yaml(research_root / "implementation-contract.yml", contract)

    result = run_synthetic(context_for(tmp_path, study_id))

    assert result.status == "passed"
    assert result.details["passed_cases"] == [
        "rsi",
        "readiness",
        "intraday-exit",
        "holding-cooldown",
    ]

    contract["indicator_contract"]["rsi"]["not_ready"] = None
    write_yaml(research_root / "implementation-contract.yml", contract)
    rejected = run_synthetic(context_for(tmp_path, study_id))

    assert rejected.status == "failed"
    assert any(
        "not-ready NaN" in item["message"]
        for item in rejected.errors
        if item["code"] == "synthetic-case-failed"
    )


def test_synthetic_supports_both_contract_close_directions() -> None:
    upward = run_synthetic(
        context_for(REPOSITORY_ROOT, "tsm-mean-reversion-reversal-trigger--v002")
    )
    downward = run_synthetic(
        context_for(REPOSITORY_ROOT, "tsm-mean-reversion-volume-leads--v003")
    )

    assert upward.status == "passed"
    assert downward.status == "passed"
    assert upward.details["passed_cases"][-1] == "holding-cooldown"
    assert downward.details["passed_cases"][-1] == "holding-cooldown"


def test_synthetic_atr_like_fixture_reports_raw_accepted_rejected_and_trades() -> None:
    context = context_for(
        REPOSITORY_ROOT, "tsm-mean-reversion-supplemental-divergence--v002"
    )

    result = run_synthetic(context)

    assert result.status == "passed"
    assert result.details["signal_case"]["kind"] == "atr-like"
    assert result.details["raw_signals"]
    assert result.details["accepted_signals"]
    assert isinstance(result.details["rejected_signals"], list)
    assert result.details["trades"]
    assert result.details["signal_case"]["raw_signal_columns"][-1] == "supplemental_signal"


def test_synthetic_holding_cooldown_fixture_has_two_trades_and_explicit_rejection() -> None:
    context = context_for(
        REPOSITORY_ROOT, "tsm-mean-reversion-supplemental-divergence--v002"
    )

    result = run_synthetic(context)

    case = result.details["holding_cooldown_case"]
    assert result.status == "passed"
    assert len(case["trades"]) == 2
    assert case["trades"][0]["exit_reason"] == "time"
    assert case["trades"][0]["held_sessions"] == 10
    assert any(
        item["reason"] == "cooldown-not-complete"
        for item in case["rejected_signals"]
    )


def test_synthetic_invalid_fixture_is_not_reported_as_trade_count_only(tmp_path: Path) -> None:
    study_id = "synthetic-fixture-invalid-v001"
    research_root = tmp_path / "research" / study_id
    engine_relative = "src/invalid_engine.py"
    engine_path = tmp_path / engine_relative
    engine_path.parent.mkdir(parents=True)
    engine_path.write_text(
        "from types import SimpleNamespace\n"
        "DEFAULT_SPEC = SimpleNamespace(holding_sessions=3, cooldown_sessions=1, "
        "volume_lead_window=2)\n"
        "BASE_COST = None\n"
        "def indicators(bars, spec=DEFAULT_SPEC):\n"
        "    frame = bars.copy()\n"
        "    frame['raw_signal'] = False\n"
        "    return frame\n"
        "def backtest(bars, spec=DEFAULT_SPEC, cost=None):\n"
        "    return SimpleNamespace(accepted_signal_sessions=(), trades=())\n",
        encoding="utf-8",
    )
    research_root.mkdir(parents=True)
    _write_yaml(research_root / "preregistration.yml", {})
    _write_yaml(research_root / "candidate-definition.yml", {})
    _write_yaml(
        research_root / "implementation-contract.yml",
        {
            "schema_version": 1,
            "engine": {"path": engine_relative},
            "indicator_contract": {"required_history_sessions": 0},
        },
    )
    _write_yaml(
        research_root / "source-bundle.yml",
        {
            "schema_version": 1,
            "files": [
                {
                    "path": engine_relative,
                    "digest": hashlib.sha256(engine_path.read_bytes()).hexdigest(),
                }
            ],
        },
    )

    result = run_synthetic(context_for(tmp_path, study_id))

    assert result.status == "failed"
    fixture_errors = [
        item for item in result.errors if item["code"] == "synthetic-fixture-invalid"
    ]
    assert fixture_errors
    assert all(item["actual"] == "fixture-invalid" for item in fixture_errors)
    assert not any(
        item["code"] == "synthetic-case-failed"
        and "交易數量" in item["message"]
        for item in result.errors
    )
