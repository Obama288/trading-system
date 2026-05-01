from __future__ import annotations

import base64
import hashlib
import hmac

import pytest
from pydantic import SecretStr

from libs.exchange.bitget_auth import (
    BitgetAuth,
    bitget_signature_payload,
    redact_sensitive,
    safe_headers_for_log,
    sign_payload,
)
from libs.exchange.errors import ExchangeAuthError


FAKE_API_KEY = "demo_fake_key"
FAKE_API_SECRET = "demo_fake_secret"
FAKE_PASSPHRASE = "demo_fake_passphrase"


def test_signature_payload_is_deterministic_for_fixed_inputs():
    assert bitget_signature_payload(
        timestamp_ms=1700000000000,
        method="get",
        request_path="/api/v2/mix/account/account",
        query_string="productType=USDT-FUTURES&symbol=BTCUSDT",
        body='{"limit":"20"}',
    ) == (
        "1700000000000"
        "GET"
        "/api/v2/mix/account/account"
        "?productType=USDT-FUTURES&symbol=BTCUSDT"
        '{"limit":"20"}'
    )


def test_method_is_uppercased_before_signing():
    lower = bitget_signature_payload(
        timestamp_ms=1700000000000,
        method="post",
        request_path="/api/v2/mix/order/place-order",
    )
    upper = bitget_signature_payload(
        timestamp_ms=1700000000000,
        method="POST",
        request_path="/api/v2/mix/order/place-order",
    )

    assert lower == upper
    assert "POST" in lower


def test_query_string_is_included_only_when_present():
    with_query = bitget_signature_payload(
        timestamp_ms=1700000000000,
        method="GET",
        request_path="/api/v2/public/time",
        query_string="locale=en-US",
    )
    without_query = bitget_signature_payload(
        timestamp_ms=1700000000000,
        method="GET",
        request_path="/api/v2/public/time",
    )

    assert with_query.endswith("/api/v2/public/time?locale=en-US")
    assert without_query.endswith("/api/v2/public/time")
    assert "?" not in without_query


def test_body_is_included_exactly_as_supplied():
    body = '{"symbol":"BTCUSDT","note":"  keep exact spacing  "}'

    payload = bitget_signature_payload(
        timestamp_ms=1700000000000,
        method="POST",
        request_path="/api/v2/mix/order/place-order",
        body=body,
    )

    assert payload.endswith(body)


def test_signature_matches_hmac_sha256_base64():
    payload = bitget_signature_payload(
        timestamp_ms=1700000000000,
        method="GET",
        request_path="/api/v2/public/time",
    )

    signature = sign_payload(payload, FAKE_API_SECRET)

    expected = base64.b64encode(
        hmac.new(
            FAKE_API_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")
    assert signature == expected


def test_signed_headers_include_required_bitget_header_names():
    auth = BitgetAuth(
        api_key=SecretStr(FAKE_API_KEY),
        api_secret=SecretStr(FAKE_API_SECRET),
        passphrase=SecretStr(FAKE_PASSPHRASE),
    )

    headers = auth.signed_headers(
        timestamp_ms=1700000000000,
        method="get",
        request_path="/api/v2/public/time",
    )

    assert headers["ACCESS-KEY"] == FAKE_API_KEY
    assert headers["ACCESS-TIMESTAMP"] == "1700000000000"
    assert headers["ACCESS-PASSPHRASE"] == FAKE_PASSPHRASE
    assert headers["Content-Type"] == "application/json"
    assert "ACCESS-SIGN" in headers
    assert "paptrading" not in headers


@pytest.mark.parametrize(
    ("api_key", "api_secret", "passphrase"),
    [
        (None, FAKE_API_SECRET, FAKE_PASSPHRASE),
        (FAKE_API_KEY, None, FAKE_PASSPHRASE),
        (FAKE_API_KEY, FAKE_API_SECRET, None),
        ("", FAKE_API_SECRET, FAKE_PASSPHRASE),
        (FAKE_API_KEY, "", FAKE_PASSPHRASE),
        (FAKE_API_KEY, FAKE_API_SECRET, ""),
        ("   ", FAKE_API_SECRET, FAKE_PASSPHRASE),
    ],
)
def test_missing_or_empty_credentials_fail_closed(
    api_key: str | None,
    api_secret: str | None,
    passphrase: str | None,
):
    with pytest.raises(ExchangeAuthError):
        BitgetAuth(
            api_key=SecretStr(api_key) if api_key is not None else None,  # type: ignore[arg-type]
            api_secret=SecretStr(api_secret) if api_secret is not None else None,  # type: ignore[arg-type]
            passphrase=SecretStr(passphrase) if passphrase is not None else None,  # type: ignore[arg-type]
        )


def test_safe_repr_and_redaction_do_not_expose_secret_bearing_values():
    auth = BitgetAuth(
        api_key=SecretStr(FAKE_API_KEY),
        api_secret=SecretStr(FAKE_API_SECRET),
        passphrase=SecretStr(FAKE_PASSPHRASE),
    )
    headers = auth.signed_headers(
        timestamp_ms=1700000000000,
        method="GET",
        request_path="/api/v2/public/time",
    )

    rendered = repr(auth)
    assert FAKE_API_KEY not in rendered
    assert FAKE_API_SECRET not in rendered
    assert FAKE_PASSPHRASE not in rendered

    safe_dict = auth.safe_dict()
    assert safe_dict["api_key"] == "[REDACTED]"
    assert safe_dict["api_secret"] == "[REDACTED]"
    assert safe_dict["passphrase"] == "[REDACTED]"
    assert FAKE_API_KEY not in repr(safe_dict)
    assert FAKE_API_SECRET not in repr(safe_dict)
    assert FAKE_PASSPHRASE not in repr(safe_dict)

    safe_headers = safe_headers_for_log(headers)
    assert safe_headers["ACCESS-KEY"] == "[REDACTED]"
    assert safe_headers["ACCESS-SIGN"] == "[REDACTED]"
    assert safe_headers["ACCESS-PASSPHRASE"] == "[REDACTED]"
    assert FAKE_API_KEY not in repr(safe_headers)
    assert FAKE_API_SECRET not in repr(safe_headers)
    assert FAKE_PASSPHRASE not in repr(safe_headers)
    assert headers["ACCESS-SIGN"] not in repr(safe_headers)

    redacted = redact_sensitive(
        {
            "api_key": SecretStr(FAKE_API_KEY),
            "nested": {
                "api_secret": SecretStr(FAKE_API_SECRET),
                "passphrase": SecretStr(FAKE_PASSPHRASE),
            },
        }
    )
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["api_secret"] == "[REDACTED]"
    assert redacted["nested"]["passphrase"] == "[REDACTED]"


def test_helper_exposes_no_network_or_client_behavior():
    auth = BitgetAuth(
        api_key=SecretStr(FAKE_API_KEY),
        api_secret=SecretStr(FAKE_API_SECRET),
        passphrase=SecretStr(FAKE_PASSPHRASE),
    )

    assert hasattr(auth, "signed_headers")
    for forbidden in (
        "get",
        "post",
        "request",
        "get_wallet_balance",
        "get_open_positions",
        "get_query_api_info",
        "_private_get",
        "_client",
    ):
        assert not hasattr(auth, forbidden), f"Forbidden attribute exists: {forbidden}"
