from __future__ import annotations


class ExchangeError(Exception):
    """Base class for all exchange adapter errors."""


class UnsupportedSymbol(ExchangeError):
    """Symbol is not in the supported internal-to-exchange symbol map."""


class UnsupportedMarketType(ExchangeError):
    """market_type is not one of the supported values (spot, linear)."""


class UnsupportedTimeframe(ExchangeError):
    """Timeframe string has no mapping to an exchange-native interval."""


class ExchangeResponseError(ExchangeError):
    """Bybit returned retCode != 0 and it is not a special-cased error code."""

    def __init__(self, ret_code: int, ret_msg: str) -> None:
        self.ret_code = ret_code
        self.ret_msg = ret_msg
        super().__init__(f"Bybit error {ret_code}: {ret_msg}")


class ExchangeRateLimited(ExchangeError):
    """Bybit returned a rate-limit response (retCode 10006 or HTTP 429)."""


class MarketDataUnavailable(ExchangeError):
    """Market data could not be fetched (network error, timeout, empty response)."""


class InstrumentNotTradable(ExchangeError):
    """Instrument exists on the exchange but its status is not 'Trading'."""


class LiquidityCheckFailed(ExchangeError):
    """Orderbook failed the spread or depth guard. Always fail-closed."""


class StaleMarketData(ExchangeError):
    """Market data timestamp exceeds the configured freshness threshold."""
