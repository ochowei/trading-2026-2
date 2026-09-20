"""TSM v001 策略核心的邊界與 look-ahead 測試。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_2026_2 import tsm_momentum_trend_volume_ramp_v001 as strategy


def make_bars(rows: int = 180, signal_index: int = 40) -> pd.DataFrame:
    index = pd.date_range("2014-01-02", periods=rows, freq="B")
    close = np.full(rows, 100.0)
    open_price = np.full(rows, 100.0)
    high = np.full(rows, 101.0)
    low = np.full(rows, 99.0)
    volume = np.full(rows, 1_000_000.0)
    close[signal_index - 1] = 90.0
    open_price[signal_index - 1] = 90.0
    high[signal_index - 1] = 91.0
    low[signal_index - 1] = 89.5
    close[signal_index] = 95.0
    open_price[signal_index] = 95.0
    high[signal_index] = 100.0
    low[signal_index] = 94.5
    volume[signal_index - 3] = 1_000_000.0
    volume[signal_index - 2] = 1_100_000.0
    volume[signal_index - 1] = 1_250_000.0
    return pd.DataFrame(
        {
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def test_short_window_volume_pulse_precedes_price_acceleration() -> None:
    bars = make_bars()
    frame = strategy.indicators(bars)
    signal = frame.iloc[40]

    assert bool(signal["trend_regime"])
    assert signal["price_acceleration"] >= 0.02
    assert signal["prior_volume_spike_ratio"] >= 1.05
    assert bool(signal["volume_pulse_lead"])
    assert bool(signal["raw_signal"])


def test_volume_ramp_columns_do_not_use_current_volume() -> None:
    bars = make_bars()
    changed = bars.copy()
    changed.iloc[40, changed.columns.get_loc("Volume")] = 99_000_000.0

    before = strategy.indicators(bars).iloc[40]
    after = strategy.indicators(changed).iloc[40]

    for column in ("prior_volume_spike_ratio", "volume_pulse_lead", "raw_signal"):
        assert before[column] == after[column]


def test_baseline_is_same_price_path_without_volume_pulse() -> None:
    bars = make_bars()
    for offset in (1, 2, 3):
        bars.iloc[40 - offset, bars.columns.get_loc("Volume")] = 1_000_000.0

    candidate = strategy.indicators(bars)
    baseline = strategy.indicators(bars, strategy.BASELINE_SPEC)

    assert not bool(candidate.iloc[40]["volume_pulse_lead"])
    assert not bool(candidate.iloc[40]["raw_signal"])
    assert bool(baseline.iloc[40]["raw_signal"])


def test_execution_enters_next_open_and_time_exits_after_ten_sessions() -> None:
    result = strategy.backtest(make_bars())

    assert len(result.trades) == 1
    trade = result.trades[0]
    signal_index = 40
    entry_index = signal_index + 1
    assert trade.signal_session == pd.Timestamp("2014-02-27")
    assert trade.entry_session == result.accepted_signal_sessions[0] + pd.tseries.offsets.BDay(1)
    assert trade.held_sessions == 10
    assert trade.exit_reason == "time"
    assert trade.exit_session > trade.entry_session
    assert trade.raw_entry_price == 100.0
    assert trade.raw_exit_price == 100.0
    assert entry_index == 41
