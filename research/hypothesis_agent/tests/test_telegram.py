from __future__ import annotations

from research.hypothesis_agent.alerts import telegram


def test_send_research_alert_prefixes_message(monkeypatch):
    captured: dict = {}

    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

    class DummyRequests:
        def post(self, url: str, json: dict, timeout: int) -> DummyResponse:
            captured["url"] = url
            captured["json"] = json
            captured["timeout"] = timeout
            return DummyResponse()

    monkeypatch.setattr(telegram, "requests", DummyRequests())

    sent = telegram.send_research_alert("New hypothesis generated", bot_token="token", chat_id="123")

    assert sent is True
    assert captured["json"]["text"] == "[RESEARCH] New hypothesis generated"


def test_send_research_alert_skips_without_credentials():
    assert telegram.send_research_alert("anything", bot_token=None, chat_id="123") is False
