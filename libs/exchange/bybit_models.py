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
