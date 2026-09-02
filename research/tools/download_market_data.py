"""下載並驗證單一 ticker 的 Yahoo Finance 日線 OHLCV 快照。

這支工具把使用者指定的起訖日視為「含頭含尾」，呼叫 Yahoo 時會自動把
結束日轉成 exclusive end。它只處理單一 ticker、XNYS（或指定的交易所日曆）
與 1d 日線，輸出欄位固定為 Date、Open、High、Low、Close、Volume。

輸出的 CSV 使用內容雜湊命名，避免後續 Study 不小心讀到會被覆寫的
``latest.csv``。下載完成後會另外產生同名的 ``.quality.yml`` 報告。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import exchange_calendars as xcals
import numpy as np
import pandas as pd
import yaml
import yfinance as yf

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPOSITORY_ROOT / "research" / "market-data" / "yahoo"
CSV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
PRICE_COLUMNS = ("Open", "High", "Low", "Close")
OHLC_TOLERANCE = 1e-10


class MarketDataError(RuntimeError):
    """市場資料無法下載、解析或通過完整性檢查。"""


class DataQualityError(MarketDataError):
    """下載到的資料含有不合理的價格、數量或交易日。"""


@dataclass(frozen=True)
class DownloadResult:
    """成功下載並保存一份快照後回傳的摘要。"""

    ticker: str
    start_date: date
    end_date: date
    output_path: Path
    report_path: Path
    digest: str
    quality: dict[str, Any]


def parse_iso_date(value: str, *, option: str) -> date:
    """解析 CLI 的 ISO 日期，並提供較容易理解的錯誤訊息。"""

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise MarketDataError(f"{option} 必須是 YYYY-MM-DD 日期：{value}") from exc


def expected_sessions(calendar_name: str, start_date: date, end_date: date) -> list[str]:
    """回傳指定交易所日曆在含頭含尾區間內的 session 清單。"""

    try:
        calendar = xcals.get_calendar(calendar_name)
    except Exception as exc:  # exchange_calendars 對未知名稱會拋出多種例外型別
        raise MarketDataError(f"找不到交易所日曆：{calendar_name}") from exc
    return [
        timestamp.strftime("%Y-%m-%d")
        for timestamp in calendar.sessions_in_range(
            start_date.isoformat(), end_date.isoformat()
        )
    ]


def _column_candidates(columns: pd.Index, expected: str) -> list[Any]:
    """在 flat 或 yfinance MultiIndex 欄位中找出指定欄位。"""

    candidates: list[Any] = []
    expected_key = expected.casefold()
    for column in columns:
        parts = column if isinstance(column, tuple) else (column,)
        if any(str(part).strip().casefold() == expected_key for part in parts):
            candidates.append(column)
    return candidates


def normalize_download(downloaded: pd.DataFrame) -> pd.DataFrame:
    """把 yfinance 結果整理成固定欄位和無時區的交易日索引。"""

    if not isinstance(downloaded, pd.DataFrame):
        raise MarketDataError("Yahoo 回傳資料不是 DataFrame")
    if downloaded.empty:
        raise MarketDataError("Yahoo 沒有回傳任何資料；請檢查 ticker 和日期區間")

    selected: list[Any] = []
    for column in CSV_COLUMNS:
        candidates = _column_candidates(downloaded.columns, column)
        if len(candidates) != 1:
            found = ", ".join(str(item) for item in candidates) or "無"
            raise MarketDataError(
                f"Yahoo 資料的 {column} 欄位不唯一或不存在；候選欄位：{found}"
            )
        selected.append(candidates[0])

    frame = downloaded.loc[:, selected].copy()
    frame.columns = list(CSV_COLUMNS)
    if isinstance(frame.index, pd.MultiIndex):
        raise MarketDataError("Yahoo 回傳的日期索引是 MultiIndex，無法安全解析")

    parsed_index = pd.to_datetime(frame.index, errors="coerce")
    if not isinstance(parsed_index, pd.DatetimeIndex) or parsed_index.isna().any():
        raise MarketDataError("Yahoo 回傳資料含有無法解析的日期")
    if parsed_index.tz is not None:
        parsed_index = parsed_index.tz_localize(None)
    frame.index = parsed_index.normalize()
    return frame


def _sample_dates(frame: pd.DataFrame, mask: pd.Series, limit: int = 5) -> list[str]:
    """將布林遮罩轉成有限長度的日期樣本，避免錯誤訊息過長。"""

    indexes = frame.index[mask.to_numpy()]
    return [timestamp.strftime("%Y-%m-%d") for timestamp in indexes[:limit]]


def validate_frame(
    frame: pd.DataFrame,
    *,
    calendar_name: str,
    start_date: date,
    end_date: date,
    ohlc_tolerance: float = OHLC_TOLERANCE,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """驗證並回傳可保存的 OHLCV frame 與品質摘要。

    High 或 Low 若只有不超過 ``ohlc_tolerance`` 的浮點 round-off 誤差，會被
    校正到合理邊界並記錄在報告中；超過容許值的資料直接拒絕保存。
    """

    if start_date > end_date:
        raise MarketDataError("start date 不得晚於 end date")
    if ohlc_tolerance < 0 or not np.isfinite(ohlc_tolerance):
        raise MarketDataError("OHLC tolerance 必須是有限且不小於 0 的數字")
    if tuple(frame.columns) != CSV_COLUMNS:
        raise MarketDataError(
            f"資料欄位必須正好是 {', '.join(CSV_COLUMNS)}；實際是 {list(frame.columns)}"
        )
    if frame.index.has_duplicates:
        duplicates = frame.index[frame.index.duplicated()].strftime("%Y-%m-%d").tolist()
        raise DataQualityError(f"交易日重複：{duplicates[:5]}")
    if not frame.index.is_monotonic_increasing:
        raise DataQualityError("交易日未依時間遞增排序")

    expected = expected_sessions(calendar_name, start_date, end_date)
    observed = [timestamp.strftime("%Y-%m-%d") for timestamp in frame.index]
    if observed != expected:
        expected_set = set(expected)
        observed_set = set(observed)
        missing = [session for session in expected if session not in observed_set]
        extra = [session for session in observed if session not in expected_set]
        raise DataQualityError(
            "交易日清單與交易所日曆不一致："
            f"missing={missing[:5]}, extra={extra[:5]}"
        )

    result = frame.copy()
    for column in CSV_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    numeric = result.loc[:, CSV_COLUMNS].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        bad = ~np.isfinite(numeric).all(axis=1)
        raise DataQualityError(f"資料含有 NaN 或無限大數值：{_sample_dates(result, pd.Series(bad))}")

    invalid_price = (result.loc[:, PRICE_COLUMNS] <= 0).any(axis=1)
    if invalid_price.any():
        raise DataQualityError(
            f"Open/High/Low/Close 必須大於 0：{_sample_dates(result, invalid_price)}"
        )
    invalid_volume = result["Volume"] < 0
    if invalid_volume.any():
        raise DataQualityError(f"Volume 不得小於 0：{_sample_dates(result, invalid_volume)}")

    low_above_high = result["Low"] > result["High"]
    if low_above_high.any():
        raise DataQualityError(
            f"Low 高於 High，無法形成有效 K 線：{_sample_dates(result, low_above_high)}"
        )

    high_floor = result.loc[:, ["Open", "Close", "Low"]].max(axis=1)
    low_ceiling = result.loc[:, ["Open", "Close", "High"]].min(axis=1)
    high_violation = result["High"] < high_floor
    low_violation = result["Low"] > low_ceiling
    high_delta = high_floor - result["High"]
    low_delta = result["Low"] - low_ceiling
    if (high_violation & (high_delta > ohlc_tolerance)).any():
        bad = high_violation & (high_delta > ohlc_tolerance)
        raise DataQualityError(
            "High 低於 Open、Close 或 Low，且超過浮點 round-off 容許值："
            f"{_sample_dates(result, bad)}"
        )
    if (low_violation & (low_delta > ohlc_tolerance)).any():
        bad = low_violation & (low_delta > ohlc_tolerance)
        raise DataQualityError(
            "Low 高於 Open、Close 或 High，且超過浮點 round-off 容許值："
            f"{_sample_dates(result, bad)}"
        )

    repair_high = high_violation & (high_delta > 0)
    repair_low = low_violation & (low_delta > 0)
    if repair_high.any():
        result.loc[repair_high, "High"] = high_floor[repair_high]
    if repair_low.any():
        result.loc[repair_low, "Low"] = low_ceiling[repair_low]

    quality = {
        "status": "passed",
        "calendar": calendar_name,
        "expected_sessions": len(expected),
        "observed_sessions": len(observed),
        "first_session": observed[0],
        "last_session": observed[-1],
        "rows": len(result),
        "ohlc_tolerance": format(ohlc_tolerance, ".17g"),
        "repaired_high_rows": int(repair_high.sum()),
        "repaired_low_rows": int(repair_low.sum()),
    }
    return result.astype(float), quality


def download_frame(ticker: str, *, start_date: date, end_date: date) -> pd.DataFrame:
    """從 Yahoo 下載含頭含尾日期區間的單一 ticker 日線資料。"""

    normalized_ticker = ticker.strip()
    if not normalized_ticker:
        raise MarketDataError("ticker 不得是空字串")
    end_exclusive = end_date + timedelta(days=1)
    try:
        downloaded = yf.download(
            normalized_ticker,
            start=start_date.isoformat(),
            end=end_exclusive.isoformat(),
            interval="1d",
            auto_adjust=True,
            actions=False,
            group_by="column",
            ignore_tz=True,
            keepna=True,
            multi_level_index=False,
            progress=False,
            repair=False,
            threads=False,
        )
    except Exception as exc:
        raise MarketDataError(f"Yahoo 下載 {normalized_ticker} 失敗：{exc}") from exc
    return normalize_download(downloaded)


def csv_bytes(frame: pd.DataFrame) -> bytes:
    """將已驗證 frame 序列化成固定 CSV bytes。"""

    result = frame.loc[:, CSV_COLUMNS].copy()
    result.index = pd.to_datetime(result.index).normalize()
    result.index.name = "Date"
    return result.to_csv(index=True, index_label="Date", lineterminator="\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ticker_slug(ticker: str) -> str:
    """把 ticker 轉成不會逃出輸出目錄的檔名片段。"""

    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", ticker.strip().upper()).strip("-.")
    if not slug:
        raise MarketDataError(f"ticker 無法形成安全檔名：{ticker}")
    return slug


def atomic_create(path: Path, data: bytes) -> None:
    """不可覆寫地建立檔案；同內容重跑時視為成功。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError as exc:
            if path.read_bytes() == data:
                return
            raise MarketDataError(f"拒絕覆寫不同內容：{path}") from exc
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary_path.unlink(missing_ok=True)


