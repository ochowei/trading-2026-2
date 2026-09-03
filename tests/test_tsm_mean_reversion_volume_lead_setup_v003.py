"""v003「量先於價」訊號契約測試。"""

import numpy as np
import pandas as pd

from trading_2026_2.tsm_mean_reversion_volume_lead_setup_v003 import (
    BASELINE_SPEC,
    DEFAULT_SPEC,
    indicators,
)


def setup_bars() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=30)
    close = np.full(30, 100.0)
    close[24] = 98.0
    close[25] = 97.0
    volume = np.full(30, 100.0)
    volume[24] = 200.0
    volume[25] = 100_000.0
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )


def test_volume_lead_setup_does_not_require_signal_day_up_close() -> None:
    result = indicators(setup_bars(), spec=DEFAULT_SPEC)
    signal = result.iloc[25]

    assert signal["mean_reversion_gap"] >= 0.02
    assert signal["rsi_2"] <= 35.0
    assert signal["prior_volume_spike_ratio"] >= 1.25
    assert signal["close_above_prior_close"] is False or not bool(
        signal["close_above_prior_close"]
    )
    assert bool(signal["raw_signal"])


def test_baseline_keeps_same_mean_reversion_setup_without_volume_filter() -> None:
    result = indicators(setup_bars(), spec=BASELINE_SPEC)

    assert not BASELINE_SPEC.volume_lead_enabled
    assert not BASELINE_SPEC.require_close_above_prior_close
    assert bool(result.iloc[25]["raw_signal"])
