"""TSM v001 量能窄幅壓縮核心的邊界與 look-ahead 測試。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_2026_2 import tsm_momentum_trend_volume_range_compression_v001 as strategy


def make_bars(rows: int = 180, signal_index: int = 40) -> pd.DataFrame:
    index = pd.date_range("2014-01-02", periods=rows, freq="B")
    close = np.full(rows, 100.0)
    open_price = np.full(rows, 100.0)
    high = np.full(rows, 100.5)
    low = np.full(rows, 99.5)
    volume = np.full(rows, 1_000_000.0)

    # 先在訊號日前五個已完成 session 形成高量窄幅，最後一天保留回落後的價格。
    for offset in (1, 2, 3, 4, 5):
        position = signal_index - offset
        high[position] = close[position] + 0.5
        low[position] = close[position] - 0.5
        volume[position] = 1_250_000.0
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


def test_range_compression_precedes_price_acceleration() -> None:
    frame = strategy.indicators(make_bars())
    signal = frame.iloc[40]

    assert bool(signal["trend_regime"])
    assert signal["price_acceleration"] >= 0.02
    assert signal["prior_volume_range_compression"] <= 1.05
    assert signal["prior_volume_ratio"] >= 1.05
    assert bool(signal["volume_range_compression_lead"])
    assert bool(signal["raw_signal"])


def test_prior_compression_columns_do_not_use_current_volume_or_range() -> None:
    bars = make_bars()
    changed = bars.copy()
    changed.iloc[40, changed.columns.get_loc("Volume")] = 99_000_000.0
    changed.iloc[40, changed.columns.get_loc("High")] = 120.0
    changed.iloc[40, changed.columns.get_loc("Low")] = 80.0

    before = strategy.indicators(bars).iloc[40]
    after = strategy.indicators(changed).iloc[40]

    for column in (
        "prior_volume_range_compression",
        "prior_volume_ratio",
        "volume_range_compression_lead",
        "raw_signal",
    ):
        assert before[column] == after[column]


def test_baseline_is_same_price_path_without_range_compression() -> None:
    bars = make_bars()
    candidate = strategy.indicators(bars)
    baseline = strategy.indicators(bars, strategy.BASELINE_SPEC)

    assert bool(candidate.iloc[40]["volume_range_compression_lead"])
    assert bool(candidate.iloc[40]["raw_signal"])
    assert not bool(baseline.iloc[40]["volume_range_compression_lead"])
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
