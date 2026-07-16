from __future__ import annotations

import json
import urllib.request
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from research.signal_observation import h1_phase_a_probe as probe


SENTINELS = (
    "RATE_SENTINEL_91.2345",
    "PRICE_SENTINEL_987654.321",
    "VOLUME_SENTINEL_123456789",
)


def _payloads() -> dict[str, bytes]:
    rate, price, volume = SENTINELS
    return {
        "binance": json.dumps(
            [
                {
                    "symbol": "BTCUSDT",
                    "fundingTime": 1_700_000_000_000,
                    "fundingRate": rate,
                    "markPrice": price,
                    "volume": volume,
                },
                {
                    "symbol": "BTCUSDT",
                    "fundingTime": 1_700_028_800_000,
                    "fundingRate": rate,
                    "markPrice": price,
                },
            ]
        ).encode(),
        "bitget": json.dumps(
            {
                "code": "00000",
                "msg": "success",
                "requestTime": 1_700_028_800_001,
                "data": [
                    {
                        "symbol": "BTCUSDT",
                        "fundingTime": "1700000000000",
                        "fundingRate": rate,
                        "markPrice": price,
                    }
                ],
            }
        ).encode(),
        "bybit": json.dumps(
            {
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "category": "linear",
                    "list": [
                        {
                            "symbol": "BTCUSDT",
                            "fundingRateTimestamp": "1700000000000",
                            "fundingRate": rate,
                            "markPrice": price,
                        }
                    ],
                },
                "time": 1_700_028_800_002,
            }
        ).encode(),
        "okx": json.dumps(
            {
                "code": "0",
                "msg": "",
                "data": [
                    {
                        "instId": "BTC-USDT-SWAP",
                        "fundingTime": "1700000000000",
                        "fundingRate": rate,
                        "realizedRate": rate,
                        "markPx": price,
                    }
                ],
            }
        ).encode(),
    }


