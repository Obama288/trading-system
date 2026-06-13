"""Tests for coinalyze_downloader — all HTTP is mocked; no network calls."""
from __future__ import annotations

import csv
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from research.signal_observation.coinalyze_downloader import (
    LIQUIDATION_CSV_HEADER,
    OHLCV_CSV_HEADER,
    _s_to_iso,
    fetch_liquidation_4h_history,
    fetch_ohlcv_4h_history,
    require_api_key,
    write_liquidation_csv,
    write_ohlcv_csv,
)

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

_T1 = 1_700_000_000  # seconds  (~2023-11-14) — API returns POSIX seconds, verified live
_T2 = _T1 + 4 * 3600  # next 4H bar
_T3 = _T2 + 4 * 3600

_SYM = "BTCUSDT_PERP.A"


def _ohlcv_bar(t: int) -> dict:
    return {"t": t, "o": 30000, "h": 31000, "l": 29500, "c": 30500, "v": 100}


def _liq_bar(t: int) -> dict:
    return {"t": t, "l": 500_000, "s": 300_000}


def _response(sym: str, history: list[dict]) -> bytes:
    return json.dumps([{"symbol": sym, "history": history}]).encode()


class _MockUrlopen:
    """Callable that pops pre-queued bytes responses for urlopen side_effect."""

    def __init__(self, pages: list[bytes]) -> None:
        self._pages = list(pages)

    def __call__(self, req):
        data = self._pages.pop(0)

        class _Resp:
            def __init__(self, d: bytes) -> None:
                self._d = d

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def read(self) -> bytes:
                return self._d

        return _Resp(data)


def _mock_429(retry_after: float = 0.01):
    """urlopen side_effect that raises HTTP 429 once, then returns success."""
    calls = 0

    def _side(req):
        nonlocal calls
        calls += 1
        if calls == 1:
            hdrs = MagicMock()
            hdrs.get = lambda h, *_: str(retry_after) if h == "Retry-After" else None
            raise urllib.error.HTTPError(
                url="x", code=429, msg="Too Many Requests", hdrs=hdrs, fp=None
            )
        # Second call succeeds
        class _Resp:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self): return _response(_SYM, [_ohlcv_bar(_T1)])
        return _Resp()

    return _side


# ---------------------------------------------------------------------------
# Test: key-missing error
# ---------------------------------------------------------------------------

