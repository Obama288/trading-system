from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = ROOT / "research" / "signal_observation" / "output" / "funding_normalization"
FUNDING_RAW = (
    ROOT
    / "research"
    / "signal_observation"
    / "setup_d_d1_funding_acquisition"
    / "d1_funding_raw.json"
)
OHLCV_PATHS = {
    "BTCUSDT": ROOT
    / "research"
    / "signal_observation"
    / "data"
    / "binance"
    / "expanded"
    / "BTCUSDT_USDT-FUTURES_4H.csv",
    "ETHUSDT": ROOT
    / "research"
    / "signal_observation"
    / "data"
    / "binance"
    / "expanded"
    / "ETHUSDT_USDT-FUTURES_4H.csv",
}
REPORT_TXT = OUT_DIR / "funding_normalization_btc_eth_discovery_screening_report.txt"
REPORT_JSON = OUT_DIR / "funding_normalization_btc_eth_discovery_screening_report.json"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
DISCOVERY_ROWS = 1502
TOTAL_EXPECTED_ROWS = 2147
HELD_OUT_ROWS = TOTAL_EXPECTED_ROWS - DISCOVERY_ROWS
WINDOWS = {"W1": 1, "W3": 3, "W8": 8}
EIGHT_H_MS = 8 * 60 * 60 * 1000
FOUR_H = timedelta(hours=4)
MAGNITUDE_FLOOR_BPS = 9.0


class ScreeningBlocked(RuntimeError):
    pass


def require_file(path: Path) -> None:
    if not path.exists():
        raise ScreeningBlocked(f"missing expected file: {path}")


def utc_from_ms(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_funding_time(ms: int) -> datetime:
    rounded = round(ms / EIGHT_H_MS) * EIGHT_H_MS
    if abs(rounded - ms) > 60_000:
        raise ScreeningBlocked(f"fundingTime not within 60s of an 8H boundary: {ms}")
    return utc_from_ms(int(rounded)).replace(microsecond=0)


def extract_first_symbol_rows(symbol: str, limit: int) -> list[dict]:
    pattern = f'"{symbol}":['
    decoder = json.JSONDecoder()
    rows: list[dict] = []
    buffer = ""
    found = False

    with FUNDING_RAW.open("r", encoding="utf-8") as handle:
        while not found:
            chunk = handle.read(8192)
            if not chunk:
                raise ScreeningBlocked(f"symbol section not found in funding raw: {symbol}")
            buffer += chunk
            idx = buffer.find(pattern)
            if idx >= 0:
                buffer = buffer[idx + len(pattern) :]
                found = True
            elif len(buffer) > len(pattern):
                buffer = buffer[-len(pattern) :]

        while len(rows) < limit:
            buffer = buffer.lstrip()
            if not buffer:
                chunk = handle.read(8192)
                if not chunk:
                    raise ScreeningBlocked(f"unexpected EOF while reading {symbol}")
                buffer += chunk
                continue
            if buffer[0] == ",":
                buffer = buffer[1:]
                continue
            if buffer[0] == "]":
                raise ScreeningBlocked(f"{symbol} has fewer than {limit} rows")
            try:
                obj, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                chunk = handle.read(8192)
                if not chunk:
                    raise
                buffer += chunk
                continue
            if obj.get("symbol") != symbol:
                raise ScreeningBlocked(f"unexpected symbol in {symbol} section: {obj.get('symbol')}")
            rows.append(obj)
            buffer = buffer[end:]

    return rows


def load_funding(symbol: str) -> list[dict]:
    raw_rows = extract_first_symbol_rows(symbol, DISCOVERY_ROWS)
    rows = []
    previous = None
    for index, raw in enumerate(raw_rows, start=1):
        if set(raw.keys()) < {"symbol", "fundingTime", "fundingRate"}:
            raise ScreeningBlocked(f"funding schema mismatch for {symbol} row {index}")
        funding_time = canonical_funding_time(int(raw["fundingTime"]))
        if previous is not None and funding_time <= previous:
            raise ScreeningBlocked(f"fundingTime not monotonic for {symbol} row {index}")
        previous = funding_time
        rows.append(
            {
                "row": index,
                "symbol": symbol,
                "funding_time": funding_time,
                "funding_rate": float(raw["fundingRate"]),
            }
        )
    return rows


def percentile_nearest_rank(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil((pct / 100.0) * len(ordered)) - 1)
    return ordered[index]


def load_ohlcv_context(symbol: str, required_timestamps: set[datetime]) -> tuple[dict[datetime, float], dict]:
    path = OHLCV_PATHS[symbol]
    require_file(path)
    if not required_timestamps:
        return {}, {"rows_loaded": 0, "first_loaded": None, "last_loaded": None}

    max_required = max(required_timestamps)
    min_required = min(required_timestamps)
    context: dict[datetime, float] = {}
    rows_loaded = 0
    first_loaded = None
    last_loaded = None

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ["timestamp", "open", "high", "low", "close", "volume"]
        if reader.fieldnames != expected:
            raise ScreeningBlocked(f"OHLCV schema mismatch for {symbol}: {reader.fieldnames}")
        for row in reader:
            ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).astimezone(timezone.utc)
            if ts > max_required:
                break
            if ts in required_timestamps:
                context[ts] = float(row["close"])
                rows_loaded += 1
                first_loaded = first_loaded or ts
                last_loaded = ts

    missing = sorted(required_timestamps - set(context))
    return context, {
        "rows_loaded": rows_loaded,
        "first_loaded": iso(first_loaded) if first_loaded else None,
        "last_loaded": iso(last_loaded) if last_loaded else None,
        "min_required": iso(min_required),
        "max_required": iso(max_required),
        "missing_count": len(missing),
        "missing_examples": [iso(x) for x in missing[:5]],
    }


