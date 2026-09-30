"""本地 in-memory synthetic preflight；不讀任何市場 CSV，也不建立 Study。"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import exchange_calendars as xcals
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from trading_2026_2 import tsm_mean_reversion_two_stage_volume_reversal_sma20_sma50_regime_v001 as candidate
from trading_2026_2 import tsm_mean_reversion_two_stage_volume_reversal_v009 as control

def bars(kind: str, n: int = 80, event: int = 60) -> pd.DataFrame:
    sessions = xcals.get_calendar("XNYS").sessions_in_range("2014-01-02", "2014-06-30")
    idx = pd.DatetimeIndex(sessions[:n]).tz_localize(None)
    i = np.arange(n, dtype=float)
    if kind == "above":
        close = 80.0 + 0.4 * i
        close[event - 1], close[event] = 94.0, 96.5
    elif kind == "below":
        close = 120.0 - 0.4 * i
        close[event - 1], close[event] = 86.0, 88.5
    elif kind == "equal":
        close = np.full(n, 100.0)
        close[41] = 115.0
        close[59], close[60] = 90.0, 95.0
    elif kind == "unready":
        close = 80.0 + 0.4 * i
        close[event - 1], close[event] = 85.0, 87.5
    else:
        raise ValueError(kind)
    volume = np.full(n, 1_000_000.0)
    volume[event - 5] = 5_000_000.0
    frame = pd.DataFrame({"Open": close, "High": close + 1.0, "Low": close - 1.0, "Close": close, "Volume": volume}, index=idx)
    return frame

def main() -> None:
    # Candidate accepts an otherwise valid v009 signal only in strict up-regime.
    for kind, index, expected in (("above", 60, True), ("below", 60, False), ("equal", 60, False), ("unready", 34, False)):
        frame = bars(kind, event=index)
        c = candidate.indicators(frame)
        b = control.indicators(frame)
        assert bool(b["raw_signal"].iloc[index]), f"Control fixture did not signal: {kind}"
        assert bool(c["raw_signal"].iloc[index]) is expected, f"Candidate regime result mismatch: {kind}"
        if kind == "above":
            assert c["regime_sma20"].iloc[index] > c["regime_sma50"].iloc[index]
        if kind == "equal":
            assert c["regime_sma20"].iloc[index] == c["regime_sma50"].iloc[index]
        if kind == "unready":
            assert pd.isna(c["regime_sma50"].iloc[index])
    base = bars("above")
    before = candidate.indicators(base).iloc[60]
    changed = base.copy()
    changed.iloc[61:, changed.columns.get_loc("Close")] += np.linspace(50.0, 100.0, len(changed) - 61)
    changed.iloc[61:, changed.columns.get_loc("Open")] = changed["Close"].iloc[61:]
    changed.iloc[61:, changed.columns.get_loc("High")] = changed["Close"].iloc[61:] + 1.0
    changed.iloc[61:, changed.columns.get_loc("Low")] = changed["Close"].iloc[61:] - 1.0
    after = candidate.indicators(changed).iloc[60]
    for column in ("regime_sma20", "regime_sma50", "sma20_above_sma50", "raw_signal"):
        assert before[column] == after[column], f"future data changed signal-day {column}"
    candidate_result = candidate.backtest(base, cost=candidate.BASE_COST)
    control_result = control.backtest(base, cost=control.BASE_COST)
    assert len(candidate_result.trades) == len(control_result.trades) == 1
    ctrade, btrade = candidate_result.trades[0], control_result.trades[0]
    for field in ("signal_session", "entry_session", "exit_session", "raw_entry_price", "raw_exit_price", "executed_entry_price", "executed_exit_price", "shares", "fees", "pnl", "exit_reason", "held_sessions"):
        assert getattr(ctrade, field) == getattr(btrade, field), f"pass-path execution mismatch: {field}"
    print("synthetic_preflight: PASS; above/below/equal/unready and future-perturbation; candidate/control execution parity")

if __name__ == "__main__":
    main()
