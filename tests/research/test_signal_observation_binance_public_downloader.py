from __future__ import annotations

import json
import urllib.error
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest

from research.signal_observation.binance_public_downloader import (
    BINANCE_FUTURES_KLINES_URL,
    SUPPORTED_INTERVALS,
    download_binance_futures_klines,
)


BAR_MS_4H = 4 * 60 * 60 * 1000


class _MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


class _MockHTTPError(urllib.error.HTTPError):
    def __init__(self, code: int, body: str | bytes):
        super().__init__(url="https://fapi.binance.com/fapi/v1/klines", code=code, msg="error", hdrs=None, fp=None)
        self._body = body.encode("utf-8") if isinstance(body, str) else body

    def read(self) -> bytes:
        return self._body


class _NonClosingStringIO(StringIO):
    def close(self) -> None:
        return None


def _binance_row(
    open_ms: int,
    *,
    open_: str = "100",
    high: str = "101",
    low: str = "99",
    close: str = "100.5",
    volume: str = "10",
) -> list:
    """One Binance kline row in the wire shape (12 elements)."""
    return [
        open_ms,
        open_,
        high,
        low,
        close,
        volume,
        open_ms + 14_399_999,  # close_time
        "1000",  # quote_volume
        5,  # trades
        "500",  # taker_base_volume
        "5",  # taker_quote_volume
        "0",  # ignore
    ]


def _payload(rows: list[list]) -> list[list]:
    return rows


