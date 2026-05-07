from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.signal_observation.candles import Candle
from research.signal_observation.setup_b import SignalDirection
from research.signal_observation.setup_b_discovery_crosscheck import (
    B8_RETIRE,
    B8_SURVIVES,
    B8_TOO_FEW,
    build_discovery_high_vol_eligible_indices,
    build_discovery_crosscheck_report,
    evaluate_b8_gate,
    reconstruct_discovery_high_vol_entries,
    run_discovery_random_1r_baseline,
)
from research.signal_observation.setup_b_exit_research import (
    VARIANT_A,
    ExitEntry,
    evaluate_exit_variant,
    metrics_for_outcomes,
)
from research.signal_observation.setup_b_high_vol_validation import DISCOVERY_START


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


def test_discovery_validation_window_split_in_real_data() -> None:
    entries, reconstruction, candles_by_symbol = reconstruct_discovery_high_vol_entries(DATA_DIR)

    assert reconstruction["window"] == "discovery"
    assert reconstruction["all_discovery_observations"] >= len(entries)
    assert all(entry.entry_time >= DISCOVERY_START for entry in entries)
    assert all(candles_by_symbol[symbol] for symbol in candles_by_symbol)


def test_discovery_window_only_high_vol_extraction(monkeypatch: pytest.MonkeyPatch) -> None:
    before = DISCOVERY_START - timedelta(hours=4)
    after = DISCOVERY_START + timedelta(hours=4)
    candles = [
        Candle(before, Decimal("90"), Decimal("100"), Decimal("80"), Decimal("95"), Decimal("1")),
        Candle(after, Decimal("100"), Decimal("110"), Decimal("90"), Decimal("105"), Decimal("1")),
    ]

    def fake_load(data_dir: object) -> dict[str, list[Candle]]:
        return {"BTCUSDT": candles, "ETHUSDT": candles, "SOLUSDT": candles}

    def fake_detect(candles_arg: object, *, symbol: str, direction: SignalDirection) -> list[object]:
        if symbol != "BTCUSDT" or direction is not SignalDirection.LONG:
            return []
        return [
            SimpleNamespace(
                symbol=symbol,
                signal_time=before,
                entry_time=before,
                entry_price=Decimal("95"),
                stop=Decimal("90"),
                atr_at_entry=Decimal("9"),
                signal_direction=direction,
            ),
            SimpleNamespace(
                symbol=symbol,
                signal_time=after,
                entry_time=after,
                entry_price=Decimal("105"),
                stop=Decimal("100"),
                atr_at_entry=Decimal("11"),
                signal_direction=direction,
            ),
        ]

    monkeypatch.setattr(
        "research.signal_observation.setup_b_discovery_crosscheck.load_bitget_4h_candles",
        fake_load,
    )
    monkeypatch.setattr(
        "research.signal_observation.setup_b_discovery_crosscheck.detect_setup_b",
        fake_detect,
    )
    monkeypatch.setattr(
        "research.signal_observation.setup_b_discovery_crosscheck._validation_atr_thresholds",
        lambda candles_by_symbol: {"BTCUSDT": Decimal("10"), "ETHUSDT": Decimal("10"), "SOLUSDT": Decimal("10")},
    )

    entries, reconstruction, _ = reconstruct_discovery_high_vol_entries("unused")

    assert len(entries) == 1
    assert entries[0].entry_time == after
    assert reconstruction["high_vol_observations"] == 1


def test_fixed_1r_exit_outcome() -> None:
    candles = [
        _candle(0, "100", "101", "99", "100"),
        _candle(1, "100", "111", "99", "108"),
    ]

    outcome = evaluate_exit_variant(entry=_entry(), candles=candles, variant=VARIANT_A)

    assert outcome.outcome == "win"
    assert outcome.result_r == Decimal("1")


def test_stop_first_same_candle_ambiguity() -> None:
    candles = [
        _candle(0, "100", "101", "99", "100"),
        _candle(1, "100", "111", "89", "105"),
    ]

    outcome = evaluate_exit_variant(entry=_entry(), candles=candles, variant=VARIANT_A)

    assert outcome.outcome == "loss"
    assert outcome.result_r == Decimal("-1")


def test_cost_adjusted_expectancy_under_moderate_cost() -> None:
    win = evaluate_exit_variant(
        entry=_entry(),
        candles=[_candle(0, "100", "101", "99", "100"), _candle(1, "100", "111", "99", "108")],
        variant=VARIANT_A,
    )
    flat = evaluate_exit_variant(
        entry=_entry(),
        candles=[_candle(0, "100", "101", "99", "100"), _candle(1, "100", "105", "95", "101")],
        variant=VARIANT_A,
    )

    metrics = metrics_for_outcomes([win, flat])

    assert metrics["raw_expectancy_r"] == Decimal("0.5")
    assert metrics["post_cost_expectancy_r"]["moderate"] == Decimal("0.42")


