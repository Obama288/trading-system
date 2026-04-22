from uuid import uuid4

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.kill_switch.application.get_status import get_kill_switch_status_use_case
from apps.kill_switch.application.halt import halt_use_case
from apps.kill_switch.application.resume import resume_use_case
from apps.kill_switch.infrastructure.system_state_repo import SystemStateRepository
from libs.db.models.journal_event import JournalEventModel
from libs.db.repositories.operator_action_repo import OperatorActionRepository
from libs.db.session import get_db

app = FastAPI(title="kill-switch")


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
    operator_action_repo = OperatorActionRepository(db)
    state = halt_use_case(repo, reason=req.reason, actor=req.actor)
    operator_action_repo.record(
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
    return {
        "ok": True,
        "service": "kill-switch",
        "version": "v1",
        "correlation_id": req.correlation_id,
        "data": state,
        "error": None,
    }


@app.post("/v1/kill-switch/resume")
def resume(req: ResumeRequest, db: Session = Depends(get_db)) -> dict:
    repo = SystemStateRepository(db)
    operator_action_repo = OperatorActionRepository(db)
    state = resume_use_case(repo, actor=req.actor)
    operator_action_repo.record(
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
    db.commit()
    return {
        "ok": True,
        "service": "kill-switch",
        "version": "v1",
        "correlation_id": req.correlation_id,
        "data": state,
        "error": None,
    }
