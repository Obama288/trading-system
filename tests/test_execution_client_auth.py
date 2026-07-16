from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from apps.orchestrator.infrastructure.execution_client import HttpExecutionClient


class TestHttpExecutionClientAuth:
    @pytest.mark.asyncio
    async def test_sends_internal_token_header(self):
        with patch("apps.orchestrator.infrastructure.execution_client.httpx.AsyncClient") as mock_client_class:
            mock_response = Mock()
            mock_response.json = lambda: {"ok": True}
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with patch.dict("os.environ", {"INTERNAL_SERVICE_TOKEN": "test-internal-token"}):
                client = HttpExecutionClient(base_url="http://test:8000")
                await client.place(
                    candidate_id="cand-123",
                    execution_candidate={"side": "buy"},
                    correlation_id="test-corr",
                )

                mock_client.post.assert_called_once()
                call_kwargs = mock_client.post.call_args.kwargs
                assert "headers" in call_kwargs
                assert call_kwargs["headers"]["X-Internal-Token"] == "test-internal-token"

    def test_raises_when_token_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                HttpExecutionClient(base_url="http://test:8000")
            assert "INTERNAL_SERVICE_TOKEN" in str(exc_info.value)