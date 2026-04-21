from fastapi import FastAPI

from apps.review_gateway.application.review_candidate import review_candidate_use_case
from apps.review_gateway.schemas.review_requests import ReviewCandidateRequest
from libs.config.settings import load_all_configs
from libs.schemas.common import ServiceEnvelope

app = FastAPI(title="review-gateway")


@app.get("/health")
def health() -> dict:
    return {"service": "review-gateway", "status": "healthy"}


@app.post("/v1/review/check")
def review_candidate(req: ReviewCandidateRequest) -> ServiceEnvelope[dict]:
    configs = load_all_configs()
    stale_threshold_seconds = int(
        configs["risk"].get("market_data", {}).get("stale_snapshot_threshold_seconds", 30)
    )
    # fallback stays at 30s until risk.yaml explicitly overrides it

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
