from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from research.hypothesis_agent.analysis.sessions import classify_session

try:
    import requests
except ImportError:  # pragma: no cover - exercised only when requests is installed
    requests = None


def _utc_datetime_from_ms(value: str) -> datetime:
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)


class OkxMarketDataFetcher:
    def __init__(self, base_url: str = "https://www.okx.com", session: object | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = session

    def _request_json(self, path: str, params: dict[str, str]) -> dict:
        url = f"{self.base_url}{path}?{urlencode(params)}"
        if self.session is not None:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        if requests is not None:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()

        request = Request(url, headers={"User-Agent": "hypothesis-agent"})
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
        rows = payload.get("data", [])
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
            }
            candle["body"] = abs(candle["close"] - candle["open"])
            candle["session"] = classify_session(timestamp)
            candles.append(candle)
        candles.sort(key=lambda item: item["timestamp"])
        return candles

    def fetch_history(self, symbol: str, timeframe: str, *, days: int, limit: int | None = None) -> list[dict]:
        if limit is not None:
            remaining = max(1, limit)
            all_candles: list[dict] = []
            after: str | None = None

            while remaining > 0:
                batch = self.fetch_candles(symbol, timeframe, limit=min(100, remaining), after=after)
                if not batch:
                    break
                all_candles = batch + all_candles
                remaining -= len(batch)
                oldest = int(batch[0]["timestamp"].timestamp() * 1000)
                after = str(oldest)  # returns records older than this timestamp

            all_candles.sort(key=lambda item: item["timestamp"])
            return all_candles[-limit:]

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        all_candles: list[dict] = []
        after: str | None = None

        while True:
            batch = self.fetch_candles(symbol, timeframe, limit=100, after=after)
            if not batch:
                break
            all_candles = batch + all_candles
            if batch[0]["timestamp"] <= cutoff:
                break
            oldest = int(batch[0]["timestamp"].timestamp() * 1000)
            after = str(oldest)  # returns records older than this timestamp

        filtered = [item for item in all_candles if item["timestamp"] >= cutoff]
        filtered.sort(key=lambda item: item["timestamp"])
        return filtered
