from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from trading_2026_2.tsm_mean_reversion_supplemental_divergence_v001 import (
    BASE_COST,
    BASELINE_SPEC,
    DEFAULT_SPEC,
    STRESS_COST,
    V009_ONLY_SPEC,
    WITHOUT_VOLUME_LEAD_SPEC,
    _intraday_exit,
    _rsi,
    backtest,
    indicators,
    mark_to_market_drawdown,
    qualification_metrics,
    risk_budget_shares,
)


def make_bars(rows: int = 120) -> pd.DataFrame:
    index = pd.date_range("2020-01-02", periods=rows, freq="B")
    # Add a slight drift to ensure std > 0 across rolling windows
    drift = np.sin(np.arange(rows) / 5.0)
    close = 100.0 + drift
    open_price = close.copy()
    high = close + 1.0
    low = close - 1.0
    volume = np.full(rows, 1_000_000.0)
    return pd.DataFrame(
        {"Open": open_price, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=index,
    )


def add_v009_signal(bars: pd.DataFrame, signal_index: int) -> None:
    bars.iloc[signal_index - 5, bars.columns.get_loc("Volume")] = 2_000_000.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Open")] = 96.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Close")] = 95.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Low")] = 94.0
    bars.iloc[signal_index, bars.columns.get_loc("Open")] = 95.5
    bars.iloc[signal_index, bars.columns.get_loc("Close")] = 96.0
    bars.iloc[signal_index, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("Low")] = 95.0


def test_rsi_keeps_not_ready_values_and_handles_zero_gain_loss_branches() -> None:
    close = pd.Series([100.0, 100.0, 100.0, 101.0, 100.0, 99.0])

    result = _rsi(close, length=2)

    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(50.0)
    assert result.iloc[3] == pytest.approx(100.0)
    assert result.iloc[4] == pytest.approx(50.0)
    assert result.iloc[5] == pytest.approx(0.0)


def test_indicator_readiness_starts_at_declared_25_session_history() -> None:
    frame = indicators(make_bars(80))
    ready = frame[["sma_20", "rsi_2", "prior_volume_spike_ratio", "bollinger_percent_b", "atr_20"]].notna().all(axis=1)

    assert int(np.flatnonzero(ready.to_numpy())[0]) == 25
    assert DEFAULT_SPEC.fold_warmup_sessions == 25


def test_volume_lead_and_price_direction_are_prior_only() -> None:
    bars = make_bars()
    add_v009_signal(bars, 43)

    original = indicators(bars)
    changed = bars.copy()
    changed.iloc[43, changed.columns.get_loc("Volume")] = 50_000_000.0
    current_volume_changed = indicators(changed)

    assert bool(original.iloc[43]["prior_volume_spike_ratio"] >= 1.05)
    assert bool(original.iloc[43]["close_above_prior_close"])
    assert bool(original.iloc[43]["v009_raw_signal"])
    assert original.iloc[43]["v009_raw_signal"] == current_volume_changed.iloc[43]["v009_raw_signal"]


def test_intraday_exit_adverse_stop_first_and_gap_handling() -> None:
    target = 104.0
    stop = 96.0

    assert _intraday_exit(pd.Series({"Open": 95.0, "High": 100.0, "Low": 94.0}), target, stop) == (95.0, "stop-gap")
    assert _intraday_exit(pd.Series({"Open": 105.0, "High": 106.0, "Low": 104.0}), target, stop) == (105.0, "target-gap")
    assert _intraday_exit(pd.Series({"Open": 100.0, "High": 105.0, "Low": 95.0}), target, stop) == (96.0, "stop-same-session")
    assert _intraday_exit(pd.Series({"Open": 100.0, "High": 103.0, "Low": 97.0}), target, stop) is None


