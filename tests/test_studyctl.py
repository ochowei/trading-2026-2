from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "tsm-mean-reversion-volume-leads--v002"
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import canonical_bytes  # noqa: E402

from research.tools.studyctl import (  # noqa: E402
    _derived_history_sessions,
    context_for,
    run_contract,
    run_identity,
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
