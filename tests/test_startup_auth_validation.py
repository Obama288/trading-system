from __future__ import annotations

import os
import pytest
from unittest.mock import patch

from libs.security import validate_startup_auth


class TestStartupAuthValidation:
    def test_kill_switch_client_fails_without_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                from libs.clients.kill_switch_client import HttpKillSwitchClient
                HttpKillSwitchClient(base_url="http://test:8000")
            assert "INTERNAL_SERVICE_TOKEN" in str(exc_info.value)

    def test_journal_client_fails_without_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                from libs.messaging.journal_client import HttpJournalClient
                HttpJournalClient(base_url="http://test:8000")
            assert "INTERNAL_SERVICE_TOKEN" in str(exc_info.value)

    def test_execution_client_fails_without_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                from apps.orchestrator.infrastructure.execution_client import HttpExecutionClient
                HttpExecutionClient(base_url="http://test:8000")
            assert "INTERNAL_SERVICE_TOKEN" in str(exc_info.value)

    def test_position_manager_client_fails_without_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                from apps.execution_service.infrastructure.position_manager_client import HttpPositionManagerClient
                HttpPositionManagerClient(base_url="http://test:8000")
            assert "INTERNAL_SERVICE_TOKEN" in str(exc_info.value)

    def test_alert_client_fails_without_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                from apps.position_manager.infrastructure.journal_client import HttpAlertClient
                HttpAlertClient(base_url="http://test:8000")
            assert "INTERNAL_SERVICE_TOKEN" in str(exc_info.value)

    def test_orchestrator_evaluate_client_fails_without_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                from ops.paper_pipeline_runner import OrchestratorEvaluateClient
                OrchestratorEvaluateClient(base_url="http://test:8000")
            assert "INTERNAL_SERVICE_TOKEN" in str(exc_info.value)

    def test_security_module_fails_without_internal_token_at_request_time(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                from libs.security import get_internal_service_auth
                get_internal_service_auth(x_internal_token="test")
            assert "INTERNAL_SERVICE_TOKEN" in str(exc_info.value)

    def test_security_module_fails_without_operator_token_at_request_time(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                from libs.security import get_operator_auth
                get_operator_auth(x_operator_token="test")
            assert "OPERATOR_TOKEN" in str(exc_info.value)

    def test_security_module_fails_without_admin_token_at_request_time(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                from libs.security import get_admin_auth
                get_admin_auth(x_admin_token="test")
            assert "ADMIN_TOKEN" in str(exc_info.value)


class TestTokenStrengthValidation:
    def test_short_internal_token_raises_at_startup(self):
        with patch.dict(os.environ, {"INTERNAL_SERVICE_TOKEN": "tooshort"}):
            with pytest.raises(RuntimeError, match="too short"):
                validate_startup_auth(require_internal=True)

    def test_short_operator_token_raises_at_startup(self):
        with patch.dict(os.environ, {"OPERATOR_TOKEN": "tooshort"}):
            with pytest.raises(RuntimeError, match="too short"):
                validate_startup_auth(require_operator=True)

    def test_short_admin_token_raises_at_startup(self):
        with patch.dict(os.environ, {"ADMIN_TOKEN": "tooshort"}):
            with pytest.raises(RuntimeError, match="too short"):
                validate_startup_auth(require_admin=True)

    def test_denylisted_internal_token_raises_at_startup(self):
        with patch.dict(os.environ, {"INTERNAL_SERVICE_TOKEN": "secret"}):
            with pytest.raises(RuntimeError, match="well-known weak token"):
                validate_startup_auth(require_internal=True)

    def test_denylisted_operator_token_raises_at_startup(self):
        with patch.dict(os.environ, {"OPERATOR_TOKEN": "password"}):
            with pytest.raises(RuntimeError, match="well-known weak token"):
                validate_startup_auth(require_operator=True)

    def test_denylisted_admin_token_raises_at_startup(self):
        with patch.dict(os.environ, {"ADMIN_TOKEN": "admin"}):
            with pytest.raises(RuntimeError, match="well-known weak token"):
                validate_startup_auth(require_admin=True)

    def test_strong_token_passes_startup(self):
        strong = "x" * 32
        with patch.dict(os.environ, {
            "INTERNAL_SERVICE_TOKEN": strong,
            "OPERATOR_TOKEN": strong,
            "ADMIN_TOKEN": strong,
        }):
            validate_startup_auth(require_internal=True, require_operator=True, require_admin=True)

    def test_error_message_names_failing_token(self):
        with patch.dict(os.environ, {"INTERNAL_SERVICE_TOKEN": "tooshort"}):
            with pytest.raises(RuntimeError, match="INTERNAL_SERVICE_TOKEN"):
                validate_startup_auth(require_internal=True)

    def test_multiple_weak_tokens_all_reported(self):
        with patch.dict(os.environ, {
            "INTERNAL_SERVICE_TOKEN": "tooshort",
            "OPERATOR_TOKEN": "tooshort",
        }):
            with pytest.raises(RuntimeError) as exc_info:
                validate_startup_auth(require_internal=True, require_operator=True)
            msg = str(exc_info.value)
            assert "INTERNAL_SERVICE_TOKEN" in msg
            assert "OPERATOR_TOKEN" in msg