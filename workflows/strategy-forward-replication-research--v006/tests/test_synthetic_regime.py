"""只測人造資料與唯讀原生 guard；不使用會形成 RC 的 workflow_root fixture。"""

from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest
from operations import legacy_checks as native
from operations.synthetic_fixtures import (
    RegimeContractError,
    make_sma_regime_bars,
    regime_contract,
    verify_regime_frame,
)
from synthetic_helpers import PACKAGE, REGIME, make_context, refresh_bundle, write
from validator.canonical_yaml import load_canonical

VALUES = {"sma_lookback": 20, "rsi_lookback": 2, "volume_lookback": 20, "volume_lead_window": 5}


def load_engine(name: str):
    path = PACKAGE / "tests/fixtures/regime" / name
    loader = importlib.util.spec_from_file_location(f"_regime_test_{path.stem}", path)
    module = importlib.util.module_from_spec(loader)
    sys.modules[loader.name] = module
    loader.loader.exec_module(module)
    return module


@pytest.fixture
def engine():
    return load_engine("candidate_engine.py")


@pytest.fixture
def indicator():
    value = load_canonical(PACKAGE / "tests/fixtures/contract/implementation-contract.yml")[
        "indicator_contract"
    ]
    value.update(regime=deepcopy(REGIME), required_history_sessions=49)
    return value


def test_generator_is_deterministic_and_has_no_injected_signal():
    first = make_sma_regime_bars(150, [57, 71, 73])
    second = make_sma_regime_bars(150, [57, 71, 73])
    assert first.equals(second)
    assert set(first.columns) == {"Open", "High", "Low", "Close", "Volume"}
    assert not first.equals(make_sma_regime_bars(150, [57, 71, 73], variant=1))


@pytest.mark.parametrize(
    ("kind", "seed", "expected"),
    [
        ("above", 57, True),
        ("below", 57, False),
        ("equal", 57, False),
        ("above", 48, False),
        ("above", 49, True),
    ],
)
def test_real_indicators_and_backtest_boundaries(engine, indicator, kind, seed, expected):
    bars = make_sma_regime_bars(150, [seed], regime=kind)
    frame = engine.indicators(bars)
    verify_regime_frame(bars, frame, engine.DEFAULT_SPEC, indicator)
    assert bool(frame.raw_signal.iloc[seed]) is expected
    bt = engine.backtest(bars)
    assert (bars.index[seed] in bt.accepted_signal_sessions) is expected
    control = load_engine("control_engine.py")
    assert bool(control.indicators(bars).raw_signal.iloc[seed])
    assert bars.index[seed] in control.backtest(bars).accepted_signal_sessions
    if kind == "equal":
        assert frame.regime_sma20.iloc[seed] == frame.regime_sma50.iloc[seed]
    if seed == 48:
        assert np.isnan(frame.regime_sma50.iloc[seed])


def test_longest_declared_history_and_readiness(engine, indicator):
    assert native._derived_history_sessions(VALUES, indicator) == 49
    result = native.CheckResult("readiness")
    native._run_readiness_case(result, engine, engine.DEFAULT_SPEC, VALUES, indicator)
    assert result.details["first_ready_index"] == 49
    assert set(result.details["indicator_columns"].values()) >= {"regime_sma20", "regime_sma50"}
    longer = deepcopy(indicator)
    longer["regime"]["slow"].update(lookback=80, min_periods=80)
    assert native._derived_history_sessions(VALUES, longer) == 79


def test_native_two_time_exits_and_exact_cooldown_boundary(engine, indicator):
    contract = {"indicator_contract": indicator}
    result = native.CheckResult("holding")
    native._run_holding_cooldown_case(
        result, engine, engine.DEFAULT_SPEC, engine.BASE_COST, contract
    )
    audit = result.details["holding_cooldown_case"]
    assert len(audit["raw_signals"]) == 3
    assert len(audit["accepted_signals"]) == len(audit["trades"]) == 2
    assert audit["rejected_signals"][0]["reason"] == "cooldown-not-complete"
    bars = make_sma_regime_bars(180, [57, 71, 73])
    bt = engine.backtest(bars)
    assert audit["accepted_signal_seed"] == bars.index[73].isoformat()
    assert bt.trades[0].exit_session == bars.index[68]
    assert bt.trades[1].signal_session == bars.index[73]  # 已完成 5 個 session 步距
    assert bt.trades[1].entry_session == bars.index[74]
    assert all(trade.exit_reason == "time" and trade.held_sessions == 10 for trade in bt.trades)
    control = load_engine("control_engine.py").backtest(bars)
    assert bt.accepted_signal_sessions == control.accepted_signal_sessions
    assert [(t.entry_session, t.exit_session) for t in bt.trades] == [
        (t.entry_session, t.exit_session) for t in control.trades
    ]


