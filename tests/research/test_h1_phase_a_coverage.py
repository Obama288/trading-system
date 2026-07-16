from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

import pytest

from research.signal_observation import h1_phase_a_coverage as coverage


class FakeResponse:
    def __init__(self, url: str, body: bytes, *, status: int = 200, headers: dict[str, str] | None = None) -> None:
        self._url = url
        self._body = body
        self._status = status
        self.headers = {"Content-Type": "application/json; charset=utf-8", **(headers or {})}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def getcode(self) -> int:
        return self._status

    def geturl(self) -> str:
        return self._url

    def read(self, amount: int = -1) -> bytes:
        return self._body if amount < 0 else self._body[:amount]


class FakeOpener:
    def __init__(self, handler: Callable[[urllib.request.Request, int], FakeResponse]) -> None:
        self.handler = handler
        self.calls: list[tuple[str, int]] = []

    def open(self, request: urllib.request.Request, *, timeout: int) -> FakeResponse:
        self.calls.append((request.full_url, timeout))
        return self.handler(request, len(self.calls))


def _json_response(request: urllib.request.Request, payload: Any) -> FakeResponse:
    body = json.dumps(payload, separators=(",", ":")).encode()
    return FakeResponse(request.full_url, body, headers={"Content-Length": str(len(body))})


def _row(spec: coverage.VenueSpec, timestamp: int) -> dict[str, str]:
    return {
        spec.contract_field: spec.contract_id,
        spec.timestamp_field: str(timestamp),
        "fundingRate": "DO_NOT_LEAK_SENTINEL",
    }


def _payload(spec: coverage.VenueSpec, timestamps: list[int]) -> Any:
    rows = [_row(spec, timestamp) for timestamp in timestamps]
    if spec.venue == "binance":
        return rows
    if spec.venue == "bitget":
        return {"code": "00000", "data": rows}
    if spec.venue == "bybit":
        return {"retCode": 0, "result": {"category": "linear", "list": rows}}
    return {"code": "0", "data": rows}


def _full_timestamps(descending: bool) -> list[int]:
    hour = 60 * 60 * 1000
    values = [
        coverage.TARGET_START_MS,
        coverage.WINDOWS[0][2] - 8 * hour,
        coverage.WINDOWS[1][1],
        coverage.WINDOWS[1][2] - 8 * hour,
        coverage.WINDOWS[2][1],
        coverage.TARGET_END_MS - 8 * hour,
    ]
    return sorted(values, reverse=descending)


def _dense_timestamps(descending: bool = False) -> list[int]:
    step = 8 * 60 * 60 * 1000
    return sorted(
        range(coverage.TARGET_START_MS, coverage.TARGET_END_MS, step),
        reverse=descending,
    )


@pytest.mark.parametrize(
    ("venue", "expected"),
    [
        ("binance", {"symbol", "startTime", "endTime", "limit"}),
        ("bitget", {"symbol", "productType", "pageSize", "pageNo"}),
        ("bybit", {"category", "symbol", "endTime", "limit"}),
        ("okx", {"instId", "after", "limit"}),
    ],
)
def test_frozen_request_contracts(venue: str, expected: set[str]) -> None:
    spec = coverage._SPEC_BY_VENUE[venue]
    cursor = None if venue == "bitget" else coverage._initial_cursor(spec)
    request = coverage.build_request(spec, 1, cursor)
    parsed = urllib.parse.urlsplit(request.url)
    query = dict(urllib.parse.parse_qsl(parsed.query))

    assert parsed.scheme == "https"
    assert parsed.hostname == spec.host
    assert parsed.path == spec.path
    assert set(query) == expected
    assert query.get("symbol", query.get("instId")) == spec.contract_id
    assert query.get("limit", query.get("pageSize")) == {
        "binance": "1000",
        "bitget": "100",
        "bybit": "200",
        "okx": "400",
    }[venue]


