import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from apps.review_gateway.application.review_candidate import review_candidate_use_case
from apps.review_gateway.schemas.review_requests import ReviewCandidateRequest
from libs.config.settings import load_all_configs
from libs.logging.context import set_correlation_id
from libs.schemas.common import ServiceEnvelope
from libs.security import require_internal_service_auth, validate_startup_auth
from libs.db.startup_health import ensure_db_connection_startup

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_startup_auth(require_internal=True)
    await ensure_db_connection_startup(service_name="review-gateway", app=app)
    yield


app = FastAPI(title="review-gateway", lifespan=lifespan)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
    set_correlation_id(corr)
    try:
        response = await call_next(request)
    except Exception:
        LOGGER.exception("unhandled_exception_in_middleware", extra={"correlation_id": corr})
        response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
    response.headers["X-Correlation-Id"] = corr
    return response


@app.get("/health")
def health() -> dict:
    return {"service": "review-gateway", "status": "healthy"}


@app.post("/v1/review/check")
def review_candidate(
    req: ReviewCandidateRequest,
    _: str = require_internal_service_auth(),
) -> ServiceEnvelope[dict]:
    configs = load_all_configs()
    stale_threshold_seconds = int(
        configs["risk"].get("market_data", {}).get("stale_snapshot_threshold_seconds", 30)
    )

    decision = review_candidate_use_case(
        signal=req.signal,
        risk=req.risk,
        snapshot=req.market_snapshot,
        stale_threshold_seconds=stale_threshold_seconds,
    )
    return ServiceEnvelope[dict](
        ok=True,
        service="review-gateway",
        correlation_id=req.correlation_id,
        data=decision.model_dump(mode="json"),
        error=None,
    )
