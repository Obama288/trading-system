from uuid import uuid4

from fastapi import FastAPI, Request

from apps.journal_ingest.api.routes import router
from libs.logging.context import set_correlation_id

app = FastAPI(title="journal-ingest")


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
    set_correlation_id(corr)
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = corr
    return response


app.include_router(router)
