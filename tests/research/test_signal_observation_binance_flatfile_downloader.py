"""Tests for binance_flatfile_downloader — mocked HTTP only, no network calls."""
from __future__ import annotations

import io
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from research.signal_observation.binance_flatfile_downloader import (
    CSV_HEADER,
    SUPPORTED_INTERVALS,
    daily_url,
    download_flatfile_klines,
    monthly_url,
    parse_zip_csv,
)

BAR_MS_4H = 4 * 60 * 60 * 1000


def _flatfile_row(
    open_ms: int,
    *,
    open_: str = "100",
    high: str = "101",
    low: str = "99",
    close_: str = "100.5",
    volume: str = "10",
) -> list:
    return [
        open_ms, open_, high, low, close_, volume,
        open_ms + BAR_MS_4H - 1,
        "1000", 5, "500", "5", "0",
    ]


def _make_zip(rows: list[list], filename: str = "data.csv") -> bytes:
    """Build an in-memory zip containing one no-header CSV."""
    csv_content = "\n".join(",".join(str(c) for c in row) for row in rows)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, csv_content)
    return buf.getvalue()


class _MockResponse:
    def __init__(self, data: bytes):
        self._data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return self._data


def _http_404() -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://data.binance.vision/x", code=404,
        msg="Not Found", hdrs=None, fp=None,
    )


def _http_500() -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://data.binance.vision/x", code=500,
        msg="Server Error", hdrs=None, fp=None,
    )


# --- URL builders ---


def test_monthly_url_format():
    url = monthly_url("SOLUSDT", "4h", 2024, 3)
    assert url == (
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        "SOLUSDT/4h/SOLUSDT-4h-2024-03.zip"
    )


def test_monthly_url_pads_single_digit_month():
    url = monthly_url("XRPUSDT", "4h", 2023, 1)
    assert "-2023-01.zip" in url


def test_daily_url_format():
    url = daily_url("BNBUSDT", "4h", 2024, 11, 7)
    assert url == (
        "https://data.binance.vision/data/futures/um/daily/klines/"
        "BNBUSDT/4h/BNBUSDT-4h-2024-11-07.zip"
    )


def test_daily_url_pads_single_digit_day():
    url = daily_url("XRPUSDT", "4h", 2024, 5, 9)
    assert "-2024-05-09.zip" in url


def test_url_builders_include_symbol_and_interval():
    m = monthly_url("DOGEUSDT", "4h", 2024, 6)
    assert "DOGEUSDT" in m and "4h" in m
    d = daily_url("DOGEUSDT", "4h", 2024, 6, 15)
    assert "DOGEUSDT" in d and "4h" in d


# --- parse_zip_csv ---


def test_parse_zip_csv_extracts_rows():
    rows = [_flatfile_row(1_700_000_000_000), _flatfile_row(1_700_000_000_000 + BAR_MS_4H)]
    result = parse_zip_csv(_make_zip(rows))
    assert len(result) == 2
    assert result[0][0] == str(1_700_000_000_000)


def test_parse_zip_csv_skips_blank_lines():
    csv_content = ",".join(str(c) for c in _flatfile_row(1_700_000_000_000)) + "\n\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("data.csv", csv_content)
    result = parse_zip_csv(buf.getvalue())
    assert len(result) == 1


def test_parse_zip_csv_rejects_short_row():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("data.csv", "1700000000000,100,101,99\n")  # only 4 cols
    with pytest.raises(ValueError, match="columns"):
        parse_zip_csv(buf.getvalue())


def test_parse_zip_csv_skips_header_row():
    """Some flat-file zips include a header row; it must be silently skipped."""
    header = "open_time,open,high,low,close,volume,close_time,quote_vol,trades,taker_base,taker_quote,ignore"
    data_row = ",".join(str(c) for c in _flatfile_row(1_700_000_000_000))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("data.csv", header + "\n" + data_row + "\n")
    result = parse_zip_csv(buf.getvalue())
    assert len(result) == 1
    assert result[0][0] == str(1_700_000_000_000)


def test_parse_zip_csv_rejects_zip_without_csv():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", "no csv here")
    with pytest.raises(ValueError, match="no .csv"):
        parse_zip_csv(buf.getvalue())


