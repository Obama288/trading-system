import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from apps.journal_ingest.api.routes import router
from libs.db.startup_health import ensure_db_connection_startup
from libs.logging.context import set_correlation_id
from libs.security import validate_startup_auth

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_startup_auth(require_internal=True, require_operator=True)
    await ensure_db_connection_startup(service_name="journal-ingest", app=app)
    yield


app = FastAPI(title="journal-ingest", lifespan=lifespan)


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


app.include_router(router)
