"""Tests for aggtrades_downloader — mocked HTTP only, no network calls."""
from __future__ import annotations

import io
import urllib.error
import zipfile
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from research.signal_observation.aggtrades_downloader import (
    HOURLY_HEADER,
    US_THRESHOLD,
    HourBin,
    aggregate_to_hourly,
    daily_url,
    detect_ts_unit,
    download_aggtrades_hourly,
    monthly_url,
    parse_aggtrades_zip,
)

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

# A timestamp well inside the ms range (2020-09-13 ~12:26 UTC)
_MS_TS = 1_600_000_000_000
# Same instant in µs
_US_TS = 1_600_000_000_000_000

# Hour-aligned ms timestamps for aggregation tests (epoch + N hours)
_HOUR1_MS = 3_600_000       # 1970-01-01 01:00:00 UTC
_HOUR2_MS = 7_200_000       # 1970-01-01 02:00:00 UTC
# Ticks inside hour 1 (arbitrary offsets)
_H1_T1 = _HOUR1_MS + 100
_H1_T2 = _HOUR1_MS + 200
_H1_T3 = _HOUR1_MS + 300
# Tick inside hour 2
_H2_T1 = _HOUR2_MS + 100


def _make_csv(*rows: list) -> str:
    """Build a CSV string from lists of values (no header)."""
    return "\n".join(",".join(str(v) for v in row) for row in rows)


def _make_aggtrade_row(
    ts: int,
    price: str = "100.00",
    qty: str = "1.0",
    is_buyer_maker: str = "False",
    agg_id: int = 1,
) -> list:
    """Build one aggTrades CSV row (7 columns, UM futures schema)."""
    return [agg_id, price, qty, agg_id * 10, agg_id * 10 + 1, ts, is_buyer_maker]


def _make_zip(csv_content: str, filename: str = "BTCUSDT-aggTrades-2020-01.csv") -> bytes:
    """Wrap a CSV string in an in-memory zip."""
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
        url="https://data.binance.vision/x",
        code=404, msg="Not Found", hdrs=None, fp=None,
    )


def _http_500() -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://data.binance.vision/x",
        code=500, msg="Internal Server Error", hdrs=None, fp=None,
    )


# ---------------------------------------------------------------------------
# URL builder tests
# ---------------------------------------------------------------------------

class TestMonthlyUrl:
    def test_format_includes_symbol_year_month(self):
        url = monthly_url("BTCUSDT", 2022, 3)
        assert "BTCUSDT" in url
        assert "2022" in url
        assert "03" in url

    def test_month_is_zero_padded(self):
        url = monthly_url("BTCUSDT", 2023, 5)
        assert "-2023-05.zip" in url

    def test_path_includes_aggtrades_segment(self):
        url = monthly_url("BTCUSDT", 2023, 1)
        assert "/aggTrades/" in url

    def test_base_domain_is_data_binance_vision(self):
        url = monthly_url("BTCUSDT", 2023, 1)
        assert url.startswith("https://data.binance.vision/")

    def test_futures_um_in_path(self):
        url = monthly_url("ETHUSDT", 2023, 1)
        assert "/futures/um/" in url

    def test_full_url_format(self):
        url = monthly_url("BTCUSDT", 2024, 11)
        assert url == (
            "https://data.binance.vision/data/futures/um/monthly/aggTrades/"
            "BTCUSDT/BTCUSDT-aggTrades-2024-11.zip"
        )


class TestDailyUrl:
    def test_format_includes_symbol_year_month_day(self):
        url = daily_url("ETHUSDT", 2024, 3, 15)
        assert "ETHUSDT" in url
        assert "2024" in url
        assert "03" in url
        assert "15" in url

    def test_month_and_day_are_zero_padded(self):
        url = daily_url("BTCUSDT", 2024, 5, 9)
        assert "-2024-05-09.zip" in url

    def test_path_includes_aggtrades_segment(self):
        url = daily_url("BTCUSDT", 2024, 1, 1)
        assert "/aggTrades/" in url

    def test_full_url_format(self):
        url = daily_url("BTCUSDT", 2024, 6, 7)
        assert url == (
            "https://data.binance.vision/data/futures/um/daily/aggTrades/"
            "BTCUSDT/BTCUSDT-aggTrades-2024-06-07.zip"
        )


# ---------------------------------------------------------------------------
# Timestamp unit detection tests
# ---------------------------------------------------------------------------

