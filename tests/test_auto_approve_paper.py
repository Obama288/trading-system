from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from ops import auto_approve_paper


class _FailingSessionFactory:
    def __call__(self):
        raise AssertionError("DB scan should not be attempted")


class _Query:
    def __init__(self, candidates: list[SimpleNamespace]) -> None:
        self._candidates = candidates

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self) -> list[SimpleNamespace]:
        return self._candidates


class _Session:
    def __init__(self, candidates: list[SimpleNamespace]) -> None:
        self._candidates = candidates

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def query(self, *_args, **_kwargs) -> _Query:
        return _Query(self._candidates)


class _SessionFactory:
    def __init__(self, candidates: list[SimpleNamespace]) -> None:
        self.calls = 0
        self._candidates = candidates

    def __call__(self) -> _Session:
        self.calls += 1
        return _Session(self._candidates)


class _Response:
    status_code = 200

    def json(self) -> dict:
        return {"ok": True, "code": "APPROVED"}


def _candidate() -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id="cand_auto_001",
        status="pending",
        symbol="BTCUSDT",
        side="buy",
        ttl_expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        execution_payload_json={"symbol": "BTCUSDT"},
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.parametrize("token_value", [None, "", "   "])
def test_run_loop_fails_fast_without_operator_token(
    monkeypatch: pytest.MonkeyPatch,
    token_value: str | None,
) -> None:
    if token_value is None:
        monkeypatch.delenv("OPERATOR_TOKEN", raising=False)
    else:
        monkeypatch.setenv("OPERATOR_TOKEN", token_value)
    monkeypatch.setattr(auto_approve_paper, "get_session_factory", _FailingSessionFactory())
    monkeypatch.setattr(
        auto_approve_paper.httpx,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("HTTP request should not be attempted")),
    )

    with pytest.raises(RuntimeError, match="OPERATOR_TOKEN"):
        auto_approve_paper.run_loop(
            interval_seconds=0,
            operator_user_id=9001,
            orchestrator_base_url="http://orchestrator.test",
            once=True,
        )


def test_run_loop_fails_fast_when_paper_mode_is_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_TOKEN", "test-operator-token-000000000000")
    monkeypatch.setattr(auto_approve_paper, "load_all_configs", lambda: {"system": {"paper_mode": False}})
    monkeypatch.setattr(auto_approve_paper, "get_session_factory", _FailingSessionFactory())
    monkeypatch.setattr(
        auto_approve_paper.httpx,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("HTTP request should not be attempted")),
    )

    with pytest.raises(RuntimeError, match="paper_mode: true"):
        auto_approve_paper.run_loop(
            interval_seconds=0,
            operator_user_id=9001,
            orchestrator_base_url="http://orchestrator.test",
            once=True,
        )


def test_run_loop_uses_operator_token_when_paper_mode_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    session_factory = _SessionFactory([_candidate()])
    requests: list[dict] = []

    def _post(url: str, *, json: dict, headers: dict, timeout: float) -> _Response:
        requests.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return _Response()

    monkeypatch.setenv("OPERATOR_TOKEN", "test-operator-token-000000000000")
    monkeypatch.setattr(auto_approve_paper, "load_all_configs", lambda: {"system": {"paper_mode": True}})
    monkeypatch.setattr(auto_approve_paper, "get_session_factory", lambda: session_factory)
    monkeypatch.setattr(auto_approve_paper.httpx, "post", _post)

    auto_approve_paper.run_loop(
        interval_seconds=0,
        operator_user_id=9001,
        orchestrator_base_url="http://orchestrator.test/",
        once=True,
    )

    assert session_factory.calls == 1
    assert len(requests) == 1
    assert requests[0]["url"] == "http://orchestrator.test/v1/pipeline/approve"
    assert requests[0]["headers"] == {"X-Operator-Token": "test-operator-token-000000000000"}
    assert requests[0]["json"]["candidate_id"] == "cand_auto_001"
    assert requests[0]["json"]["telegram_user_id"] == 9001
