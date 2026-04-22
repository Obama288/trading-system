from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from libs.schemas.common import (
    EntryZone,
    ExecutionCandidate,
    OrderSide,
    ReviewDecision,
    RiskDecision,
    RiskReasonCode,
    SignalDecision,
    SignalStatus,
    TradeDirection,
)
from ops.paper_pipeline_runner import PipelineAccountState, _stale_threshold_seconds_for_timeframe, run_cycle


class DummyKillSwitchClient:
    def __init__(self, *, active: bool) -> None:
        self.active = active
        self.calls = 0

    async def get_status(self, correlation_id: str) -> dict:
        self.calls += 1
        return {
            "ok": True,
            "service": "kill-switch",
            "version": "v1",
            "correlation_id": correlation_id,
            "data": {
                "trading_enabled": not self.active,
                "kill_switch_active": self.active,
                "incident_code": "manual_halt" if self.active else None,
            },
            "error": None,
        }


class DummyMarketFetcher:
    def __init__(self, candles: list[dict]) -> None:
        self.candles = candles
        self.calls = 0

    def fetch_candles(self, symbol: str, timeframe: str, limit: int) -> list[dict]:
        self.calls += 1
        return self.candles


class DummyEvaluateClient:
    def __init__(self) -> None:
        self.calls = 0
        self.payloads = []

    async def evaluate(self, payload) -> dict:
        self.calls += 1
        self.payloads.append(payload)
        return {"ok": True, "data": {"candidate_id": "cand_001"}}


def make_candles(*, stale: bool = False) -> list[dict]:
    end = datetime.now(timezone.utc) - (timedelta(minutes=10) if stale else timedelta(seconds=5))
    start = end - timedelta(minutes=15 * 59)
    candles: list[dict] = []
    price = 100.0
    for index in range(60):
        timestamp = start + timedelta(minutes=15 * index)
        open_price = price
        close_price = price + 0.5
        candles.append(
            {
                "timestamp": timestamp,
                "open": open_price,
                "high": close_price + 0.5,
                "low": open_price - 0.5,
                "close": close_price,
                "session": "london_ny_overlap",
            }
        )
        price = close_price
    return candles


def make_candles_with_age(*, age_seconds: int, timeframe_minutes: int) -> list[dict]:
    end = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    start = end - timedelta(minutes=timeframe_minutes * 59)
    candles: list[dict] = []
    price = 100.0
    for index in range(60):
        timestamp = start + timedelta(minutes=timeframe_minutes * index)
        open_price = price
        close_price = price + 0.5
        candles.append(
            {
                "timestamp": timestamp,
                "open": open_price,
                "high": close_price + 0.5,
                "low": open_price - 0.5,
                "close": close_price,
                "session": "london_ny_overlap",
            }
        )
        price = close_price
    return candles


def make_signal() -> SignalDecision:
    return SignalDecision(
        signal_id="sig_001",
        status=SignalStatus.CANDIDATE,
        symbol="BTC-USDT",
        side=TradeDirection.LONG,
        setup_type="breakout_retest",
        entry_zone=EntryZone(min=100.0, max=101.0),
        stop_loss=95.0,
        take_profit=[110.0],
        confidence=0.6,
        invalidation=None,
        reasoning_summary="candidate",
    )


def make_risk() -> RiskDecision:
    return RiskDecision(
        risk_id="risk_sig_001",
        signal_id="sig_001",
        symbol="BTC-USDT",
        approved=True,
        position_size=1.0,
        notional_usdt=100.5,
        max_loss_usdt=5.0,
        risk_pct_of_equity=0.5,
        entry_price=100.5,
        leverage=1.0,
        portfolio_exposure_pct=0.0,
        daily_loss_limit_status="ok",
        drawdown_lock=False,
        kill_switch_required=False,
        reason_codes=[RiskReasonCode.RISK_OK],
    )


def make_review() -> ReviewDecision:
    return ReviewDecision(
        review_id="rev_001",
        signal_id="sig_001",
        risk_id="risk_sig_001",
        passed=True,
        anomaly_flags=[],
        review_notes="ok",
        execution_candidate=ExecutionCandidate(
            symbol="BTC-USDT",
            side=OrderSide.BUY,
            order_type="limit",
            entry_price=100.5,
            quantity=1.0,
            stop_loss=95.0,
            take_profit=[110.0],
            time_in_force="GTC",
        ),
    )


@pytest.mark.asyncio
async def test_run_cycle_skips_when_kill_switch_active():
    evaluate_client = DummyEvaluateClient()
    result = await run_cycle(
        symbol="BTC-USDT",
        timeframe="15m",
        candle_limit=60,
        kill_switch_client=DummyKillSwitchClient(active=True),
        market_fetcher=DummyMarketFetcher(make_candles()),
        evaluate_client=evaluate_client,
        account_state=PipelineAccountState(
            equity_usdt=1000.0,
            daily_pnl_usdt=0.0,
            portfolio_exposure_pct=0.0,
            open_positions=0,
        ),
    )

    assert result["candidate_created"] is False
    assert result["reason"] == "kill_switch_active"
    assert evaluate_client.calls == 0


