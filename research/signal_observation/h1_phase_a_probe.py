"""Bounded metadata-only funding coverage probe for H1 Phase A.

Economic values are treated as opaque payload data.  The only human-readable
output is structural metadata described by ``ProbeRecord``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol, Sequence


TIMEOUT_SECONDS = 15
MAX_REQUESTS = 8
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
ACQUISITION_ID_RE = re.compile(r"^[a-z0-9_-]+$")
OUTPUT_ROOT = Path(__file__).resolve().parent / "data" / "h1" / "phase_a"


@dataclass(frozen=True)
class RequestSpec:
    venue: str
    host: str
    path: str
    contract_id: str
    query: tuple[tuple[str, str], ...]

    @property
    def url(self) -> str:
        return urllib.parse.urlunsplit(
            ("https", self.host, self.path, urllib.parse.urlencode(self.query), "")
        )


REQUEST_SPECS: tuple[RequestSpec, ...] = (
    RequestSpec(
        venue="binance",
        host="fapi.binance.com",
        path="/fapi/v1/fundingRate",
        contract_id="BTCUSDT",
        query=(("symbol", "BTCUSDT"), ("limit", "1000")),
    ),
    RequestSpec(
        venue="bitget",
        host="api.bitget.com",
        path="/api/v2/mix/market/history-fund-rate",
        contract_id="BTCUSDT",
        query=(
            ("symbol", "BTCUSDT"),
            ("productType", "USDT-FUTURES"),
            ("pageSize", "100"),
        ),
    ),
    RequestSpec(
        venue="bybit",
        host="api.bybit.com",
        path="/v5/market/funding/history",
        contract_id="BTCUSDT",
        query=(("category", "linear"), ("symbol", "BTCUSDT"), ("limit", "200")),
    ),
    RequestSpec(
        venue="okx",
        host="www.okx.com",
        path="/api/v5/public/funding-rate-history",
        contract_id="BTC-USDT-SWAP",
        query=(("instId", "BTC-USDT-SWAP"), ("limit", "100")),
    ),
)

_FROZEN_ALLOWLIST = {
    spec.venue: (spec.host, spec.path, spec.contract_id, spec.query)
    for spec in REQUEST_SPECS
}


@dataclass(frozen=True)
class ProbeRecord:
    venue: str
    structural_status: str
    http_status: int | None
    byte_count: int
    row_count: int
    field_names: list[str]
    min_funding_timestamp_utc: str | None
    max_funding_timestamp_utc: str | None
    contract_id: str
    sanitized_error_code: str | None


class ProbeFailure(Exception):
    """Failure whose string representation is always a fixed safe code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ResponseLike(Protocol):
    headers: Mapping[str, str]

    def __enter__(self) -> "ResponseLike": ...

    def __exit__(self, *args: object) -> None: ...

    def getcode(self) -> int: ...

    def geturl(self) -> str: ...

    def read(self, amount: int = -1) -> bytes: ...


class OpenerLike(Protocol):
    def open(self, request: urllib.request.Request, *, timeout: int) -> ResponseLike: ...


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Mapping[str, str],
        newurl: str,
    ) -> None:
        raise ProbeFailure("redirect_rejected")


def _default_opener() -> OpenerLike:
    context = ssl.create_default_context()
    return urllib.request.build_opener(
        _RejectRedirects(), urllib.request.HTTPSHandler(context=context)
    )


