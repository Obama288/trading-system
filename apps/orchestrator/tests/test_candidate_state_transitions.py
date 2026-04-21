from datetime import datetime, timedelta, timezone

from apps.orchestrator.application.approve_candidate import approve_candidate_use_case
from apps.orchestrator.application.create_candidate import create_candidate_use_case
from apps.orchestrator.application.reject_candidate import reject_candidate_use_case
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


class DummyExecutionClient:
    def __init__(self, execution_id: str | None = "exe_001") -> None:
        self.execution_id = execution_id

    def place(self, *, candidate_id: str, execution_candidate: dict, correlation_id: str) -> dict:
        return {"ok": True, "data": {"execution_id": self.execution_id}}


class DummyJournalClient:
    def __init__(self) -> None:
        self.writes: list[dict] = []

    def write(self, payload: dict) -> None:
        self.writes.append(payload)


class DummyOperatorActionRepo:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(self, **kwargs):
        self.records.append(kwargs)
        return kwargs


class DummyCandidate:
    def __init__(self, status: str = "pending", expired: bool = False):
        self.candidate_id = "cand_001"
        self.status = status
        self.execution_payload_json = {"symbol": "BTCUSDT", "side": "buy"}
        self.ttl_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1) if expired else datetime.now(timezone.utc) + timedelta(seconds=120)


class DummyRepo:
    def __init__(self, candidate):
        self.candidate = candidate

    def create_candidate(self, **kwargs):
        class Row:
            candidate_id = kwargs["candidate_id"]
            status = "pending"
            ttl_expires_at = kwargs["ttl_expires_at"]
        return Row()

    def get_candidate(self, candidate_id: str):
        return self.candidate

    def expire_if_needed(self, model):
        if model.status == "pending" and model.ttl_expires_at <= datetime.now(timezone.utc):
            model.status = "expired"
        return model

    def approve_candidate(self, model, telegram_user_id: int):
        model.status = "approved"
        return model

    def reject_candidate(self, model, telegram_user_id: int):
        model.status = "rejected"
        return model

    def attach_execution(self, model, execution_id: str):
        model.execution_id = execution_id
        model.status = "submitted"
        return model


def make_signal() -> SignalDecision:
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


def make_risk() -> RiskDecision:
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


def make_review(passed: bool = True) -> ReviewDecision:
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
        passed=passed,
        anomaly_flags=[],
        review_notes="ok",
        execution_candidate=candidate if passed else None,
    )


def test_create_candidate_success_and_writes_journal():
    repo = DummyRepo(None)
    journal = DummyJournalClient()
    result = create_candidate_use_case(repo, journal, make_signal(), make_risk(), make_review(True), "corr_001", ttl_seconds=120)
    assert result["ok"] is True
    assert result["code"] == "CANDIDATE_CREATED"
    assert len(journal.writes) == 1


def test_approve_candidate_submits_execution_and_writes_audit_and_journal():
    repo = DummyRepo(DummyCandidate())
    journal = DummyJournalClient()
    audit = DummyOperatorActionRepo()
    result = approve_candidate_use_case(repo, DummyExecutionClient(), audit, journal, "cand_001", 123, "corr_001")
    assert result["ok"] is True
    assert result["execution_id"] == "exe_001"
    assert len(audit.records) == 1
    assert len(journal.writes) == 1


def test_approve_candidate_missing_execution_id_writes_failure_journal():
    repo = DummyRepo(DummyCandidate())
    journal = DummyJournalClient()
    audit = DummyOperatorActionRepo()
    result = approve_candidate_use_case(repo, DummyExecutionClient(execution_id=None), audit, journal, "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXECUTION_SUBMISSION_NO_ID"
    assert len(audit.records) == 1
    assert len(journal.writes) == 1
    assert journal.writes[0]["event_type"] == "candidate_approve_handoff_failed"


def test_approve_candidate_expired():
    repo = DummyRepo(DummyCandidate(expired=True))
    result = approve_candidate_use_case(repo, DummyExecutionClient(), DummyOperatorActionRepo(), DummyJournalClient(), "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXPIRED"


def test_reject_candidate_already_approved():
    repo = DummyRepo(DummyCandidate(status="approved"))
    result = reject_candidate_use_case(repo, DummyOperatorActionRepo(), DummyJournalClient(), "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "ALREADY_APPROVED"


def test_approve_candidate_not_found():
    repo = DummyRepo(None)
    result = approve_candidate_use_case(repo, DummyExecutionClient(), DummyOperatorActionRepo(), DummyJournalClient(), "cand_missing", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "NOT_FOUND"
