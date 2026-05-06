from __future__ import annotations

import json
import random
import shutil
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from research.signal_observation.candles import Candle
from research.signal_observation.setup_b_conditional_random_baseline import (
    CANDIDATE_CONDITIONS,
    CONDITION_INTERSECTION,
    CONDITION_TREND_BELOW_FALLING,
    CONDITION_VOL_HIGH,
    MEANINGFUL_MARGIN_THRESHOLD,
    build_eligible_indices,
    build_conditional_bucket_specs,
    format_conditional_baseline_report,
    run_all_conditional_baselines,
    write_conditional_baseline_artifacts,
    _compare_actual_to_conditional_random,
    _sample_conditional_iteration,
    _vol_high_eligible,
    _trend_below_falling_eligible,
    _compute_sma,
)
from research.signal_observation.indicators import atr as compute_atr
from research.signal_observation.setup_b_conditional_diagnostics import (
    ATR_PERIOD,
    SMA_PERIOD,
)
from research.signal_observation.setup_b_random_baseline import BucketSpec


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_candle(
    index: int,
    close: Decimal,
    high: Decimal | None = None,
    low: Decimal | None = None,
) -> Candle:
    ts = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(hours=4 * index)
    c_high = high if high is not None else close + Decimal("1")
    c_low = low if low is not None else close - Decimal("1")
    return Candle(
        timestamp=ts,
        open=close,
        high=c_high,
        low=c_low,
        close=close,
        volume=Decimal("100"),
    )


def _make_falling_candles(count: int = 200, start: Decimal = Decimal("200")) -> list[Candle]:
    """Monotonically falling closes: start, start-1, start-2, ..."""
    return [_make_candle(i, start - Decimal(i)) for i in range(count)]


def _make_rising_candles(count: int = 200, start: Decimal = Decimal("100")) -> list[Candle]:
    return [_make_candle(i, start + Decimal(i)) for i in range(count)]


def _make_high_volatility_candles(count: int = 200) -> list[Candle]:
    """First half: tiny spread (spread=1). Second half: huge spread (spread=200)."""
    candles = []
    for i in range(count):
        if i < count // 2:
            spread = Decimal("1")
        else:
            spread = Decimal("200")
        close = Decimal("100")
        candles.append(_make_candle(i, close, high=close + spread, low=close - spread))
    return candles


def _minimal_obs(
    symbol: str = "SYM",
    direction: str = "long",
    candle_index: int = 60,
    outcome_1r: str = "win",
    entry_price: str = "100",
    stop: str = "95",
    tag_vol: str = "high",
    tag_trend: str = "below_sma_falling",
) -> dict[str, object]:
    ts = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(hours=4 * candle_index)
    return {
        "symbol": symbol,
        "signal_direction": direction,
        "signal_time": ts.isoformat(),
        "entry_time": ts.isoformat(),
        "entry_price": entry_price,
        "stop": stop,
        "atr_at_entry": "10",
        "session_label": "Europe",
        "signal_hour_utc": 10,
        "outcome_1r": outcome_1r,
        "outcome_1_5r": outcome_1r,
        "outcome_2r": outcome_1r,
        "mae_1r": "-0.3",
        "mfe_1r": "1.2",
        "mae_1_5r": "-0.3",
        "mfe_1_5r": "1.5",
        "mae_2r": "-0.3",
        "mfe_2r": "2.1",
        "bars_to_resolution_1r": 3,
        "bars_to_resolution_1_5r": 5,
        "bars_to_resolution_2r": 7,
        "tag_volatility_regime": tag_vol,
        "tag_slow_trend_state": tag_trend,
        "tag_session": "Europe",
        "tag_htf_alignment": "not_available",
        "tag_mfe_shape": "mfe_ge_1_0r",
        "tag_flat_decomp": outcome_1r,
    }


# ---------------------------------------------------------------------------
# 1. Eligible indices: volatility_regime=high
# ---------------------------------------------------------------------------


