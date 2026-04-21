from fastapi import FastAPI
from pydantic import BaseModel

from apps.risk_engine.application.evaluate_risk import evaluate_risk_use_case
from libs.schemas.common import EntryZone, RiskReasonCode, TradeDirection

app = FastAPI(title="risk-engine")


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
def evaluate_risk(req: RiskRequest) -> dict:
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
