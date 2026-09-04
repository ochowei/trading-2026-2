from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v002 import (
    BASE_COST,
    BASELINE_SPEC,
    DEFAULT_SPEC,
    STRESS_COST,
    _intraday_exit,
    _rsi,
    backtest,
    indicators,
    risk_budget_shares,
)


def make_bars(rows: int = 120) -> pd.DataFrame:
    index = pd.date_range("2020-01-02", periods=rows, freq="B")
    close = np.full(rows, 100.0)
    open_price = close.copy()
    high = close + 1.0
    low = close - 1.0
    volume = np.full(rows, 1_000_000.0)
    return pd.DataFrame(
        {"Open": open_price, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=index,
    )


def add_signal(bars: pd.DataFrame, signal_index: int) -> None:
    bars.iloc[signal_index - 5, bars.columns.get_loc("Volume")] = 2_000_000.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Close")] = 95.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Low")] = 94.0
    bars.iloc[signal_index, bars.columns.get_loc("Close")] = 96.0
    bars.iloc[signal_index, bars.columns.get_loc("Open")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("Low")] = 95.0


def load_research_runner(name: str, filename: str):
    repository_root = Path(__file__).resolve().parents[1]
    runner_path = repository_root / "research" / "tsm-mean-reversion-two-stage-volume-reversal--v002" / filename
    spec = importlib.util.spec_from_file_location(name, runner_path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_rsi_keeps_not_ready_values_and_handles_zero_gain_loss_branches() -> None:
    close = pd.Series([100.0, 100.0, 100.0, 101.0, 100.0, 99.0])

    result = _rsi(close, length=2)

    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(50.0)
    assert result.iloc[3] == pytest.approx(100.0)
    assert result.iloc[4] == pytest.approx(50.0)
    assert result.iloc[5] == pytest.approx(0.0)


def test_indicator_readiness_starts_at_declared_25_session_history() -> None:
    frame = indicators(make_bars(80))
    ready = frame[["sma_20", "rsi_2", "prior_volume_spike_ratio"]].notna().all(axis=1)

    assert int(np.flatnonzero(ready.to_numpy())[0]) == 25
    assert DEFAULT_SPEC.fold_warmup_sessions == 25


def test_volume_lead_and_price_direction_are_prior_only_and_current_volume_is_ignored() -> None:
    bars = make_bars()
    add_signal(bars, 43)

    original = indicators(bars)
    changed = bars.copy()
    changed.iloc[43, changed.columns.get_loc("Volume")] = 50_000_000.0
    current_volume_changed = indicators(changed)

    assert bool(original.iloc[43]["prior_volume_spike_ratio"] >= 1.25)
    assert bool(original.iloc[43]["close_above_prior_close"])
    assert bool(original.iloc[43]["raw_signal"])
    assert original.iloc[43]["raw_signal"] == current_volume_changed.iloc[43]["raw_signal"]


def test_baseline_disables_volume_and_direction_conditions_but_keeps_same_indicator_engine() -> None:
    bars = make_bars()
    signal_index = 43
    bars.iloc[signal_index, bars.columns.get_loc("Close")] = 96.0
    bars.iloc[signal_index, bars.columns.get_loc("Open")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("Low")] = 95.0

    candidate = indicators(bars, DEFAULT_SPEC)
    baseline = indicators(bars, BASELINE_SPEC)

    assert not bool(candidate.iloc[signal_index]["raw_signal"])
    assert bool(baseline.iloc[signal_index]["raw_signal"])


def test_risk_budget_respects_cash_and_modeled_stop() -> None:
    shares = risk_budget_shares(
        100_000.0,
        100.0,
        stop_return=-0.04,
        risk_fraction=0.02,
        cost=BASE_COST,
    )
    entry = 100.0 * (1 + BASE_COST.slippage_bps / 10_000)
    stop = 100.0 * (1 - 0.04) * (1 - BASE_COST.slippage_bps / 10_000)
    expected_loss = shares * (
        entry * (1 + BASE_COST.fee_bps / 10_000)
        - stop * (1 - BASE_COST.fee_bps / 10_000)
    )

    assert shares > 0
    assert expected_loss <= 2_000.0


def test_intraday_exit_uses_gap_and_adverse_stop_first() -> None:
    assert _intraday_exit(
        pd.Series({"Open": 95.0, "High": 100.0, "Low": 94.0}), 104.0, 96.0
    ) == (95.0, "stop-gap")
    assert _intraday_exit(
        pd.Series({"Open": 105.0, "High": 106.0, "Low": 104.0}), 104.0, 96.0
    ) == (105.0, "target-gap")
    assert _intraday_exit(
        pd.Series({"Open": 100.0, "High": 105.0, "Low": 95.0}), 104.0, 96.0
    ) == (96.0, "stop-same-session")


def test_backtest_enters_next_open_and_time_exits_after_15_complete_sessions() -> None:
    bars = make_bars()
    add_signal(bars, 40)
    bars.iloc[41, bars.columns.get_loc("Open")] = 98.0
    bars.iloc[41, bars.columns.get_loc("Close")] = 98.0
    bars.iloc[41, bars.columns.get_loc("High")] = 98.5
    bars.iloc[41, bars.columns.get_loc("Low")] = 97.5

    result = backtest(bars, cost=BASE_COST)

    assert result.trades
    trade = result.trades[0]
    assert trade.signal_session == bars.index[40]
    assert trade.entry_session == bars.index[41]
    assert trade.exit_session == bars.index[56]
    assert trade.exit_reason == "time"
    assert trade.held_sessions == 15


def test_cooldown_starts_at_completed_exit_and_accepts_only_after_five_sessions() -> None:
    bars = make_bars(150)
    add_signal(bars, 40)
    add_signal(bars, 61)

    result = backtest(bars, cost=STRESS_COST)

    assert len(result.trades) == 2
    assert result.trades[0].exit_session == bars.index[56]
    assert result.trades[1].signal_session == bars.index[61]
    assert bars.index[60] not in result.accepted_signal_sessions
    assert result.trades[1].entry_session == bars.index[62]


def test_reset_at_start_uses_fold_warmup_and_does_not_carry_portfolio_state() -> None:
    bars = make_bars(90)
    add_signal(bars, 25)

    result = backtest(bars, reset_at_start=True)

    assert result.accepted_signal_sessions == (bars.index[25],)
    assert result.trades[0].entry_session == bars.index[26]


def test_historical_runner_signal_matches_candidate_definition() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    runner = load_research_runner(
        "historical_runner_two_stage_signal_v002", "run_historical_evaluation.py"
    )
    candidate = runner.load_canonical(
        repository_root
        / "research"
        / "tsm-mean-reversion-two-stage-volume-reversal--v002"
        / "candidate-definition.yml"
    )

    assert candidate["signal"] == runner._engine_signal()


def test_development_runner_preserves_source_lines_when_hashing_snapshot_views(
    tmp_path: Path,
) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    runner = load_research_runner(
        "development_runner_two_stage_digest_v002", "run_development.py"
    )
    source_path = (
        repository_root
        / "research"
        / "market-data"
        / "yahoo"
        / "TSM-2013-01-02-2025-12-31-auto-adjust--sha256-50178c8f2965b76b37f60e906901d2ec06e997e3c647df6b885bb99464788e95.csv"
    )
    original_digest = runner._source_lines_digest(
        source_path, "2014-01-01", "2018-12-31"
    )
    altered_path = tmp_path / source_path.name
    altered_path.write_bytes(
        source_path.read_bytes().replace(
            b"12.630525252018865", b"12.630525252018866", 1
        )
    )

    assert (
        original_digest
        == "4e443b4c7db125967ef936d615b6d2283da8ba0bccc62239a5770daf176eccc3"
    )
    assert (
        runner._source_lines_digest(altered_path, "2014-01-01", "2018-12-31")
        != original_digest
    )


def _synthetic_year(year: int) -> pd.DataFrame:
    frame = make_bars(80)
    frame.index = pd.date_range(f"{year}-01-02", periods=80, freq="B")
    add_signal(frame, 40)
    return frame


def test_historical_runner_produces_schema_shape_from_synthetic_folds() -> None:
    runner_path = (
        Path(__file__).resolve().parents[1]
        / "research"
        / "tsm-mean-reversion-two-stage-volume-reversal--v002"
        / "run_historical_evaluation.py"
    )
    if not runner_path.is_file():
        pytest.skip("Historical runner not yet created in research directory")
    runner = load_research_runner("historical_runner_two_stage_v002", "run_historical_evaluation.py")

    bars = pd.concat([_synthetic_year(year) for year in range(2020, 2025)])
    evidence = runner.historical_evidence(
        bars,
        {
            "initial_cash": "100000",
            "evaluation_gates": {
                "family_wise_confidence": {"value": "0.90"},
                "stress_max_drawdown": {"value": "0.10"},
            },
        },
    )

    assert evidence["stage"] == "historical-evaluation"
    assert len(evidence["trades"]) == 5
    assert {trade["fold"] for trade in evidence["trades"]} == set(range(2020, 2025))