def test_exact_global_request_budget_and_page_bounds() -> None:
    assert sum(spec.max_pages for spec in coverage.VENUE_SPECS) == 80
    for spec in coverage.VENUE_SPECS:
        cursor = None if spec.venue == "bitget" else coverage._initial_cursor(spec)
        coverage.build_request(spec, spec.max_pages, cursor)
        with pytest.raises(coverage.CoverageFailure, match="page_budget_exceeded"):
            coverage.build_request(spec, spec.max_pages + 1, cursor)


def test_cursor_algorithms_and_non_progress() -> None:
    binance = coverage._SPEC_BY_VENUE["binance"]
    bybit = coverage._SPEC_BY_VENUE["bybit"]
    assert coverage.next_cursor(binance, 100, [100, 200]) == 201
    assert coverage.next_cursor(bybit, 300, [250, 200]) == 199
    with pytest.raises(coverage.CoverageFailure, match="non_progress"):
        coverage.next_cursor(binance, 300, [100, 200])
    with pytest.raises(coverage.CoverageFailure, match="non_progress"):
        coverage.next_cursor(bybit, 100, [250, 200])


@pytest.mark.parametrize("venue", ["binance", "bitget", "bybit", "okx"])
def test_all_schema_algorithms_accept_frozen_contract(venue: str) -> None:
    spec = coverage._SPEC_BY_VENUE[venue]
    timestamps = _full_timestamps(spec.direction == "descending")
    rows = coverage._rows_for(venue, _payload(spec, timestamps))
    parsed, fields = coverage.validate_rows(spec, rows, set())

    assert parsed == timestamps
    assert spec.contract_field in fields
    assert spec.timestamp_field in fields


def test_duplicate_timestamp_is_rejected_across_pages() -> None:
    spec = coverage._SPEC_BY_VENUE["binance"]
    seen: set[int] = set()
    coverage.validate_rows(spec, [_row(spec, 100)], seen)
    with pytest.raises(coverage.CoverageFailure, match="duplicate_timestamp"):
        coverage.validate_rows(spec, [_row(spec, 100)], seen)


@pytest.mark.parametrize("venue", ["binance", "okx"])
def test_wrong_order_is_rejected(venue: str) -> None:
    spec = coverage._SPEC_BY_VENUE[venue]
    wrong = [200, 100] if spec.direction == "ascending" else [100, 200]
    with pytest.raises(coverage.CoverageFailure, match="unexpected_order"):
        coverage.validate_rows(spec, [_row(spec, value) for value in wrong], set())


def test_contract_mismatch_is_rejected() -> None:
    spec = coverage._SPEC_BY_VENUE["okx"]
    row = _row(spec, coverage.TARGET_START_MS)
    row[spec.contract_field] = "OTHER"
    with pytest.raises(coverage.CoverageFailure, match="contract_mismatch"):
        coverage.validate_rows(spec, [row], set())


def test_structural_coverage_uses_all_three_locked_windows() -> None:
    full = _dense_timestamps()
    result = coverage.structural_coverage(full)
    assert result == {"discovery": True, "validation": True, "holdout": True, "target": True}

    gap_start = coverage.WINDOWS[1][1] + coverage.MAX_ALLOWED_GAP_MS
    with_gap = [
        value
        for value in full
        if not gap_start <= value <= gap_start + coverage.MAX_ALLOWED_GAP_MS
    ]
    result = coverage.structural_coverage(with_gap)
    assert coverage.max_gap_ms(with_gap) > coverage.MAX_ALLOWED_GAP_MS
    assert result["validation"] is False
    assert result["target"] is False

    boundary_only = _full_timestamps(False)
    assert coverage.structural_coverage(boundary_only)["target"] is False


