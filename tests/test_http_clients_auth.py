from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from libs.clients.kill_switch_client import HttpKillSwitchClient


class TestHttpKillSwitchClientAuth:
    @pytest.mark.asyncio
    async def test_sends_internal_token_header(self):
        with patch("libs.clients.kill_switch_client.httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.raise_for_status = AsyncMock()
            mock_response.json = lambda: {
                "ok": True,
                "data": {"trading_enabled": True, "kill_switch_active": False},
            }
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with patch.dict("os.environ", {"INTERNAL_SERVICE_TOKEN": "test-token-123"}):
                client = HttpKillSwitchClient(base_url="http://test:8000")
                await client.get_status(correlation_id="test-corr")

                mock_client.get.assert_called_once()
                call_kwargs = mock_client.get.call_args.kwargs
                assert "headers" in call_kwargs
                assert call_kwargs["headers"]["X-Internal-Token"] == "test-token-123"

    @pytest.mark.asyncio
    async def test_raises_kill_switch_error_on_transport_error(self):
        import httpx
        from libs.clients.kill_switch_client import KillSwitchError

        with patch("libs.clients.kill_switch_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=httpx.RequestError("connection failed"))
            mock_client_class.return_value = mock_client

            with patch.dict("os.environ", {"INTERNAL_SERVICE_TOKEN": "test-token-123"}):
                client = HttpKillSwitchClient(base_url="http://test:8000")
                with pytest.raises(KillSwitchError):
                    await client.get_status(correlation_id="test-corr")

    @pytest.mark.asyncio
    async def test_raises_kill_switch_unavailable_on_connect_error(self):
        import httpx
        from libs.clients.kill_switch_client import KillSwitchUnavailableError

        with patch("libs.clients.kill_switch_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
            mock_client_class.return_value = mock_client

            with patch.dict("os.environ", {"INTERNAL_SERVICE_TOKEN": "test-token-123"}):
                client = HttpKillSwitchClient(base_url="http://test:8000")
                with pytest.raises(KillSwitchUnavailableError):
                    await client.get_status(correlation_id="test-corr")

    @pytest.mark.asyncio
    async def test_raises_kill_switch_error_on_http_5xx(self):
        import httpx
        from libs.clients.kill_switch_client import KillSwitchError

        with patch("libs.clients.kill_switch_client.httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.raise_for_status = lambda: (_ for _ in ()).throw(
                httpx.HTTPStatusError("500 error", request=AsyncMock(), response=mock_response)
            )
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with patch.dict("os.environ", {"INTERNAL_SERVICE_TOKEN": "test-token-123"}):
                client = HttpKillSwitchClient(base_url="http://test:8000")
                with pytest.raises(KillSwitchError):
                    await client.get_status(correlation_id="test-corr")

    @pytest.mark.asyncio
    async def test_raises_kill_switch_auth_error_on_403(self):
        import httpx
        from libs.clients.kill_switch_client import KillSwitchAuthError

        with patch("libs.clients.kill_switch_client.httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 403
            mock_response.raise_for_status = lambda: (_ for _ in ()).throw(
                httpx.HTTPStatusError("403 error", request=AsyncMock(), response=mock_response)
            )
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with patch.dict("os.environ", {"INTERNAL_SERVICE_TOKEN": "test-token-123"}):
                client = HttpKillSwitchClient(base_url="http://test:8000")
                with pytest.raises(KillSwitchAuthError):
                    await client.get_status(correlation_id="test-corr")

    def test_raises_when_token_missing(self):
        import os

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                HttpKillSwitchClient(base_url="http://test:8000")
            assert "INTERNAL_SERVICE_TOKEN" in str(exc_info.value)