from __future__ import annotations

from datetime import datetime, timezone

from libs.clients.okx_market_data_fetcher import OkxMarketDataFetcher


def _ts_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _row(ts_ms: int, confirm: str = "1") -> list:
    return [str(ts_ms), "100", "101", "99", "100.5", "10", "0", "0", confirm]


class _StubFetcher(OkxMarketDataFetcher):
    def __init__(self, responses: list[dict]) -> None:
        super().__init__(base_url="http://stub")
        self._responses = list(responses)
        self.captured_params: list[dict] = []

    def _request_json(self, path: str, params: dict[str, str]) -> dict:
        self.captured_params.append(dict(params))
        return self._responses.pop(0)


# --- confirm-flag filtering ---

def test_fetch_candles_excludes_unconfirmed_rows():
    ts1 = 1_700_000_000_000
    ts2 = 1_700_014_400_000
    fetcher = _StubFetcher([{"data": [_row(ts2, "0"), _row(ts1, "1")]}])
    candles = fetcher.fetch_candles("BTC-USDT", "4H")
    assert len(candles) == 1
    assert candles[0]["close"] == 100.5
    assert int(candles[0]["timestamp"].timestamp() * 1000) == ts1


def test_fetch_candles_includes_all_confirmed_rows():
    ts1 = 1_700_000_000_000
    ts2 = 1_700_014_400_000
    fetcher = _StubFetcher([{"data": [_row(ts2, "1"), _row(ts1, "1")]}])
    candles = fetcher.fetch_candles("BTC-USDT", "4H")
    assert len(candles) == 2


def test_fetch_candles_tolerates_short_rows_without_confirm_field():
    """Rows with fewer than 9 fields (no confirm column) are treated as confirmed."""
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


# --- candle parsing ---

def test_fetch_candles_parses_fields_correctly():
    ts_ms = 1_714_608_000_000
    row = [str(ts_ms), "50000", "51000", "49000", "50500", "3.5", "0", "0", "1"]
    fetcher = _StubFetcher([{"data": [row]}])
    candles = fetcher.fetch_candles("BTC-USDT", "1H")
    c = candles[0]
    assert c["open"] == 50000.0
    assert c["high"] == 51000.0
    assert c["low"] == 49000.0
    assert c["close"] == 50500.0
    assert c["volume"] == 3.5
    expected_ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    assert c["timestamp"] == expected_ts


def test_fetch_candles_sorts_ascending():
    ts_a = 1_700_000_000_000
    ts_b = 1_700_014_400_000
    fetcher = _StubFetcher([{"data": [_row(ts_b), _row(ts_a)]}])
    candles = fetcher.fetch_candles("BTC-USDT", "4H")
    assert candles[0]["timestamp"] < candles[1]["timestamp"]


def test_fetch_candles_returns_empty_on_missing_data_key():
    fetcher = _StubFetcher([{"msg": "ok"}])
    candles = fetcher.fetch_candles("BTC-USDT", "4H")
    assert candles == []


def test_fetch_candles_returns_empty_on_null_data():
    fetcher = _StubFetcher([{"data": None}])
    candles = fetcher.fetch_candles("BTC-USDT", "4H")
    assert candles == []