def assign_funding_state(rate: float, thresholds: dict[str, float]) -> str:
    if rate >= thresholds["p80"]:
        return "HIGH"
    if rate <= thresholds["p20"]:
        return "LOW"
    if thresholds["p30"] <= rate <= thresholds["p70"]:
        return "NEUTRAL"
    if thresholds["p70"] < rate < thresholds["p80"]:
        return "TRANSITION_HIGH"
    if thresholds["p20"] < rate < thresholds["p30"]:
        return "TRANSITION_LOW"
    return "EXCLUDED_OTHER"


def p95_expected(values: list[float], branch: str) -> float:
    if branch == "HIGH":
        return percentile_nearest_rank(values, 5)
    return percentile_nearest_rank(values, 95)


def expected_direction_pass(value: float, branch: str) -> bool:
    return value < 0 if branch == "HIGH" else value > 0


def separation_pass(active_median: float, baseline_median: float, branch: str) -> bool:
    return active_median < baseline_median if branch == "HIGH" else active_median > baseline_median


def run_symbol(symbol: str) -> dict:
    funding = load_funding(symbol)
    if len(funding) != DISCOVERY_ROWS:
        raise ScreeningBlocked(f"{symbol} discovery rows loaded != {DISCOVERY_ROWS}")

    rates = [row["funding_rate"] for row in funding]
    thresholds = {
        f"p{pct}": percentile_nearest_rank(rates, pct)
        for pct in (20, 30, 70, 80)
    }

    required_ohlcv_times = set()
    for row in funding:
        aligned_open = row["funding_time"] - FOUR_H
        if row["row"] != 1:
            required_ohlcv_times.add(aligned_open)
        if row["row"] > 20:
            prior_row = funding[row["row"] - 21]
            if prior_row["row"] != 1:
                required_ohlcv_times.add(prior_row["funding_time"] - FOUR_H)

    ohlcv_context, ohlcv_summary = load_ohlcv_context(symbol, required_ohlcv_times)
    if ohlcv_summary["missing_count"]:
        raise ScreeningBlocked(f"{symbol} OHLCV t-4H alignment missing: {ohlcv_summary['missing_examples']}")

    flatness: list[bool | None] = []
    for i, row in enumerate(funding):
        aligned_open = row["funding_time"] - FOUR_H
        current_close = ohlcv_context.get(aligned_open)
        row["ohlcv_open_time"] = aligned_open
        row["ohlcv_aligned"] = current_close is not None
        row["close_context"] = current_close
        if i < 20 or current_close is None:
            flatness.append(None)
            continue
        prior_close = funding[i - 20].get("close_context")
        if prior_close is None:
            flatness.append(None)
            continue
        flatness.append(abs(current_close - prior_close) / prior_close < 0.05)

    for i, row in enumerate(funding):
        row["funding_state"] = assign_funding_state(row["funding_rate"], thresholds)
        if i < 20 or flatness[i] is None:
            row["regime"] = "UNDEFINED"
        elif flatness[i] and i >= 22 and flatness[i - 1] and flatness[i - 2]:
            row["regime"] = "SIDEWAYS"
        else:
            row["regime"] = "NON_SIDEWAYS"

        fs = row["funding_state"]
        regime = row["regime"]
        if fs in {"TRANSITION_HIGH", "TRANSITION_LOW"}:
            row["combined_state"] = "EXCLUDED_TRANSITION"
        elif regime == "UNDEFINED":
            row["combined_state"] = "EXCLUDED_UNDEFINED"
        elif fs == "HIGH" and regime == "SIDEWAYS":
            row["combined_state"] = "ACTIVE_HIGH"
        elif fs == "LOW" and regime == "SIDEWAYS":
            row["combined_state"] = "ACTIVE_LOW"
        elif fs == "NEUTRAL" and regime == "SIDEWAYS":
            row["combined_state"] = "BASELINE"
        elif fs == "NEUTRAL" and regime == "NON_SIDEWAYS":
            row["combined_state"] = "NEUTRAL_NON_SIDEWAYS"
        elif fs in {"HIGH", "LOW"} and regime == "NON_SIDEWAYS":
            row["combined_state"] = "INACTIVE_DISPLACED"
        else:
            row["combined_state"] = "EXCLUDED_OTHER"

    state_counts = Counter(row["combined_state"] for row in funding)
    regime_counts = Counter(row["regime"] for row in funding)
    funding_state_counts = Counter(row["funding_state"] for row in funding)

    window_results = {}
    summary_labels = {}
    blockers = []

    for branch, active_state in (("HIGH", "ACTIVE_HIGH"), ("LOW", "ACTIVE_LOW")):
        branch_positive_windows = 0
        branch_direction_windows = 0
        branch_window_labels = {}
        active_total = state_counts[active_state]

        for window_name, offset in WINDOWS.items():
            active_deltas = []
            baseline_deltas = []
            no_forward = 0
            for i, row in enumerate(funding):
                if i + offset >= DISCOVERY_ROWS:
                    no_forward += 1
                    continue
                delta_bps = (funding[i + offset]["funding_rate"] - row["funding_rate"]) * 10000.0
                if row["combined_state"] == active_state:
                    active_deltas.append(delta_bps)
                elif row["combined_state"] == "BASELINE":
                    baseline_deltas.append(delta_bps)

            if active_total < 30:
                label = "NORMALIZATION_SCREEN_INCONCLUSIVE"
                blocker = "SCREENING_INSUFFICIENT_ACTIVE_OBSERVATIONS"
                blockers.append(f"{blocker}:{symbol}:{branch}")
                metrics = {
                    "label": label,
                    "active_n": len(active_deltas),
                    "baseline_n": len(baseline_deltas),
                    "no_forward_rows": no_forward,
                }
            elif regime_counts["SIDEWAYS"] < 50:
                label = "NORMALIZATION_SCREEN_INCONCLUSIVE"
                blockers.append(f"SCREENING_SIDEWAYS_TOO_SPARSE:{symbol}:{branch}")
                metrics = {
                    "label": label,
                    "active_n": len(active_deltas),
                    "baseline_n": len(baseline_deltas),
                    "no_forward_rows": no_forward,
                }
            elif not active_deltas or not baseline_deltas:
                label = "NORMALIZATION_SCREEN_INCONCLUSIVE"
                blockers.append(f"SCREENING_EMPTY_COMPARISON:{symbol}:{branch}:{window_name}")
                metrics = {
                    "label": label,
                    "active_n": len(active_deltas),
                    "baseline_n": len(baseline_deltas),
                    "no_forward_rows": no_forward,
                }
            else:
                active_median = median(active_deltas)
                baseline_median = median(baseline_deltas)
                active_median_abs = median([abs(v) for v in active_deltas])
                direction = expected_direction_pass(active_median, branch)
                separated = separation_pass(active_median, baseline_median, branch)
                magnitude = active_median_abs >= MAGNITUDE_FLOOR_BPS
                if direction and separated and magnitude:
                    label = "NORMALIZATION_SCREEN_POSITIVE"
                    branch_positive_windows += 1
                elif direction and separated:
                    label = "NORMALIZATION_SCREEN_WEAK"
                    branch_direction_windows += 1
                else:
                    label = "NORMALIZATION_SCREEN_ABSENT"
                metrics = {
                    "label": label,
                    "active_n": len(active_deltas),
                    "baseline_n": len(baseline_deltas),
                    "active_median_delta_f_bps": active_median,
                    "baseline_median_delta_f_bps": baseline_median,
                    "active_median_abs_delta_f_bps": active_median_abs,
                    "direction_pass": direction,
                    "baseline_separation_pass": separated,
                    "normalization_magnitude_floor_pass": magnitude,
                    "baseline_expected_direction_95pct_bps": p95_expected(baseline_deltas, branch),
                    "no_forward_rows": no_forward,
                }
            window_results[f"{branch}_{window_name}"] = metrics
            branch_window_labels[window_name] = metrics["label"]

        if active_total < 30 or regime_counts["SIDEWAYS"] < 50:
            summary = "NORMALIZATION_SCREEN_INCONCLUSIVE"
        elif branch_positive_windows >= 2:
            summary = "NORMALIZATION_SCREEN_POSITIVE"
        elif branch_positive_windows == 1 or branch_direction_windows >= 1:
            summary = "NORMALIZATION_SCREEN_WEAK"
        else:
            summary = "NORMALIZATION_SCREEN_ABSENT"

        summary_labels[branch] = {
            "summary_label": summary,
            "window_labels": branch_window_labels,
            "strong_anomaly_candidate": False,
        }

    return {
        "symbol": symbol,
        "funding_rows_loaded": len(funding),
        "held_out_rows_excluded": HELD_OUT_ROWS,
        "first_discovery_funding_time": iso(funding[0]["funding_time"]),
        "last_discovery_funding_time": iso(funding[-1]["funding_time"]),
        "threshold_method": "nearest-rank percentile on discovery rows only",
        "thresholds": {k: v for k, v in thresholds.items()},
        "state_counts": dict(state_counts),
        "funding_state_counts": dict(funding_state_counts),
        "regime_counts": dict(regime_counts),
        "ohlcv_alignment": ohlcv_summary,
        "window_results": window_results,
        "summary_labels": summary_labels,
        "blocker_flags": sorted(set(blockers)),
    }


