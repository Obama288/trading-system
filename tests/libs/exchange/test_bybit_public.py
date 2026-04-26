"""
Mocked unit tests for Stage 53-A: Bybit public market data adapter.

All HTTP is mocked. No live network calls are made.
No API keys, private endpoints, orders, balances, or positions are tested here.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from libs.exchange.bybit_public import BybitMarketDataFetcher
from libs.exchange.errors import (
    ExchangeRateLimited,
    ExchangeResponseError,
    LiquidityCheckFailed,
    MarketDataUnavailable,
    UnsupportedMarketType,
    UnsupportedSymbol,
    UnsupportedTimeframe,
)
from libs.exchange.liquidity_guard import check_liquidity
from libs.exchange.models import OrderbookLevel, OrderbookSnapshot
from libs.exchange.symbols import to_exchange_symbol, to_internal_symbol


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

class _FakeSyncResponse:
    """Minimal httpx sync response stand-in."""

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        pass


class _FakeAsyncClient:
    """Minimal httpx.AsyncClient stand-in for async tests."""

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def get(self, url: str, **kwargs: object) -> _FakeSyncResponse:
        return _FakeSyncResponse(self._payload)


def _fetcher(market_type: str = "linear") -> BybitMarketDataFetcher:
    return BybitMarketDataFetcher(market_type=market_type)


def _patch_sync(payload: dict):
    """Patch httpx.get inside bybit_public to return the given payload."""
    mock_httpx = MagicMock()
    mock_httpx.get.return_value = _FakeSyncResponse(payload)
    return patch("libs.exchange.bybit_public.httpx", mock_httpx), mock_httpx


def _patch_async(payload: dict):
    """Patch httpx.AsyncClient inside bybit_public to return the given payload."""
    mock_httpx = MagicMock()
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(payload)
    return patch("libs.exchange.bybit_public.httpx", mock_httpx), mock_httpx


# ---------------------------------------------------------------------------
# Sample payloads
# ---------------------------------------------------------------------------

_KLINE_PAYLOAD = {
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "symbol": "BTCUSDT",
        "category": "linear",
        "list": [
            ["1700000060000", "35100.0", "35200.0", "35000.0", "35050.0", "10.5", "368025.0"],
            ["1700000000000", "35000.0", "35150.0", "34900.0", "35100.0", "12.0", "420000.0"],
        ],
    },
}

_INSTRUMENT_PAYLOAD = {
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "list": [
            {
                "symbol": "BTCUSDT",
                "status": "Trading",
                "lotSizeFilter": {
                    "minOrderQty": "0.001",
                    "maxOrderQty": "100",
                    "qtyStep": "0.001",
                    "minNotionalValue": "5",
                },
                "priceFilter": {
                    "tickSize": "0.1",
                },
            }
        ]
    },
}

_ORDERBOOK_PAYLOAD = {
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "s": "BTCUSDT",
        "b": [["35000.0", "1.5"], ["34990.0", "2.0"]],
        "a": [["35010.0", "1.0"], ["35020.0", "0.5"]],
        "ts": 1700000000000,
    },
}

_TICKER_PAYLOAD = {
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "list": [
            {
                "symbol": "BTCUSDT",
                "lastPrice": "35005.0",
                "bid1Price": "35000.0",
                "ask1Price": "35010.0",
                "ts": "1700000000000",
            }
        ]
    },
}


# ===========================================================================
# 1. Symbol mapping
# ===========================================================================

def test_to_exchange_symbol_btc():
    assert to_exchange_symbol("BTC-USDT") == "BTCUSDT"


def test_to_exchange_symbol_eth():
    assert to_exchange_symbol("ETH-USDT") == "ETHUSDT"


def test_to_internal_symbol_btc():
    assert to_internal_symbol("BTCUSDT") == "BTC-USDT"


def test_to_internal_symbol_eth():
    assert to_internal_symbol("ETHUSDT") == "ETH-USDT"


def test_unsupported_internal_symbol_raises():
    with pytest.raises(UnsupportedSymbol):
        to_exchange_symbol("DOGE-USDT")


def test_unsupported_exchange_symbol_raises():
    with pytest.raises(UnsupportedSymbol):
        to_internal_symbol("DOGEUSDT")


# ===========================================================================
# 2. market_type validation
# ===========================================================================

def test_unsupported_market_type_raises():
    with pytest.raises(UnsupportedMarketType):
        BybitMarketDataFetcher(market_type="inverse")


def test_empty_market_type_raises():
    with pytest.raises(UnsupportedMarketType):
        BybitMarketDataFetcher(market_type="")


def test_linear_market_type_accepted():
    f = BybitMarketDataFetcher(market_type="linear")
    assert f.market_type == "linear"


def test_spot_market_type_accepted():
    f = BybitMarketDataFetcher(market_type="spot")
    assert f.market_type == "spot"


# ===========================================================================
# 3. fetch_candles - sync, MarketFetcher Protocol
# ===========================================================================

def test_fetch_candles_returns_sorted_ascending():
    patcher, _ = _patch_sync(_KLINE_PAYLOAD)
    with patcher:
        candles = _fetcher().fetch_candles("BTC-USDT", "1m", limit=2)

    assert len(candles) == 2
    assert candles[0]["timestamp"] < candles[1]["timestamp"]


def test_fetch_candles_output_shape():
    patcher, _ = _patch_sync(_KLINE_PAYLOAD)
    with patcher:
        candles = _fetcher().fetch_candles("BTC-USDT", "1m", limit=2)

    c = candles[0]
    for key in ("timestamp", "open", "high", "low", "close", "volume", "session", "body"):
        assert key in c, f"Missing key: {key}"
    assert c["session"] == "unknown"
    assert isinstance(c["open"], float)
    assert isinstance(c["close"], float)


def test_fetch_candles_body_equals_abs_close_minus_open():
    patcher, _ = _patch_sync(_KLINE_PAYLOAD)
    with patcher:
        candles = _fetcher().fetch_candles("BTC-USDT", "1m", limit=2)

    for c in candles:
        assert abs(c["close"] - c["open"]) == pytest.approx(c["body"])


def test_fetch_candles_unsupported_timeframe_raises():
    f = _fetcher()
    with pytest.raises(UnsupportedTimeframe):
        f.fetch_candles("BTC-USDT", "3m", limit=2)


def test_fetch_candles_sends_exchange_symbol_not_internal():
    """BTC-USDT must be translated to BTCUSDT before the HTTP request."""
    patcher, mock_httpx = _patch_sync(_KLINE_PAYLOAD)
    with patcher:
        _fetcher().fetch_candles("BTC-USDT", "1m", limit=2)

    url_called = mock_httpx.get.call_args[0][0]
    assert "BTCUSDT" in url_called
    assert "BTC-USDT" not in url_called


def test_fetch_candles_unsupported_symbol_raises():
    f = _fetcher()
    with pytest.raises(UnsupportedSymbol):
        f.fetch_candles("DOGE-USDT", "1m", limit=2)


# ===========================================================================
# 4. No private/auth headers
# ===========================================================================

def test_fetch_candles_no_auth_headers_in_sync_request():
    """Public adapter must not send any authentication headers."""
    patcher, mock_httpx = _patch_sync(_KLINE_PAYLOAD)
    with patcher:
        _fetcher().fetch_candles("BTC-USDT", "1m", limit=2)

    headers = mock_httpx.get.call_args[1].get("headers", {})
    for forbidden in ("X-BAPI-API-KEY", "Authorization", "X-Internal-Token", "X-Admin-Token"):
        assert forbidden not in headers, f"Auth header found: {forbidden}"


@pytest.mark.asyncio
async def test_fetch_instrument_rules_no_auth_headers_in_async_request():
    """Async public methods must not send any authentication headers."""
    patcher, mock_httpx = _patch_async(_INSTRUMENT_PAYLOAD)
    captured_kwargs: dict = {}

    class _CapturingClient(_FakeAsyncClient):
        async def get(self, url: str, **kwargs: object) -> _FakeSyncResponse:
            captured_kwargs.update(kwargs)
            return await super().get(url, **kwargs)

    mock_httpx.AsyncClient.return_value = _CapturingClient(_INSTRUMENT_PAYLOAD)
    with patcher:
        await _fetcher().fetch_instrument_rules("BTC-USDT")

    headers = captured_kwargs.get("headers", {})
    for forbidden in ("X-BAPI-API-KEY", "Authorization", "X-Internal-Token", "X-Admin-Token"):
        assert forbidden not in headers, f"Auth header found: {forbidden}"


# ===========================================================================
# 5. fetch_instrument_rules - Decimal normalization
# ===========================================================================

@pytest.mark.asyncio
async def test_fetch_instrument_rules_all_numeric_fields_are_decimal():
    patcher, mock_httpx = _patch_async(_INSTRUMENT_PAYLOAD)
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(_INSTRUMENT_PAYLOAD)
    with patcher:
        rules = await _fetcher().fetch_instrument_rules("BTC-USDT")

    for field_name in ("price_tick", "qty_step", "min_qty", "max_qty", "min_notional"):
        value = getattr(rules, field_name)
        assert isinstance(value, Decimal), f"{field_name} is {type(value)}, expected Decimal"


@pytest.mark.asyncio
async def test_fetch_instrument_rules_correct_values():
    patcher, mock_httpx = _patch_async(_INSTRUMENT_PAYLOAD)
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(_INSTRUMENT_PAYLOAD)
    with patcher:
        rules = await _fetcher().fetch_instrument_rules("BTC-USDT")

    assert rules.price_tick == Decimal("0.1")
    assert rules.qty_step == Decimal("0.001")
    assert rules.min_qty == Decimal("0.001")
    assert rules.max_qty == Decimal("100")
    assert rules.min_notional == Decimal("5")
    assert rules.status == "Trading"


@pytest.mark.asyncio
async def test_fetch_instrument_rules_contains_both_symbol_formats():
    """Normalized model must include both internal BTC-USDT and exchange BTCUSDT."""
    patcher, mock_httpx = _patch_async(_INSTRUMENT_PAYLOAD)
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(_INSTRUMENT_PAYLOAD)
    with patcher:
        rules = await _fetcher().fetch_instrument_rules("BTC-USDT")

    assert rules.symbol_internal == "BTC-USDT"
    assert rules.symbol_exchange == "BTCUSDT"
    assert rules.exchange == "bybit"
    assert rules.market_type == "linear"


# ===========================================================================
# 6. fetch_orderbook - Decimal normalization + both symbol formats
# ===========================================================================

@pytest.mark.asyncio
async def test_fetch_orderbook_levels_are_decimal():
    patcher, mock_httpx = _patch_async(_ORDERBOOK_PAYLOAD)
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(_ORDERBOOK_PAYLOAD)
    with patcher:
        snap = await _fetcher().fetch_orderbook("BTC-USDT", depth=5)

    assert isinstance(snap.best_bid, Decimal)
    assert isinstance(snap.best_ask, Decimal)
    assert snap.best_bid == Decimal("35000.0")
    assert snap.best_ask == Decimal("35010.0")


@pytest.mark.asyncio
async def test_fetch_orderbook_contains_both_symbol_formats():
    patcher, mock_httpx = _patch_async(_ORDERBOOK_PAYLOAD)
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(_ORDERBOOK_PAYLOAD)
    with patcher:
        snap = await _fetcher().fetch_orderbook("BTC-USDT", depth=5)

    assert snap.symbol_internal == "BTC-USDT"
    assert snap.symbol_exchange == "BTCUSDT"


@pytest.mark.asyncio
async def test_fetch_orderbook_bids_sorted_descending():
    patcher, mock_httpx = _patch_async(_ORDERBOOK_PAYLOAD)
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(_ORDERBOOK_PAYLOAD)
    with patcher:
        snap = await _fetcher().fetch_orderbook("BTC-USDT", depth=5)

    bid_prices = [lv.price for lv in snap.bids]
    assert bid_prices == sorted(bid_prices, reverse=True)


@pytest.mark.asyncio
async def test_fetch_orderbook_asks_sorted_ascending():
    patcher, mock_httpx = _patch_async(_ORDERBOOK_PAYLOAD)
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(_ORDERBOOK_PAYLOAD)
    with patcher:
        snap = await _fetcher().fetch_orderbook("BTC-USDT", depth=5)

    ask_prices = [lv.price for lv in snap.asks]
    assert ask_prices == sorted(ask_prices)


# ===========================================================================
# 7. Liquidity guard
# ===========================================================================

def _make_snapshot(
    bids: list[tuple[str, str]],
    asks: list[tuple[str, str]],
) -> OrderbookSnapshot:
    return OrderbookSnapshot(
        symbol_internal="BTC-USDT",
        symbol_exchange="BTCUSDT",
        exchange="bybit",
        market_type="linear",
        bids=tuple(
            OrderbookLevel(price=Decimal(p), qty=Decimal(q)) for p, q in bids
        ),
        asks=tuple(
            OrderbookLevel(price=Decimal(p), qty=Decimal(q)) for p, q in asks
        ),
        timestamp_ms=1700000000000,
    )


def test_liquidity_guard_empty_bids_fails_closed():
    snap = _make_snapshot(bids=[], asks=[("35010", "1")])
    with pytest.raises(LiquidityCheckFailed):
        check_liquidity(snap)


def test_liquidity_guard_empty_asks_fails_closed():
    snap = _make_snapshot(bids=[("35000", "1")], asks=[])
    with pytest.raises(LiquidityCheckFailed):
        check_liquidity(snap)


def test_liquidity_guard_both_sides_empty_fails_closed():
    snap = _make_snapshot(bids=[], asks=[])
    with pytest.raises(LiquidityCheckFailed):
        check_liquidity(snap)


def test_liquidity_guard_spread_calculation_within_limit():
    """bid=35000, ask=35007 -> ~2 bps - well under 50 bps default."""
    snap = _make_snapshot(bids=[("35000", "1")], asks=[("35007", "1")])
    check_liquidity(snap)  # must not raise


def test_liquidity_guard_spread_too_wide_rejected():
    """bid=35000, ask=35200 -> ~57 bps - exceeds 50 bps default."""
    snap = _make_snapshot(bids=[("35000", "1")], asks=[("35200", "1")])
    with pytest.raises(LiquidityCheckFailed, match="bps"):
        check_liquidity(snap)


def test_liquidity_guard_custom_threshold():
    """Custom 5 bps threshold; bid=35000, ask=35007 (~2 bps) should still pass."""
    snap = _make_snapshot(bids=[("35000", "1")], asks=[("35007", "1")])
    check_liquidity(snap, max_spread_bps=Decimal("5"))  # ~2 bps < 5 bps - passes


def test_liquidity_guard_crossed_orderbook_rejected():
    """bid > ask is a crossed book - must always fail."""
    snap = _make_snapshot(bids=[("35100", "1")], asks=[("35000", "1")])
    with pytest.raises(LiquidityCheckFailed):
        check_liquidity(snap)


def test_liquidity_guard_min_levels_not_met():
    snap = _make_snapshot(bids=[("35000", "1")], asks=[("35010", "1")])
    with pytest.raises(LiquidityCheckFailed):
        check_liquidity(snap, min_levels=2)


def test_liquidity_guard_valid_orderbook_passes():
    snap = _make_snapshot(
        bids=[("35000", "1"), ("34990", "2")],
        asks=[("35005", "1"), ("35010", "0.5")],
    )
    check_liquidity(snap, min_levels=2)  # must not raise


# ===========================================================================
# 8. Exchange error codes - sync (fetch_candles path)
# ===========================================================================

def test_bybit_ret_code_nonzero_raises_exchange_response_error():
    patcher, mock_httpx = _patch_sync({"retCode": 10001, "retMsg": "invalid symbol"})
    with patcher:
        with pytest.raises(ExchangeResponseError) as exc_info:
            _fetcher().fetch_candles("BTC-USDT", "1m", limit=1)

    assert exc_info.value.ret_code == 10001
    assert "invalid symbol" in str(exc_info.value)


def test_bybit_rate_limit_code_raises_rate_limited_sync():
    patcher, mock_httpx = _patch_sync({"retCode": 10006, "retMsg": "too many requests"})
    with patcher:
        with pytest.raises(ExchangeRateLimited):
            _fetcher().fetch_candles("BTC-USDT", "1m", limit=1)


# ===========================================================================
# 9. Exchange error codes - async (fetch_instrument_rules path)
# ===========================================================================

@pytest.mark.asyncio
async def test_bybit_ret_code_nonzero_raises_exchange_response_error_async():
    patcher, mock_httpx = _patch_async({"retCode": 10001, "retMsg": "bad request"})
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient({"retCode": 10001, "retMsg": "bad request"})
    with patcher:
        with pytest.raises(ExchangeResponseError) as exc_info:
            await _fetcher().fetch_instrument_rules("BTC-USDT")

    assert exc_info.value.ret_code == 10001


@pytest.mark.asyncio
async def test_bybit_rate_limit_code_raises_rate_limited_async():
    payload = {"retCode": 10006, "retMsg": "too many requests"}
    patcher, mock_httpx = _patch_async(payload)
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(payload)
    with patcher:
        with pytest.raises(ExchangeRateLimited):
            await _fetcher().fetch_instrument_rules("BTC-USDT")


# ===========================================================================
# 10. Ticker - both symbol formats
# ===========================================================================

@pytest.mark.asyncio
async def test_fetch_ticker_contains_both_symbol_formats():
    patcher, mock_httpx = _patch_async(_TICKER_PAYLOAD)
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(_TICKER_PAYLOAD)
    with patcher:
        ticker = await _fetcher().fetch_ticker("BTC-USDT")

    assert ticker.symbol_internal == "BTC-USDT"
    assert ticker.symbol_exchange == "BTCUSDT"
    assert isinstance(ticker.last_price, Decimal)
    assert isinstance(ticker.bid, Decimal)
    assert isinstance(ticker.ask, Decimal)
