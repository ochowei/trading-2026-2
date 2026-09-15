from __future__ import annotations

import numpy as np
import pandas as pd

from trading_2026_2 import (
    tsm_mean_reversion_two_stage_volume_reversal_v009 as v009,
)
from trading_2026_2 import (
    tsm_mean_reversion_two_stage_volume_reversal_v022 as v022,
)


def make_bars(rows: int = 180) -> pd.DataFrame:
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


def add_momentum_event(
    bars: pd.DataFrame,
    event_index: int,
    *,
    event_high: float = 101.5,
    event_low: float = 99.0,
    confirmation_close: float | None = 102.0,
) -> None:
    bars.iloc[event_index, bars.columns.get_loc("Close")] = 100.5
    bars.iloc[event_index, bars.columns.get_loc("High")] = event_high
    bars.iloc[event_index, bars.columns.get_loc("Low")] = event_low
    bars.iloc[event_index, bars.columns.get_loc("Volume")] = 2_000_000.0
    if confirmation_close is not None:
        confirmation_index = event_index + 1
        bars.iloc[confirmation_index, bars.columns.get_loc("Close")] = (
            confirmation_close
        )
        bars.iloc[confirmation_index, bars.columns.get_loc("Open")] = 100.0
        bars.iloc[confirmation_index, bars.columns.get_loc("High")] = max(
            103.0, confirmation_close
        )
        bars.iloc[confirmation_index, bars.columns.get_loc("Low")] = 99.0


def add_original_signal(bars: pd.DataFrame, signal_index: int) -> None:
    bars.iloc[signal_index - 5, bars.columns.get_loc("Volume")] = 2_000_000.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Close")] = 95.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Low")] = 94.0
    bars.iloc[signal_index, bars.columns.get_loc("Close")] = 96.0
    bars.iloc[signal_index, bars.columns.get_loc("Open")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("Low")] = 95.0


def test_momentum_event_uses_prior_only_inputs_and_next_session_entry() -> None:
    bars = make_bars()
    event_index = 50
    add_momentum_event(bars, event_index)

    frame = v022.indicators(bars)
    event = frame.iloc[event_index]

    assert bool(event["trend_condition"])
    assert float(event["prior_volume_average"]) == 1_000_000.0
    assert float(event["event_volume_ratio"]) == 2.0
    assert bool(event["volume_event"])
    assert float(event["fixed_breakout_price"]) == 101.5
    assert not bool(event["supplemental_raw_signal"])

    result = v022.backtest(bars)

    assert result.accepted_signal_sessions == (bars.index[event_index + 1],)
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.signal_session == bars.index[event_index + 1]
    assert trade.entry_session == bars.index[event_index + 2]
    assert trade.signal_origin == "supplemental"
    assert result.supplemental_diagnostics["confirmation_count"] == 1


def test_event_day_cannot_confirm_and_fifth_session_is_checked_before_expiry() -> None:
    bars = make_bars()
    event_index = 50
    add_momentum_event(bars, event_index, confirmation_close=None)
    # The fifth post-event close is strictly above the fixed breakout; this must
    # confirm before the same-day expiry check.
    fifth_index = event_index + 5
    bars.iloc[fifth_index, bars.columns.get_loc("Close")] = 102.0
    bars.iloc[fifth_index, bars.columns.get_loc("High")] = 103.0

    result = v022.backtest(bars)
    diagnostics = result.supplemental_diagnostics

    assert diagnostics["confirmation_count"] == 1
    assert diagnostics["expired_event_count"] == 0
    assert result.accepted_signal_sessions == (bars.index[fifth_index],)


def test_close_equal_to_breakout_does_not_confirm_and_event_can_invalidate() -> None:
    equal_bars = make_bars()
    event_index = 50
    add_momentum_event(equal_bars, event_index, confirmation_close=101.5)
    equal_result = v022.backtest(equal_bars)

    assert equal_result.supplemental_diagnostics["confirmation_count"] == 0
    assert equal_result.supplemental_diagnostics["expired_event_count"] == 1

    invalidated_bars = make_bars()
    add_momentum_event(invalidated_bars, event_index, confirmation_close=None)
    invalidated_bars.iloc[event_index + 1, invalidated_bars.columns.get_loc("Close")] = 98.5
    invalidated_bars.iloc[event_index + 1, invalidated_bars.columns.get_loc("Low")] = 98.0
    invalidated_result = v022.backtest(invalidated_bars)

    assert invalidated_result.supplemental_diagnostics["invalidated_event_count"] == 1
    assert invalidated_result.supplemental_diagnostics["confirmation_count"] == 0


def test_new_event_during_tracking_is_ignored_and_does_not_replace_first_event() -> None:
    bars = make_bars()
    event_index = 50
    add_momentum_event(bars, event_index, event_high=101.5, confirmation_close=None)
    add_momentum_event(bars, event_index + 2, event_high=105.0, confirmation_close=None)
    confirmation_index = event_index + 5
    bars.iloc[confirmation_index, bars.columns.get_loc("Close")] = 102.0
    bars.iloc[confirmation_index, bars.columns.get_loc("High")] = 103.0

    result = v022.backtest(bars)
    diagnostics = result.supplemental_diagnostics

    assert diagnostics["events_started_count"] == 1
    assert diagnostics["events_ignored_while_tracking_count"] == 1
    assert diagnostics["confirmation_count"] == 1
    assert diagnostics["event_ledger"][0]["fixed_breakout_price"] == "101.5"
    assert diagnostics["confirmation_ledger"][0]["confirmation_session"] == str(
        bars.index[confirmation_index].date()
    )


def test_unresolved_event_is_censored_at_signal_end_not_snapshot_end() -> None:
    bars = make_bars()
    event_index = 50
    add_momentum_event(bars, event_index, confirmation_close=None)
    signal_end_index = event_index + 1

    result = v022.backtest(
        bars,
        signal_start=bars.index[25],
        signal_end=bars.index[signal_end_index],
    )
    event = result.supplemental_diagnostics["event_ledger"][0]

    assert result.supplemental_diagnostics["censored_at_signal_end_count"] == 1
    assert event["resolution_session"] == str(bars.index[signal_end_index].date())


def test_original_path_lifecycle_matches_v009_when_supplemental_path_is_disabled() -> None:
    bars = make_bars()
    add_original_signal(bars, 50)
    add_original_signal(bars, 80)

    control = v009.backtest(bars, cost=v009.BASE_COST)
    result = v022.backtest(
        bars, spec=v022.V009_ONLY_SPEC, cost=v022.BASE_COST
    )

    assert result.accepted_signal_sessions == control.accepted_signal_sessions
    assert len(result.trades) == len(control.trades)
    for candidate_trade, control_trade in zip(result.trades, control.trades, strict=True):
        assert candidate_trade.signal_session == control_trade.signal_session
        assert candidate_trade.entry_session == control_trade.entry_session
        assert candidate_trade.exit_session == control_trade.exit_session
        assert candidate_trade.raw_entry_price == control_trade.raw_entry_price
        assert candidate_trade.raw_exit_price == control_trade.raw_exit_price
        assert candidate_trade.executed_entry_price == control_trade.executed_entry_price
        assert candidate_trade.executed_exit_price == control_trade.executed_exit_price
        assert candidate_trade.shares == control_trade.shares
        assert candidate_trade.fees == control_trade.fees
        assert candidate_trade.pnl == control_trade.pnl
        assert candidate_trade.exit_reason == control_trade.exit_reason
        assert candidate_trade.held_sessions == control_trade.held_sessions
        assert candidate_trade.signal_origin == "original"

