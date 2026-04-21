from __future__ import annotations


def compute_max_loss_usdt(equity_usdt: float, max_risk_fraction: float) -> float:
    return round(equity_usdt * max_risk_fraction, 2)


def compute_position_size(entry_price: float, stop_loss: float, max_loss_usdt: float) -> float:
    stop_distance = abs(entry_price - stop_loss)
    if stop_distance <= 0:
        raise ValueError("Stop distance must be positive")
    return round(max_loss_usdt / stop_distance, 6)


def compute_notional_usdt(entry_price: float, position_size: float) -> float:
    return round(entry_price * position_size, 2)


def compute_risk_pct_of_equity(max_loss_usdt: float, equity_usdt: float) -> float:
    if equity_usdt <= 0:
        return 0.0
    return round((max_loss_usdt / equity_usdt) * 100, 4)
