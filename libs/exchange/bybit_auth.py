from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

from pydantic import SecretStr

from libs.exchange.errors import ExchangeAuthError, ExchangeConfigurationError

_MIN_RECV_WINDOW_MS = 1_000
_MAX_RECV_WINDOW_MS = 60_000
_REDACTED = "[REDACTED]"


def now_ms() -> int:
    return int(time.time() * 1000)


def validate_recv_window(recv_window_ms: int) -> int:
    if not isinstance(recv_window_ms, int):
        raise ExchangeConfigurationError("recv_window_ms must be an integer")
    if not _MIN_RECV_WINDOW_MS <= recv_window_ms <= _MAX_RECV_WINDOW_MS:
        raise ExchangeConfigurationError(
            f"recv_window_ms must be between {_MIN_RECV_WINDOW_MS} and "
            f"{_MAX_RECV_WINDOW_MS}"
        )
    return recv_window_ms


def _secret_value(value: SecretStr | str | None, *, label: str) -> str:
    if value is None:
        raise ExchangeAuthError(f"Bybit {label} is required")
    raw = value.get_secret_value() if isinstance(value, SecretStr) else value
    if not isinstance(raw, str) or not raw.strip():
        raise ExchangeAuthError(f"Bybit {label} is required")
    if any(ch.isspace() for ch in raw):
        raise ExchangeAuthError(f"Bybit {label} is malformed")
    return raw


def canonical_query(params: dict[str, Any] | None) -> str:
    if not params:
        return ""
    return urlencode(sorted((str(k), str(v)) for k, v in params.items()))


def canonical_json_body(body: dict[str, Any] | None) -> str:
    if not body:
        return ""
    return json.dumps(body, separators=(",", ":"), sort_keys=True)


def bybit_signature_payload(
    *,
    timestamp_ms: int,
    api_key: str,
    recv_window_ms: int,
    query_string: str = "",
    body: str = "",
) -> str:
    return f"{timestamp_ms}{api_key}{recv_window_ms}{query_string or body}"


def sign_payload(payload: str, api_secret: str) -> str:
    return hmac.new(
        api_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, SecretStr):
        return _REDACTED
    if isinstance(value, dict):
        return {k: redact_sensitive(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(redact_sensitive(v) for v in value)
    return value


def safe_headers_for_log(headers: dict[str, str]) -> dict[str, str]:
    sensitive = {
        "X-BAPI-API-KEY",
        "X-BAPI-SIGN",
        "X-BAPI-TIMESTAMP",
        "Authorization",
    }
    return {
        key: (_REDACTED if key in sensitive else value)
        for key, value in headers.items()
    }


@dataclass(frozen=True)
class BybitAuth:
    api_key: SecretStr = field(repr=False)
    api_secret: SecretStr = field(repr=False)
    recv_window_ms: int = 5_000

    def __post_init__(self) -> None:
        validate_recv_window(self.recv_window_ms)
        _secret_value(self.api_key, label="api_key")
        _secret_value(self.api_secret, label="api_secret")

    def signed_headers(
        self,
        *,
        query_params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        timestamp_ms: int | None = None,
    ) -> dict[str, str]:
        api_key = _secret_value(self.api_key, label="api_key")
        api_secret = _secret_value(self.api_secret, label="api_secret")
        ts = timestamp_ms if timestamp_ms is not None else now_ms()
        query_string = canonical_query(query_params)
        body_string = canonical_json_body(body)
        payload = bybit_signature_payload(
            timestamp_ms=ts,
            api_key=api_key,
            recv_window_ms=self.recv_window_ms,
            query_string=query_string,
            body=body_string,
        )
        return {
            "X-BAPI-API-KEY": api_key,
            "X-BAPI-TIMESTAMP": str(ts),
            "X-BAPI-RECV-WINDOW": str(self.recv_window_ms),
            "X-BAPI-SIGN": sign_payload(payload, api_secret),
            "User-Agent": "trading-system",
        }
