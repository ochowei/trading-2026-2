"""用合成資料檢查布林計算、資料邊界與 frozen runner；不讀正式價格。"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from trading_2026_2 import tsm_mean_reversion_bollinger_rebound_v001 as engine
from trading_2026_2.frozen_ohlcv_views_v001 import (
    read_development_view,
    view_digest,
)

ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "tsm-mean-reversion-bollinger-rebound--v001"


def runner(name: str):
    path = ROOT / "research" / STUDY_ID / name
    spec = importlib.util.spec_from_file_location(f"bollinger_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def bars(close, *, start="2020-01-02"):
    close = np.array(close, dtype=float)
    return pd.DataFrame(
        {
            "Open": 100.0,
            "High": np.maximum(close, 100.0) + 0.5,
            "Low": np.minimum(close, 100.0) - 0.5,
            "Close": close,
            "Volume": 1_000_000.0,
        },
        index=pd.date_range(start, periods=len(close), freq="B"),
    )


def rebound_bars(*, start="2020-01-02", rows=85):
    frame = bars([100.0] * rows, start=start)
    for signal in (30, 55):
        frame.iloc[signal - 1, frame.columns.get_loc("Close")] = 96.0
        frame.iloc[signal, frame.columns.get_loc("Close")] = 97.0
        frame.iloc[signal - 1 : signal + 1, frame.columns.get_loc("Low")] = 95.5
        frame.iloc[signal - 5, frame.columns.get_loc("Volume")] = 2_000_000.0
    return frame


def test_population_std_and_percent_b_match_independent_calculation():
    close = [100 + i % 7 for i in range(45)]
    result = engine.indicators(bars(close))
    for index in range(19, len(close)):
        window = close[index - 19 : index + 1]
        mean = sum(window) / 20
        sigma = (sum((item - mean) ** 2 for item in window) / 20) ** 0.5
        assert result.iloc[index]["bollinger_std"] == pytest.approx(sigma)
        assert result.iloc[index]["bollinger_lower"] == pytest.approx(mean - 2 * sigma)
        assert result.iloc[index]["bollinger_upper"] == pytest.approx(mean + 2 * sigma)
        expected = (close[index] - mean + 2 * sigma) / (4 * sigma)
        assert result.iloc[index]["bollinger_percent_b"] == pytest.approx(expected)
    assert result["bollinger_percent_b"].iloc[:19].isna().all()


def test_zero_width_and_not_ready_never_signal():
    result = engine.indicators(bars([100.0] * 60), engine.BASELINE_SPEC)
    assert result["bollinger_percent_b"].isna().all()
    assert not result["raw_signal"].any()


def test_percent_b_threshold_is_inclusive_and_legacy_filters_do_not_apply():
    frame = rebound_bars()
    value = float(engine.indicators(frame).iloc[30]["bollinger_percent_b"])
    spec = engine.DEFAULT_SPEC.with_changes(
        bollinger_percent_b_max=value, mean_reversion_min=0.99, rsi_max=-1
    )
    assert engine.indicators(frame, spec).iloc[30]["raw_signal"]
    below = spec.with_changes(bollinger_percent_b_max=np.nextafter(value, -np.inf))
    assert not engine.indicators(frame, below).iloc[30]["raw_signal"]
    with pytest.raises(ValueError, match="不得啟用"):
        engine.indicators(frame, spec.with_changes(legacy_oversold_filter_enabled=True))


def test_future_prices_and_signal_day_volume_cannot_change_current_signal():
    frame = rebound_bars()
    before = engine.indicators(frame)
    changed = frame.copy()
    changed.iloc[31:, changed.columns.get_indexer(["Open", "High", "Low", "Close"])] *= 3
    changed.iloc[30, changed.columns.get_loc("Volume")] *= 100
    after = engine.indicators(changed)
    columns = ["bollinger_percent_b", "prior_volume_spike_ratio", "raw_signal"]
    pd.testing.assert_frame_equal(before[columns].iloc[:31], after[columns].iloc[:31])
    assert before["prior_volume_spike_ratio"].iloc[:25].isna().all()
    assert pd.notna(before["prior_volume_spike_ratio"].iloc[25])


def test_close_rebound_and_prior_volume_confirmation_are_both_required():
    frame = rebound_bars()
    assert engine.indicators(frame).iloc[30]["raw_signal"]
    no_volume = frame.assign(Volume=1_000_000.0)
    assert not engine.indicators(no_volume).iloc[30]["raw_signal"]
    falling = frame.copy()
    falling.iloc[30, falling.columns.get_loc("Close")] = 96.0
    assert not engine.indicators(falling).iloc[30]["raw_signal"]


@pytest.mark.parametrize(
    "values, expected",
    [
        ([95, 100, 94], (95, "stop-gap")),
        ([105, 106, 104], (105, "target-gap")),
        ([100, 105, 95], (96, "stop-same-session")),
    ],
)
def test_adverse_exit_order(values, expected):
    assert (
        engine._intraday_exit(
            pd.Series(dict(zip(["Open", "High", "Low"], values, strict=True))), 104, 96
        )
        == expected
    )


def test_next_open_holding_span_and_fold_cutoff():
    frame = rebound_bars()
    result = engine.backtest(frame, reset_at_start=True)
    assert len(result.trades) == 2
    first = result.trades[0]
    assert first.signal_session == frame.index[30]
    assert first.entry_session == frame.index[31]
    assert first.exit_session == frame.index[41]
    assert first.held_sessions == 10 and first.exit_reason == "time"
    short = engine.backtest(frame.iloc[:40], reset_at_start=True)
    assert short.trades == () and short.accepted_signal_sessions == ()


def test_cost_inclusive_risk_sizing_is_maximal_integer_within_both_caps():
    cost = engine.STRESS_COST
    shares = engine.risk_budget_shares(
        100_000, 100, stop_return=-0.04, risk_fraction=0.02, cost=cost
    )
    debit = 100 * 1.002 * 1.0002
    loss = debit - 96 * 0.998 * 0.9998
    assert shares * debit <= 100_000 and shares * loss <= 2000
    assert (shares + 1) * debit > 100_000 or (shares + 1) * loss > 2000


def test_development_filters_dates_before_parsing_prices(tmp_path):
    path = tmp_path / "frozen.csv"
    header = b"Date,Open,High,Low,Close,Volume\n"
    allowed = b"2014-01-02,100,101,99,100,1000\n"
    path.write_bytes(
        header + allowed + b"2019-01-02,FORBIDDEN-NOT-A-NUMBER\n2020-01-02,FORBIDDEN\n"
    )
    result = read_development_view(path, "2014-01-01", "2018-12-31")
    assert len(result) == 1 and result.iloc[0]["Close"] == 100
    assert (
        view_digest(path, "2014-01-01", "2018-12-31")
        == hashlib.sha256(header + allowed).hexdigest()
    )
    with pytest.raises(ValueError, match="只允許"):
        read_development_view(path, "2020-01-01", "2024-12-31")


def test_candidate_preregistration_contract_and_runners_bind_same_bollinger_rules():
    dev = runner("run_development.py")
    evaluation = runner("run_historical_evaluation.py")
    research = ROOT / "research" / STUDY_ID
    candidate = dev.load_canonical(research / "candidate-definition.yml")
    prereg = dev.load_canonical(research / "preregistration.yml")
    contract = dev.load_canonical(research / "implementation-contract.yml")
    assert candidate["signal"] == engine.signal_definition() == evaluation._engine_signal()
    assert (
        prereg["eligibility_rules"]["accepted_signal"]["bollinger"]
        == candidate["signal"]["bollinger"]
    )
    assert contract["indicator_contract"]["bollinger"] == candidate["signal"]["bollinger"]
    assert contract["indicator_contract"]["rsi"]["used_for_signal"] is False


def test_evaluation_synthetic_folds_reset_cash_and_match_schema():
    evaluation = runner("run_historical_evaluation.py")
    research = ROOT / "research" / STUDY_ID
    prereg = evaluation.load_canonical(research / "preregistration.yml")
    frames = [rebound_bars(start=f"{year}-01-02") for year in range(2020, 2025)]
    evidence = evaluation.historical_evidence(pd.concat(frames), prereg)
    from validator.schema_validation import SchemaStore

    SchemaStore(evaluation.WORKFLOW_ROOT / "schemas").validate(
        "historical-evaluation.schema.yml", evidence
    )
    assert len(evidence["trades"]) == 10
    first_pnl = evidence["trades"][0]["base_pnl"]
    for year in range(2020, 2025):
        trades = [item for item in evidence["trades"] if item["fold"] == year]
        assert len(trades) == 2 and trades[0]["base_pnl"] == first_pnl
        assert all(
            item["signal_date"].startswith(str(year)) and item["exit_date"].startswith(str(year))
            for item in trades
        )


def test_gate_thresholds_come_from_preregistration_and_bad_gate_is_rejected():
    dev = runner("run_development.py")
    rules = {"completed_trades": {"operator": ">=", "value": 30}}
    assert dev.gate_records({"completed_trades": 29}, rules)[1] == ["completed_trades"]
    assert dev.gate_records({"completed_trades": 30}, rules)[1] == []
    with pytest.raises(RuntimeError, match="不一致"):
        dev.gate_records({"invented": 30}, rules)


def test_evaluation_cli_shared_reference_binding_and_no_overwrite(tmp_path, monkeypatch):
    evaluation = runner("run_historical_evaluation.py")
    research = tmp_path / "research" / STUDY_ID
    research.mkdir(parents=True)
    for name in ("candidate-definition.yml", "preregistration.yml", "qualification-spec.yml"):
        (research / name).write_bytes((ROOT / "research" / STUDY_ID / name).read_bytes())
    frames = [rebound_bars(start=f"{year}-01-02") for year in range(2020, 2025)]
    synthetic = pd.concat(frames)
    snapshot_path = tmp_path / "synthetic.csv"
    synthetic.to_csv(snapshot_path, index_label="Date", lineterminator="\n")
    digest = evaluation.digest(snapshot_path)
    snapshot_set = {
        "snapshots": [
            {
                "role": "historical-evaluation",
                "data_digest": digest,
                "sessions": list(synthetic.index.strftime("%Y-%m-%d")),
            }
        ],
    }
    acquisition = {
        "roles": {
            "historical-evaluation": {
                "source_path": "synthetic.csv",
                "source_digest": digest,
            }
        },
    }
    (research / "data-snapshot-set.yml").write_bytes(evaluation.canonical_bytes(snapshot_set))
    (research / "data-snapshot-acquisition.yml").write_bytes(
        evaluation.canonical_bytes(acquisition)
    )
    source_bundle = {
        "schema_version": 1,
        "files": [
            {"path": str(path.relative_to(tmp_path)), "digest": evaluation.digest(path)}
            for path in sorted(research.glob("*.yml"))
        ],
    }
    (research / "source-bundle.yml").write_bytes(evaluation.canonical_bytes(source_bundle))
    output = tmp_path / "synthetic-output.yml"
    argv = [
        "run_historical_evaluation.py",
        "--evaluation",
        str(snapshot_path),
        "--output",
        str(output),
    ]
    for flag, name in (
        ("--candidate-definition", "candidate-definition.yml"),
        ("--preregistration", "preregistration.yml"),
        ("--qualification-spec", "qualification-spec.yml"),
        ("--snapshot-set", "data-snapshot-set.yml"),
        ("--source-bundle", "source-bundle.yml"),
    ):
        argv += [flag, str(research / name)]
    monkeypatch.setattr(evaluation, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", argv)
    assert evaluation.main() == 0
    assert len(evaluation.load_canonical(output)["trades"]) == 10
    original_digest = evaluation.digest(output)
    with pytest.raises(RuntimeError, match="拒絕覆寫"):
        evaluation.main()
    assert evaluation.digest(output) == original_digest
    args = evaluation.parser().parse_args(argv[1:])
    tampered = evaluation.load_canonical(research / "candidate-definition.yml")
    tampered["signal"]["bollinger"]["percent_b_maximum"] = "0.30"
    (research / "candidate-definition.yml").write_bytes(evaluation.canonical_bytes(tampered))
    with pytest.raises(RuntimeError, match="signal 與 frozen"):
        evaluation.validate_frozen_inputs(args)


def test_research_document_is_single_trial_without_post_result_retuning():
    dev = runner("run_development.py")
    research = ROOT / "research" / STUDY_ID
    prereg = dev.load_canonical(research / "preregistration.yml")
    qualification = dev.load_canonical(research / "qualification-spec.yml")
    assert prereg["maximum_trials"] == 1
    assert prereg["complete_candidate_family"] == ["tsm-mr-bollinger-rebound-v001"]
    assert qualification["development"] == prereg["eligibility_rules"]["development_gates"]
    assert qualification["evaluation"] == prereg["evaluation_gates"]