def test_risk_budget_shares_includes_modeled_costs() -> None:
    cash = 100_000.0
    raw_entry = 100.0
    shares_base = risk_budget_shares(cash, raw_entry, stop_return=-0.04, risk_fraction=0.02, cost=BASE_COST)
    shares_stress = risk_budget_shares(cash, raw_entry, stop_return=-0.04, risk_fraction=0.02, cost=STRESS_COST)

    assert shares_base > 0
    assert shares_stress > 0
    assert shares_stress < shares_base


def test_supplemental_path_requires_volume_turnaround_and_retest() -> None:
    bars = make_bars(80)
    # Day 30 to 34: dip so %B <= 0.25
    for idx in range(30, 35):
        bars.iloc[idx, bars.columns.get_loc("Open")] = 90.0
        bars.iloc[idx, bars.columns.get_loc("Close")] = 90.0
        bars.iloc[idx, bars.columns.get_loc("High")] = 91.0
        bars.iloc[idx, bars.columns.get_loc("Low")] = 89.0
    
    # Day 34: volume turnaround event (CLV positive and score3 flips positive)
    bars.iloc[34, bars.columns.get_loc("Open")] = 89.5
    bars.iloc[34, bars.columns.get_loc("Close")] = 91.0
    bars.iloc[34, bars.columns.get_loc("High")] = 91.0
    bars.iloc[34, bars.columns.get_loc("Low")] = 89.0
    bars.iloc[34, bars.columns.get_loc("Volume")] = 2_000_000.0

    # Day 35: retest with low volume and price bounce (Close > prior Close, Close < SMA20)
    bars.iloc[35, bars.columns.get_loc("Open")] = 91.0
    bars.iloc[35, bars.columns.get_loc("Close")] = 92.0
    bars.iloc[35, bars.columns.get_loc("High")] = 92.5
    bars.iloc[35, bars.columns.get_loc("Low")] = 90.5
    bars.iloc[35, bars.columns.get_loc("Volume")] = 500_000.0  # low volume

    # Run backtest with V009_ONLY vs candidate
    res_v009 = backtest(bars, spec=V009_ONLY_SPEC)
    res_cand = backtest(bars, spec=DEFAULT_SPEC)

    assert len(res_v009.trades) == 0
    assert len(res_cand.trades) == 1
    assert res_cand.trades[0].signal_origin == "supplemental"


def test_supplemental_invalidation_when_ref_low_breached() -> None:
    bars = make_bars(80)
    for idx in range(30, 35):
        bars.iloc[idx, bars.columns.get_loc("Open")] = 90.0
        bars.iloc[idx, bars.columns.get_loc("Close")] = 90.0
        bars.iloc[idx, bars.columns.get_loc("High")] = 91.0
        bars.iloc[idx, bars.columns.get_loc("Low")] = 89.0
    
    # Event on Day 34
    bars.iloc[34, bars.columns.get_loc("Open")] = 89.5
    bars.iloc[34, bars.columns.get_loc("Close")] = 91.0
    bars.iloc[34, bars.columns.get_loc("High")] = 91.0
    bars.iloc[34, bars.columns.get_loc("Low")] = 89.0
    bars.iloc[34, bars.columns.get_loc("Volume")] = 2_000_000.0

    # Day 35 breaches ref_low (Low[32..34] min is 89.0) by closing at 88.0 -> invalidates
    bars.iloc[35, bars.columns.get_loc("Open")] = 88.5
    bars.iloc[35, bars.columns.get_loc("Close")] = 88.0
    bars.iloc[35, bars.columns.get_loc("High")] = 89.0
    bars.iloc[35, bars.columns.get_loc("Low")] = 87.0

    # Day 36 attempts bounce
    bars.iloc[36, bars.columns.get_loc("Open")] = 88.0
    bars.iloc[36, bars.columns.get_loc("Close")] = 89.0
    bars.iloc[36, bars.columns.get_loc("High")] = 90.0
    bars.iloc[36, bars.columns.get_loc("Low")] = 88.0
    bars.iloc[36, bars.columns.get_loc("Volume")] = 500_000.0

    res = backtest(bars, spec=DEFAULT_SPEC)
    assert "supplemental" not in res.trade_origins
