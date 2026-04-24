from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from libs.messaging.journal_client import HttpJournalClient


class TestHttpJournalClientAuth:
    @pytest.mark.asyncio
    async def test_sends_internal_token_header(self):
        with patch("libs.messaging.journal_client.httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.raise_for_status = AsyncMock()
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with patch.dict("os.environ", {"INTERNAL_SERVICE_TOKEN": "test-internal-token"}):
                client = HttpJournalClient(base_url="http://test:8000", retries=0)
                await client.write({"event_id": "test", "event_type": "test"})

                mock_client.post.assert_called_once()
                call_kwargs = mock_client.post.call_args.kwargs
                assert "headers" in call_kwargs
                assert call_kwargs["headers"]["X-Internal-Token"] == "test-internal-token"

    def test_raises_when_token_missing(self):
        import os

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                HttpJournalClient(base_url="http://test:8000")
            assert "INTERNAL_SERVICE_TOKEN" in str(exc_info.value)