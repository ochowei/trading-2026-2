from __future__ import annotations

from math import floor

import numpy as np
import pandas as pd

import trading_2026_2.fxi_mean_reversion_exit_cooldown as module
from trading_2026_2.fxi_mean_reversion_exit_cooldown import (
    CostModel,
    StrategySpec,
    backtest,
    indicators,
)


def bars(rows: int = 60, close: float = 100.0) -> pd.DataFrame:
    index = pd.bdate_range("2020-01-02", periods=rows)
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


def run_with_signals(
    sample: pd.DataFrame, spec: StrategySpec, signal_indexes: list[int], cost: CostModel
):
    prepared = indicators(sample, spec)
    prepared["raw_signal"] = False
    prepared.loc[prepared.index[signal_indexes], "raw_signal"] = True
    original = module.indicators
    module.indicators = lambda _bars, _spec: prepared  # type: ignore[assignment]
    try:
        return backtest(sample, spec=spec, cost=cost, reset_at_start=True)
    finally:
        module.indicators = original


def test_exit_based_cooldown_requires_seven_sessions_after_exit() -> None:
    sample = bars(45)
    spec = StrategySpec(holding_sessions=1, cooldown_sessions=7, fold_warmup_sessions=0)
    result = run_with_signals(sample, spec, [19, 27, 28], CostModel(0, 0))
    assert result.trades[0].exit_session == sample.index[21]
    assert result.accepted_signal_sessions == (sample.index[19], sample.index[28])


def test_zero_cooldown_can_accept_a_signal_on_the_exit_session() -> None:
    sample = bars(40)
    spec = StrategySpec(holding_sessions=1, cooldown_sessions=0, fold_warmup_sessions=0)
    result = run_with_signals(sample, spec, [19, 21], CostModel(0, 0))
    assert result.accepted_signal_sessions == (sample.index[19], sample.index[21])


def test_same_entry_session_target_and_stop_remains_stop_first() -> None:
    sample = bars(35)
    sample.loc[sample.index[21], ["Open", "High", "Low", "Close"]] = [100, 106, 94, 100]
    spec = StrategySpec(holding_sessions=10, cooldown_sessions=7, fold_warmup_sessions=0)
    result = run_with_signals(sample, spec, [20], CostModel(0, 0))
    trade = result.trades[0]
    assert trade.entry_session == sample.index[21]
    assert trade.exit_session == sample.index[21]
    assert trade.exit_reason == "stop-same-session"
    assert trade.held_sessions == 1


def test_costs_and_integer_shares_do_not_borrow() -> None:
    sample = bars(30)
    spec = StrategySpec(
        holding_sessions=1,
        cooldown_sessions=7,
        fold_warmup_sessions=0,
        initial_cash=100_000,
    )
    cost = CostModel(slippage_bps=5, fee_bps=1)
    result = run_with_signals(sample, spec, [20], cost)
    trade = result.trades[0]
    expected_entry = 100 * 1.0005
    expected_shares = floor(100_000 / (expected_entry * 1.0001))
    assert trade.executed_entry_price == expected_entry
    assert trade.shares == expected_shares
    assert expected_shares * expected_entry * 1.0001 <= 100_000
    assert (expected_shares + 1) * expected_entry * 1.0001 > 100_000


def test_time_exit_still_occurs_after_twenty_complete_sessions() -> None:
    sample = bars(50)
    spec = StrategySpec(holding_sessions=20, cooldown_sessions=7, fold_warmup_sessions=0)
    result = run_with_signals(sample, spec, [20], CostModel(0, 0))
    trade = result.trades[0]
    assert trade.entry_session == sample.index[21]
    assert trade.exit_session == sample.index[41]
    assert trade.held_sessions == 20
    assert trade.exit_reason == "time"
