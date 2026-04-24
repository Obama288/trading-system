from __future__ import annotations

import os
import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status


def _get_internal_service_token() -> str:
    token = os.getenv("INTERNAL_SERVICE_TOKEN")
    if not token:
        raise RuntimeError(
            "INTERNAL_SERVICE_TOKEN environment variable is not set. "
            "Internal service auth requires explicit token configuration."
        )
    return token


def _get_operator_token() -> str:
    token = os.getenv("OPERATOR_TOKEN")
    if not token:
        raise RuntimeError(
            "OPERATOR_TOKEN environment variable is not set. "
            "Operator auth requires explicit token configuration."
        )
    return token


def _get_admin_token() -> str:
    token = os.getenv("ADMIN_TOKEN")
    if not token:
        raise RuntimeError(
            "ADMIN_TOKEN environment variable is not set. "
            "Admin auth requires explicit token configuration."
        )
    return token


def get_internal_service_auth(
    x_internal_token: Annotated[str | None, Header(alias="X-Internal-Token")] = None,
) -> str:
    if x_internal_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Internal-Token header",
        )
    expected = _get_internal_service_token()
    if not secrets.compare_digest(x_internal_token, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid X-Internal-Token",
        )
    return x_internal_token


def get_operator_auth(
    x_operator_token: Annotated[str | None, Header(alias="X-Operator-Token")] = None,
) -> str:
    if x_operator_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Operator-Token header",
        )
    expected = _get_operator_token()
    if not secrets.compare_digest(x_operator_token, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid X-Operator-Token",
        )
    return x_operator_token


def get_admin_auth(
    x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
) -> str:
    if x_admin_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Admin-Token header",
        )
    expected = _get_admin_token()
    if not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid X-Admin-Token",
        )
    return x_admin_token


def require_internal_service_auth() -> str:
    return Depends(get_internal_service_auth)


def require_operator_auth() -> str:
    return Depends(get_operator_auth)


def require_admin_auth() -> str:
    return Depends(get_admin_auth)


def validate_startup_auth(require_internal: bool = False, require_operator: bool = False, require_admin: bool = False) -> None:
    """Validate required auth tokens at service startup.
    
    Call this in the service's lifespan to fail fast if required tokens are missing.
    
    Args:
        require_internal: Validate INTERNAL_SERVICE_TOKEN exists
        require_operator: Validate OPERATOR_TOKEN exists
        require_admin: Validate ADMIN_TOKEN exists
    
    Raises:
        RuntimeError: If any required token is missing
    """
    errors = []
    if require_internal:
        try:
            _get_internal_service_token()
        except RuntimeError as e:
            errors.append(str(e))
    if require_operator:
        try:
            _get_operator_token()
        except RuntimeError as e:
            errors.append(str(e))
    if require_admin:
        try:
            _get_admin_token()
        except RuntimeError as e:
            errors.append(str(e))
    if errors:
        raise RuntimeError("Auth startup validation failed: " + "; ".join(errors))