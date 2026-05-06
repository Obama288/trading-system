from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from research.signal_observation.candles import Candle
from research.signal_observation.models import BtcScore
from research.signal_observation.setup_a import detect_setup_a
from research.signal_observation.setup_a_diagnostics import (
    diagnose_setup_a,
    format_diagnostics_report,
    write_diagnostics_artifacts,
)


def test_diagnostics_do_not_change_normal_detector_output() -> None:
    context = _context_candles()
    trigger = _trigger_candles()

    before = detect_setup_a(
        context,
        trigger,
        symbol="BTCUSDT",
        source_exchange="fixture",
        btc_score=BtcScore.BULLISH,
    )
    diagnostics = diagnose_setup_a(
        context,
        trigger,
        symbol="BTCUSDT",
        source_exchange="fixture",
        btc_score=BtcScore.BULLISH,
    )
    after = detect_setup_a(
        context,
        trigger,
        symbol="BTCUSDT",
        source_exchange="fixture",
        btc_score=BtcScore.BULLISH,
    )

    assert before == after
    assert diagnostics.final_observations == len(before) == 1
    assert before[0].btc_score is BtcScore.BULLISH


def test_funnel_counts_are_deterministic_for_valid_fixture() -> None:
    diagnostics = diagnose_setup_a(
        _context_candles(),
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
    )

    assert diagnostics.base_windows_checked == 1
    assert diagnostics.range_touch_candidates == 1
    assert diagnostics.passed_min_touches == 1
    assert diagnostics.breakout_candidates == 1
    assert diagnostics.passed_breakout_distance == 1
    assert diagnostics.passed_body_ratio == 1
    assert diagnostics.passed_volume == 1
    assert diagnostics.retest_search_reached == 1
    assert diagnostics.retest_candidates_found == 1
    assert diagnostics.final_observations == 1


def test_min_touches_failure_is_counted() -> None:
    diagnostics = diagnose_setup_a(
        _context_candles(touches=2),
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
    )

    assert diagnostics.range_touch_candidates == 1
    assert diagnostics.failed_min_touches == 1
    assert diagnostics.final_observations == 0


def test_breakout_distance_failure_is_counted() -> None:
    diagnostics = diagnose_setup_a(
        _context_candles(breakout_close=Decimal("111")),
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
    )

    assert diagnostics.breakout_candidates == 1
    assert diagnostics.failed_breakout_distance == 1
    assert diagnostics.final_observations == 0


def test_body_ratio_failure_is_counted() -> None:
    diagnostics = diagnose_setup_a(
        _context_candles(
            breakout_open=Decimal("112.8"),
            breakout_high=Decimal("116"),
            breakout_low=Decimal("110"),
            breakout_close=Decimal("113"),
        ),
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
    )

    assert diagnostics.passed_breakout_distance == 1
    assert diagnostics.failed_body_ratio == 1
    assert diagnostics.final_observations == 0


def test_volume_failure_is_counted() -> None:
    diagnostics = diagnose_setup_a(
        _context_candles(breakout_volume=Decimal("120")),
        _trigger_candles(),
        symbol="BTCUSDT",
        source_exchange="fixture",
    )

    assert diagnostics.passed_body_ratio == 1
    assert diagnostics.failed_volume == 1
    assert diagnostics.final_observations == 0


def test_retest_failure_is_counted() -> None:
    diagnostics = diagnose_setup_a(
        _context_candles(),
        _trigger_candles(retest=False),
        symbol="BTCUSDT",
        source_exchange="fixture",
    )

    assert diagnostics.retest_search_reached == 1
    assert diagnostics.failed_no_retest == 1
    assert diagnostics.final_observations == 0


def test_report_writers_are_stable() -> None:
    diagnostics = [
        diagnose_setup_a(
            _context_candles(),
            _trigger_candles(),
            symbol="BTCUSDT",
            source_exchange="fixture",
        )
    ]
    output_dir = Path(".pytest-temp-run") / "setup_a_diagnostics_test"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    text_path = output_dir / "diagnostics.txt"
    json_path = output_dir / "diagnostics.json"

    write_diagnostics_artifacts(
        diagnostics,
        text_path=text_path,
        json_path=json_path,
    )

    text = text_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert text == format_diagnostics_report(diagnostics)
    assert payload[0]["symbol"] == "BTCUSDT"
    assert payload[0]["final_observations"] == 1
    shutil.rmtree(output_dir)


def test_diagnostics_modules_do_not_import_network_libraries() -> None:
    repo_root = Path(__file__).parent.parent.parent
    module_paths = [
        repo_root / "research" / "signal_observation" / "setup_a_diagnostics.py",
        repo_root / "research" / "signal_observation" / "run_setup_a_diagnostics.py",
    ]

    for path in module_paths:
        text = path.read_text(encoding="utf-8")
        assert "urllib" not in text
        assert "requests" not in text
        assert "http.client" not in text
        assert "socket" not in text


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