@pytest.mark.asyncio
async def test_run_cycle_skips_stale_snapshot():
    evaluate_client = DummyEvaluateClient()
    result = await run_cycle(
        symbol="BTC-USDT",
        timeframe="15m",
        candle_limit=60,
        kill_switch_client=DummyKillSwitchClient(active=False),
        market_fetcher=DummyMarketFetcher(make_candles_with_age(age_seconds=1200, timeframe_minutes=15)),
        evaluate_client=evaluate_client,
        account_state=PipelineAccountState(
            equity_usdt=1000.0,
            daily_pnl_usdt=0.0,
            portfolio_exposure_pct=0.0,
            open_positions=0,
        ),
    )

    assert result["candidate_created"] is False
    assert result["reason"] == "stale_snapshot"
    assert evaluate_client.calls == 0


@pytest.mark.asyncio
async def test_run_cycle_1m_keeps_strict_stale_threshold():
    evaluate_client = DummyEvaluateClient()
    result = await run_cycle(
        symbol="BTC-USDT",
        timeframe="1m",
        candle_limit=60,
        kill_switch_client=DummyKillSwitchClient(active=False),
        market_fetcher=DummyMarketFetcher(make_candles_with_age(age_seconds=180, timeframe_minutes=1)),
        evaluate_client=evaluate_client,
        account_state=PipelineAccountState(
            equity_usdt=1000.0,
            daily_pnl_usdt=0.0,
            portfolio_exposure_pct=0.0,
            open_positions=0,
        ),
    )

    assert result["candidate_created"] is False
    assert result["reason"] == "stale_snapshot"
    assert evaluate_client.calls == 0


@pytest.mark.asyncio
async def test_run_cycle_5m_uses_expanded_freshness_threshold():
    evaluate_client = DummyEvaluateClient()
    result = await run_cycle(
        symbol="BTC-USDT",
        timeframe="5m",
        candle_limit=60,
        kill_switch_client=DummyKillSwitchClient(active=False),
        market_fetcher=DummyMarketFetcher(make_candles_with_age(age_seconds=300, timeframe_minutes=5)),
        evaluate_client=evaluate_client,
        account_state=PipelineAccountState(
            equity_usdt=1000.0,
            daily_pnl_usdt=0.0,
            portfolio_exposure_pct=0.0,
            open_positions=0,
        ),
        signal_evaluator=lambda snapshot: make_signal(),
        risk_evaluator=lambda req: make_risk().model_dump(mode="python", exclude={"risk_id", "signal_id", "symbol"}),
        review_evaluator=lambda signal, risk, snapshot, stale_threshold_seconds: make_review(),
    )

    assert result["candidate_created"] is True
    assert result["reason"] is None
    assert evaluate_client.calls == 1


@pytest.mark.asyncio
async def test_run_cycle_15m_uses_expanded_freshness_threshold():
    evaluate_client = DummyEvaluateClient()
    result = await run_cycle(
        symbol="BTC-USDT",
        timeframe="15m",
        candle_limit=60,
        kill_switch_client=DummyKillSwitchClient(active=False),
        market_fetcher=DummyMarketFetcher(make_candles_with_age(age_seconds=900, timeframe_minutes=15)),
        evaluate_client=evaluate_client,
        account_state=PipelineAccountState(
            equity_usdt=1000.0,
            daily_pnl_usdt=0.0,
            portfolio_exposure_pct=0.0,
            open_positions=0,
        ),
        signal_evaluator=lambda snapshot: make_signal(),
        risk_evaluator=lambda req: make_risk().model_dump(mode="python", exclude={"risk_id", "signal_id", "symbol"}),
        review_evaluator=lambda signal, risk, snapshot, stale_threshold_seconds: make_review(),
    )

    assert result["candidate_created"] is True
    assert result["reason"] is None
    assert evaluate_client.calls == 1


def test_unknown_timeframe_falls_back_to_config_threshold(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "ops.paper_pipeline_runner.load_all_configs",
        lambda: {"risk": {"market_data": {"stale_snapshot_threshold_seconds": 77}}},
    )

    assert _stale_threshold_seconds_for_timeframe("30m") == 77


@pytest.mark.asyncio
async def test_run_cycle_calls_orchestrator_for_valid_candidate():
    evaluate_client = DummyEvaluateClient()
    result = await run_cycle(
        symbol="BTC-USDT",
        timeframe="15m",
        candle_limit=60,
        kill_switch_client=DummyKillSwitchClient(active=False),
        market_fetcher=DummyMarketFetcher(make_candles()),
        evaluate_client=evaluate_client,
        account_state=PipelineAccountState(
            equity_usdt=1000.0,
            daily_pnl_usdt=0.0,
            portfolio_exposure_pct=0.0,
            open_positions=0,
        ),
        signal_evaluator=lambda snapshot: make_signal(),
        risk_evaluator=lambda req: make_risk().model_dump(mode="python", exclude={"risk_id", "signal_id", "symbol"}),
        review_evaluator=lambda signal, risk, snapshot, stale_threshold_seconds: make_review(),
    )

    assert result["candidate_created"] is True
    assert result["reason"] is None
    assert evaluate_client.calls == 1
    assert evaluate_client.payloads[0].signal.signal_id == "sig_001"
