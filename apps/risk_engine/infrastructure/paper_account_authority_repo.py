from __future__ import annotations

from sqlalchemy.orm import Session

from libs.db.models.paper_account_authority import PaperAccountAuthorityModel


PAPER_ACCOUNT_AUTHORITY_KEY = "default_paper_account"


class PaperAccountAuthorityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_current_equity_usdt(self) -> float | None:
        model = self.db.get(PaperAccountAuthorityModel, PAPER_ACCOUNT_AUTHORITY_KEY)
        if model is None:
            return None
        return model.equity_usdt
