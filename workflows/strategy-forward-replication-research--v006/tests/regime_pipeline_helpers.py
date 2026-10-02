"""完整 SMA regime 的人造來源定義；建立檔案時不執行任何 Lifecycle。"""

from __future__ import annotations

import shutil

import exchange_calendars as xcals
from operations.legacy_checks import StudyContext
from operations.preflight import synthetic_csv
from operations.synthetic_fixtures import make_sma_regime_bars
from synthetic_helpers import make_context
from test_operations import fixture_repository, refresh_bundle, write
from validator.canonical_yaml import canonical_digest, load_canonical


def regime_repository(tmp_path, *, ready=True):
    repository, package, study_id, authority, research = fixture_repository(tmp_path)
    settings = make_context(tmp_path / "regime-settings", ready=ready, study_id=study_id)
    for name in ("preregistration", "qualification-spec", "candidate-definition",
                 "implementation-contract", "development-trial-inputs"):
        write(research / f"{name}.yml", load_canonical(settings.research_root / f"{name}.yml"))
    # 只替換本函式剛建立的人造 src，完整綁定 wrapper 與其公開依賴。
    shutil.rmtree(repository / "src")
    shutil.copytree(settings.repository_root / "src", repository / "src")
    engine = "ready_engine" if ready else "candidate_engine"
    runner = research / "runner.py"
    runner.write_text(runner.read_text().replace(
        "trading_2026_2.tsm_mean_reversion_reversal_trigger_v001", engine))
    prereg = load_canonical(research / "preregistration.yml")
    prereg["eligibility_rules"]["development_gates"] = {
        "completed_trades": {"operator": ">=", "value": 1}
    }
    prereg["eligibility_rules"]["development_diagnostics"]["block_bootstrap"]["repetitions"] = 100
    prereg["baseline_definition"]["simpler_rule"] = (
        "相同 SMA20>SMA50 與均值回歸指標，移除成交量先行與收盤反轉確認；執行／成本／暖機相同。")
    prereg["baseline_definition"]["objectively_simpler_because"] = (
        "保留真實引擎的 BASELINE_SPEC；只少兩個訊號條件，不使用另一份 toy evidence。")
    prereg["evaluation_gates"] = {}
    write(research / "preregistration.yml", prereg)
    contract = load_canonical(research / "runner-contract.yml")
    cases = []
    calendar = xcals.get_calendar("XNYS")
    for stage, year in (("development", 2014), ("historical-evaluation", 2020)):
        dates = calendar.sessions_in_range(f"{year}-01-02", f"{year}-12-31")[:180]
        for expectation in ("trades", "no-trades"):
            frame = make_sma_regime_bars(180, [57, 73], regime="above" if expectation == "trades" else "below")
            rows = [[day.strftime("%Y-%m-%d"), *map(str, row)]
                    for day, row in zip(dates, frame.to_numpy(), strict=True)]
            cases.append({"stage": stage, "expect": expectation, "rows": rows})
    contract["cases"] = cases
    write(research / "runner-contract.yml", contract)
    data = synthetic_csv(cases[0])
    (research / "development.csv").write_bytes(data)
    inputs = load_canonical(research / "development-trial-inputs.yml")
    inputs["development_runner_path"] = f"research/{study_id}/runner.py"
    inputs["development_diagnostics"]["repetitions"] = 100
    for role in ("warmup", "development"):
        inputs["data_bindings"][f"{role}_path"] = f"research/{study_id}/development.csv"
        inputs["data_bindings"][f"{role}_digest"] = canonical_digest(data)
    write(research / "development-trial-inputs.yml", inputs)
    refresh_bundle(repository, research)
    return repository, package, study_id, authority, research


def context(repository, package, study_id):
    return StudyContext(repository, package, study_id)
