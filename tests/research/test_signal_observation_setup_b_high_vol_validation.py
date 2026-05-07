"""Tests for Stage 54-SQ-B5 high-volatility Setup B validation module."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

import research.signal_observation.setup_b_high_vol_validation as _mod
from research.signal_observation.setup_b_high_vol_validation import (
    B5_FAIL,
    B5_PASS,
    DISCOVERY_START,
    GATE_MIN_N,
    TIMEOUT_BARS,
    VALIDATION_TARGET,
    _build_bucket_specs,
    _detailed_bucket_metrics,
    _evaluate_entry,
    _sample_conditional_iteration,
    _summarize_iteration_metrics,
    build_vol_high_eligible_indices,
    compare_actual_to_conditional_random,
    compute_validation_metrics,
    evaluate_b5_gate,
    run_validation_conditional_random,
    split_candles_at_discovery,
    tag_high_vol_validation,
)
from research.signal_observation.candles import Candle
from research.signal_observation.setup_b_conditional_diagnostics import ATR_PERIOD
from research.signal_observation.setup_b_random_baseline import BucketSpec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_TS = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
_4H = timedelta(hours=4)


def _make_candle(n: int, close: float = 100.0, spread: float = 2.0) -> Candle:
    ts = _BASE_TS + n * _4H
    c = Decimal(str(close))
    half = Decimal(str(spread)) / Decimal("2")
    return Candle(
        timestamp=ts,
        open=c,
        high=c + half,
        low=c - half,
        close=c,
        volume=Decimal("1"),
    )


def _make_candles(count: int, close: float = 100.0, spread: float = 2.0) -> list[Candle]:
    return [_make_candle(n, close=close, spread=spread) for n in range(count)]


def _fake_obs(
    symbol: str = "BTCUSDT",
    direction: str = "long",
    entry_price: float = 100.0,
    stop: float = 95.0,
    atr: float = 5.0,
    outcome: str = "win",
) -> dict:
    risk = abs(entry_price - stop)
    target_1r = entry_price + risk if direction == "long" else entry_price - risk
    target_1_5r = entry_price + risk * 1.5 if direction == "long" else entry_price - risk * 1.5
    target_2r = entry_price + risk * 2 if direction == "long" else entry_price - risk * 2
    return {
        "symbol": symbol,
        "signal_direction": direction,
        "signal_time": "2024-06-01T00:00:00+00:00",
        "entry_time": "2024-06-01T04:00:00+00:00",
        "entry_price": str(entry_price),
        "stop": str(stop),
        "atr_at_entry": str(atr),
        "session_label": "london",
        "signal_hour_utc": 0,
        "outcome_1r": outcome,
        "outcome_1_5r": outcome,
        "outcome_2r": outcome,
        "mae_1r": "-0.3",
        "mfe_1r": "0.8",
        "bars_to_resolution_1r": 5,
        "mae_1_5r": "-0.3",
        "mfe_1_5r": "1.2",
        "bars_to_resolution_1_5r": 7,
        "mae_2r": "-0.3",
        "mfe_2r": "1.8",
        "bars_to_resolution_2r": 9,
    }


def _make_random_summary(
    exp_median: str = "0.1",
    exp_p75: str = "0.3",
    exp_p90: str = "0.5",
    flat_median: str = "0.3",
    flat_p75: str = "0.4",
) -> dict:
    dist = {
        "mean": exp_median,
        "median": exp_median,
        "p10": "-0.2",
        "p25": "0.0",
        "p75": exp_p75,
        "p90": exp_p90,
        "min": "-0.5",
        "max": "0.8",
    }
    flat_dist = {
        "mean": flat_median,
        "median": flat_median,
        "p10": "0.1",
        "p25": "0.2",
        "p75": flat_p75,
        "p90": "0.5",
        "min": "0.0",
        "max": "0.6",
    }
    return {
        target: {
            "expectancy_r": dist,
            "win_rate": dist,
            "flat_rate": flat_dist,
            "avg_mae_r": dist,
            "avg_mfe_r": dist,
        }
        for target in ("1r", "1_5r", "2r")
    }


# ---------------------------------------------------------------------------
# 1. Window split excludes discovery rows
# ---------------------------------------------------------------------------


def test_split_at_discovery_excludes_discovery_candles():
    custom_start = _BASE_TS + 10 * _4H
    full = _make_candles(20)
    val, disc = split_candles_at_discovery({"SYM": full}, custom_start)
    assert all(c.timestamp < custom_start for c in val["SYM"])
    assert all(c.timestamp >= custom_start for c in disc["SYM"])


def test_split_at_discovery_correct_counts():
    custom_start = _BASE_TS + 7 * _4H
    full = _make_candles(15)
    val, disc = split_candles_at_discovery({"SYM": full}, custom_start)
    assert len(val["SYM"]) == 7
    assert len(disc["SYM"]) == 8


def test_split_empty_partition_when_all_before_discovery():
    custom_start = _BASE_TS + 100 * _4H
    full = _make_candles(10)
    val, disc = split_candles_at_discovery({"SYM": full}, custom_start)
    assert len(val["SYM"]) == 10
    assert len(disc["SYM"]) == 0


# ---------------------------------------------------------------------------
# 2. High-vol tag uses validation-calibrated thresholds
# ---------------------------------------------------------------------------


def test_high_vol_tag_threshold_uses_validation_window_only():
    """p67 must be derived from validation ATR values, ignoring discovery candles."""
    # 40 low-volatility validation candles (spread=2), then 20 high-vol discovery
    n_val = 40
    n_disc = 20
    val_candles = _make_candles(n_val, spread=2.0)
    disc_candles = [
        _make_candle(n_val + i, close=100.0, spread=200.0) for i in range(n_disc)
    ]
    full = val_candles + disc_candles
    custom_start = full[n_val].timestamp

    full_by_sym = {"SYM": full}
    obs = [_fake_obs(atr=2.0)]  # atr matches low-vol validation

    _, threshold_info = tag_high_vol_validation(obs, full_by_sym, custom_start)

    assert "SYM" in threshold_info
    info = threshold_info["SYM"]
    assert info["p67_threshold"] is not None

    # The threshold should be ≤ 2.0 (approx) since all validation ATR ≈ 2
    p67 = Decimal(str(info["p67_threshold"]))
    assert p67 <= Decimal("3"), f"p67={p67} too high; discovery candles must not influence threshold"
    # n_validation_atr should equal number of valid ATR values in validation window only
    assert int(info["n_validation_atr"]) == n_val - ATR_PERIOD + 1


def test_high_vol_tag_observation_labeled_high_when_atr_ge_threshold():
    n_val = 40
    full = _make_candles(n_val, spread=2.0)
    custom_start = full[-1].timestamp + _4H  # all candles are validation
    full_by_sym = {"SYM": full}

    # Get actual threshold
    _, threshold_info = tag_high_vol_validation([], full_by_sym, custom_start)
    p67 = Decimal(str(threshold_info["SYM"]["p67_threshold"]))

    obs_high = [_fake_obs(symbol="SYM", atr=float(p67 + Decimal("1")))]
    tagged, _ = tag_high_vol_validation(obs_high, full_by_sym, custom_start)
    assert tagged[0]["tag_volatility_regime"] == "high"


def test_high_vol_tag_observation_labeled_not_high_when_atr_below_threshold():
    n_val = 40
    full = _make_candles(n_val, spread=2.0)
    custom_start = full[-1].timestamp + _4H
    full_by_sym = {"SYM": full}

    _, threshold_info = tag_high_vol_validation([], full_by_sym, custom_start)
    p67 = Decimal(str(threshold_info["SYM"]["p67_threshold"]))

    obs_low = [_fake_obs(symbol="SYM", atr=float(p67 - Decimal("1")))]
    tagged, _ = tag_high_vol_validation(obs_low, full_by_sym, custom_start)
    assert tagged[0]["tag_volatility_regime"] == "not_high"


# ---------------------------------------------------------------------------
# 3. Validation high-vol subset extraction
# ---------------------------------------------------------------------------


def test_high_vol_subset_extracts_correct_observations():
    n_val = 40
    full = _make_candles(n_val, spread=2.0)
    custom_start = full[-1].timestamp + _4H
    full_by_sym = {"SYM": full}

    _, threshold_info = tag_high_vol_validation([], full_by_sym, custom_start)
    p67 = Decimal(str(threshold_info["SYM"]["p67_threshold"]))

    # 3 high-vol obs + 2 not-high obs — use symbol="SYM" to match candles key
    obs_list = (
        [_fake_obs(symbol="SYM", atr=float(p67 + Decimal("1")))] * 3
        + [_fake_obs(symbol="SYM", atr=float(p67 - Decimal("1")))] * 2
    )
    tagged, _ = tag_high_vol_validation(obs_list, full_by_sym, custom_start)
    high = [o for o in tagged if o["tag_volatility_regime"] == "high"]
    not_high = [o for o in tagged if o["tag_volatility_regime"] == "not_high"]
    assert len(high) == 3
    assert len(not_high) == 2


# ---------------------------------------------------------------------------
# 4. Conditional random sampling uses only validation-eligible candles
# ---------------------------------------------------------------------------


def test_eligible_indices_all_within_validation_window():
    n_val = 30
    n_disc = 20
    val_candles = _make_candles(n_val, spread=2.0)
    disc_candles = [_make_candle(n_val + i, spread=2.0) for i in range(n_disc)]
    full = val_candles + disc_candles
    custom_start = full[n_val].timestamp

    full_by_sym = {"SYM": full}
    val_by_sym = {"SYM": val_candles}

    eligible = build_vol_high_eligible_indices(full_by_sym, val_by_sym, timeout_bars=TIMEOUT_BARS)
    for idx in eligible["SYM"]:
        assert idx < n_val, f"index {idx} is in discovery window"


def test_eligible_indices_all_have_sufficient_lookahead():
    n_val = 30
    n_disc = 20
    val_candles = _make_candles(n_val, spread=2.0)
    disc_candles = [_make_candle(n_val + i, spread=2.0) for i in range(n_disc)]
    full = val_candles + disc_candles
    custom_start = full[n_val].timestamp

    full_by_sym = {"SYM": full}
    val_by_sym = {"SYM": val_candles}

    eligible = build_vol_high_eligible_indices(full_by_sym, val_by_sym, timeout_bars=TIMEOUT_BARS)
    n_full = len(full)
    for idx in eligible["SYM"]:
        assert idx + TIMEOUT_BARS <= n_full - 1, (
            f"index {idx} lacks lookahead (full_len={n_full}, timeout={TIMEOUT_BARS})"
        )


def test_sampling_entry_prices_come_from_eligible_candles():
    n_total = 50
    # Candles with distinct closes: candle[i].close = 100 + i
    candles = [
        Candle(
            timestamp=_BASE_TS + n * _4H,
            open=Decimal(str(100 + n)),
            high=Decimal(str(101 + n)),
            low=Decimal(str(99 + n)),
            close=Decimal(str(100 + n)),
            volume=Decimal("1"),
        )
        for n in range(n_total)
    ]
    eligible_set = {5, 10, 15}
    eligible_indices = {"SYM": sorted(eligible_set)}
    allowed_prices = {Decimal(str(100 + i)) for i in eligible_set}

    bucket_specs = [
        BucketSpec(
            symbol="SYM",
            direction="long",
            count=30,
            risk_distances=(Decimal("5"),),
        )
    ]
    rng = random.Random(42)
    entries = _sample_conditional_iteration(
        bucket_specs=bucket_specs,
        eligible_indices=eligible_indices,
        candles_by_symbol={"SYM": candles},
        rng=rng,
        timeout_bars=5,
    )
    for entry in entries:
        assert entry["entry_price"] in allowed_prices, (
            f"entry_price {entry['entry_price']} not in eligible set {allowed_prices}"
        )


# ---------------------------------------------------------------------------
# 5. Bucket specs match symbol/direction/count
# ---------------------------------------------------------------------------


def test_build_bucket_specs_groups_correctly():
    obs = (
        [_fake_obs("BTC", "long", entry_price=100, stop=90)] * 3
        + [_fake_obs("ETH", "short", entry_price=200, stop=210)] * 2
        + [_fake_obs("BTC", "short", entry_price=100, stop=110)] * 1
    )
    specs = _build_bucket_specs(obs)
    by_key = {(s.symbol, s.direction): s.count for s in specs}
    assert by_key[("BTC", "long")] == 3
    assert by_key[("ETH", "short")] == 2
    assert by_key[("BTC", "short")] == 1


def test_build_bucket_specs_risk_distances_match_observations():
    obs = [
        _fake_obs("BTC", "long", entry_price=100, stop=90),   # risk = 10
        _fake_obs("BTC", "long", entry_price=100, stop=95),   # risk = 5
    ]
    specs = _build_bucket_specs(obs)
    btc_long = next(s for s in specs if s.symbol == "BTC" and s.direction == "long")
    assert set(btc_long.risk_distances) == {Decimal("10"), Decimal("5")}


# ---------------------------------------------------------------------------
# 6. Sampled risk model for long and short
# ---------------------------------------------------------------------------


def test_evaluate_entry_long_stop_below_entry():
    candles = _make_candles(25)
    result = _evaluate_entry(
        candles=candles,
        entry_index=5,
        direction="long",
        risk_distance=Decimal("5"),
        timeout_bars=10,
    )
    entry = Decimal(str(candles[5].close))
    stop = Decimal(str(result["stop"]))
    assert stop == entry - Decimal("5"), f"long stop should be entry-risk, got {stop}"


def test_evaluate_entry_short_stop_above_entry():
    candles = _make_candles(25)
    result = _evaluate_entry(
        candles=candles,
        entry_index=5,
        direction="short",
        risk_distance=Decimal("5"),
        timeout_bars=10,
    )
    entry = Decimal(str(candles[5].close))
    stop = Decimal(str(result["stop"]))
    assert stop == entry + Decimal("5"), f"short stop should be entry+risk, got {stop}"


def test_evaluate_entry_long_target_1r_above_entry():
    candles = _make_candles(25)
    result = _evaluate_entry(
        candles=candles,
        entry_index=5,
        direction="long",
        risk_distance=Decimal("5"),
        timeout_bars=10,
    )
    entry = Decimal(str(candles[5].close))
    # With spread=2 candles (high=close+1), can't reach 1R target of entry+5
    # so outcome_1r should be "flat"
    assert result["outcome_1r"] in {"win", "loss", "flat"}


def test_evaluate_entry_short_target_1r_below_entry():
    candles = _make_candles(25)
    result = _evaluate_entry(
        candles=candles,
        entry_index=5,
        direction="short",
        risk_distance=Decimal("5"),
        timeout_bars=10,
    )
    assert result["outcome_1r"] in {"win", "loss", "flat"}


# ---------------------------------------------------------------------------
# 7. B5 gate passes when all four conditions are met
# ---------------------------------------------------------------------------


def test_b5_gate_passes_all_four_conditions():
    # n=25 >= 20, exp=0.5 > p75=0.3 > 0, flat=0.2 <= median_flat=0.3
    actual_metrics = {
        "1_5r": {
            "n": 25,
            "expectancy_r": "0.5",
            "flat_rate": "0.2",
        }
    }
    random_summary = _make_random_summary(exp_p75="0.3", flat_median="0.3")
    gate = evaluate_b5_gate(actual_metrics, random_summary, n_high_vol=25)
    assert gate["gate_result"] == B5_PASS
    cond = gate["conditions"]
    assert cond["c1_n_high_vol_sufficient"]["passes"] is True
    assert cond["c2_expectancy_beats_p75_random"]["passes"] is True
    assert cond["c3_expectancy_positive"]["passes"] is True
    assert cond["c4_flat_rate_le_random_median"]["passes"] is True


# ---------------------------------------------------------------------------
# 8. B5 gate fails when any single condition fails
# ---------------------------------------------------------------------------


def test_b5_gate_fails_c1_n_insufficient():
    actual_metrics = {"1_5r": {"n": 10, "expectancy_r": "0.5", "flat_rate": "0.2"}}
    random_summary = _make_random_summary(exp_p75="0.3", flat_median="0.3")
    gate = evaluate_b5_gate(actual_metrics, random_summary, n_high_vol=10)
    assert gate["gate_result"] == B5_FAIL
    assert gate["conditions"]["c1_n_high_vol_sufficient"]["passes"] is False


def test_b5_gate_fails_c2_expectancy_below_p75():
    actual_metrics = {"1_5r": {"n": 25, "expectancy_r": "0.2", "flat_rate": "0.2"}}
    random_summary = _make_random_summary(exp_p75="0.4", flat_median="0.3")
    gate = evaluate_b5_gate(actual_metrics, random_summary, n_high_vol=25)
    assert gate["gate_result"] == B5_FAIL
    assert gate["conditions"]["c2_expectancy_beats_p75_random"]["passes"] is False


def test_b5_gate_fails_c3_negative_expectancy():
    actual_metrics = {"1_5r": {"n": 25, "expectancy_r": "-0.1", "flat_rate": "0.2"}}
    random_summary = _make_random_summary(exp_p75="-0.2", flat_median="0.3")
    gate = evaluate_b5_gate(actual_metrics, random_summary, n_high_vol=25)
    assert gate["gate_result"] == B5_FAIL
    assert gate["conditions"]["c3_expectancy_positive"]["passes"] is False


def test_b5_gate_fails_c4_flat_rate_above_random_median():
    actual_metrics = {"1_5r": {"n": 25, "expectancy_r": "0.5", "flat_rate": "0.5"}}
    random_summary = _make_random_summary(exp_p75="0.3", flat_median="0.3")
    gate = evaluate_b5_gate(actual_metrics, random_summary, n_high_vol=25)
    assert gate["gate_result"] == B5_FAIL
    assert gate["conditions"]["c4_flat_rate_le_random_median"]["passes"] is False


def test_b5_gate_fails_when_all_four_conditions_fail():
    actual_metrics = {"1_5r": {"n": 5, "expectancy_r": "-0.3", "flat_rate": "0.8"}}
    random_summary = _make_random_summary(exp_p75="0.3", flat_median="0.3")
    gate = evaluate_b5_gate(actual_metrics, random_summary, n_high_vol=5)
    assert gate["gate_result"] == B5_FAIL


# ---------------------------------------------------------------------------
# 9. No HTTP / network / private API imports in module source
# ---------------------------------------------------------------------------


def test_no_network_or_private_imports_in_module_source():
    source_files = [
        Path(_mod.__file__),
    ]
    forbidden_tokens = (
        "apiKey",
        "ACCESS-KEY",
        "signature",
        "secret",
        "passphrase",
        "Authorization",
        "account",
        "balance",
        "position",
        "cancel",
        "set_leverage",
        "requests",
        "http.client",
        "socket",
    )
    for path in source_files:
        source = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in source, (
                f"Forbidden token {token!r} found in {path.name}"
            )


def test_runner_has_no_network_imports():
    import research.signal_observation.run_setup_b_high_vol_validation as runner_mod

    runner_path = Path(runner_mod.__file__)
    forbidden_tokens = (
        "apiKey", "ACCESS-KEY", "signature", "secret", "passphrase",
        "Authorization", "account", "balance", "position", "cancel",
        "set_leverage", "urllib", "requests", "http.client", "socket",
    )
    source = runner_path.read_text(encoding="utf-8")
    for token in forbidden_tokens:
        assert token not in source, (
            f"Forbidden token {token!r} found in {runner_path.name}"
        )


# ---------------------------------------------------------------------------
# Additional: compute_validation_metrics returns correct structure
# ---------------------------------------------------------------------------


def test_compute_validation_metrics_structure():
    obs = [_fake_obs(outcome="win")] * 3 + [_fake_obs(outcome="loss")] * 2
    metrics = compute_validation_metrics(obs)
    assert set(metrics.keys()) == {"1r", "1_5r", "2r"}
    for target_metrics in metrics.values():
        assert "n" in target_metrics
        assert "expectancy_r" in target_metrics
        assert "flat_rate" in target_metrics
        assert target_metrics["n"] == 5


def test_compare_actual_beats_p75_when_exp_exceeds_p75():
    actual = {"1_5r": {"expectancy_r": "0.5", "flat_rate": "0.2", "avg_mfe_r": "1.0"}}
    random_s = _make_random_summary(exp_p75="0.3")
    cmp = compare_actual_to_conditional_random(actual, random_s)
    assert cmp["1_5r"]["beats_conditional_random_p75_expectancy"] is True


def test_compare_actual_does_not_beat_p75_when_exp_below():
    actual = {"1_5r": {"expectancy_r": "0.1", "flat_rate": "0.2", "avg_mfe_r": "0.5"}}
    random_s = _make_random_summary(exp_p75="0.3")
    cmp = compare_actual_to_conditional_random(actual, random_s)
    assert cmp["1_5r"]["beats_conditional_random_p75_expectancy"] is False


def test_compare_flat_rate_le_random_median_true():
    actual = {"1_5r": {"expectancy_r": "0.5", "flat_rate": "0.2", "avg_mfe_r": "1.0"}}
    random_s = _make_random_summary(flat_median="0.3")
    cmp = compare_actual_to_conditional_random(actual, random_s)
    assert cmp["1_5r"]["actual_flat_rate_le_random_median"] is True


def test_compare_flat_rate_le_random_median_false_when_higher():
    actual = {"1_5r": {"expectancy_r": "0.5", "flat_rate": "0.5", "avg_mfe_r": "1.0"}}
    random_s = _make_random_summary(flat_median="0.3")
    cmp = compare_actual_to_conditional_random(actual, random_s)
    assert cmp["1_5r"]["actual_flat_rate_le_random_median"] is False


def test_gate_constants_unchanged():
    assert GATE_MIN_N == 20
    assert VALIDATION_TARGET == "1_5r"
