"""隔離重現 v005 的 SMA 濾網案例不足；不執行任何 Study Lifecycle。"""

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

parser = argparse.ArgumentParser(description="只使用公開 v005 定義與人造價格重現原生案例限制")
parser.add_argument("--repository-root", type=Path, required=True)
args = parser.parse_args()
repo = args.repository_root.resolve()
source = repo / "workflows/strategy-forward-replication-research--v005"
manifest = yaml.safe_load((source / "release-manifest.yml").read_text())
root = Path(tempfile.mkdtemp(prefix="task037-repro-"))
package = root / "workflows/strategy-forward-replication-research--v005"
for item in manifest["files"]:
    rel = Path(item["path"])
    assert not {"studies", "runtime", "evidence", "authority"}.intersection(rel.parts)
    assert rel.name not in {"release.yml", "release-manifest.yml", "release-test-report.yml"}
    dst = package / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / rel, dst)
paths = [
    "src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_sma20_sma50_regime_v001.py",
    "src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py",
]
for rel in paths:
    dst = root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repo / rel, dst)
sys.path.insert(0, str(package))
from operations import legacy_checks as check  # noqa: E402
from validator.canonical_yaml import load_canonical  # noqa: E402

r = check.CheckResult("load")
module = check._load_engine(root / paths[0], r)
control = check._load_engine(root / paths[1], r)
assert module is not None and control is not None
contract = load_canonical(package / "tests/fixtures/contract/implementation-contract.yml")
contract["engine"]["path"] = paths[0]
contract["execution"]["exits"]["holding_exit"] = "next-open-after-10-complete-sessions"
indicator = contract["indicator_contract"]
values = {"sma_lookback": 20, "rsi_lookback": 2, "volume_lookback": 20, "volume_lead_window": 5}
result = check.CheckResult("native-synthetic")
for _name, fn in [
    (
        "signal",
        lambda: check._run_signal_case(
            result, module, module.DEFAULT_SPEC, module.BASE_COST, contract, indicator, values
        ),
    ),
    (
        "holding-cooldown",
        lambda: check._run_holding_cooldown_case(
            result, module, module.DEFAULT_SPEC, module.BASE_COST, contract
        ),
    ),
]:
    try:
        fn()
    except check.SyntheticFixtureInvalid as e:
        result.error("synthetic-" + e.classification, str(e))
summary = {
    "isolation": str(root),
    "engine": paths[0],
    "spec": "DEFAULT_SPEC",
    "source_sha256": hashlib.sha256((root / paths[0]).read_bytes()).hexdigest(),
    "contract_required_history": indicator["required_history_sessions"],
    "derived_history_v005": check._derived_history_sessions(values, indicator),
    "engine_fold_warmup": module.DEFAULT_SPEC.fold_warmup_sessions,
    "actual_regime_first_ready": 49,
    "native_errors": result.errors,
    "signal_attempts": result.details.get("signal_case_attempts"),
    "holding_attempt_count": len(result.details.get("holding_cooldown_attempts", [])),
    "samples": [],
}
for seed in [36, 49, 57, 65]:
    bars = check._make_bars(180, [seed], close_direction="above")
    frame = check._call_indicators(module, bars, module.DEFAULT_SPEC)
    bt = check._call_backtest(module, bars, module.DEFAULT_SPEC, module.BASE_COST)
    cb = check._call_backtest(control, bars, control.DEFAULT_SPEC, control.BASE_COST)
    row = frame.iloc[seed]
    summary["samples"].append(
        {
            "seed": seed,
            "sma20": None
            if row["regime_sma20"] != row["regime_sma20"]
            else float(row["regime_sma20"]),
            "sma50": None
            if row["regime_sma50"] != row["regime_sma50"]
            else float(row["regime_sma50"]),
            "regime": bool(row["sma20_above_sma50"]),
            "candidate_raw": int(frame.raw_signal.sum()),
            "candidate_accepted": len(bt.accepted_signal_sessions),
            "control_raw": int(control.indicators(bars).raw_signal.sum()),
            "control_accepted": len(cb.accepted_signal_sessions),
            "filter_rejection": "regime-not-ready" if seed < 49 else "sma20-not-above-sma50",
        }
    )
(root / "reproduction.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(json.dumps(summary, ensure_ascii=False, indent=2))
