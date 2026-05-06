from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from research.signal_observation.candles import Candle
from research.signal_observation.setup_b_conditional_diagnostics import (
    SAMPLE_SIZE_FLAG_THRESHOLD,
    TAG_KEYS,
    TARGETS,
    build_conditional_report,
    compute_conditional_metrics,
    format_conditional_report,
    tag_observations,
    write_conditional_artifacts,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_candle(index: int, close: Decimal, high: Decimal | None = None, low: Decimal | None = None) -> Candle:
    ts = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(hours=4 * index)
    c_high = high if high is not None else close + Decimal("5")
    c_low = low if low is not None else close - Decimal("5")
    c_open = close
    return Candle(
        timestamp=ts,
        open=c_open,
        high=c_high,
        low=c_low,
        close=close,
        volume=Decimal("100"),
    )


def _make_candles(count: int = 100, base_close: Decimal = Decimal("100")) -> list[Candle]:
    candles = []
    for i in range(count):
        close = base_close + Decimal(i)
        candles.append(_make_candle(i, close))
    return candles


def _make_observation(
    symbol: str = "BTCUSDT",
    direction: str = "long",
    outcome_1r: str = "win",
    outcome_1_5r: str = "win",
    outcome_2r: str = "win",
    session_label: str = "Europe",
    signal_hour_utc: int = 10,
    atr_at_entry: str = "500",
    mfe_1r: str = "1.2",
    mae_1r: str = "-0.3",
    mfe_1_5r: str = "1.5",
    mae_1_5r: str = "-0.3",
    mfe_2r: str = "2.1",
    mae_2r: str = "-0.3",
    entry_price: str = "100",
    candle_index: int = 60,
) -> dict[str, object]:
    ts = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(hours=4 * candle_index)
    return {
        "symbol": symbol,
        "signal_direction": direction,
        "signal_time": ts.isoformat(),
        "entry_time": ts.isoformat(),
        "entry_price": entry_price,
        "stop": "95",
        "atr_at_entry": atr_at_entry,
        "session_label": session_label,
        "signal_hour_utc": signal_hour_utc,
        "outcome_1r": outcome_1r,
        "outcome_1_5r": outcome_1_5r,
        "outcome_2r": outcome_2r,
        "mae_1r": mae_1r,
        "mfe_1r": mfe_1r,
        "mae_1_5r": mae_1_5r,
        "mfe_1_5r": mfe_1_5r,
        "mae_2r": mae_2r,
        "mfe_2r": mfe_2r,
        "bars_to_resolution_1r": 3,
        "bars_to_resolution_1_5r": 5,
        "bars_to_resolution_2r": 7,
    }


def _minimal_candles_by_symbol(count: int = 100) -> dict[str, list[Candle]]:
    return {"BTCUSDT": _make_candles(count)}


# ---------------------------------------------------------------------------
# 1. Session tag
# ---------------------------------------------------------------------------


def test_session_tag_uses_existing_session_label() -> None:
    obs = [_make_observation(session_label="Asia"), _make_observation(session_label="overlap")]
    candles_by_symbol = _minimal_candles_by_symbol()

    tagged = tag_observations(obs, candles_by_symbol)

    assert tagged[0]["tag_session"] == "Asia"
    assert tagged[1]["tag_session"] == "overlap"


# ---------------------------------------------------------------------------
# 2. Volatility regime tag
# ---------------------------------------------------------------------------


def test_volatility_regime_low_mid_high_classification() -> None:
    # Build candles with varying ATR so we can test classification
    candles = _make_candles(200)
    obs_low = _make_observation(atr_at_entry="1", candle_index=60)   # very low ATR
    obs_high = _make_observation(atr_at_entry="9999", candle_index=60)  # very high ATR
    candles_by_symbol = {"BTCUSDT": candles}

    tagged = tag_observations([obs_low, obs_high], candles_by_symbol)

    assert tagged[0]["tag_volatility_regime"] == "low"
    assert tagged[1]["tag_volatility_regime"] == "high"


def test_volatility_regime_unknown_symbol_returns_unavailable() -> None:
    obs = [_make_observation(symbol="XYZUSDT", atr_at_entry="500", candle_index=60)]
    candles_by_symbol = _minimal_candles_by_symbol()

    tagged = tag_observations(obs, candles_by_symbol)

    assert tagged[0]["tag_volatility_regime"] == "atr_unavailable"


# ---------------------------------------------------------------------------
# 3. Slow trend state tag
# ---------------------------------------------------------------------------


def test_slow_trend_state_above_sma_rising() -> None:
    # Rising close prices → SMA is rising; entry price above SMA
    candles = [_make_candle(i, Decimal(100 + i)) for i in range(100)]
    obs = [_make_observation(entry_price="200", candle_index=99)]
    candles_by_symbol = {"BTCUSDT": candles}

    tagged = tag_observations(obs, candles_by_symbol)

    state = tagged[0]["tag_slow_trend_state"]
    assert state.startswith("above_sma")


def test_slow_trend_state_unavailable_when_candle_not_found() -> None:
    obs = [_make_observation(symbol="BTCUSDT", candle_index=9999)]  # index beyond candle range
    candles_by_symbol = _minimal_candles_by_symbol(100)

    tagged = tag_observations(obs, candles_by_symbol)

    assert tagged[0]["tag_slow_trend_state"] == "sma_unavailable"


def test_slow_trend_state_unavailable_before_sma_period() -> None:
    # candle_index=5 → index < SMA_PERIOD(50), so SMA is None
    obs = [_make_observation(candle_index=5)]
    candles_by_symbol = _minimal_candles_by_symbol(100)

    tagged = tag_observations(obs, candles_by_symbol)

    assert tagged[0]["tag_slow_trend_state"] == "sma_unavailable"


# ---------------------------------------------------------------------------
# 4. MFE shape tag
# ---------------------------------------------------------------------------


def test_mfe_shape_tag_buckets_are_exhaustive() -> None:
    cases = [
        ("1.5", "mfe_ge_1_0r"),
        ("1.0", "mfe_ge_1_0r"),
        ("0.7", "mfe_0_5_to_1_0r"),
        ("0.5", "mfe_0_5_to_1_0r"),
        ("0.4", "mfe_0_3_to_0_5r"),
        ("0.3", "mfe_0_3_to_0_5r"),
        ("0.1", "mfe_lt_0_3r"),
    ]
    obs = [_make_observation(mfe_1r=mfe) for mfe, _ in cases]
    candles_by_symbol = _minimal_candles_by_symbol()

    tagged = tag_observations(obs, candles_by_symbol)

    for i, (_, expected) in enumerate(cases):
        assert tagged[i]["tag_mfe_shape"] == expected, f"case {i}: mfe_1r={cases[i][0]}"


# ---------------------------------------------------------------------------
# 5. Flat decomp tag
# ---------------------------------------------------------------------------


def test_flat_decomp_win_and_loss_pass_through() -> None:
    obs = [
        _make_observation(outcome_1r="win", mfe_1r="1.2", mae_1r="-0.1"),
        _make_observation(outcome_1r="loss", mfe_1r="0.2", mae_1r="-1.0"),
    ]
    candles_by_symbol = _minimal_candles_by_symbol()

    tagged = tag_observations(obs, candles_by_symbol)

    assert tagged[0]["tag_flat_decomp"] == "win"
    assert tagged[1]["tag_flat_decomp"] == "loss"


def test_flat_decomp_categories_are_mutually_exclusive() -> None:
    obs = [
        _make_observation(outcome_1r="flat", mfe_1r="0.9", mae_1r="-0.2"),   # near_win_flat
        _make_observation(outcome_1r="flat", mfe_1r="0.4", mae_1r="-0.8"),   # adverse_flat
        _make_observation(outcome_1r="flat", mfe_1r="0.1", mae_1r="-0.1"),   # dead_flat
        _make_observation(outcome_1r="flat", mfe_1r="0.5", mae_1r="-0.4"),   # ordinary_flat
    ]
    candles_by_symbol = _minimal_candles_by_symbol()

    tagged = tag_observations(obs, candles_by_symbol)

    assert tagged[0]["tag_flat_decomp"] == "near_win_flat"
    assert tagged[1]["tag_flat_decomp"] == "adverse_flat"
    assert tagged[2]["tag_flat_decomp"] == "dead_flat"
    assert tagged[3]["tag_flat_decomp"] == "ordinary_flat"


# ---------------------------------------------------------------------------
# 6. Bucket metrics computation
# ---------------------------------------------------------------------------


def test_bucket_metrics_win_loss_flat_counts_are_correct() -> None:
    obs = [
        _make_observation(outcome_1r="win"),
        _make_observation(outcome_1r="win"),
        _make_observation(outcome_1r="loss"),
        _make_observation(outcome_1r="flat"),
    ]
    candles_by_symbol = _minimal_candles_by_symbol()

    tagged = tag_observations(obs, candles_by_symbol)
    metrics = compute_conditional_metrics(tagged)

    # Find a bucket with all 4 observations (htf_alignment is always "not_available")
    htf_bucket = metrics["htf_alignment"]["not_available"]["1r"]  # type: ignore[index]
    assert htf_bucket["n"] == 4
    assert htf_bucket["wins"] == 2
    assert htf_bucket["losses"] == 1
    assert htf_bucket["flats"] == 1


def test_bucket_metrics_sample_size_flag_set_below_threshold() -> None:
    obs = [_make_observation() for _ in range(SAMPLE_SIZE_FLAG_THRESHOLD - 1)]
    candles_by_symbol = _minimal_candles_by_symbol()

    tagged = tag_observations(obs, candles_by_symbol)
    metrics = compute_conditional_metrics(tagged)

    htf_bucket = metrics["htf_alignment"]["not_available"]["1r"]  # type: ignore[index]
    assert htf_bucket["sample_size_flag"] is True


def test_bucket_metrics_sample_size_flag_clear_at_threshold() -> None:
    obs = [_make_observation() for _ in range(SAMPLE_SIZE_FLAG_THRESHOLD)]
    candles_by_symbol = _minimal_candles_by_symbol()

    tagged = tag_observations(obs, candles_by_symbol)
    metrics = compute_conditional_metrics(tagged)

    htf_bucket = metrics["htf_alignment"]["not_available"]["1r"]  # type: ignore[index]
    assert htf_bucket["sample_size_flag"] is False


# ---------------------------------------------------------------------------
# 7. P(reach_1R | reach_0.5R) computation
# ---------------------------------------------------------------------------


def test_p_reach_1r_given_0_5r_is_correct() -> None:
    # 3 obs: mfe_1r = 0.6 (>= 0.5, < 1.0), 1.2 (>= 1.0), 0.2 (< 0.5)
    # reached_0_5r: [True, True, False] → count=2
    # reached_1_0r given 0.5r: [False, True] → count=1
    # P = 1/2 = 0.5
    obs = [
        _make_observation(mfe_1r="0.6"),
        _make_observation(mfe_1r="1.2"),
        _make_observation(mfe_1r="0.2"),
    ]
    candles_by_symbol = _minimal_candles_by_symbol()

    tagged = tag_observations(obs, candles_by_symbol)
    metrics = compute_conditional_metrics(tagged)

    htf_bucket = metrics["htf_alignment"]["not_available"]["1r"]  # type: ignore[index]
    p = Decimal(str(htf_bucket["p_reach_1r_given_reach_0_5r"]))
    assert p == Decimal("0.5")


def test_p_reach_1r_given_0_5r_none_when_no_obs_reached_0_5r() -> None:
    obs = [_make_observation(mfe_1r="0.1"), _make_observation(mfe_1r="0.2")]
    candles_by_symbol = _minimal_candles_by_symbol()

    tagged = tag_observations(obs, candles_by_symbol)
    metrics = compute_conditional_metrics(tagged)

    htf_bucket = metrics["htf_alignment"]["not_available"]["1r"]  # type: ignore[index]
    assert htf_bucket["p_reach_1r_given_reach_0_5r"] is None


# ---------------------------------------------------------------------------
# 8. Decision gate
# ---------------------------------------------------------------------------


def test_decision_gate_flags_condition_beating_overall() -> None:
    # Mix: 3 wins + 1 loss for session=Europe (expectancy=0.5), 1 loss for session=Asia (expectancy=-1)
    obs = [
        _make_observation(outcome_1r="win", session_label="Europe"),
        _make_observation(outcome_1r="win", session_label="Europe"),
        _make_observation(outcome_1r="win", session_label="Europe"),
        _make_observation(outcome_1r="loss", session_label="Europe"),
        _make_observation(outcome_1r="loss", session_label="Asia"),
    ]
    candles_by_symbol = _minimal_candles_by_symbol()

    report = build_conditional_report(obs, candles_by_symbol)

    gate = report["decision_gate"]  # type: ignore[index]
    flag_tags = [f["tag"] for f in gate["flags"]]  # type: ignore[union-attr]
    assert any("session=Europe" in tag for tag in flag_tags)


def test_decision_gate_summary_counts_qualified_conditions() -> None:
    obs = [_make_observation(outcome_1r="win") for _ in range(SAMPLE_SIZE_FLAG_THRESHOLD)]
    candles_by_symbol = _minimal_candles_by_symbol()

    report = build_conditional_report(obs, candles_by_symbol)

    gate = report["decision_gate"]  # type: ignore[index]
    assert "condition" in str(gate["summary"])


# ---------------------------------------------------------------------------
# 9. Report writers
# ---------------------------------------------------------------------------


def test_report_writers_produce_stable_artifacts() -> None:
    obs = [
        _make_observation(outcome_1r="win", session_label="Europe"),
        _make_observation(outcome_1r="loss", session_label="Asia"),
        _make_observation(outcome_1r="flat", session_label="US"),
    ]
    candles_by_symbol = _minimal_candles_by_symbol()
    report = build_conditional_report(obs, candles_by_symbol)

    output_dir = Path(".pytest-temp-run") / "setup_b_conditional_diagnostics_test"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    text_path = output_dir / "diagnostics.txt"
    json_path = output_dir / "diagnostics.json"

    write_conditional_artifacts(report, text_path=text_path, json_path=json_path)

    assert text_path.read_text(encoding="utf-8") == format_conditional_report(report)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "setup_b_conditional_diagnostics_v1"
    assert payload["observation_count"] == 3
    assert "conditional_metrics" in payload
    assert "decision_gate" in payload
    for tag_key in TAG_KEYS:
        assert tag_key in payload["conditional_metrics"]
    shutil.rmtree(output_dir)


# ---------------------------------------------------------------------------
# 10. No network imports
# ---------------------------------------------------------------------------


def test_conditional_diagnostics_modules_do_not_import_network_libraries() -> None:
    repo_root = Path(__file__).parent.parent.parent
    module_paths = [
        repo_root / "research" / "signal_observation" / "setup_b_conditional_diagnostics.py",
        repo_root / "research" / "signal_observation" / "run_setup_b_conditional_diagnostics.py",
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