def test_vol_high_eligible_indices_all_have_atr_ge_p67() -> None:
    candles = _make_high_volatility_candles(200)
    candles_by_symbol = {"SYM": candles}
    timeout_bars = 10

    eligible = _vol_high_eligible(candles_by_symbol, timeout_bars)["SYM"]

    assert len(eligible) > 0, "expected some eligible indices"

    atr_series = compute_atr(candles, ATR_PERIOD)
    valid_atrs = sorted(v for v in atr_series if v is not None)
    # p67 threshold
    n = len(valid_atrs)
    rank = Decimal("0.667") * Decimal(n - 1)
    lower = int(rank.to_integral_value(rounding="ROUND_FLOOR"))
    upper = int(rank.to_integral_value(rounding="ROUND_CEILING"))
    frac = rank - Decimal(lower)
    p67 = valid_atrs[lower] + (valid_atrs[upper] - valid_atrs[lower]) * frac if lower != upper else valid_atrs[lower]

    for idx in eligible:
        assert atr_series[idx] is not None
        assert atr_series[idx] >= p67, f"index {idx} ATR={atr_series[idx]} below p67={p67}"


# ---------------------------------------------------------------------------
# 2. Eligible indices: slow_trend_state=below_sma_falling
# ---------------------------------------------------------------------------


def test_trend_below_falling_eligible_indices_satisfy_condition() -> None:
    candles = _make_falling_candles(200)
    candles_by_symbol = {"SYM": candles}
    timeout_bars = 10

    eligible = _trend_below_falling_eligible(candles_by_symbol, timeout_bars)["SYM"]

    assert len(eligible) > 0, "expected some eligible indices for falling candles"

    sma = _compute_sma(candles, SMA_PERIOD)
    for idx in eligible:
        sma_now = sma[idx]
        sma_prev = sma[idx - 1] if idx > 0 else None
        assert sma_now is not None
        assert sma_prev is not None
        assert candles[idx].close < sma_now, f"index {idx}: close not below SMA"
        assert sma_now < sma_prev, f"index {idx}: SMA not falling"


# ---------------------------------------------------------------------------
# 3. Intersection is subset of both component conditions
# ---------------------------------------------------------------------------


def test_intersection_eligible_is_subset_of_both_conditions() -> None:
    candles = _make_falling_candles(200)
    candles_by_symbol = {"SYM": candles}
    timeout_bars = 10

    vol_eligible = build_eligible_indices(candles_by_symbol, CONDITION_VOL_HIGH, timeout_bars)
    trend_eligible = build_eligible_indices(candles_by_symbol, CONDITION_TREND_BELOW_FALLING, timeout_bars)
    intersect = build_eligible_indices(candles_by_symbol, CONDITION_INTERSECTION, timeout_bars)

    vol_set = set(vol_eligible["SYM"])
    trend_set = set(trend_eligible["SYM"])
    intersect_set = set(intersect["SYM"])

    assert intersect_set <= vol_set, "intersection not subset of vol_high"
    assert intersect_set <= trend_set, "intersection not subset of trend_below_falling"


# ---------------------------------------------------------------------------
# 4. Eligible indices respect lookahead cutoff
# ---------------------------------------------------------------------------


def test_eligible_indices_respect_lookahead_cutoff() -> None:
    candles = _make_high_volatility_candles(200)
    candles_by_symbol = {"SYM": candles}
    timeout_bars = 10

    eligible_vol = _vol_high_eligible(candles_by_symbol, timeout_bars)["SYM"]
    eligible_trend = _trend_below_falling_eligible(
        {"SYM": _make_falling_candles(200)}, timeout_bars
    )["SYM"]

    max_allowed = len(candles) - timeout_bars - 1
    for idx in eligible_vol:
        assert idx <= max_allowed, f"vol index {idx} exceeds max {max_allowed}"
    for idx in eligible_trend:
        assert idx <= max_allowed, f"trend index {idx} exceeds max {max_allowed}"


# ---------------------------------------------------------------------------
# 5. Conditional sampling uses only eligible candles
# ---------------------------------------------------------------------------


