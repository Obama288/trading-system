from __future__ import annotations

import pytest
from unittest.mock import patch
import secrets


class TestConstantTimeTokenComparison:
    def test_compare_digest_is_used_for_internal_token(self):
        import libs.security as security_module
        original_compare_digest = secrets.compare_digest
        compare_digest_called = []

        def mock_compare_digest(a, b):
            compare_digest_called.append((a, b))
            return original_compare_digest(a, b)

        with patch.object(secrets, "compare_digest", side_effect=mock_compare_digest):
            with patch.dict("os.environ", {"INTERNAL_SERVICE_TOKEN": "test-token-123"}):
                from libs.security import get_internal_service_auth
                try:
                    get_internal_service_auth(x_internal_token="test-token-123")
                except Exception:
                    pass
                assert len(compare_digest_called) == 1

    def test_compare_digest_is_used_for_operator_token(self):
        import libs.security as security_module
        original_compare_digest = secrets.compare_digest
        compare_digest_called = []

        def mock_compare_digest(a, b):
            compare_digest_called.append((a, b))
            return original_compare_digest(a, b)

        with patch.object(secrets, "compare_digest", side_effect=mock_compare_digest):
            with patch.dict("os.environ", {"OPERATOR_TOKEN": "operator-token-456"}):
                from libs.security import get_operator_auth
                try:
                    get_operator_auth(x_operator_token="operator-token-456")
                except Exception:
                    pass
                assert len(compare_digest_called) == 1

    def test_compare_digest_is_used_for_admin_token(self):
        import libs.security as security_module
        original_compare_digest = secrets.compare_digest
        compare_digest_called = []

        def mock_compare_digest(a, b):
            compare_digest_called.append((a, b))
            return original_compare_digest(a, b)

        with patch.object(secrets, "compare_digest", side_effect=mock_compare_digest):
            with patch.dict("os.environ", {"ADMIN_TOKEN": "admin-token-789"}):
                from libs.security import get_admin_auth
                try:
                    get_admin_auth(x_admin_token="admin-token-789")
                except Exception:
                    pass
                assert len(compare_digest_called) == 1