import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

# 研究工具是以 repository script 形式執行，不是安裝到 src package 的 runtime。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.tools.download_market_data import (
    DataQualityError,
    download_and_save,
    expected_sessions,
    validate_frame,
)


def bars(*, high: float = 105.0, low: float = 95.0) -> pd.DataFrame:
    sessions = expected_sessions("XNYS", date(2024, 1, 2), date(2024, 1, 5))
    return pd.DataFrame(
        {
            "Open": [100.0] * len(sessions),
            "High": [high] * len(sessions),
            "Low": [low] * len(sessions),
            "Close": [102.0] * len(sessions),
            "Volume": [1_000_000.0] * len(sessions),
        },
        index=pd.to_datetime(sessions),
    )


def test_validate_frame_accepts_valid_ohlcv() -> None:
    frame, quality = validate_frame(
        bars(),
        calendar_name="XNYS",
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 5),
    )

    assert len(frame) == 4
    assert quality["status"] == "passed"
    assert quality["repaired_high_rows"] == 0
    assert quality["repaired_low_rows"] == 0


def test_validate_frame_rejects_close_above_high() -> None:
    with pytest.raises(DataQualityError, match="High 低於 Open、Close 或 Low"):
        validate_frame(
            bars(high=101.0),
            calendar_name="XNYS",
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 5),
        )


def test_validate_frame_repairs_only_tiny_high_roundoff() -> None:
    frame, quality = validate_frame(
        bars(high=101.99999999995),
        calendar_name="XNYS",
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 5),
    )

    assert quality["repaired_high_rows"] == 4
    assert (frame["High"] == 102.0).all()


def test_validate_frame_rejects_low_above_high() -> None:
    with pytest.raises(DataQualityError, match="Low 高於 High"):
        validate_frame(
            bars(high=100.0, low=100.00000000001),
            calendar_name="XNYS",
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 5),
        )


def test_download_and_save_uses_content_addressed_name(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "research.tools.download_market_data.download_frame",
        lambda ticker, *, start_date, end_date: bars(),
    )

    result = download_and_save(
        "TSM",
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 5),
        output_dir=tmp_path,
        calendar_name="XNYS",
    )

    assert result.output_path.exists()
    assert result.report_path.exists()
    assert "TSM-2024-01-02-2024-01-05-auto-adjust--sha256-" in result.output_path.name
    assert result.output_path.read_bytes()
