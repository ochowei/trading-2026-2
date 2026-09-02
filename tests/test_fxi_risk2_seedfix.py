from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import trading_2026_2.fxi_risk2_seedfix as module
from trading_2026_2.fxi_mean_reversion import BacktestResult, Trade
from trading_2026_2.fxi_risk2_seedfix import (
    bootstrap,
    evaluate_gate_records,
    historical_evidence,
)


def test_bootstrap_uses_exact_registered_seed_for_every_block_length() -> None:
    rates = np.asarray([0.01, -0.02, 0.03, 0.01, -0.01])
    short = bootstrap(rates, 3, repetitions=100, seed=20260904)
    long = bootstrap(rates, 5, repetitions=100, seed=20260904)
    assert short["seed"] == 20260904
    assert long["seed"] == 20260904


def test_gate_evaluator_uses_all_registered_rules_and_ten_percent_drawdown() -> None:
    rules = {
        "stress_maximum_drawdown": {"operator": "<=", "value": "0.10"},
        "completed_trades": {"operator": ">=", "value": 20},
    }
    records, failures = evaluate_gate_records(
        {"stress_maximum_drawdown": "0.11", "completed_trades": 22}, rules
    )
    assert [record["gate"] for record in records] == [
        "stress_maximum_drawdown",
        "completed_trades",
    ]
    assert failures == ["stress_maximum_drawdown"]


def test_gate_evaluator_rejects_missing_metric() -> None:
    with pytest.raises(ValueError, match="缺少"):
        evaluate_gate_records(
            {"completed_trades": 22},
            {
                "completed_trades": {"operator": ">=", "value": 20},
                "stress_return": {"operator": ">", "value": "0"},
            },
        )


def test_historical_evidence_resets_each_fold_and_never_crosses_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    indexes = pd.DatetimeIndex(
        [timestamp for year in range(2020, 2025) for timestamp in pd.bdate_range(f"{year}-01-02", periods=40)]
    )
    bars = pd.DataFrame(
        {name: np.full(len(indexes), value) for name, value in {
            "Open": 100.0,
            "High": 101.0,
            "Low": 99.0,
            "Close": 100.0,
            "Volume": 1_000_000.0,
        }.items()},
        index=indexes,
    )
    calls: list[tuple[int, bool]] = []

    def fake_backtest(fold, *, cost, risk_fraction, reset_at_start):
        year = int(fold.index[0].year)
        calls.append((year, reset_at_start))
        signal = fold.index[25]
        entry = fold.index[26]
        exit_session = fold.index[27]
        pnl = 100.0 if cost == module.BASE_COST else 80.0
        trade = Trade(
            signal_session=signal,
            entry_session=entry,
            exit_session=exit_session,
            raw_entry_price=100.0,
            raw_exit_price=101.0,
            executed_entry_price=100.0,
            executed_exit_price=101.0,
            shares=100,
            fees=0.0,
            pnl=pnl,
            exit_reason="target",
            held_sessions=2,
        )
        return BacktestResult((trade,), (signal,), 100_000.0 + pnl)

    monkeypatch.setattr(module, "backtest", fake_backtest)
    evidence = historical_evidence(bars, family_wise_confidence="0.90")
    assert calls == [(year, True) for year in range(2020, 2025) for _ in range(2)]
    assert [trade["fold"] for trade in evidence["trades"]] == list(range(2020, 2025))
    assert all(
        trade["signal_date"][:4] == trade["exit_date"][:4]
        for trade in evidence["trades"]
    )