class TestDetectTsUnit:
    def test_small_timestamp_is_ms(self):
        assert detect_ts_unit(_MS_TS) == "ms"

    def test_large_timestamp_is_us(self):
        assert detect_ts_unit(_US_TS) == "us"

    def test_threshold_itself_is_us(self):
        assert detect_ts_unit(US_THRESHOLD) == "us"

    def test_one_below_threshold_is_ms(self):
        assert detect_ts_unit(US_THRESHOLD - 1) == "ms"

    def test_typical_2020_ms_timestamp(self):
        # 2020-01-01 00:00:00 UTC in ms
        ts_2020_ms = 1_577_836_800_000
        assert detect_ts_unit(ts_2020_ms) == "ms"

    def test_typical_2025_us_timestamp(self):
        # 2025-01-01 00:00:00 UTC in µs
        ts_2025_us = 1_735_689_600_000_000
        assert detect_ts_unit(ts_2025_us) == "us"


# ---------------------------------------------------------------------------
# parse_aggtrades_zip tests
# ---------------------------------------------------------------------------

class TestParseAggtrades:
    def _zip_with_rows(self, *rows: list) -> bytes:
        return _make_zip(_make_csv(*rows))

    def test_parses_7col_row_and_returns_correct_fields(self):
        row = _make_aggtrade_row(_HOUR1_MS + 50, price="50000.00", qty="0.5")
        unit, rows = parse_aggtrades_zip(self._zip_with_rows(row))
        assert len(rows) == 1
        ts, price, qty, is_buyer_maker = rows[0]
        assert ts == _HOUR1_MS + 50
        assert price == Decimal("50000.00")
        assert qty == Decimal("0.5")
        assert is_buyer_maker is False

    def test_parses_multiple_rows(self):
        r1 = _make_aggtrade_row(_H1_T1, agg_id=1)
        r2 = _make_aggtrade_row(_H1_T2, agg_id=2)
        _, rows = parse_aggtrades_zip(self._zip_with_rows(r1, r2))
        assert len(rows) == 2

    def test_skips_header_row(self):
        header = "agg_trade_id,price,qty,first_trade_id,last_trade_id,transact_time,is_buyer_maker"
        data_row = _make_csv(_make_aggtrade_row(_H1_T1))
        zip_bytes = _make_zip(header + "\n" + data_row)
        _, rows = parse_aggtrades_zip(zip_bytes)
        assert len(rows) == 1

    def test_skips_blank_lines(self):
        row = _make_aggtrade_row(_H1_T1)
        zip_bytes = _make_zip(_make_csv(row) + "\n\n")
        _, rows = parse_aggtrades_zip(zip_bytes)
        assert len(rows) == 1

    def test_detects_ms_unit_from_first_row(self):
        row = _make_aggtrade_row(_MS_TS)
        unit, _ = parse_aggtrades_zip(self._zip_with_rows(row))
        assert unit == "ms"

    def test_detects_us_unit_from_first_row(self):
        row = _make_aggtrade_row(_US_TS)
        unit, _ = parse_aggtrades_zip(self._zip_with_rows(row))
        assert unit == "us"

    def test_parses_8col_row_ignoring_extra_column(self):
        # Spot-style rows include isBestMatch as column 7; UM futures omit it.
        # The parser must handle 8-col rows without error.
        row = _make_aggtrade_row(_H1_T1) + ["True"]  # 8 cols
        _, rows = parse_aggtrades_zip(self._zip_with_rows(row))
        assert len(rows) == 1

    def test_raises_on_zip_without_csv(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("readme.txt", "no csv here")
        with pytest.raises(ValueError, match="no .csv"):
            parse_aggtrades_zip(buf.getvalue())

    def test_raises_on_row_with_too_few_columns(self):
        short_row = "1,100.0,1.0"  # only 3 columns
        zip_bytes = _make_zip(short_row)
        with pytest.raises(ValueError, match="columns"):
            parse_aggtrades_zip(zip_bytes)

    def test_is_buyer_maker_true_parsed_correctly(self):
        row = _make_aggtrade_row(_H1_T1, is_buyer_maker="True")
        _, rows = parse_aggtrades_zip(self._zip_with_rows(row))
        assert rows[0][3] is True

    def test_is_buyer_maker_false_parsed_correctly(self):
        row = _make_aggtrade_row(_H1_T1, is_buyer_maker="False")
        _, rows = parse_aggtrades_zip(self._zip_with_rows(row))
        assert rows[0][3] is False


# ---------------------------------------------------------------------------
# aggregate_to_hourly tests
# ---------------------------------------------------------------------------

class TestAggregateToHourly:
    """
    All hand-verified expectations.

    _HOUR1_MS = 3_600_000  → UTC hour 01:00:00 on 1970-01-01
    _H1_T1 = 3_600_100, _H1_T2 = 3_600_200, _H1_T3 = 3_600_300
    _H2_T1 = 7_200_100  → falls in hour 02:00:00
    """

    def _rows(self, *items: tuple) -> list[tuple[int, Decimal, Decimal, bool]]:
        return [(ts, Decimal(str(p)), Decimal(str(q)), ibm) for ts, p, q, ibm in items]

    def test_single_tick_sets_all_four_prices_equal(self):
        rows = self._rows((_H1_T1, 100, 1, False))
        bins = aggregate_to_hourly(rows, unit="ms")
        b = bins[_HOUR1_MS]
        assert b.open == b.high == b.low == b.close == Decimal("100")

    def test_open_is_first_price_in_hour(self):
        # Prices: 100, 110, 105 — open must be 100
        rows = self._rows(
            (_H1_T1, 100, 1, False),
            (_H1_T2, 110, 1, False),
            (_H1_T3, 105, 1, False),
        )
        bins = aggregate_to_hourly(rows, unit="ms")
        assert bins[_HOUR1_MS].open == Decimal("100")

    def test_close_is_last_price_in_hour(self):
        # Prices in order: 100, 110, 105 — close must be 105
        rows = self._rows(
            (_H1_T1, 100, 1, False),
            (_H1_T2, 110, 1, False),
            (_H1_T3, 105, 1, False),
        )
        bins = aggregate_to_hourly(rows, unit="ms")
        assert bins[_HOUR1_MS].close == Decimal("105")

    def test_high_is_max_price_in_hour(self):
        rows = self._rows(
            (_H1_T1, 100, 1, False),
            (_H1_T2, 110, 1, False),
            (_H1_T3, 105, 1, False),
        )
        bins = aggregate_to_hourly(rows, unit="ms")
        assert bins[_HOUR1_MS].high == Decimal("110")

    def test_low_is_min_price_in_hour(self):
        rows = self._rows(
            (_H1_T1, 100, 1, False),
            (_H1_T2, 110, 1, False),
            (_H1_T3,  95, 1, False),
        )
        bins = aggregate_to_hourly(rows, unit="ms")
        assert bins[_HOUR1_MS].low == Decimal("95")

    def test_taker_buy_vol_sums_qty_where_not_is_buyer_maker(self):
        # isBuyerMaker=False → taker-buy; qty = 10, 30; total = 40
        rows = self._rows(
            (_H1_T1, 100, 10, False),  # taker buy
            (_H1_T2, 100, 20, True),   # taker sell
            (_H1_T3, 100, 30, False),  # taker buy
        )
        bins = aggregate_to_hourly(rows, unit="ms")
        assert bins[_HOUR1_MS].taker_buy_vol == Decimal("40")

    def test_taker_sell_vol_sums_qty_where_is_buyer_maker(self):
        # isBuyerMaker=True → taker-sell; only qty=20
        rows = self._rows(
            (_H1_T1, 100, 10, False),
            (_H1_T2, 100, 20, True),
            (_H1_T3, 100, 30, False),
        )
        bins = aggregate_to_hourly(rows, unit="ms")
        assert bins[_HOUR1_MS].taker_sell_vol == Decimal("20")

    def test_ticks_in_different_hours_go_to_separate_bins(self):
        rows = self._rows(
            (_H1_T1, 100, 1, False),
            (_H2_T1, 200, 1, False),
        )
        bins = aggregate_to_hourly(rows, unit="ms")
        assert len(bins) == 2
        assert _HOUR1_MS in bins
        assert _HOUR2_MS in bins

    def test_each_bin_has_independent_open_close(self):
        rows = self._rows(
            (_H1_T1, 100, 1, False),  # hour 1: open=100
            (_H1_T2, 105, 1, False),  # hour 1: close=105
            (_H2_T1, 200, 1, False),  # hour 2: open=close=200
        )
        bins = aggregate_to_hourly(rows, unit="ms")
        assert bins[_HOUR1_MS].open == Decimal("100")
        assert bins[_HOUR1_MS].close == Decimal("105")
        assert bins[_HOUR2_MS].open == Decimal("200")

    def test_microsecond_timestamps_map_to_correct_hour(self):
        # _US_TS = 1_600_000_000_000_000 µs = 1_600_000_000_000 ms
        hour_ms = (_US_TS // 1000 // 3_600_000) * 3_600_000
        rows = self._rows((_US_TS, 50000, 1, False))
        bins = aggregate_to_hourly(rows, unit="us")
        assert hour_ms in bins

    def test_empty_rows_returns_empty_dict(self):
        assert aggregate_to_hourly([], unit="ms") == {}


# ---------------------------------------------------------------------------
# download_aggtrades_hourly integration tests
# ---------------------------------------------------------------------------

_PATCH = "research.signal_observation.aggtrades_downloader.urllib.request.urlopen"


def _single_row_zip(ts: int = _H1_T1) -> bytes:
    row = _make_aggtrade_row(ts, price="50000.00", qty="0.1", is_buyer_maker="False")
    return _make_zip(_make_csv(row))


class TestDownloadAggtrades:
    def test_404_skipped_and_empty_csv_written(self, tmp_path):
        with patch(_PATCH, side_effect=lambda req, *, timeout=60: (_ for _ in ()).throw(_http_404())):
            out = download_aggtrades_hourly(
                symbol="BTCUSDT",
                output_dir=tmp_path,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )
        lines = out.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(HOURLY_HEADER)
        assert len(lines) == 1  # header only

    def test_500_error_propagates(self, tmp_path):
        with patch(_PATCH, side_effect=lambda req, *, timeout=60: (_ for _ in ()).throw(_http_500())):
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                download_aggtrades_hourly(
                    symbol="BTCUSDT",
                    output_dir=tmp_path,
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 31),
                )
        assert exc_info.value.code == 500

    def test_output_csv_header_matches_hourly_header(self, tmp_path):
        with patch(_PATCH, return_value=_MockResponse(_single_row_zip())):
            out = download_aggtrades_hourly(
                symbol="BTCUSDT",
                output_dir=tmp_path,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )
        first_line = out.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == ",".join(HOURLY_HEADER)

    def test_output_path_returned_and_exists(self, tmp_path):
        with patch(_PATCH, return_value=_MockResponse(_single_row_zip())):
            out = download_aggtrades_hourly(
                symbol="BTCUSDT",
                output_dir=tmp_path,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )
        assert out == tmp_path / "BTCUSDT_aggtrades_1h.csv"
        assert out.exists()

    def test_output_sorted_ascending_by_timestamp(self, tmp_path):
        # Two rows in different hours; zip delivers them already sorted
        r1 = _make_aggtrade_row(_H1_T1, agg_id=1, price="100")
        r2 = _make_aggtrade_row(_H2_T1, agg_id=2, price="200")
        zip_bytes = _make_zip(_make_csv(r1, r2))
        with patch(_PATCH, return_value=_MockResponse(zip_bytes)):
            out = download_aggtrades_hourly(
                symbol="BTCUSDT",
                output_dir=tmp_path,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )
        timestamps = [ln.split(",")[0] for ln in out.read_text("utf-8").splitlines()[1:]]
        assert timestamps == sorted(timestamps)

    def test_rejects_empty_symbol(self, tmp_path):
        with pytest.raises(ValueError, match="symbol"):
            download_aggtrades_hourly(symbol="", output_dir=tmp_path)

    def test_past_month_uses_monthly_url(self, tmp_path):
        urls_called: list[str] = []

        def fake_urlopen(req, *, timeout=60):
            urls_called.append(req.full_url)
            raise _http_404()

        with patch(_PATCH, side_effect=fake_urlopen):
            download_aggtrades_hourly(
                symbol="BTCUSDT",
                output_dir=tmp_path,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert len(urls_called) == 1
        assert "/monthly/" in urls_called[0]
        assert "/daily/" not in urls_called[0]

    def test_no_auth_headers_sent(self, tmp_path):
        headers_seen: list[str] = []

        def fake_urlopen(req, *, timeout=60):
            headers_seen.extend(k.lower() for k, _ in req.header_items())
            raise _http_404()

        with patch(_PATCH, side_effect=fake_urlopen):
            download_aggtrades_hourly(
                symbol="BTCUSDT",
                output_dir=tmp_path,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert not any("apikey" in h or "x-mbx" in h or "authorization" in h
                       for h in headers_seen)

    def test_no_private_endpoints_in_source(self):
        text = Path("research/signal_observation/aggtrades_downloader.py").read_text(
            encoding="utf-8"
        )
        forbidden = (
            "requests", "ccxt", "pandas", "numpy",
            "X-MBX-APIKEY", "/fapi/v1/order", "userDataStream",
            "withdraw", "transfer", "leverage",
        )
        for token in forbidden:
            assert token not in text, f"forbidden token found: {token!r}"
