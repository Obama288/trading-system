from __future__ import annotations


def decide_mode(*, market_regime: str, has_degraded_hypothesis: bool) -> tuple[str, str]:
    if has_degraded_hypothesis:
        return "backtest", "active hypothesis win_rate dropped below threshold"
    if market_regime in {"volatile", "trending"}:
        return "live", f"market regime is {market_regime}"
    return "backtest", f"market regime is {market_regime}"
