"""Diagnostics and artifact helpers for Setup B research observations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Sequence

from .candles import Candle
from .setup_b import (
    SetupBDetectionResult,
    SetupBObservation,
    SignalDirection,
    detect_setup_b_with_diagnostics,
)


@dataclass(frozen=True, slots=True)
class SetupBDiagnosticsSummary:
    """Stable diagnostics summary for one symbol/direction pair."""

    symbol: str
    direction: str
    candles_loaded: int
    windows_checked: int
    pivots_detected: int
    trend_detected: int
    pullback_candidates: int
    valid_pullbacks: int
    pullback_invalidated_before_bos: int
    bos_candidates: int
    bos_confirmed: int
    entry_observations: int
    resolved_1r: int
    wins_1r: int
    losses_1r: int
    flats_1r: int
    resolved_1_5r: int
    wins_1_5r: int
    losses_1_5r: int
    flats_1_5r: int
    resolved_2r: int
    wins_2r: int
    losses_2r: int
    flats_2r: int
    expectancy_r_1r: Decimal | None
    expectancy_r_1_5r: Decimal | None
    expectancy_r_2r: Decimal | None
    failures_by_reason: dict[str, int]


def diagnose_setup_b(
    candles_4h: Sequence[Candle],
    *,
    symbol: str,
    direction: SignalDirection,
) -> tuple[SetupBDiagnosticsSummary, list[SetupBObservation]]:
    """Run Setup B detector and return deterministic diagnostics."""

    result = detect_setup_b_with_diagnostics(
        candles_4h,
        symbol=symbol,
        direction=direction,
    )
    return _summary_from_result(result), result.observations


def format_setup_b_diagnostics_report(
    diagnostics: Sequence[SetupBDiagnosticsSummary],
) -> str:
    """Format stable text diagnostics for CLI and artifacts."""

    lines = ["Setup B diagnostics", ""]
    for item in diagnostics:
        lines.extend(
            [
                f"symbol: {item.symbol}",
                f"direction: {item.direction}",
                f"candles_loaded: {item.candles_loaded}",
                f"windows_checked: {item.windows_checked}",
                f"pivots_detected: {item.pivots_detected}",
                f"trend_detected: {item.trend_detected}",
                f"pullback_candidates: {item.pullback_candidates}",
                f"valid_pullbacks: {item.valid_pullbacks}",
                (
                    "pullback_invalidated_before_bos: "
                    f"{item.pullback_invalidated_before_bos}"
                ),
                f"bos_candidates: {item.bos_candidates}",
                f"bos_confirmed: {item.bos_confirmed}",
                f"entry_observations: {item.entry_observations}",
                f"resolved_1r: {item.resolved_1r}",
                f"wins_1r: {item.wins_1r}",
                f"losses_1r: {item.losses_1r}",
                f"flats_1r: {item.flats_1r}",
                f"expectancy_r_1r: {_format_decimal(item.expectancy_r_1r)}",
                f"resolved_1_5r: {item.resolved_1_5r}",
                f"wins_1_5r: {item.wins_1_5r}",
                f"losses_1_5r: {item.losses_1_5r}",
                f"flats_1_5r: {item.flats_1_5r}",
                f"expectancy_r_1_5r: {_format_decimal(item.expectancy_r_1_5r)}",
                f"resolved_2r: {item.resolved_2r}",
                f"wins_2r: {item.wins_2r}",
                f"losses_2r: {item.losses_2r}",
                f"flats_2r: {item.flats_2r}",
                f"expectancy_r_2r: {_format_decimal(item.expectancy_r_2r)}",
                f"failures_by_reason: {json.dumps(item.failures_by_reason, sort_keys=True)}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_setup_b_artifacts(
    diagnostics: Sequence[SetupBDiagnosticsSummary],
    observations: Sequence[SetupBObservation],
    *,
    text_path: str | Path,
    diagnostics_json_path: str | Path,
    observations_json_path: str | Path,
) -> None:
    """Write deterministic Setup B diagnostics and observations artifacts."""

    text_output = Path(text_path)
    diagnostics_output = Path(diagnostics_json_path)
    observations_output = Path(observations_json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_output.parent.mkdir(parents=True, exist_ok=True)
    observations_output.parent.mkdir(parents=True, exist_ok=True)

    text_output.write_text(
        format_setup_b_diagnostics_report(diagnostics),
        encoding="utf-8",
    )
    diagnostics_output.write_text(
        json.dumps(_json_safe([asdict(item) for item in diagnostics]), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    observations_output.write_text(
        json.dumps(_json_safe([asdict(item) for item in observations]), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def _summary_from_result(result: SetupBDetectionResult) -> SetupBDiagnosticsSummary:
    counters = result.counters
    return SetupBDiagnosticsSummary(
        symbol=result.symbol,
        direction=result.direction.value,
        candles_loaded=counters.candles_loaded,
        windows_checked=counters.windows_checked,
        pivots_detected=counters.pivots_detected,
        trend_detected=counters.trend_detected,
        pullback_candidates=counters.pullback_candidates,
        valid_pullbacks=counters.valid_pullbacks,
        pullback_invalidated_before_bos=counters.pullback_invalidated_before_bos,
        bos_candidates=counters.bos_candidates,
        bos_confirmed=counters.bos_confirmed,
        entry_observations=counters.entry_observations,
        resolved_1r=counters.resolved_1r,
        wins_1r=counters.wins_1r,
        losses_1r=counters.losses_1r,
        flats_1r=counters.flats_1r,
        resolved_1_5r=counters.resolved_1_5r,
        wins_1_5r=counters.wins_1_5r,
        losses_1_5r=counters.losses_1_5r,
        flats_1_5r=counters.flats_1_5r,
        resolved_2r=counters.resolved_2r,
        wins_2r=counters.wins_2r,
        losses_2r=counters.losses_2r,
        flats_2r=counters.flats_2r,
        expectancy_r_1r=_expectancy(result.observations, target_attr="outcome_1r", win_r=Decimal("1")),
        expectancy_r_1_5r=_expectancy(
            result.observations,
            target_attr="outcome_1_5r",
            win_r=Decimal("1.5"),
        ),
        expectancy_r_2r=_expectancy(result.observations, target_attr="outcome_2r", win_r=Decimal("2")),
        failures_by_reason=dict(sorted(result.failures_by_reason.items())),
    )


def _expectancy(
    observations: Sequence[SetupBObservation],
    *,
    target_attr: str,
    win_r: Decimal,
) -> Decimal | None:
    if not observations:
        return None
    values: list[Decimal] = []
    for observation in observations:
        outcome = getattr(observation, target_attr)
        if outcome == "win":
            values.append(win_r)
        elif outcome == "loss":
            values.append(Decimal("-1"))
        else:
            values.append(Decimal("0"))
    return sum(values) / Decimal(len(values))


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "None"
    return str(value)
