from __future__ import annotations

from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="unset")


def set_correlation_id(value: str) -> None:
    correlation_id_var.set(value)


def get_correlation_id() -> str:
    return correlation_id_var.get()
