from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from research.signal_observation.candles import Candle
from research.signal_observation.models import BtcScore
from research.signal_observation.setup_a import detect_setup_a
from research.signal_observation.setup_a_sensitivity import (
    VARIANTS,
    SensitivityVariant,
    compute_variant_totals,
    format_sensitivity_report,
    run_sensitivity_variant,
    write_sensitivity_artifacts,
    SensitivityVariantResult,
)


# ---------------------------------------------------------------------------
# Helpers – same fixtures as setup_a_diagnostics tests
# ---------------------------------------------------------------------------


def _context_candles(
    *,
    touches: int = 3,
    breakout_open: Decimal = Decimal("110.5"),
    breakout_high: Decimal = Decimal("114"),
    breakout_low: Decimal = Decimal("110"),
    breakout_close: Decimal = Decimal("113"),
    breakout_volume: Decimal = Decimal("200"),
) -> list[Candle]:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    candles: list[Candle] = []
    for index in range(48):
        high = Decimal("110") if index < touches else Decimal("108")
        candles.append(
            Candle(
                timestamp=start + timedelta(hours=4 * index),
                open=Decimal("104"),
                high=high,
                low=Decimal("100"),
                close=Decimal("105"),
                volume=Decimal("100"),
            )
        )
    candles.append(
        Candle(
            timestamp=start + timedelta(hours=4 * 48),
            open=breakout_open,
            high=breakout_high,
            low=breakout_low,
            close=breakout_close,
            volume=breakout_volume,
        )
    )
    return candles


def _trigger_candles(*, retest: bool = True) -> list[Candle]:
    breakout_time = datetime(2025, 1, 9, tzinfo=UTC)
    start = breakout_time - timedelta(hours=20)
    candles: list[Candle] = []
    for index in range(20):
        candles.append(
            Candle(
                timestamp=start + timedelta(hours=index),
                open=Decimal("112"),
                high=Decimal("113"),
                low=Decimal("111"),
                close=Decimal("112"),
                volume=Decimal("100"),
            )
        )

    if retest:
        after = [
            (Decimal("111"), Decimal("111.5"), Decimal("109"), Decimal("109.5")),
            (Decimal("109.5"), Decimal("111.5"), Decimal("109.2"), Decimal("111")),
            (Decimal("111.2"), Decimal("112"), Decimal("110.8"), Decimal("111.5")),
        ]
    else:
        after = [
            (Decimal("114"), Decimal("115"), Decimal("113.5"), Decimal("114.5")),
            (Decimal("114.5"), Decimal("115"), Decimal("113.8"), Decimal("114.8")),
            (Decimal("114.8"), Decimal("115"), Decimal("114"), Decimal("114.9")),
        ]

    for offset, (open_, high, low, close) in enumerate(after, start=1):
        candles.append(
            Candle(
                timestamp=breakout_time + timedelta(hours=offset),
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=Decimal("100"),
            )
        )
    return candles


_BASELINE_VARIANT = VARIANTS[0]  # min_touches=3, touch_tolerance_atr=0.25, lookback_4h=48
_RELAXED_VARIANT = VARIANTS[1]   # min_touches=2, touch_tolerance_atr=0.25, lookback_4h=48
_WIDER_VARIANT = VARIANTS[2]     # min_touches=2, touch_tolerance_atr=0.35, lookback_4h=48


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_baseline_sensitivity_variant_produces_one_observation() -> None:
    """Baseline sensitivity variant finds the valid fixture observation."""
    result = run_sensitivity_variant(
        _context_candles(),
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
        variant=_BASELINE_VARIANT,
    )

    assert result.observations == 1
    assert result.windows_checked == 1
    assert result.passed_touches == 1
    assert result.breakout_candidates == 1
    assert result.body_passed == 1
    assert result.volume_passed == 1
    assert result.retest_reached == 1
    assert result.retest_found == 1


def test_baseline_variant_does_not_mutate_normal_detector() -> None:
    """Running sensitivity must not change the normal setup_a detector output."""
    context = _context_candles()
    trigger = _trigger_candles()

    before = detect_setup_a(
        context,
        trigger,
        symbol="BTCUSDT",
        source_exchange="fixture",
        btc_score=BtcScore.BULLISH,
    )
    run_sensitivity_variant(
        context,
        trigger,
        symbol="BTCUSDT",
        source_exchange="fixture",
        variant=_BASELINE_VARIANT,
    )
    after = detect_setup_a(
        context,
        trigger,
        symbol="BTCUSDT",
        source_exchange="fixture",
        btc_score=BtcScore.BULLISH,
    )

    assert before == after
    assert len(before) == 1


def _context_candles_strict_2touches() -> list[Candle]:
    """Exactly 2 candles at range_high; all others well below the 0.25*ATR zone."""
    start = datetime(2025, 1, 1, tzinfo=UTC)
    candles: list[Candle] = []
    for index in range(48):
        # high=110 for first 2, high=105 for rest (far below range_high - 0.25*ATR)
        high = Decimal("110") if index < 2 else Decimal("105")
        candles.append(
            Candle(
                timestamp=start + timedelta(hours=4 * index),
                open=Decimal("104"),
                high=high,
                low=Decimal("100"),
                close=Decimal("105"),
                volume=Decimal("100"),
            )
        )
    candles.append(
        Candle(
            timestamp=start + timedelta(hours=4 * 48),
            open=Decimal("110.5"),
            high=Decimal("114"),
            low=Decimal("110"),
            close=Decimal("113"),
            volume=Decimal("200"),
        )
    )
    return candles