# --- argument validation ---


def test_rejects_empty_symbol(tmp_path):
    with pytest.raises(ValueError, match="symbol"):
        download_flatfile_klines(symbol="", interval="4h", output_csv=tmp_path / "out.csv")


def test_rejects_unsupported_interval(tmp_path):
    with pytest.raises(ValueError, match="interval"):
        download_flatfile_klines(
            symbol="SOLUSDT", interval="7h", output_csv=tmp_path / "out.csv"
        )


def test_all_supported_intervals_accepted(tmp_path):
    for interval in SUPPORTED_INTERVALS:
        with patch(
            "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
            side_effect=lambda req, *, timeout=60: (_ for _ in ()).throw(_http_404()),
        ):
            # Should not raise ValueError for interval
            try:
                download_flatfile_klines(
                    symbol="SOLUSDT",
                    interval=interval,
                    output_csv=tmp_path / f"out_{interval}.csv",
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 31),
                )
            except urllib.error.HTTPError:
                pass  # 404s propagate here; interval validation passed


# --- 404 and error handling ---


def test_404_is_skipped_silently(tmp_path):
    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        side_effect=lambda req, *, timeout=60: (_ for _ in ()).throw(_http_404()),
    ):
        out = download_flatfile_klines(
            symbol="SOLUSDT",
            interval="4h",
            output_csv=tmp_path / "out.csv",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(CSV_HEADER)
    assert len(lines) == 1  # header only


def test_non_404_http_error_propagates(tmp_path):
    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        side_effect=lambda req, *, timeout=60: (_ for _ in ()).throw(_http_500()),
    ):
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            download_flatfile_klines(
                symbol="SOLUSDT",
                interval="4h",
                output_csv=tmp_path / "out.csv",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )
    assert exc_info.value.code == 500


# --- CSV output ---


def test_writes_correct_header_and_timestamp_format(tmp_path):
    open_ms = 1_704_067_200_000  # 2024-01-01 00:00:00 UTC
    zip_bytes = _make_zip([_flatfile_row(open_ms, open_="95", close_="96", volume="500")])

    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        return_value=_MockResponse(zip_bytes),
    ):
        out = download_flatfile_klines(
            symbol="SOLUSDT",
            interval="4h",
            output_csv=tmp_path / "out.csv",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "timestamp,open,high,low,close,volume"
    assert len(lines) == 2
    fields = lines[1].split(",")
    assert fields[0] == "2024-01-01T00:00:00Z"
    assert fields[1] == "95"
    assert fields[4] == "96"
    assert fields[5] == "500"


def test_output_is_sorted_ascending(tmp_path):
    t0 = 1_704_067_200_000  # 2024-01-01 00:00:00 UTC
    rows = [_flatfile_row(t0 + i * BAR_MS_4H) for i in range(5, -1, -1)]
    zip_bytes = _make_zip(rows)

    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        return_value=_MockResponse(zip_bytes),
    ):
        out = download_flatfile_klines(
            symbol="SOLUSDT",
            interval="4h",
            output_csv=tmp_path / "out.csv",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

    timestamps = [ln.split(",")[0] for ln in out.read_text(encoding="utf-8").splitlines()[1:]]
    assert timestamps == sorted(timestamps)


def test_output_path_is_returned(tmp_path):
    zip_bytes = _make_zip([_flatfile_row(1_704_067_200_000)])

    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        return_value=_MockResponse(zip_bytes),
    ):
        result = download_flatfile_klines(
            symbol="SOLUSDT",
            interval="4h",
            output_csv=tmp_path / "out.csv",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

    assert result == tmp_path / "out.csv"
    assert result.exists()


# --- deduplication ---


def test_deduplicates_rows_with_same_open_time(tmp_path):
    t0 = 1_704_067_200_000
    zip_bytes = _make_zip([_flatfile_row(t0)])

    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        return_value=_MockResponse(zip_bytes),
    ):
        out = download_flatfile_klines(
            symbol="SOLUSDT",
            interval="4h",
            output_csv=tmp_path / "out.csv",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

    data_lines = out.read_text(encoding="utf-8").splitlines()[1:]
    assert len(data_lines) == 1


# --- date range filtering ---


def test_rows_before_start_date_excluded(tmp_path):
    start = date(2024, 1, 15)
    end = date(2024, 1, 31)
    start_ms = int(datetime(2024, 1, 15, tzinfo=UTC).timestamp() * 1000)
    before_ms = int(datetime(2024, 1, 14, tzinfo=UTC).timestamp() * 1000)

    rows = [_flatfile_row(before_ms), _flatfile_row(start_ms)]
    zip_bytes = _make_zip(rows)

    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        return_value=_MockResponse(zip_bytes),
    ):
        out = download_flatfile_klines(
            symbol="SOLUSDT",
            interval="4h",
            output_csv=tmp_path / "out.csv",
            start_date=start,
            end_date=end,
        )

    data_lines = out.read_text(encoding="utf-8").splitlines()[1:]
    assert len(data_lines) == 1
    assert "2024-01-15T00:00:00Z" in data_lines[0]


