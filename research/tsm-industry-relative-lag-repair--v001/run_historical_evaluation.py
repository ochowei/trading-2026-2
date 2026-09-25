"""v005 request runner 的 Historical Evaluation 入口。

本 TASK 不會呼叫正式入口；prepare 只以 Workflow runner-contract 中的合成資料
檢查回應格式。正式評估仍須另有評估角色與 assignment。
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd
from validator.canonical_yaml import atomic_create, canonical_bytes, load_canonical

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_engine as engine  # noqa: E402


def _load(path: Path, digest: str) -> pd.DataFrame:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("runner request 的 Historical Evaluation data digest 不一致")
    frame = pd.read_csv(path, parse_dates=["Date"])
    if list(frame.columns) != ["Date", "Open", "High", "Low", "Close", "Volume"]:
        raise ValueError("Historical Evaluation OHLCV 欄位不符")
    frame = frame.set_index("Date")
    frame.index = pd.DatetimeIndex(frame.index).tz_localize(None).normalize()
    return frame.astype(float)


def _bars(request: dict) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
    assets = request.get("data_assets")
    if assets is None:
        # Workflow preflight 的 Historical runner fixtures 固定為單一合成序列。
        # 真正的多資產 Evaluation request 則必須提供 TSM／SOXX roster。
        path = Path(request["data_path"])
        if not path.is_absolute():
            path = Path.cwd() / path
        bars = _load(path, request["data_digest"])
        return bars, bars.copy(), True

    loaded: dict[str, pd.DataFrame] = {}
    for asset in assets:
        path = Path(asset["data_path"])
        if not path.is_absolute():
            path = Path.cwd() / path
        loaded[asset["asset_id"]] = _load(path, asset["data_digest"])
    if set(loaded) != {"SOXX", "TSM"} or not loaded["TSM"].index.equals(loaded["SOXX"].index):
        raise ValueError("Historical Evaluation 必須完整提供已對齊的 SOXX／TSM")
    return loaded["TSM"], loaded["SOXX"], False


def build_result(request: dict) -> dict:
    if request.get("stage") != "historical-evaluation":
        raise ValueError("Historical Evaluation runner 收到錯誤 stage")
    prereg = request["preregistration"]
    tsm, soxx, _ = _bars(request)
    all_trades = []
    for year in range(2020, 2025):
        trades = engine.combined_backtest(
            tsm,
            soxx,
            cost=engine.BASE_COST,
            signal_start=f"{year}-01-01",
            signal_end=f"{year}-12-31",
        )
        stress = engine.combined_backtest(
            tsm,
            soxx,
            cost=engine.STRESS_COST,
            signal_start=f"{year}-01-01",
            signal_end=f"{year}-12-31",
        )
        base_signature = [
            (trade.signal_session, trade.entry_session, trade.exit_session, trade.strategy_component)
            for trade in trades
        ]
        stress_signature = [
            (trade.signal_session, trade.entry_session, trade.exit_session, trade.strategy_component)
            for trade in stress
        ]
        if base_signature != stress_signature:
            raise ValueError("Evaluation base/stress 成本改變成交路徑")
        for base, stressed in zip(trades, stress, strict=True):
            if base.signal_session.year != year:
                continue
            if base.exit_reason.startswith("stop"):
                order_type = "STOP_MARKET"
            elif base.exit_reason.startswith("target"):
                order_type = "LIMIT"
            else:
                order_type = "MARKET"
            all_trades.append(
                {
                    "trade_id": f"{base.strategy_component}:{base.signal_session:%Y-%m-%d}",
                    "fold": year,
                    "signal_date": base.signal_session.strftime("%Y-%m-%d"),
                    "exit_date": base.exit_session.strftime("%Y-%m-%d"),
                    "order_type": order_type,
                    "base_pnl": str(float(base.pnl)),
                    "stress_pnl": str(float(stressed.pnl)),
                }
            )
    return {
        "schema_version": 1,
        "stage": "historical-evaluation",
        "initial_cash": prereg["initial_cash"],
        "family_wise_confidence": prereg["evaluation_gates"]["family_wise_confidence"]["value"],
        "stress_drawdown_limit": prereg["evaluation_gates"]["stress_max_drawdown"]["value"],
        "trades": all_trades,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = load_canonical(args.request)
    atomic_create(args.output, canonical_bytes(build_result(request)))


if __name__ == "__main__":
    main()
