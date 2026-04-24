from __future__ import annotations

import asyncio
import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Callable

from fastapi import FastAPI
from sqlalchemy import text

from libs.db.session import get_db, get_session_factory

LOGGER = logging.getLogger(__name__)


@contextmanager
def _open_db_from_dependency(
    *,
    app: FastAPI | None,
    db_dependency: Callable[[], Generator[Any, None, None]],
):
    dependency = db_dependency
    if app is not None and db_dependency in app.dependency_overrides:
        dependency = app.dependency_overrides[db_dependency]

    generator = dependency()
    db = next(generator)
    try:
        yield db
    finally:
        generator.close()


@contextmanager
def _open_db_session(*, app: FastAPI | None):
    if app is not None:
        with _open_db_from_dependency(app=app, db_dependency=get_db) as db:
            yield db
        return

    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


async def ensure_db_connection_startup(
    *,
    service_name: str,
    app: FastAPI | None = None,
    retries: int = 3,
    delay_seconds: float = 2.0,
) -> None:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with _open_db_session(app=app) as db:
                db.execute(text("SELECT 1"))
            LOGGER.info("DB connection OK", extra={"service": service_name, "attempt": attempt})
            return
        except Exception as exc:  # noqa: BLE001 - fail-fast on any connectivity/session init issue.
            last_exc = exc
            if attempt < retries:
                LOGGER.warning(
                    "DB connection check failed; retrying",
                    extra={
                        "service": service_name,
                        "attempt": attempt,
                        "retries": retries,
                        "error": str(exc),
                    },
                )
                await asyncio.sleep(delay_seconds)

    LOGGER.error(
        "DB connection failed, shutting down",
        extra={"service": service_name, "retries": retries, "error": str(last_exc) if last_exc else None},
    )
    raise RuntimeError("DB connection failed, shutting down") from last_exc
