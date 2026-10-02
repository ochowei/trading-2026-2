"""依明示的指標契約產生人造價格；訊號仍由策略引擎計算。"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


class RegimeContractError(ValueError):
    """契約無法由內建案例完整驗證；不代表策略失敗。"""


def regime_contract(indicator: dict) -> dict | None:
    regime = indicator.get("regime")
    if regime is None:
        return None
    if not isinstance(regime, dict):
        raise RegimeContractError("regime 必須是明示的均線比較契約")
    if (
        regime.get("kind") != "sma-comparison"
        or regime.get("operator") != ">"
        or regime.get("input") != "Close"
        or regime.get("include_current_session") is not True
        or regime.get("not_ready_allowed") is not False
    ):
        raise RegimeContractError("內建案例目前只支援含當日 Close、未就緒為 false 的 SMA fast>slow")
    for name in ("fast", "slow"):
        window = regime.get(name)
        if not isinstance(window, dict):
            raise RegimeContractError(f"regime 缺少 {name} 視窗")
        length, minimum = window.get("lookback"), window.get("min_periods")
        if (
            not isinstance(length, int)
            or isinstance(length, bool)
            or not isinstance(minimum, int)
            or isinstance(minimum, bool)
            or minimum != length
            or minimum < 2
            or not isinstance(window.get("column"), str)
        ):
            raise RegimeContractError("regime 視窗須完整暖機，並明列指標輸出欄位")
    if regime["fast"]["lookback"] >= regime["slow"]["lookback"]:
        raise RegimeContractError("regime fast 視窗必須短於 slow 視窗")
    names = [regime["fast"]["column"], regime["slow"]["column"], regime.get("allowed_column")]
    if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != 3:
        raise RegimeContractError("regime 的 fast、slow、允許欄位必須各自唯一")
    return regime


def make_sma_regime_bars(
    rows: int,
    signal_indices: Iterable[int],
    *,
    regime: str = "above",
    volume_lead_window: int = 5,
    fast_lookback: int = 20,
    slow_lookback: int = 50,
    variant: int = 0,
) -> pd.DataFrame:
    """先上升、再短期回檔反轉；持有期間留在平台，避免碰到 stop/target。

    seed 是價格事件的位置，不能當成訊號答案。相等案例只支援單一事件，
    以價格歷史讓兩個實際 rolling mean 相等，沒有注入指標或 raw_signal。
    日期只是連續人造工作日，不能作為正式 XNYS 市場資料。
    """

    seeds = list(signal_indices)
    if not seeds or regime not in {"above", "below", "equal"}:
        raise RegimeContractError("需明列價格事件與 above/below/equal 人造情境")
    if rows > 10000 or rows < 1 or any(not 1 <= seed < rows for seed in seeds):
        raise RegimeContractError("人造案例的列數或事件位置不合法")
    first = min(seeds)
    slope = 0.7 + variant * 0.05
    positions = np.minimum(np.arange(rows), first)
    baseline = 100.0 + slope * positions if regime == "above" else np.full(rows, 100.0)
    if regime == "below":
        baseline = 100.0 + slope * (first - positions)
    close = baseline.copy()
    for seed in seeds:
        close[seed - 1] = baseline[seed] * (0.85 - variant * 0.002)
        close[seed] = baseline[seed] * (0.90 - variant * 0.002)
    if regime == "equal":
        if len(seeds) != 1 or first < slow_lookback - 1:
            raise RegimeContractError("相等情境需單一已完整暖機事件")
        recent = close[first - fast_lookback + 1 : first + 1].mean()
        close[first - slow_lookback + 1 : first - fast_lookback + 1] = recent
    volume = np.full(rows, 1_000_000.0)
    for seed in seeds:
        if seed >= volume_lead_window:
            volume[seed - volume_lead_window] = 5_000_000.0
    return pd.DataFrame(
        {
            "Open": close.copy(),
            "High": close + 0.5,
            "Low": close - 0.5,
            "Close": close,
            "Volume": volume,
        },
        index=pd.date_range("2020-01-02", periods=rows, freq="B"),
    )


def verify_regime_frame(bars: pd.DataFrame, frame: pd.DataFrame, spec, indicator: dict) -> None:
    """由原始 Close 重算契約，不相信引擎自行宣稱的均線或通過結果。"""

    regime = regime_contract(indicator)
    undeclared = {name for name in frame if name.startswith("regime_")}
    if regime is None:
        if undeclared or "sma20_above_sma50" in frame:
            raise RegimeContractError("引擎有 regime 指標，但 implementation contract 未登記")
        return
    if not frame.index.equals(bars.index):
        raise ValueError("indicators 的日期與人造資料不一致")
    expected = {}
    for name in ("fast", "slow"):
        window = regime[name]
        column = window["column"]
        if column not in frame:
            raise ValueError(f"indicators 缺少 regime 欄位：{column}")
        expected[name] = (
            bars["Close"].rolling(window["lookback"], min_periods=window["min_periods"]).mean()
        )
        if not np.allclose(frame[column], expected[name], equal_nan=True, rtol=1e-12, atol=1e-12):
            raise ValueError(f"{column} 與原始 Close 重算的均線不一致")
    allowed = expected["fast"] > expected["slow"]
    column = regime["allowed_column"]
    if (
        column not in frame
        or frame[column].isna().any()
        or not frame[column].isin([True, False]).all()
    ):
        raise ValueError("regime 允許欄位必須是完整 boolean")
    if not (frame[column] == allowed).all():
        raise ValueError("regime 允許條件不符 strict > 或未就緒拒絕規則")
    if "raw_signal" not in frame:
        raise ValueError("indicators 缺少可驗證的 raw_signal")
    fields = {"mean_reversion_gap", "rsi_2", "prior_volume_spike_ratio", "close_above_prior_close"}
    if not fields.issubset(frame.columns):
        raise RegimeContractError("均線比較案例目前需要可核對的均值回歸、RSI 與成交量欄位")
    core = (frame["mean_reversion_gap"] >= spec.mean_reversion_min) & (
        frame["rsi_2"] <= spec.rsi_max
    )
    if spec.volume_lead_enabled:
        core &= frame["prior_volume_spike_ratio"] >= spec.volume_spike_ratio
    if spec.require_close_above_prior_close:
        core &= frame["close_above_prior_close"]
    if not (frame["raw_signal"] == (core & allowed)).all():
        raise ValueError("raw_signal 沒有完整套用已登記的基本條件與 regime 濾網")
