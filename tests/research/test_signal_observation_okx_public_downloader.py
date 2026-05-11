from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest

from research.signal_observation.okx_public_downloader import (
    OKX_HISTORY_CANDLES_URL,
    download_okx_history_candles,
)


class _MockResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


class _NonClosingStringIO(StringIO):
    def close(self) -> None:
        return None


def _success_payload() -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [
            [
                "1714564800000",
                "102",
                "103",
                "101",
                "102.5",
                "12",
                "0",
                "0",
                "1",
            ],
            [
                "1714561200000",
                "100",
                "101",
                "99",
                "100.5",
                "10",
                "0",
                "0",
                "1",
            ],
            [
                "1714568400000",
                "103",
                "104",
                "102",
                "103.5",
                "14",
                "0",
                "0",
                "0",
            ],
        ],
    }


def _run_download(payload: dict | None = None):
    output = _NonClosingStringIO()
    requests = []

    def fake_urlopen(request):
        requests.append(request)
        return _MockResponse(payload or _success_payload())

    with patch(
        "research.signal_observation.okx_public_downloader.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ), patch.object(Path, "open", return_value=output):
        path = download_okx_history_candles(
            inst_id="BTC-USDT",
            bar="1H",
            output_csv="out.csv",
            limit=123,
            before="before-token",
            after="after-token",
        )
    return path, output.getvalue(), requests


def test_builds_url_with_correct_endpoint_and_params() -> None:
    _path, _csv_text, requests = _run_download()

    parsed = urlparse(requests[0].full_url)
    query = parse_qs(parsed.query)

    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == OKX_HISTORY_CANDLES_URL
    assert query["instId"] == ["BTC-USDT"]
    assert query["bar"] == ["1H"]
    assert query["limit"] == ["123"]
    assert query["before"] == ["before-token"]
    assert query["after"] == ["after-token"]


def test_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError, match="limit"):
        download_okx_history_candles(
            inst_id="BTC-USDT",
            bar="1H",
            output_csv="out.csv",
            limit=301,
        )


def test_rejects_unsupported_bar() -> None:
    with pytest.raises(ValueError, match="bar"):
        download_okx_history_candles(
            inst_id="BTC-USDT",
            bar="15m",
            output_csv="out.csv",
        )


def test_writes_valid_csv_from_successful_response() -> None:
    path, csv_text, _requests = _run_download()

    assert path == Path("out.csv")
    assert csv_text.splitlines()[0] == "timestamp,open,high,low,close,volume"
    assert "2024-05-01T11:00:00Z,100,101,99,100.5,10" in csv_text
    assert "2024-05-01T12:00:00Z,102,103,101,102.5,12" in csv_text


def test_excludes_unconfirmed_candles() -> None:
    _path, csv_text, _requests = _run_download()

    assert "103.5" not in csv_text


def test_sorts_candles_ascending() -> None:
    _path, csv_text, _requests = _run_download()
    lines = csv_text.splitlines()

    assert lines[1].startswith("2024-05-01T11:00:00Z")
    assert lines[2].startswith("2024-05-01T12:00:00Z")


def test_raises_on_nonzero_okx_code() -> None:
    with pytest.raises(ValueError, match="bad request"):
        _run_download({"code": "51000", "msg": "bad request", "data": []})


def test_no_auth_headers_are_used() -> None:
    _path, _csv_text, requests = _run_download()
    headers = dict(requests[0].header_items())

    assert all(not key.upper().startswith("OK-ACCESS") for key in headers)


def test_no_private_endpoint_strings_or_external_dependencies() -> None:
    text = Path("research/signal_observation/okx_public_downloader.py").read_text(
        encoding="utf-8"
    )
    forbidden_tokens = (
        "requests",
        "ccxt",
        "pandas",
        "numpy",
        "account",
        "order",
        "position",
        "OK-ACCESS",
    )

    for token in forbidden_tokens:
        assert token not in text


# --- bounded-pagination tests ---


def _bounded_payload(timestamps_ms: list[int], confirm_overrides: dict[int, str] | None = None) -> dict:
    """Build an OKX response payload listing candles in descending order."""

    overrides = confirm_overrides or {}
    data = []
    for ts in sorted(timestamps_ms, reverse=True):
        confirm = overrides.get(ts, "1")
        data.append([str(ts), "100", "101", "99", "100.5", "10", "0", "0", confirm])
    return {"code": "0", "msg": "", "data": data}


