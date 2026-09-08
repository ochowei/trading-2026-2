from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from trading_2026_2.tsm_mean_reversion_bollinger_rebound_v002 import (
    BASE_COST,
    STRESS_COST,
    backtest,
    indicators,
)


def make_bars(rows: int = 160) -> pd.DataFrame:
    index = pd.date_range("2020-01-02", periods=rows, freq="B")
    return pd.DataFrame(
        {
            "Open": np.full(rows, 100.0),
            "High": np.full(rows, 101.0),
            "Low": np.full(rows, 99.0),
            "Close": np.full(rows, 100.0),
            "Volume": np.full(rows, 1_000_000.0),
        },
        index=index,
    )


def add_event_and_confirmation(bars: pd.DataFrame, event_index: int = 30) -> None:
    columns = {name: bars.columns.get_loc(name) for name in bars.columns}
    bars.iloc[event_index, columns["Close"]] = 90.0
    bars.iloc[event_index, columns["Open"]] = 90.0
    bars.iloc[event_index, columns["High"]] = 100.0
    bars.iloc[event_index, columns["Low"]] = 89.0
    bars.iloc[event_index, columns["Volume"]] = 2_000_000.0
    bars.iloc[event_index + 1, columns["Close"]] = 89.5
    bars.iloc[event_index + 1, columns["Open"]] = 90.0
    bars.iloc[event_index + 1, columns["High"]] = 91.0
    bars.iloc[event_index + 1, columns["Low"]] = 89.2
    bars.iloc[event_index + 1, columns["Volume"]] = 900_000.0
    bars.iloc[event_index + 2, columns["Close"]] = 91.0
    bars.iloc[event_index + 2, columns["Open"]] = 91.0
    bars.iloc[event_index + 2, columns["High"]] = 92.0
    bars.iloc[event_index + 2, columns["Low"]] = 90.0
    bars.iloc[event_index + 2, columns["Volume"]] = 900_000.0
    bars.iloc[event_index + 3, columns["Open"]] = 91.0
    bars.iloc[event_index + 3, columns["Low"]] = 90.0


def test_event_quiet_hold_confirmation_and_next_open() -> None:
    bars = make_bars()
    add_event_and_confirmation(bars)
    frame = indicators(bars)
    assert bool(frame.iloc[30]["event_signal"])
    assert not bool(frame.iloc[30]["rebound_confirmation_signal"])
    assert bool(frame.iloc[32]["rebound_confirmation_signal"])

    result = backtest(bars, cost=BASE_COST)

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.event_session == bars.index[30]
    assert trade.quiet_hold_session == bars.index[31]
    assert trade.signal_session == bars.index[32]
    assert trade.entry_session == bars.index[33]
    assert trade.confirmation_type == "after-quiet"
    assert result.event_audit.volume_drop_events == 1
    assert result.event_audit.quiet_hold_events == 1
    assert result.event_audit.rebound_confirmations == 1
    assert result.event_audit.actual_entries == 1


def test_invalidation_precedes_confirmation_and_new_event_does_not_reset() -> None:
    bars = make_bars()
    add_event_and_confirmation(bars)
    bars.iloc[31, bars.columns.get_loc("Close")] = 88.0
    bars.iloc[31, bars.columns.get_loc("Low")] = 87.5
    result = backtest(bars, cost=BASE_COST)
    assert not result.trades
    assert result.event_audit.invalidated_events == 1


def test_base_and_stress_keep_identical_lifecycle() -> None:
    bars = make_bars()
    add_event_and_confirmation(bars)
    base = backtest(bars, cost=BASE_COST)
    stress = backtest(bars, cost=STRESS_COST)
    assert [
        (item.signal_session, item.entry_session, item.exit_session, item.exit_reason)
        for item in base.trades
    ] == [
        (item.signal_session, item.entry_session, item.exit_session, item.exit_reason)
        for item in stress.trades
    ]


def test_historical_runner_generates_schema_shape_from_synthetic_folds() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    runner_path = repository_root / "research" / "tsm-mean-reversion-bollinger-rebound--v002" / "run_historical_evaluation.py"
    spec = importlib.util.spec_from_file_location("v002_historical_runner", runner_path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    frames = []
    for year in range(2020, 2025):
        frame = make_bars()
        frame.index = pd.date_range(f"{year}-01-02", periods=len(frame), freq="B")
        add_event_and_confirmation(frame)
        frames.append(frame)
    result = runner.historical_evidence(
        pd.concat(frames),
        {
            "initial_cash": "100000",
            "evaluation_gates": {
                "family_wise_confidence": {"value": "0.90"},
                "stress_max_drawdown": {"value": "0.10"},
            },
        },
    )
    assert result["schema_version"] == 1
    assert result["stage"] == "historical-evaluation"
    assert result["trades"]
    assert all(item["order_type"] == "MARKET" for item in result["trades"])
