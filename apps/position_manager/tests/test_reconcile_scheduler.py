from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

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

    async def fake_reconcile_positions_use_case(*, repo, journal_client, alert_client, req):
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


# ---------------------------------------------------------------------------
# Scheduler loop behaviour tests
# ---------------------------------------------------------------------------


class _RecordingAlertClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def notify(self, payload: dict) -> None:
        self.calls.append(payload)


def _success_result() -> dict:
    return {"ok": True, "reconciled_count": 0, "open_positions": [], "correlation_id": "c"}


@pytest.mark.asyncio
async def test_scheduler_loop_reraises_when_continue_on_error_false(monkeypatch):
    """First failure must propagate when continue_on_error=False."""
    async def failing_to_thread(func, /, *args, **kwargs):
        raise RuntimeError("boom")

    async def noop_sleep(seconds: float) -> None:
        pass

    monkeypatch.setattr(asyncio, "to_thread", failing_to_thread)
    monkeypatch.setattr(asyncio, "sleep", noop_sleep)

    with pytest.raises(RuntimeError, match="boom"):
        await scheduler.run_reconcile_scheduler_loop(
            session_factory=object(),
            journal_client=object(),
            alert_client=_RecordingAlertClient(),
            market_fetcher=object(),
            interval_seconds=1.0,
            timeframe="1m",
            candle_limit=2,
            continue_on_error=False,
        )


@pytest.mark.asyncio
async def test_scheduler_loop_escalation_alert_emitted_at_threshold(monkeypatch):
    """After _ESCALATION_THRESHOLD consecutive failures alert_client.notify must be called."""
    alert_client = _RecordingAlertClient()
    stop = asyncio.Event()
    call_count = 0

    async def failing_to_thread(func, /, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("simulated db failure")

    async def recording_sleep(seconds: float) -> None:
        if call_count >= scheduler._ESCALATION_THRESHOLD:
            stop.set()

    monkeypatch.setattr(asyncio, "to_thread", failing_to_thread)
    monkeypatch.setattr(asyncio, "sleep", recording_sleep)

    await scheduler.run_reconcile_scheduler_loop(
        session_factory=object(),
        journal_client=object(),
        alert_client=alert_client,
        market_fetcher=object(),
        interval_seconds=1.0,
        timeframe="1m",
        candle_limit=2,
        continue_on_error=True,
        stop_event=stop,
    )

    assert len(alert_client.calls) >= 1
    payload = alert_client.calls[0]
    assert payload["event_type"] == "scheduler_failure_escalation"
    assert payload["consecutive_failures"] >= scheduler._ESCALATION_THRESHOLD
    assert "error" in payload


@pytest.mark.asyncio
async def test_scheduler_loop_no_escalation_before_threshold(monkeypatch):
    """Fewer than _ESCALATION_THRESHOLD consecutive failures must not emit an alert."""
    alert_client = _RecordingAlertClient()
    stop = asyncio.Event()
    call_count = 0

    async def failing_to_thread(func, /, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("transient failure")

    async def recording_sleep(seconds: float) -> None:
        if call_count >= scheduler._ESCALATION_THRESHOLD - 1:
            stop.set()

    monkeypatch.setattr(asyncio, "to_thread", failing_to_thread)
    monkeypatch.setattr(asyncio, "sleep", recording_sleep)

    await scheduler.run_reconcile_scheduler_loop(
        session_factory=object(),
        journal_client=object(),
        alert_client=alert_client,
        market_fetcher=object(),
        interval_seconds=1.0,
        timeframe="1m",
        candle_limit=2,
        continue_on_error=True,
        stop_event=stop,
    )

    assert len(alert_client.calls) == 0


@pytest.mark.asyncio
async def test_scheduler_loop_consecutive_failures_reset_on_success(monkeypatch):
    """A successful cycle resets the counter — 2 fails + success + 2 fails must not escalate."""
    alert_client = _RecordingAlertClient()
    stop = asyncio.Event()
    call_count = 0
    outcomes = iter([
        RuntimeError("fail 1"),
        RuntimeError("fail 2"),
        None,               # success
        RuntimeError("fail 3"),
        RuntimeError("fail 4"),
    ])

    async def controlled_to_thread(func, /, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        outcome = next(outcomes, None)
        if isinstance(outcome, Exception):
            raise outcome
        return _success_result()

    async def recording_sleep(seconds: float) -> None:
        if call_count >= 5:
            stop.set()

    monkeypatch.setattr(asyncio, "to_thread", controlled_to_thread)
    monkeypatch.setattr(asyncio, "sleep", recording_sleep)

    await scheduler.run_reconcile_scheduler_loop(
        session_factory=object(),
        journal_client=object(),
        alert_client=alert_client,
        market_fetcher=object(),
        interval_seconds=1.0,
        timeframe="1m",
        candle_limit=2,
        continue_on_error=True,
        stop_event=stop,
    )

    assert len(alert_client.calls) == 0


@pytest.mark.asyncio
async def test_scheduler_loop_backoff_doubles_on_consecutive_failures(monkeypatch):
    """Sleep duration must double with each consecutive failure, capped at MAX_BACKOFF_FACTOR."""
    sleep_durations: list[float] = []
    stop = asyncio.Event()
    call_count = 0
    interval = 10.0

    async def failing_to_thread(func, /, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("persistent failure")

    async def recording_sleep(seconds: float) -> None:
        sleep_durations.append(seconds)
        if call_count >= 3:
            stop.set()

    monkeypatch.setattr(asyncio, "to_thread", failing_to_thread)
    monkeypatch.setattr(asyncio, "sleep", recording_sleep)

    await scheduler.run_reconcile_scheduler_loop(
        session_factory=object(),
        journal_client=object(),
        alert_client=_RecordingAlertClient(),
        market_fetcher=object(),
        interval_seconds=interval,
        timeframe="1m",
        candle_limit=2,
        continue_on_error=True,
        stop_event=stop,
    )

    # failure 1: interval * 2^0 = 10.0
    # failure 2: interval * 2^1 = 20.0
    # failure 3: interval * 2^2 = 40.0
    assert sleep_durations[0] == interval
    assert sleep_durations[1] == interval * 2
    assert sleep_durations[2] == interval * 4
