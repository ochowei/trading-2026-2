"""TSM「動能趨勢＋量先價行」v001 的事前機制測試。"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from trading_2026_2 import tsm_momentum_trend_volume_lead_confirmation_v001 as strategy


def make_bars(rows: int = 100) -> pd.DataFrame:
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


def add_volume_event_and_confirmation(
    bars: pd.DataFrame,
    event_index: int,
    confirmation_index: int | None = None,
) -> None:
    bars.iloc[event_index, bars.columns.get_loc("Volume")] = 2_000_000.0
    if confirmation_index is not None:
        bars.iloc[confirmation_index, bars.columns.get_loc("Open")] = 101.0
        bars.iloc[confirmation_index, bars.columns.get_loc("Close")] = 102.0
        bars.iloc[confirmation_index, bars.columns.get_loc("High")] = 103.0
        bars.iloc[confirmation_index, bars.columns.get_loc("Low")] = 100.0


def test_volume_event_is_prior_only_and_event_day_cannot_confirm() -> None:
    bars = make_bars()
    event_index = 50
    add_volume_event_and_confirmation(bars, event_index, event_index)

    frame = strategy.indicators(bars)
    event = frame.iloc[event_index]

    assert bool(event["trend_state"])
    assert float(event["prior_volume_average"]) == pytest.approx(1_000_000.0)
    assert float(event["volume_event_ratio"]) == pytest.approx(2.0)
    assert bool(event["volume_event"])
    assert not bool(event["price_confirmation"])
    assert not bool(event["momentum_raw_signal"])


def test_price_confirmation_occurs_only_after_volume_event() -> None:
    bars = make_bars()
    event_index = 50
    confirmation_index = event_index + 1
    add_volume_event_and_confirmation(bars, event_index, confirmation_index)

    frame = strategy.indicators(bars)

    assert bool(frame.iloc[event_index]["volume_event"])
    assert not bool(frame.iloc[event_index]["momentum_raw_signal"])
    assert bool(frame.iloc[confirmation_index]["price_confirmation"])
    assert bool(frame.iloc[confirmation_index]["momentum_raw_signal"])
    assert frame.iloc[confirmation_index]["confirmation_delay_sessions"] == 1
    assert frame.iloc[confirmation_index]["event_origin_index"] == event_index


def test_event_expires_after_five_sessions_without_price_confirmation() -> None:
    bars = make_bars()
    event_index = 50
    add_volume_event_and_confirmation(bars, event_index)
    for index in range(event_index + 1, event_index + 6):
        bars.iloc[index, bars.columns.get_loc("Close")] = 99.0
        bars.iloc[index, bars.columns.get_loc("Open")] = 99.0
        bars.iloc[index, bars.columns.get_loc("High")] = 100.0
        bars.iloc[index, bars.columns.get_loc("Low")] = 98.0

    frame = strategy.indicators(bars)

    assert not frame.loc[bars.index[event_index + 1] : bars.index[event_index + 6], "momentum_raw_signal"].any()
    assert not bool(frame.iloc[event_index + 6]["price_confirmation"])


def test_event_is_invalidated_by_close_below_event_floor() -> None:
    bars = make_bars()
    event_index = 50
    add_volume_event_and_confirmation(bars, event_index)
    invalidation_index = event_index + 1
    bars.iloc[invalidation_index, bars.columns.get_loc("Open")] = 84.0
    bars.iloc[invalidation_index, bars.columns.get_loc("High")] = 85.0
    bars.iloc[invalidation_index, bars.columns.get_loc("Low")] = 83.0
    bars.iloc[invalidation_index, bars.columns.get_loc("Close")] = 84.0

    frame = strategy.indicators(bars)

    assert not bool(frame.iloc[invalidation_index]["price_confirmation"])
    assert not frame.loc[bars.index[invalidation_index] : bars.index[invalidation_index + 5], "momentum_raw_signal"].any()


def test_extending_data_does_not_change_past_indicator_values() -> None:
    bars = make_bars(80)
    add_volume_event_and_confirmation(bars, 50, 51)
    shorter = strategy.indicators(bars.iloc[:60])
    longer = strategy.indicators(bars)

    for column in (
        "sma_20",
        "rsi_2",
        "prior_volume_average",
        "volume_event_ratio",
        "volume_event",
        "price_confirmation",
        "momentum_raw_signal",
    ):
        pd.testing.assert_series_equal(
            shorter[column], longer.loc[shorter.index, column], check_names=False
        )


def test_backtest_enters_on_next_open_and_exits_after_ten_complete_sessions() -> None:
    bars = make_bars(100)
    event_index = 50
    confirmation_index = 51
    entry_index = 52
    add_volume_event_and_confirmation(bars, event_index, confirmation_index)
    bars.iloc[entry_index, bars.columns.get_loc("Open")] = 103.0
    bars.iloc[entry_index, bars.columns.get_loc("High")] = 104.0
    bars.iloc[entry_index, bars.columns.get_loc("Low")] = 102.0
    bars.iloc[entry_index, bars.columns.get_loc("Close")] = 103.0

    result = strategy.backtest(bars)

    assert result.accepted_signal_sessions == (bars.index[confirmation_index],)
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.entry_session == bars.index[entry_index]
    assert trade.raw_entry_price == pytest.approx(103.0)
    assert trade.exit_session == bars.index[entry_index + strategy.DEFAULT_SPEC.holding_sessions]
    assert trade.exit_reason == "time"
    assert trade.held_sessions == strategy.DEFAULT_SPEC.holding_sessions


def test_intraday_exit_uses_gap_and_adverse_stop_rules() -> None:
    assert strategy._intraday_exit(
        pd.Series({"Open": 95.0, "High": 100.0, "Low": 94.0}), 104.0, 96.0
    ) == (95.0, "stop-gap")
    assert strategy._intraday_exit(
        pd.Series({"Open": 105.0, "High": 106.0, "Low": 104.0}), 104.0, 96.0
    ) == (105.0, "target-gap")
    assert strategy._intraday_exit(
        pd.Series({"Open": 100.0, "High": 105.0, "Low": 95.0}), 104.0, 96.0
    ) == (96.0, "stop-same-session")


def test_baseline_disables_the_volume_lead_route() -> None:
    bars = make_bars()
    add_volume_event_and_confirmation(bars, 50, 51)

    frame = strategy.indicators(bars, spec=strategy.BASELINE_SPEC)

    assert not strategy.BASELINE_SPEC.volume_lead_enabled
    assert not frame["volume_event"].any()
    assert not frame["momentum_raw_signal"].any()


def test_rsi_edge_values_are_explicit() -> None:
    close = pd.Series([100.0, 100.0, 100.0, 101.0, 102.0, 101.0, 100.0])
    rsi = strategy._rsi(close, length=2)

    assert pd.isna(rsi.iloc[0])
    assert rsi.iloc[2] == pytest.approx(50.0)
    assert rsi.iloc[3] == pytest.approx(100.0)
    assert rsi.iloc[6] == pytest.approx(0.0)