def test_conditional_random_comparison_under_fixed_1r(monkeypatch: pytest.MonkeyPatch) -> None:
    candles = [_candle(0, "100", "101", "99", "100")]
    candles.extend(_candle(i, "100", "111", "99", "108") for i in range(1, 14))

    monkeypatch.setattr(
        "research.signal_observation.setup_b_discovery_crosscheck.build_discovery_high_vol_eligible_indices",
        lambda candles_by_symbol: {"BTCUSDT": [1, 2]},
    )

    summary = run_discovery_random_1r_baseline(
        entries=[_entry()],
        candles_by_symbol={"BTCUSDT": candles},
        seed=7,
        iterations=3,
    )

    assert summary["post_cost_expectancy_r"]["p75"] is not None
    assert summary["flat_rate"]["median"] is not None


def test_b8_gate_passes_all_conditions() -> None:
    actual = {
        "n": 15,
        "post_cost_expectancy_r": {"moderate": Decimal("0.02")},
    }
    random_summary = {"post_cost_expectancy_r": {"p75": Decimal("0.01")}}

    gate = evaluate_b8_gate(actual, random_summary)

    assert gate["decision"] == B8_SURVIVES
    assert gate["conditions"]["n_ge_15"] is True
    assert gate["conditions"]["post_cost_moderate_expectancy_gt_0"] is True
    assert gate["conditions"]["beats_conditional_random_p75"] is True


def test_b8_gate_fails_if_n_below_floor() -> None:
    actual = {
        "n": 14,
        "post_cost_expectancy_r": {"moderate": Decimal("0.02")},
    }
    random_summary = {"post_cost_expectancy_r": {"p75": Decimal("0.01")}}

    gate = evaluate_b8_gate(actual, random_summary)

    assert gate["decision"] == B8_TOO_FEW
    assert gate["conditions"]["n_ge_15"] is False


def test_b8_gate_fails_if_moderate_expectancy_nonpositive() -> None:
    actual = {
        "n": 15,
        "post_cost_expectancy_r": {"moderate": Decimal("0")},
    }
    random_summary = {"post_cost_expectancy_r": {"p75": Decimal("-0.01")}}

    gate = evaluate_b8_gate(actual, random_summary)

    assert gate["decision"] == B8_RETIRE
    assert gate["conditions"]["post_cost_moderate_expectancy_gt_0"] is False


def test_b8_gate_fails_if_random_p75_not_beaten() -> None:
    actual = {
        "n": 15,
        "post_cost_expectancy_r": {"moderate": Decimal("0.01")},
    }
    random_summary = {"post_cost_expectancy_r": {"p75": Decimal("0.02")}}

    gate = evaluate_b8_gate(actual, random_summary)

    assert gate["decision"] == B8_RETIRE
    assert gate["conditions"]["beats_conditional_random_p75"] is False


def test_report_json_structure_includes_side_by_side() -> None:
    report = build_discovery_crosscheck_report(
        entries=[],
        candles_by_symbol={},
        reconstruction={"high_vol_observations": 0},
        b7_exit_artifact={
            "actual_metrics": {
                "A_FIXED_1R": {
                    "n": 62,
                    "post_cost_expectancy_r": {"moderate": "0.016"},
                }
            },
            "conditional_random_summary": {
                "A_FIXED_1R": {
                    "post_cost_expectancy_r": {"p75": "-0.031"},
                }
            },
        },
        iterations=0,
    )

    assert report["schema"] == "setup_b_discovery_crosscheck_v1"
    assert report["b7_validation_side_by_side"]["validation_n"] == 62


def test_eligible_indices_use_discovery_window(monkeypatch: pytest.MonkeyPatch) -> None:
    candles = [
        Candle(
            DISCOVERY_START - timedelta(hours=8) + timedelta(hours=4 * i),
            Decimal("100") + Decimal(i),
            Decimal("110") + Decimal(i),
            Decimal("90") + Decimal(i),
            Decimal("105") + Decimal(i),
            Decimal("1"),
        )
        for i in range(30)
    ]
    candles_by_symbol = {"BTCUSDT": candles, "ETHUSDT": candles, "SOLUSDT": candles}
    monkeypatch.setattr(
        "research.signal_observation.setup_b_discovery_crosscheck._validation_atr_thresholds",
        lambda values: {"BTCUSDT": Decimal("1"), "ETHUSDT": Decimal("1"), "SOLUSDT": Decimal("1")},
    )

    eligible = build_discovery_high_vol_eligible_indices(candles_by_symbol, timeout_bars=3)

    assert all(index >= 2 for index in eligible["BTCUSDT"])
    assert all(index <= len(candles) - 4 for index in eligible["BTCUSDT"])


def test_discovery_crosscheck_modules_do_not_import_network_or_private_libraries() -> None:
    paths = [
        REPO / "research" / "signal_observation" / "setup_b_discovery_crosscheck.py",
        REPO / "research" / "signal_observation" / "run_setup_b_discovery_crosscheck.py",
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
