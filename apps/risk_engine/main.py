import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.risk_engine.infrastructure.paper_account_authority_repo import PaperAccountAuthorityRepository
from libs.db.models.position import PositionModel
from libs.db.session import get_db
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


def _fail_closed_response(
    *,
    req: RiskRequest,
    code: str,
    detail: str,
    status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "service": "risk-engine",
            "version": "v1",
            "correlation_id": req.correlation_id,
            "data": {
                "risk_id": f"risk_{req.signal_id}",
                "signal_id": req.signal_id,
                "symbol": req.symbol,
                "approved": False,
                "reason_codes": [RiskReasonCode.RISK_REJECTED],
            },
            "error": {
                "code": code,
                "detail": detail,
            },
        },
    )


def _get_authoritative_equity_usdt(db: Session) -> float | None:
    return PaperAccountAuthorityRepository(db).get_current_equity_usdt()


def _get_authoritative_open_positions(db: Session) -> int:
    stmt = select(func.count()).select_from(PositionModel).where(PositionModel.status == "open")
    return int(db.execute(stmt).scalar_one())


@app.get("/health")
def health() -> dict:
    return {"service": "risk-engine", "status": "healthy"}


@app.post("/v1/risk/evaluate")
def evaluate_risk(
    req: RiskRequest,
    _: str = require_internal_service_auth(),
    db: Session = Depends(get_db),
):
    try:
        authoritative_equity = _get_authoritative_equity_usdt(db)
    except Exception:
        LOGGER.exception("paper_equity_authority_unavailable", extra={"correlation_id": req.correlation_id})
        return _fail_closed_response(
            req=req,
            code="PAPER_EQUITY_AUTHORITY_UNAVAILABLE",
            detail="Authoritative paper equity is unavailable.",
        )

    if authoritative_equity is None:
        return _fail_closed_response(
            req=req,
            code="PAPER_EQUITY_AUTHORITY_MISSING",
            detail="Authoritative paper equity is missing.",
        )
    if authoritative_equity <= 0:
        return _fail_closed_response(
            req=req,
            code="PAPER_EQUITY_AUTHORITY_INVALID",
            detail="Authoritative paper equity is invalid.",
        )

    try:
        _get_authoritative_open_positions(db)
    except Exception:
        LOGGER.exception("open_positions_authority_unavailable", extra={"correlation_id": req.correlation_id})
        return _fail_closed_response(
            req=req,
            code="OPEN_POSITIONS_AUTHORITY_UNAVAILABLE",
            detail="Authoritative open-position count is unavailable.",
        )

    return _fail_closed_response(
        req=req,
        code="DAILY_PNL_AUTHORITY_UNAVAILABLE",
        detail="Authoritative daily PnL is not implemented for protected risk admission.",
    )
