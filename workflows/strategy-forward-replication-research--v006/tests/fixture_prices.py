"""只建立人造價格，供開發檢查與執行者的 terminal 整合案例共用。"""

from __future__ import annotations

import exchange_calendars as xcals
from operations.legacy_checks import _make_bars


def evaluation_rows(*, passing: bool) -> list[list[str]]:
    calendar = xcals.get_calendar("XNYS")
    rows = []
    for year in range(2020, 2025):
        days = calendar.sessions_in_range(f"{year}-01-01", f"{year}-12-31")
        # 每年分開建立就緒歷史；至少 30 列間距，避免持倉與冷卻重疊。
        seeds = list(range(36, len(days) - 18, 30)) if passing else []
        frame = _make_bars(len(days), seeds, close_direction="above")
        for seed in seeds:
            # 訊號次日開盤仍在回檔價，當日價格恢復至 100；真實引擎以
            # next-open 進場並按 target 成交，不能靠 toy runner 宣稱獲利。
            entry = frame.index[seed + 1]
            frame.loc[entry, "Open"] = frame.iloc[seed]["Close"]
            frame.loc[entry, "Low"] = frame.iloc[seed]["Close"] - 0.5
        rows.extend([
            [day.strftime("%Y-%m-%d"), *map(str, row)]
            for day, row in zip(days, frame.to_numpy(), strict=True)
        ])
    return rows
