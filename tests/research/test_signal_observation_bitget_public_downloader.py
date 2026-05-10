from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest

from research.signal_observation.bitget_public_downloader import (
    BITGET_HISTORY_CANDLES_URL,
    download_bitget_history_candles,
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
        "code": "00000",
        "msg": "success",
        "data": [
            [
                "1714564800000",
                "102",
                "103",
                "101",
                "102.5",
                "12",
                "1224",
            ],
            [
                "1714561200000",
                "100",
                "101",
                "99",
                "100.5",
                "10",
                "1005",
            ],
        ],
    }


def _success_payload_page_two() -> dict:
    return {
        "code": "00000",
        "msg": "success",
        "data": [
            [
                "1714572000000",
                "104",
                "105",
                "103",
                "104.5",
                "14",
                "1463",
            ],
            [
                "1714564800000",
                "999",
                "999",
                "999",
                "999",
                "999",
                "999",
            ],
        ],
    }


def _run_download(
    payload: dict | None = None,
    *,
    payloads: list[dict] | None = None,
    limit: int = 123,
    start_time: str | None = "1714561200000",
    end_time: str | None = "1714564800000",
    max_pages: int = 1,
    granularity: str = "1H",
):
    output = _NonClosingStringIO()
    requests = []
    payload_queue = list(payloads) if payloads is not None else None

    def fake_urlopen(request):
        requests.append(request)
        if payload_queue is not None:
            return _MockResponse(payload_queue.pop(0))
        return _MockResponse(payload or _success_payload())

    with patch(
        "research.signal_observation.bitget_public_downloader.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ), patch.object(Path, "open", return_value=output):
        path = download_bitget_history_candles(
            symbol="BTCUSDT",
            product_type="USDT-FUTURES",
            granularity=granularity,
            output_csv="out.csv",
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            max_pages=max_pages,
        )
    return path, output.getvalue(), requests


def test_builds_url_with_correct_endpoint_and_params() -> None:
    _path, _csv_text, requests = _run_download()

    parsed = urlparse(requests[0].full_url)
    query = parse_qs(parsed.query)

    assert (
        f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        == BITGET_HISTORY_CANDLES_URL
    )
    assert query["symbol"] == ["BTCUSDT"]
    assert query["productType"] == ["USDT-FUTURES"]
    assert query["granularity"] == ["1H"]
    assert query["limit"] == ["123"]
    assert query["startTime"] == ["1714561200000"]
    assert query["endTime"] == ["1714564800000"]


def test_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError, match="limit"):
        download_bitget_history_candles(
            symbol="BTCUSDT",
            product_type="USDT-FUTURES",
            granularity="1H",
            output_csv="out.csv",
            limit=201,
        )


def test_rejects_invalid_max_pages() -> None:
    with pytest.raises(ValueError, match="max_pages"):
        download_bitget_history_candles(
            symbol="BTCUSDT",
            product_type="USDT-FUTURES",
            granularity="1H",
            output_csv="out.csv",
            max_pages=0,
        )


def test_rejects_unsupported_granularity() -> None:
    with pytest.raises(ValueError, match="granularity"):
        download_bitget_history_candles(
            symbol="BTCUSDT",
            product_type="USDT-FUTURES",
            granularity="15m",
            output_csv="out.csv",
        )


def test_rejects_unsupported_product_type() -> None:
    with pytest.raises(ValueError, match="product_type"):
        download_bitget_history_candles(
            symbol="BTCUSDT",
            product_type="SPOT",
            granularity="1H",
            output_csv="out.csv",
        )


def test_writes_valid_csv_from_successful_response() -> None:
    path, csv_text, _requests = _run_download()

    assert path == Path("out.csv")
    assert csv_text.splitlines()[0] == "timestamp,open,high,low,close,volume"
    assert "2024-05-01T11:00:00Z,100,101,99,100.5,10" in csv_text
    assert "2024-05-01T12:00:00Z,102,103,101,102.5,12" in csv_text
    assert "1224" not in csv_text


def test_sorts_candles_ascending() -> None:
    _path, csv_text, _requests = _run_download()
    lines = csv_text.splitlines()

    assert lines[1].startswith("2024-05-01T11:00:00Z")
    assert lines[2].startswith("2024-05-01T12:00:00Z")


