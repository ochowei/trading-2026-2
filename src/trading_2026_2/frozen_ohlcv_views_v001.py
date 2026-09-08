"""以日期先篩選 immutable OHLCV，非指定區間只核對 bytes 與日期。"""

from __future__ import annotations

import hashlib
from datetime import date
from io import BytesIO
from pathlib import Path

import pandas as pd

HEADER = b"Date,Open,High,Low,Close,Volume\n"


def view_bytes(path: Path, start: str, end: str) -> bytes:
    """保留原始列的序列化；只將指定日期範圍的價格送進解析器。"""

    start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
    if start_date > end_date:
        raise ValueError("view 起日不得晚於迄日")
    selected: list[bytes] = []
    previous: date | None = None
    with path.open("rb") as stream:
        if stream.readline() != HEADER:
            raise ValueError("OHLCV 必須採固定 UTF-8、LF 與欄位順序")
        for line in stream:
            raw_date = line.split(b",", 1)[0].decode("ascii")
            session = date.fromisoformat(raw_date)
            if session.isoformat() != raw_date or (previous is not None and session <= previous):
                raise ValueError("session 日期必須固定格式、嚴格遞增且不重複")
            previous = session
            if start_date <= session <= end_date:
                selected.append(line)
    if not selected:
        raise ValueError("指定日期 view 沒有資料")
    return HEADER + b"".join(selected)


def view_digest(path: Path, start: str, end: str) -> str:
    return hashlib.sha256(view_bytes(path, start, end)).hexdigest()


def read_view(path: Path, start: str, end: str) -> pd.DataFrame:
    return pd.read_csv(
        BytesIO(view_bytes(path, start, end)), parse_dates=["Date"], index_col="Date"
    )


def read_development_view(path: Path, start: str, end: str) -> pd.DataFrame:
    allowed = {("2013-01-01", "2013-12-31"), ("2014-01-01", "2018-12-31")}
    if (start, end) not in allowed:
        raise ValueError("Development 只允許 2013 暖機或 2014–2018 開發 view")
    return read_view(path, start, end)