def test_conditional_sampling_uses_only_eligible_candles() -> None:
    # 30 candles with distinct close prices so we can identify which was sampled
    candles = [_make_candle(i, Decimal(100 + i)) for i in range(30)]
    # Restrict eligible to exactly indices 5, 10, 15 (each has 10+ future candles)
    eligible_indices = {"SYM": [5, 10, 15]}
    eligible_prices = {
        candles[5].close,
        candles[10].close,
        candles[15].close,
    }
    specs = [
        BucketSpec(
            symbol="SYM",
            direction="long",
            count=20,
            risk_distances=(Decimal("2"),),
        )
    ]
    rng = random.Random(42)

    entries = _sample_conditional_iteration(
        bucket_specs=specs,
        eligible_indices=eligible_indices,
        candles_by_symbol={"SYM": candles},
        rng=rng,
        timeout_bars=10,
    )

    assert len(entries) == 20
    for entry in entries:
        assert Decimal(str(entry["entry_price"])) in eligible_prices, (
            f"entry_price {entry['entry_price']} not from eligible candles"
        )


# ---------------------------------------------------------------------------
# 6. Comparison fields beats_* are computed correctly
# ---------------------------------------------------------------------------


def test_comparison_beats_fields_are_correct() -> None:
    actual_metrics = {
        "1r": {
            "n": 25,
            "wins": 6,
            "losses": 3,
            "flats": 16,
            "win_rate": Decimal("0.24"),
            "flat_rate": Decimal("0.64"),
            "expectancy_r": Decimal("0.12"),
            "avg_mfe_r": Decimal("0.67"),
            "avg_mae_r": Decimal("-0.55"),
            "median_mfe_r": Decimal("0.5"),
            "median_mae_r": Decimal("-0.5"),
        },
        "1_5r": {
            "n": 25,
            "wins": 3,
            "losses": 6,
            "flats": 16,
            "win_rate": Decimal("0.12"),
            "flat_rate": Decimal("0.64"),
            "expectancy_r": Decimal("-0.18"),
            "avg_mfe_r": Decimal("0.55"),
            "avg_mae_r": Decimal("-0.60"),
            "median_mfe_r": Decimal("0.4"),
            "median_mae_r": Decimal("-0.5"),
        },
        "2r": {
            "n": 25,
            "wins": 3,
            "losses": 6,
            "flats": 16,
            "win_rate": Decimal("0.12"),
            "flat_rate": Decimal("0.64"),
            "expectancy_r": Decimal("-0.18"),
            "avg_mfe_r": Decimal("0.55"),
            "avg_mae_r": Decimal("-0.60"),
            "median_mfe_r": Decimal("0.4"),
            "median_mae_r": Decimal("-0.5"),
        },
    }
    random_summary = {
        "1r": {
            "expectancy_r": {
                "mean": Decimal("0.01"),
                "median": Decimal("0.00"),
                "p10": Decimal("-0.06"),
                "p25": Decimal("-0.02"),
                "p75": Decimal("0.06"),
                "p90": Decimal("0.12"),
                "min": Decimal("-0.12"),
                "max": Decimal("0.18"),
            },
            "avg_mfe_r": {
                "mean": Decimal("0.65"),
                "median": Decimal("0.65"),
                "p10": Decimal("0.60"),
                "p25": Decimal("0.62"),
                "p75": Decimal("0.68"),
                "p90": Decimal("0.72"),
                "min": Decimal("0.55"),
                "max": Decimal("0.80"),
            },
            "win_rate": {
                "mean": Decimal("0.20"),
                "median": Decimal("0.20"),
                "p10": Decimal("0.15"),
                "p25": Decimal("0.18"),
                "p75": Decimal("0.23"),
                "p90": Decimal("0.25"),
                "min": Decimal("0.10"),
                "max": Decimal("0.30"),
            },
            "avg_mae_r": {
                "mean": Decimal("-0.50"),
                "median": Decimal("-0.50"),
                "p10": Decimal("-0.60"),
                "p25": Decimal("-0.55"),
                "p75": Decimal("-0.45"),
                "p90": Decimal("-0.40"),
                "min": Decimal("-0.70"),
                "max": Decimal("-0.30"),
            },
        },
        "1_5r": {
            "expectancy_r": {
                "mean": Decimal("0.01"), "median": Decimal("0.00"), "p10": Decimal("-0.06"),
                "p25": Decimal("-0.02"), "p75": Decimal("0.06"), "p90": Decimal("0.12"),
                "min": Decimal("-0.12"), "max": Decimal("0.18"),
            },
            "avg_mfe_r": {
                "mean": Decimal("0.65"), "median": Decimal("0.65"), "p10": Decimal("0.60"),
                "p25": Decimal("0.62"), "p75": Decimal("0.68"), "p90": Decimal("0.72"),
                "min": Decimal("0.55"), "max": Decimal("0.80"),
            },
            "win_rate": {
                "mean": Decimal("0.20"), "median": Decimal("0.20"), "p10": Decimal("0.15"),
                "p25": Decimal("0.18"), "p75": Decimal("0.23"), "p90": Decimal("0.25"),
                "min": Decimal("0.10"), "max": Decimal("0.30"),
            },
            "avg_mae_r": {
                "mean": Decimal("-0.50"), "median": Decimal("-0.50"), "p10": Decimal("-0.60"),
                "p25": Decimal("-0.55"), "p75": Decimal("-0.45"), "p90": Decimal("-0.40"),
                "min": Decimal("-0.70"), "max": Decimal("-0.30"),
            },
        },
        "2r": {
            "expectancy_r": {
                "mean": Decimal("0.01"), "median": Decimal("0.00"), "p10": Decimal("-0.06"),
                "p25": Decimal("-0.02"), "p75": Decimal("0.06"), "p90": Decimal("0.12"),
                "min": Decimal("-0.12"), "max": Decimal("0.18"),
            },
            "avg_mfe_r": {
                "mean": Decimal("0.65"), "median": Decimal("0.65"), "p10": Decimal("0.60"),
                "p25": Decimal("0.62"), "p75": Decimal("0.68"), "p90": Decimal("0.72"),
                "min": Decimal("0.55"), "max": Decimal("0.80"),
            },
            "win_rate": {
                "mean": Decimal("0.20"), "median": Decimal("0.20"), "p10": Decimal("0.15"),
                "p25": Decimal("0.18"), "p75": Decimal("0.23"), "p90": Decimal("0.25"),
                "min": Decimal("0.10"), "max": Decimal("0.30"),
            },
            "avg_mae_r": {
                "mean": Decimal("-0.50"), "median": Decimal("-0.50"), "p10": Decimal("-0.60"),
                "p25": Decimal("-0.55"), "p75": Decimal("-0.45"), "p90": Decimal("-0.40"),
                "min": Decimal("-0.70"), "max": Decimal("-0.30"),
            },
        },
    }

    comparison = _compare_actual_to_conditional_random(actual_metrics, random_summary)
    c1r = comparison["1r"]

    # actual_exp=0.12, median=0.00, p75=0.06, p90=0.12
    assert c1r["beats_conditional_random_median_expectancy"] is True   # 0.12 > 0.00
    assert c1r["beats_conditional_random_p75_expectancy"] is True      # 0.12 > 0.06
    assert c1r["beats_conditional_random_p90_expectancy"] is False     # 0.12 == 0.12, not >
    assert c1r["beats_conditional_random_median_mfe"] is True          # 0.67 > 0.65


