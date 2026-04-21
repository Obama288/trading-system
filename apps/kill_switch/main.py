from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.kill_switch.application.get_status import get_kill_switch_status_use_case
from apps.kill_switch.application.halt import halt_use_case
from apps.kill_switch.infrastructure.system_state_repo import SystemStateRepository
from libs.db.session import get_db

app = FastAPI(title="kill-switch")


class HaltRequest(BaseModel):
    reason: str
    actor: str
    correlation_id: str


@app.get("/health")
def health() -> dict:
    return {"service": "kill-switch", "status": "healthy"}


@app.get("/v1/kill-switch/status")
def status(correlation_id: str, db: Session = Depends(get_db)) -> dict:
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
def halt(req: HaltRequest, db: Session = Depends(get_db)) -> dict:
    # actor still needs internal auth / ACL validation before non-MVP use.
    repo = SystemStateRepository(db)
    state = halt_use_case(repo, reason=req.reason, actor=req.actor)
    return {
        "ok": True,
        "service": "kill-switch",
        "version": "v1",
        "correlation_id": req.correlation_id,
        "data": state,
        "error": None,
    }


@app.post("/v1/kill-switch/resume")
def resume(correlation_id: str) -> dict:
    return {
        "ok": False,
        "service": "kill-switch",
        "version": "v1",
        "correlation_id": correlation_id,
        "data": None,
        "error": {"code": "NOT_IMPLEMENTED", "message": "safe resume is not implemented yet"},
    }
