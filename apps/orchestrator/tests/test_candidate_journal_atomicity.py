from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.orchestrator.application.create_candidate import create_candidate_use_case
from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from libs.db.base import Base
from libs.db.models.journal_event import JournalEventModel
from libs.db.models.trade_candidate import TradeCandidateModel
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


class _NoopJournalClient:
    def write(self, payload: dict) -> None:
        return None


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _make_signal() -> SignalDecision:
    return SignalDecision(
        signal_id="sig_001",
        status=SignalStatus.CANDIDATE,
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        setup_type="breakout_retest",
        entry_zone=EntryZone(min=100.0, max=101.0),
        stop_loss=95.0,
        take_profit=[110.0],
        confidence=0.6,
        reasoning_summary="ok",
    )


def _make_risk() -> RiskDecision:
    return RiskDecision(
        risk_id="risk_001",
        signal_id="sig_001",
        symbol="BTCUSDT",
        approved=True,
        position_size=1.0,
        notional_usdt=100.0,
        max_loss_usdt=5.0,
        risk_pct_of_equity=0.5,
        leverage=1.0,
        portfolio_exposure_pct=10.0,
        daily_loss_limit_status="ok",
        drawdown_lock=False,
        kill_switch_required=False,
        reason_codes=[RiskReasonCode.RISK_OK],
    )


def _make_review() -> ReviewDecision:
    candidate = ExecutionCandidate(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type="limit",
        entry_price=101.0,
        quantity=1.0,
        stop_loss=95.0,
        take_profit=[110.0],
        time_in_force="GTC",
    )
    return ReviewDecision(
        review_id="rev_001",
        signal_id="sig_001",
        risk_id="risk_001",
        passed=True,
        anomaly_flags=[],
        review_notes="ok",
        execution_candidate=candidate,
    )


def test_candidate_created_is_persisted_with_matching_journal_event(db: Session) -> None:
    repo = TradeCandidateRepository(db)
    result = create_candidate_use_case(
        repo=repo,
        journal_client=_NoopJournalClient(),
        signal=_make_signal(),
        risk=_make_risk(),
        review=_make_review(),
        correlation_id="corr_001",
        ttl_seconds=120,
    )
    assert result["ok"] is True
    candidate_id = result["candidate_id"]

    cand = db.execute(
        select(TradeCandidateModel).where(TradeCandidateModel.candidate_id == candidate_id)
    ).scalar_one_or_none()
    assert cand is not None

    evt = db.get(JournalEventModel, f"evt_candidate_{candidate_id}")
    assert evt is not None
    assert evt.event_type == "candidate_created"


def test_candidate_is_not_persisted_if_journal_event_insert_fails(db: Session, monkeypatch) -> None:
    # Force deterministic candidate_id so we can pre-insert a colliding journal event_id.
    from apps.orchestrator.application import create_candidate as mod

    class _FakeUuid:
        hex = "abc"

    monkeypatch.setattr(mod, "uuid4", lambda: _FakeUuid())

    candidate_id = "cand_abc"
    db.add(
        JournalEventModel(
            event_id=f"evt_candidate_{candidate_id}",
            event_type="candidate_created",
            severity="info",
            correlation_id="corr_pre",
            payload={"note": "preexisting"},
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    repo = TradeCandidateRepository(db)
    result = create_candidate_use_case(
        repo=repo,
        journal_client=_NoopJournalClient(),
        signal=_make_signal(),
        risk=_make_risk(),
        review=_make_review(),
        correlation_id="corr_002",
        ttl_seconds=120,
    )
    assert result["ok"] is False
    assert result["code"] == "JOURNAL_WRITE_FAILED"

    cand = db.execute(
        select(TradeCandidateModel).where(TradeCandidateModel.candidate_id == candidate_id)
    ).scalar_one_or_none()
    assert cand is None


def test_evaluate_is_idempotent_on_signal_id(db: Session) -> None:
    repo = TradeCandidateRepository(db)
    first = create_candidate_use_case(
        repo=repo,
        journal_client=_NoopJournalClient(),
        signal=_make_signal(),
        risk=_make_risk(),
        review=_make_review(),
        correlation_id="corr_001",
        ttl_seconds=120,
    )
    second = create_candidate_use_case(
        repo=repo,
        journal_client=_NoopJournalClient(),
        signal=_make_signal(),
        risk=_make_risk(),
        review=_make_review(),
        correlation_id="corr_002",
        ttl_seconds=120,
    )

    assert first["ok"] is True
    assert second["ok"] is True
    assert second["code"] == "CANDIDATE_EXISTS"
    assert second["candidate_id"] == first["candidate_id"]

    rows = db.execute(select(TradeCandidateModel)).scalars().all()
    assert len(rows) == 1
