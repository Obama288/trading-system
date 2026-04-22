from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from apps.position_manager.application import reconcile_scheduler as scheduler


@dataclass
class FakePosition:
    position_id: str
    execution_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    opened_at: datetime
    ttl_expires_at: datetime | None = None


class FakeFetcher:
    def __init__(self, close_by_symbol: dict[str, float]) -> None:
        self.close_by_symbol = close_by_symbol
        self.calls: list[tuple[str, str, int]] = []

    def fetch_candles(self, symbol: str, timeframe: str, *, limit: int = 2) -> list[dict]:
        self.calls.append((symbol, timeframe, limit))
        close = self.close_by_symbol[symbol]
        return [{"close": close, "timestamp": datetime.now(timezone.utc)}]


class FakeRepo:
    def __init__(self, positions: list[FakePosition]) -> None:
        self._positions = positions

    def list_open_positions(self) -> list[FakePosition]:
        return self._positions


def test_build_reconcile_request_reuses_symbol_price_once():
    now = datetime.now(timezone.utc)
    open_positions = [
        FakePosition("pos1", "exe1", "BTC-USDT", "long", 1.0, 100.0, now),
        FakePosition("pos2", "exe2", "BTC-USDT", "long", 2.0, 110.0, now),
    ]
    fetcher = FakeFetcher({"BTC-USDT": 123.45})

    req = scheduler.build_reconcile_request(
        open_positions=open_positions,
        market_fetcher=fetcher,
        timeframe="1m",
        candle_limit=3,
        correlation_id="corr_test",
    )

    assert len(req.exchange_positions) == 2
    assert req.exchange_positions[0].mark_price == 123.45
    assert req.exchange_positions[1].mark_price == 123.45
    assert fetcher.calls == [("BTC-USDT", "1m", 3)]


def test_run_reconcile_cycle_returns_empty_result_when_no_open_positions():
    repo = FakeRepo([])
    fetcher = FakeFetcher({})
    result = scheduler.run_reconcile_cycle(
        repo=repo,  # type: ignore[arg-type]
        journal_client=object(),
        alert_client=object(),
        market_fetcher=fetcher,
        timeframe="1m",
        candle_limit=2,
        correlation_id="corr_no_positions",
    )

    assert result["ok"] is True
    assert result["reconciled_count"] == 0
    assert result["results"] == []
    assert result["open_positions"] == []
    assert result["correlation_id"] == "corr_no_positions"
    assert fetcher.calls == []


def test_run_reconcile_cycle_calls_reconcile_with_generated_snapshots(monkeypatch):
    now = datetime.now(timezone.utc)
    repo = FakeRepo(
        [
            FakePosition("pos1", "exe1", "BTC-USDT", "long", 1.5, 100.0, now),
            FakePosition("pos2", "exe2", "ETH-USDT", "short", 2.0, 200.0, now),
        ]
    )
    fetcher = FakeFetcher({"BTC-USDT": 101.0, "ETH-USDT": 199.0})
    captured: dict = {}

    def fake_reconcile_positions_use_case(*, repo, journal_client, alert_client, req):
        captured["req"] = req
        return {"ok": True, "code": "RECONCILED", "reconciled_count": 0, "results": [], "open_positions": []}

    monkeypatch.setattr(scheduler, "reconcile_positions_use_case", fake_reconcile_positions_use_case)

    result = scheduler.run_reconcile_cycle(
        repo=repo,  # type: ignore[arg-type]
        journal_client=object(),
        alert_client=object(),
        market_fetcher=fetcher,
        timeframe="5m",
        candle_limit=4,
        correlation_id="corr_capture",
    )

    req = captured["req"]
    assert req.correlation_id == "corr_capture"
    assert len(req.exchange_positions) == 2
    assert req.exchange_positions[0].status == "open"
    assert req.exchange_positions[0].mark_price == 101.0
    assert req.exchange_positions[1].mark_price == 199.0
    assert result["correlation_id"] == "corr_capture"
