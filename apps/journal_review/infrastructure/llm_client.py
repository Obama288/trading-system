from __future__ import annotations

import json
from typing import Protocol

import httpx


class LLMClient(Protocol):
    def summarize_journal(self, *, events: list[dict], start_at: str, end_at: str) -> dict: ...

    def review_patterns(
        self,
        *,
        events: list[dict],
        start_at: str,
        end_at: str,
        event_type: str | None = None,
    ) -> dict: ...


class AnthropicLLMClient:
    def __init__(self, *, api_key: str | None, model: str, base_url: str = "https://api.anthropic.com") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def summarize_journal(self, *, events: list[dict], start_at: str, end_at: str) -> dict:
        prompt = (
            "You are an advisory-only journal review assistant. "
            "You must never recommend direct trade execution, position opening, or pipeline control. "
            "Analyze the journal events and return strict JSON with keys: "
            "summary_text, key_patterns, recurring_risks, suggested_focus. "
            f"Window: {start_at} to {end_at}. "
            f"Events JSON: {json.dumps(events, ensure_ascii=True)}"
        )
        return self._request_json(prompt)

    def review_patterns(
        self,
        *,
        events: list[dict],
        start_at: str,
        end_at: str,
        event_type: str | None = None,
    ) -> dict:
        prompt = (
            "You are an advisory-only journal pattern reviewer. "
            "You must never produce trading decisions or operational authority. "
            "Detect recurring patterns and return strict JSON with keys: "
            "summary_text, key_patterns, recurring_risks, suggested_focus. "
            f"Window: {start_at} to {end_at}. "
            f"Event type filter: {event_type or 'none'}. "
            f"Events JSON: {json.dumps(events, ensure_ascii=True)}"
        )
        return self._request_json(prompt)

    def _request_json(self, prompt: str) -> dict:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured")

        response = httpx.post(
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 800,
                "system": (
                    "Output is advisory only. Never issue execution instructions, approvals, "
                    "or authoritative trading commands. Return valid JSON only."
                ),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20.0,
        )
        response.raise_for_status()
        body = response.json()
        text_blocks = body.get("content", [])
        if not text_blocks:
            raise ValueError("Anthropic response did not contain content")
        text = "".join(block.get("text", "") for block in text_blocks if block.get("type") == "text").strip()
        if not text:
            raise ValueError("Anthropic response did not contain text")
        return json.loads(text)