def test_native_regime_cases_compute_values_and_digests(engine, indicator):
    result = native.CheckResult("regime")
    native._run_regime_case(result, engine, engine.DEFAULT_SPEC, engine.BASE_COST, indicator)
    cases = result.details["regime_cases"]
    assert set(cases) == {"above", "below", "equal", "not-ready", "just-ready"}
    assert cases["above"]["accepted_signals"]
    assert cases["equal"]["probe"]["filter_rejection"] == "sma-fast-not-above-slow"
    assert cases["not-ready"]["probe"]["slow_sma"] is None
    assert cases["just-ready"]["probe"]["index"] == 49
    assert all(len(case["data_digest"]) == 64 for case in cases.values())


def test_independent_cooldown_four_rejects_five_accepts(engine, indicator):
    result = native.CheckResult("cooldown-boundaries")
    native._run_cooldown_boundary_cases(
        result, engine, engine.DEFAULT_SPEC, engine.BASE_COST, indicator
    )
    cases = result.details["cooldown_boundary_cases"]
    before = cases["one-step-before-complete"]
    complete = cases["at-completion"]
    assert before["probe"] == {
        "index": 72,
        "steps_after_exit": 4,
        "raw_signal": True,
        "accepted": False,
    }
    assert before["rejected_signals"][0]["reason"] == "cooldown-not-complete"
    assert complete["probe"] == {
        "index": 73,
        "steps_after_exit": 5,
        "raw_signal": True,
        "accepted": True,
    }
    assert complete["trades"][1]["signal_session"] == complete["accepted_signals"][1]
    assert (
        complete["trades"][1]["entry_session"]
        == make_sma_regime_bars(180, [57, 73]).index[74].isoformat()
    )
    assert before["data_digest"] != complete["data_digest"]


def test_cooldown_ignored_by_wrong_backtest_is_implementation_invalid(engine, indicator):
    def ignore_cooldown(bars, spec, cost):
        return engine.backtest(bars, spec=spec.with_changes(cooldown_sessions=0), cost=cost)

    broken = SimpleNamespace(indicators=engine.indicators, backtest=ignore_cooldown)
    with pytest.raises(native.SyntheticFixtureInvalid) as error:
        native._run_cooldown_boundary_cases(
            native.CheckResult("cooldown"), broken, engine.DEFAULT_SPEC, engine.BASE_COST, indicator
        )
    assert error.value.classification == "strategy-implementation"


def test_early_exit_from_wrong_holding_is_implementation_invalid(engine, indicator):
    def wrong_holding(bars, spec, cost):
        return engine.backtest(bars, spec=spec.with_changes(holding_sessions=8), cost=cost)

    broken = SimpleNamespace(indicators=engine.indicators, backtest=wrong_holding)
    with pytest.raises(native.SyntheticFixtureInvalid) as error:
        native._run_cooldown_boundary_cases(
            native.CheckResult("holding"), broken, engine.DEFAULT_SPEC, engine.BASE_COST, indicator
        )
    assert error.value.classification == "strategy-implementation"


def test_original_flat_fixture_remains_invalid(engine, indicator):
    bars = native._make_bars(180, [57], close_direction="above")
    frame = engine.indicators(bars)
    assert frame.regime_sma20.iloc[57] == 99.25
    assert frame.regime_sma50.iloc[57] == 99.7
    assert not frame.raw_signal.any()
    assert load_engine("control_engine.py").indicators(bars).raw_signal.any()
    # 未明示 regime 的舊契約不會因新產生器而自動通過。
    missing = deepcopy(indicator)
    missing.pop("regime")
    with pytest.raises(RegimeContractError, match="未登記"):
        verify_regime_frame(bars, frame, engine.DEFAULT_SPEC, missing)


@pytest.mark.parametrize(
    "field", ["regime_sma20", "regime_sma50", "sma20_above_sma50", "raw_signal"]
)
def test_wrong_indicator_or_signal_is_rejected(engine, indicator, field):
    bars = make_sma_regime_bars(150, [57])
    frame = engine.indicators(bars)
    frame[field] = 0.0 if field.startswith("regime_sma") else False
    with pytest.raises(ValueError):
        verify_regime_frame(bars, frame, engine.DEFAULT_SPEC, indicator)