def test_per_response_and_cumulative_byte_budgets() -> None:
    budget = coverage._Budget(bytes=coverage.MAX_CUMULATIVE_BYTES - 1)
    response = FakeResponse("https://example.invalid", b"xx")
    with pytest.raises(coverage.CoverageFailure, match="cumulative_byte_budget_exceeded"):
        coverage._read_bounded(response, budget)

    oversized = FakeResponse(
        "https://example.invalid",
        b"",
        headers={"Content-Length": str(coverage.MAX_RESPONSE_BYTES + 1)},
    )
    with pytest.raises(coverage.CoverageFailure, match="response_too_large"):
        coverage._read_bounded(oversized, coverage._Budget())


def test_complete_synthetic_acquisition_persists_opaque_page_create_only(tmp_path: Path) -> None:
    spec = coverage._SPEC_BY_VENUE["binance"]

    def handler(request: urllib.request.Request, call: int) -> FakeResponse:
        assert call == 1
        return _json_response(request, _payload(spec, _dense_timestamps()))

    output = coverage.run_acquisition("synthetic_1", output_root=tmp_path, opener=FakeOpener(handler), specs=[spec])
    record = output[0]
    raw = tmp_path / "synthetic_1" / "raw" / "binance" / "page_0001.json"

    assert record["status"] == "PASS"
    assert record["page_count"] == 1
    assert record["target_coverage"] is True
    assert len(record["raw_pages"][0]["sha256"]) == 64
    assert "DO_NOT_LEAK_SENTINEL" in raw.read_text(encoding="utf-8")
    assert "DO_NOT_LEAK_SENTINEL" not in json.dumps(record)
    with pytest.raises(coverage.CoverageFailure, match="acquisition_exists"):
        coverage.run_acquisition("synthetic_1", output_root=tmp_path, opener=FakeOpener(handler), specs=[spec])


def test_okx_insufficient_retention_is_structural_fail(tmp_path: Path) -> None:
    spec = coverage._SPEC_BY_VENUE["okx"]
    responses = [
        _payload(spec, [coverage.TARGET_END_MS - 8 * 60 * 60 * 1000]),
        _payload(spec, []),
    ]

    def handler(request: urllib.request.Request, call: int) -> FakeResponse:
        return _json_response(request, responses[call - 1])

    output = coverage.run_acquisition("okx_short", output_root=tmp_path, opener=FakeOpener(handler), specs=[spec])
    record = output[0]

    assert record["status"] == "FAIL"
    assert record["sanitized_code"] == "insufficient_coverage"
    assert record["http_status"] == 200
    assert record["page_count"] == 2
    assert record["target_coverage"] is False


def test_injected_opener_never_uses_real_page_sleep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = coverage._SPEC_BY_VENUE["okx"]
    responses = [
        _payload(spec, [coverage.TARGET_END_MS - 8 * 60 * 60 * 1000]),
        _payload(spec, []),
    ]

    def handler(request: urllib.request.Request, call: int) -> FakeResponse:
        return _json_response(request, responses[call - 1])

    def forbidden_sleep(seconds: float) -> None:
        raise AssertionError(f"synthetic sleep called: {seconds}")

    monkeypatch.setattr(coverage.time, "sleep", forbidden_sleep)
    output = coverage.run_acquisition(
        "no_synthetic_sleep",
        output_root=tmp_path,
        opener=FakeOpener(handler),
        specs=[spec],
    )

    assert output[0]["page_count"] == 2
    assert output[0]["status"] == "FAIL"


def test_exception_body_and_funding_values_never_leak(tmp_path: Path) -> None:
    sentinel = "SECRET_EXCEPTION_AND_FUNDING_VALUE"

    def handler(request: urllib.request.Request, call: int) -> FakeResponse:
        raise urllib.error.URLError(sentinel)

    spec = coverage._SPEC_BY_VENUE["bybit"]
    output = coverage.run_acquisition("no_leak", output_root=tmp_path, opener=FakeOpener(handler), specs=[spec])
    encoded = json.dumps(output)

    assert output[0]["status"] == "ERROR"
    assert output[0]["sanitized_code"] == "transport_error"
    assert sentinel not in encoded
    assert sentinel not in (tmp_path / "no_leak" / "metadata.json").read_text(encoding="utf-8")


