"""v012 當日盤中反轉確認的邊界測試。"""

from __future__ import annotations

import pandas as pd

from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v012 import (
    DEFAULT_SPEC,
    indicators,
)


def _bars(rows: list[dict[str, float]]) -> pd.DataFrame:
    index = pd.date_range("2020-01-02", periods=len(rows), freq="B")
    return pd.DataFrame(rows, index=index)


def _ready_prefix(size: int = 30) -> list[dict[str, float]]:
    return [
        {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 1_000_000.0}
        for _ in range(size)
    ]


def test_accepts_new_intraday_reversal_when_strict_v009_qualification_holds() -> None:
    rows = _ready_prefix()
    rows[-2]["Volume"] = 1_200_000.0
    rows[-1] = {
        "Open": 96.0,
        "High": 100.0,
        "Low": 94.0,
        "Close": 98.0,
        "Volume": 1_000_000.0,
    }
    frame = indicators(_bars(rows), DEFAULT_SPEC)
    assert bool(frame.iloc[-1]["close_above_prior_close"]) is False
    assert bool(frame.iloc[-1]["intraday_reversal_confirmation"]) is True
    assert bool(frame.iloc[-1]["raw_signal"]) is True


def test_rejects_close_below_prior_close_without_upper_third_close() -> None:
    rows = _ready_prefix()
    rows[-2]["Volume"] = 1_200_000.0
    rows[-1] = {
        "Open": 96.0,
        "High": 100.0,
        "Low": 90.0,
        "Close": 96.5,
        "Volume": 1_000_000.0,
    }
    frame = indicators(_bars(rows), DEFAULT_SPEC)
    assert bool(frame.iloc[-1]["intraday_reversal_confirmation"]) is False
    assert bool(frame.iloc[-1]["raw_signal"]) is False


def test_rejects_flat_intraday_range() -> None:
    rows = _ready_prefix()
    rows[-1] = {
        "Open": 99.0,
        "High": 99.0,
        "Low": 99.0,
        "Close": 99.0,
        "Volume": 1_000_000.0,
    }
    frame = indicators(_bars(rows), DEFAULT_SPEC)
    assert bool(frame.iloc[-1]["intraday_reversal_confirmation"]) is False


def test_original_v009_confirmation_remains_available() -> None:
    rows = _ready_prefix()
    rows[-2]["Volume"] = 1_200_000.0
    rows[-1] = {
        "Open": 96.0,
        "High": 100.0,
        "Low": 94.0,
        "Close": 98.0,
        "Volume": 1_000_000.0,
    }
    rows[-2]["Close"] = 97.0
    rows[-2]["Open"] = 98.0
    rows[-2]["High"] = 100.0
    rows[-2]["Low"] = 96.0
    frame = indicators(_bars(rows), DEFAULT_SPEC)
    assert bool(frame.iloc[-1]["same_day_v009_confirmation"]) is True
    assert bool(frame.iloc[-1]["raw_signal"]) is True
