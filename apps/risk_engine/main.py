import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.risk_engine.application.evaluate_risk import evaluate_risk_use_case
from libs.schemas.common import EntryZone, RiskReasonCode, TradeDirection
from libs.security import require_internal_service_auth, validate_startup_auth
from libs.db.startup_health import ensure_db_connection_startup
from libs.logging.context import set_correlation_id

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_startup_auth(require_internal=True)
    await ensure_db_connection_startup(service_name="risk-engine", app=app)
    yield


app = FastAPI(title="risk-engine", lifespan=lifespan)


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


class AccountState(BaseModel):
    equity_usdt: float
    daily_pnl_usdt: float
    open_positions: int
    portfolio_exposure_pct: float


class RiskRequest(BaseModel):
    signal_id: str
    symbol: str
    side: TradeDirection
    confidence: float | None = None
    entry_zone: EntryZone
    stop_loss: float
    account_state: AccountState
    correlation_id: str


@app.get("/health")
def health() -> dict:
    return {"service": "risk-engine", "status": "healthy"}


@app.post("/v1/risk/evaluate")
def evaluate_risk(
    req: RiskRequest,
    _: str = require_internal_service_auth(),
) -> dict:
    result = evaluate_risk_use_case(req)
    return {
        "ok": True,
        "service": "risk-engine",
        "version": "v1",
        "correlation_id": req.correlation_id,
        "data": {
            "risk_id": f"risk_{req.signal_id}",
            "signal_id": req.signal_id,
            "symbol": req.symbol,
            **result,
        },
        "error": None,
    }
