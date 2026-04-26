from __future__ import annotations

from decimal import Decimal

from libs.exchange.errors import LiquidityCheckFailed
from libs.exchange.models import OrderbookSnapshot

_DEFAULT_MAX_SPREAD_BPS: Decimal = Decimal("50")
_DEFAULT_MIN_LEVELS: int = 1


def check_liquidity(
    snapshot: OrderbookSnapshot,
    *,
    max_spread_bps: Decimal = _DEFAULT_MAX_SPREAD_BPS,
    min_levels: int = _DEFAULT_MIN_LEVELS,
) -> None:
    """Validate orderbook liquidity. Raises LiquidityCheckFailed on any guard failure.

    All checks are fail-closed - empty, crossed, or wide-spread orderbooks always fail.

    Args:
        snapshot: Orderbook snapshot to validate.
        max_spread_bps: Maximum allowed bid-ask spread in basis points.
        min_levels: Minimum required price levels on each side.

    Raises:
        LiquidityCheckFailed: On any failed guard. The message describes which check failed.
    """
    if not snapshot.bids or not snapshot.asks:
        raise LiquidityCheckFailed(
            f"Orderbook is empty for {snapshot.symbol_internal}: "
            f"{len(snapshot.bids)} bids, {len(snapshot.asks)} asks"
        )

    if len(snapshot.bids) < min_levels or len(snapshot.asks) < min_levels:
        raise LiquidityCheckFailed(
            f"Orderbook depth below minimum ({min_levels}) for {snapshot.symbol_internal}: "
            f"{len(snapshot.bids)} bids, {len(snapshot.asks)} asks"
        )

    bid = snapshot.best_bid
    ask = snapshot.best_ask

    if bid is None or bid <= 0:
        raise LiquidityCheckFailed(
            f"Invalid bid price for {snapshot.symbol_internal}: {bid}"
        )
    if ask is None or ask <= 0:
        raise LiquidityCheckFailed(
            f"Invalid ask price for {snapshot.symbol_internal}: {ask}"
        )
    if ask < bid:
        raise LiquidityCheckFailed(
            f"Crossed orderbook for {snapshot.symbol_internal}: bid={bid} ask={ask}"
        )

    mid = (bid + ask) / Decimal("2")
    spread_bps = ((ask - bid) / mid) * Decimal("10000")
    if spread_bps > max_spread_bps:
        raise LiquidityCheckFailed(
            f"Spread {spread_bps:.2f} bps exceeds maximum {max_spread_bps} bps "
            f"for {snapshot.symbol_internal}"
        )
