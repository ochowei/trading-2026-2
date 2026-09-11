from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from trading_2026_2 import tsm_mean_reversion_two_stage_volume_reversal_v009 as v009
from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v018 import (
    BASE_COST,
    STRESS_COST,
    V009_ONLY_SPEC,
    _intraday_exit,
    backtest,
    indicators,
    qualification_metrics,
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


def add_original_signal(bars: pd.DataFrame, signal_index: int) -> None:
    bars.iloc[signal_index - 5, bars.columns.get_loc("Volume")] = 2_000_000.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Close")] = 95.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Low")] = 94.0
    bars.iloc[signal_index, bars.columns.get_loc("Close")] = 96.0
    bars.iloc[signal_index, bars.columns.get_loc("Open")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("Low")] = 95.0


def add_supplemental_signal(bars: pd.DataFrame, signal_index: int) -> None:
    # t-2 收跌、t-1 跌幅收斂且低點持平；t 僅比 SMA(20) 低約 1.06%。
    bars.iloc[signal_index - 2, bars.columns.get_loc("Close")] = 98.8
    bars.iloc[signal_index - 2, bars.columns.get_loc("Low")] = 98.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Close")] = 98.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Low")] = 98.0
    bars.iloc[signal_index, bars.columns.get_loc("Close")] = 98.5
    bars.iloc[signal_index, bars.columns.get_loc("Low")] = 98.0
    bars.iloc[signal_index - 2, bars.columns.get_loc("Volume")] = 1_100_000.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Volume")] = 1_100_000.0


def lifecycle(trade: object) -> tuple[object, ...]:
    return (
        trade.signal_session,
        trade.entry_session,
        trade.exit_session,
        trade.exit_reason,
    )


def load_runner(filename: str):
    repository_root = Path(__file__).resolve().parents[1]
    runner_path = (
        repository_root
        / "research"
        / "tsm-mean-reversion-two-stage-volume-reversal--v018"
        / filename
    )
    spec = importlib.util.spec_from_file_location(f"v018_{filename}", runner_path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_supplemental_path_requires_all_fixed_conditions() -> None:
    bars = make_bars()
    add_supplemental_signal(bars, 50)

    frame = indicators(bars)
    row = frame.iloc[50]

    assert row["volume_ratio_t_minus_2"] >= 1.05
    assert row["volume_ratio_t_minus_1"] >= 1.05
    assert row["return_t_minus_2"] < row["return_t_minus_1"] <= 0
    assert row["low_t_minus_1"] >= row["low_t_minus_2"]
    assert 0.010 <= row["mean_reversion_gap"] < 0.015
    assert row["rsi_2"] <= 50
    assert row["Close"] > row["prior_close"]
    assert bool(row["supplemental_raw_signal"])
    assert not bool(row["v009_raw_signal"])

    result = backtest(bars, cost=BASE_COST)
    assert result.trades[0].signal_session == bars.index[50]
    assert result.trades[0].signal_origin == "supplemental"
    assert result.supplemental_diagnostics["supplemental_signals_accepted"] == 1


def test_supplemental_volume_average_excludes_current_signal_day() -> None:
    bars = make_bars()
    add_supplemental_signal(bars, 50)
    original = indicators(bars).iloc[50]

    changed = bars.copy()
    changed.iloc[50, changed.columns.get_loc("Volume")] = 50_000_000.0
    current_volume_changed = indicators(changed).iloc[50]

    assert bool(original["supplemental_raw_signal"])
    assert bool(current_volume_changed["supplemental_raw_signal"])
    assert original["volume_ratio_t_minus_2"] == current_volume_changed["volume_ratio_t_minus_2"]
    assert original["volume_ratio_t_minus_1"] == current_volume_changed["volume_ratio_t_minus_1"]


def test_supplemental_upper_gap_boundary_is_exclusive() -> None:
    bars = make_bars()
    add_supplemental_signal(bars, 50)
    frame = indicators(bars)
    previous_sum = float(frame.iloc[50]["sma_20"] * 20 - frame.iloc[50]["Close"])
    desired_close = 0.985 * previous_sum / 19.015
    bars.iloc[50, bars.columns.get_loc("Close")] = desired_close
    bars.iloc[50, bars.columns.get_loc("Low")] = desired_close - 0.2

    row = indicators(bars).iloc[50]
    assert row["mean_reversion_gap"] == pytest.approx(0.015)
    assert not bool(row["supplemental_raw_signal"])


def test_original_path_matches_v009_when_supplemental_path_is_disabled() -> None:
    bars = make_bars(150)
    add_original_signal(bars, 40)
    add_original_signal(bars, 90)

    candidate = backtest(bars, spec=V009_ONLY_SPEC, cost=BASE_COST)
    control = v009.backtest(bars, spec=v009.DEFAULT_SPEC, cost=v009.BASE_COST)

    assert [lifecycle(trade) for trade in candidate.trades] == [
        lifecycle(trade) for trade in control.trades
    ]
    assert candidate.accepted_signal_sessions == control.accepted_signal_sessions
    assert qualification_metrics(candidate) == pytest.approx(
        qualification_metrics(control)
    )


def test_execution_and_cooldown_remain_v009_semantics() -> None:
    bars = make_bars(150)
    add_supplemental_signal(bars, 40)
    add_supplemental_signal(bars, 61)

    result = backtest(bars, cost=STRESS_COST)

    assert len(result.trades) == 2
    assert result.trades[0].entry_session == bars.index[41]
    assert result.trades[0].exit_session == bars.index[51]
    assert result.trades[1].signal_session == bars.index[61]
    assert result.trades[1].entry_session == bars.index[62]
    assert bars.index[60] not in result.accepted_signal_sessions


def test_intraday_exit_keeps_gap_and_adverse_stop_first() -> None:
    assert _intraday_exit(
        pd.Series({"Open": 95.0, "High": 100.0, "Low": 94.0}), 104.0, 96.0
    ) == (95.0, "stop-gap")
    assert _intraday_exit(
        pd.Series({"Open": 105.0, "High": 106.0, "Low": 104.0}), 104.0, 96.0
    ) == (105.0, "target-gap")
    assert _intraday_exit(
        pd.Series({"Open": 100.0, "High": 105.0, "Low": 95.0}), 104.0, 96.0
    ) == (96.0, "stop-same-session")


def test_historical_runner_signal_matches_candidate_definition() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    runner = load_runner("run_historical_evaluation.py")
    candidate = runner.load_canonical(
        repository_root
        / "research"
        / "tsm-mean-reversion-two-stage-volume-reversal--v018"
        / "candidate-definition.yml"
    )
    assert candidate["signal"] == runner._engine_signal()
