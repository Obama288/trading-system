import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.kill_switch.application.get_status import get_kill_switch_status_use_case
from apps.kill_switch.application.halt import halt_use_case
from apps.kill_switch.application.resume import resume_use_case
from apps.kill_switch.infrastructure.system_state_repo import SystemStateRepository
from libs.db.models.journal_event import JournalEventModel
from libs.db.repositories.operator_action_repo import OperatorActionRepository
from libs.db.session import get_db
from libs.db.startup_health import ensure_db_connection_startup
from libs.logging.context import set_correlation_id
from libs.security import require_internal_service_auth, require_admin_auth, validate_startup_auth

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_startup_auth(require_internal=True, require_admin=True)
    await ensure_db_connection_startup(service_name="kill-switch", app=app)
    yield


app = FastAPI(title="kill-switch", lifespan=lifespan)


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


class HaltRequest(BaseModel):
    operator_user_id: int
    reason: str
    actor: str
    correlation_id: str


class ResumeRequest(BaseModel):
    operator_user_id: int
    actor: str
    correlation_id: str


@app.get("/health")
def health() -> dict:
    return {"service": "kill-switch", "status": "healthy"}


@app.get("/v1/kill-switch/status")
def status(
    correlation_id: str,
    db: Session = Depends(get_db),
    _: str = require_internal_service_auth(),
) -> dict:
    repo = SystemStateRepository(db)
    state = get_kill_switch_status_use_case(repo)
    return {
        "ok": True,
        "service": "kill-switch",
        "version": "v1",
        "correlation_id": correlation_id,
        "data": state,
        "error": None,
    }


@app.post("/v1/kill-switch/halt")
def halt(
    req: HaltRequest,
    db: Session = Depends(get_db),
    _: str = require_admin_auth(),
) -> dict:
    repo = SystemStateRepository(db)
    operator_action_repo = OperatorActionRepository(db)
    state = halt_use_case(repo, reason=req.reason, actor=req.actor)
    operator_action_repo.record_no_commit(
        operator_user_id=req.operator_user_id,
        action_type="kill_switch_halt",
        target_type="system_state",
        target_id="kill_switch_state",
        correlation_id=req.correlation_id,
        payload_json={
            "reason": req.reason,
            "actor": req.actor,
            "result": "halted",
        },
    )
    db.add(
        JournalEventModel(
            event_id=f"evt_kill_switch_halt_{uuid4().hex}",
            event_type="kill_switch_halted",
            severity="warning",
            correlation_id=req.correlation_id,
            payload={
                "operator_user_id": req.operator_user_id,
                "actor": req.actor,
                "reason": req.reason,
                "result": "halted",
            },
        )
    )
    db.commit()  # single commit: state + operator_action + journal
    return {
        "ok": True,
        "service": "kill-switch",
        "version": "v1",
        "correlation_id": req.correlation_id,
        "data": state,
        "error": None,
    }


@app.post("/v1/kill-switch/resume")
def resume(
    req: ResumeRequest,
    db: Session = Depends(get_db),
    _: str = require_admin_auth(),
) -> dict:
    repo = SystemStateRepository(db)
    operator_action_repo = OperatorActionRepository(db)
    state = resume_use_case(repo, actor=req.actor)
    operator_action_repo.record_no_commit(
        operator_user_id=req.operator_user_id,
        action_type="kill_switch_resume",
        target_type="system_state",
        target_id="kill_switch_state",
        correlation_id=req.correlation_id,
        payload_json={
            "actor": req.actor,
            "result": "resumed",
        },
    )
    db.add(
        JournalEventModel(
            event_id=f"evt_kill_switch_resume_{uuid4().hex}",
            event_type="kill_switch_resumed",
            severity="info",
            correlation_id=req.correlation_id,
            payload={
                "operator_user_id": req.operator_user_id,
                "actor": req.actor,
                "result": "resumed",
            },
        )
    )
    db.commit()  # single commit: state + operator_action + journal
    return {
        "ok": True,
        "service": "kill-switch",
        "version": "v1",
        "correlation_id": req.correlation_id,
        "data": state,
        "error": None,
    }
