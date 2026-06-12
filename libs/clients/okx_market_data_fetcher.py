from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None


def _utc_datetime_from_ms(value: str) -> datetime:
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)


class OkxMarketDataFetcher:
    """
    Production-safe OKX market data fetcher.

    Notes:
    - This is intentionally not sourced from research/* to keep the production boundary clean.
    - The output shape matches what the paper runner and reconcile scheduler expect:
      candles with timestamp/open/high/low/close/volume (and optional session/body fields).
    """

    def __init__(self, base_url: str = "https://www.okx.com") -> None:
        self.base_url = base_url.rstrip("/")

    def _request_json(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self.base_url}{path}?{urlencode(params)}"

        if httpx is not None:
            # Synchronous by design: call sites either run in sync loops or in a worker thread.
            response = httpx.get(url, timeout=10.0, headers={"User-Agent": "trading-system"})
            response.raise_for_status()
            return response.json()

        request = Request(url, headers={"User-Agent": "trading-system"})
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int = 100,
        after: str | None = None,
    ) -> list[dict]:
        params = {"instId": symbol, "bar": timeframe, "limit": str(limit)}
        if after is not None:
            params["after"] = after

        payload = self._request_json("/api/v5/market/candles", params)
        rows = payload.get("data", []) or []

        candles: list[dict] = []
        for row in rows:
            # row[8] is the OKX confirm flag: "1" = closed bar, "0" = unclosed/live.
            if len(row) > 8 and row[8] != "1":
                continue
            timestamp = _utc_datetime_from_ms(row[0])
            candle = {
                "timestamp": timestamp,
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                # Keep compatibility with snapshot builders that read `session` opportunistically.
                "session": "unknown",
            }
            candle["body"] = abs(candle["close"] - candle["open"])
            candles.append(candle)

        candles.sort(key=lambda item: item["timestamp"])
        return candles

