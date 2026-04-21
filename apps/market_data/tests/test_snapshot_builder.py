import pytest

def test_build_snapshot_raises_on_insufficient_data():
    from apps.market_data.domain.snapshot_builder import build_market_snapshot
    with pytest.raises(ValueError, match="Insufficient candle data"):
        build_market_snapshot(
            symbol="BTCUSDT",
            timeframe="15m",
            last_price=100.0,
            bid=99.9,
            ask=100.1,
            closes=[100.0] * 10,
            highs=[101.0] * 10,
            lows=[99.0] * 10,
        )
