"""Fixed v005 Historical Evaluation runner source; prepare invokes it on synthetic data only."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path.cwd().resolve()
WORKFLOW_ROOT = ROOT / "workflows" / "strategy-forward-replication-research--v005"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import atomic_create, canonical_bytes, canonical_digest, load_canonical  # noqa: E402

ENGINE = "src/trading_2026_2/tsm_mean_reversion_selling_pressure_core_first_v001.py"


def load_candidate():
    path = (ROOT / ENGINE).resolve()
    path.relative_to(ROOT)
    spec = importlib.util.spec_from_file_location("_task032_core_first_evaluation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("無法載入 Source Bundle 綁定的 Candidate engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_bars(request: dict) -> pd.DataFrame:
    if isinstance(request.get("data_assets"), list):
        selected = [asset for asset in request["data_assets"] if asset.get("use") == "trade"]
        if len(selected) != 1:
            raise RuntimeError("TSM Evaluation 必須且只能有一個 trade asset")
        asset = selected[0]
        relative = Path(asset["data_path"])
        digest = asset["data_digest"]
    else:
        relative = Path(request["data_path"])
        digest = request["data_digest"]
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError("拒絕讀取隔離 repository 外的 Evaluation asset")
    path = (ROOT / relative).resolve()
    path.relative_to(ROOT)
    if canonical_digest(path.read_bytes()) != digest:
        raise RuntimeError("Evaluation asset digest 不一致")
    bars = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
    if list(bars.columns) != ["Open", "High", "Low", "Close", "Volume"]:
        raise RuntimeError("Evaluation CSV 欄位不符合固定 OHLCV schema")
    if bars.empty or bars.index.has_duplicates or not bars.index.is_monotonic_increasing:
        raise RuntimeError("Evaluation CSV session 空白、重複或未排序")
    return bars


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError("拒絕覆寫 Historical Evaluation output")
    request = load_canonical(args.request)
    if request.get("stage") != "historical-evaluation":
        raise RuntimeError("Historical Evaluation runner 只接受 historical-evaluation stage")
    preregistration = request["preregistration"]
    bars = load_bars(request)
    candidate = load_candidate()
    trades = []
    counter = 1
    for year in range(2020, 2025):
        fold = bars.loc[f"{year}-01-01":f"{year}-12-31"]
        if fold.empty:
            continue
        base = candidate.backtest(
            fold,
            spec=candidate.DEFAULT_SPEC,
            cost=candidate.BASE_COST,
            reset_at_start=True,
        )
        stress = candidate.backtest(
            fold,
            spec=candidate.DEFAULT_SPEC,
            cost=candidate.STRESS_COST,
            reset_at_start=True,
        )
        if len(base.trades) != len(stress.trades):
            raise RuntimeError("base 與 stress 的 Evaluation 交易數不一致")
        for base_trade, stress_trade in zip(base.trades, stress.trades, strict=True):
            left = (
                base_trade.signal_session,
                base_trade.entry_session,
                base_trade.exit_session,
                base_trade.exit_reason,
            )
            right = (
                stress_trade.signal_session,
                stress_trade.entry_session,
                stress_trade.exit_session,
                stress_trade.exit_reason,
            )
            if left != right:
                raise RuntimeError("base 與 stress 的 Evaluation trade lifecycle 不一致")
            if base_trade.signal_session.year != year or base_trade.exit_session.year != year:
                raise RuntimeError("Evaluation trade 不得跨越 fold")
            trades.append(
                {
                    "trade_id": f"evaluation-{counter:04d}",
                    "fold": year,
                    "signal_date": base_trade.signal_session.strftime("%Y-%m-%d"),
                    "exit_date": base_trade.exit_session.strftime("%Y-%m-%d"),
                    "order_type": "MARKET",
                    "base_pnl": repr(float(base_trade.pnl)),
                    "stress_pnl": repr(float(stress_trade.pnl)),
                }
            )
            counter += 1
    gates = preregistration["evaluation_gates"]
    result = {
        "schema_version": 1,
        "stage": "historical-evaluation",
        "initial_cash": preregistration["initial_cash"],
        "family_wise_confidence": gates["family_wise_confidence"]["value"],
        "stress_drawdown_limit": gates["stress_max_drawdown"]["value"],
        "trades": trades,
    }
    atomic_create(args.output, canonical_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
