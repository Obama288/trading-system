import pytest


def _build_snapshot(closes: list[float]):
    from apps.market_data.domain.snapshot_builder import build_market_snapshot

    return build_market_snapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        last_price=closes[-1],
        bid=closes[-1] - 0.1,
        ask=closes[-1] + 0.1,
        closes=closes,
        highs=[price + 1.0 for price in closes],
        lows=[price - 1.0 for price in closes],
    )


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


def test_build_snapshot_uses_true_ema_20_for_non_linear_closes():
    closes = [100 + i * 0.7 + ((i % 5) - 2) * 1.3 for i in range(60)]

    snapshot = _build_snapshot(closes)

    assert snapshot.indicators.ema_20 == pytest.approx(134.904364544817)


def test_build_snapshot_uses_true_ema_50_for_non_linear_closes():
    closes = [200 + i * 0.4 + ((i % 7) - 3) * 0.9 for i in range(80)]

    snapshot = _build_snapshot(closes)

    assert snapshot.indicators.ema_50 == pytest.approx(221.7007162619758)


def test_build_snapshot_true_ema_differs_from_last_period_sma_on_non_linear_closes():
    closes = [100 + i * 0.7 + ((i % 5) - 2) * 1.3 for i in range(60)]

    snapshot = _build_snapshot(closes)
    last_20_sma = sum(closes[-20:]) / 20

    assert snapshot.indicators.ema_20 != pytest.approx(last_20_sma)
