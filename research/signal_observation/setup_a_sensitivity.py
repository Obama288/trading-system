"""Diagnostics-only sensitivity analysis for Setup A parameter variants."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .candles import Candle
from .indicators import atr
from .models import (
    BtcScore,
    Direction,
    ObservationStatus,
    SetupId,
    SignalObservation,
)
from .outcomes import resolve_outcome
from .sessions import session_label
from .setup_a import (
    CONTEXT_TIMEFRAME,
    OUTCOME_WINDOW_CANDLES,
    RETEST_WINDOW_1H,
    TRIGGER_TIMEFRAME,
    VOLUME_LOOKBACK,
)
from .summary import summarize_outcomes


@dataclass(frozen=True, slots=True)
class SensitivityVariant:
    """Parameter set for one Setup A sensitivity experiment."""

    name: str
    min_touches: int
    touch_tolerance_atr: Decimal
    lookback_4h: int


VARIANTS: tuple[SensitivityVariant, ...] = (
    SensitivityVariant("baseline", 3, Decimal("0.15"), 48),
    SensitivityVariant("relaxed_touches", 2, Decimal("0.25"), 48),
    SensitivityVariant("relaxed_touches_wider_zone", 2, Decimal("0.35"), 48),
    SensitivityVariant(
        "relaxed_touches_wider_zone_longer_lookback", 2, Decimal("0.35"), 72
    ),
)


@dataclass(frozen=True, slots=True)
class SensitivitySymbolResult:
    """Sensitivity funnel result for one variant-symbol combination."""

    variant: str
    symbol: str
    source_exchange: str
    windows_checked: int
    passed_touches: int
    failed_min_touches: int
    breakout_candidates: int
    body_passed: int
    volume_passed: int
    retest_reached: int
    retest_found: int
    observations: int
    resolved: int
    wins: int
    losses: int
    flats: int
    win_rate: str | None
    expectancy_r: str | None
    profit_factor: str | None
    avg_win_r: str | None
    avg_loss_r: str | None


@dataclass(frozen=True, slots=True)
class SensitivityVariantTotals:
    """Aggregate sensitivity result for one variant across all symbols."""

    variant: str
    total_observations: int
    total_resolved: int
    total_wins: int
    total_losses: int
    total_flats: int
    aggregate_win_rate: str | None
    aggregate_expectancy_r: str | None
    aggregate_profit_factor: str | None
    largest_dropoff_stage: str


@dataclass(frozen=True, slots=True)
class SensitivityVariantResult:
    """Complete sensitivity result for one variant and its aggregates."""

    variant: str
    symbol_results: list[SensitivitySymbolResult]
    totals: SensitivityVariantTotals


def run_sensitivity_variant(
    context_candles_4h: Sequence[Candle],
    trigger_candles_1h: Sequence[Candle],
    *,
    symbol: str,
    source_exchange: str,
    variant: SensitivityVariant,
    btc_score: BtcScore = BtcScore.CHOP,
) -> SensitivitySymbolResult:
    """Run one sensitivity variant for one symbol and return funnel counts."""

    if not symbol:
        raise ValueError("symbol must not be empty")
    if not source_exchange:
        raise ValueError("source_exchange must not be empty")

    if not context_candles_4h or not trigger_candles_1h:
        return _build_empty_symbol_result(variant=variant, symbol=symbol, source_exchange=source_exchange)

    context_atr = atr(context_candles_4h, period=14)
    trigger_atr = atr(trigger_candles_1h, period=14)

    windows_checked = 0
    passed_touches = 0
    failed_min_touches = 0
    breakout_candidates = 0
    body_passed = 0
    volume_passed = 0
    retest_reached = 0
    retest_found = 0
    observations: list[SignalObservation] = []

    for index, breakout_candle in enumerate(context_candles_4h):
        atr_4h = context_atr[index]
        if atr_4h is None:
            continue
        if index < variant.lookback_4h:
            continue

        windows_checked += 1
        base = context_candles_4h[index - variant.lookback_4h : index]
        range_high = max(candle.high for candle in base)
        range_low = min(candle.low for candle in base)
        if range_high - range_low < atr_4h:
            failed_min_touches += 1
            continue

        touch_tolerance = atr_4h * variant.touch_tolerance_atr
        touches = [
            candle
            for candle in base
            if range_high - touch_tolerance <= candle.high <= range_high
        ]
        if len(touches) < variant.min_touches:
            failed_min_touches += 1
            continue

        passed_touches += 1
        if breakout_candle.close <= range_high:
            continue

        breakout_candidates += 1
        if breakout_candle.close - range_high < atr_4h * Decimal("0.2"):
            continue

        candle_range = breakout_candle.high - breakout_candle.low
        candle_body = abs(breakout_candle.close - breakout_candle.open)
        if candle_range <= Decimal("0") or candle_body < candle_range * Decimal("0.5"):
            continue

        body_passed += 1
        average_volume = (
            sum(candle.volume for candle in context_candles_4h[index - VOLUME_LOOKBACK : index])
            / Decimal(VOLUME_LOOKBACK)
        )
        if breakout_candle.volume <= average_volume * Decimal("1.5"):
            continue

        volume_passed += 1
        retest_reached += 1
        obs = _detect_retest_observation(
            trigger_candles_1h=trigger_candles_1h,
            trigger_atr=trigger_atr,
            breakout_time=breakout_candle.timestamp,
            range_high=range_high,
            symbol=symbol,
            source_exchange=source_exchange,
            btc_score=btc_score,
            variant_name=variant.name,
        )
        if obs is not None:
            retest_found += 1
            observations.append(obs)

    outcomes = [resolve_outcome(obs, trigger_candles_1h) for obs in observations]
    metrics = summarize_outcomes(outcomes)

    return SensitivitySymbolResult(
        variant=variant.name,
        symbol=symbol,
        source_exchange=source_exchange,
        windows_checked=windows_checked,
        passed_touches=passed_touches,
        failed_min_touches=failed_min_touches,
        breakout_candidates=breakout_candidates,
        body_passed=body_passed,
        volume_passed=volume_passed,
        retest_reached=retest_reached,
        retest_found=retest_found,
        observations=len(observations),
        resolved=metrics.resolved_count,
        wins=metrics.win_count,
        losses=metrics.loss_count,
        flats=metrics.flat_count,
        win_rate=_decimal_str(metrics.win_rate),
        expectancy_r=_decimal_str(metrics.expectancy_r),
        profit_factor=_decimal_str(metrics.profit_factor),
        avg_win_r=_decimal_str(metrics.avg_win_r),
        avg_loss_r=_decimal_str(metrics.avg_loss_r),
    )


def compute_variant_totals(
    symbol_results: Sequence[SensitivitySymbolResult],
    variant_name: str,
) -> SensitivityVariantTotals:
    """Aggregate symbol results into per-variant totals."""

    total_obs = sum(r.observations for r in symbol_results)
    total_resolved = sum(r.resolved for r in symbol_results)
    total_wins = sum(r.wins for r in symbol_results)
    total_losses = sum(r.losses for r in symbol_results)
    total_flats = sum(r.flats for r in symbol_results)

    if total_resolved > 0:
        agg_win_rate = _decimal_str(Decimal(total_wins) / Decimal(total_resolved))
        resolved_values = []
        for r in symbol_results:
            if r.expectancy_r is not None:
                resolved_values.append((Decimal(r.expectancy_r), r.resolved))
        if resolved_values:
            weighted_sum = sum(v * Decimal(n) for v, n in resolved_values)
            agg_expectancy = _decimal_str(weighted_sum / Decimal(total_resolved))
        else:
            agg_expectancy = None
    else:
        agg_win_rate = None
        agg_expectancy = None

    agg_pf = _aggregate_profit_factor(symbol_results)

    largest_stage = _largest_dropoff_stage(symbol_results)

    return SensitivityVariantTotals(
        variant=variant_name,
        total_observations=total_obs,
        total_resolved=total_resolved,
        total_wins=total_wins,
        total_losses=total_losses,
        total_flats=total_flats,
        aggregate_win_rate=agg_win_rate,
        aggregate_expectancy_r=agg_expectancy,
        aggregate_profit_factor=agg_pf,
        largest_dropoff_stage=largest_stage,
    )


def format_sensitivity_report(
    variant_results: Sequence[SensitivityVariantResult],
) -> str:
    """Format stable text diagnostics for repo artifacts and CLI output."""

    lines = ["Setup A sensitivity diagnostics", ""]
    for vr in variant_results:
        lines.append(f"=== variant: {vr.variant} ===")
        lines.append("")
        for sr in vr.symbol_results:
            lines.extend([
                f"  symbol: {sr.symbol}",
                f"  source_exchange: {sr.source_exchange}",
                f"  windows_checked: {sr.windows_checked}",
                f"  passed_touches: {sr.passed_touches}",
                f"  failed_min_touches: {sr.failed_min_touches}",
                f"  breakout_candidates: {sr.breakout_candidates}",
                f"  body_passed: {sr.body_passed}",
                f"  volume_passed: {sr.volume_passed}",
                f"  retest_reached: {sr.retest_reached}",
                f"  retest_found: {sr.retest_found}",
                f"  observations: {sr.observations}",
                f"  resolved: {sr.resolved}",
                f"  wins: {sr.wins}",
                f"  losses: {sr.losses}",
                f"  flats: {sr.flats}",
                f"  win_rate: {sr.win_rate if sr.win_rate is not None else 'n/a'}",
                f"  expectancy_r: {sr.expectancy_r if sr.expectancy_r is not None else 'n/a'}",
                f"  profit_factor: {sr.profit_factor if sr.profit_factor is not None else 'n/a'}",
                f"  avg_win_r: {sr.avg_win_r if sr.avg_win_r is not None else 'n/a'}",
                f"  avg_loss_r: {sr.avg_loss_r if sr.avg_loss_r is not None else 'n/a'}",
                "",
            ])
        t = vr.totals
        lines.extend([
            f"  --- totals ---",
            f"  total_observations: {t.total_observations}",
            f"  total_resolved: {t.total_resolved}",
            f"  total_wins: {t.total_wins}",
            f"  total_losses: {t.total_losses}",
            f"  total_flats: {t.total_flats}",
            f"  aggregate_win_rate: {t.aggregate_win_rate if t.aggregate_win_rate is not None else 'n/a'}",
            f"  aggregate_expectancy_r: {t.aggregate_expectancy_r if t.aggregate_expectancy_r is not None else 'n/a'}",
            f"  aggregate_profit_factor: {t.aggregate_profit_factor if t.aggregate_profit_factor is not None else 'n/a'}",
            f"  largest_dropoff_stage: {t.largest_dropoff_stage}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def write_sensitivity_artifacts(
    variant_results: Sequence[SensitivityVariantResult],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic text and JSON sensitivity artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)

    text_output.write_text(format_sensitivity_report(variant_results), encoding="utf-8")
    json_output.write_text(
        json.dumps(
            [asdict(vr) for vr in variant_results],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _detect_retest_observation(
    *,
    trigger_candles_1h: Sequence[Candle],
    trigger_atr: Sequence[Decimal | None],
    breakout_time: datetime,
    range_high: Decimal,
    symbol: str,
    source_exchange: str,
    btc_score: BtcScore,
    variant_name: str,
) -> SignalObservation | None:
    after_breakout = [
        (index, candle)
        for index, candle in enumerate(trigger_candles_1h)
        if candle.timestamp > breakout_time
    ][:RETEST_WINDOW_1H]

    retest_candidates: list[tuple[int, Candle]] = []
    for index, candle in after_breakout:
        atr_1h = trigger_atr[index]
        if atr_1h is None:
            continue
        retest_tolerance = atr_1h * Decimal("0.25")
        if candle.low <= range_high + retest_tolerance and candle.high >= range_high - retest_tolerance:
            retest_candidates.append((index, candle))
        if retest_candidates and candle.close > range_high:
            entry_index = index + 1
            if entry_index >= len(trigger_candles_1h):
                return None
            entry_candle = trigger_candles_1h[entry_index]
            stop_atr = trigger_atr[index]
            if stop_atr is None:
                return None
            retest_swing_low = min(item.low for _, item in retest_candidates)
            stop = retest_swing_low - (stop_atr * Decimal("0.1"))
            entry = entry_candle.open
            initial_r = entry - stop
            if initial_r <= Decimal("0"):
                return None
            target = entry + (Decimal("2") * initial_r)
            signal_time = candle.timestamp.astimezone(UTC)
            compact_time = signal_time.strftime("%Y%m%dT%H%M%SZ")
            obs_id = f"setup-a-sens-{variant_name}-{symbol.lower()}-{compact_time}"

            return SignalObservation(
                observation_id=obs_id,
                created_at_utc=signal_time,
                source_exchange=source_exchange,
                symbol=symbol,
                setup_id=SetupId.A,
                direction=Direction.LONG,
                context_timeframe=CONTEXT_TIMEFRAME,
                trigger_timeframe=TRIGGER_TIMEFRAME,
                signal_time=signal_time,
                entry_time_theoretical=entry_candle.timestamp,
                entry_price_theoretical=entry,
                stop_price_theoretical=stop,
                target_price_theoretical=target,
                initial_r=initial_r,
                btc_score=btc_score,
                session_utc_hour=signal_time.hour,
                session_label=session_label(signal_time),
                status=ObservationStatus.VALID,
                outcome_window_candles=OUTCOME_WINDOW_CANDLES,
            )

    return None


def _build_empty_symbol_result(
    *,
    variant: SensitivityVariant,
    symbol: str,
    source_exchange: str,
) -> SensitivitySymbolResult:
    return SensitivitySymbolResult(
        variant=variant.name,
        symbol=symbol,
        source_exchange=source_exchange,
        windows_checked=0,
        passed_touches=0,
        failed_min_touches=0,
        breakout_candidates=0,
        body_passed=0,
        volume_passed=0,
        retest_reached=0,
        retest_found=0,
        observations=0,
        resolved=0,
        wins=0,
        losses=0,
        flats=0,
        win_rate=None,
        expectancy_r=None,
        profit_factor=None,
        avg_win_r=None,
        avg_loss_r=None,
    )


def _decimal_str(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _aggregate_profit_factor(
    symbol_results: Sequence[SensitivitySymbolResult],
) -> str | None:
    total_wins_r = Decimal("0")
    total_losses_r = Decimal("0")
    for r in symbol_results:
        if r.avg_win_r is not None and r.wins > 0:
            total_wins_r += Decimal(r.avg_win_r) * Decimal(r.wins)
        if r.avg_loss_r is not None and r.losses > 0:
            total_losses_r += Decimal(r.avg_loss_r) * Decimal(r.losses)
    if total_losses_r == Decimal("0"):
        return None
    pf = total_wins_r / abs(total_losses_r)
    return str(pf)


def _largest_dropoff_stage(
    symbol_results: Sequence[SensitivitySymbolResult],
) -> str:
    total_failed_touches = sum(r.failed_min_touches for r in symbol_results)
    total_passed_touches = sum(r.passed_touches for r in symbol_results)
    total_breakout = sum(r.breakout_candidates for r in symbol_results)
    total_body = sum(r.body_passed for r in symbol_results)
    total_volume = sum(r.volume_passed for r in symbol_results)
    total_retest_reached = sum(r.retest_reached for r in symbol_results)
    total_retest_found = sum(r.retest_found for r in symbol_results)

    drops = {
        "min_touches": total_failed_touches,
        "no_breakout": total_passed_touches - total_breakout,
        "breakout_distance_or_body": total_breakout - total_body,
        "volume": total_body - total_volume,
        "no_retest": total_retest_reached - total_retest_found,
    }
    return max(drops, key=lambda k: drops[k])
