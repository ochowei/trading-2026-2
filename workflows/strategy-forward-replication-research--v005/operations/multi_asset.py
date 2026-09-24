"""Development 多資產資料的固定檢查與隔離執行清單。"""

from __future__ import annotations

import csv
import io
import math
from datetime import date
from pathlib import Path

import exchange_calendars as xcals
from validator.canonical_yaml import canonical_digest
from validator.errors import IntegrityError, ValidationError
from validator.paths import resolve_inside

MAX_ASSETS = 16
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_ROWS = 10000
FORBIDDEN = {
    ".super-admin",
    ".project-manager",
    "historical-evaluation-artifacts",
    "studies",
    "quarantine",
    "evaluation",
}
COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]


def snapshot_identity(asset: dict) -> dict:
    """去除本機路徑後，用來凍結一份資料來源的跨階段身分。"""
    return {key: value for key, value in asset.items() if key not in {"data_path", "interval_role"}}


def validate_assets(
    repository: Path, assets: list[dict], intervals: list[dict], *, stage: str = "development"
) -> list[tuple[dict, bytes]]:
    """在複製到 runner 前逐檔核對路徑、雜湊、日期與同日對齊。"""
    if not 1 <= len(assets) <= MAX_ASSETS:
        raise ValidationError(f"Development 資產數須為 1 至 {MAX_ASSETS}")
    ids = [asset["asset_id"] for asset in assets]
    if len(ids) != len(set(ids)) or ids != sorted(ids):
        raise ValidationError("資產 ID 必須唯一並以 ID 排序")
    if sum(asset["use"] == "trade" for asset in assets) != 1:
        raise ValidationError("恰須一個交易標的，其餘資產僅供參考")
    roles = {"warmup-only", "development"} if stage == "development" else {"historical-evaluation"}
    allowed = [part for part in intervals if part["role"] in roles]
    calendar = xcals.get_calendar("XNYS")
    result = []
    primary_dates = None
    total = 0
    for asset in assets:
        expected_role = "warmup-development" if stage == "development" else "historical-evaluation"
        if asset["interval_role"] != expected_role:
            raise ValidationError("資產資料角色與執行階段不一致")
        relative = Path(asset["data_path"])
        if relative.is_absolute() or FORBIDDEN.intersection(relative.parts):
            raise ValidationError("Development 資產路徑含受限目錄")
        path = resolve_inside(repository, asset["data_path"])
        if FORBIDDEN.intersection(path.relative_to(repository.resolve()).parts):
            raise ValidationError("Development 資產路徑解析到受限目錄")
        if not path.is_file():
            raise ValidationError("Development 資產檔案不存在")
        if path.suffix.lower() != ".csv":
            raise ValidationError("Development 資產必須為 CSV")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValidationError("Development 單一資產超過 32 MiB")
        data = path.read_bytes()
        total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise ValidationError("Development 資產總量超過 128 MiB")
        if canonical_digest(data) != asset["data_digest"]:
            raise IntegrityError("Development 資產 digest 漂移")
        try:
            reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
            if reader.fieldnames != COLUMNS:
                raise ValidationError("Development CSV 必須是 Date/Open/High/Low/Close/Volume 六欄")
            dates = []
            for row in reader:
                if len(dates) >= MAX_ROWS:
                    raise ValidationError("Development 單一資產超過 10000 列")
                if None in row or any(row[name] in (None, "") for name in COLUMNS):
                    raise ValidationError("Development CSV 有缺漏欄位")
                day = date.fromisoformat(row["Date"])
                if day.isoformat() != row["Date"] or not calendar.is_session(row["Date"]):
                    raise ValidationError("Development CSV 日期非 XNYS 交易日")
                if not any(part["start_date"] <= row["Date"] <= part["end_date"] for part in allowed):
                    raise ValidationError("Development CSV 含 quarantine／Evaluation 日期")
                for name in COLUMNS[1:]:
                    number = float(row[name])
                    if not math.isfinite(number) or (name != "Volume" and number <= 0) or number < 0:
                        raise ValidationError("Development CSV 含無效價格或成交量")
                dates.append(row["Date"])
        except (UnicodeDecodeError, ValueError, csv.Error) as exc:
            raise ValidationError("Development CSV 格式或日期無效") from exc
        if not dates or dates != sorted(set(dates)):
            raise ValidationError("Development CSV 日期必須非空、唯一且遞增")
        if dates[0] != asset["start_date"] or dates[-1] != asset["end_date"]:
            raise IntegrityError("Development 資產日期界線與檔案不一致")
        expected = [
            stamp.strftime("%Y-%m-%d")
            for stamp in calendar.sessions_in_range(dates[0], dates[-1])
        ]
        if dates != expected:
            raise ValidationError("Development 資產交易日缺漏；不得前填或補值")
        if primary_dates is None:
            primary_dates = dates
        elif dates != primary_dates:
            raise ValidationError("多資產交易日未完全對齊；不得補值或前填")
        result.append((asset, data))
    return result


def request_assets(assets: list[dict]) -> list[dict]:
    """request 不暴露 repository 原路徑，只交付隔離空間中的固定檔名。"""
    return [dict(asset, data_path=f"run/assets/{asset['asset_id']}.csv") for asset in assets]
