from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_2026_2.tsm_mean_reversion_divergence_sma20_exit_v001 import (
    BASE_COST,
    SMA20_REENTRY_EXIT_SPEC,
    STRESS_COST,
    backtest,
)
from validator.canonical_yaml import load_canonical, write_canonical


def bars_from_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["Date"])
    if list(frame.columns) != ["Date", "Open", "High", "Low", "Close", "Volume"]:
        raise ValueError("輸入 CSV 欄位必須固定為 Date 與五個 OHLCV 欄")
    return frame.set_index("Date")


def text(value: float) -> str:
    return repr(float(value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    request = load_canonical(args.request)
    if request["stage"] != "historical-evaluation":
        raise ValueError("本 runner 僅接受 Historical Evaluation request")
    bars = bars_from_csv(Path(request["data_path"]))
    prereg = request["preregistration"]
    spec = SMA20_REENTRY_EXIT_SPEC.with_changes(
        initial_cash=float(prereg["initial_cash"]),
        mean_reversion_min=0.015,
        rsi_max=50.0,
        volume_spike_ratio=1.05,
        holding_sessions=10,
        cooldown_sessions=5,
        stop_return=-0.04,
        target_return=0.04,
        risk_fraction=0.02,
    )
    trades = []
    for year in range(2020, 2025):
        year_bars = bars.loc[
            (bars.index >= f"{year}-01-01") & (bars.index <= f"{year}-12-31")
        ]
        if year_bars.empty:
            continue
        base = backtest(
            year_bars,
            spec=spec,
            cost=BASE_COST,
            reset_at_start=True,
            signal_start=f"{year}-01-01",
            signal_end=f"{year}-12-31",
        )
        stress = backtest(
            year_bars,
            spec=spec,
            cost=STRESS_COST,
            reset_at_start=True,
            signal_start=f"{year}-01-01",
            signal_end=f"{year}-12-31",
        )
        if len(base.trades) != len(stress.trades):
            raise ValueError("base/stress 交易數不同")
        for index, (base_trade, stress_trade) in enumerate(
            zip(base.trades, stress.trades, strict=True), start=1
        ):
            lifecycle = (
                base_trade.signal_session,
                base_trade.entry_session,
                base_trade.exit_session,
            )
            stress_lifecycle = (
                stress_trade.signal_session,
                stress_trade.entry_session,
                stress_trade.exit_session,
            )
            if lifecycle != stress_lifecycle:
                raise ValueError("base/stress 交易生命週期不同")
            trades.append(
                {
                    "trade_id": f"{year}-{index:04d}",
                    "fold": year,
                    "signal_date": base_trade.signal_session.date().isoformat(),
                    "exit_date": base_trade.exit_session.date().isoformat(),
                    "order_type": "MARKET",
                    "base_pnl": text(base_trade.pnl),
                    "stress_pnl": text(stress_trade.pnl),
                }
            )
    gates = prereg["evaluation_gates"]
    write_canonical(
        args.output,
        {
            "schema_version": 1,
            "stage": "historical-evaluation",
            "initial_cash": prereg["initial_cash"],
            "family_wise_confidence": gates["family_wise_confidence"]["value"],
            "stress_drawdown_limit": gates["stress_max_drawdown"]["value"],
            "trades": trades,
        },
    )


if __name__ == "__main__":
    main()
