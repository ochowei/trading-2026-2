"""從已發布且 digest 驗證的 Development raw trades 重算 TASK-023 研究目標。

本程式只輸出補充計算，不寫入 Workflow evidence，不參與 v005 eligibility。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from validator.canonical_yaml import canonical_digest, load_canonical

INITIAL_CASH = Decimal("100000")
MIN_NONOVERLAPPING_OVERLAY_TRADES = 5


def _raw_artifact(root: Path, reference: dict) -> tuple[Path, dict]:
    path = (root / reference["path"]).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("publication artifact path escapes repository") from exc
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference["digest"]:
        raise ValueError(f"publication artifact digest mismatch: {reference['path']}")
    return path, load_canonical(path)


def _pnl(trade: dict) -> Decimal:
    return Decimal(trade["stress"]["pnl"])


def _maximum_drawdown(trades: list[dict]) -> Decimal:
    equity = INITIAL_CASH
    peak = equity
    maximum = Decimal("0")
    previous_exit: date | None = None
    for trade in trades:
        exit_day = date.fromisoformat(trade["exit_session"])
        if previous_exit is not None and exit_day < previous_exit:
            raise ValueError("raw trades are not in chronological exit order")
        previous_exit = exit_day
        equity += _pnl(trade)
        peak = max(peak, equity)
        if peak > 0:
            maximum = max(maximum, (peak - equity) / peak)
    return maximum


def _overlap(left: dict, right: dict) -> bool:
    left_start = date.fromisoformat(left["entry_session"])
    left_end = date.fromisoformat(left["exit_session"])
    right_start = date.fromisoformat(right["entry_session"])
    right_end = date.fromisoformat(right["exit_session"])
    # 兩端都包含；同一個 XNYS session 持有即視為重疊。
    return left_start <= right_end and right_start <= left_end


def calculate(candidate: dict, baseline: dict) -> dict:
    candidate_trades = candidate["trades"]
    baseline_trades = baseline["trades"]
    if any("strategy_component" not in trade for trade in candidate_trades):
        raise ValueError("candidate raw trade 缺 runner 產生的 strategy_component")
    if any(trade.get("strategy_component") != "v009" for trade in baseline_trades):
        raise ValueError("baseline raw trade 並非固定 v009 component")

    overlay_trades = [
        trade for trade in candidate_trades
        if trade["strategy_component"] == "industry-relative-lag"
    ]
    candidate_v009 = {
        trade["signal_session"]
        for trade in candidate_trades
        if trade["strategy_component"] == "v009"
    }
    baseline_by_signal = {trade["signal_session"]: trade for trade in baseline_trades}
    if len(baseline_by_signal) != len(baseline_trades):
        raise ValueError("baseline 含重複 signal_session，無法固定對照")
    displaced = [
        trade for signal, trade in baseline_by_signal.items()
        if signal not in candidate_v009
    ]
    nonoverlap = [
        trade for trade in overlay_trades
        if not any(_overlap(trade, baseline_trade) for baseline_trade in baseline_trades)
    ]

    candidate_stress_pnl = sum((_pnl(trade) for trade in candidate_trades), Decimal("0"))
    baseline_stress_pnl = sum((_pnl(trade) for trade in baseline_trades), Decimal("0"))
    delta = candidate_stress_pnl - baseline_stress_pnl
    candidate_drawdown = _maximum_drawdown(candidate_trades)
    baseline_drawdown = _maximum_drawdown(baseline_trades)
    simultaneous = [
        trade for trade in candidate_trades
        if set(trade.get("trigger_components", [])) == {"v009", "industry-relative-lag"}
    ]

    return {
        "formal_qualification": "由 v005 validator 獨立判定；本程式不修改 qualification",
        "definitions": {
            "nonoverlap": "candidate 中 industry-relative-lag 成交的 entry–exit inclusive 區間，不與任一 isolated v009 baseline 成交區間共享 XNYS session",
            "displaced_v009": "isolated v009 baseline 有成交、但 candidate 中沒有相同 signal_session 的 v009 component 成交；候選 runner 固定只有 overlay 持倉／冷卻造成缺席，v009 同日訊號則優先",
            "net_stress_pnl": "candidate 全部已實現 stress PnL 合計減 isolated v009 baseline 全部已實現 stress PnL 合計；同一初始資金與每筆交易成本，差額包含未執行的 baseline 成交與組合部位順序影響",
            "stress_drawdown": "依 raw stress pnl 的完成交易順序，初始資金 100000、每筆 pnl 後更新資金峰值，取最大 (peak-equity)/peak；與 v005 development validator 使用的 realized trade-to-trade drawdown 一致",
        },
        "signal_overlap_count": len(simultaneous),
        "displaced_v009_trade_count": len(displaced),
        "displaced_v009_stress_pnl": str(sum((_pnl(trade) for trade in displaced), Decimal("0"))),
        "nonoverlapping_overlay_trade_count": len(nonoverlap),
        "nonoverlapping_overlay_target": {
            "operator": ">=",
            "value": MIN_NONOVERLAPPING_OVERLAY_TRADES,
            "passed": len(nonoverlap) >= MIN_NONOVERLAPPING_OVERLAY_TRADES,
        },
        "candidate_stress_pnl": str(candidate_stress_pnl),
        "v009_stress_pnl": str(baseline_stress_pnl),
        "stress_net_pnl_after_displacement": str(delta),
        "stress_net_pnl_target": {"operator": ">", "value": "0", "passed": delta > 0},
        "candidate_stress_realized_maximum_drawdown": str(candidate_drawdown),
        "v009_stress_realized_maximum_drawdown": str(baseline_drawdown),
        "stress_drawdown_target": {
            "operator": "<=",
            "passed": candidate_drawdown <= baseline_drawdown,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--publication", type=Path, required=True)
    args = parser.parse_args()
    root = args.repository_root.resolve()
    publication_path = args.publication.resolve()
    try:
        publication_path.relative_to(root)
    except ValueError as exc:
        raise SystemExit("publication path must stay inside repository") from exc
    publication = load_canonical(publication_path)
    _, candidate = _raw_artifact(root, publication["artifacts"]["candidate"])
    _, baseline = _raw_artifact(root, publication["artifacts"]["baseline"])
    _, inputs = _raw_artifact(root, publication["artifacts"]["inputs"])
    if publication["envelope_digest"] != canonical_digest(
        {"candidate": candidate, "baseline": baseline}
    ):
        raise SystemExit("publication envelope digest mismatch")
    if publication["trial_id"] != inputs.get("trial_id"):
        raise SystemExit("publication trial identity mismatch")
    if publication["source_bundle_digest"] != inputs.get("source_bundle_digest"):
        raise SystemExit("publication source bundle binding mismatch")
    if publication["preregistration_digest"] != inputs.get("preregistration_digest"):
        raise SystemExit("publication preregistration binding mismatch")
    baseline_id = inputs.get("baseline_comparison", {}).get("baseline_id")
    inputs_digest = canonical_digest(inputs)
    if candidate.get("candidate_id") != inputs.get("candidate_id"):
        raise SystemExit("candidate evidence identity mismatch")
    if baseline.get("candidate_id") != baseline_id:
        raise SystemExit("baseline evidence identity mismatch")
    for evidence in (candidate, baseline):
        if (
            evidence.get("stage") != "development"
            or evidence.get("bindings", {}).get("source_bundle_digest")
            != publication["source_bundle_digest"]
            or evidence.get("bindings", {}).get("preregistration_digest")
            != publication["preregistration_digest"]
            or evidence.get("bindings", {}).get("trial_inputs_digest")
            != inputs_digest
        ):
            raise SystemExit("raw Development evidence publication binding mismatch")
    asset_digest = canonical_digest(inputs["data_bindings"]["assets"])
    if publication.get("data_assets_digest") != asset_digest or any(
        evidence.get("bindings", {}).get("data_assets_digest") != asset_digest
        for evidence in (candidate, baseline)
    ):
        raise SystemExit("publication data assets digest mismatch")
    result = calculate(candidate, baseline)
    result["bindings"] = {
        "publication_digest": hashlib.sha256(publication_path.read_bytes()).hexdigest(),
        "candidate_digest": publication["artifacts"]["candidate"]["digest"],
        "baseline_digest": publication["artifacts"]["baseline"]["digest"],
        "inputs_digest": publication["artifacts"]["inputs"]["digest"],
        "source_bundle_digest": publication["source_bundle_digest"],
        "preregistration_digest": publication["preregistration_digest"],
        "data_assets_digest": asset_digest,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
