from __future__ import annotations

import hashlib
import hmac

import pytest
from pydantic import SecretStr

from libs.exchange.bybit_auth import (
    BybitAuth,
    bybit_signature_payload,
    canonical_query,
    redact_sensitive,
    safe_headers_for_log,
    sign_payload,
    validate_recv_window,
)
from libs.exchange.errors import ExchangeAuthError, ExchangeConfigurationError


FAKE_API_KEY = "testnet_fake_key"
FAKE_API_SECRET = "testnet_fake_secret"


def test_canonical_query_sorts_params():
    assert canonical_query({"symbol": "BTCUSDT", "category": "linear"}) == (
        "category=linear&symbol=BTCUSDT"
    )


def test_bybit_signature_matches_hmac_sha256():
    payload = bybit_signature_payload(
        timestamp_ms=1700000000000,
        api_key=FAKE_API_KEY,
        recv_window_ms=5000,
        query_string="category=linear&symbol=BTCUSDT",
    )

    signature = sign_payload(payload, FAKE_API_SECRET)

    assert signature == hmac.new(
        FAKE_API_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def test_signed_headers_include_auth_headers_without_leaking_in_repr():
    auth = BybitAuth(
        api_key=SecretStr(FAKE_API_KEY),
        api_secret=SecretStr(FAKE_API_SECRET),
    )

    headers = auth.signed_headers(
        query_params={"category": "linear"},
        timestamp_ms=1700000000000,
    )

    assert headers["X-BAPI-API-KEY"] == FAKE_API_KEY
    assert headers["X-BAPI-TIMESTAMP"] == "1700000000000"
    assert headers["X-BAPI-RECV-WINDOW"] == "5000"
    assert "X-BAPI-SIGN" in headers
    rendered = repr(auth)
    assert FAKE_API_KEY not in rendered
    assert FAKE_API_SECRET not in rendered


@pytest.mark.parametrize("api_key,api_secret", [(None, FAKE_API_SECRET), (FAKE_API_KEY, None)])
def test_missing_credentials_fail_closed(api_key: str | None, api_secret: str | None):
    with pytest.raises(ExchangeAuthError):
        BybitAuth(
            api_key=SecretStr(api_key) if api_key else None,  # type: ignore[arg-type]
            api_secret=SecretStr(api_secret) if api_secret else None,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("bad_value", ["", "   ", "bad key"])
def test_malformed_credentials_fail_closed(bad_value: str):
    with pytest.raises(ExchangeAuthError):
        BybitAuth(api_key=SecretStr(bad_value), api_secret=SecretStr(FAKE_API_SECRET))


@pytest.mark.parametrize("recv_window", [999, 60001])
def test_recv_window_outside_safe_bounds_rejected(recv_window: int):
    with pytest.raises(ExchangeConfigurationError):
        validate_recv_window(recv_window)


def test_safe_headers_for_log_redacts_auth_material():
    headers = {
        "X-BAPI-API-KEY": FAKE_API_KEY,
        "X-BAPI-SIGN": "fake_signature",
        "X-BAPI-TIMESTAMP": "1700000000000",
        "X-BAPI-RECV-WINDOW": "5000",
        "User-Agent": "trading-system",
    }

    safe = safe_headers_for_log(headers)

    assert safe["X-BAPI-API-KEY"] == "[REDACTED]"
    assert safe["X-BAPI-SIGN"] == "[REDACTED]"
    assert safe["X-BAPI-TIMESTAMP"] == "[REDACTED]"
    assert safe["X-BAPI-RECV-WINDOW"] == "5000"
    assert FAKE_API_KEY not in repr(safe)
    assert "fake_signature" not in repr(safe)


def test_redact_sensitive_redacts_secretstr_nested_values():
    payload = {
        "api_key": SecretStr(FAKE_API_KEY),
        "nested": {"api_secret": SecretStr(FAKE_API_SECRET)},
    }

    redacted = redact_sensitive(payload)

    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["api_secret"] == "[REDACTED]"
    assert FAKE_API_KEY not in repr(redacted)
    assert FAKE_API_SECRET not in repr(redacted)
