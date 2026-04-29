from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ServerTime:
    """Bybit server time normalized from the V5 market time endpoint."""

    exchange: str
    time_second: int
    time_nano: int

    @property
    def timestamp_ms(self) -> int:
        return self.time_nano // 1_000_000

    @property
    def as_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp_ms / 1000, tz=timezone.utc)


@dataclass(frozen=True)
class WalletCoinBalance:
    """Read-only Bybit wallet balance for one coin.

    Numeric values are intentionally hidden from repr/model_dump because balances
    are sensitive external account observations.
    """

    coin: str
    wallet_balance: Decimal
    equity: Decimal
    available_to_withdraw: Decimal | None = None

    def __repr__(self) -> str:
        return f"WalletCoinBalance(coin={self.coin!r}, balances='[REDACTED]')"

    def model_dump(self) -> dict[str, Any]:
        return {"coin": self.coin, "balances": "[REDACTED]"}


@dataclass(frozen=True)
class WalletBalance:
    """Read-only Bybit wallet balance snapshot.

    This model is an external observation only. It is not internal trading
    authority and must not be used as a source of truth for execution state.
    """

    exchange: str
    account_type: str
    total_equity: Decimal
    total_wallet_balance: Decimal
    coins: tuple[WalletCoinBalance, ...]

    def __repr__(self) -> str:
        return (
            "WalletBalance("
            f"exchange={self.exchange!r}, account_type={self.account_type!r}, "
            "balances='[REDACTED]', "
            f"coin_count={len(self.coins)})"
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "exchange": self.exchange,
            "account_type": self.account_type,
            "balances": "[REDACTED]",
            "coin_count": len(self.coins),
            "coins": [coin.model_dump() for coin in self.coins],
        }


@dataclass(frozen=True)
class OpenPosition:
    """External read-only Bybit position observation.

    This is not internal trading authority and must not be mapped into
    position_manager domain state.
    """

    symbol: str
    side: str
    size: Decimal
    avg_price: Decimal
    mark_price: Decimal
    position_value: Decimal
    unrealised_pnl: Decimal
    position_im: Decimal
    position_mm: Decimal
    leverage: Decimal

    def __repr__(self) -> str:
        return "OpenPosition(symbol='[REDACTED]', values='[REDACTED]')"

    def model_dump(self) -> dict[str, Any]:
        return {
            "symbol": "[REDACTED]",
            "values": "[REDACTED]",
        }


@dataclass(frozen=True)
class OpenPositions:
    """External read-only Bybit open positions snapshot.

    Positions are external exchange observations only. They are not internal
    authoritative position state and must not drive live execution/reconcile.
    """

    exchange: str
    category: str
    positions: tuple[OpenPosition, ...]

    def __repr__(self) -> str:
        return (
            "OpenPositions("
            f"exchange={self.exchange!r}, category={self.category!r}, "
            "positions='[REDACTED]', "
            f"position_count={len(self.positions)})"
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "exchange": self.exchange,
            "category": self.category,
            "positions": "[REDACTED]",
            "position_count": len(self.positions),
        }


@dataclass(frozen=True)
class ApiKeyInfo:
    """Sanitized read-only Bybit API key preflight summary.

    Raw permission groups, account/user identifiers, IP allowlists, and expiry
    values are intentionally not retained or exposed.
    """

    exchange: str
    read_only: bool
    permissions_safe: bool
    key_active: bool
    deadline_days_present: bool
    expired_at_present: bool

    def __repr__(self) -> str:
        return (
            "ApiKeyInfo("
            f"exchange={self.exchange!r}, read_only={self.read_only!r}, "
            f"permissions_safe={self.permissions_safe!r}, "
            f"key_active={self.key_active!r}, "
            f"deadline_days_present={self.deadline_days_present!r}, "
            f"expired_at_present={self.expired_at_present!r})"
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "exchange": self.exchange,
            "read_only": self.read_only,
            "permissions_safe": self.permissions_safe,
            "key_active": self.key_active,
            "deadline_days_present": self.deadline_days_present,
            "expired_at_present": self.expired_at_present,
        }
