from apps.risk_engine.domain.sizing import (
    compute_max_loss_usdt,
    compute_notional_usdt,
    compute_position_size,
)


def test_compute_max_loss_usdt():
    assert compute_max_loss_usdt(10000.0, 0.005) == 50.0


def test_compute_position_size():
    assert compute_position_size(100.0, 95.0, 50.0) == 10.0


def test_compute_notional_usdt():
    assert compute_notional_usdt(100.0, 10.0) == 1000.0
