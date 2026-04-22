from __future__ import annotations

from statistics import mean


def compute_win_rate(trades: list[dict]) -> float:
    if not trades:
        return 0.0
    wins = sum(1 for trade in trades if trade["win"])
    return round((wins / len(trades)) * 100, 2)


def compute_avg_rr(trades: list[dict]) -> float:
    if not trades:
        return 0.0
    return round(mean(trade["rr"] for trade in trades), 2)


def compute_avg_duration_candles(trades: list[dict]) -> float:
    if not trades:
        return 0.0
    return round(mean(trade["duration_candles"] for trade in trades), 2)


def compute_sharpe(trades: list[dict]) -> float:
    if len(trades) < 2:
        return 0.0
    returns = [trade["rr"] if trade["win"] else -1.0 for trade in trades]
    avg_return = mean(returns)
    variance = sum((value - avg_return) ** 2 for value in returns) / (len(returns) - 1)
    if variance <= 0:
        return 0.0
    return round(avg_return / (variance ** 0.5), 3)


def classify_confidence(sample_count: int, win_rate: float) -> str:
    if sample_count > 50 and win_rate > 55:
        return "HIGH"
    if sample_count > 30 and win_rate > 50:
        return "MEDIUM"
    return "LOW"


def summarize_trades(trades: list[dict]) -> dict:
    session_stats: dict[str, dict] = {}
    for session in ("asia", "london", "ny", "london_ny_overlap"):
        session_trades = [trade for trade in trades if trade["session"] == session]
        session_stats[session] = {
            "sample_count": len(session_trades),
            "win_rate": compute_win_rate(session_trades),
        }

    best_session = max(
        session_stats.items(),
        key=lambda item: (item[1]["win_rate"], item[1]["sample_count"]),
    )[0]
    sample_count = len(trades)
    win_rate = compute_win_rate(trades)
    return {
        "win_rate": win_rate,
        "avg_rr": compute_avg_rr(trades),
        "avg_duration_candles": compute_avg_duration_candles(trades),
        "sample_count": sample_count,
        "best_session": best_session,
        "confidence": classify_confidence(sample_count, win_rate),
        "sharpe": compute_sharpe(trades),
    }
