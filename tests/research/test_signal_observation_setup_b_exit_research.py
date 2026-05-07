from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from research.signal_observation.candles import Candle
from research.signal_observation.setup_b_exit_research import (
    B7_CANDIDATE,
    B7_RETIRE,
    EXPECTED_HIGH_VOL_N,
    VARIANT_A,
    VARIANT_B,
    VARIANT_C,
    ExitEntry,
    build_exit_research_report,
    evaluate_exit_variant,
    evaluate_variant_gate,
    metrics_for_outcomes,
    reconstruct_high_vol_entries,
    run_conditional_random_exit_baseline,
)


REPO = Path(__file__).parent.parent.parent
DATA_DIR = REPO / "research" / "signal_observation" / "data" / "bitget"


def _candle(index: int, open_: str, high: str, low: str, close: str) -> Candle:
    return Candle(
        timestamp=datetime(2025, 1, 1, tzinfo=UTC) + timedelta(hours=4 * index),
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal("100"),
    )


def _entry(direction: str = "long") -> ExitEntry:
    entry_price = Decimal("100")
    stop = Decimal("90") if direction == "long" else Decimal("110")
    return ExitEntry(
        symbol="BTCUSDT",
        direction=direction,
        entry_index=0,
        entry_time=datetime(2025, 1, 1, tzinfo=UTC),
        entry_price=entry_price,
        stop=stop,
        risk_distance=Decimal("10"),
    )


def test_reconstruct_high_vol_subset_matches_frozen_n() -> None:
    entries, reconstruction, _ = reconstruct_high_vol_entries(DATA_DIR)

    assert len(entries) == EXPECTED_HIGH_VOL_N
    assert reconstruction["reconstructed_n"] == EXPECTED_HIGH_VOL_N
    assert reconstruction["matched_expected_n"] is True


def test_build_report_fails_on_reconstruction_mismatch() -> None:
    with pytest.raises(ValueError):
        build_exit_research_report(entries=[], candles_by_symbol={}, reconstruction={})


def test_variant_a_fixed_1r_target_outcome() -> None:
    candles = [
        _candle(0, "100", "101", "99", "100"),
        _candle(1, "100", "111", "99", "108"),
    ]

    outcome = evaluate_exit_variant(entry=_entry(), candles=candles, variant=VARIANT_A)

    assert outcome.outcome == "win"
    assert outcome.result_r == Decimal("1")
    assert outcome.bars_to_resolution == 1


def test_variant_b_protective_exit_after_activation() -> None:
    candles = [
        _candle(0, "100", "101", "99", "100"),
        _candle(1, "104", "107", "104", "106"),
        _candle(2, "106", "106", "103", "104"),
    ]

    outcome = evaluate_exit_variant(entry=_entry(), candles=candles, variant=VARIANT_B)

    assert outcome.outcome == "win"
    assert outcome.result_r == Decimal("0.3")
    assert outcome.bars_to_resolution == 2


def test_variant_b_target_wins_before_protective_retrace() -> None:
    candles = [
        _candle(0, "100", "101", "99", "100"),
        _candle(1, "104", "115", "104", "114"),
    ]

    outcome = evaluate_exit_variant(entry=_entry(), candles=candles, variant=VARIANT_B)

    assert outcome.outcome == "win"
    assert outcome.result_r == Decimal("1.5")


def test_variant_c_breakeven_after_1r_activation() -> None:
    candles = [
        _candle(0, "100", "101", "99", "100"),
        _candle(1, "101", "110", "101", "108"),
        _candle(2, "108", "109", "100", "101"),
    ]

    outcome = evaluate_exit_variant(entry=_entry(), candles=candles, variant=VARIANT_C)

    assert outcome.outcome == "flat"
    assert outcome.result_r == Decimal("0")
    assert outcome.bars_to_resolution == 2


def test_variant_c_original_stop_applies_before_activation() -> None:
    candles = [
        _candle(0, "100", "101", "99", "100"),
        _candle(1, "100", "110", "89", "105"),
    ]

    outcome = evaluate_exit_variant(entry=_entry(), candles=candles, variant=VARIANT_C)

    assert outcome.outcome == "loss"
    assert outcome.result_r == Decimal("-1")


def test_stop_first_same_candle_ambiguity() -> None:
    candles = [
        _candle(0, "100", "101", "99", "100"),
        _candle(1, "100", "120", "89", "105"),
    ]

    outcome = evaluate_exit_variant(entry=_entry(), candles=candles, variant=VARIANT_A)

    assert outcome.outcome == "loss"
    assert outcome.result_r == Decimal("-1")


def test_cost_adjusted_expectancy_under_moderate_cost() -> None:
    candles = [
        _candle(0, "100", "101", "99", "100"),
        _candle(1, "100", "111", "99", "108"),
    ]
    win = evaluate_exit_variant(entry=_entry(), candles=candles, variant=VARIANT_A)
    loss = evaluate_exit_variant(
        entry=_entry(),
        candles=[candles[0], _candle(1, "100", "101", "89", "91")],
        variant=VARIANT_A,
    )

    metrics = metrics_for_outcomes([win, loss])

    assert metrics["raw_expectancy_r"] == Decimal("0")
    assert metrics["post_cost_expectancy_r"]["moderate"] == Decimal("-0.08")


def test_conditional_random_comparison_uses_same_exit_logic(monkeypatch: pytest.MonkeyPatch) -> None:
    candles = [_candle(0, "100", "101", "99", "100")]
    candles.extend(_candle(i, "100", "111", "99", "108") for i in range(1, 14))
    entries = [_entry()]

    def fake_eligible(*args: object, **kwargs: object) -> dict[str, list[int]]:
        return {"BTCUSDT": [1, 2]}

    monkeypatch.setattr(
        "research.signal_observation.setup_b_exit_research.build_vol_high_eligible_indices",
        fake_eligible,
    )

    summary = run_conditional_random_exit_baseline(
        entries=entries,
        candles_by_symbol={"BTCUSDT": candles},
        seed=7,
        iterations=3,
    )

    assert set(summary) == {VARIANT_A, VARIANT_B, VARIANT_C}
    assert summary[VARIANT_A]["post_cost_expectancy_r"]["p75"] is not None


def test_b7_pass_and_fail_gate() -> None:
    actual_pass = {
        "n": EXPECTED_HIGH_VOL_N,
        "post_cost_expectancy_r": {"moderate": Decimal("0.02")},
    }
    random_summary = {"post_cost_expectancy_r": {"p75": Decimal("0.01")}}

    passed = evaluate_variant_gate(actual_pass, random_summary)

    assert passed["passes"] is True

    actual_fail = {
        "n": EXPECTED_HIGH_VOL_N,
        "post_cost_expectancy_r": {"moderate": Decimal("-0.01")},
    }

    failed = evaluate_variant_gate(actual_fail, random_summary)

    assert failed["passes"] is False


def test_b7_decision_constants_are_frozen() -> None:
    assert B7_CANDIDATE == "EXIT_VARIANT_RESEARCH_CANDIDATE"
    assert B7_RETIRE == "RETIRE_HIGH_VOL_SETUP_B"


def test_exit_research_modules_do_not_import_network_or_private_libraries() -> None:
    paths = [
        REPO / "research" / "signal_observation" / "setup_b_exit_research.py",
        REPO / "research" / "signal_observation" / "run_setup_b_exit_research.py",
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
