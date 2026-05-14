from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.risk_engine.infrastructure.paper_account_authority_repo import (
    PAPER_ACCOUNT_AUTHORITY_KEY,
    PaperAccountAuthorityRepository,
)
from libs.db.base import Base
from libs.db.models.paper_account_authority import PaperAccountAuthorityModel


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_get_current_equity_usdt_returns_persisted_authority():
    db = _session()
    try:
        db.add(
            PaperAccountAuthorityModel(
                account_key=PAPER_ACCOUNT_AUTHORITY_KEY,
                equity_usdt=1234.56,
                updated_by="test",
            )
        )
        db.commit()

        repo = PaperAccountAuthorityRepository(db)

        assert repo.get_current_equity_usdt() == 1234.56
    finally:
        db.close()


def test_get_current_equity_usdt_returns_none_when_authority_absent():
    db = _session()
    try:
        repo = PaperAccountAuthorityRepository(db)

        assert repo.get_current_equity_usdt() is None
    finally:
        db.close()
