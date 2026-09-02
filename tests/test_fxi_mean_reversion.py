from __future__ import annotations

import numpy as np
import pandas as pd

from trading_2026_2.fxi_mean_reversion import (
    CostModel,
    StrategySpec,
    _intraday_exit,
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


def test_signal_uses_adjusted_high_williams_and_wilder_atr() -> None:
    sample = bars(25)
    sample.loc[sample.index[-10] :, "High"] = [100, 100, 100, 100, 100, 100, 100, 100, 100, 92]
    sample.loc[sample.index[-10] :, "Low"] = [90, 90, 90, 90, 90, 90, 90, 90, 90, 88]
    sample.loc[sample.index[-1], ["Open", "Close"]] = [89, 89]
    # 拉高最近五日 true range，讓 ATR(5) / ATR(20) 明確高於 1.05。
    sample.loc[sample.index[-5] :, "High"] = [101, 101, 101, 101, 92]
    sample.loc[sample.index[-5] :, "Low"] = [87, 87, 87, 87, 88]
    result = indicators(sample)
    final = result.iloc[-1]
    assert 0.05 <= final["pullback"] <= 0.12
    assert final["williams_r_10"] <= -80
    assert final["atr_ratio"] > 1.05
    assert bool(final["raw_signal"])


def test_same_session_target_and_stop_uses_stop() -> None:
    bar = pd.Series({"Open": 100.0, "High": 106.0, "Low": 94.0})
    assert _intraday_exit(bar, target=105.5, stop=95.0) == (
        95.0,
        "stop-same-session",
    )


def test_stop_gap_fills_at_open_not_at_stop() -> None:
    bar = pd.Series({"Open": 93.0, "High": 96.0, "Low": 92.0})
    assert _intraday_exit(bar, target=105.5, stop=95.0) == (93.0, "stop-gap")


def test_target_gap_receives_open_price_improvement() -> None:
    bar = pd.Series({"Open": 107.0, "High": 108.0, "Low": 106.0})
    assert _intraday_exit(bar, target=105.5, stop=95.0) == (107.0, "target-gap")


def test_cooldown_requires_seven_completed_session_steps() -> None:
    sample = bars(35)
    spec = StrategySpec(holding_sessions=1, cooldown_sessions=7, fold_warmup_sessions=0)
    prepared = indicators(sample, spec)
    prepared["raw_signal"] = False
    prepared.loc[prepared.index[[19, 22, 26]], "raw_signal"] = True

    # 將測試已算好的訊號注入 runner，隔離 cooldown 行為。
    import trading_2026_2.fxi_mean_reversion as module

    original = module.indicators
    module.indicators = lambda _bars, _spec: prepared  # type: ignore[assignment]
    try:
        result = backtest(sample, spec=spec, cost=CostModel(0, 0), reset_at_start=True)
    finally:
        module.indicators = original
    assert result.accepted_signal_sessions == (
        prepared.index[19],
        prepared.index[26],
    )


def test_time_exit_occurs_after_twenty_complete_holding_sessions() -> None:
    sample = bars(50)
    spec = StrategySpec(holding_sessions=20, fold_warmup_sessions=0)
    prepared = indicators(sample, spec)
    prepared["raw_signal"] = False
    prepared.loc[prepared.index[20], "raw_signal"] = True

    import trading_2026_2.fxi_mean_reversion as module

    original = module.indicators
    module.indicators = lambda _bars, _spec: prepared  # type: ignore[assignment]
    try:
        result = backtest(sample, spec=spec, cost=CostModel(0, 0), reset_at_start=True)
    finally:
        module.indicators = original
    trade = result.trades[0]
    assert trade.entry_session == sample.index[21]
    assert trade.exit_session == sample.index[41]
    assert trade.held_sessions == 20
    assert trade.exit_reason == "time"


def test_last_signal_is_suppressed_when_fold_cannot_contain_time_exit() -> None:
    sample = bars(30)
    spec = StrategySpec(holding_sessions=20, fold_warmup_sessions=0)
    prepared = indicators(sample, spec)
    prepared["raw_signal"] = False
    prepared.loc[prepared.index[9], "raw_signal"] = True

    import trading_2026_2.fxi_mean_reversion as module

    original = module.indicators
    module.indicators = lambda _bars, _spec: prepared  # type: ignore[assignment]
    try:
        result = backtest(sample, spec=spec, cost=CostModel(0, 0), reset_at_start=True)
    finally:
        module.indicators = original
    assert result.accepted_signal_sessions == ()
    assert result.trades == ()


def test_development_warmup_cannot_accept_signal_before_2014() -> None:
    sample = bars(50)
    sample.index = pd.bdate_range("2013-12-02", periods=50)
    spec = StrategySpec(holding_sessions=1)
    prepared = indicators(sample, spec)
    prepared["raw_signal"] = False
    prepared.loc[prepared.index[[20, 25]], "raw_signal"] = True

    import trading_2026_2.fxi_mean_reversion as module

    original = module.indicators
    module.indicators = lambda _bars, _spec: prepared  # type: ignore[assignment]
    try:
        result = backtest(
            sample,
            spec=spec,
            cost=CostModel(0, 0),
            signal_start="2014-01-01",
            signal_end="2018-12-31",
        )
    finally:
        module.indicators = original
    assert all(session.year >= 2014 for session in result.accepted_signal_sessions)
    assert result.accepted_signal_sessions == (prepared.index[25],)
