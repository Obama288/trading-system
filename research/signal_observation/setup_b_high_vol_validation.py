"""Stage 54-SQ-B5 out-of-time validation for high-volatility Setup B 1.5R hypothesis.

Scope: exploratory research only.
No profitability, paper-trading, live-trading, or readiness claim.
"""

from __future__ import annotations

import csv
import json
import random
import tempfile
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .bitget_public_downloader import download_bitget_history_candles
from .candles import Candle
from .csv_loader import load_ohlcv_csv
from .indicators import atr as compute_atr
from .setup_b import SetupBObservation, SignalDirection, detect_setup_b
from .setup_b_conditional_diagnostics import ATR_PERIOD
from .setup_b_random_baseline import BucketSpec, TARGETS, TARGET_R_VALUES


DISCOVERY_START = datetime(2025, 10, 17, 16, 0, 0, tzinfo=UTC)
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
PRODUCT_TYPE = "USDT-FUTURES"
VALIDATION_TARGET = "1_5r"
GATE_MIN_N = 20
DEFAULT_SEED = 5403
DEFAULT_ITERATIONS = 1000
TIMEOUT_BARS = 10
MAX_EXTENSION_PAGES = 20
EXTENSION_LIMIT = 200
_P67 = Decimal("0.667")
B5_PASS = "PASS"
B5_FAIL = "FAIL"


# ---------------------------------------------------------------------------
# CSV extension
# ---------------------------------------------------------------------------


def extend_4h_csvs_backward(
    data_dir: str | Path,
    *,
    discovery_start: datetime = DISCOVERY_START,
    symbols: tuple[str, ...] = SYMBOLS,
    product_type: str = PRODUCT_TYPE,
    max_pages: int = MAX_EXTENSION_PAGES,
    limit: int = EXTENSION_LIMIT,
) -> dict[str, object]:
    """Download historical candles before discovery_start and merge into existing CSVs."""

    base = Path(data_dir)
    end_time_ms = str(int(discovery_start.timestamp() * 1000) - 1)
    report: dict[str, object] = {}

    for symbol in symbols:
        csv_path = base / f"{symbol}_{product_type}_4H.csv"
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir) / f"{symbol}_ext.csv"
                download_bitget_history_candles(
                    symbol=symbol,
                    product_type=product_type,
                    granularity="4H",
                    output_csv=tmp_path,
                    limit=limit,
                    end_time=end_time_ms,
                    max_pages=max_pages,
                )
                new_candles = load_ohlcv_csv(tmp_path)

            existing_candles = load_ohlcv_csv(csv_path)
            merged = _merge_candles(existing_candles, new_candles)
            rows_added = len(merged) - len(existing_candles)
            new_first = merged[0].timestamp.isoformat() if merged else None
            _write_candles_csv(merged, csv_path)

            report[symbol] = {
                "status": "ok",
                "rows_added": rows_added,
                "new_first": new_first,
                "total_rows": len(merged),
            }
        except Exception as exc:
            report[symbol] = {"status": "error", "error": str(exc)}

    return report


# ---------------------------------------------------------------------------
# Window split
# ---------------------------------------------------------------------------


def split_candles_at_discovery(
    candles_by_symbol: dict[str, list[Candle]],
    discovery_start: datetime = DISCOVERY_START,
) -> tuple[dict[str, list[Candle]], dict[str, list[Candle]]]:
    """Split candles into validation (ts < discovery_start) and discovery partitions."""

    val: dict[str, list[Candle]] = {}
    disc: dict[str, list[Candle]] = {}
    for sym, candles in candles_by_symbol.items():
        val[sym] = [c for c in candles if c.timestamp < discovery_start]
        disc[sym] = [c for c in candles if c.timestamp >= discovery_start]
    return val, disc


# ---------------------------------------------------------------------------
# Observation detection
# ---------------------------------------------------------------------------


def run_validation_observations(
    full_candles_by_symbol: dict[str, list[Candle]],
    discovery_start: datetime = DISCOVERY_START,
) -> list[dict[str, object]]:
    """Run frozen Setup B detector; return observations with signal_time before discovery."""

    result: list[dict[str, object]] = []
    for symbol, candles in full_candles_by_symbol.items():
        for direction in (SignalDirection.LONG, SignalDirection.SHORT):
            for obs in detect_setup_b(candles, symbol=symbol, direction=direction):
                if obs.signal_time < discovery_start:
                    result.append(_obs_to_dict(obs, symbol))
    return result