def test_api_key_missing_raises_clear_error(monkeypatch):
    monkeypatch.delenv("COINALYZE_API_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="COINALYZE_API_KEY"):
        require_api_key()


def test_api_key_present_is_returned(monkeypatch):
    monkeypatch.setenv("COINALYZE_API_KEY", "test-key-abc")
    assert require_api_key() == "test-key-abc"


# ---------------------------------------------------------------------------
# Test: OHLCV CSV schema
# ---------------------------------------------------------------------------

def test_ohlcv_csv_header_and_rows(tmp_path):
    bars = [_ohlcv_bar(_T1), _ohlcv_bar(_T2)]
    out = write_ohlcv_csv(bars, tmp_path / "btc_ohlcv_4h.csv")
    rows = list(csv.reader(out.read_text(encoding="utf-8").splitlines()))

    # Header matches constant
    assert rows[0] == list(OHLCV_CSV_HEADER)
    assert len(rows) == 3  # header + 2 bars

    # timestamp is ISO UTC
    assert rows[1][0].endswith("Z")
    assert "T" in rows[1][0]

    # Numeric fields are preserved as strings
    assert rows[1][1] == "30000"   # open
    assert rows[1][4] == "30500"  # close


def test_ohlcv_csv_creates_parent_dirs(tmp_path):
    bars = [_ohlcv_bar(_T1)]
    path = tmp_path / "nested" / "dir" / "test.csv"
    write_ohlcv_csv(bars, path)
    assert path.exists()


# ---------------------------------------------------------------------------
# Test: liquidation CSV schema
# ---------------------------------------------------------------------------

def test_liquidation_csv_header_and_rows(tmp_path):
    bars = [_liq_bar(_T1), _liq_bar(_T2)]
    out = write_liquidation_csv(bars, tmp_path / "btc_liq_4h.csv")
    rows = list(csv.reader(out.read_text(encoding="utf-8").splitlines()))

    assert rows[0] == list(LIQUIDATION_CSV_HEADER)
    assert len(rows) == 3

    assert rows[1][0].endswith("Z")   # timestamp_utc
    assert rows[1][1] == "500000"     # long_notional_usd
    assert rows[1][2] == "300000"     # short_notional_usd


# ---------------------------------------------------------------------------
# Test: retry on 429
# ---------------------------------------------------------------------------

def test_retry_on_429_then_success():
    """A 429 response is retried; the second attempt returns data."""
    with patch("urllib.request.urlopen", side_effect=_mock_429()), \
         patch("time.sleep"):
        result = fetch_ohlcv_4h_history([_SYM], api_key="key")

    assert len(result[_SYM]) == 1
    assert result[_SYM][0]["t"] == _T1


def test_retry_reads_retry_after_header():
    """Retry-After header value is passed to time.sleep on 429."""
    sleep_calls: list[float] = []

    def _fake_sleep(s: float) -> None:
        sleep_calls.append(s)

    with patch("urllib.request.urlopen", side_effect=_mock_429(retry_after=7.5)), \
         patch("time.sleep", side_effect=_fake_sleep):
        fetch_ohlcv_4h_history([_SYM], api_key="key")

    assert any(abs(s - 7.5) < 0.01 for s in sleep_calls), (
        f"expected time.sleep(7.5) call; got {sleep_calls}"
    )


# ---------------------------------------------------------------------------
# Test: pagination
# ---------------------------------------------------------------------------

def test_pagination_stops_on_empty_second_page():
    """Second page with empty history stops the loop after one extra request."""
    page1 = _response(_SYM, [_ohlcv_bar(_T1), _ohlcv_bar(_T2)])
    page2 = _response(_SYM, [])  # empty → stop

    with patch("urllib.request.urlopen", side_effect=_MockUrlopen([page1, page2])), \
         patch("time.sleep"):
        result = fetch_ohlcv_4h_history([_SYM], api_key="key")

    assert [b["t"] for b in result[_SYM]] == [_T1, _T2]


def test_pagination_deduplicates_overlapping_pages():
    """Bars returned on both pages are counted only once."""
    bar1 = _ohlcv_bar(_T1)
    bar2 = _ohlcv_bar(_T2)
    page1 = _response(_SYM, [bar1, bar2])
    page2 = _response(_SYM, [bar1])  # overlap → deduplicated

    with patch("urllib.request.urlopen", side_effect=_MockUrlopen([page1, page2])), \
         patch("time.sleep"):
        result = fetch_ohlcv_4h_history([_SYM], api_key="key")

    assert len(result[_SYM]) == 2


def test_pagination_throttle_called_between_pages():
    """time.sleep is called with a positive value between page requests."""
    page1 = _response(_SYM, [_ohlcv_bar(_T2)])
    page2 = _response(_SYM, [])

    sleep_calls: list[float] = []
    with patch("urllib.request.urlopen", side_effect=_MockUrlopen([page1, page2])), \
         patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        fetch_ohlcv_4h_history([_SYM], api_key="key")

    assert any(s > 0 for s in sleep_calls), (
        "throttle should call time.sleep with a positive value between pages"
    )


# ---------------------------------------------------------------------------
# Test: liquidation endpoint uses convert_to_usd=true
# ---------------------------------------------------------------------------

def test_liquidation_fetch_passes_convert_to_usd():
    """Liquidation endpoint must set convert_to_usd=true in the query."""
    captured_urls: list[str] = []

    def _fake_urlopen(req):
        captured_urls.append(req.full_url)

        class _R:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self): return _response(_SYM, [])
        return _R()

    with patch("urllib.request.urlopen", side_effect=_fake_urlopen), \
         patch("time.sleep"):
        fetch_liquidation_4h_history([_SYM], api_key="key")

    assert captured_urls, "urlopen was not called"
    assert "convert_to_usd=true" in captured_urls[0], (
        f"expected convert_to_usd=true in URL; got {captured_urls[0]}"
    )
