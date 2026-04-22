import os
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session

from apps.orchestrator.application.approve_candidate import approve_candidate_use_case
from apps.orchestrator.application.evaluate_pipeline import evaluate_pipeline_use_case
from apps.orchestrator.application.list_pending_candidates import list_pending_candidates_use_case
from apps.orchestrator.application.reject_candidate import reject_candidate_use_case
from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from apps.orchestrator.infrastructure.execution_client import HttpExecutionClient
from apps.orchestrator.infrastructure.journal_client import HttpJournalClient
from apps.orchestrator.schemas.pipeline_requests import (
    ApproveCandidateRequest,
    EvaluatePipelineRequest,
    RejectCandidateRequest,
)
from libs.clients.kill_switch_client import HttpKillSwitchClient
from libs.db.repositories.operator_action_repo import OperatorActionRepository
from libs.db.session import get_db
from libs.logging.context import set_correlation_id

app = FastAPI(title="orchestrator")
EXECUTION_CLIENT = HttpExecutionClient(
    base_url=os.getenv("EXECUTION_SERVICE_BASE_URL", "http://execution-service:8000")
)
JOURNAL_CLIENT = HttpJournalClient(
    base_url=os.getenv("JOURNAL_SERVICE_BASE_URL", "http://journal-ingest:8000")
)
KILL_SWITCH_CLIENT = HttpKillSwitchClient(
    base_url=os.getenv("KILL_SWITCH_BASE_URL", "http://kill-switch:8000")
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
    set_correlation_id(corr)
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = corr
    return response


@app.get("/health")
def health() -> dict:
    return {"service": "orchestrator", "status": "healthy"}


@app.post("/v1/pipeline/evaluate")
def evaluate_pipeline(req: EvaluatePipelineRequest, db: Session = Depends(get_db)) -> dict:
    repo = TradeCandidateRepository(db)
    result = evaluate_pipeline_use_case(
        repo=repo,
        journal_client=JOURNAL_CLIENT,
        signal=req.signal,
        risk=req.risk,
        review=req.review,
        correlation_id=req.correlation_id,
    )
    return {
        "ok": result["ok"],
        "service": "orchestrator",
        "version": "v1",
        "correlation_id": req.correlation_id,
        "data": result if result["ok"] else None,
        "error": None if result["ok"] else {"code": result["code"]},
    }


@app.get("/v1/pipeline/pending")
def list_pending(db: Session = Depends(get_db)) -> dict:
    repo = TradeCandidateRepository(db)
    items = list_pending_candidates_use_case(repo)
    return {"ok": True, "items": items}


@app.post("/v1/pipeline/approve")
async def approve(req: ApproveCandidateRequest, db: Session = Depends(get_db)) -> dict:
    repo = TradeCandidateRepository(db)
    operator_action_repo = OperatorActionRepository(db)
    return await approve_candidate_use_case(
        repo=repo,
        kill_switch_client=KILL_SWITCH_CLIENT,
        execution_client=EXECUTION_CLIENT,
        operator_action_repo=operator_action_repo,
        journal_client=JOURNAL_CLIENT,
        candidate_id=req.candidate_id,
        telegram_user_id=req.telegram_user_id,
        correlation_id=req.correlation_id,
    )


@app.post("/v1/pipeline/reject")
def reject(req: RejectCandidateRequest, db: Session = Depends(get_db)) -> dict:
    repo = TradeCandidateRepository(db)
    operator_action_repo = OperatorActionRepository(db)
    return reject_candidate_use_case(
        repo=repo,
        operator_action_repo=operator_action_repo,
        journal_client=JOURNAL_CLIENT,
        candidate_id=req.candidate_id,
        telegram_user_id=req.telegram_user_id,
        correlation_id=req.correlation_id,
    )