def _validate_spec(spec: RequestSpec) -> None:
    frozen = _FROZEN_ALLOWLIST.get(spec.venue)
    if frozen != (spec.host, spec.path, spec.contract_id, spec.query):
        raise ProbeFailure("source_not_allowlisted")
    parsed = urllib.parse.urlsplit(spec.url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != spec.host
        or parsed.path != spec.path
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        raise ProbeFailure("source_not_allowlisted")


def _validate_final_url(spec: RequestSpec, final_url: str) -> None:
    parsed = urllib.parse.urlsplit(final_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != spec.host
        or parsed.path != spec.path
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        raise ProbeFailure("unexpected_final_source")


def _read_bounded(response: ResponseLike) -> bytes:
    content_length = response.headers.get("Content-Length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_RESPONSE_BYTES:
                raise ProbeFailure("response_too_large")
        except ValueError:
            raise ProbeFailure("invalid_content_length") from None
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ProbeFailure("response_too_large")
    return body


def _decode_object(body: bytes) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ProbeFailure("invalid_json") from None


def _require_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ProbeFailure("unknown_schema")
    rows: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or not all(isinstance(key, str) for key in item):
            raise ProbeFailure("unknown_schema")
        rows.append(item)
    return rows


def _parse_binance(payload: Any) -> list[dict[str, Any]]:
    return _require_rows(payload)


def _parse_bitget(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("code") != "00000":
        raise ProbeFailure("unknown_schema")
    return _require_rows(payload.get("data"))


def _parse_bybit(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("retCode") != 0:
        raise ProbeFailure("unknown_schema")
    result = payload.get("result")
    if not isinstance(result, dict) or result.get("category") != "linear":
        raise ProbeFailure("unknown_schema")
    return _require_rows(result.get("list"))


def _parse_okx(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("code") != "0":
        raise ProbeFailure("unknown_schema")
    return _require_rows(payload.get("data"))


_PARSERS: Mapping[str, Callable[[Any], list[dict[str, Any]]]] = {
    "binance": _parse_binance,
    "bitget": _parse_bitget,
    "bybit": _parse_bybit,
    "okx": _parse_okx,
}

_ROW_FIELDS = {
    "binance": ("symbol", "fundingTime"),
    "bitget": ("symbol", "fundingTime"),
    "bybit": ("symbol", "fundingRateTimestamp"),
    "okx": ("instId", "fundingTime"),
}


def _timestamp_utc(value: Any) -> tuple[int, str]:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ProbeFailure("unknown_schema")
    try:
        milliseconds = int(value)
        moment = datetime.fromtimestamp(milliseconds / 1000, tz=timezone.utc)
    except (ValueError, OverflowError, OSError):
        raise ProbeFailure("invalid_timestamp") from None
    return milliseconds, moment.isoformat().replace("+00:00", "Z")


def _structural_metadata(
    spec: RequestSpec, rows: Sequence[dict[str, Any]]
) -> tuple[list[str], str | None, str | None]:
    contract_field, timestamp_field = _ROW_FIELDS[spec.venue]
    field_names = sorted({key for row in rows for key in row})
    timestamps: list[tuple[int, str]] = []
    seen: set[int] = set()
    for row in rows:
        if contract_field not in row or timestamp_field not in row:
            raise ProbeFailure("unknown_schema")
        if row[contract_field] != spec.contract_id:
            raise ProbeFailure("contract_mismatch")
        numeric, rendered = _timestamp_utc(row[timestamp_field])
        if numeric in seen:
            raise ProbeFailure("duplicate_timestamp")
        seen.add(numeric)
        timestamps.append((numeric, rendered))
    if not timestamps:
        return field_names, None, None
    timestamps.sort(key=lambda item: item[0])
    return field_names, timestamps[0][1], timestamps[-1][1]


def _atomic_create(path: Path, data: bytes) -> None:
    """Publish complete bytes atomically and refuse an existing destination."""

    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    except FileExistsError:
        raise ProbeFailure("destination_exists") from None
    except OSError:
        raise ProbeFailure("storage_error") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _error_record(
    spec: RequestSpec,
    code: str,
    *,
    http_status: int | None = None,
    byte_count: int = 0,
) -> ProbeRecord:
    return ProbeRecord(
        venue=spec.venue,
        structural_status="error",
        http_status=http_status,
        byte_count=byte_count,
        row_count=0,
        field_names=[],
        min_funding_timestamp_utc=None,
        max_funding_timestamp_utc=None,
        contract_id=spec.contract_id,
        sanitized_error_code=code,
    )


def _probe_one(spec: RequestSpec, raw_dir: Path, opener: OpenerLike) -> ProbeRecord:
    body = b""
    http_status: int | None = None
    try:
        _validate_spec(spec)
        request = urllib.request.Request(
            spec.url,
            headers={"Accept": "application/json", "User-Agent": "hephaestus-h1-phase-a/1"},
            method="GET",
        )
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            http_status = response.getcode()
            if http_status in (401, 403, 407):
                raise ProbeFailure("auth_challenge")
            if http_status != 200:
                raise ProbeFailure("http_error")
            _validate_final_url(spec, response.geturl())
            body = _read_bounded(response)
        _atomic_create(raw_dir / f"{spec.venue}.json", body)
        rows = _PARSERS[spec.venue](_decode_object(body))
        fields, minimum, maximum = _structural_metadata(spec, rows)
        return ProbeRecord(
            venue=spec.venue,
            structural_status="valid",
            http_status=http_status,
            byte_count=len(body),
            row_count=len(rows),
            field_names=fields,
            min_funding_timestamp_utc=minimum,
            max_funding_timestamp_utc=maximum,
            contract_id=spec.contract_id,
            sanitized_error_code=None,
        )
    except ProbeFailure as exc:
        return _error_record(
            spec, exc.code, http_status=http_status, byte_count=len(body)
        )
    except urllib.error.HTTPError as exc:
        code = "auth_challenge" if exc.code in (401, 403, 407) else "http_error"
        return _error_record(spec, code, http_status=exc.code)
    except (urllib.error.URLError, TimeoutError, OSError):
        return _error_record(spec, "transport_error", http_status=http_status)


def run_probe(
    acquisition_id: str,
    *,
    output_root: Path = OUTPUT_ROOT,
    opener: OpenerLike | None = None,
    specs: Sequence[RequestSpec] = REQUEST_SPECS,
) -> list[dict[str, Any]]:
    if not ACQUISITION_ID_RE.fullmatch(acquisition_id):
        raise ProbeFailure("invalid_acquisition_id")
    if len(specs) > MAX_REQUESTS:
        raise ProbeFailure("request_budget_exceeded")

    acquisition_dir = output_root / acquisition_id
    try:
        acquisition_dir.mkdir(parents=True, exist_ok=False)
        raw_dir = acquisition_dir / "raw"
        raw_dir.mkdir()
    except FileExistsError:
        raise ProbeFailure("acquisition_exists") from None
    except OSError:
        raise ProbeFailure("storage_error") from None

    active_opener = opener or _default_opener()
    records = [_probe_one(spec, raw_dir, active_opener) for spec in specs]
    output = [asdict(record) for record in records]
    encoded = json.dumps(output, sort_keys=True, separators=(",", ":")).encode("utf-8")
    _atomic_create(acquisition_dir / "metadata.json", encoded)
    return output


def _acquisition_id(value: str) -> str:
    if not ACQUISITION_ID_RE.fullmatch(value):
        raise argparse.ArgumentTypeError("must match [a-z0-9_-]+")
    return value


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the H1 Phase A metadata probe")
    parser.add_argument("--acquisition-id", required=True, type=_acquisition_id)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        output = run_probe(args.acquisition_id)
    except ProbeFailure as exc:
        print(json.dumps({"sanitized_error_code": exc.code}), file=sys.stderr)
        return 2
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
