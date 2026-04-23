from __future__ import annotations

from libs.messaging.journal_client import DbJournalClient

__all__ = ["DbJournalClient", "NoopAlertClient"]


class NoopAlertClient:
    def notify(self, payload: dict) -> None:
        return None
