"""TSM v004 量先價後延遲報酬傳導的 look-ahead 與執行測試。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_2026_2 import tsm_momentum_trend_volume_response_lag_v001 as strategy


def make_bars(rows: int = 180, signal_index: int = 50) -> pd.DataFrame:
    index = pd.date_range("2014-01-02", periods=rows, freq="B")
    close = np.full(rows, 100.0)
    open_price = np.full(rows, 100.0)
    high = np.full(rows, 100.5)
    low = np.full(rows, 99.5)
    volume = np.full(rows, 1_000_000.0)

    # t-5 的量配對到 t-5→t-4 的後續報酬；t-2→t-1 的負報酬
    # 讓未加權平均較差，但量加權結果仍高於固定下限且有超額。
    for offset in (1, 2, 3, 4, 5):
        volume[signal_index - offset] = 1_100_000.0
    volume[signal_index - 5] = 1_500_000.0
    close[signal_index - 5] = 100.0
    open_price[signal_index - 4] = 112.0
    close[signal_index - 4] = 112.0
    high[signal_index - 4] = 112.5
    low[signal_index - 4] = 111.5
    close[signal_index - 2] = 100.0
    close[signal_index - 1] = 90.0
    open_price[signal_index - 1] = 89.5
    high[signal_index - 1] = 90.0
    low[signal_index - 1] = 89.0
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


def test_volume_forward_response_precedes_price_acceleration() -> None:
    frame = strategy.indicators(make_bars())
    signal = frame.iloc[50]

    assert bool(signal["trend_regime"])
    assert signal["price_acceleration"] >= 0.02
    assert signal["prior_volume_ratio"] >= 1.05
    assert signal["prior_volume_forward_return"] >= -0.02
    assert signal["prior_volume_forward_advantage"] >= 0.0005
    assert bool(signal["volume_forward_response_lead"])
    assert bool(signal["raw_signal"])


def test_forward_response_does_not_use_current_bar() -> None:
    bars = make_bars()
    changed = bars.copy()
    changed.iloc[50, changed.columns.get_loc("Open")] = 120.0
    changed.iloc[50, changed.columns.get_loc("High")] = 120.0
    changed.iloc[50, changed.columns.get_loc("Low")] = 80.0
    changed.iloc[50, changed.columns.get_loc("Volume")] = 99_000_000.0

    before = strategy.indicators(bars).iloc[50]
    after = strategy.indicators(changed).iloc[50]
    for column in (
        "prior_volume_ratio",
        "prior_volume_forward_return",
        "prior_unweighted_forward_return",
        "prior_volume_forward_advantage",
        "volume_forward_response_lead",
        "raw_signal",
    ):
        assert before[column] == after[column]


def test_baseline_removes_only_delayed_response_filter() -> None:
    candidate = strategy.indicators(make_bars()).iloc[50]
    baseline = strategy.indicators(make_bars(), strategy.BASELINE_SPEC).iloc[50]

    assert bool(candidate["volume_ratio_lead"])
    assert bool(candidate["volume_forward_response_lead"])
    assert bool(candidate["raw_signal"])
    assert bool(baseline["volume_forward_response_lead"])
    assert bool(baseline["raw_signal"])


def test_execution_enters_next_open_and_time_exits_after_ten_sessions() -> None:
    result = strategy.backtest(make_bars())

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.entry_session == result.accepted_signal_sessions[0] + pd.tseries.offsets.BDay(1)
    assert trade.held_sessions == 10
    assert trade.exit_reason == "time"
    assert trade.exit_session > trade.entry_session
    assert trade.raw_entry_price == 100.0
    assert trade.raw_exit_price == 100.0