# ---------------------------------------------------------------------------
# High-vol tagging
# ---------------------------------------------------------------------------


def tag_high_vol_validation(
    observations: list[dict[str, object]],
    full_candles_by_symbol: dict[str, list[Candle]],
    discovery_start: datetime = DISCOVERY_START,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Tag observations with high/not_high using validation-calibrated ATR p67 threshold."""

    atr_by_sym: dict[str, list[Decimal | None]] = {
        sym: compute_atr(candles, ATR_PERIOD)
        for sym, candles in full_candles_by_symbol.items()
    }
    val_count_by_sym: dict[str, int] = {
        sym: sum(1 for c in candles if c.timestamp < discovery_start)
        for sym, candles in full_candles_by_symbol.items()
    }

    p67_by_sym: dict[str, Decimal] = {}
    threshold_info: dict[str, object] = {}
    for sym, series in atr_by_sym.items():
        val_count = val_count_by_sym[sym]
        valid_vals = sorted(v for v in series[:val_count] if v is not None)
        if len(valid_vals) < 3:
            threshold_info[sym] = {
                "p67_threshold": None,
                "n_validation_atr": len(valid_vals),
            }
            continue
        p67 = _percentile_value(valid_vals, _P67)
        p67_by_sym[sym] = p67
        threshold_info[sym] = {
            "p67_threshold": str(p67),
            "n_validation_atr": len(valid_vals),
        }

    tagged: list[dict[str, object]] = []
    for obs in observations:
        sym = str(obs["symbol"])
        atr_val = Decimal(str(obs["atr_at_entry"]))
        p67 = p67_by_sym.get(sym)
        vol_tag = "high" if (p67 is not None and atr_val >= p67) else "not_high"
        result = dict(obs)
        result["tag_volatility_regime"] = vol_tag
        tagged.append(result)

    return tagged, threshold_info


# ---------------------------------------------------------------------------
# Eligible index construction
# ---------------------------------------------------------------------------


def build_vol_high_eligible_indices(
    full_candles_by_symbol: dict[str, list[Candle]],
    val_candles_by_symbol: dict[str, list[Candle]],
    timeout_bars: int = TIMEOUT_BARS,
) -> dict[str, list[int]]:
    """Return per-symbol indices in the validation window with high ATR and full lookahead."""

    eligible: dict[str, list[int]] = {}
    for sym, full_candles in full_candles_by_symbol.items():
        val_count = len(val_candles_by_symbol.get(sym, []))
        series = compute_atr(full_candles, ATR_PERIOD)

        valid_vals = sorted(v for v in series[:val_count] if v is not None)
        if len(valid_vals) < 3:
            eligible[sym] = []
            continue

        p67 = _percentile_value(valid_vals, _P67)
        max_idx = len(full_candles) - timeout_bars - 1

        eligible[sym] = [
            i for i, val in enumerate(series)
            if i < val_count and val is not None and val >= p67 and i <= max_idx
        ]
    return eligible


# ---------------------------------------------------------------------------
# Conditional random baseline
# ---------------------------------------------------------------------------


def run_validation_conditional_random(
    *,
    high_vol_observations: list[dict[str, object]],
    eligible_indices: dict[str, list[int]],
    full_candles_by_symbol: dict[str, list[Candle]],
    seed: int = DEFAULT_SEED,
    iterations: int = DEFAULT_ITERATIONS,
    timeout_bars: int = TIMEOUT_BARS,
) -> dict[str, object]:
    """Run conditional random baseline over validation-eligible candles."""

    if not high_vol_observations:
        return {}

    bucket_specs = _build_bucket_specs(high_vol_observations)
    if not bucket_specs:
        return {}

    for spec in bucket_specs:
        if not eligible_indices.get(spec.symbol):
            raise ValueError(f"no eligible candles for {spec.symbol}")

    rng = random.Random(seed)
    iteration_metrics: list[dict[str, dict[str, object]]] = []
    for _ in range(iterations):
        entries = _sample_conditional_iteration(
            bucket_specs=bucket_specs,
            eligible_indices=eligible_indices,
            candles_by_symbol=full_candles_by_symbol,
            rng=rng,
            timeout_bars=timeout_bars,
        )
        iteration_metrics.append(_metrics_for_iteration(entries))

    return _summarize_iteration_metrics(iteration_metrics)


# ---------------------------------------------------------------------------
# Metrics and gate
# ---------------------------------------------------------------------------


def compute_validation_metrics(
    observations: Sequence[dict[str, object]],
) -> dict[str, object]:
    """Compute per-target metrics for actual validation observations."""

    return {target: _detailed_bucket_metrics(observations, target) for target in TARGETS}


def compare_actual_to_conditional_random(
    actual_metrics: dict[str, object],
    random_summary: dict[str, object],
) -> dict[str, object]:
    """Compare actual validation metrics against conditional random distribution."""

    output: dict[str, object] = {}
    for target in TARGETS:
        actual = actual_metrics.get(target, {})
        random_t = random_summary.get(target, {}) if random_summary else {}

        raw_exp = actual.get("expectancy_r")
        actual_exp = Decimal(str(raw_exp)) if raw_exp is not None else Decimal("0")
        raw_flat = actual.get("flat_rate")
        actual_flat = Decimal(str(raw_flat)) if raw_flat is not None else Decimal("0")
        raw_mfe = actual.get("avg_mfe_r")
        actual_mfe = Decimal(str(raw_mfe)) if raw_mfe is not None else Decimal("0")

        exp_dist = random_t.get("expectancy_r", {}) if random_t else {}
        flat_dist = random_t.get("flat_rate", {}) if random_t else {}
        mfe_dist = random_t.get("avg_mfe_r", {}) if random_t else {}

        median_exp = _optional_decimal(exp_dist.get("median") if exp_dist else None)
        p75_exp = _optional_decimal(exp_dist.get("p75") if exp_dist else None)
        p90_exp = _optional_decimal(exp_dist.get("p90") if exp_dist else None)
        median_flat = _optional_decimal(flat_dist.get("median") if flat_dist else None)
        median_mfe = _optional_decimal(mfe_dist.get("median") if mfe_dist else None)

        margin_over_p75 = (actual_exp - p75_exp) if p75_exp is not None else None
        if margin_over_p75 is not None:
            classification: str | None = (
                "potentially_meaningful"
                if margin_over_p75 >= Decimal("0.05")
                else "weak"
            )
        else:
            classification = None

        output[target] = {
            "beats_conditional_random_median_expectancy": (
                median_exp is not None and actual_exp > median_exp
            ),
            "beats_conditional_random_p75_expectancy": (
                p75_exp is not None and actual_exp > p75_exp
            ),
            "beats_conditional_random_p90_expectancy": (
                p90_exp is not None and actual_exp > p90_exp
            ),
            "beats_conditional_random_median_mfe": (
                median_mfe is not None and actual_mfe > median_mfe
            ),
            "actual_flat_rate_le_random_median": (
                median_flat is not None and actual_flat <= median_flat
            ),
            "meaningful_margin_over_p75": str(margin_over_p75) if margin_over_p75 is not None else None,
            "meaningful_margin_classification": classification,
        }
    return output


def evaluate_b5_gate(
    actual_metrics: dict[str, object],
    random_summary: dict[str, object],
    n_high_vol: int,
) -> dict[str, object]:
    """Evaluate the 4-condition B5 gate for the validation target."""

    target_m = actual_metrics.get(VALIDATION_TARGET, {})
    random_t = random_summary.get(VALIDATION_TARGET, {}) if random_summary else {}

    exp_dist = random_t.get("expectancy_r", {}) if random_t else {}
    flat_dist = random_t.get("flat_rate", {}) if random_t else {}

    raw_exp = target_m.get("expectancy_r")
    actual_exp = Decimal(str(raw_exp)) if raw_exp is not None else Decimal("0")
    raw_flat = target_m.get("flat_rate")
    actual_flat = Decimal(str(raw_flat)) if raw_flat is not None else Decimal("0")

    p75_exp = _optional_decimal(exp_dist.get("p75") if exp_dist else None)
    median_flat = _optional_decimal(flat_dist.get("median") if flat_dist else None)

    c1 = n_high_vol >= GATE_MIN_N
    c2 = p75_exp is not None and actual_exp > p75_exp
    c3 = actual_exp > Decimal("0")
    c4 = median_flat is not None and actual_flat <= median_flat

    gate_result = B5_PASS if (c1 and c2 and c3 and c4) else B5_FAIL

    return {
        "gate_result": gate_result,
        "target": VALIDATION_TARGET,
        "conditions": {
            "c1_n_high_vol_sufficient": {
                "passes": c1,
                "n_high_vol": n_high_vol,
                "required": GATE_MIN_N,
            },
            "c2_expectancy_beats_p75_random": {
                "passes": c2,
                "actual_expectancy_r": str(actual_exp),
                "p75_random_expectancy_r": str(p75_exp) if p75_exp is not None else None,
            },
            "c3_expectancy_positive": {
                "passes": c3,
                "actual_expectancy_r": str(actual_exp),
            },
            "c4_flat_rate_le_random_median": {
                "passes": c4,
                "actual_flat_rate": str(actual_flat),
                "median_random_flat_rate": str(median_flat) if median_flat is not None else None,
            },
        },
    }


# ---------------------------------------------------------------------------
# Report assembly and output
# ---------------------------------------------------------------------------


def build_b5_report(
    *,
    csv_extension: dict[str, object],
    window_info: dict[str, object],
    all_val_observations: list[dict[str, object]],
    high_vol_observations: list[dict[str, object]],
    atr_threshold_info: dict[str, object],
    eligible_candle_counts: dict[str, int],
    actual_metrics: dict[str, object],
    random_summary: dict[str, object],
    comparison: dict[str, object],
    b5_gate: dict[str, object],
    seed: int = DEFAULT_SEED,
    iterations: int = DEFAULT_ITERATIONS,
    timeout_bars: int = TIMEOUT_BARS,
) -> dict[str, object]:
    """Assemble the full B5 validation report."""

    return _json_safe({
        "schema": "setup_b_high_vol_validation_v1",
        "seed": seed,
        "iterations": iterations,
        "timeout_bars": timeout_bars,
        "discovery_start": DISCOVERY_START.isoformat(),
        "validation_target": VALIDATION_TARGET,
        "gate_min_n": GATE_MIN_N,
        "csv_extension": csv_extension,
        "window_info": window_info,
        "n_all_validation_observations": len(all_val_observations),
        "n_high_vol_observations": len(high_vol_observations),
        "atr_threshold_info": atr_threshold_info,
        "eligible_candle_counts": eligible_candle_counts,
        "actual_metrics": actual_metrics,
        "random_summary": random_summary,
        "comparison": comparison,
        "b5_gate": b5_gate,
    })


def write_b5_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write B5 validation artifacts to disk."""

    text_out = Path(text_path)
    json_out = Path(json_path)
    text_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    text_out.write_text(format_b5_report(report), encoding="utf-8")
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_b5_report(report: dict[str, object]) -> str:
    """Format a stable text report for the B5 validation."""

    lines = [
        "Setup B Stage B5 high-volatility out-of-time validation",
        "",
        "Scope: exploratory research only.",
        "No profitability, paper-trading, live-trading, or readiness claim.",
        "",
        f"discovery_start: {report['discovery_start']}",
        f"validation_target: {report['validation_target']}",
        f"gate_min_n: {report['gate_min_n']}",
        f"seed: {report['seed']}",
        f"iterations: {report['iterations']}",
        f"timeout_bars: {report['timeout_bars']}",
        "",
        "CSV extension",
    ]
    for sym, ext_info in sorted(report["csv_extension"].items()):  # type: ignore[union-attr]
        if isinstance(ext_info, dict):
            lines.append(
                f"  {sym}: status={ext_info.get('status')}"
                f" rows_added={ext_info.get('rows_added')}"
                f" first={ext_info.get('new_first')}"
                f" total={ext_info.get('total_rows')}"
            )
        else:
            lines.append(f"  {sym}: {ext_info}")

    lines.extend(["", "Validation window"])
    for sym, info in sorted(report["window_info"].items()):  # type: ignore[union-attr]
        if isinstance(info, dict):
            lines.append(
                f"  {sym}: val_n={info.get('val_candle_count')}"
                f" disc_n={info.get('disc_candle_count')}"
                f" total={info.get('total_candle_count')}"
            )

    lines.extend([
        "",
        f"All validation observations: {report['n_all_validation_observations']}",
        f"High-vol validation observations: {report['n_high_vol_observations']}",
        "",
        "ATR p67 thresholds (validation-calibrated)",
    ])
    for sym, info in sorted(report["atr_threshold_info"].items()):  # type: ignore[union-attr]
        if isinstance(info, dict):
            lines.append(
                f"  {sym}: p67={info.get('p67_threshold')}"
                f" n_atr={info.get('n_validation_atr')}"
            )

    lines.extend(["", "Eligible candle counts (validation window, high-ATR)"])
    for sym, count in sorted(report["eligible_candle_counts"].items()):  # type: ignore[union-attr]
        lines.append(f"  {sym}: {count}")

    gate = report["b5_gate"]  # type: ignore[index]
    gate_result = gate.get("gate_result", "?")
    lines.extend([
        "",
        f"B5 Gate evaluation (target: {gate.get('target', VALIDATION_TARGET)})",
        f"  gate_result: {gate_result}",
    ])
    conditions = gate.get("conditions", {})
    if conditions:
        c1 = conditions.get("c1_n_high_vol_sufficient", {})
        c2 = conditions.get("c2_expectancy_beats_p75_random", {})
        c3 = conditions.get("c3_expectancy_positive", {})
        c4 = conditions.get("c4_flat_rate_le_random_median", {})
        lines.extend([
            f"  c1_n_high_vol_sufficient: {c1.get('passes')}"
            f" (n={c1.get('n_high_vol')}, required>={c1.get('required')})",
            f"  c2_expectancy_beats_p75_random: {c2.get('passes')}"
            f" (actual={c2.get('actual_expectancy_r')}, p75={c2.get('p75_random_expectancy_r')})",
            f"  c3_expectancy_positive: {c3.get('passes')}"
            f" (actual={c3.get('actual_expectancy_r')})",
            f"  c4_flat_rate_le_random_median: {c4.get('passes')}"
            f" (actual={c4.get('actual_flat_rate')}, median={c4.get('median_random_flat_rate')})",
        ])

    lines.extend(["", "Actual vs conditional random (high-vol validation)"])
    actual = report.get("actual_metrics", {})
    random_s = report.get("random_summary", {})
    comparison = report.get("comparison", {})
    for target in TARGETS:
        act = actual.get(target, {}) if actual else {}  # type: ignore[union-attr]
        rand = random_s.get(target, {}) if random_s else {}  # type: ignore[union-attr]
        cmp = comparison.get(target, {}) if comparison else {}  # type: ignore[union-attr]
        exp_dist = rand.get("expectancy_r", {}) if rand else {}
        flat_dist = rand.get("flat_rate", {}) if rand else {}
        lines.extend([
            f"  target: {target}",
            f"    n: {act.get('n')}",
            f"    actual_expectancy_r: {act.get('expectancy_r')}",
            f"    actual_flat_rate: {act.get('flat_rate')}",
            f"    random_median_expectancy_r: {exp_dist.get('median') if exp_dist else None}",
            f"    random_p75_expectancy_r: {exp_dist.get('p75') if exp_dist else None}",
            f"    random_median_flat_rate: {flat_dist.get('median') if flat_dist else None}",
            f"    beats_p75_expectancy: {cmp.get('beats_conditional_random_p75_expectancy')}",
            f"    meaningful_margin_over_p75: {cmp.get('meaningful_margin_over_p75')}",
            f"    meaningful_margin_classification: {cmp.get('meaningful_margin_classification')}",
        ])

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Private helpers — observation conversion
# ---------------------------------------------------------------------------


def _obs_to_dict(obs: SetupBObservation, symbol: str) -> dict[str, object]:
    return {
        "symbol": symbol,
        "signal_direction": obs.signal_direction.value,
        "signal_time": obs.signal_time.isoformat(),
        "entry_time": obs.entry_time.isoformat(),
        "entry_price": str(obs.entry_price),
        "stop": str(obs.stop),
        "atr_at_entry": str(obs.atr_at_entry),
        "session_label": obs.session_label,
        "signal_hour_utc": obs.signal_hour_utc,
        "outcome_1r": obs.outcome_1r,
        "outcome_1_5r": obs.outcome_1_5r,
        "outcome_2r": obs.outcome_2r,
        "mae_1r": str(obs.mae_1r) if obs.mae_1r is not None else None,
        "mfe_1r": str(obs.mfe_1r) if obs.mfe_1r is not None else None,
        "bars_to_resolution_1r": obs.bars_to_resolution_1r,
        "mae_1_5r": str(obs.mae_1_5r) if obs.mae_1_5r is not None else None,
        "mfe_1_5r": str(obs.mfe_1_5r) if obs.mfe_1_5r is not None else None,
        "bars_to_resolution_1_5r": obs.bars_to_resolution_1_5r,
        "mae_2r": str(obs.mae_2r) if obs.mae_2r is not None else None,
        "mfe_2r": str(obs.mfe_2r) if obs.mfe_2r is not None else None,
        "bars_to_resolution_2r": obs.bars_to_resolution_2r,
    }


# ---------------------------------------------------------------------------
# Private helpers — CSV merge/write
# ---------------------------------------------------------------------------


def _merge_candles(existing: list[Candle], new: list[Candle]) -> list[Candle]:
    by_ts: dict = {c.timestamp: c for c in existing}
    for c in new:
        by_ts[c.timestamp] = c
    return sorted(by_ts.values(), key=lambda c: c.timestamp)


def _write_candles_csv(candles: list[Candle], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(("timestamp", "open", "high", "low", "close", "volume"))
        for c in candles:
            writer.writerow((
                c.timestamp.isoformat(),
                str(c.open),
                str(c.high),
                str(c.low),
                str(c.close),
                str(c.volume),
            ))


# ---------------------------------------------------------------------------
# Private helpers — sampling
# ---------------------------------------------------------------------------


def _build_bucket_specs(observations: Sequence[dict[str, object]]) -> list[BucketSpec]:
    grouped: dict[tuple[str, str], list[Decimal]] = defaultdict(list)
    for obs in observations:
        symbol = str(obs["symbol"])
        direction = str(obs["signal_direction"])
        entry = Decimal(str(obs["entry_price"]))
        stop = Decimal(str(obs["stop"]))
        risk = abs(entry - stop)
        if risk <= Decimal("0"):
            raise ValueError(f"non-positive risk: {symbol} {direction}")
        grouped[(symbol, direction)].append(risk)
    return [
        BucketSpec(
            symbol=symbol,
            direction=direction,
            count=len(risks),
            risk_distances=tuple(risks),
        )
        for (symbol, direction), risks in sorted(grouped.items())
    ]


def _sample_conditional_iteration(
    *,
    bucket_specs: Sequence[BucketSpec],
    eligible_indices: dict[str, list[int]],
    candles_by_symbol: dict[str, Sequence[Candle]],
    rng: random.Random,
    timeout_bars: int,
) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for spec in bucket_specs:
        candles = candles_by_symbol[spec.symbol]
        eligible = eligible_indices[spec.symbol]
        for _ in range(spec.count):
            entry_index = rng.choice(eligible)
            risk = rng.choice(spec.risk_distances)
            entries.append(
                _evaluate_entry(
                    candles=candles,
                    entry_index=entry_index,
                    direction=spec.direction,
                    risk_distance=risk,
                    timeout_bars=timeout_bars,
                )
            )
    return entries


def _evaluate_entry(
    *,
    candles: Sequence[Candle],
    entry_index: int,
    direction: str,
    risk_distance: Decimal,
    timeout_bars: int,
) -> dict[str, object]:
    entry = candles[entry_index].close
    if direction == "long":
        stop = entry - risk_distance
    elif direction == "short":
        stop = entry + risk_distance
    else:
        raise ValueError(f"unsupported direction: {direction}")

    window = candles[entry_index + 1 : entry_index + 1 + timeout_bars]
    result: dict[str, object] = {
        "direction": direction,
        "entry_price": entry,
        "stop": stop,
        "risk_distance": risk_distance,
    }
    for target, target_r in TARGET_R_VALUES.items():
        target_price = _target_price(entry, risk_distance, target_r, direction)
        outcome, mae_r, mfe_r, bars = _resolve_outcome(
            window=window,
            entry=entry,
            stop=stop,
            target=target_price,
            direction=direction,
            risk_distance=risk_distance,
        )
        result[f"outcome_{target}"] = outcome
        result[f"mae_{target}"] = mae_r
        result[f"mfe_{target}"] = mfe_r
        result[f"bars_to_resolution_{target}"] = bars
    return result


def _target_price(
    entry: Decimal, risk_distance: Decimal, target_r: Decimal, direction: str
) -> Decimal:
    if direction == "long":
        return entry + (risk_distance * target_r)
    return entry - (risk_distance * target_r)


def _resolve_outcome(
    *,
    window: Sequence[Candle],
    entry: Decimal,
    stop: Decimal,
    target: Decimal,
    direction: str,
    risk_distance: Decimal,
) -> tuple[str, Decimal, Decimal, int]:
    if not window:
        return "flat", Decimal("0"), Decimal("0"), 0

    for offset, candle in enumerate(window, start=1):
        resolution_window = window[:offset]
        if direction == "long":
            if candle.low <= stop:
                mae_r, mfe_r = _excursions(
                    resolution_window, entry=entry, risk_distance=risk_distance, direction=direction
                )
                return "loss", mae_r, mfe_r, offset
            if candle.high >= target:
                mae_r, mfe_r = _excursions(
                    resolution_window, entry=entry, risk_distance=risk_distance, direction=direction
                )
                return "win", mae_r, mfe_r, offset
        else:
            if candle.high >= stop:
                mae_r, mfe_r = _excursions(
                    resolution_window, entry=entry, risk_distance=risk_distance, direction=direction
                )
                return "loss", mae_r, mfe_r, offset
            if candle.low <= target:
                mae_r, mfe_r = _excursions(
                    resolution_window, entry=entry, risk_distance=risk_distance, direction=direction
                )
                return "win", mae_r, mfe_r, offset

    mae_r, mfe_r = _excursions(window, entry=entry, risk_distance=risk_distance, direction=direction)
    return "flat", mae_r, mfe_r, len(window)


def _excursions(
    window: Sequence[Candle],
    *,
    entry: Decimal,
    risk_distance: Decimal,
    direction: str,
) -> tuple[Decimal, Decimal]:
    if direction == "long":
        mfe_r = max((c.high - entry) / risk_distance for c in window)
        mae_r = min((c.low - entry) / risk_distance for c in window)
    else:
        mfe_r = max((entry - c.low) / risk_distance for c in window)
        mae_r = min((entry - c.high) / risk_distance for c in window)
    return mae_r, mfe_r


# ---------------------------------------------------------------------------
# Private helpers — metrics
# ---------------------------------------------------------------------------


def _metrics_for_iteration(
    entries: Sequence[dict[str, object]],
) -> dict[str, dict[str, object]]:
    return {target: _target_metrics(entries, target) for target in TARGETS}


def _target_metrics(
    entries: Sequence[dict[str, object]], target: str
) -> dict[str, object]:
    target_r = TARGET_R_VALUES[target]
    outcomes = [str(e[f"outcome_{target}"]) for e in entries]
    r_values = [_outcome_r(o, target_r) for o in outcomes]
    wins = outcomes.count("win")
    losses = outcomes.count("loss")
    flats = outcomes.count("flat")
    mae_vals = [Decimal(str(e[f"mae_{target}"])) for e in entries]
    mfe_vals = [Decimal(str(e[f"mfe_{target}"])) for e in entries]
    n = len(entries)
    return {
        "observations": n,
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate": _rate(wins, n),
        "flat_rate": _rate(flats, n),
        "expectancy_r": _average(r_values),
        "avg_mae_r": _average(mae_vals),
        "avg_mfe_r": _average(mfe_vals),
    }


def _detailed_bucket_metrics(
    observations: Sequence[dict[str, object]], target: str
) -> dict[str, object]:
    target_r = TARGET_R_VALUES[target]
    outcomes = [str(obs[f"outcome_{target}"]) for obs in observations]
    wins = outcomes.count("win")
    losses = outcomes.count("loss")
    flats = outcomes.count("flat")
    n = len(observations)
    r_values = [_outcome_r(o, target_r) for o in outcomes]
    mae_vals = [
        Decimal(str(obs[f"mae_{target}"]))
        for obs in observations
        if obs.get(f"mae_{target}") is not None
    ]
    mfe_vals = [
        Decimal(str(obs[f"mfe_{target}"]))
        for obs in observations
        if obs.get(f"mfe_{target}") is not None
    ]
    bars = [
        Decimal(str(obs[f"bars_to_resolution_{target}"]))
        for obs in observations
        if obs.get(f"bars_to_resolution_{target}") is not None
    ]
    wins_r = sum((v for v in r_values if v > Decimal("0")), Decimal("0"))
    losses_abs = abs(sum((v for v in r_values if v < Decimal("0")), Decimal("0")))
    profit_factor: Decimal | None = (
        wins_r / losses_abs if wins_r > Decimal("0") and losses_abs > Decimal("0") else None
    )
    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate": _rate(wins, n),
        "flat_rate": _rate(flats, n),
        "expectancy_r": _average(r_values),
        "profit_factor": profit_factor,
        "avg_mae_r": _average(mae_vals),
        "avg_mfe_r": _average(mfe_vals),
        "median_mae_r": _median(mae_vals),
        "median_mfe_r": _median(mfe_vals),
        "avg_bars_to_resolution": _average(bars),
        "median_bars_to_resolution": _median(bars),
    }


def _summarize_iteration_metrics(
    iteration_metrics: Sequence[dict[str, dict[str, object]]],
) -> dict[str, object]:
    output: dict[str, object] = {}
    for target in TARGETS:
        output[target] = {
            metric: _distribution_summary(
                [
                    _optional_decimal(iteration[target][metric])
                    for iteration in iteration_metrics
                    if _optional_decimal(iteration[target][metric]) is not None
                ]
            )
            for metric in ("expectancy_r", "win_rate", "flat_rate", "avg_mae_r", "avg_mfe_r")
        }
    return output


# ---------------------------------------------------------------------------
# Private helpers — math
# ---------------------------------------------------------------------------


def _percentile_value(sorted_vals: list[Decimal], percentile: Decimal) -> Decimal:
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    rank = percentile * Decimal(len(sorted_vals) - 1)
    lower = int(rank.to_integral_value(rounding="ROUND_FLOOR"))
    upper = int(rank.to_integral_value(rounding="ROUND_CEILING"))
    if lower == upper:
        return sorted_vals[lower]
    frac = rank - Decimal(lower)
    return sorted_vals[lower] + (sorted_vals[upper] - sorted_vals[lower]) * frac


def _distribution_summary(values: Sequence[Decimal]) -> dict[str, Decimal | None]:
    if not values:
        return {
            "mean": None, "median": None, "p10": None, "p25": None,
            "p75": None, "p90": None, "min": None, "max": None,
        }
    sv = sorted(values)
    return {
        "mean": _average(sv),
        "median": _median(sv),
        "p10": _percentile_value(sv, Decimal("0.10")),
        "p25": _percentile_value(sv, Decimal("0.25")),
        "p75": _percentile_value(sv, Decimal("0.75")),
        "p90": _percentile_value(sv, Decimal("0.90")),
        "min": sv[0],
        "max": sv[-1],
    }


def _average(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    return sum(values, Decimal("0")) / Decimal(len(values))


def _median(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    sv = sorted(values)
    mid = len(sv) // 2
    if len(sv) % 2:
        return sv[mid]
    return (sv[mid - 1] + sv[mid]) / Decimal("2")


def _rate(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return Decimal(count) / Decimal(total)


def _outcome_r(outcome: str, target_r: Decimal) -> Decimal:
    if outcome == "win":
        return target_r
    if outcome == "loss":
        return Decimal("-1")
    return Decimal("0")


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value
