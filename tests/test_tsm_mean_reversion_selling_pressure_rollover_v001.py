from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from trading_2026_2 import tsm_mean_reversion_selling_pressure_rollover_v001 as engine
from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v009 import (
    indicators as v009_indicators,
)


def make_bars(rows: int = 100) -> pd.DataFrame:
    index = pd.date_range("2013-01-02", periods=rows, freq="B")
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


def make_path_b_bars() -> tuple[pd.DataFrame, int]:
    bars = make_bars(80)
    # 先建立連續下跌，讓 prior five-session SVB3 留下至少一個 -1。
    closes = {25: 98.0, 26: 96.0, 27: 94.0, 28: 93.0, 29: 92.0}
    # 接著兩個放量上漲、最後一個小量下跌；最後一天仍然 RSI(2) <= 50，
    # 但 Close < prior Close，專門驗證 Path B 不偷加價格方向確認。
    closes.update({30: 95.0, 31: 96.0, 32: 94.5})
    for index, value in closes.items():
        bars.iloc[index, bars.columns.get_loc("Open")] = value
        bars.iloc[index, bars.columns.get_loc("Close")] = value
        bars.iloc[index, bars.columns.get_loc("High")] = value + 0.5
        bars.iloc[index, bars.columns.get_loc("Low")] = value - 0.5
    bars.iloc[30, bars.columns.get_loc("Volume")] = 10_000_000.0
    bars.iloc[31, bars.columns.get_loc("Volume")] = 10_000_000.0
    return bars, 32


def test_rsi_keeps_not_ready_values_and_handles_zero_gain_loss_branches() -> None:
    close = pd.Series([100.0, 100.0, 100.0, 101.0, 100.0, 99.0])

    result = engine._rsi(close, length=2)

    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(50.0)
    assert result.iloc[3] == pytest.approx(100.0)
    assert result.iloc[4] == pytest.approx(50.0)
    assert result.iloc[5] == pytest.approx(0.0)


def test_path_a_is_the_existing_v009_signal() -> None:
    bars, _ = make_path_b_bars()
    expected = v009_indicators(bars)["raw_signal"]
    actual = engine.indicators(bars)["path_a_raw_signal"]

    pd.testing.assert_series_equal(actual, expected, check_names=False)


def test_svb3_uses_flat_zero_and_keeps_zero_denominator_unready() -> None:
    bars = make_bars(60)
    bars.iloc[10:13, bars.columns.get_loc("Volume")] = 0.0
    frame = engine.indicators(bars)

    assert pd.isna(frame.iloc[12]["svb3"])
    assert frame.iloc[40]["svb3"] == pytest.approx(0.0)


def test_path_b_can_trigger_when_close_is_below_prior_close() -> None:
    bars, signal_index = make_path_b_bars()
    frame = engine.indicators(bars)
    row = frame.iloc[signal_index]

    assert row["base_oversold"]
    assert row["prior_svb3_min_5"] <= -0.50
    assert row["svb3"] >= -0.15
    assert not row["close_above_prior_close"]
    assert not row["path_a_raw_signal"]
    assert row["path_b_raw_signal"]


def test_path_b_signal_is_deduplicated_and_enters_next_session_open() -> None:
    bars, signal_index = make_path_b_bars()
    result = engine.backtest(bars, spec=engine.DEFAULT_SPEC)

    assert result.accepted_signal_sessions.count(bars.index[signal_index]) == 1
    matching = [trade for trade in result.trades if trade.signal_session == bars.index[signal_index]]
    assert len(matching) == 1
    assert matching[0].signal_origin == "path_b"
    assert matching[0].entry_session == bars.index[signal_index + 1]


def test_required_history_and_intraday_execution_contract() -> None:
    frame = engine.indicators(make_bars(80))
    ready = frame[["sma_20", "rsi_2", "prior_volume_spike_ratio"]].notna().all(axis=1)

    assert int(np.flatnonzero(ready.to_numpy())[0]) == 25
    assert engine.DEFAULT_SPEC.fold_warmup_sessions == 25
    assert engine._intraday_exit(
        pd.Series({"Open": 95.0, "High": 100.0, "Low": 94.0}), 104.0, 96.0
    ) == (95.0, "stop-gap")
    assert engine._intraday_exit(
        pd.Series({"Open": 100.0, "High": 105.0, "Low": 95.0}), 104.0, 96.0
    ) == (96.0, "stop-same-session")