def write_reports(result: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "Funding Normalization BTC/ETH Discovery Screening Report",
        "=======================================================",
        "",
        "Status: DISCOVERY-ONLY CHEAP-FALSIFICATION SCREENING.",
        "This report is non-evidence and does not authorize validation, readiness,",
        "paper/probe/runtime/live activity, trading, PnL claims, or capital use.",
        "",
        f"Overall label: {result['overall_label']}",
        f"Blocker flags: {', '.join(result['blocker_flags']) if result['blocker_flags'] else 'none'}",
        "",
        "Boundary confirmations:",
        "- BTCUSDT and ETHUSDT only.",
        "- SOLUSDT not decoded or included in computations.",
        "- Discovery rows only: rows 1-1502 in fundingTime ascending order.",
        "- Held-out rows 1503-2147 not decoded into row objects and not used.",
        "- No acquisition, download, API call, validation, PnL, returns, Sharpe, win rate, or readiness computation.",
        "",
        "Per-symbol summary:",
    ]
    for symbol, data in result["symbols"].items():
        lines.extend(
            [
                "",
                f"{symbol}:",
                f"- Funding rows used: {data['funding_rows_loaded']}",
                f"- Held-out rows excluded: {data['held_out_rows_excluded']}",
                f"- Discovery funding window: {data['first_discovery_funding_time']} to {data['last_discovery_funding_time']}",
                f"- OHLCV rows loaded for aligned context: {data['ohlcv_alignment']['rows_loaded']}",
                f"- OHLCV required window: {data['ohlcv_alignment']['min_required']} to {data['ohlcv_alignment']['max_required']}",
                f"- OHLCV missing aligned rows: {data['ohlcv_alignment']['missing_count']}",
                f"- Combined state counts: {data['state_counts']}",
                f"- Regime counts: {data['regime_counts']}",
                f"- Funding state counts: {data['funding_state_counts']}",
                f"- HIGH summary label: {data['summary_labels']['HIGH']['summary_label']}",
                f"- LOW summary label: {data['summary_labels']['LOW']['summary_label']}",
                f"- Symbol blocker flags: {', '.join(data['blocker_flags']) if data['blocker_flags'] else 'none'}",
            ]
        )
        for key, metrics in data["window_results"].items():
            metric_line = (
                f"  - {key}: {metrics['label']} "
                f"(active_n={metrics.get('active_n')}, baseline_n={metrics.get('baseline_n')})"
            )
            if "active_median_delta_f_bps" in metrics:
                metric_line += (
                    f"; active_median_delta_f_bps={metrics['active_median_delta_f_bps']:.6f}; "
                    f"baseline_median_delta_f_bps={metrics['baseline_median_delta_f_bps']:.6f}; "
                    f"active_median_abs_delta_f_bps={metrics['active_median_abs_delta_f_bps']:.6f}"
                )
            lines.append(metric_line)

    REPORT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    require_file(FUNDING_RAW)
    for path in OHLCV_PATHS.values():
        require_file(path)

    result = {
        "status": "DISCOVERY_ONLY_CHEAP_FALSIFICATION_SCREENING",
        "scope": {
            "symbols": list(SYMBOLS),
            "discovery_rows": DISCOVERY_ROWS,
            "held_out_rows_excluded_per_symbol": HELD_OUT_ROWS,
            "solusdt_included": False,
            "new_pairs_included": False,
        },
        "design_constraints": {
            "baseline": "NEUTRAL_AND_SIDEWAYS",
            "treatment": "HIGH_OR_LOW_AND_SIDEWAYS",
            "neutral_non_sideways": "observational_only_not_treatment_or_baseline_not_label_input",
            "ohlcv_alignment": "fundingTime t -> OHLCV open timestamp t-4H -> close field",
            "sideways_classifier": "5pct_net_move_20_funding_period_lookback_3_period_min_duration",
            "response": "delta_funding_rate_only",
            "windows": WINDOWS,
            "normalization_magnitude_floor_bps": MAGNITUDE_FLOOR_BPS,
        },
        "symbols": {},
        "blocker_flags": [],
        "overall_label": None,
    }

    for symbol in SYMBOLS:
        symbol_result = run_symbol(symbol)
        result["symbols"][symbol] = symbol_result
        result["blocker_flags"].extend(symbol_result["blocker_flags"])

    result["blocker_flags"] = sorted(set(result["blocker_flags"]))
    labels = [
        branch_data["summary_label"]
        for symbol_data in result["symbols"].values()
        for branch_data in symbol_data["summary_labels"].values()
    ]
    if result["blocker_flags"] or "NORMALIZATION_SCREEN_INCONCLUSIVE" in labels:
        result["overall_label"] = "NORMALIZATION_SCREEN_INCONCLUSIVE"
    elif "NORMALIZATION_SCREEN_POSITIVE" in labels:
        result["overall_label"] = "NORMALIZATION_SCREEN_POSITIVE"
    elif "NORMALIZATION_SCREEN_WEAK" in labels:
        result["overall_label"] = "NORMALIZATION_SCREEN_WEAK"
    else:
        result["overall_label"] = "NORMALIZATION_SCREEN_ABSENT"

    write_reports(result)
    print(json.dumps({"overall_label": result["overall_label"], "blocker_flags": result["blocker_flags"]}, indent=2))


if __name__ == "__main__":
    main()