# ---------------------------------------------------------------------------
# 7. Meaningful margin >= threshold → "potentially_meaningful"
# ---------------------------------------------------------------------------


def test_meaningful_margin_potentially_meaningful_when_ge_threshold() -> None:
    actual_metrics = {
        target: {
            "n": 10,
            "wins": 3,
            "losses": 2,
            "flats": 5,
            "win_rate": Decimal("0.3"),
            "flat_rate": Decimal("0.5"),
            "expectancy_r": Decimal("0.11"),
            "avg_mfe_r": Decimal("0.65"),
            "avg_mae_r": Decimal("-0.50"),
            "median_mfe_r": Decimal("0.60"),
            "median_mae_r": Decimal("-0.45"),
        }
        for target in ("1r", "1_5r", "2r")
    }
    # p75 = 0.06 → margin = 0.11 - 0.06 = 0.05 >= MEANINGFUL_MARGIN_THRESHOLD
    dummy_dist = {
        "mean": Decimal("0.01"), "median": Decimal("0.00"), "p10": Decimal("-0.06"),
        "p25": Decimal("-0.02"), "p75": Decimal("0.06"), "p90": Decimal("0.12"),
        "min": Decimal("-0.12"), "max": Decimal("0.18"),
    }
    dummy_mfe_dist = {
        "mean": Decimal("0.64"), "median": Decimal("0.63"), "p10": Decimal("0.58"),
        "p25": Decimal("0.60"), "p75": Decimal("0.67"), "p90": Decimal("0.70"),
        "min": Decimal("0.50"), "max": Decimal("0.80"),
    }
    random_summary = {
        target: {"expectancy_r": dummy_dist, "avg_mfe_r": dummy_mfe_dist,
                 "win_rate": dummy_dist, "avg_mae_r": dummy_dist}
        for target in ("1r", "1_5r", "2r")
    }

    comparison = _compare_actual_to_conditional_random(actual_metrics, random_summary)

    assert comparison["1r"]["meaningful_margin_classification"] == "potentially_meaningful"
    # margin = 0.11 - 0.06 = 0.05 exactly
    assert Decimal(comparison["1r"]["meaningful_margin_over_p75"]) >= MEANINGFUL_MARGIN_THRESHOLD  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 8. Meaningful margin < threshold → "weak"