def _run_bounded(
    *,
    responses: list[dict],
    start_time: str | int,
    end_time: str | int,
    limit: int = 5,
    max_pages: int = 5,
):
    output = _NonClosingStringIO()
    requests = []

    def fake_urlopen(request):
        requests.append(request)
        return _MockResponse(responses[len(requests) - 1])

    with patch(
        "research.signal_observation.okx_public_downloader.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ), patch.object(Path, "open", return_value=output):
        path = download_okx_history_candles(
            inst_id="BTC-USDT-SWAP",
            bar="4H",
            output_csv="out.csv",
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            max_pages=max_pages,
        )
    return path, output.getvalue(), requests


def test_bounded_pagination_rejects_mixing_legacy_cursor_args() -> None:
    with pytest.raises(ValueError, match="bounded.*not both"):
        download_okx_history_candles(
            inst_id="BTC-USDT-SWAP",
            bar="4H",
            output_csv="out.csv",
            start_time="1640995200000",
            end_time="1702814400000",
            before="cursor",
        )


def test_bounded_pagination_requires_both_bounds() -> None:
    with pytest.raises(ValueError, match="both start_time and end_time"):
        download_okx_history_candles(
            inst_id="BTC-USDT-SWAP",
            bar="4H",
            output_csv="out.csv",
            start_time="1640995200000",
        )


def test_bounded_pagination_rejects_inverted_bounds() -> None:
    with pytest.raises(ValueError, match="strictly before"):
        download_okx_history_candles(
            inst_id="BTC-USDT-SWAP",
            bar="4H",
            output_csv="out.csv",
            start_time="1702814400000",
            end_time="1640995200000",
        )


def test_bounded_pagination_rejects_invalid_max_pages() -> None:
    with pytest.raises(ValueError, match="max_pages must be positive"):
        download_okx_history_candles(
            inst_id="BTC-USDT-SWAP",
            bar="4H",
            output_csv="out.csv",
            start_time="1640995200000",
            end_time="1702814400000",
            max_pages=0,
        )


def test_bounded_pagination_walks_back_until_start_reached() -> None:
    # 4H bar = 14_400_000 ms. Build 3 pages of 5 candles each, descending.
    bar_ms = 4 * 60 * 60 * 1000
    end_ms = 1_000_000_000_000
    start_ms = end_ms - 12 * bar_ms  # 12 bars of room
    page1 = [end_ms - i * bar_ms for i in range(1, 6)]  # 5 candles below end_ms
    page2 = [page1[-1] - i * bar_ms for i in range(1, 6)]
    page3 = [page2[-1] - i * bar_ms for i in range(1, 6)]  # crosses start

    _path, csv_text, requests = _run_bounded(
        responses=[
            _bounded_payload(page1),
            _bounded_payload(page2),
            _bounded_payload(page3),
        ],
        start_time=start_ms,
        end_time=end_ms,
        limit=5,
        max_pages=10,
    )

    # First call should use after=end_ms.
    first_query = parse_qs(urlparse(requests[0].full_url).query)
    assert first_query["after"] == [str(end_ms)]
    assert "before" not in first_query
    # Pagination cursor should decrease deterministically across pages.
    second_query = parse_qs(urlparse(requests[1].full_url).query)
    third_query = parse_qs(urlparse(requests[2].full_url).query)
    assert int(second_query["after"][0]) == min(page1)
    assert int(third_query["after"][0]) == min(page2)
    # Should stop after the page that crosses start_ms (no fourth call).
    assert len(requests) == 3
    # CSV body should contain only timestamps within [start_ms, end_ms].
    lines = csv_text.splitlines()
    assert lines[0] == "timestamp,open,high,low,close,volume"
    data_lines = lines[1:]
    assert all(line.split(",")[0] >= "1970" for line in data_lines)
    assert len(data_lines) >= 12  # at least the in-range candles
    # Timestamps must be ascending in the CSV.
    timestamps = [line.split(",")[0] for line in data_lines]
    assert timestamps == sorted(timestamps)


def test_bounded_pagination_filters_unconfirmed_rows() -> None:
    bar_ms = 4 * 60 * 60 * 1000
    end_ms = 1_000_000_000_000
    start_ms = end_ms - 5 * bar_ms
    page = [end_ms - i * bar_ms for i in range(1, 4)]
    unconfirmed = page[0]
    _path, csv_text, _requests = _run_bounded(
        responses=[_bounded_payload(page, confirm_overrides={unconfirmed: "0"})],
        start_time=start_ms,
        end_time=end_ms,
        limit=10,
        max_pages=3,
    )

    lines = csv_text.splitlines()
    data_lines = lines[1:]
    # Unconfirmed candle must be excluded; the other two confirmed candles remain.
    assert len(data_lines) == 2
    assert str(unconfirmed) not in csv_text


def test_bounded_pagination_filters_out_of_bound_rows() -> None:
    bar_ms = 4 * 60 * 60 * 1000
    end_ms = 1_000_000_000_000
    start_ms = end_ms - 3 * bar_ms
    # Build a single page that includes one candle BELOW start_ms.
    page = [end_ms - i * bar_ms for i in range(1, 6)]  # 5 candles; last is below start
    _path, csv_text, _requests = _run_bounded(
        responses=[_bounded_payload(page)],
        start_time=start_ms,
        end_time=end_ms,
        limit=10,
        max_pages=3,
    )

    data_lines = csv_text.splitlines()[1:]
    # Only candles within [start_ms, end_ms] should remain.
    assert len(data_lines) == 3
    out_of_bound_ts = end_ms - 4 * bar_ms
    assert str(out_of_bound_ts) not in csv_text


def test_bounded_pagination_deduplicates_overlapping_timestamps() -> None:
    bar_ms = 4 * 60 * 60 * 1000
    end_ms = 1_000_000_000_000
    start_ms = end_ms - 10 * bar_ms
    page1 = [end_ms - i * bar_ms for i in range(1, 4)]  # 3 candles, full limit
    # Second page repeats one of page1's timestamps and adds one new lower one.
    # Page2 is shorter than limit so pagination stops cleanly.
    repeat_ts = page1[-1]
    page2 = [repeat_ts, repeat_ts - bar_ms]

    _path, csv_text, _requests = _run_bounded(
        responses=[_bounded_payload(page1), _bounded_payload(page2)],
        start_time=start_ms,
        end_time=end_ms,
        limit=3,
        max_pages=5,
    )

    data_lines = csv_text.splitlines()[1:]
    unique_timestamps = {line.split(",")[0] for line in data_lines}
    assert len(unique_timestamps) == len(data_lines)  # no duplicates
    assert len(data_lines) == 4  # 3 + 1 new (one was a duplicate)


def test_bounded_pagination_stops_at_max_pages() -> None:
    bar_ms = 4 * 60 * 60 * 1000
    end_ms = 1_000_000_000_000
    start_ms = end_ms - 1_000 * bar_ms  # very far back; never crossed

    def make_payload(after_ms: int) -> dict:
        return _bounded_payload([after_ms - i * bar_ms for i in range(1, 6)])

    # Pre-generate 3 payloads matching the cursor each iteration would derive.
    p1 = make_payload(end_ms)
    p1_oldest = end_ms - 5 * bar_ms
    p2 = make_payload(p1_oldest)
    p2_oldest = p1_oldest - 5 * bar_ms
    p3 = make_payload(p2_oldest)

    _path, _csv_text, requests = _run_bounded(
        responses=[p1, p2, p3],
        start_time=start_ms,
        end_time=end_ms,
        limit=5,
        max_pages=3,
    )

    # Pagination must stop deterministically at max_pages=3 (never crosses start).
    assert len(requests) == 3


def test_bounded_pagination_stops_when_page_smaller_than_limit() -> None:
    bar_ms = 4 * 60 * 60 * 1000
    end_ms = 1_000_000_000_000
    start_ms = end_ms - 100 * bar_ms
    # First page returns only 2 candles even though limit=5 → exchange has no more.
    short_page = [end_ms - bar_ms, end_ms - 2 * bar_ms]

    _path, csv_text, requests = _run_bounded(
        responses=[_bounded_payload(short_page)],
        start_time=start_ms,
        end_time=end_ms,
        limit=5,
        max_pages=10,
    )

    assert len(requests) == 1
    data_lines = csv_text.splitlines()[1:]
    assert len(data_lines) == 2


def test_bounded_pagination_propagates_okx_error_code() -> None:
    with pytest.raises(ValueError, match="bad request"):
        _run_bounded(
            responses=[{"code": "51000", "msg": "bad request", "data": []}],
            start_time=0,
            end_time=14_400_000,
            limit=5,
            max_pages=2,
        )


def test_bounded_pagination_accepts_int_timestamps() -> None:
    bar_ms = 4 * 60 * 60 * 1000
    end_ms = 1_000_000_000_000
    start_ms = end_ms - 2 * bar_ms
    page = [end_ms - bar_ms]

    _path, csv_text, _requests = _run_bounded(
        responses=[_bounded_payload(page)],
        start_time=int(start_ms),
        end_time=int(end_ms),
        limit=5,
        max_pages=2,
    )

    assert "timestamp,open,high,low,close,volume" in csv_text


def test_bounded_pagination_no_legacy_cursor_in_pagination_requests() -> None:
    bar_ms = 4 * 60 * 60 * 1000
    end_ms = 1_000_000_000_000
    start_ms = end_ms - 5 * bar_ms
    page = [end_ms - bar_ms]

    _path, _csv_text, requests = _run_bounded(
        responses=[_bounded_payload(page)],
        start_time=start_ms,
        end_time=end_ms,
        limit=5,
        max_pages=2,
    )

    query = parse_qs(urlparse(requests[0].full_url).query)
    # Bounded mode must never send a `before` cursor.
    assert "before" not in query
    assert query["after"] == [str(end_ms)]
