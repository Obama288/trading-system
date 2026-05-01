from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Any

from pydantic import SecretStr

from libs.exchange.errors import ExchangeAuthError, ExchangeConfigurationError

_REDACTED = "[REDACTED]"


def _secret_value(value: SecretStr | str | None, *, label: str) -> str:
    if value is None:
        raise ExchangeAuthError(f"Bitget {label} is required")
    raw = value.get_secret_value() if isinstance(value, SecretStr) else value
    if not isinstance(raw, str) or not raw.strip():
        raise ExchangeAuthError(f"Bitget {label} is required")
    return raw


def _normalized_method(method: str) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ExchangeConfigurationError("Bitget method is required")
    return method.strip().upper()


def _normalized_request_path(request_path: str) -> str:
    if not isinstance(request_path, str) or not request_path.strip():
        raise ExchangeConfigurationError("Bitget request_path is required")
    path = request_path.strip()
    if not path.startswith("/"):
        raise ExchangeConfigurationError("Bitget request_path must start with '/'")
    return path


def bitget_signature_payload(
    *,
    timestamp_ms: int | str,
    method: str,
    request_path: str,
    query_string: str = "",
    body: str = "",
) -> str:
    normalized_query = f"?{query_string}" if query_string else ""
    return (
        f"{timestamp_ms}"
        f"{_normalized_method(method)}"
        f"{_normalized_request_path(request_path)}"
        f"{normalized_query}"
        f"{body}"
    )


def sign_payload(payload: str, api_secret: str) -> str:
    digest = hmac.new(
        api_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


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
        "ACCESS-KEY",
        "ACCESS-SIGN",
        "ACCESS-PASSPHRASE",
    }
    return {
        key: (_REDACTED if key in sensitive else value)
        for key, value in headers.items()
    }


@dataclass(frozen=True)
class BitgetAuth:
    api_key: SecretStr = field(repr=False)
    api_secret: SecretStr = field(repr=False)
    passphrase: SecretStr = field(repr=False)

    def __post_init__(self) -> None:
        _secret_value(self.api_key, label="api_key")
        _secret_value(self.api_secret, label="api_secret")
        _secret_value(self.passphrase, label="passphrase")

    def safe_dict(self) -> dict[str, str]:
        return {
            "api_key": _REDACTED,
            "api_secret": _REDACTED,
            "passphrase": _REDACTED,
        }

    def signed_headers(
        self,
        *,
        timestamp_ms: int | str,
        method: str,
        request_path: str,
        query_string: str = "",
        body: str = "",
    ) -> dict[str, str]:
        api_key = _secret_value(self.api_key, label="api_key")
        api_secret = _secret_value(self.api_secret, label="api_secret")
        passphrase = _secret_value(self.passphrase, label="passphrase")
        payload = bitget_signature_payload(
            timestamp_ms=timestamp_ms,
            method=method,
            request_path=request_path,
            query_string=query_string,
            body=body,
        )
        return {
            "ACCESS-KEY": api_key,
            "ACCESS-SIGN": sign_payload(payload, api_secret),
            "ACCESS-TIMESTAMP": str(timestamp_ms),
            "ACCESS-PASSPHRASE": passphrase,
            "Content-Type": "application/json",
        }
