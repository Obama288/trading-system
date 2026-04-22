from __future__ import annotations

import json
from urllib.request import Request, urlopen

try:
    import requests
except ImportError:  # pragma: no cover - exercised only when requests is installed
    requests = None


def _build_message(text: str) -> str:
    return text if text.startswith("[RESEARCH]") else f"[RESEARCH] {text}"


def send_research_alert(message: str, *, bot_token: str | None, chat_id: str | None) -> bool:
    if not bot_token or not chat_id:
        return False

    payload = {"chat_id": chat_id, "text": _build_message(message)}
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    if requests is not None:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return True

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=15):
        return True
