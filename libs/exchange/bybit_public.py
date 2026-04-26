from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import httpx

from libs.exchange.errors import (
    ExchangeRateLimited,
    ExchangeResponseError,
    InstrumentNotTradable,
    MarketDataUnavailable,
    UnsupportedMarketType,
    UnsupportedTimeframe,
)
from libs.exchange.models import (
    InstrumentRules,
    OrderbookLevel,
    OrderbookSnapshot,
    TickerSnapshot,
)
from libs.exchange.symbols import to_exchange_symbol

LOGGER = logging.getLogger(__name__)

_SUPPORTED_MARKET_TYPES: frozenset[str] = frozenset({"spot", "linear"})

# Bybit V5 retCode for rate limiting.
_BYBIT_RATE_LIMIT_CODE: int = 10006

# Internal timeframe -> Bybit interval string.
# Only entries in this map are accepted; unknown timeframes raise UnsupportedTimeframe.
_TIMEFRAME_MAP: dict[str, str] = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "4h": "240",
    "1d": "D",
}


def _utc_datetime_from_ms(value: str | int) -> datetime:
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)


def _raise_for_bybit_error(payload: dict[str, Any]) -> None:
    """Inspect a Bybit V5 response and raise a typed error if retCode != 0."""
    ret_code = int(payload.get("retCode", 0))
    if ret_code == 0:
        return
    ret_msg = str(payload.get("retMsg", ""))
    if ret_code == _BYBIT_RATE_LIMIT_CODE:
        raise ExchangeRateLimited(
            f"Bybit rate limited (retCode {ret_code}): {ret_msg}"
        )
    raise ExchangeResponseError(ret_code=ret_code, ret_msg=ret_msg)


