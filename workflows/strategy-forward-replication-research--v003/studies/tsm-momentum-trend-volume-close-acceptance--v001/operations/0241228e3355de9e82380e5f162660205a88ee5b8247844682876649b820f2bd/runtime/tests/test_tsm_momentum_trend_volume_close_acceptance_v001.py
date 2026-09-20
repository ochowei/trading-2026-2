"""TSM v001 收盤承接指標的邊界與 look-ahead 測試。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_2026_2 import tsm_momentum_trend_volume_close_acceptance_v001 as strategy


def make_bars(rows: int = 180, signal_index: int = 40) -> pd.DataFrame:
    index = pd.date_range("2014-01-02", periods=rows, freq="B")
    close = np.full(rows, 100.0)
    open_price = np.full(rows, 100.0)
    high = np.full(rows, 101.0)
    low = np.full(rows, 99.0)
    volume = np.full(rows, 1_000_000.0)

    # 訊號日前五個 session：高量日收在區間高點，低量日收在區間低位，
    # 讓 volume-weighted close location 明顯高於未加權位置。
    close[signal_index - 1] = 90.0
    open_price[signal_index - 1] = 90.0
    high[signal_index - 1] = 90.0
    low[signal_index - 1] = 89.0
    volume[signal_index - 1] = 8_000_000.0
    for offset in (2, 3, 4, 5):
        row = signal_index - offset
        close[row] = 99.4
        open_price[row] = 99.4
        high[row] = 101.0
        low[row] = 99.0

    close[signal_index] = 95.0
    open_price[signal_index] = 95.0
    high[signal_index] = 100.0
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


def test_volume_weighted_close_acceptance_precedes_price_acceleration() -> None:
    bars = make_bars()
    frame = strategy.indicators(bars)
    signal = frame.iloc[40]

    assert bool(signal["trend_regime"])
    assert signal["price_acceleration"] >= 0.02
    assert signal["prior_volume_weighted_close_location"] >= 0.65
    assert signal["prior_volume_close_acceptance"] >= 0.10
    assert signal["prior_volume_ratio"] >= 1.05
    assert bool(signal["volume_close_acceptance_lead"])
    assert bool(signal["raw_signal"])


def test_close_acceptance_does_not_use_current_volume_or_close() -> None:
    bars = make_bars()
    changed = bars.copy()
    changed.iloc[40, changed.columns.get_loc("Volume")] = 99_000_000.0
    changed.iloc[40, changed.columns.get_loc("Close")] = 99.0
    changed.iloc[40, changed.columns.get_loc("High")] = 100.0

    before = strategy.indicators(bars).iloc[40]
    after = strategy.indicators(changed).iloc[40]

    for column in (
        "prior_volume_weighted_close_location",
        "prior_unweighted_close_location",
        "prior_volume_close_acceptance",
        "prior_volume_ratio",
        "volume_close_acceptance_lead",
    ):
        assert before[column] == after[column]


def test_baseline_is_same_price_path_without_close_acceptance() -> None:
    bars = make_bars()
    candidate = strategy.indicators(bars)
    baseline = strategy.indicators(bars, strategy.BASELINE_SPEC)

    assert bool(candidate.iloc[40]["volume_close_acceptance_lead"])
    assert bool(candidate.iloc[40]["raw_signal"])
    assert bool(baseline.iloc[40]["raw_momentum_signal"])
    assert bool(baseline.iloc[40]["raw_signal"])


def test_execution_enters_next_open_and_time_exits_after_ten_sessions() -> None:
    result = strategy.backtest(make_bars())

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.signal_session == pd.Timestamp("2014-02-27")
    assert trade.entry_session == result.accepted_signal_sessions[0] + pd.tseries.offsets.BDay(1)
    assert trade.held_sessions == 10
    assert trade.exit_reason == "time"
    assert trade.exit_session > trade.entry_session
    assert trade.raw_entry_price == 100.0
    assert trade.raw_exit_price == 100.0
