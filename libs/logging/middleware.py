from __future__ import annotations

from uuid import uuid4
from fastapi import Request

from libs.logging.context import set_correlation_id


async def correlation_id_middleware(request: Request, call_next):
    corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
    set_correlation_id(corr)
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = corr
    return response
