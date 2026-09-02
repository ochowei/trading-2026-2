from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from trading_2026_2.tsm_mean_reversion_volume_leads import (
    BASE_COST,
    DEFAULT_SPEC,
    STRESS_COST,
    backtest,
    indicators,
    risk_budget_shares,
    validate_bars,
)


def make_bars(rows: int = 80, *, base: float = 100.0) -> pd.DataFrame:
    index = pd.date_range("2020-01-02", periods=rows, freq="B")
    close = np.full(rows, base)
    open_price = close.copy()
    high = close + 1.0
    low = close - 1.0
    volume = np.full(rows, 1_000_000.0)
    return pd.DataFrame(
        {"Open": open_price, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=index,
    )


def test_indicators_require_prior_volume_spike_and_current_mean_reversion() -> None:
    bars = make_bars()
    bars.iloc[40, bars.columns.get_loc("Volume")] = 2_000_000.0
    bars.iloc[43, bars.columns.get_loc("Close")] = 96.0
    bars.iloc[43, bars.columns.get_loc("Open")] = 97.0
    bars.iloc[43, bars.columns.get_loc("Low")] = 95.0
    result = indicators(bars)
    assert not bool(result.iloc[40]["raw_signal"])
    assert bool(result.iloc[43]["prior_volume_spike_ratio"] >= DEFAULT_SPEC.volume_spike_ratio)
    assert bool(result.iloc[43]["raw_signal"])


def test_current_volume_does_not_change_current_signal() -> None:
    bars = make_bars()
    bars.iloc[43, bars.columns.get_loc("Close")] = 96.0
    bars.iloc[43, bars.columns.get_loc("Open")] = 97.0
    bars.iloc[43, bars.columns.get_loc("Low")] = 95.0
    changed = bars.copy()
    changed.iloc[43, changed.columns.get_loc("Volume")] = 50_000_000.0
    assert indicators(bars).iloc[43]["raw_signal"] == indicators(changed).iloc[43]["raw_signal"]


def test_risk_budget_respects_cash_and_modeled_stop() -> None:
    shares = risk_budget_shares(
        100_000.0,
        100.0,
        stop_return=-0.04,
        risk_fraction=0.02,
        cost=BASE_COST,
    )
    assert shares > 0
    entry = 100.0 * (1 + BASE_COST.slippage_bps / 10_000)
    stop = 100.0 * (1 - 0.04) * (1 - BASE_COST.slippage_bps / 10_000)
    expected_loss = shares * (entry * (1 + BASE_COST.fee_bps / 10_000) - stop * (1 - BASE_COST.fee_bps / 10_000))
    assert expected_loss <= 2_000.0


def test_backtest_uses_next_open_and_returns_completed_trades() -> None:
    bars = make_bars(100)
    bars.iloc[40, bars.columns.get_loc("Volume")] = 2_000_000.0
    bars.iloc[43, bars.columns.get_loc("Close")] = 96.0
    bars.iloc[43, bars.columns.get_loc("Open")] = 97.0
    bars.iloc[43, bars.columns.get_loc("Low")] = 95.0
    entry_row = 44
    bars.iloc[entry_row, bars.columns.get_loc("Open")] = 98.0
    bars.iloc[entry_row, bars.columns.get_loc("High")] = 98.5
    bars.iloc[entry_row, bars.columns.get_loc("Low")] = 97.5
    bars.iloc[entry_row, bars.columns.get_loc("Close")] = 98.0
    result = backtest(bars, spec=DEFAULT_SPEC, cost=BASE_COST)
    assert result.trades
    assert result.trades[0].entry_session == bars.index[entry_row]
    assert result.trades[0].raw_entry_price == pytest.approx(98.0)


def test_stress_cost_is_more_adverse_than_base_for_same_signal_path() -> None:
    bars = make_bars(100)
    bars.iloc[40, bars.columns.get_loc("Volume")] = 2_000_000.0
    bars.iloc[43, bars.columns.get_loc("Close")] = 96.0
    bars.iloc[43, bars.columns.get_loc("Open")] = 97.0
    bars.iloc[43, bars.columns.get_loc("Low")] = 95.0
    base = backtest(bars, cost=BASE_COST)
    stress = backtest(bars, cost=STRESS_COST)
    assert len(base.trades) == len(stress.trades)
    assert [trade.signal_session for trade in base.trades] == [
        trade.signal_session for trade in stress.trades
    ]
    assert sum(trade.pnl for trade in stress.trades) <= sum(trade.pnl for trade in base.trades)


def test_validate_bars_rejects_invalid_volume() -> None:
    bars = make_bars()
    bars.iloc[0, bars.columns.get_loc("Volume")] = -1.0
    with pytest.raises(ValueError, match="Volume"):
        validate_bars(bars)


def test_spec_with_changes_is_explicit_variant() -> None:
    variant = DEFAULT_SPEC.with_changes(volume_spike_ratio=1.5)
    assert variant.volume_spike_ratio == 1.5
    assert DEFAULT_SPEC.volume_spike_ratio == 1.25
