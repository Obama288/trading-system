from __future__ import annotations

from decimal import Decimal

from research.signal_observation.models import OutcomeResult
from research.signal_observation.summary import SummaryMetrics, summarize_outcomes


def _result(value: Decimal | None) -> OutcomeResult:
    return OutcomeResult(outcome_window_candles=24, final_r=value)


def test_empty_results_do_not_crash() -> None:
    metrics = summarize_outcomes([])

    assert metrics == SummaryMetrics(
        observation_count=0,
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


def test_all_unresolved_results_do_not_crash() -> None:
    metrics = summarize_outcomes([_result(None), _result(None)])

    assert metrics.observation_count == 2
    assert metrics.resolved_count == 0
    assert metrics.expectancy_r is None
    assert metrics.profit_factor is None


def test_mixed_wins_losses_and_flats_calculate_counts() -> None:
    metrics = summarize_outcomes(
        [_result(Decimal("2")), _result(Decimal("-1")), _result(Decimal("0"))]
    )

    assert metrics.observation_count == 3
    assert metrics.resolved_count == 3
    assert metrics.win_count == 1
    assert metrics.loss_count == 1
    assert metrics.flat_count == 1


def test_expectancy_r_is_average_of_resolved_results() -> None:
    metrics = summarize_outcomes(
        [_result(Decimal("2")), _result(Decimal("-1")), _result(Decimal("0"))]
    )

    assert metrics.expectancy_r == Decimal("1") / Decimal("3")
    assert isinstance(metrics.expectancy_r, Decimal)


def test_profit_factor_is_sum_wins_over_absolute_sum_losses() -> None:
    metrics = summarize_outcomes(
        [_result(Decimal("2")), _result(Decimal("1")), _result(Decimal("-2"))]
    )

    assert metrics.profit_factor == Decimal("1.5")
    assert metrics.avg_win_r == Decimal("1.5")
    assert metrics.avg_loss_r == Decimal("-2")


def test_no_loss_case_returns_none_profit_factor() -> None:
    metrics = summarize_outcomes([_result(Decimal("2")), _result(Decimal("1"))])

    assert metrics.profit_factor is None
    assert metrics.avg_loss_r is None


def test_decimal_values_are_preserved() -> None:
    metrics = summarize_outcomes([_result(Decimal("1.25")), _result(Decimal("-0.25"))])

    assert isinstance(metrics.win_rate, Decimal)
    assert isinstance(metrics.expectancy_r, Decimal)
    assert isinstance(metrics.profit_factor, Decimal)
    assert metrics.expectancy_r == Decimal("0.50")