class BybitMarketDataFetcher:
    """Public (no-auth) Bybit V5 market data adapter.

    Satisfies the MarketFetcher Protocol from reconcile_scheduler.py:
        fetch_candles(symbol, timeframe, *, limit) -> list[dict]

    Also provides async methods for instrument rules, ticker, and orderbook.
    These are read-only, public Bybit endpoints - no API key required.

    Symbol translation is centralised in libs/exchange/symbols.py.
    market_type must be supplied by the caller; there is no hidden default.

    Scope: Stage 53-A only.
    No orders. No cancels. No balances. No positions. No authentication.
    """

    BASE_URL: str = "https://api.bybit.com"

    def __init__(
        self,
        market_type: str,
        base_url: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        if market_type not in _SUPPORTED_MARKET_TYPES:
            raise UnsupportedMarketType(
                f"market_type must be one of {sorted(_SUPPORTED_MARKET_TYPES)!r}, "
                f"got {market_type!r}"
            )
        self.market_type = market_type
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Sync interface - satisfies MarketFetcher Protocol
    # ------------------------------------------------------------------

    def _sync_get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        """Synchronous HTTP GET. Wraps transport errors in MarketDataUnavailable.

        Note: ExchangeResponseError / ExchangeRateLimited are raised by callers after
        inspecting the returned payload. They are never raised inside this method.
        """
        url = f"{self.base_url}{path}?{urlencode(params)}"
        try:
            response = httpx.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": "trading-system"},
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise MarketDataUnavailable(
                f"Bybit request failed [{path}]: {exc}"
            ) from exc

    def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int = 100,
    ) -> list[dict]:
        """Fetch OHLCV candles from Bybit public kline endpoint.

        Args:
            symbol: Internal format BTC-USDT. Translated to BTCUSDT internally.
            timeframe: Internal timeframe e.g. "1m". Mapped to Bybit interval.
            limit: Number of candles.

        Returns:
            Candles sorted ascending by timestamp, matching MarketFetcher Protocol shape:
            {timestamp, open, high, low, close, volume, session, body}
            Numeric fields are float (Protocol compatibility with reconcile_scheduler).

        Raises:
            UnsupportedSymbol: Symbol not in the map.
            UnsupportedTimeframe: Timeframe not in the map.
            ExchangeResponseError: Bybit retCode != 0.
            ExchangeRateLimited: Bybit retCode == 10006.
            MarketDataUnavailable: Network or timeout error.
        """
        if timeframe not in _TIMEFRAME_MAP:
            raise UnsupportedTimeframe(
                f"Timeframe {timeframe!r} has no Bybit mapping. "
                f"Supported: {sorted(_TIMEFRAME_MAP)}"
            )

        exchange_symbol = to_exchange_symbol(symbol)
        bybit_interval = _TIMEFRAME_MAP[timeframe]

        payload = self._sync_get(
            "/v5/market/kline",
            {
                "category": self.market_type,
                "symbol": exchange_symbol,
                "interval": bybit_interval,
                "limit": str(limit),
            },
        )
        _raise_for_bybit_error(payload)

        # Bybit returns list[0] = newest candle.
        # Column order: [startTime_ms, open, high, low, close, volume, turnover]
        rows = (payload.get("result") or {}).get("list") or []

        candles: list[dict] = []
        for row in rows:
            candle = {
                "timestamp": _utc_datetime_from_ms(row[0]),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "session": "unknown",
            }
            candle["body"] = abs(candle["close"] - candle["open"])
            candles.append(candle)

        candles.sort(key=lambda c: c["timestamp"])
        return candles

    # ------------------------------------------------------------------
    # Async interface - Stage 53-B+ preparation
    # ------------------------------------------------------------------

    async def _async_get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        """Asynchronous HTTP GET. Wraps transport errors in MarketDataUnavailable."""
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers={"User-Agent": "trading-system"},
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            raise MarketDataUnavailable(
                f"Bybit async request failed [{path}]: {exc}"
            ) from exc

    async def fetch_instrument_rules(self, symbol: str) -> InstrumentRules:
        """Fetch and normalize instrument rules for a symbol.

        All numeric fields in the returned InstrumentRules use Decimal.
        Both internal and exchange symbol formats are included.

        Raises:
            UnsupportedSymbol, InstrumentNotTradable, ExchangeResponseError,
            ExchangeRateLimited, MarketDataUnavailable
        """
        exchange_symbol = to_exchange_symbol(symbol)
        payload = await self._async_get(
            "/v5/market/instruments-info",
            {"category": self.market_type, "symbol": exchange_symbol},
        )
        _raise_for_bybit_error(payload)

        items = (payload.get("result") or {}).get("list") or []
        if not items:
            raise MarketDataUnavailable(
                f"No instrument info returned for {symbol} ({exchange_symbol})"
            )

        item = items[0]
        status = item.get("status", "")
        if status != "Trading":
            raise InstrumentNotTradable(
                f"Instrument {symbol} has status {status!r}, not 'Trading'"
            )

        lot = item.get("lotSizeFilter") or {}
        price_filter = item.get("priceFilter") or {}

        return InstrumentRules(
            symbol_internal=symbol,
            symbol_exchange=exchange_symbol,
            exchange="bybit",
            market_type=self.market_type,
            price_tick=Decimal(str(price_filter.get("tickSize", "0"))),
            qty_step=Decimal(str(lot.get("qtyStep", "0"))),
            min_qty=Decimal(str(lot.get("minOrderQty", "0"))),
            max_qty=Decimal(str(lot.get("maxOrderQty", "0"))),
            min_notional=Decimal(str(lot.get("minNotionalValue", "0"))),
            status=status,
        )

    async def fetch_ticker(self, symbol: str) -> TickerSnapshot:
        """Fetch latest ticker (last price, best bid, best ask) for a symbol.

        All prices in the returned TickerSnapshot use Decimal.

        Raises:
            UnsupportedSymbol, ExchangeResponseError, ExchangeRateLimited,
            MarketDataUnavailable
        """
        exchange_symbol = to_exchange_symbol(symbol)
        payload = await self._async_get(
            "/v5/market/tickers",
            {"category": self.market_type, "symbol": exchange_symbol},
        )
        _raise_for_bybit_error(payload)

        items = (payload.get("result") or {}).get("list") or []
        if not items:
            raise MarketDataUnavailable(
                f"No ticker data returned for {symbol} ({exchange_symbol})"
            )

        item = items[0]
        return TickerSnapshot(
            symbol_internal=symbol,
            symbol_exchange=exchange_symbol,
            exchange="bybit",
            market_type=self.market_type,
            last_price=Decimal(str(item.get("lastPrice", "0"))),
            bid=Decimal(str(item.get("bid1Price", "0"))),
            ask=Decimal(str(item.get("ask1Price", "0"))),
            timestamp_ms=int(item.get("ts", 0)),
        )

    async def fetch_orderbook(self, symbol: str, *, depth: int = 5) -> OrderbookSnapshot:
        """Fetch top-of-book snapshot for a symbol.

        bids are sorted descending (best bid first).
        asks are sorted ascending (best ask first).
        All prices and quantities use Decimal.

        Raises:
            UnsupportedSymbol, ExchangeResponseError, ExchangeRateLimited,
            MarketDataUnavailable
        """
        exchange_symbol = to_exchange_symbol(symbol)
        payload = await self._async_get(
            "/v5/market/orderbook",
            {
                "category": self.market_type,
                "symbol": exchange_symbol,
                "limit": str(depth),
            },
        )
        _raise_for_bybit_error(payload)

        result = payload.get("result") or {}
        raw_bids = result.get("b") or []
        raw_asks = result.get("a") or []
        timestamp_ms = int(result.get("ts", 0))

        bids = tuple(
            sorted(
                (OrderbookLevel(price=Decimal(str(lv[0])), qty=Decimal(str(lv[1])))
                 for lv in raw_bids),
                key=lambda lv: lv.price,
                reverse=True,
            )
        )
        asks = tuple(
            sorted(
                (OrderbookLevel(price=Decimal(str(lv[0])), qty=Decimal(str(lv[1])))
                 for lv in raw_asks),
                key=lambda lv: lv.price,
            )
        )

        return OrderbookSnapshot(
            symbol_internal=symbol,
            symbol_exchange=exchange_symbol,
            exchange="bybit",
            market_type=self.market_type,
            bids=bids,
            asks=asks,
            timestamp_ms=timestamp_ms,
        )