# ---------------------------------------------------------------------------


def test_meaningful_margin_weak_when_below_threshold() -> None:
    actual_metrics = {
        target: {
            "n": 10,
            "wins": 2,
            "losses": 3,
            "flats": 5,
            "win_rate": Decimal("0.2"),
            "flat_rate": Decimal("0.5"),
            "expectancy_r": Decimal("0.04"),  # just below p75=0.06
            "avg_mfe_r": Decimal("0.60"),
            "avg_mae_r": Decimal("-0.55"),
            "median_mfe_r": Decimal("0.55"),
            "median_mae_r": Decimal("-0.50"),
        }
        for target in ("1r", "1_5r", "2r")
    }
    dummy_dist = {
        "mean": Decimal("0.01"), "median": Decimal("0.00"), "p10": Decimal("-0.06"),
        "p25": Decimal("-0.02"), "p75": Decimal("0.06"), "p90": Decimal("0.12"),
        "min": Decimal("-0.12"), "max": Decimal("0.18"),
    }
    dummy_mfe_dist = {
        "mean": Decimal("0.64"), "median": Decimal("0.63"), "p10": Decimal("0.58"),
        "p25": Decimal("0.60"), "p75": Decimal("0.67"), "p90": Decimal("0.70"),
        "min": Decimal("0.50"), "max": Decimal("0.80"),
    }
    random_summary = {
        target: {"expectancy_r": dummy_dist, "avg_mfe_r": dummy_mfe_dist,
                 "win_rate": dummy_dist, "avg_mae_r": dummy_dist}
        for target in ("1r", "1_5r", "2r")
    }

    comparison = _compare_actual_to_conditional_random(actual_metrics, random_summary)

    assert comparison["1r"]["meaningful_margin_classification"] == "weak"
    # margin = 0.04 - 0.06 = -0.02 < MEANINGFUL_MARGIN_THRESHOLD
    assert Decimal(comparison["1r"]["meaningful_margin_over_p75"]) < MEANINGFUL_MARGIN_THRESHOLD  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 9. Empty condition handled gracefully
# ---------------------------------------------------------------------------