def _run_single_page(payload: list | dict | None = None):
    output = _NonClosingStringIO()
    requests: list = []

    if payload is None:
        payload = _payload(
            [
                _binance_row(1_700_000_000_000, open_="100"),
                _binance_row(1_700_000_000_000 + BAR_MS_4H, open_="102"),
            ]
        )

    def fake_urlopen(request):
        requests.append(request)
        return _MockResponse(payload)

    with patch(
        "research.signal_observation.binance_public_downloader.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ), patch.object(Path, "open", return_value=output):
        path = download_binance_futures_klines(
            symbol="BTCUSDT",
            interval="4h",
            output_csv="out.csv",
            limit=500,
        )
    return path, output.getvalue(), requests


def _run_bounded(
    *,
    responses: list[list | dict],
    start_time: int | str,
    end_time: int | str,
    limit: int = 5,
    max_pages: int = 5,
    symbol: str = "BTCUSDT",
    interval: str = "4h",
):
    output = _NonClosingStringIO()
    requests: list = []

    def fake_urlopen(request):
        requests.append(request)
        return _MockResponse(responses[len(requests) - 1])

    with patch(
        "research.signal_observation.binance_public_downloader.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ), patch.object(Path, "open", return_value=output):
        path = download_binance_futures_klines(
            symbol=symbol,
            interval=interval,
            output_csv="out.csv",
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            max_pages=max_pages,
        )
    return path, output.getvalue(), requests


# --- argument validation ---


def test_rejects_empty_symbol() -> None:
    with pytest.raises(ValueError, match="symbol"):
        download_binance_futures_klines(
            symbol="",
            interval="4h",
            output_csv="out.csv",
        )


def test_rejects_unsupported_interval() -> None:
    with pytest.raises(ValueError, match="interval"):
        download_binance_futures_klines(
            symbol="BTCUSDT",
            interval="15m",
            output_csv="out.csv",
        )


def test_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError, match="limit"):
        download_binance_futures_klines(
            symbol="BTCUSDT",
            interval="4h",
            output_csv="out.csv",
            limit=1501,
        )


def test_rejects_invalid_max_pages() -> None:
    with pytest.raises(ValueError, match="max_pages must be positive"):
        download_binance_futures_klines(
            symbol="BTCUSDT",
            interval="4h",
            output_csv="out.csv",
            start_time=1,
            end_time=2,
            max_pages=0,
        )


def test_rejects_half_bounded_args() -> None:
    with pytest.raises(ValueError, match="both start_time and end_time"):
        download_binance_futures_klines(
            symbol="BTCUSDT",
            interval="4h",
            output_csv="out.csv",
            start_time=1,
        )


def test_rejects_inverted_bounds() -> None:
    with pytest.raises(ValueError, match="strictly before"):
        _run_bounded(
            responses=[_payload([])],
            start_time=2_000_000_000_000,
            end_time=1_000_000_000_000,
            limit=5,
            max_pages=2,
        )


# --- single-page mode ---


def test_builds_url_with_correct_endpoint_and_params() -> None:
    _path, _csv_text, requests = _run_single_page()

    parsed = urlparse(requests[0].full_url)
    query = parse_qs(parsed.query)

    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == BINANCE_FUTURES_KLINES_URL
    assert query["symbol"] == ["BTCUSDT"]
    assert query["interval"] == ["4h"]
    assert query["limit"] == ["500"]
    assert "startTime" not in query
    assert "endTime" not in query


def test_writes_valid_csv_from_successful_single_page_response() -> None:
    _path, csv_text, _requests = _run_single_page()

    lines = csv_text.splitlines()
    assert lines[0] == "timestamp,open,high,low,close,volume"
    assert len(lines) == 3  # header + 2 rows
    # Ascending order in CSV.
    assert lines[1].split(",")[0] < lines[2].split(",")[0]


def test_single_page_supports_all_supported_intervals() -> None:
    output = _NonClosingStringIO()
    requests: list = []

    def fake_urlopen(request):
        requests.append(request)
        return _MockResponse(_payload([_binance_row(1_700_000_000_000)]))

    for interval in SUPPORTED_INTERVALS:
        with patch(
            "research.signal_observation.binance_public_downloader.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ), patch.object(Path, "open", return_value=output):
            download_binance_futures_klines(
                symbol="BTCUSDT",
                interval=interval,
                output_csv="out.csv",
                limit=1,
            )

    assert len(requests) == len(SUPPORTED_INTERVALS)


# --- bounded pagination ---


def test_bounded_pagination_sends_start_and_end_times() -> None:
    start_ms = 1_700_000_000_000
    end_ms = start_ms + 5 * BAR_MS_4H
    _path, _csv_text, requests = _run_bounded(
        responses=[_payload([_binance_row(start_ms + i * BAR_MS_4H) for i in range(2)])],
        start_time=start_ms,
        end_time=end_ms,
        limit=2,
        max_pages=1,
    )

    query = parse_qs(urlparse(requests[0].full_url).query)
    assert query["startTime"] == [str(start_ms)]
    assert query["endTime"] == [str(end_ms)]
    assert query["limit"] == ["2"]
    assert len(requests) == 1


def test_bounded_pagination_walks_forward_until_end() -> None:
    start_ms = 1_700_000_000_000
    end_ms = start_ms + 14 * BAR_MS_4H
    page1 = [_binance_row(start_ms + i * BAR_MS_4H) for i in range(5)]
    page2 = [_binance_row(start_ms + (5 + i) * BAR_MS_4H) for i in range(5)]
    page3 = [_binance_row(start_ms + (10 + i) * BAR_MS_4H) for i in range(5)]  # crosses end

    _path, csv_text, requests = _run_bounded(
        responses=[_payload(page1), _payload(page2), _payload(page3)],
        start_time=start_ms,
        end_time=end_ms,
        limit=5,
        max_pages=10,
    )

    # First call uses startTime=start_ms.
    q1 = parse_qs(urlparse(requests[0].full_url).query)
    assert q1["startTime"] == [str(start_ms)]
    # Second call advances startTime past previous page's latest open + 1.
    q2 = parse_qs(urlparse(requests[1].full_url).query)
    assert int(q2["startTime"][0]) == start_ms + 4 * BAR_MS_4H + 1
    # Third call should stop after this page since it crosses end_ms.
    assert len(requests) == 3
    # CSV: only timestamps within [start_ms, end_ms].
    lines = csv_text.splitlines()
    assert lines[0] == "timestamp,open,high,low,close,volume"
    data_lines = lines[1:]
    assert len(data_lines) == 15  # 5+5+5 all within bounds (last page latest = start + 14*4h = end_ms)
    timestamps = [line.split(",")[0] for line in data_lines]
    assert timestamps == sorted(timestamps)


def test_bounded_pagination_stops_at_end_time() -> None:
    start_ms = 1_700_000_000_000
    end_ms = start_ms + 3 * BAR_MS_4H
    page = [_binance_row(start_ms + i * BAR_MS_4H) for i in range(4)]  # crosses end

    _path, csv_text, requests = _run_bounded(
        responses=[_payload(page)],
        start_time=start_ms,
        end_time=end_ms,
        limit=10,
        max_pages=5,
    )

    # One page; latest open = start + 3*bar = end_ms; stops.
    assert len(requests) == 1
    data_lines = csv_text.splitlines()[1:]
    assert len(data_lines) == 4  # all 4 in bounds (inclusive end)


def test_bounded_pagination_stops_at_max_pages() -> None:
    start_ms = 1_700_000_000_000
    end_ms = start_ms + 10_000 * BAR_MS_4H  # very far ahead; never crossed

    def make_payload(window_start):
        return _payload([_binance_row(window_start + i * BAR_MS_4H) for i in range(5)])

    p1 = make_payload(start_ms)
    p2 = make_payload(start_ms + 5 * BAR_MS_4H + 1)
    p3 = make_payload(start_ms + 10 * BAR_MS_4H + 2)

    _path, _csv_text, requests = _run_bounded(
        responses=[p1, p2, p3],
        start_time=start_ms,
        end_time=end_ms,
        limit=5,
        max_pages=3,
    )

    assert len(requests) == 3  # stopped deterministically at max_pages


def test_bounded_pagination_stops_when_page_smaller_than_limit() -> None:
    start_ms = 1_700_000_000_000
    end_ms = start_ms + 1_000 * BAR_MS_4H
    short_page = [_binance_row(start_ms + i * BAR_MS_4H) for i in range(2)]

    _path, csv_text, requests = _run_bounded(
        responses=[_payload(short_page)],
        start_time=start_ms,
        end_time=end_ms,
        limit=5,
        max_pages=10,
    )

    assert len(requests) == 1
    assert len(csv_text.splitlines()[1:]) == 2


def test_bounded_pagination_filters_out_of_bound_rows() -> None:
    start_ms = 1_700_000_000_000
    end_ms = start_ms + 2 * BAR_MS_4H
    # Page includes one row BEFORE start (out of bounds).
    page = [
        _binance_row(start_ms - BAR_MS_4H),  # out
        _binance_row(start_ms),  # in
        _binance_row(start_ms + BAR_MS_4H),  # in
        _binance_row(start_ms + 2 * BAR_MS_4H),  # in (inclusive end)
    ]

    _path, csv_text, _requests = _run_bounded(
        responses=[_payload(page)],
        start_time=start_ms,
        end_time=end_ms,
        limit=10,
        max_pages=2,
    )

    data_lines = csv_text.splitlines()[1:]
    assert len(data_lines) == 3
    timestamps_ms = [int(line.split(",")[0][0:4]) for line in data_lines]  # year prefix is fine for ordering check
    # Confirm out-of-bound timestamp not present.
    iso_before_start = "1969"  # well before any in-bound iso
    assert all(iso_before_start not in line for line in data_lines)


def test_bounded_pagination_deduplicates_overlapping_timestamps() -> None:
    start_ms = 1_700_000_000_000
    end_ms = start_ms + 10 * BAR_MS_4H
    page1 = [_binance_row(start_ms + i * BAR_MS_4H) for i in range(3)]
    # Page2 repeats one timestamp from page1 and adds one new in-bound timestamp.
    repeat_ms = start_ms + 2 * BAR_MS_4H
    page2 = [_binance_row(repeat_ms), _binance_row(start_ms + 3 * BAR_MS_4H)]

    _path, csv_text, _requests = _run_bounded(
        responses=[_payload(page1), _payload(page2)],
        start_time=start_ms,
        end_time=end_ms,
        limit=3,
        max_pages=5,
    )

    data_lines = csv_text.splitlines()[1:]
    unique_timestamps = {line.split(",")[0] for line in data_lines}
    assert len(unique_timestamps) == len(data_lines)
    assert len(data_lines) == 4  # 3 + 1 new (one was a duplicate)


def test_bounded_pagination_accepts_int_timestamps() -> None:
    start_ms = 1_700_000_000_000
    end_ms = start_ms + 2 * BAR_MS_4H
    page = [_binance_row(start_ms + BAR_MS_4H)]

    _path, csv_text, _requests = _run_bounded(
        responses=[_payload(page)],
        start_time=int(start_ms),
        end_time=int(end_ms),
        limit=5,
        max_pages=2,
    )

    assert "timestamp,open,high,low,close,volume" in csv_text


# --- error handling ---


def test_handles_binance_error_dict_response() -> None:
    err_payload = {"code": -1121, "msg": "Invalid symbol."}
    with pytest.raises(ValueError, match="Binance API error"):
        _run_single_page(payload=err_payload)


def test_handles_binance_http_error_response() -> None:
    output = _NonClosingStringIO()
    err = _MockHTTPError(
        code=400,
        body=json.dumps({"code": -1121, "msg": "Invalid symbol."}),
    )

    def fake_urlopen(request):
        raise err

    with patch(
        "research.signal_observation.binance_public_downloader.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ), patch.object(Path, "open", return_value=output):
        with pytest.raises(ValueError, match="Binance API HTTP 400"):
            download_binance_futures_klines(
                symbol="BTCUSDT",
                interval="4h",
                output_csv="out.csv",
                limit=10,
            )


def test_handles_malformed_kline_row() -> None:
    bad_payload = _payload([[1_700_000_000_000, "100", "101"]])  # only 3 elements
    with pytest.raises(ValueError, match="kline row is incomplete"):
        _run_single_page(payload=bad_payload)


def test_handles_unexpected_payload_shape() -> None:
    weird_payload = "this is not a list"
    with pytest.raises(ValueError, match="unexpected Binance response shape"):
        _run_single_page(payload=weird_payload)


# --- credential / private-endpoint hygiene ---


def test_no_auth_headers_are_used() -> None:
    _path, _csv_text, requests = _run_single_page()
    headers = dict(requests[0].header_items())

    # Binance auth headers are X-MBX-APIKEY (read API key). Must not be set.
    assert all(key.upper() != "X-MBX-APIKEY" for key in headers)
    assert all(not key.upper().startswith("X-MBX-") for key in headers)


def test_no_private_endpoint_strings_or_external_dependencies() -> None:
    text = Path(
        "research/signal_observation/binance_public_downloader.py"
    ).read_text(encoding="utf-8")
    forbidden_tokens = (
        "requests",
        "ccxt",
        "pandas",
        "numpy",
        "X-MBX-APIKEY",
        "/fapi/v1/account",
        "/fapi/v1/order",
        "/fapi/v2/account",
        "/fapi/v2/positionRisk",
        "/fapi/v1/listenKey",
        "userDataStream",
        "openOrders",
        "myTrades",
        "leverage",
        "withdraw",
        "transfer",
    )

    for token in forbidden_tokens:
        assert token not in text
