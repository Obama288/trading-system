from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

from research.signal_observation.setup_b_cost_aware import (
    B6_CANDIDATE,
    B6_LONG_SHOT,
    B6_RETIRE,
    b6_decision,
    flat_trade_breakdown,
    mfe_breakdown,
    post_cost_metrics,
    random_post_cost_comparison,
)


def _obs(outcome: str, mfe: str = "0.5", mae: str = "-0.4") -> dict[str, object]:
    return {
        "outcome_1_5r": outcome,
        "mfe_1_5r": mfe,
        "mae_1_5r": mae,
    }


def test_post_cost_expectancy_subtracts_cost_per_trade() -> None:
    observations = [_obs("win"), _obs("loss"), _obs("flat")]

    metrics = post_cost_metrics(observations, Decimal("0.10"))

    assert metrics["post_cost_total_r"] == Decimal("0.2")
    assert metrics["post_cost_expectancy_r"] == Decimal("0.2") / Decimal("3")
    assert metrics["post_cost_positive_count"] == 1
    assert metrics["post_cost_negative_count"] == 2


def test_post_cost_profit_factor_includes_costed_flats_as_losses() -> None:
    observations = [_obs("win"), _obs("loss"), _obs("flat")]

    metrics = post_cost_metrics(observations, Decimal("0.10"))

    assert metrics["post_cost_profit_factor"] == Decimal("1.4") / Decimal("1.2")


def test_random_expectancy_distribution_cost_subtraction() -> None:
    random_target = {
        "expectancy_r": {
            "median": "0.05",
            "p75": "0.10",
            "p90": "0.20",
        }
    }

    adjusted = random_post_cost_comparison(random_target, Decimal("0.04"))

    assert adjusted["random_median_expectancy_post_cost"] == Decimal("0.01")
    assert adjusted["random_p75_expectancy_post_cost"] == Decimal("0.06")
    assert adjusted["random_p90_expectancy_post_cost"] == Decimal("0.16")


def test_mfe_percentiles_and_thresholds() -> None:
    observations = [
        _obs("flat", "0.2"),
        _obs("flat", "0.5"),
        _obs("flat", "1.0"),
        _obs("win", "1.5"),
    ]

    metrics = mfe_breakdown(observations)

    assert metrics["median_mfe_r"] == Decimal("0.75")
    assert metrics["p25_mfe_r"] == Decimal("0.425")
    assert metrics["p75_mfe_r"] == Decimal("1.125")
    assert metrics["pct_reached_0_5r"] == Decimal("0.75")
    assert metrics["pct_reached_1_0r"] == Decimal("0.5")


def test_flat_trade_mfe_breakdown_and_classification() -> None:
    observations = [
        _obs("flat", "0.2", "-0.2"),
        _obs("flat", "0.9", "-0.3"),
        _obs("flat", "0.6", "-0.9"),
        _obs("win", "1.5", "-0.5"),
    ]

    metrics = flat_trade_breakdown(observations)

    assert metrics["flat_count"] == 3
    assert metrics["median_flat_mfe_r"] == Decimal("0.6")
    assert metrics["pct_flat_mfe_ge_0_5r"] == Decimal("2") / Decimal("3")
    assert metrics["flat_classification_counts"] == {
        "near_win": 1,
        "dead_flat": 1,
        "adverse_flat": 1,
        "ordinary_flat": 0,
    }


def test_b6_decision_retire_when_costs_negative_and_no_mfe_opportunity() -> None:
    post_cost = _post_cost_scenarios("-0.01", "-0.02", "-0.03")
    flats = {"median_flat_mfe_r": Decimal("0.4"), "pct_flat_mfe_ge_1_0r": Decimal("0.1")}

    decision = b6_decision(post_cost, flats)

    assert decision["decision"] == B6_RETIRE
    assert decision["mfe_opportunity"] is False


def test_b6_decision_long_shot_when_costs_negative_but_mfe_opportunity_exists() -> None:
    post_cost = _post_cost_scenarios("-0.01", "-0.02", "-0.03")
    flats = {"median_flat_mfe_r": Decimal("0.75"), "pct_flat_mfe_ge_1_0r": Decimal("0.1")}

    decision = b6_decision(post_cost, flats)

    assert decision["decision"] == B6_LONG_SHOT
    assert decision["mfe_opportunity"] is True


def test_b6_decision_candidate_when_moderate_cost_survives_and_mfe_supports() -> None:
    post_cost = _post_cost_scenarios("-0.01", "0.02", "-0.03")
    flats = {"median_flat_mfe_r": Decimal("0.75"), "pct_flat_mfe_ge_1_0r": Decimal("0.1")}

    decision = b6_decision(post_cost, flats)

    assert decision["decision"] == B6_CANDIDATE


def test_cost_aware_modules_do_not_import_network_or_private_libraries() -> None:
    repo = Path(__file__).parent.parent.parent
    paths = [
        repo / "research" / "signal_observation" / "setup_b_cost_aware.py",
        repo / "research" / "signal_observation" / "run_setup_b_cost_aware.py",
    ]
    forbidden_imports = {
        "".join(("url", "lib")),
        "".join(("req", "uests")),
        "".join(("ht", "tp")),
        "".join(("so", "cket")),
        ".".join(("http", "client")),
    }
    forbidden_terms = {
        "".join(("api", "Key")),
        "-".join(("ACCESS", "KEY")),
        "".join(("sig", "nature")),
        "".join(("sec", "ret")),
        "".join(("pass", "phrase")),
        "".join(("Author", "ization")),
        "".join(("acc", "ount")),
        "".join(("bal", "ance")),
        "".join(("pos", "ition")),
        "".join(("ord", "er")),
        "".join(("can", "cel")),
        "_".join(("set", "leverage")),
    }

    for path in paths:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        imported = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        imported.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert forbidden_imports.isdisjoint(imported)
        assert not any(term in text for term in forbidden_terms)


def _post_cost_scenarios(
    optimistic: str,
    moderate: str,
    conservative: str,
) -> dict[str, dict[str, object]]:
    return {
        "optimistic": {"post_cost_expectancy_r": Decimal(optimistic)},
        "moderate": {"post_cost_expectancy_r": Decimal(moderate)},
        "conservative": {"post_cost_expectancy_r": Decimal(conservative)},
    }