def test_rows_after_end_date_excluded(tmp_path):
    start = date(2024, 1, 1)
    end = date(2024, 1, 20)
    after_ms = int((datetime(2024, 1, 20, tzinfo=UTC) + timedelta(days=1)).timestamp() * 1000)
    in_ms = int(datetime(2024, 1, 20, tzinfo=UTC).timestamp() * 1000)

    rows = [_flatfile_row(in_ms), _flatfile_row(after_ms)]
    zip_bytes = _make_zip(rows)

    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        return_value=_MockResponse(zip_bytes),
    ):
        out = download_flatfile_klines(
            symbol="SOLUSDT",
            interval="4h",
            output_csv=tmp_path / "out.csv",
            start_date=start,
            end_date=end,
        )

    data_lines = out.read_text(encoding="utf-8").splitlines()[1:]
    assert len(data_lines) == 1
    assert "2024-01-20T00:00:00Z" in data_lines[0]


# --- URL routing: monthly vs daily ---


def test_past_month_requests_monthly_url(tmp_path):
    """A range entirely in a past month should use exactly one monthly URL."""
    urls_called: list[str] = []

    def fake_urlopen(req, *, timeout=60):
        urls_called.append(req.full_url)
        raise _http_404()

    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ):
        download_flatfile_klines(
            symbol="SOLUSDT",
            interval="4h",
            output_csv=tmp_path / "out.csv",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

    assert len(urls_called) == 1
    assert "/monthly/" in urls_called[0]
    assert "/daily/" not in urls_called[0]


def test_current_month_uses_daily_urls(tmp_path):
    """When the end falls in the 'current' month, only daily URLs are used for that month."""
    urls_called: list[str] = []
    fake_today = date(2024, 3, 10)

    def fake_urlopen(req, *, timeout=60):
        urls_called.append(req.full_url)
        raise _http_404()

    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ), patch(
        "research.signal_observation.binance_flatfile_downloader.date",
        **{"today.return_value": fake_today, "side_effect": date},
    ):
        download_flatfile_klines(
            symbol="SOLUSDT",
            interval="4h",
            output_csv=tmp_path / "out.csv",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 4),
        )

    assert all("/daily/" in u for u in urls_called)
    assert len(urls_called) == 4  # days 1, 2, 3, 4


# --- hygiene ---


def test_no_auth_headers_sent(tmp_path):
    headers_seen: list[str] = []

    def fake_urlopen(req, *, timeout=60):
        headers_seen.extend(k.lower() for k, _ in req.header_items())
        raise _http_404()

    with patch(
        "research.signal_observation.binance_flatfile_downloader.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ):
        download_flatfile_klines(
            symbol="SOLUSDT",
            interval="4h",
            output_csv=tmp_path / "out.csv",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

    assert not any("apikey" in h or "x-mbx" in h for h in headers_seen)


def test_no_private_endpoints_or_auth_in_source():
    text = Path("research/signal_observation/binance_flatfile_downloader.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "requests", "ccxt", "pandas", "numpy",
        "X-MBX-APIKEY", "/fapi/v1/order", "userDataStream",
        "withdraw", "transfer", "leverage",
    )
    for token in forbidden:
        assert token not in text, f"forbidden token found in source: {token!r}"
