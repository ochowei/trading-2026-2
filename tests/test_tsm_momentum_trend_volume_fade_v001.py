"""TSM v004 先前量能先行後鈍化的 look-ahead 與 baseline 測試。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_2026_2 import tsm_momentum_trend_volume_fade_v001 as strategy


def make_bars(rows: int = 180, signal_index: int = 40) -> pd.DataFrame:
    index = pd.date_range("2014-01-02", periods=rows, freq="B")
    close = np.full(rows, 100.0)
    open_price = np.full(rows, 100.0)
    high = np.full(rows, 100.5)
    low = np.full(rows, 99.5)
    volume = np.full(rows, 1_000_000.0)
    volume[signal_index - 5] = 5_000_000.0
    close[signal_index - 1] = 90.0
    open_price[signal_index - 1] = 90.0
    high[signal_index - 1] = 90.5
    low[signal_index - 1] = 89.5
    close[signal_index] = 95.0
    open_price[signal_index] = 95.0
    high[signal_index] = 95.5
    low[signal_index] = 94.5
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


def make_rising_led_bars(rows: int = 180, signal_index: int = 40) -> pd.DataFrame:
    bars = make_bars(rows=rows, signal_index=signal_index)
    volume_column = bars.columns.get_loc("Volume")
    bars.iloc[signal_index - 5 : signal_index, volume_column] = 1_000_000.0
    bars.iloc[signal_index - 4 : signal_index, volume_column] = 1_250_000.0
    return bars


def test_volume_fade_precedes_price_acceleration() -> None:
    signal = strategy.indicators(make_bars()).iloc[40]

    assert bool(signal["trend_regime"])
    assert signal["price_acceleration"] >= 0.02
    assert signal["prior_volume_endpoint_ratio"] <= 1.0
    assert bool(signal["volume_fade_lead"])
    assert bool(signal["raw_signal"])


def test_fade_columns_do_not_use_current_bar() -> None:
    bars = make_bars()
    changed = bars.copy()
    changed.iloc[40, changed.columns.get_loc("Volume")] = 99_000_000.0
    changed.iloc[40, changed.columns.get_loc("High")] = 120.0
    changed.iloc[40, changed.columns.get_loc("Low")] = 80.0

    before = strategy.indicators(bars).iloc[40]
    after = strategy.indicators(changed).iloc[40]
    for column in (
        "prior_volume_ratio",
        "prior_volume_endpoint_ratio",
        "volume_fade_lead",
        "raw_signal",
    ):
        assert before[column] == after[column]


def test_baseline_is_same_price_path_without_fade_filter() -> None:
    bars = make_rising_led_bars()
    candidate = strategy.indicators(bars)
    baseline = strategy.indicators(bars, strategy.BASELINE_SPEC)

    assert not bool(candidate.iloc[40]["volume_fade_lead"])
    assert not bool(candidate.iloc[40]["raw_signal"])
    assert strategy.DEFAULT_SPEC.volume_fade_enabled
    assert not strategy.BASELINE_SPEC.volume_fade_enabled
    assert bool(baseline.iloc[40]["raw_signal"])


def test_execution_enters_next_open_and_time_exits_after_ten_sessions() -> None:
    result = strategy.backtest(make_bars())

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.entry_session == result.accepted_signal_sessions[0] + pd.tseries.offsets.BDay(1)
    assert trade.held_sessions == 10
    assert trade.exit_reason == "time"
    assert trade.raw_entry_price == 100.0
    assert trade.raw_exit_price == 100.0
