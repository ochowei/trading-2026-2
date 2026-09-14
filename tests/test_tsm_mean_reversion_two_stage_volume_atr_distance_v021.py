from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from trading_2026_2 import tsm_mean_reversion_two_stage_volume_reversal_v009 as v009
from trading_2026_2.tsm_mean_reversion_two_stage_volume_atr_distance_v021 import (
    BASE_COST,
    STRESS_COST,
    V009_ONLY_SPEC,
    _intraday_exit,
    _wilder_average,
    backtest,
    indicators,
    qualification_metrics,
    risk_budget_shares,
)


def make_bars(rows: int = 140, close: float = 100.0) -> pd.DataFrame:
    index = pd.date_range("2020-01-02", periods=rows, freq="B")
    return pd.DataFrame(
        {
            "Open": np.full(rows, close),
            "High": np.full(rows, close + 1.0),
            "Low": np.full(rows, close - 1.0),
            "Close": np.full(rows, close),
            "Volume": np.full(rows, 1_000_000.0),
        },
        index=index,
    )


def add_signal(bars: pd.DataFrame, signal_index: int) -> None:
    bars.iloc[signal_index - 5, bars.columns.get_loc("Volume")] = 2_000_000.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Close")] = 95.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index - 1, bars.columns.get_loc("Low")] = 94.0
    bars.iloc[signal_index, bars.columns.get_loc("Close")] = 96.0
    bars.iloc[signal_index, bars.columns.get_loc("Open")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("High")] = 100.0
    bars.iloc[signal_index, bars.columns.get_loc("Low")] = 95.0


def lifecycle(trade: object) -> tuple[object, ...]:
    return (
        trade.signal_session,
        trade.entry_session,
        trade.exit_session,
        trade.exit_reason,
    )


def test_wilder_atr_uses_seed_then_recursive_update() -> None:
    index = pd.date_range("2020-01-02", periods=16, freq="B")
    values = pd.Series(np.arange(1.0, 17.0), index=index)
    result = _wilder_average(values, 14)

    assert result.iloc[:13].isna().all()
    assert result.iloc[13] == pytest.approx(7.5)
    assert result.iloc[14] == pytest.approx((7.5 * 13 + 15.0) / 14.0)


def test_signal_uses_signal_close_and_previous_completed_atr_only() -> None:
    bars = make_bars(90)
    add_signal(bars, 43)
    frame = indicators(bars)
    row = frame.iloc[43]

    assert row["sma_20"] == pytest.approx(
        bars.iloc[24:44]["Close"].mean()
    )
    assert row["prior_atr_14"] == pytest.approx(frame.iloc[42]["atr_14"])
    assert row["atr_distance"] == pytest.approx(
        (row["sma_20"] - row["Close"]) / row["prior_atr_14"]
    )
    assert row["atr_distance"] >= 1.0
    assert bool(row["raw_signal"])

    changed = bars.copy()
    changed.iloc[43, changed.columns.get_loc("Volume")] = 50_000_000.0
    changed_frame = indicators(changed)
    assert changed_frame.iloc[43]["prior_atr_14"] == pytest.approx(row["prior_atr_14"])
    assert changed_frame.iloc[43]["raw_signal"] == row["raw_signal"]


def test_nonpositive_previous_atr_blocks_signal() -> None:
    bars = make_bars(90, close=100.0)
    # 全部 OHLC 相同，真實波幅與 ATR 都是 0；即使其餘條件被注入也不能進場。
    bars.loc[:, ["Open", "High", "Low", "Close"]] = 100.0
    frame = indicators(bars)
    assert (frame["atr_14"].iloc[13:] == 0).all()
    assert not frame["atr_distance_valid"].any()
    assert not frame["raw_signal"].any()


def test_next_open_holding_and_cooldown_keep_v009_semantics(monkeypatch: pytest.MonkeyPatch) -> None:
    bars = make_bars(150)
    prepared = indicators(bars)
    prepared["raw_signal"] = False
    prepared.loc[prepared.index[[40, 61]], "raw_signal"] = True
    import trading_2026_2.tsm_mean_reversion_two_stage_volume_atr_distance_v021 as module

    monkeypatch.setattr(module, "indicators", lambda _bars, _spec: prepared)
    result = backtest(bars, cost=STRESS_COST)

    assert result.accepted_signal_sessions == (prepared.index[40], prepared.index[61])
    assert result.trades[0].entry_session == bars.index[41]
    assert result.trades[0].exit_session == bars.index[51]
    assert result.trades[0].held_sessions == 10
    assert result.trades[1].entry_session == bars.index[62]


def test_v009_control_spec_matches_frozen_v009_on_synthetic_bars() -> None:
    bars = make_bars(160)
    add_signal(bars, 40)
    add_signal(bars, 90)

    candidate = backtest(bars, spec=V009_ONLY_SPEC, cost=BASE_COST)
    control = v009.backtest(bars, spec=v009.DEFAULT_SPEC, cost=v009.BASE_COST)

    assert [lifecycle(trade) for trade in candidate.trades] == [
        lifecycle(trade) for trade in control.trades
    ]
    assert candidate.accepted_signal_sessions == control.accepted_signal_sessions
    assert qualification_metrics(candidate) == pytest.approx(
        qualification_metrics(control)
    )


def test_risk_and_intraday_fill_rules_are_v009_rules() -> None:
    shares = risk_budget_shares(
        100_000.0,
        100.0,
        stop_return=-0.04,
        risk_fraction=0.02,
        cost=BASE_COST,
    )
    assert shares > 0
    assert _intraday_exit(
        pd.Series({"Open": 100.0, "High": 105.0, "Low": 95.0}), 104.0, 96.0
    ) == (96.0, "stop-same-session")
