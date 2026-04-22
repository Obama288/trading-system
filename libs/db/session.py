from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from libs.config.settings import AppSettings


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


@lru_cache(maxsize=1)
def get_engine():
    # sync engine — acceptable for MVP; migrate to async engine/driver before high-load production use.
    return create_engine(
        get_settings().postgres_dsn.get_secret_value(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


@lru_cache(maxsize=1)
def get_session_factory():
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
    )


def get_db():
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
