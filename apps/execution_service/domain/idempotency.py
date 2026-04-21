from __future__ import annotations


def validate_idempotency_key(key: str) -> None:
    if not key or not key.strip():
        raise ValueError("execution_idempotency_key is required")
