from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session

from apps.journal_review.application.daily_summary import daily_summary_use_case
from apps.journal_review.application.pattern_review import pattern_review_use_case
from apps.journal_review.config import get_config
from apps.journal_review.infrastructure.journal_reader import JournalReader
from apps.journal_review.infrastructure.llm_client import AnthropicLLMClient
from apps.journal_review.schemas.requests import DailySummaryRequest, PatternReviewRequest
from libs.db.session import get_db
from libs.logging.context import get_correlation_id, set_correlation_id
from libs.schemas.common import ServiceEnvelope

app = FastAPI(title="journal-review")
CONFIG = get_config()
LLM_CLIENT = AnthropicLLMClient(
    api_key=CONFIG.anthropic_api_key.get_secret_value() if CONFIG.anthropic_api_key else None,
    model=CONFIG.model,
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
    set_correlation_id(corr)
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = corr
    return response


@app.get("/health")
def health(request: Request) -> ServiceEnvelope[dict]:
    return ServiceEnvelope[dict](
        ok=True,
        service=CONFIG.service_name,
        correlation_id=request.headers.get("X-Correlation-Id") or get_correlation_id(),
        data={"status": "healthy", "provider": CONFIG.provider, "model": CONFIG.model},
        error=None,
    )


@app.post("/v1/journal-review/daily-summary")
def daily_summary(req: DailySummaryRequest, db: Session = Depends(get_db)) -> ServiceEnvelope[dict]:
    result = daily_summary_use_case(
        journal_reader=JournalReader(db),
        llm_client=LLM_CLIENT,
        req=req,
    )
    return ServiceEnvelope[dict](
        ok=True,
        service=CONFIG.service_name,
        correlation_id=req.correlation_id,
        data=result,
        error=None,
    )


@app.post("/v1/journal-review/pattern-review")
def pattern_review(req: PatternReviewRequest, db: Session = Depends(get_db)) -> ServiceEnvelope[dict]:
    result = pattern_review_use_case(
        journal_reader=JournalReader(db),
        llm_client=LLM_CLIENT,
        req=req,
    )
    return ServiceEnvelope[dict](
        ok=True,
        service=CONFIG.service_name,
        correlation_id=req.correlation_id,
        data=result,
        error=None,
    )