def test_unexpected_programmer_exception_propagates(tmp_path: Path) -> None:
    def handler(request: urllib.request.Request, call: int) -> FakeResponse:
        raise RuntimeError("PROGRAMMER_ERROR_SENTINEL")

    spec = coverage._SPEC_BY_VENUE["bybit"]
    with pytest.raises(RuntimeError, match="PROGRAMMER_ERROR_SENTINEL"):
        coverage.run_acquisition(
            "programmer_error",
            output_root=tmp_path,
            opener=FakeOpener(handler),
            specs=[spec],
        )


def test_unexpected_content_type_is_sanitized(tmp_path: Path) -> None:
    spec = coverage._SPEC_BY_VENUE["binance"]

    def handler(request: urllib.request.Request, call: int) -> FakeResponse:
        return FakeResponse(
            request.full_url,
            b"SECRET_HTML_BODY",
            headers={"Content-Type": "text/html"},
        )

    output = coverage.run_acquisition(
        "bad_content_type",
        output_root=tmp_path,
        opener=FakeOpener(handler),
        specs=[spec],
    )
    assert output[0]["sanitized_code"] == "unexpected_content_type"
    assert "SECRET_HTML_BODY" not in json.dumps(output)


def test_bitget_cross_page_progress_must_be_strictly_older() -> None:
    spec = coverage._SPEC_BY_VENUE["bitget"]
    previous = coverage.validate_page_progress(spec, None, [300, 250, 200], None)
    assert coverage.validate_page_progress(
        spec, None, [199, 150, 100], previous
    ) == (100, 199)
    with pytest.raises(coverage.CoverageFailure, match="non_progress"):
        coverage.validate_page_progress(spec, None, [200, 150, 100], previous)


@pytest.mark.parametrize(
    ("venue", "cursor", "timestamps"),
    [
        ("binance", 100, [99]),
        ("bybit", 100, [101]),
        ("okx", 100, [100]),
    ],
)
def test_cursor_venues_reject_rows_on_wrong_requested_side(
    venue: str, cursor: int, timestamps: list[int]
) -> None:
    spec = coverage._SPEC_BY_VENUE[venue]
    with pytest.raises(coverage.CoverageFailure, match="non_progress"):
        coverage.validate_page_progress(spec, cursor, timestamps, None)


def test_redirect_query_mutation_and_auth_are_rejected(tmp_path: Path) -> None:
    spec = coverage._SPEC_BY_VENUE["binance"]

    def redirected(request: urllib.request.Request, call: int) -> FakeResponse:
        return FakeResponse(request.full_url + "&extra=1", b"[]")

    output = coverage.run_acquisition("redirected", output_root=tmp_path, opener=FakeOpener(redirected), specs=[spec])
    assert output[0]["sanitized_code"] == "unexpected_final_source"

    def auth(request: urllib.request.Request, call: int) -> FakeResponse:
        return FakeResponse(request.full_url, b"PRIVATE BODY", status=403)

    output = coverage.run_acquisition("auth", output_root=tmp_path, opener=FakeOpener(auth), specs=[spec])
    assert output[0]["sanitized_code"] == "auth_challenge"
    assert "PRIVATE BODY" not in json.dumps(output)


@pytest.mark.parametrize("bad_id", ["Upper", "has space", "../escape", "", "a.b"])
def test_acquisition_id_rejects_unsafe_values(tmp_path: Path, bad_id: str) -> None:
    with pytest.raises(coverage.CoverageFailure, match="invalid_acquisition_id"):
        coverage.run_acquisition(bad_id, output_root=tmp_path, opener=FakeOpener(lambda request, call: FakeResponse(request.full_url, b"[]")), specs=[])
