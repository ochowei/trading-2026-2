"""TSM v018 Historical Evaluation runner 的凍結前相容實作。

本檔案只在候選已凍結後才可對 2020--2024 evaluation view 使用。候選凍結前
本 Study 僅用 workflow 的 synthetic checks 驗證介面，絕不執行這個 runner，
也不連線資料供應商、券商或其他外部服務。
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd

from trading_2026_2.tsm_mean_reversion_two_stage_volume_reversal_v018 import (
    BASE_COST,
    DEFAULT_SPEC,
    STRESS_COST,
    backtest,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import atomic_create, canonical_bytes, load_canonical  # noqa: E402

CANDIDATE_ID = "tsm-mr-two-stage-volume-reversal-shallow-reversal-v018"
SYMBOL = "TSM"


def _decimal_text(value: int | float) -> str:
    return format(Decimal(str(value)).normalize(), "f")


def _engine_signal() -> dict[str, object]:
    """由 frozen spec 組出候選 signal，避免另抄一份參數。"""

    spec = DEFAULT_SPEC
    return {
        "accepted_only_when_flat": True,
        "cooldown": {
            "clock_anchor": "completed-position-exit",
            "completed_session_steps_after_exit": spec.cooldown_sessions,
        },
        "decision_time": "completed-session-close",
        "mean_reversion": {
            "close_vs_sma20_gap_minimum": _decimal_text(spec.mean_reversion_min),
            "rsi_length": spec.rsi_lookback,
            "rsi_maximum": _decimal_text(spec.rsi_max),
            "sma_length": spec.sma_lookback,
        },
        "original_path": {
            "close_above_prior_close": spec.require_close_above_prior_close,
            "gap_operator": ">=",
            "gap_value": _decimal_text(spec.mean_reversion_min),
            "volume_lead_enabled": spec.volume_lead_enabled,
            "volume_lead_window": spec.volume_lead_window,
            "volume_ratio_minimum": _decimal_text(spec.volume_spike_ratio),
        },
        "price_direction_confirmation": {
            "close_above_prior_close": spec.require_close_above_prior_close,
        },
        "supplemental_path": {
            "close_above_prior_close": True,
            "gap_lower_inclusive": "0.010",
            "gap_upper_exclusive": _decimal_text(spec.supplemental_gap_max_exclusive),
            "low_t_minus_1_operator": ">=",
            "low_t_minus_2_reference": True,
            "price_return_t_minus_1_operator": "<=",
            "price_return_t_minus_2_operator": "<",
            "rsi_maximum": _decimal_text(spec.supplemental_rsi_max),
            "volume_average_excludes_current_day": True,
            "volume_average_length": spec.volume_lookback,
            "volume_ratio_minimum": _decimal_text(spec.volume_spike_ratio),
            "volume_t_minus_1_operator": ">=",
            "volume_t_minus_2_operator": ">=",
        },
        "symbol": SYMBOL,
        "volume_leads_price": {
            "enabled": spec.volume_lead_enabled,
            "prior_session_window": spec.volume_lead_window,
            "volume_average_length": spec.volume_lookback,
            "volume_ratio_minimum": _decimal_text(spec.volume_spike_ratio),
            "volume_ratio_operator": ">=",
            "volume_ratio_value": _decimal_text(spec.volume_spike_ratio),
            "volume_shock_is_before_signal": True,
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="產生 TSM v018 2020--2024 raw evidence")
    result.add_argument("--evaluation", type=Path, required=True)
    result.add_argument("--candidate-definition", type=Path, required=True)
    result.add_argument("--preregistration", type=Path, required=True)
    result.add_argument("--qualification-spec", type=Path, required=True)
    result.add_argument("--snapshot-set", type=Path, required=True)
    result.add_argument("--source-bundle", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_frozen_inputs(args: argparse.Namespace) -> dict:
    candidate = load_canonical(args.candidate_definition)
    preregistration = load_canonical(args.preregistration)
    qualification = load_canonical(args.qualification_spec)
    snapshot_set = load_canonical(args.snapshot_set)
    source_bundle = load_canonical(args.source_bundle)
    if candidate["signal"]["symbol"] != SYMBOL:
        raise RuntimeError("Candidate definition 不是 TSM")
    if candidate["signal"] != _engine_signal():
        raise RuntimeError("Candidate definition signal 與 frozen strategy 不一致")
    if candidate["signal"]["symbol"] != preregistration["eligibility_rules"]["accepted_signal"]["symbol"]:
        raise RuntimeError("Candidate 與 preregistration symbol 不一致")
    if candidate["execution"]["maximum_holding_session_span_for_validator"] != preregistration["maximum_holding_sessions"]:
        raise RuntimeError("Candidate maximum holding span 與 preregistration 不一致")
    if candidate["execution"]["held_complete_sessions"] + 1 != preregistration["maximum_holding_sessions"]:
        raise RuntimeError("Candidate holding period 與 validator span 不一致")
    if candidate["costs"] != preregistration["eligibility_rules"]["costs"]:
        raise RuntimeError("Candidate costs 與 preregistration 不一致")
    if preregistration["selection_rule"]["selected_candidate_id"] != CANDIDATE_ID:
        raise RuntimeError("preregistration selected candidate identity 不正確")
    if preregistration["fold_warmup_sessions"] != DEFAULT_SPEC.fold_warmup_sessions:
        raise RuntimeError("fold warmup 與 frozen engine 不一致")
    if qualification["development"] != preregistration["eligibility_rules"]["development_gates"]:
        raise RuntimeError("Development gates 不是單一來源")
    if qualification["evaluation"] != preregistration["evaluation_gates"]:
        raise RuntimeError("Evaluation gates 不是單一來源")
    evaluation_snapshot = next(
        item for item in snapshot_set["snapshots"] if item["role"] == "historical-evaluation"
    )
    if digest(args.evaluation) != evaluation_snapshot["data_digest"]:
        raise RuntimeError("Evaluation snapshot digest 與 frozen snapshot set 不一致")
    for item in source_bundle["files"]:
        path = (REPOSITORY_ROOT / item["path"]).resolve()
        try:
            path.relative_to(REPOSITORY_ROOT)
        except ValueError as exc:
            raise RuntimeError(f"Source Bundle 路徑逃出 repository: {item['path']}") from exc
        if not path.is_file() or digest(path) != item["digest"]:
            raise RuntimeError(f"Source Bundle digest drift: {item['path']}")
    return preregistration


def historical_evidence(bars: pd.DataFrame, preregistration: dict) -> dict:
    trades: list[dict[str, object]] = []
    counter = 1
    for year in range(2020, 2025):
        fold = bars.loc[f"{year}-01-01":f"{year}-12-31"]
        base = backtest(fold, spec=DEFAULT_SPEC, cost=BASE_COST, reset_at_start=True)
        stress = backtest(fold, spec=DEFAULT_SPEC, cost=STRESS_COST, reset_at_start=True)
        if len(base.trades) != len(stress.trades):
            raise RuntimeError("base 與 stress 的 Evaluation 交易數不一致")
        for base_trade, stress_trade in zip(base.trades, stress.trades, strict=True):
            if (
                base_trade.signal_session,
                base_trade.entry_session,
                base_trade.exit_session,
                base_trade.exit_reason,
            ) != (
                stress_trade.signal_session,
                stress_trade.entry_session,
                stress_trade.exit_session,
                stress_trade.exit_reason,
            ):
                raise RuntimeError("base 與 stress 的 Evaluation 交易生命週期不一致")
            if base_trade.signal_session.year != year or base_trade.exit_session.year != year:
                raise RuntimeError("Evaluation trade 不得跨越 fold")
            trades.append(
                {
                    "trade_id": f"evaluation-{counter:03d}",
                    "fold": year,
                    "signal_date": str(base_trade.signal_session.date()),
                    "exit_date": str(base_trade.exit_session.date()),
                    "order_type": "MARKET",
                    "entry_mode": base_trade.signal_origin,
                    "base_pnl": str(float(base_trade.pnl)),
                    "stress_pnl": str(float(stress_trade.pnl)),
                }
            )
            counter += 1
    return {
        "schema_version": 1,
        "stage": "historical-evaluation",
        "initial_cash": preregistration["initial_cash"],
        "family_wise_confidence": preregistration["evaluation_gates"]["family_wise_confidence"]["value"],
        "stress_drawdown_limit": preregistration["evaluation_gates"]["stress_max_drawdown"]["value"],
        "trades": trades,
    }


def main() -> int:
    args = parser().parse_args()
    if args.output.exists():
        raise RuntimeError("拒絕覆寫既有 Historical Evaluation output")
    preregistration = validate_frozen_inputs(args)
    bars = pd.read_csv(args.evaluation, parse_dates=["Date"], index_col="Date")
    atomic_create(args.output, canonical_bytes(historical_evidence(bars, preregistration)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
