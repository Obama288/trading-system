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


def _run_download(payload: dict | None = None):
    output = _NonClosingStringIO()
    requests = []

    def fake_urlopen(request):
        requests.append(request)
        return _MockResponse(payload or _success_payload())

    with patch(
        "research.signal_observation.bitget_public_downloader.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ), patch.object(Path, "open", return_value=output):
        path = download_bitget_history_candles(
            symbol="BTCUSDT",
            product_type="USDT-FUTURES",
            granularity="1H",
            output_csv="out.csv",
            limit=123,
            start_time="1714561200000",
            end_time="1714564800000",
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


def test_empty_candle_response_writes_header_only() -> None:
    _path, csv_text, _requests = _run_download(
        {"code": "00000", "msg": "success", "data": []}
    )

    assert csv_text.splitlines() == ["timestamp,open,high,low,close,volume"]


def test_raises_on_nonzero_bitget_code() -> None:
    with pytest.raises(ValueError, match="bad request"):
        _run_download({"code": "40001", "msg": "bad request", "data": []})


def test_no_auth_headers_are_used() -> None:
    _path, _csv_text, requests = _run_download()
    headers = dict(requests[0].header_items())

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
