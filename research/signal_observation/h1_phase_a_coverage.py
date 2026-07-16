"""Blind, bounded acquisition of H1 historical funding coverage.

Raw funding values remain opaque. Human-readable output contains structural
coverage metadata only; this module performs no strategy or outcome analysis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence


TIMEOUT_SECONDS = 15
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_CUMULATIVE_BYTES = 64 * 1024 * 1024
MAX_REQUESTS = 80
MIN_PAGE_PAUSE_SECONDS = 0.1
MAX_ALLOWED_GAP_MS = 24 * 60 * 60 * 1000
BOUNDARY_TOLERANCE_MS = MAX_ALLOWED_GAP_MS
ACQUISITION_ID_RE = re.compile(r"^[a-z0-9_-]+$")
OUTPUT_ROOT = Path(__file__).resolve().parent / "data" / "h1" / "phase_a_coverage"


def _utc_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


TARGET_START_MS = _utc_ms("2023-01-01T00:00:00Z")
TARGET_END_MS = _utc_ms("2026-07-01T00:00:00Z")
WINDOWS: tuple[tuple[str, int, int], ...] = (
    ("discovery", TARGET_START_MS, _utc_ms("2024-07-01T00:00:00Z")),
    ("validation", _utc_ms("2024-07-01T00:00:00Z"), _utc_ms("2025-07-01T00:00:00Z")),
    ("holdout", _utc_ms("2025-07-01T00:00:00Z"), _utc_ms("2026-07-01T00:00:00Z")),
)


@dataclass(frozen=True)
class VenueSpec:
    venue: str
    host: str
    path: str
    contract_id: str
    contract_field: str
    timestamp_field: str
    direction: str
    max_pages: int


VENUE_SPECS: tuple[VenueSpec, ...] = (
    VenueSpec("binance", "fapi.binance.com", "/fapi/v1/fundingRate", "BTCUSDT", "symbol", "fundingTime", "ascending", 6),
    VenueSpec("bitget", "api.bitget.com", "/api/v2/mix/market/history-fund-rate", "BTCUSDT", "symbol", "fundingTime", "descending", 45),
    VenueSpec("bybit", "api.bybit.com", "/v5/market/funding/history", "BTCUSDT", "symbol", "fundingRateTimestamp", "descending", 24),
    VenueSpec("okx", "www.okx.com", "/api/v5/public/funding-rate-history", "BTC-USDT-SWAP", "instId", "fundingTime", "descending", 5),
)
_SPEC_BY_VENUE = {spec.venue: spec for spec in VENUE_SPECS}
_FROZEN_SOURCES = {
    spec.venue: (spec.host, spec.path, spec.contract_id, spec.direction, spec.max_pages)
    for spec in VENUE_SPECS
}
_QUERY_KEYS = {
    "binance": frozenset({"symbol", "startTime", "endTime", "limit"}),
    "bitget": frozenset({"symbol", "productType", "pageSize", "pageNo"}),
    "bybit": frozenset({"category", "symbol", "endTime", "limit"}),
    "okx": frozenset({"instId", "after", "limit"}),
}


@dataclass(frozen=True)
class RequestSpec:
    venue: str
    host: str
    path: str
    query: tuple[tuple[str, str], ...]

    @property
    def url(self) -> str:
        return urllib.parse.urlunsplit(("https", self.host, self.path, urllib.parse.urlencode(self.query), ""))


@dataclass(frozen=True)
class RawPageRecord:
    page: int
    http_status: int
    byte_count: int
    row_count: int
    sha256: str


@dataclass(frozen=True)
class CoverageRecord:
    venue: str
    status: str
    http_status: int | None
    page_count: int
    byte_count: int
    row_count: int
    field_names: list[str]
    min_funding_timestamp_utc: str | None
    max_funding_timestamp_utc: str | None
    max_gap_ms: int | None
    contract_id: str
    target_coverage: bool
    discovery_coverage: bool
    validation_coverage: bool
    holdout_coverage: bool
    sanitized_code: str | None
    raw_pages: list[RawPageRecord]


class CoverageFailure(Exception):
    """Failure whose printable representation is a fixed, non-sensitive code."""

    def __init__(self, code: str, *, http_status: int | None = None) -> None:
        self.code = code
        self.http_status = http_status
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
    def redirect_request(self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Mapping[str, str], newurl: str) -> None:
        raise CoverageFailure("redirect_rejected")


@dataclass
class _Budget:
    request_count: int = 0
    bytes: int = 0

    def reserve_request(self) -> None:
        if self.request_count >= MAX_REQUESTS:
            raise CoverageFailure("request_budget_exceeded")
        self.request_count += 1

    def add_bytes(self, amount: int) -> None:
        if amount > MAX_RESPONSE_BYTES:
            raise CoverageFailure("response_too_large")
        if self.bytes + amount > MAX_CUMULATIVE_BYTES:
            raise CoverageFailure("cumulative_byte_budget_exceeded")
        self.bytes += amount


def _default_opener() -> OpenerLike:
    context = ssl.create_default_context()
    return urllib.request.build_opener(_RejectRedirects(), urllib.request.HTTPSHandler(context=context))


def build_request(spec: VenueSpec, page: int, cursor: int | None) -> RequestSpec:
    if page < 1 or page > spec.max_pages:
        raise CoverageFailure("page_budget_exceeded")
    if spec.venue == "binance":
        if cursor is None:
            raise CoverageFailure("invalid_cursor")
        query = (("symbol", "BTCUSDT"), ("startTime", str(cursor)), ("endTime", str(TARGET_END_MS - 1)), ("limit", "1000"))
    elif spec.venue == "bitget":
        query = (("symbol", "BTCUSDT"), ("productType", "USDT-FUTURES"), ("pageSize", "100"), ("pageNo", str(page)))
    elif spec.venue == "bybit":
        if cursor is None:
            raise CoverageFailure("invalid_cursor")
        query = (("category", "linear"), ("symbol", "BTCUSDT"), ("endTime", str(cursor)), ("limit", "200"))
    elif spec.venue == "okx":
        if cursor is None:
            raise CoverageFailure("invalid_cursor")
        query = (("instId", "BTC-USDT-SWAP"), ("after", str(cursor)), ("limit", "400"))
    else:
        raise CoverageFailure("source_not_allowlisted")
    request = RequestSpec(spec.venue, spec.host, spec.path, query)
    _validate_request(spec, request)
    return request


def _validate_request(spec: VenueSpec, request: RequestSpec) -> None:
    frozen = _FROZEN_SOURCES.get(spec.venue)
    if frozen != (spec.host, spec.path, spec.contract_id, spec.direction, spec.max_pages):
        raise CoverageFailure("source_not_allowlisted")
    parsed = urllib.parse.urlsplit(request.url)
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    keys = [key for key, _ in pairs]
    if (
        request.venue != spec.venue
        or parsed.scheme != "https"
        or parsed.hostname != spec.host
        or parsed.path != spec.path
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or len(keys) != len(set(keys))
        or frozenset(keys) != _QUERY_KEYS[spec.venue]
    ):
        raise CoverageFailure("source_not_allowlisted")


def _validate_final_url(request: RequestSpec, final_url: str) -> None:
    parsed = urllib.parse.urlsplit(final_url)
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    expected = urllib.parse.parse_qsl(urllib.parse.urlsplit(request.url).query, keep_blank_values=True)
    if (
        parsed.scheme != "https"
        or parsed.hostname != request.host
        or parsed.path != request.path
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or pairs != expected
    ):
        raise CoverageFailure("unexpected_final_source")


def _read_bounded(response: ResponseLike, budget: _Budget) -> bytes:
    content_type = response.headers.get("Content-Type", "")
    if not content_type.lower().startswith("application/json"):
        raise CoverageFailure("unexpected_content_type")
    content_length = response.headers.get("Content-Length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except ValueError:
            raise CoverageFailure("invalid_content_length") from None
        if declared < 0 or declared > MAX_RESPONSE_BYTES:
            raise CoverageFailure("response_too_large")
        if budget.bytes + declared > MAX_CUMULATIVE_BYTES:
            raise CoverageFailure("cumulative_byte_budget_exceeded")
    body = response.read(MAX_RESPONSE_BYTES + 1)
    budget.add_bytes(len(body))
    return body


def _decode(body: bytes) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise CoverageFailure("invalid_json") from None


def _rows_for(venue: str, payload: Any) -> list[dict[str, Any]]:
    value: Any
    if venue == "binance":
        value = payload
    elif venue == "bitget" and isinstance(payload, dict) and payload.get("code") == "00000":
        value = payload.get("data")
    elif venue == "bybit" and isinstance(payload, dict) and payload.get("retCode") == 0:
        result = payload.get("result")
        if not isinstance(result, dict) or result.get("category") != "linear":
            raise CoverageFailure("unknown_schema")
        value = result.get("list")
    elif venue == "okx" and isinstance(payload, dict) and payload.get("code") == "0":
        value = payload.get("data")
    else:
        raise CoverageFailure("unknown_schema")
    if not isinstance(value, list):
        raise CoverageFailure("unknown_schema")
    rows: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or not all(isinstance(key, str) for key in item):
            raise CoverageFailure("unknown_schema")
        rows.append(item)
    return rows


def _timestamp(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise CoverageFailure("unknown_schema")
    try:
        timestamp = int(value)
        datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    except (ValueError, OverflowError, OSError):
        raise CoverageFailure("invalid_timestamp") from None
    return timestamp


def validate_rows(spec: VenueSpec, rows: Sequence[dict[str, Any]], seen: set[int]) -> tuple[list[int], set[str]]:
    timestamps: list[int] = []
    fields: set[str] = set()
    for row in rows:
        fields.update(row)
        if row.get(spec.contract_field) != spec.contract_id or spec.timestamp_field not in row:
            code = "contract_mismatch" if spec.contract_field in row else "unknown_schema"
            raise CoverageFailure(code)
        timestamp = _timestamp(row[spec.timestamp_field])
        if timestamp in seen:
            raise CoverageFailure("duplicate_timestamp")
        seen.add(timestamp)
        timestamps.append(timestamp)
    ordered = sorted(timestamps, reverse=spec.direction == "descending")
    if timestamps != ordered or len(timestamps) != len(set(timestamps)):
        raise CoverageFailure("unexpected_order")
    return timestamps, fields


def next_cursor(spec: VenueSpec, current: int | None, timestamps: Sequence[int]) -> int | None:
    if not timestamps:
        return None
    candidate = max(timestamps) + 1 if spec.direction == "ascending" else min(timestamps) - 1
    if current is not None:
        progressing = candidate > current if spec.direction == "ascending" else candidate < current
        if not progressing:
            raise CoverageFailure("non_progress")
    return candidate


def validate_page_progress(
    spec: VenueSpec,
    cursor: int | None,
    timestamps: Sequence[int],
    previous_bounds: tuple[int, int] | None,
) -> tuple[int, int] | None:
    if not timestamps:
        return previous_bounds
    page_min = min(timestamps)
    page_max = max(timestamps)
    if spec.venue == "binance":
        if cursor is None or page_min < cursor or page_max >= TARGET_END_MS:
            raise CoverageFailure("non_progress")
    elif spec.venue == "bybit":
        if cursor is None or page_max > cursor:
            raise CoverageFailure("non_progress")
    elif spec.venue == "okx":
        if cursor is None or page_max >= cursor:
            raise CoverageFailure("non_progress")
    if previous_bounds is not None:
        previous_min, previous_max = previous_bounds
        if spec.direction == "ascending" and page_min <= previous_max:
            raise CoverageFailure("non_progress")
        if spec.direction == "descending" and page_max >= previous_min:
            raise CoverageFailure("non_progress")
    return page_min, page_max


def max_gap_ms(timestamps: Sequence[int]) -> int | None:
    ordered = sorted(set(timestamps))
    if len(ordered) < 2:
        return None
    return max(right - left for left, right in zip(ordered, ordered[1:]))


def _covers(timestamps: Sequence[int], start: int, end: int) -> bool:
    in_window = sorted({value for value in timestamps if start <= value < end})
    gap = max_gap_ms(in_window)
    return (
        bool(in_window)
        and in_window[0] < start + BOUNDARY_TOLERANCE_MS
        and in_window[-1] >= end - BOUNDARY_TOLERANCE_MS
        and gap is not None
        and gap <= MAX_ALLOWED_GAP_MS
    )


def structural_coverage(timestamps: Sequence[int]) -> dict[str, bool]:
    result = {name: _covers(timestamps, start, end) for name, start, end in WINDOWS}
    result["target"] = _covers(timestamps, TARGET_START_MS, TARGET_END_MS) and all(result.values())
    return result


def _render_timestamp(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_create(path: Path, data: bytes) -> None:
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
        raise CoverageFailure("destination_exists") from None
    except OSError:
        raise CoverageFailure("storage_error") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _initial_cursor(spec: VenueSpec) -> int | None:
    if spec.venue == "binance":
        return TARGET_START_MS
    if spec.venue == "bitget":
        return None
    if spec.venue == "bybit":
        return TARGET_END_MS - 1
    return TARGET_END_MS


def _empty_record(spec: VenueSpec, code: str, *, http_status: int | None = None, pages: Sequence[RawPageRecord] = ()) -> CoverageRecord:
    return CoverageRecord(spec.venue, "ERROR", http_status, len(pages), sum(page.byte_count for page in pages), sum(page.row_count for page in pages), [], None, None, None, spec.contract_id, False, False, False, False, code, list(pages))


def _acquire_venue(
    spec: VenueSpec,
    raw_root: Path,
    opener: OpenerLike,
    budget: _Budget,
    page_pause_seconds: float,
) -> CoverageRecord:
    venue_dir = raw_root / spec.venue
    try:
        venue_dir.mkdir()
    except OSError:
        return _empty_record(spec, "storage_error")
    cursor = _initial_cursor(spec)
    seen: set[int] = set()
    all_timestamps: list[int] = []
    fields: set[str] = set()
    pages: list[RawPageRecord] = []
    last_http: int | None = None
    previous_bounds: tuple[int, int] | None = None
    try:
        for page_number in range(1, spec.max_pages + 1):
            if page_number > 1 and page_pause_seconds > 0:
                time.sleep(page_pause_seconds)
            request = build_request(spec, page_number, cursor)
            budget.reserve_request()
            raw_request = urllib.request.Request(request.url, headers={"Accept": "application/json", "User-Agent": "hephaestus-h1-coverage/1"}, method="GET")
            with opener.open(raw_request, timeout=TIMEOUT_SECONDS) as response:
                last_http = response.getcode()
                if last_http in (401, 403, 407):
                    raise CoverageFailure("auth_challenge", http_status=last_http)
                if last_http != 200:
                    raise CoverageFailure("http_error", http_status=last_http)
                _validate_final_url(request, response.geturl())
                body = _read_bounded(response, budget)
            raw_path = venue_dir / f"page_{page_number:04d}.json"
            _atomic_create(raw_path, body)
            digest = hashlib.sha256(body).hexdigest()
            pages.append(RawPageRecord(page_number, last_http, len(body), 0, digest))
            rows = _rows_for(spec.venue, _decode(body))
            pages[-1] = RawPageRecord(page_number, last_http, len(body), len(rows), digest)
            timestamps, page_fields = validate_rows(spec, rows, seen)
            previous_bounds = validate_page_progress(spec, cursor, timestamps, previous_bounds)
            fields.update(page_fields)
            all_timestamps.extend(timestamps)
            if not timestamps:
                break
            coverage = structural_coverage(all_timestamps)
            if coverage["target"]:
                break
            if spec.venue != "bitget":
                candidate = next_cursor(spec, cursor, timestamps)
                if candidate is None:
                    break
                cursor = candidate
        coverage = structural_coverage(all_timestamps)
        status = "PASS" if coverage["target"] else "FAIL"
        return CoverageRecord(
            spec.venue, status, last_http, len(pages), sum(page.byte_count for page in pages), len(all_timestamps), sorted(fields),
            _render_timestamp(min(all_timestamps) if all_timestamps else None),
            _render_timestamp(max(all_timestamps) if all_timestamps else None),
            max_gap_ms([value for value in all_timestamps if TARGET_START_MS <= value < TARGET_END_MS]),
            spec.contract_id, coverage["target"], coverage["discovery"], coverage["validation"], coverage["holdout"],
            None if status == "PASS" else "insufficient_coverage", pages,
        )
    except CoverageFailure as exc:
        return _empty_record(spec, exc.code, http_status=exc.http_status or last_http, pages=pages)
    except urllib.error.HTTPError as exc:
        code = "auth_challenge" if exc.code in (401, 403, 407) else "http_error"
        return _empty_record(spec, code, http_status=exc.code, pages=pages)
    except (urllib.error.URLError, TimeoutError, OSError):
        return _empty_record(spec, "transport_error", http_status=last_http, pages=pages)


def run_acquisition(acquisition_id: str, *, output_root: Path = OUTPUT_ROOT, opener: OpenerLike | None = None, specs: Sequence[VenueSpec] = VENUE_SPECS) -> list[dict[str, Any]]:
    if not ACQUISITION_ID_RE.fullmatch(acquisition_id):
        raise CoverageFailure("invalid_acquisition_id")
    if sum(spec.max_pages for spec in specs) > MAX_REQUESTS:
        raise CoverageFailure("request_budget_exceeded")
    acquisition_dir = output_root / acquisition_id
    try:
        acquisition_dir.mkdir(parents=True, exist_ok=False)
        raw_root = acquisition_dir / "raw"
        raw_root.mkdir()
    except FileExistsError:
        raise CoverageFailure("acquisition_exists") from None
    except OSError:
        raise CoverageFailure("storage_error") from None
    active_opener = opener or _default_opener()
    page_pause_seconds = 0.0 if opener is not None else MIN_PAGE_PAUSE_SECONDS
    budget = _Budget()
    records = [
        _acquire_venue(spec, raw_root, active_opener, budget, page_pause_seconds)
        for spec in specs
    ]
    output = [asdict(record) for record in records]
    encoded = json.dumps(output, sort_keys=True, separators=(",", ":")).encode("utf-8")
    _atomic_create(acquisition_dir / "metadata.json", encoded)
    return output


def _acquisition_id(value: str) -> str:
    if not ACQUISITION_ID_RE.fullmatch(value):
        raise argparse.ArgumentTypeError("must match [a-z0-9_-]+")
    return value


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Acquire blind H1 funding coverage")
    parser.add_argument("--acquisition-id", required=True, type=_acquisition_id)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        output = run_acquisition(args.acquisition_id)
    except CoverageFailure as exc:
        print(json.dumps({"sanitized_code": exc.code}), file=sys.stderr)
        return 2
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