class FakeResponse:
    def __init__(
        self,
        body: bytes,
        url: str,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.body = body
        self.url = url
        self.status = status
        self.headers = headers or {"Content-Length": str(len(body))}

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def getcode(self) -> int:
        return self.status

    def geturl(self) -> str:
        return self.url

    def read(self, amount: int = -1) -> bytes:
        return self.body if amount < 0 else self.body[:amount]


class FakeOpener:
    def __init__(self, payloads: dict[str, bytes]) -> None:
        self.payloads = payloads
        self.calls: list[tuple[str, int]] = []

    def open(
        self, request: urllib.request.Request, *, timeout: int
    ) -> FakeResponse:
        url = request.full_url
        spec = next(spec for spec in probe.REQUEST_SPECS if spec.url == url)
        self.calls.append((url, timeout))
        return FakeResponse(self.payloads[spec.venue], url)


def test_all_four_envelopes_emit_only_structural_metadata(tmp_path: Path) -> None:
    opener = FakeOpener(_payloads())

    records = probe.run_probe("fixture_001", output_root=tmp_path, opener=opener)

    assert [record["venue"] for record in records] == [
        "binance",
        "bitget",
        "bybit",
        "okx",
    ]
    assert all(record["structural_status"] == "valid" for record in records)
    assert len(opener.calls) == 4
    assert all(timeout == 15 for _, timeout in opener.calls)
    assert all(url.startswith("https://") for url, _ in opener.calls)
    assert records[0]["row_count"] == 2
    assert records[0]["min_funding_timestamp_utc"] == "2023-11-14T22:13:20Z"
    assert records[0]["max_funding_timestamp_utc"] == "2023-11-15T06:13:20Z"

    rendered = json.dumps(records)
    persisted = (tmp_path / "fixture_001" / "metadata.json").read_text()
    for sentinel in SENTINELS:
        assert sentinel not in rendered
        assert sentinel not in persisted
    for venue, body in _payloads().items():
        assert (tmp_path / "fixture_001" / "raw" / f"{venue}.json").read_bytes() == body


def test_output_schema_is_exact(tmp_path: Path) -> None:
    records = probe.run_probe(
        "schema", output_root=tmp_path, opener=FakeOpener(_payloads())
    )

    assert set(records[0]) == {
        "venue",
        "structural_status",
        "http_status",
        "byte_count",
        "row_count",
        "field_names",
        "min_funding_timestamp_utc",
        "max_funding_timestamp_utc",
        "contract_id",
        "sanitized_error_code",
    }


def test_cli_stdout_never_contains_sentinel_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    records = probe.run_probe(
        "stdout_fixture", output_root=tmp_path, opener=FakeOpener(_payloads())
    )
    monkeypatch.setattr(probe, "run_probe", lambda acquisition_id: records)

    assert probe.main(["--acquisition-id", "stdout_fixture"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == records
    for sentinel in SENTINELS:
        assert sentinel not in captured.out

@pytest.mark.parametrize(
    ("field", "value"),
    (("host", "evil.example"), ("path", "/private/funding")),
)
def test_host_and_path_are_frozen_allowlist(
    tmp_path: Path, field: str, value: str
) -> None:
    original = probe.REQUEST_SPECS[0]
    altered = replace(original, **{field: value})
    opener = FakeOpener(_payloads())

    records = probe.run_probe(
        f"bad_{field}", output_root=tmp_path, opener=opener, specs=(altered,)
    )

    assert records[0]["sanitized_error_code"] == "source_not_allowlisted"
    assert opener.calls == []


def test_oversized_content_length_fails_without_reading_values(tmp_path: Path) -> None:
    spec = probe.REQUEST_SPECS[0]

    class OversizedOpener:
        def open(self, request: urllib.request.Request, *, timeout: int) -> FakeResponse:
            return FakeResponse(
                b"not-read " + SENTINELS[0].encode(),
                spec.url,
                headers={"Content-Length": str(probe.MAX_RESPONSE_BYTES + 1)},
            )

    records = probe.run_probe(
        "oversized", output_root=tmp_path, opener=OversizedOpener(), specs=(spec,)
    )

    assert records[0]["sanitized_error_code"] == "response_too_large"
    assert SENTINELS[0] not in json.dumps(records)


def test_redirect_is_rejected_with_sanitized_error(tmp_path: Path) -> None:
    class RedirectOpener:
        def open(self, request: urllib.request.Request, *, timeout: int) -> Any:
            raise probe.ProbeFailure("redirect_rejected")

    records = probe.run_probe(
        "redirect",
        output_root=tmp_path,
        opener=RedirectOpener(),
        specs=(probe.REQUEST_SPECS[0],),
    )

    assert records[0]["sanitized_error_code"] == "redirect_rejected"
    assert records[0]["field_names"] == []


def test_unexpected_final_host_is_rejected(tmp_path: Path) -> None:
    spec = probe.REQUEST_SPECS[0]

    class ChangedFinalUrlOpener:
        def open(self, request: urllib.request.Request, *, timeout: int) -> FakeResponse:
            return FakeResponse(_payloads()[spec.venue], "https://evil.example/final")

    records = probe.run_probe(
        "final_host",
        output_root=tmp_path,
        opener=ChangedFinalUrlOpener(),
        specs=(spec,),
    )

    assert records[0]["sanitized_error_code"] == "unexpected_final_source"


def test_duplicate_timestamps_fail_without_value_leak(tmp_path: Path) -> None:
    spec = probe.REQUEST_SPECS[0]
    duplicate = json.dumps(
        [
            {
                "symbol": "BTCUSDT",
                "fundingTime": 1_700_000_000_000,
                "fundingRate": SENTINELS[0],
            },
            {
                "symbol": "BTCUSDT",
                "fundingTime": 1_700_000_000_000,
                "fundingRate": SENTINELS[0],
            },
        ]
    ).encode()
    opener = FakeOpener({spec.venue: duplicate})

    records = probe.run_probe(
        "duplicate", output_root=tmp_path, opener=opener, specs=(spec,)
    )

    assert records[0]["sanitized_error_code"] == "duplicate_timestamp"
    assert SENTINELS[0] not in json.dumps(records)


def test_unknown_schema_does_not_put_payload_in_exception_or_metadata(
    tmp_path: Path,
) -> None:
    spec = probe.REQUEST_SPECS[0]
    body = json.dumps({"unexpected": SENTINELS[0]}).encode()
    opener = FakeOpener({spec.venue: body})

    records = probe.run_probe(
        "unknown", output_root=tmp_path, opener=opener, specs=(spec,)
    )

    rendered = json.dumps(records)
    assert records[0]["sanitized_error_code"] == "unknown_schema"
    assert SENTINELS[0] not in rendered
    assert SENTINELS[0] not in (
        tmp_path / "unknown" / "metadata.json"
    ).read_text()


def test_atomic_create_refuses_existing_destination(tmp_path: Path) -> None:
    destination = tmp_path / "artifact.json"
    destination.write_bytes(b"owner-data")

    with pytest.raises(probe.ProbeFailure, match="^destination_exists$"):
        probe._atomic_create(destination, b"replacement")

    assert destination.read_bytes() == b"owner-data"


def test_acquisition_directory_is_create_only(tmp_path: Path) -> None:
    opener = FakeOpener(_payloads())
    probe.run_probe("same_id", output_root=tmp_path, opener=opener)

    with pytest.raises(probe.ProbeFailure, match="^acquisition_exists$"):
        probe.run_probe("same_id", output_root=tmp_path, opener=opener)


@pytest.mark.parametrize("value", ("", "UPPER", "space id", "../escape", "a/b"))
def test_invalid_acquisition_id_is_rejected(tmp_path: Path, value: str) -> None:
    with pytest.raises(probe.ProbeFailure, match="^invalid_acquisition_id$"):
        probe.run_probe(value, output_root=tmp_path, opener=FakeOpener(_payloads()))


def test_request_budget_is_finite(tmp_path: Path) -> None:
    specs = tuple(probe.REQUEST_SPECS[0] for _ in range(probe.MAX_REQUESTS + 1))

    with pytest.raises(probe.ProbeFailure, match="^request_budget_exceeded$"):
        probe.run_probe("budget", output_root=tmp_path, opener=FakeOpener({}), specs=specs)
