from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class InstrumentRules:
    """Normalized instrument rules fetched from the exchange.

    All numeric fields use Decimal. No floats.
    Both internal (BTC-USDT) and exchange (BTCUSDT) symbols are stored
    so callers never need to re-translate.
    """

    symbol_internal: str    # BTC-USDT
    symbol_exchange: str    # BTCUSDT
    exchange: str           # "bybit"
    market_type: str        # "spot" or "linear"
    price_tick: Decimal     # minimum price increment (tickSize)
    qty_step: Decimal       # minimum quantity increment (qtyStep)
    min_qty: Decimal        # minimum order quantity (minOrderQty)
    max_qty: Decimal        # maximum order quantity (maxOrderQty)
    min_notional: Decimal   # minimum order value in quote currency (minNotionalValue)
    status: str             # "Trading" or other exchange-reported status


@dataclass(frozen=True)
class OrderbookLevel:
    """A single price level in an orderbook. Both fields use Decimal."""

    price: Decimal
    qty: Decimal


@dataclass(frozen=True)
class OrderbookSnapshot:
    """Normalized top-of-book snapshot.

    bids are sorted descending (best bid first).
    asks are sorted ascending (best ask first).
    All prices and quantities use Decimal.
    """

    symbol_internal: str
    symbol_exchange: str
    exchange: str
    market_type: str
    bids: tuple[OrderbookLevel, ...]
    asks: tuple[OrderbookLevel, ...]
    timestamp_ms: int

    @property
    def best_bid(self) -> Decimal | None:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> Decimal | None:
        return self.asks[0].price if self.asks else None


@dataclass(frozen=True)
class TickerSnapshot:
    """Normalized ticker snapshot. All prices use Decimal."""

    symbol_internal: str
    symbol_exchange: str
    exchange: str
    market_type: str
    last_price: Decimal
    bid: Decimal
    ask: Decimal
    timestamp_ms: int