def test_unbounded_forward_multi_page_advances_by_newest_plus_one_with_dedup() -> None:
    """Legacy unbounded-forward (start_time only): cursor advances by max_timestamp + 1."""
    _path, csv_text, requests = _run_download(
        payloads=[_success_payload(), _success_payload_page_two()],
        limit=2,
        end_time=None,
        max_pages=2,
    )
    lines = csv_text.splitlines()
    first_query = parse_qs(urlparse(requests[0].full_url).query)
    second_query = parse_qs(urlparse(requests[1].full_url).query)

    assert len(requests) == 2
    assert "endTime" not in first_query
    assert "endTime" not in second_query
    assert second_query["startTime"] == ["1714564800001"]
    assert lines == [
        "timestamp,open,high,low,close,volume",
        "2024-05-01T11:00:00Z,100,101,99,100.5,10",
        "2024-05-01T12:00:00Z,999,999,999,999,999",
        "2024-05-01T14:00:00Z,104,105,103,104.5,14",
    ]


def test_bounded_range_pagination_chunks_endtime_per_page() -> None:
    """Each page's endTime is bounded to limit*granularity_ms — never the far end."""
    page_one = {
        "code": "00000",
        "msg": "success",
        "data": [
            ["1714568400000", "10", "11", "9", "10.5", "1", "10"],
            ["1714564800000", "10", "11", "9", "10.5", "1", "10"],
        ],
    }
    page_two = {
        "code": "00000",
        "msg": "success",
        "data": [
            ["1714572000000", "20", "21", "19", "20.5", "2", "40"],
        ],
    }

    _path, _csv_text, requests = _run_download(
        payloads=[page_one, page_two],
        limit=2,
        start_time="1714561200000",
        end_time="1714572000000",
        max_pages=4,
    )

    first_query = parse_qs(urlparse(requests[0].full_url).query)
    second_query = parse_qs(urlparse(requests[1].full_url).query)

    # Per-page endTime is chunk-bounded, not the far end of the locked range.
    assert first_query["endTime"] == ["1714568399999"]
    assert int(first_query["endTime"][0]) < 1714572000000
    # Second page picks up at chunk_end + 1 and caps endTime at the locked end.
    assert second_query["startTime"] == ["1714568400000"]
    assert second_query["endTime"] == ["1714572000000"]


def test_bounded_range_pagination_filters_rows_outside_locked_range() -> None:
    """Rows outside [start_time, end_time] are dropped from the CSV output."""
    page = {
        "code": "00000",
        "msg": "success",
        "data": [
            ["1714564800000", "10", "11", "9", "10.5", "1", "10"],
            ["1714557600000", "20", "20", "20", "20", "1", "10"],
        ],
    }

    _path, csv_text, _requests = _run_download(
        payloads=[page],
        limit=2,
        start_time="1714561200000",
        end_time="1714568399999",
        max_pages=1,
    )

    # Out-of-range timestamp 1714557600000 (= 2024-05-01T10:00:00Z) is filtered.
    assert "2024-05-01T10:00:00Z" not in csv_text
    assert "20,20,20,20" not in csv_text
    assert "2024-05-01T12:00:00Z" in csv_text


def test_bounded_range_pagination_stops_at_end_time() -> None:
    """No request issued past end_time; pagination terminates at the locked bound."""
    payloads = [
        {
            "code": "00000",
            "msg": "success",
            "data": [
                ["1714564800000", "1", "1", "1", "1", "1", "1"],
                ["1714561200000", "1", "1", "1", "1", "1", "1"],
            ],
        },
        {
            "code": "00000",
            "msg": "success",
            "data": [
                ["1714572000000", "1", "1", "1", "1", "1", "1"],
            ],
        },
    ]

    _path, _csv_text, requests = _run_download(
        payloads=payloads,
        limit=2,
        start_time="1714561200000",
        end_time="1714572000000",
        max_pages=10,
    )

    # 3-hour range / 2-hour chunk = 2 pages; pagination stops naturally.
    assert len(requests) == 2
    for request in requests:
        query = parse_qs(urlparse(request.full_url).query)
        assert int(query["startTime"][0]) <= 1714572000000
        assert int(query["endTime"][0]) <= 1714572000000


def test_bounded_range_pagination_avoids_duplicate_timestamps() -> None:
    """Dedup remains intact when chunk responses overlap at a boundary."""
    page_one = {
        "code": "00000",
        "msg": "success",
        "data": [
            ["1714564800000", "1", "1", "1", "1", "1", "1"],
            ["1714561200000", "2", "2", "2", "2", "2", "2"],
        ],
    }
    page_two = {
        "code": "00000",
        "msg": "success",
        "data": [
            ["1714572000000", "3", "3", "3", "3", "3", "3"],
            ["1714568400000", "4", "4", "4", "4", "4", "4"],
        ],
    }

    _path, csv_text, _requests = _run_download(
        payloads=[page_one, page_two],
        limit=2,
        start_time="1714561200000",
        end_time="1714572000000",
        max_pages=4,
    )

    body_lines = csv_text.splitlines()[1:]
    timestamps = [line.split(",")[0] for line in body_lines]
    assert len(timestamps) == len(set(timestamps))


