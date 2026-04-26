from __future__ import annotations

from libs.exchange.errors import UnsupportedSymbol

# Explicit symbol map - no implicit string.replace() anywhere in the codebase.
# Translation happens only here and inside the exchange adapter.
# Add new trading pairs to this map; unknown symbols are rejected explicitly.
_INTERNAL_TO_EXCHANGE: dict[str, str] = {
    "BTC-USDT": "BTCUSDT",
    "ETH-USDT": "ETHUSDT",
    "SOL-USDT": "SOLUSDT",
    "BNB-USDT": "BNBUSDT",
    "XRP-USDT": "XRPUSDT",
}

_EXCHANGE_TO_INTERNAL: dict[str, str] = {v: k for k, v in _INTERNAL_TO_EXCHANGE.items()}


def to_exchange_symbol(internal: str) -> str:
    """Translate internal BTC-USDT format to exchange BTCUSDT format.

    Raises UnsupportedSymbol for any symbol not explicitly listed in the map.
    """
    try:
        return _INTERNAL_TO_EXCHANGE[internal]
    except KeyError:
        raise UnsupportedSymbol(
            f"Symbol {internal!r} is not in the supported symbol map. "
            f"Supported: {sorted(_INTERNAL_TO_EXCHANGE)}"
        )


def to_internal_symbol(exchange: str) -> str:
    """Translate exchange BTCUSDT format back to internal BTC-USDT format.

    Raises UnsupportedSymbol for any exchange symbol not in the reverse map.
    """
    try:
        return _EXCHANGE_TO_INTERNAL[exchange]
    except KeyError:
        raise UnsupportedSymbol(
            f"Exchange symbol {exchange!r} is not in the supported symbol map. "
            f"Supported: {sorted(_EXCHANGE_TO_INTERNAL)}"
        )


def supported_internal_symbols() -> list[str]:
    """Return a sorted list of all supported internal-format symbols."""
    return sorted(_INTERNAL_TO_EXCHANGE)