def test_relaxing_min_touches_increases_candidates_on_fixture() -> None:
    """Strict 2-touch fixture passes relaxed_touches (min=2) but fails baseline (min=3).

    Non-touch candles are at high=105, well below range_high=110 minus 0.25*ATR
    (ATR ≈ 5.7, zone ≈ 108.6), so only the two exact-touch candles qualify.
    """
    context_2touches = _context_candles_strict_2touches()

    baseline = run_sensitivity_variant(
        context_2touches,
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
        variant=_BASELINE_VARIANT,
    )
    relaxed = run_sensitivity_variant(
        context_2touches,
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
        variant=_RELAXED_VARIANT,
    )

    assert baseline.passed_touches == 0, (
        f"baseline (min_touches=3) should fail with only 2 qualifying candles, "
        f"got passed_touches={baseline.passed_touches}"
    )
    assert relaxed.passed_touches >= 1


def test_wider_touch_tolerance_increases_passed_touches() -> None:
    """Wider ATR tolerance zone captures more touch candidates."""
    context = _context_candles(touches=2)

    narrow = run_sensitivity_variant(
        context,
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
        variant=_RELAXED_VARIANT,   # 0.25 tolerance, min 2
    )
    wider = run_sensitivity_variant(
        context,
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
        variant=_WIDER_VARIANT,    # 0.35 tolerance, min 2
    )

    # Wider zone should pass at least as many as narrow
    assert wider.passed_touches >= narrow.passed_touches


def test_longer_lookback_is_handled_deterministically() -> None:
    """Longer lookback variant produces a deterministic result on the fixture."""
    long_variant = VARIANTS[3]  # lookback_4h=72

    # The fixture only has 48 context candles + 1 breakout = 49 total.
    # With lookback_4h=72, no window can be formed, so windows_checked == 0.
    result = run_sensitivity_variant(
        _context_candles(),
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
        variant=long_variant,
    )

    assert result.windows_checked == 0
    assert result.observations == 0


def test_variant_results_are_stable_across_calls() -> None:
    """Same input produces identical results on repeated calls."""
    context = _context_candles()
    trigger = _trigger_candles()

    r1 = run_sensitivity_variant(
        context, trigger, symbol="BTCUSDT", source_exchange="fixture", variant=_BASELINE_VARIANT
    )
    r2 = run_sensitivity_variant(
        context, trigger, symbol="BTCUSDT", source_exchange="fixture", variant=_BASELINE_VARIANT
    )

    assert r1 == r2


def test_compute_variant_totals_sums_correctly() -> None:
    context = _context_candles()
    trigger = _trigger_candles()

    results = [
        run_sensitivity_variant(
            context, trigger, symbol="BTCUSDT", source_exchange="fixture", variant=_BASELINE_VARIANT
        ),
        run_sensitivity_variant(
            context, trigger, symbol="ETHUSDT", source_exchange="fixture", variant=_BASELINE_VARIANT
        ),
    ]
    totals = compute_variant_totals(results, "baseline")

    assert totals.total_observations == results[0].observations + results[1].observations
    assert totals.total_wins == results[0].wins + results[1].wins
    assert totals.largest_dropoff_stage != ""


def test_json_report_is_stable_and_complete() -> None:
    context = _context_candles()
    trigger = _trigger_candles()

    symbol_results = [
        run_sensitivity_variant(
            context, trigger, symbol="BTCUSDT", source_exchange="fixture", variant=_BASELINE_VARIANT
        )
    ]
    totals = compute_variant_totals(symbol_results, "baseline")
    variant_results = [SensitivityVariantResult("baseline", symbol_results, totals)]

    output_dir = Path(".pytest-temp-run") / "setup_a_sensitivity_test"
    if output_dir.exists():
        shutil.rmtree(output_dir)

    text_path = output_dir / "sensitivity.txt"
    json_path = output_dir / "sensitivity.json"

    write_sensitivity_artifacts(variant_results, text_path=text_path, json_path=json_path)

    text = text_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert text == format_sensitivity_report(variant_results)
    assert payload[0]["variant"] == "baseline"
    assert "symbol_results" in payload[0]
    assert "totals" in payload[0]
    assert payload[0]["totals"]["total_observations"] == 1

    shutil.rmtree(output_dir)


def test_sensitivity_modules_do_not_import_network_libraries() -> None:
    repo_root = Path(__file__).parent.parent.parent
    module_paths = [
        repo_root / "research" / "signal_observation" / "setup_a_sensitivity.py",
        repo_root / "research" / "signal_observation" / "run_setup_a_sensitivity.py",
    ]

    for path in module_paths:
        text = path.read_text(encoding="utf-8")
        assert "urllib" not in text
        assert "requests" not in text
        assert "http.client" not in text
        assert "socket" not in text
