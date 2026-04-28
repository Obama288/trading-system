from __future__ import annotations

import argparse
import asyncio
import json
import time
from collections.abc import Callable
from pathlib import Path
import sys
from typing import Any

ENDPOINT_NAME = "server_time"
_SUCCESS_EXIT_CODE = 0
_FAILURE_EXIT_CODE = 1
_INCONCLUSIVE_EXIT_CODE = 2
_AUTHORIZATION_REQUIRED_EXIT_CODE = 3


def _base_output(*, status: str, elapsed_ms: int) -> dict[str, Any]:
    return {
        "operation": "bybit_b1_server_time_smoke",
        "endpoint": ENDPOINT_NAME,
        "endpoint_family": ENDPOINT_NAME,
        "status": status,
        "elapsed_ms": elapsed_ms,
    }


def _authorization_required_output() -> dict[str, Any]:
    return {
        "endpoint": "get_server_time",
        "status": "authorization_required",
        "message": "Real smoke execution requires explicit Human Owner authorization.",
        "exit_code": _AUTHORIZATION_REQUIRED_EXIT_CODE,
    }


def _ensure_repo_root_on_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)


def _error_category(exc: BaseException, error_types: dict[str, type[BaseException]]) -> str:
    ExchangeRateLimited = error_types["ExchangeRateLimited"]
    ExchangeAuthError = error_types["ExchangeAuthError"]
    ExchangeConfigurationError = error_types["ExchangeConfigurationError"]
    MarketDataUnavailable = error_types["MarketDataUnavailable"]
    ExchangeResponseError = error_types["ExchangeResponseError"]
    ValidationError = error_types["ValidationError"]

    if isinstance(exc, ExchangeRateLimited):
        return "rate_limited"
    if isinstance(exc, ExchangeAuthError):
        return "auth_error"
    if isinstance(exc, ExchangeConfigurationError):
        return "configuration_error"
    if isinstance(exc, MarketDataUnavailable):
        return "network_or_timeout"
    if isinstance(exc, ExchangeResponseError):
        return "response_error"
    if isinstance(exc, ValidationError):
        return "configuration_error"
    return "unexpected_error"


def _safe_ret_code(
    exc: BaseException,
    *,
    ExchangeResponseError: type[BaseException],
) -> int | None:
    if isinstance(exc, ExchangeResponseError):
        return getattr(exc, "ret_code")
    return None


async def run_server_time_smoke(
    *,
    settings: Any | None = None,
    client_factory: Callable[[Any], Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Run only the B2a server_time smoke and return sanitized output.

    This harness is real-capable, but B2a tests must mock the client/HTTP layer.
    It must not call wallet_balance, open_positions, order_status, or write/live
    methods.
    """

    _ensure_repo_root_on_path()
    from pydantic import ValidationError

    from libs.config.settings import BybitB1Settings
    from libs.exchange.bybit_read_only import BybitReadOnlyClient
    from libs.exchange.errors import (
        ExchangeAuthError,
        ExchangeConfigurationError,
        ExchangeError,
        ExchangeRateLimited,
        ExchangeResponseError,
        MarketDataUnavailable,
    )

    error_types: dict[str, type[BaseException]] = {
        "ExchangeRateLimited": ExchangeRateLimited,
        "ExchangeAuthError": ExchangeAuthError,
        "ExchangeConfigurationError": ExchangeConfigurationError,
        "MarketDataUnavailable": MarketDataUnavailable,
        "ExchangeResponseError": ExchangeResponseError,
        "ValidationError": ValidationError,
    }

    started = time.perf_counter()
    try:
        resolved_settings = settings if settings is not None else BybitB1Settings()
        resolved_client_factory = (
            client_factory if client_factory is not None else BybitReadOnlyClient
        )
        client = resolved_client_factory(resolved_settings)
        server_time = await client.get_server_time()
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        output = _base_output(status="success", elapsed_ms=elapsed_ms)
        output.update(
            {
                "exchange": server_time.exchange,
                "timestamp_second": server_time.time_second,
                "timestamp_nano": server_time.time_nano,
            }
        )
        return _SUCCESS_EXIT_CODE, output
    except ExchangeRateLimited as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        output = _base_output(status="inconclusive", elapsed_ms=elapsed_ms)
        output["error_category"] = _error_category(exc, error_types)
        return _INCONCLUSIVE_EXIT_CODE, output
    except (ExchangeError, ValidationError) as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        output = _base_output(status="failure", elapsed_ms=elapsed_ms)
        output["error_category"] = _error_category(exc, error_types)
        ret_code = _safe_ret_code(exc, ExchangeResponseError=ExchangeResponseError)
        if ret_code is not None:
            output["retCode"] = ret_code
        return _FAILURE_EXIT_CODE, output


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Stage 53-B2a Bybit server_time read-only smoke.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print sanitized JSON output.",
    )
    parser.add_argument(
        "--allow-real-smoke",
        action="store_true",
        help="Require explicit Human Owner authorization before real smoke execution.",
    )
    return parser.parse_args(argv)


async def _async_main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.allow_real_smoke:
        exit_code = _AUTHORIZATION_REQUIRED_EXIT_CODE
        output = _authorization_required_output()
    else:
        exit_code, output = await run_server_time_smoke()
    json_kwargs = {"sort_keys": True}
    if args.pretty:
        json_kwargs["indent"] = 2
    print(json.dumps(output, **json_kwargs))
    return exit_code


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_async_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