def test_bounded_range_per_page_span_does_not_exceed_chunk_size() -> None:
    """Each page's (endTime - startTime + 1) must be <= limit * granularity_ms."""
    payloads = [
        {"code": "00000", "msg": "success", "data": [
            ["1714564800000", "1", "1", "1", "1", "1", "1"],
        ]},
        {"code": "00000", "msg": "success", "data": [
            ["1714572000000", "1", "1", "1", "1", "1", "1"],
        ]},
    ]

    _path, _csv_text, requests = _run_download(
        payloads=payloads,
        limit=2,
        start_time="1714561200000",
        end_time="1714572000000",
        max_pages=10,
    )

    chunk_max_span_ms = 2 * 3_600_000  # limit * 1H
    for request in requests:
        query = parse_qs(urlparse(request.full_url).query)
        span = int(query["endTime"][0]) - int(query["startTime"][0]) + 1
        assert span <= chunk_max_span_ms


def test_bounded_range_advances_through_empty_intermediate_chunk() -> None:
    """An empty intermediate chunk advances to the next chunk instead of breaking."""
    payloads = [
        {"code": "00000", "msg": "success", "data": []},
        {
            "code": "00000",
            "msg": "success",
            "data": [
                ["1714572000000", "1", "1", "1", "1", "1", "1"],
            ],
        },
    ]

    _path, csv_text, requests = _run_download(
        payloads=payloads,
        limit=2,
        start_time="1714561200000",
        end_time="1714572000000",
        max_pages=4,
    )

    assert len(requests) >= 2
    assert "2024-05-01T14:00:00Z" in csv_text


def test_bounded_range_4h_granularity_uses_14_400_000_ms_per_bar() -> None:
    """4H granularity expands the chunk size proportionally."""
    page = {
        "code": "00000",
        "msg": "success",
        "data": [
            ["1714564800000", "1", "1", "1", "1", "1", "1"],
            ["1714550400000", "1", "1", "1", "1", "1", "1"],
        ],
    }

    _path, _csv_text, requests = _run_download(
        payloads=[page],
        limit=2,
        start_time="1714550400000",
        end_time="1714694400000",
        max_pages=1,
        granularity="4H",
    )

    first_query = parse_qs(urlparse(requests[0].full_url).query)
    # chunk_span = 2 * 14_400_000 = 28_800_000.
    assert first_query["endTime"] == ["1714579199999"]


def test_rejects_inverted_start_after_end_time() -> None:
    with pytest.raises(
        ValueError,
        match="start_time must be less than or equal to end_time",
    ):
        download_bitget_history_candles(
            symbol="BTCUSDT",
            product_type="USDT-FUTURES",
            granularity="1H",
            output_csv="out.csv",
            start_time="1714572000000",
            end_time="1714561200000",
        )


def test_max_pages_guard_limits_public_requests() -> None:
    _path, _csv_text, requests = _run_download(
        payloads=[_success_payload(), _success_payload_page_two()],
        limit=2,
        end_time="1714572000000",
        max_pages=1,
    )

    assert len(requests) == 1


def test_backward_pagination_uses_end_time_cursor_when_no_start_time() -> None:
    _path, _csv_text, requests = _run_download(
        payloads=[_success_payload(), _success_payload_page_two()],
        limit=2,
        start_time=None,
        end_time=None,
        max_pages=2,
    )
    second_query = parse_qs(urlparse(requests[1].full_url).query)

    assert len(requests) == 2
    assert "startTime" not in second_query
    assert second_query["endTime"] == ["1714561199999"]


def test_empty_candle_response_writes_header_only() -> None:
    _path, csv_text, _requests = _run_download(
        {"code": "00000", "msg": "success", "data": []}
    )

    assert csv_text.splitlines() == ["timestamp,open,high,low,close,volume"]


def test_raises_on_nonzero_bitget_code() -> None:
    with pytest.raises(ValueError, match="bad request"):
        _run_download({"code": "40001", "msg": "bad request", "data": []})


def test_no_auth_headers_are_used() -> None:
    _path, _csv_text, requests = _run_download(
        payloads=[_success_payload(), _success_payload_page_two()],
        limit=2,
        end_time="1714572000000",
        max_pages=2,
    )

    for request in requests:
        headers = dict(request.header_items())
        assert all(not key.upper().startswith("ACCESS") for key in headers)
        assert all(not key.upper().startswith("OK-ACCESS") for key in headers)


def test_no_private_endpoint_strings_or_external_dependencies() -> None:
    text = Path("research/signal_observation/bitget_public_downloader.py").read_text(
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
        "ACCESS-KEY",
        "signature",
    )

    for token in forbidden_tokens:
        assert token not in text
