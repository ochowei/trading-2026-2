from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v015 import (
    BASE_COST,
    DEFAULT_SPEC,
    STRESS_COST,
    V009_ONLY_SPEC,
    _intraday_exit,
    _rsi,
    backtest,
    indicators,
    qualification_metrics,
    risk_budget_shares,
)


def make_bars(rows: int = 120) -> pd.DataFrame:
    index = pd.date_range("2020-01-02", periods=rows, freq="B")
    close = np.full(rows, 100.0)
    return pd.DataFrame(
        {
            "Open": close.copy(),
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.full(rows, 1_000_000.0),
        },
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


def add_supplemental_setup(
    bars: pd.DataFrame,
    event_index: int = 40,
    retest_index: int = 41,
    signal_index: int = 42,
) -> None:
    # 事件日：成交量剛好達 1.25 倍，收盤在正振幅的上半部。
    bars.iloc[event_index, bars.columns.get_loc("Volume")] = 1_250_000.0
    bars.iloc[event_index, bars.columns.get_loc("Open")] = 98.0
    bars.iloc[event_index, bars.columns.get_loc("High")] = 102.0
    bars.iloc[event_index, bars.columns.get_loc("Low")] = 96.0
    bars.iloc[event_index, bars.columns.get_loc("Close")] = 99.5

    # 回測日收跌、量不超過事件量 80%，但 Low 沒有跌破事件 Low。
    bars.iloc[retest_index, bars.columns.get_loc("Volume")] = 1_000_000.0
    bars.iloc[retest_index, bars.columns.get_loc("Open")] = 97.5
    bars.iloc[retest_index, bars.columns.get_loc("High")] = 98.0
    bars.iloc[retest_index, bars.columns.get_loc("Low")] = 96.3
    bars.iloc[retest_index, bars.columns.get_loc("Close")] = 96.8

    # 確認日上漲，且相對均線的偏離落在 [1.0%, 1.5%)。
    bars.iloc[signal_index, bars.columns.get_loc("Volume")] = 1_000_000.0
    bars.iloc[signal_index, bars.columns.get_loc("Open")] = 99.0
    bars.iloc[signal_index, bars.columns.get_loc("High")] = 99.0
    bars.iloc[signal_index, bars.columns.get_loc("Low")] = 98.0
    bars.iloc[signal_index, bars.columns.get_loc("Close")] = 98.5


def test_rsi_zero_gain_loss_and_not_ready_are_explicit() -> None:
    close = pd.Series([100.0, 100.0, 100.0, 101.0, 100.0, 99.0])
    result = _rsi(close, length=2)
    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(50.0)
    assert result.iloc[3] == pytest.approx(100.0)
    assert result.iloc[4] == pytest.approx(50.0)
    assert result.iloc[5] == pytest.approx(0.0)


def test_indicator_readiness_starts_at_25_sessions() -> None:
    frame = indicators(make_bars(80))
    ready = frame[["sma_20", "rsi_2", "prior_volume_spike_ratio"]].notna().all(axis=1)
    assert int(np.flatnonzero(ready.to_numpy())[0]) == 25
    assert DEFAULT_SPEC.fold_warmup_sessions == 25


def test_supplemental_path_requires_event_retest_then_close_confirmation() -> None:
    bars = make_bars()
    add_supplemental_setup(bars)
    frame = indicators(bars)
    assert bool(frame.iloc[40]["supplemental_volume_event"])
    assert bool(frame.iloc[42]["close_above_prior_close"])
    assert 0.010 <= frame.iloc[42]["mean_reversion_gap"] < 0.015
    assert frame.iloc[42]["rsi_2"] <= 50

    result = backtest(bars, cost=BASE_COST)
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.signal_origin == "supplemental"
    assert trade.signal_session == bars.index[42]
    assert trade.entry_session == bars.index[43]
    assert result.supplemental_event_sessions == (bars.index[40],)
    assert result.supplemental_diagnostics["supplemental_confirmations"] == 1


def test_zero_range_event_is_invalid_and_newer_event_replaces_older_event() -> None:
    bars = make_bars()
    add_supplemental_setup(bars)
    event_index = 40
    invalid_bars = bars.copy()
    invalid_bars.iloc[event_index, invalid_bars.columns.get_loc("High")] = 100.0
    invalid_bars.iloc[event_index, invalid_bars.columns.get_loc("Low")] = 100.0
    invalid_bars.iloc[event_index, invalid_bars.columns.get_loc("Open")] = 100.0
    invalid_bars.iloc[event_index, invalid_bars.columns.get_loc("Close")] = 100.0
    assert not bool(indicators(invalid_bars).iloc[event_index]["supplemental_volume_event"])

    # 讓 index 41 成為新的有效事件；確認日仍必須距離新事件至少兩個 session。
    bars.iloc[41, bars.columns.get_loc("Volume")] = 1_265_625.0
    bars.iloc[41, bars.columns.get_loc("Open")] = 98.0
    bars.iloc[41, bars.columns.get_loc("High")] = 102.0
    bars.iloc[41, bars.columns.get_loc("Low")] = 96.0
    bars.iloc[41, bars.columns.get_loc("Close")] = 99.5
    bars.iloc[42, bars.columns.get_loc("Volume")] = 1_000_000.0
    bars.iloc[42, bars.columns.get_loc("Open")] = 97.5
    bars.iloc[42, bars.columns.get_loc("High")] = 98.0
    bars.iloc[42, bars.columns.get_loc("Low")] = 96.3
    bars.iloc[42, bars.columns.get_loc("Close")] = 96.8
    bars.iloc[43, bars.columns.get_loc("Close")] = 98.5
    bars.iloc[43, bars.columns.get_loc("Open")] = 99.0
    bars.iloc[43, bars.columns.get_loc("High")] = 99.0
    bars.iloc[43, bars.columns.get_loc("Low")] = 98.0

    result = backtest(bars, cost=BASE_COST)
    assert result.supplemental_event_sessions == (bars.index[41],)
    assert result.supplemental_diagnostics["volume_events_replaced"] >= 1


def test_event_low_break_invalidates_the_event() -> None:
    bars = make_bars()
    add_supplemental_setup(bars)
    bars.iloc[41, bars.columns.get_loc("Low")] = 95.9
    bars.iloc[41, bars.columns.get_loc("Close")] = 96.8
    result = backtest(bars, cost=BASE_COST)
    assert not result.trades
    assert result.supplemental_diagnostics["volume_events_invalidated"] >= 1


def test_same_event_is_consumed_once() -> None:
    bars = make_bars(150)
    add_supplemental_setup(bars, 40, 41, 42)
    # 第二個可疑回測／上漲日不能重新使用 index 40 的事件。
    bars.iloc[44, bars.columns.get_loc("Close")] = 98.5
    bars.iloc[44, bars.columns.get_loc("Open")] = 99.0
    bars.iloc[44, bars.columns.get_loc("High")] = 99.0
    bars.iloc[44, bars.columns.get_loc("Low")] = 98.0
    result = backtest(bars, cost=BASE_COST)
    assert result.supplemental_diagnostics["supplemental_confirmations"] == 1
    assert len(result.supplemental_event_sessions) == 1


def test_original_path_can_be_disabled_without_changing_execution_contract() -> None:
    bars = make_bars()
    add_original_signal(bars, 43)
    combined = backtest(bars, cost=STRESS_COST)
    control = backtest(bars, spec=V009_ONLY_SPEC, cost=STRESS_COST)
    assert combined.trades[0].signal_origin == "original"
    assert [(trade.signal_session, trade.entry_session, trade.exit_session, trade.exit_reason) for trade in combined.trades] == [
        (trade.signal_session, trade.entry_session, trade.exit_session, trade.exit_reason)
        for trade in control.trades
    ]
    assert qualification_metrics(combined) == qualification_metrics(control)


def test_risk_budget_and_intraday_exit_are_unchanged() -> None:
    shares = risk_budget_shares(
        100_000.0,
        100.0,
        stop_return=-0.04,
        risk_fraction=0.02,
        cost=BASE_COST,
    )
    assert shares > 0
    assert _intraday_exit(
        pd.Series({"Open": 100.0, "High": 105.0, "Low": 95.0}), 104.0, 96.0
    ) == (96.0, "stop-same-session")


def test_historical_runner_is_synthetic_tested_without_evaluation_snapshot() -> None:
    runner_path = (
        Path(__file__).resolve().parents[1]
        / "research"
        / "tsm-mean-reversion-two-stage-volume-reversal--v015"
        / "run_historical_evaluation.py"
    )
    module_spec = importlib.util.spec_from_file_location("tsm_v015_he_runner", runner_path)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    yearly_bars: list[pd.DataFrame] = []
    for year in range(2020, 2025):
        year_bars = make_bars(80)
        year_bars.index = pd.date_range(f"{year}-01-02", periods=80, freq="B")
        add_original_signal(year_bars, 43)
        yearly_bars.append(year_bars)
    synthetic_bars = pd.concat(yearly_bars)

    evidence = module.historical_evidence(
        synthetic_bars,
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