def test_empty_intersection_condition_returns_gracefully() -> None:
    # Observations that are all vol=low and trend=above_sma_rising → no intersection members
    tagged_obs = [
        _minimal_obs(tag_vol="low", tag_trend="above_sma_rising")
        for _ in range(5)
    ]
    candles = _make_falling_candles(200)
    candles_by_symbol = {"SYM": candles}

    specs = build_conditional_bucket_specs(tagged_obs, CONDITION_INTERSECTION)
    assert len(specs) == 0

    # _run_one_condition via run_all_conditional_baselines uses tag_observations internally,
    # so we test build_conditional_bucket_specs directly here
    specs_vol = build_conditional_bucket_specs(tagged_obs, CONDITION_VOL_HIGH)
    assert len(specs_vol) == 0


# ---------------------------------------------------------------------------
# 10. Artifact writers produce stable output
# ---------------------------------------------------------------------------


def test_artifact_writers_produce_stable_output() -> None:
    # Build a minimal report dict that matches the expected schema
    dummy_dist_str = {
        "mean": "0.01",
        "median": "0.00",
        "p10": "-0.06",
        "p25": "-0.02",
        "p75": "0.06",
        "p90": "0.12",
        "min": "-0.12",
        "max": "0.18",
    }
    dummy_actual = {
        target: {
            "n": 5,
            "wins": 2,
            "losses": 1,
            "flats": 2,
            "win_rate": "0.4",
            "flat_rate": "0.4",
            "expectancy_r": "0.2",
            "avg_mfe_r": "0.7",
            "avg_mae_r": "-0.4",
            "median_mfe_r": "0.6",
            "median_mae_r": "-0.3",
        }
        for target in ("1r", "1_5r", "2r")
    }
    dummy_random = {
        target: {
            "expectancy_r": dummy_dist_str,
            "avg_mfe_r": dummy_dist_str,
            "win_rate": dummy_dist_str,
            "avg_mae_r": dummy_dist_str,
        }
        for target in ("1r", "1_5r", "2r")
    }
    dummy_comparison = {
        target: {
            "beats_conditional_random_median_expectancy": True,
            "beats_conditional_random_p75_expectancy": True,
            "beats_conditional_random_p90_expectancy": False,
            "beats_conditional_random_median_mfe": True,
            "meaningful_margin_over_p75": "0.14",
            "meaningful_margin_classification": "potentially_meaningful",
        }
        for target in ("1r", "1_5r", "2r")
    }
    dummy_cond = {
        "observation_count": 5,
        "bucket_distribution": {"SYM / long": 5},
        "eligible_candle_counts": {"SYM": 100},
        "setup_b_actual": dummy_actual,
        "conditional_random_baseline": dummy_random,
        "comparison": dummy_comparison,
    }
    report: dict[str, object] = {
        "schema": "setup_b_conditional_random_baseline_v1",
        "seed": 5403,
        "iterations": 1000,
        "timeout_bars_4h": 10,
        "conditions": {cond: dummy_cond for cond in CANDIDATE_CONDITIONS},
    }

    output_dir = Path(".pytest-temp-run") / "setup_b_conditional_random_baseline_test"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    text_path = output_dir / "report.txt"
    json_path = output_dir / "report.json"

    write_conditional_baseline_artifacts(report, text_path=text_path, json_path=json_path)

    assert text_path.read_text(encoding="utf-8") == format_conditional_baseline_report(report)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "setup_b_conditional_random_baseline_v1"
    assert "conditions" in payload
    for cond_name in CANDIDATE_CONDITIONS:
        assert cond_name in payload["conditions"]

    shutil.rmtree(output_dir)


# ---------------------------------------------------------------------------
# 11. No network imports
# ---------------------------------------------------------------------------


def test_conditional_baseline_modules_do_not_import_network_libraries() -> None:
    repo_root = Path(__file__).parent.parent.parent
    module_paths = [
        repo_root / "research" / "signal_observation" / "setup_b_conditional_random_baseline.py",
        repo_root / "research" / "signal_observation" / "run_setup_b_conditional_random_baseline.py",
    ]
    forbidden_tokens = (
        "urllib",
        "requests",
        "http.client",
        "socket",
        "execution_service",
        "risk_engine",
        "orchestrator",
        "position_manager",
        "kill_switch",
    )
    for path in module_paths:
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"{path.name} imports forbidden token: {token!r}"
