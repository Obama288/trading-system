"""Diagnostics-only funnel counters for Setup A research observations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .candles import Candle
from .indicators import atr
from .models import BtcScore, Direction
from .outcomes import resolve_outcome
from .setup_a import (
    LOOKBACK_CANDLES_4H,
    MIN_TOUCHES,
    RETEST_WINDOW_1H,
    VOLUME_LOOKBACK,
    detect_setup_a,
)
from .summary import summarize_outcomes


@dataclass(frozen=True, slots=True)
class SetupAFunnelDiagnostics:
    """Deterministic drop-off counters for one Setup A diagnostic run."""

    symbol: str
    source_exchange: str
    base_windows_checked: int
    range_touch_candidates: int
    passed_min_touches: int
    breakout_candidates: int
    passed_breakout_distance: int
    passed_body_ratio: int
    passed_volume: int
    retest_search_reached: int
    retest_candidates_found: int
    final_observations: int
    resolved: int
    wins: int
    losses: int
    flats: int
    failed_min_touches: int
    failed_no_breakout: int
    failed_breakout_distance: int
    failed_body_ratio: int
    failed_volume: int
    failed_no_retest: int
    failed_unresolved_outcome: int


@dataclass(frozen=True, slots=True)
class _RetestInspection:
    retest_candidates_found: bool
    final_observation_found: bool


def diagnose_setup_a(
    context_candles_4h: Sequence[Candle],
    trigger_candles_1h: Sequence[Candle],
    *,
    symbol: str,
    source_exchange: str,
    btc_score: BtcScore = BtcScore.CHOP,
) -> SetupAFunnelDiagnostics:
    """Count Setup A funnel stages without changing detector behavior."""

    if not symbol:
        raise ValueError("symbol must not be empty")
    if not source_exchange:
        raise ValueError("source_exchange must not be empty")

    counters = _new_counters()
    observations = detect_setup_a(
        context_candles_4h,
        trigger_candles_1h,
        symbol=symbol,
        source_exchange=source_exchange,
        direction=Direction.LONG,
        btc_score=btc_score,
    )
    outcomes = [
        resolve_outcome(observation, trigger_candles_1h)
        for observation in observations
    ]
    metrics = summarize_outcomes(outcomes)

    if context_candles_4h and trigger_candles_1h:
        _count_funnel(
            counters=counters,
            context_candles_4h=context_candles_4h,
            trigger_candles_1h=trigger_candles_1h,
        )

    return SetupAFunnelDiagnostics(
        symbol=symbol,
        source_exchange=source_exchange,
        base_windows_checked=counters["base_windows_checked"],
        range_touch_candidates=counters["range_touch_candidates"],
        passed_min_touches=counters["passed_min_touches"],
        breakout_candidates=counters["breakout_candidates"],
        passed_breakout_distance=counters["passed_breakout_distance"],
        passed_body_ratio=counters["passed_body_ratio"],
        passed_volume=counters["passed_volume"],
        retest_search_reached=counters["retest_search_reached"],
        retest_candidates_found=counters["retest_candidates_found"],
        final_observations=len(observations),
        resolved=metrics.resolved_count,
        wins=metrics.win_count,
        losses=metrics.loss_count,
        flats=metrics.flat_count,
        failed_min_touches=counters["failed_min_touches"],
        failed_no_breakout=counters["failed_no_breakout"],
        failed_breakout_distance=counters["failed_breakout_distance"],
        failed_body_ratio=counters["failed_body_ratio"],
        failed_volume=counters["failed_volume"],
        failed_no_retest=counters["failed_no_retest"],
        failed_unresolved_outcome=len(observations) - metrics.resolved_count,
    )


def format_diagnostics_report(
    diagnostics: Sequence[SetupAFunnelDiagnostics],
) -> str:
    """Format stable text diagnostics for repo artifacts and CLI output."""

    lines = ["Setup A funnel diagnostics", ""]
    for item in diagnostics:
        lines.extend(
            [
                f"symbol: {item.symbol}",
                f"source_exchange: {item.source_exchange}",
                f"base_windows_checked: {item.base_windows_checked}",
                f"range_touch_candidates: {item.range_touch_candidates}",
                f"passed_min_touches: {item.passed_min_touches}",
                f"breakout_candidates: {item.breakout_candidates}",
                f"passed_breakout_distance: {item.passed_breakout_distance}",
                f"passed_body_ratio: {item.passed_body_ratio}",
                f"passed_volume: {item.passed_volume}",
                f"retest_search_reached: {item.retest_search_reached}",
                f"retest_candidates_found: {item.retest_candidates_found}",
                f"final_observations: {item.final_observations}",
                f"resolved: {item.resolved}",
                f"wins: {item.wins}",
                f"losses: {item.losses}",
                f"flats: {item.flats}",
                f"failed_min_touches: {item.failed_min_touches}",
                f"failed_no_breakout: {item.failed_no_breakout}",
                f"failed_breakout_distance: {item.failed_breakout_distance}",
                f"failed_body_ratio: {item.failed_body_ratio}",
                f"failed_volume: {item.failed_volume}",
                f"failed_no_retest: {item.failed_no_retest}",
                f"failed_unresolved_outcome: {item.failed_unresolved_outcome}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_diagnostics_artifacts(
    diagnostics: Sequence[SetupAFunnelDiagnostics],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic text and JSON diagnostics artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)

    text_output.write_text(format_diagnostics_report(diagnostics), encoding="utf-8")
    json_output.write_text(
        json.dumps(
            [asdict(item) for item in diagnostics],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _new_counters() -> dict[str, int]:
    return {
        "base_windows_checked": 0,
        "range_touch_candidates": 0,
        "passed_min_touches": 0,
        "breakout_candidates": 0,
        "passed_breakout_distance": 0,
        "passed_body_ratio": 0,
        "passed_volume": 0,
        "retest_search_reached": 0,
        "retest_candidates_found": 0,
        "failed_min_touches": 0,
        "failed_no_breakout": 0,
        "failed_breakout_distance": 0,
        "failed_body_ratio": 0,
        "failed_volume": 0,
        "failed_no_retest": 0,
    }


def _count_funnel(
    *,
    counters: dict[str, int],
    context_candles_4h: Sequence[Candle],
    trigger_candles_1h: Sequence[Candle],
) -> None:
    context_atr = atr(context_candles_4h, period=14)
    trigger_atr = atr(trigger_candles_1h, period=14)

    for index, breakout_candle in enumerate(context_candles_4h):
        atr_4h = context_atr[index]
        if atr_4h is None:
            continue
        if index < LOOKBACK_CANDLES_4H:
            continue

        counters["base_windows_checked"] += 1
        base = context_candles_4h[index - LOOKBACK_CANDLES_4H : index]
        range_high = max(candle.high for candle in base)
        range_low = min(candle.low for candle in base)
        if range_high - range_low < atr_4h:
            counters["failed_min_touches"] += 1
            continue

        counters["range_touch_candidates"] += 1
        touch_tolerance = atr_4h * Decimal("0.15")
        touches = [
            candle
            for candle in base
            if range_high - touch_tolerance <= candle.high <= range_high
        ]
        if len(touches) < MIN_TOUCHES:
            counters["failed_min_touches"] += 1
            continue

        counters["passed_min_touches"] += 1
        if breakout_candle.close <= range_high:
            counters["failed_no_breakout"] += 1
            continue

        counters["breakout_candidates"] += 1
        if breakout_candle.close - range_high < atr_4h * Decimal("0.2"):
            counters["failed_breakout_distance"] += 1
            continue

        counters["passed_breakout_distance"] += 1
        candle_range = breakout_candle.high - breakout_candle.low
        candle_body = abs(breakout_candle.close - breakout_candle.open)
        if candle_range <= Decimal("0") or candle_body < candle_range * Decimal("0.5"):
            counters["failed_body_ratio"] += 1
            continue

        counters["passed_body_ratio"] += 1
        average_volume = (
            sum(candle.volume for candle in context_candles_4h[index - VOLUME_LOOKBACK : index])
            / Decimal(VOLUME_LOOKBACK)
        )
        if breakout_candle.volume <= average_volume * Decimal("1.5"):
            counters["failed_volume"] += 1
            continue

        counters["passed_volume"] += 1
        counters["retest_search_reached"] += 1
        retest = _inspect_retest(
            trigger_candles_1h=trigger_candles_1h,
            trigger_atr=trigger_atr,
            breakout_time=breakout_candle.timestamp,
            range_high=range_high,
        )
        if retest.retest_candidates_found:
            counters["retest_candidates_found"] += 1
        if not retest.final_observation_found:
            counters["failed_no_retest"] += 1


def _inspect_retest(
    *,
    trigger_candles_1h: Sequence[Candle],
    trigger_atr: Sequence[Decimal | None],
    breakout_time,
    range_high: Decimal,
) -> _RetestInspection:
    after_breakout = [
        (index, candle)
        for index, candle in enumerate(trigger_candles_1h)
        if candle.timestamp > breakout_time
    ][:RETEST_WINDOW_1H]

    retest_candidates: list[tuple[int, Candle]] = []
    found_candidate = False
    for index, candle in after_breakout:
        atr_1h = trigger_atr[index]
        if atr_1h is None:
            continue
        retest_tolerance = atr_1h * Decimal("0.25")
        if (
            candle.low <= range_high + retest_tolerance
            and candle.high >= range_high - retest_tolerance
        ):
            retest_candidates.append((index, candle))
            found_candidate = True
        if retest_candidates and candle.close > range_high:
            entry_index = index + 1
            if entry_index >= len(trigger_candles_1h):
                return _RetestInspection(found_candidate, False)
            stop_atr = trigger_atr[index]
            if stop_atr is None:
                return _RetestInspection(found_candidate, False)
            entry = trigger_candles_1h[entry_index].open
            retest_swing_low = min(item.low for _, item in retest_candidates)
            stop = retest_swing_low - (stop_atr * Decimal("0.1"))
            if entry - stop <= Decimal("0"):
                return _RetestInspection(found_candidate, False)
            return _RetestInspection(found_candidate, True)

    return _RetestInspection(found_candidate, False)
