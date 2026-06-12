from __future__ import annotations

from datetime import datetime, timedelta, timezone

from research.hypothesis_agent.data.fetcher import OkxMarketDataFetcher


def _row(ts_ms: int, confirm: str = "1") -> list:
    return [str(ts_ms), "100", "101", "99", "100.5", "10", "0", "0", confirm]


class _StubFetcher(OkxMarketDataFetcher):
    def __init__(self, responses: list[dict]) -> None:
        super().__init__()
        self._responses = list(responses)
        self.captured_params: list[dict] = []

    def _request_json(self, path: str, params: dict[str, str]) -> dict:
        self.captured_params.append(dict(params))
        return self._responses.pop(0)


# --- existing parse test (updated to 9-field rows) ---

def test_fetch_candles_parses_okx_payload():
    class DummyFetcher(OkxMarketDataFetcher):
        def _request_json(self, path: str, params: dict[str, str]) -> dict:
            assert path == "/api/v5/market/candles"
            assert params["instId"] == "BTC-USDT"
            return {
                "data": [
                    ["1714608000000", "100", "110", "95", "108", "42", "0", "0", "1"],
                    ["1714607100000", "99", "101", "97", "100", "40", "0", "0", "1"],
                ]
            }

    fetcher = DummyFetcher()
    candles = fetcher.fetch_candles("BTC-USDT", "15m", limit=2)

    assert len(candles) == 2
    assert candles[0]["close"] == 100.0
    assert candles[1]["high"] == 110.0
    assert candles[0]["session"] in {"asia", "london", "ny", "london_ny_overlap"}


# --- confirm-flag filtering ---

def test_fetch_candles_excludes_unconfirmed_rows():
    ts1 = 1_700_000_000_000
    ts2 = 1_700_014_400_000
    fetcher = _StubFetcher([{"data": [_row(ts2, "0"), _row(ts1, "1")]}])
    candles = fetcher.fetch_candles("BTC-USDT", "4H")
    assert len(candles) == 1
    assert int(candles[0]["timestamp"].timestamp() * 1000) == ts1


def test_fetch_candles_includes_all_confirmed_rows():
    ts1 = 1_700_000_000_000
    ts2 = 1_700_014_400_000
    fetcher = _StubFetcher([{"data": [_row(ts2, "1"), _row(ts1, "1")]}])
    candles = fetcher.fetch_candles("BTC-USDT", "4H")
    assert len(candles) == 2


def test_fetch_candles_tolerates_short_rows_without_confirm_field():
    """Rows with fewer than 9 fields are treated as confirmed (backward compat)."""
    ts = 1_700_000_000_000
    short_row = [str(ts), "100", "101", "99", "100.5", "10"]
    fetcher = _StubFetcher([{"data": [short_row]}])
    candles = fetcher.fetch_candles("BTC-USDT", "4H")
    assert len(candles) == 1


# --- pagination uses `after`, not `before` ---

def test_fetch_candles_sends_after_param_when_provided():
    ts = 1_700_000_000_000
    fetcher = _StubFetcher([{"data": [_row(ts)]}])
    fetcher.fetch_candles("BTC-USDT", "4H", after="999999")
    assert fetcher.captured_params[0].get("after") == "999999"
    assert "before" not in fetcher.captured_params[0]


def test_fetch_candles_omits_after_when_none():
    ts = 1_700_000_000_000
    fetcher = _StubFetcher([{"data": [_row(ts)]}])
    fetcher.fetch_candles("BTC-USDT", "4H")
    assert "after" not in fetcher.captured_params[0]
    assert "before" not in fetcher.captured_params[0]


# --- fetch_history pagination uses `after` ---

def test_fetch_history_limit_paginates_with_after():
    """Each pagination batch should use after=<oldest_ms_of_prior_batch>."""
    bar_ms = 4 * 60 * 60 * 1000
    now_ms = 1_700_100_000_000
    page1 = [now_ms - i * bar_ms for i in range(1, 4)]   # 3 candles
    page2 = [now_ms - i * bar_ms for i in range(4, 7)]   # 3 older candles

    fetcher = _StubFetcher([
        {"data": [_row(ts) for ts in page1]},
        {"data": [_row(ts) for ts in page2]},
    ])
    candles = fetcher.fetch_history("BTC-USDT", "4H", days=7, limit=6)

    # First call: no after param
    assert "after" not in fetcher.captured_params[0]
    assert "before" not in fetcher.captured_params[0]
    # Second call: after = oldest timestamp of page1 (smallest in page1)
    assert fetcher.captured_params[1]["after"] == str(min(page1))
    assert "before" not in fetcher.captured_params[1]
    assert len(candles) == 6


def test_fetch_history_days_paginates_with_after():
    """Days-based fetch_history should also paginate with after."""
    bar_ms = 4 * 60 * 60 * 1000
    now = datetime.now(timezone.utc)
    # Put page1 well within the cutoff so the loop continues to page2
    page1_ts = [int((now - timedelta(hours=4 * i)).timestamp() * 1000) for i in range(1, 4)]
    # Page2 is older than the cutoff — loop stops after this batch
    cutoff = now - timedelta(days=2)
    page2_ts = [int((cutoff - timedelta(hours=4 * i)).timestamp() * 1000) for i in range(1, 4)]

    fetcher = _StubFetcher([
        {"data": [_row(ts) for ts in page1_ts]},
        {"data": [_row(ts) for ts in page2_ts]},
    ])
    fetcher.fetch_history("BTC-USDT", "4H", days=2)

    # First call has no after; second call uses after = oldest of page1
    assert "after" not in fetcher.captured_params[0]
    assert fetcher.captured_params[1]["after"] == str(min(page1_ts))
    assert "before" not in fetcher.captured_params[1]


def test_fetch_history_stops_when_batch_empty():
    fetcher = _StubFetcher([{"data": []}])
    candles = fetcher.fetch_history("BTC-USDT", "4H", days=7, limit=10)
    assert candles == []
    assert len(fetcher.captured_params) == 1