def report_bytes(report: dict[str, Any]) -> bytes:
    """將下載報告序列化成穩定、可讀的 YAML。"""

    text = yaml.safe_dump(
        report,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=True,
        width=10_000,
    )
    return text.rstrip("\n").encode("utf-8") + b"\n"


def relative_path(path: Path) -> str:
    """優先以 repository-relative path 出現在報告中。"""

    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def download_and_save(
    ticker: str,
    *,
    start_date: date,
    end_date: date,
    output_dir: Path,
    calendar_name: str,
    ohlc_tolerance: float = OHLC_TOLERANCE,
) -> DownloadResult:
    """下載、驗證、保存快照與品質報告。"""

    if start_date > end_date:
        raise MarketDataError("start date 不得晚於 end date")
    frame = download_frame(ticker, start_date=start_date, end_date=end_date)
    frame, quality = validate_frame(
        frame,
        calendar_name=calendar_name,
        start_date=start_date,
        end_date=end_date,
        ohlc_tolerance=ohlc_tolerance,
    )
    data = csv_bytes(frame)
    data_digest = sha256(data)
    name = (
        f"{ticker_slug(ticker)}-{start_date.isoformat()}-{end_date.isoformat()}"
        f"-auto-adjust--sha256-{data_digest}.csv"
    )
    output_path = output_dir.resolve() / name
    atomic_create(output_path, data)

    report = {
        "schema_version": 1,
        "provider": "yahoo",
        "ticker": ticker.strip().upper(),
        "interval": "1d",
        "adjustment_policy": "auto_adjusted",
        "request": {
            "start_inclusive": start_date.isoformat(),
            "end_inclusive": end_date.isoformat(),
            "end_exclusive": (end_date + timedelta(days=1)).isoformat(),
            "calendar": calendar_name,
        },
        "snapshot": {
            "path": relative_path(output_path),
            "digest": data_digest,
            "bytes": len(data),
            "columns": ["Date", *CSV_COLUMNS],
        },
        "quality": quality,
    }
    report_path = output_path.with_suffix(".quality.yml")
    atomic_create(report_path, report_bytes(report))
    return DownloadResult(
        ticker=ticker.strip().upper(),
        start_date=start_date,
        end_date=end_date,
        output_path=output_path,
        report_path=report_path,
        digest=data_digest,
        quality=quality,
    )


