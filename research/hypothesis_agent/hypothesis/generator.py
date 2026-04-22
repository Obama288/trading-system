from __future__ import annotations


def _score(row: dict) -> float:
    return round(row["win_rate"] + (row["avg_rr"] * 10) + (row["sample_count"] * 0.1) + row["sharpe"], 3)


def _is_promotable(row: dict) -> bool:
    return row["sample_count"] >= 30 and row["avg_rr"] > 0 and row["sharpe"] > 0


def generate_top_hypotheses(rows: list[dict], limit: int = 3) -> list[dict]:
    promotable_rows = [row for row in rows if _is_promotable(row)]
    ranked = sorted(promotable_rows, key=_score, reverse=True)
    top_rows = ranked[:limit]
    hypotheses: list[dict] = []
    for row in top_rows:
        hypotheses.append(
            {
                "pattern": row["pattern"],
                "symbol": row["symbol"],
                "timeframe": row["timeframe"],
                "direction": row["direction"],
                "best_session": row["best_session"],
                "win_rate": row["win_rate"],
                "avg_rr": row["avg_rr"],
                "sample_count": row["sample_count"],
                "confidence": row["confidence"],
                "statement": (
                    f"{row['pattern']} on {row['symbol']} {row['timeframe']} performs best in "
                    f"{row['best_session']} with {row['win_rate']}% win_rate."
                ),
            }
        )
    return hypotheses