@pytest.mark.parametrize("change", ["operator", "input", "min_periods", "window_order"])
def test_unsupported_contract_is_not_fixture_or_strategy_failure(indicator, change):
    regime = indicator["regime"]
    if change == "operator":
        regime["operator"] = "<="
    elif change == "input":
        regime["input"] = "Open"
    elif change == "min_periods":
        regime["slow"]["min_periods"] = 25
    else:
        regime["fast"]["lookback"] = regime["fast"]["min_periods"] = 60
    with pytest.raises(RegimeContractError):
        regime_contract(indicator)


def test_missing_raw_output_is_implementation_invalid(engine, indicator):
    broken = SimpleNamespace(
        indicators=lambda bars, spec: engine.indicators(bars, spec).drop(columns="raw_signal"),
        backtest=engine.backtest,
    )
    result = native.CheckResult("signal")
    with pytest.raises(native.SyntheticFixtureInvalid) as error:
        native._run_signal_case(
            result,
            broken,
            engine.DEFAULT_SPEC,
            engine.BASE_COST,
            {"indicator_contract": indicator},
            indicator,
            VALUES,
        )
    assert error.value.classification == "strategy-implementation"


def test_valid_raw_signal_but_no_acceptance_is_implementation_invalid(engine, indicator):
    broken = SimpleNamespace(
        indicators=engine.indicators,
        backtest=lambda bars, spec, cost: SimpleNamespace(accepted_signal_sessions=(), trades=()),
    )
    with pytest.raises(native.SyntheticFixtureInvalid) as error:
        native._run_signal_case(
            native.CheckResult("signal"),
            broken,
            engine.DEFAULT_SPEC,
            engine.BASE_COST,
            {"indicator_contract": indicator},
            indicator,
            VALUES,
        )
    assert error.value.classification == "strategy-implementation"


def test_impossible_core_threshold_remains_fixture_invalid(engine, indicator):
    spec = engine.DEFAULT_SPEC.with_changes(mean_reversion_min=0.99)
    with pytest.raises(native.SyntheticFixtureInvalid) as error:
        native._run_signal_case(
            native.CheckResult("signal"),
            engine,
            spec,
            engine.BASE_COST,
            {"indicator_contract": indicator},
            indicator,
            VALUES,
        )
    assert error.value.classification == "fixture-invalid"


def test_contract_accepts_complete_synthetic_spec_and_rejects_original_short_warmup(tmp_path):
    good = make_context(tmp_path / "good")
    result = native.run_contract(good)
    assert result.status == "passed", result.errors
    short = make_context(tmp_path / "short", ready=False)
    result = native.run_contract(short)
    assert result.status == "failed"
    assert any(error["code"] == "fold-warmup-too-short" for error in result.errors)
    assert result.details["derived_required_history_sessions"] == 49


def test_regime_candidate_and_registration_must_match_contract(tmp_path):
    context = make_context(tmp_path)
    candidate = load_canonical(context.research_root / "candidate-definition.yml")
    candidate["signal"]["regime"]["slow"]["lookback"] = 60
    write(context.research_root, "candidate-definition.yml", candidate)
    refresh_bundle(context.repository_root, context.research_root)
    result = native.run_contract(context)
    assert any(
        error["code"] == "contract-value-mismatch" and "signal.regime" in error["message"]
        for error in result.errors
    )


def test_native_precreate_uses_full_guards_without_creating_study(tmp_path):
    context = make_context(tmp_path)
    result = native.run_precreate(context)
    assert result.status == "passed", result.errors
    assert {item["name"] for item in result.details["subchecks"]} == {"contract", "synthetic"}
    assert not context.study_root.exists()
    assert not (tmp_path / ".authority").exists()


def test_precreate_retains_short_warmup_rejection_even_when_synthetic_passes(tmp_path):
    context = make_context(tmp_path, ready=False)
    result = native.run_precreate(context)
    assert result.status == "failed"
    assert any(error["code"] == "fold-warmup-too-short" for error in result.errors)
    synthetic = next(item for item in result.details["subchecks"] if item["name"] == "synthetic")
    assert synthetic["status"] == "passed", synthetic["errors"]
    assert not context.study_root.exists()


def test_synthetic_results_do_not_depend_on_setting_id(tmp_path):
    first = native.run_synthetic(make_context(tmp_path / "one", study_id="human-fixture-a"))
    second = native.run_synthetic(make_context(tmp_path / "two", study_id="other-case-b"))
    assert first.status == second.status == "passed"
    for key in ("regime_cases", "signal_case", "holding_cooldown_case"):
        assert first.details[key] == second.details[key]