def argument_parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="下載並驗證單一 ticker 的 Yahoo auto-adjusted 1d OHLCV 資料"
    )
    result.add_argument("--ticker", required=True, help="Yahoo Finance ticker，例如 TSM")
    result.add_argument("--start", required=True, metavar="YYYY-MM-DD", help="含頭起始日")
    result.add_argument("--end", required=True, metavar="YYYY-MM-DD", help="含尾結束日")
    result.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"輸出目錄（預設：{DEFAULT_OUTPUT_DIR}）",
    )
    result.add_argument(
        "--calendar",
        default="XNYS",
        help="exchange_calendars 日曆名稱（預設：XNYS）",
    )
    result.add_argument(
        "--ohlc-tolerance",
        type=float,
        default=OHLC_TOLERANCE,
        help=f"允許修正的浮點 round-off 上限（預設：{OHLC_TOLERANCE:g}）",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = argument_parser().parse_args(argv)
    try:
        start_date = parse_iso_date(args.start, option="--start")
        end_date = parse_iso_date(args.end, option="--end")
        result = download_and_save(
            args.ticker,
            start_date=start_date,
            end_date=end_date,
            output_dir=args.output_dir,
            calendar_name=args.calendar,
            ohlc_tolerance=args.ohlc_tolerance,
        )
    except MarketDataError as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2

    quality = result.quality
    print(f"下載完成：{result.output_path}")
    print(
        f"資料範圍：{quality['first_session']} ～ {quality['last_session']} "
        f"（{quality['rows']} 個交易日）"
    )
    print(
        "OHLCV 檢查：通過；"
        f"High 修正 {quality['repaired_high_rows']} 筆，"
        f"Low 修正 {quality['repaired_low_rows']} 筆"
    )
    print(f"SHA-256：{result.digest}")
    print(f"品質報告：{result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
