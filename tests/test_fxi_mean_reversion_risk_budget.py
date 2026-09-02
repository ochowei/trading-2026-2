from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import trading_2026_2.fxi_mean_reversion_risk_budget as module
from trading_2026_2.fxi_mean_reversion_risk_budget import (
    CostModel,
    StrategySpec,
    backtest,
    indicators,
    risk_budget_shares,
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
    sample: pd.DataFrame,
    spec: StrategySpec,
    signal_indexes: list[int],
    cost: CostModel,
    *,
    risk_fraction: float = 0.02,
):
    prepared = indicators(sample, spec)
    prepared["raw_signal"] = False
    prepared.loc[prepared.index[signal_indexes], "raw_signal"] = True
    original = module.indicators
    module.indicators = lambda _bars, _spec: prepared  # type: ignore[assignment]
    try:
        return backtest(
            sample,
            spec=spec,
            cost=cost,
            risk_fraction=risk_fraction,
            reset_at_start=True,
        )
    finally:
        module.indicators = original


@pytest.mark.parametrize("cost", [CostModel(5, 1), CostModel(20, 2)])
def test_risk_budget_includes_modeled_slippage_and_fees(cost: CostModel) -> None:
    shares = risk_budget_shares(
        100_000,
        100,
        stop_return=-0.05,
        risk_fraction=0.02,
        cost=cost,
    )
    entry_cash_per_share = 100 * (1 + cost.slippage_bps / 10_000) * (1 + cost.fee_bps / 10_000)
    stop_proceeds_per_share = 95 * (1 - cost.slippage_bps / 10_000) * (1 - cost.fee_bps / 10_000)
    modeled_loss_per_share = entry_cash_per_share - stop_proceeds_per_share
    assert shares * modeled_loss_per_share <= 2_000
    assert (shares + 1) * modeled_loss_per_share > 2_000
    assert shares * entry_cash_per_share <= 100_000


@pytest.mark.parametrize("risk_fraction", [0, -0.01, 1.01])
def test_risk_fraction_must_be_in_valid_range(risk_fraction: float) -> None:
    with pytest.raises(ValueError):
        risk_budget_shares(
            100_000,
            100,
            stop_return=-0.05,
            risk_fraction=risk_fraction,
            cost=CostModel(0, 0),
        )


def test_exact_stop_limits_realized_loss_to_two_percent() -> None:
    sample = bars(35)
    sample.loc[sample.index[21], ["Open", "High", "Low", "Close"]] = [100, 101, 95, 100]
    spec = StrategySpec(holding_sessions=10, cooldown_sessions=7, fold_warmup_sessions=0)
    result = run_with_signals(sample, spec, [20], CostModel(5, 1))
    trade = result.trades[0]
    assert trade.exit_reason == "stop"
    assert -trade.pnl / spec.initial_cash <= 0.02


def test_stop_gap_can_exceed_budget_but_never_borrows() -> None:
    sample = bars(35)
    sample.loc[sample.index[22], ["Open", "High", "Low", "Close"]] = [90, 91, 89, 90]
    spec = StrategySpec(holding_sessions=10, cooldown_sessions=7, fold_warmup_sessions=0)
    cost = CostModel(5, 1)
    result = run_with_signals(sample, spec, [20], cost)
    trade = result.trades[0]
    entry_cash = trade.shares * trade.executed_entry_price * (1 + cost.fee_bps / 10_000)
    assert trade.exit_reason == "stop-gap"
    assert entry_cash <= spec.initial_cash


@pytest.mark.parametrize("exit_kind", ["time", "stop", "target-gap"])
def test_cooldown_starts_from_every_completed_exit(exit_kind: str) -> None:
    sample = bars(50)
    holding_sessions = 1 if exit_kind == "time" else 10
    spec = StrategySpec(
        holding_sessions=holding_sessions,
        cooldown_sessions=7,
        fold_warmup_sessions=0,
    )
    if exit_kind == "stop":
        sample.loc[sample.index[21], "Low"] = 94
    elif exit_kind == "target-gap":
        sample.loc[sample.index[21], ["Open", "High", "Low", "Close"]] = [106, 107, 105, 106]
    result = run_with_signals(sample, spec, [19, 27, 28], CostModel(0, 0))
    assert result.trades[0].exit_reason == exit_kind
    assert result.trades[0].exit_session == sample.index[21]
    assert result.accepted_signal_sessions == (sample.index[19], sample.index[28])


def test_time_exit_remains_after_twenty_complete_sessions() -> None:
    sample = bars(50)
    spec = StrategySpec(holding_sessions=20, cooldown_sessions=7, fold_warmup_sessions=0)
    result = run_with_signals(sample, spec, [20], CostModel(0, 0))
    trade = result.trades[0]
    assert trade.entry_session == sample.index[21]
    assert trade.exit_session == sample.index[41]
    assert trade.held_sessions == 20
    assert trade.exit_reason == "time"
