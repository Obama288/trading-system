"""Summary metrics for signal observation outcome results."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from .models import OutcomeResult


@dataclass(frozen=True, slots=True)
class SummaryMetrics:
    """Aggregate R-based outcome metrics."""

    observation_count: int
    resolved_count: int
    win_count: int
    loss_count: int
    flat_count: int
    win_rate: Decimal | None
    expectancy_r: Decimal | None
    profit_factor: Decimal | None
    avg_win_r: Decimal | None
    avg_loss_r: Decimal | None


def summarize_outcomes(results: Sequence[OutcomeResult]) -> SummaryMetrics:
    """Summarize final R results without mutating or filtering inputs."""

    resolved = [result.final_r for result in results if result.final_r is not None]
    wins = [value for value in resolved if value > Decimal("0")]
    losses = [value for value in resolved if value < Decimal("0")]
    flats = [value for value in resolved if value == Decimal("0")]

    resolved_count = len(resolved)
    win_count = len(wins)
    loss_count = len(losses)
    flat_count = len(flats)

    if resolved_count == 0:
        return SummaryMetrics(
            observation_count=len(results),
            resolved_count=0,
            win_count=0,
            loss_count=0,
            flat_count=0,
            win_rate=None,
            expectancy_r=None,
            profit_factor=None,
            avg_win_r=None,
            avg_loss_r=None,
        )

    sum_wins = sum(wins, Decimal("0"))
    sum_losses = sum(losses, Decimal("0"))

    return SummaryMetrics(
        observation_count=len(results),
        resolved_count=resolved_count,
        win_count=win_count,
        loss_count=loss_count,
        flat_count=flat_count,
        win_rate=Decimal(win_count) / Decimal(resolved_count),
        expectancy_r=sum(resolved, Decimal("0")) / Decimal(resolved_count),
        profit_factor=_profit_factor(sum_wins, sum_losses),
        avg_win_r=_average(wins),
        avg_loss_r=_average(losses),
    )


def _average(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    return sum(values, Decimal("0")) / Decimal(len(values))


def _profit_factor(sum_wins: Decimal, sum_losses: Decimal) -> Decimal | None:
    if sum_losses == Decimal("0"):
        return None
    return sum_wins / abs(sum_losses)
