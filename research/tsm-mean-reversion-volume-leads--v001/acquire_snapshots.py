"""取得 TSM 固定 Yahoo auto-adjusted 日線快照並切成 workflow 資料角色。

這支程式只做資料取得、XNYS session 完整性檢查與 SHA-256 命名；不計算訊號、交易
或任何策略績效。正式 runner 必須使用這些已保存檔案，不能在執行時重新連線 provider。
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path

import exchange_calendars as xcals
import pandas as pd
import yfinance as yf

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import atomic_create, canonical_bytes  # noqa: E402

SYMBOL = "TSM"
START_DATE = "2013-01-01"
END_EXCLUSIVE = "2026-01-01"
ROLES = (
    ("warmup-only", "2013-01-01", "2013-12-31"),
    ("development", "2014-01-01", "2018-12-31"),
    ("quarantine", "2019-01-01", "2019-12-31"),
    ("historical-evaluation", "2020-01-01", "2024-12-31"),
    ("retrospective-execution-replay", "2025-01-01", "2025-12-31"),
)
CSV_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="取得 TSM 固定日線資料角色")
    result.add_argument(
        "--output-root",
        type=Path,
        default=Path("research/tsm-mean-reversion-volume-leads--v001"),
    )
    return result


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_sessions(start: str, end: str) -> list[str]:
    calendar = xcals.get_calendar("XNYS")
    return [
        timestamp.strftime("%Y-%m-%d")
        for timestamp in calendar.sessions_in_range(start, end)
    ]


def csv_bytes(frame: pd.DataFrame) -> bytes:
    result = frame.loc[:, ["Open", "High", "Low", "Close", "Volume"]].copy()
    result.index = pd.to_datetime(result.index).normalize()
    result.index.name = "Date"
    return result.to_csv(index=True, index_label="Date", lineterminator="\n").encode("utf-8")


def main() -> int:
    args = parser().parse_args()
    output_root = args.output_root.resolve()
    snapshot_root = output_root / "data" / "snapshots"
    snapshot_root.mkdir(parents=True, exist_ok=True)

    downloaded = yf.download(
        SYMBOL,
        start=START_DATE,
        end=END_EXCLUSIVE,
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
    if not isinstance(downloaded, pd.DataFrame):
        raise RuntimeError("Yahoo 回傳資料不是 DataFrame")
    missing_columns = sorted(set(CSV_COLUMNS[1:]) - set(downloaded.columns))
    if missing_columns:
        raise RuntimeError(f"Yahoo 資料缺少欄位: {', '.join(missing_columns)}")
    frame = downloaded.loc[:, CSV_COLUMNS[1:]].copy()
    frame.index = pd.to_datetime(frame.index).normalize()
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise RuntimeError("Yahoo session 日期重複或未排序")
    frame = frame.astype(float)
    if frame.isna().any().any() or not frame.map(lambda value: pd.notna(value)).all().all():
        raise RuntimeError("Yahoo TSM 快照包含缺值")
    high_floor = frame[["Open", "Close", "Low"]].max(axis=1)
    low_ceiling = frame[["Open", "Close", "High"]].min(axis=1)
    if (frame["High"] + 1e-10 < high_floor).any() or (
        frame["Low"] - 1e-10 > low_ceiling
    ).any():
        raise RuntimeError("Yahoo TSM OHLC 關係超出浮點 round-off 可修正範圍")
    frame["High"] = frame["High"].where(frame["High"] >= high_floor, high_floor)
    frame["Low"] = frame["Low"].where(frame["Low"] <= low_ceiling, low_ceiling)

    full_expected = expected_sessions(START_DATE, "2025-12-31")
    observed = [timestamp.strftime("%Y-%m-%d") for timestamp in frame.index]
    if observed != full_expected:
        missing = sorted(set(full_expected) - set(observed))
        extra = sorted(set(observed) - set(full_expected))
        raise RuntimeError(f"XNYS session 不完整：missing={missing[:5]}, extra={extra[:5]}")

    full_data = csv_bytes(frame)
    full_digest = digest(full_data)
    full_name = f"TSM-2013-2025-auto-adjust--sha256-{full_digest}.csv"
    full_path = snapshot_root / full_name
    atomic_create(full_path, full_data)

    snapshot_records: list[dict[str, object]] = []
    role_records: dict[str, dict[str, object]] = {}
    for role, start_date, end_date in ROLES:
        subset = frame.loc[start_date:end_date]
        sessions = expected_sessions(start_date, end_date)
        subset_sessions = [timestamp.strftime("%Y-%m-%d") for timestamp in subset.index]
        if subset_sessions != sessions:
            raise RuntimeError(f"{role} session inventory 與 XNYS 不一致")
        data = csv_bytes(subset)
        data_digest = digest(data)
        path_name = f"TSM-{role}--sha256-{data_digest}.csv"
        path = snapshot_root / path_name
        atomic_create(path, data)
        role_records[role] = {
            "bytes": len(data),
            "digest": data_digest,
            "end_date": end_date,
            "path": f"data/snapshots/{path_name}",
            "rows": len(subset),
            "start_date": start_date,
        }
        snapshot_records.append(
            {
                "schema_version": 1,
                "role": role,
                "provider": "yahoo",
                "symbols": [SYMBOL],
                "timezone": "America/New_York",
                "calendar": "XNYS",
                "interval": "1d",
                "adjustment_policy": "auto_adjusted",
                "fields": ["open", "high", "low", "close", "volume"],
                "sessions": sessions,
                "data_digest": data_digest,
            }
        )

    acquisition = {
        "schema_version": 1,
        "acquired_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "calendar_validation": {
            "expected_sessions": len(full_expected),
            "extra_sessions": 0,
            "missing_sessions": 0,
            "null_rows": 0,
            "observed_sessions": len(observed),
        },
        "dependencies": {
            "curl_cffi": __import__("curl_cffi").__version__,
            "exchange_calendars": xcals.__version__,
            "pandas": pd.__version__,
            "yfinance": yf.__version__,
        },
        "full_snapshot": {
            "bytes": len(full_data),
            "digest": full_digest,
            "first_session": observed[0],
            "last_session": observed[-1],
            "path": f"data/snapshots/{full_name}",
            "rows": len(frame),
        },
        "request": {
            "actions": False,
            "auto_adjust": True,
            "end_exclusive": END_EXCLUSIVE,
            "ignore_tz": True,
            "interval": "1d",
            "keepna": True,
            "multi_level_index": False,
            "repair": False,
            "start_inclusive": START_DATE,
            "symbol": SYMBOL,
            "threads": False,
        },
        "normalization": {
            "ohlc_rounding_repair": "只將 1e-10 內的浮點 round-off 校正至 O/C 邊界，超過者拒絕",
        },
        "roles": role_records,
        "storage_policy": {
            "filenames_include_sha256": True,
            "files_read_only": True,
            "formal_run_provider_access": "prohibited",
            "repository_root_relative_prefix": "research/tsm-mean-reversion-volume-leads--v001",
        },
    }
    atomic_create(output_root / "data-snapshot-acquisition.yml", canonical_bytes(acquisition))
    atomic_create(
        output_root / "data-snapshot-set.yml",
        canonical_bytes({"schema_version": 1, "snapshots": snapshot_records}),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
