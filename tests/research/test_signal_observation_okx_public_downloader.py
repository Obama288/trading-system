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
