"""建立隔離的人造設定；不呼叫 writer、Release 或 Study 操作。"""

from __future__ import annotations

import shutil
from copy import deepcopy
from pathlib import Path

from operations.legacy_checks import StudyContext
from validator.canonical_yaml import canonical_bytes, canonical_digest, load_canonical

PACKAGE = Path(__file__).resolve().parents[1]
REGIME = {
    "kind": "sma-comparison",
    "operator": ">",
    "input": "Close",
    "include_current_session": True,
    "not_ready_allowed": False,
    "fast": {"lookback": 20, "min_periods": 20, "column": "regime_sma20"},
    "slow": {"lookback": 50, "min_periods": 50, "column": "regime_sma50"},
    "allowed_column": "sma20_above_sma50",
}


def write(root: Path, name: str, value: dict) -> None:
    (root / name).write_bytes(canonical_bytes(value))


def make_context(
    root: Path, *, ready: bool = True, study_id: str = "synthetic-regime"
) -> StudyContext:
    """名稱只是人造設定位置，不參與案例產生或策略訊號判斷。"""

    research = root / "research" / study_id
    research.mkdir(parents=True)
    (root / "src").mkdir()
    for name in ("candidate_engine.py", "control_engine.py", "ready_engine.py"):
        shutil.copyfile(PACKAGE / "tests/fixtures/regime" / name, root / "src" / name)
    original = PACKAGE / "tests/fixtures/contract"
    contract = load_canonical(original / "implementation-contract.yml")
    contract["engine"]["path"] = "src/ready_engine.py" if ready else "src/candidate_engine.py"
    contract["indicator_contract"]["regime"] = deepcopy(REGIME)
    contract["indicator_contract"]["required_history_sessions"] = 49
    contract["execution"]["exits"]["holding_exit"] = "next-open-after-10-complete-sessions"
    candidate = load_canonical(original / "candidate-definition.yml")
    candidate["candidate_id"] = "tsm-mr-volume-lead-upclose-v006"
    candidate["signal"]["regime"] = deepcopy(REGIME)
    candidate["signal"]["mean_reversion"].update(
        close_vs_sma20_gap_minimum="0.015", rsi_maximum="50"
    )
    candidate["signal"]["volume_leads_price"]["volume_ratio_minimum"] = "1.05"
    candidate["execution"]["held_complete_sessions"] = 10
    candidate["execution"]["maximum_holding_session_span_for_validator"] = 11
    candidate["fold_policy"]["evaluation_fold_warmup_sessions"] = 49 if ready else 25
    prereg = load_canonical(original / "preregistration.yml")
    prereg["eligibility_rules"]["accepted_signal"]["regime"] = deepcopy(REGIME)
    prereg["eligibility_rules"]["accepted_signal"]["mean_reversion"].update(
        close_vs_sma20_gap_minimum="0.015", rsi_value="50"
    )
    prereg["eligibility_rules"]["accepted_signal"]["volume_leads_price"]["volume_ratio_value"] = (
        "1.05"
    )
    prereg["maximum_holding_sessions"] = 11
    prereg["fold_warmup_sessions"] = 49 if ready else 25
    qualification = load_canonical(original / "qualification-spec.yml")
    write(research, "preregistration.yml", prereg)
    qualification["preregistration_digest"] = canonical_digest(
        (research / "preregistration.yml").read_bytes()
    )
    write(research, "candidate-definition.yml", candidate)
    write(research, "qualification-spec.yml", qualification)
    write(research, "implementation-contract.yml", contract)
    # 只綁定原生 precreate 所需程序路徑；本次不執行此程序。
    (research / "run_development.py").write_text('"""此人造設定只供唯讀原生 guard 檢查。"""\n')
    refresh_bundle(root, research)
    return StudyContext(root.resolve(), PACKAGE, study_id)


def refresh_bundle(repository: Path, research: Path) -> dict:
    sources = [
        *sorted((repository / "src").glob("*.py")),
        *(
            research / name
            for name in (
                "implementation-contract.yml",
                "candidate-definition.yml",
                "preregistration.yml",
                "qualification-spec.yml",
                "run_development.py",
            )
        ),
    ]
    bundle = {
        "schema_version": 1,
        "files": [
            {
                "path": path.relative_to(repository).as_posix(),
                "digest": canonical_digest(path.read_bytes()),
            }
            for path in sources
        ],
    }
    write(research, "source-bundle.yml", bundle)
    trial = load_canonical(PACKAGE / "tests/fixtures/contract/development-trial-inputs.yml")
    trial["trial_id"] = "trial-001"
    trial["candidate_id"] = "tsm-mr-volume-lead-upclose-v006"
    trial["preregistration_digest"] = canonical_digest(
        (research / "preregistration.yml").read_bytes()
    )
    trial["source_bundle_digest"] = canonical_digest(bundle)
    contract = load_canonical(research / "implementation-contract.yml")
    trial["strategy_engine_digest"] = canonical_digest(
        (repository / contract["engine"]["path"]).read_bytes()
    )
    trial["study_procedure_digest"] = canonical_digest(
        (research / "run_development.py").read_bytes()
    )
    trial["execution"]["holding_sessions"] = 10
    trial["signal"].update(
        mean_reversion_close_vs_sma20_gap_minimum="0.015",
        mean_reversion_rsi_maximum="50",
        volume_spike_ratio_minimum="1.05",
    )
    # 沒有市場資料檔，只有明示的未執行人造設定路徑。
    for role in ("warmup", "development"):
        trial["data_bindings"][f"{role}_path"] = f"research/{research.name}/synthetic-only.csv"
        trial["data_bindings"][f"{role}_digest"] = "0" * 64
    write(research, "development-trial-inputs.yml", trial)
    return bundle
