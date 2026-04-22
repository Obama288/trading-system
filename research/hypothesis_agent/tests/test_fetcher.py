from __future__ import annotations

from research.hypothesis_agent.data.fetcher import OkxMarketDataFetcher


def test_fetch_candles_parses_okx_payload():
    class DummyFetcher(OkxMarketDataFetcher):
        def _request_json(self, path: str, params: dict[str, str]) -> dict:
            assert path == "/api/v5/market/candles"
            assert params["instId"] == "BTC-USDT"
            return {
                "data": [
                    ["1714608000000", "100", "110", "95", "108", "42"],
                    ["1714607100000", "99", "101", "97", "100", "40"],
                ]
            }

    fetcher = DummyFetcher()
    candles = fetcher.fetch_candles("BTC-USDT", "15m", limit=2)

    assert len(candles) == 2
    assert candles[0]["close"] == 100.0
    assert candles[1]["high"] == 110.0
    assert candles[0]["session"] in {"asia", "london", "ny", "london_ny_overlap"}
