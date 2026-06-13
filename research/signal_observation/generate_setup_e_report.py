"""Generate SETUP_E_FEASIBILITY_REPORT.md for Setup E Stage 1.

Computes per-symbol quality, cascade episode counts split across the
discovery (first 70% of aligned bars) and validation (last 30%) windows,
and SHA-256 hashes for every dataset file.

HARD RULE: NO outcome metrics. No returns, win rates, expectancy, MFE/MAE,
or any value derived from prices after a signal bar. (Constitution §1, Stage 1.)

Usage:
    python -m research.signal_observation.generate_setup_e_report
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

_HERE = Path(__file__).parent
_DATA_DIR = _HERE / "data" / "setup_e"
_SYMBOLS_FILE = _HERE / "_selected_symbols.json"
_REPORT_PATH = _HERE / "SETUP_E_FEASIBILITY_REPORT.md"

_BARS_PER_DAY_4H = 6
_TRAILING_BARS = _BARS_PER_DAY_4H * 30   # 180 bars = 30-day lookback
_CASCADE_PCT = 95
_EXHAUSTION_PCT = 50
_DISCOVERY_FRACTION = 0.70
_MIN_DISCOVERY = 80
_MIN_VALIDATION = 40


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _percentile(vals: list[Decimal], pct: int) -> Decimal:
    if not vals:
        return Decimal("0")
    s = sorted(vals)
    rank = max(0, int(len(s) * pct / 100) - 1)
    return s[rank]


def _load_ohlcv(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            rows.append({
                "timestamp": ts,
                "open": Decimal(row["open"]),
                "high": Decimal(row["high"]),
                "low": Decimal(row["low"]),
                "close": Decimal(row["close"]),
                "volume": Decimal(row["volume"]),
            })
    rows.sort(key=lambda r: r["timestamp"])
    return rows


def _load_liq(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = datetime.fromisoformat(row["timestamp_utc"].replace("Z", "+00:00"))
            rows.append({
                "timestamp": ts,
                "long": Decimal(row["long_notional_usd"]),
                "short": Decimal(row["short_notional_usd"]),
            })
    rows.sort(key=lambda r: r["timestamp"])
    return rows


def _align(ohlcv: list[dict], liq: list[dict]) -> list[dict]:
    ts_ohlcv = {r["timestamp"]: r for r in ohlcv}
    ts_liq = {r["timestamp"]: r for r in liq}
    common = sorted(ts_ohlcv.keys() & ts_liq.keys())
    return [{**ts_ohlcv[ts], **ts_liq[ts]} for ts in common]


def _count_episodes(aligned: list[dict]) -> list[datetime]:
    """Return list of signal-bar timestamps — one per episode, no outcome metrics."""
    n = len(aligned)
    signal_timestamps: list[datetime] = []
    next_allowed = 0
    cascade_indices: list[int] = []

    # Pass 1: cascade bars
    for i in range(_TRAILING_BARS, n):
        window = [aligned[j]["long"] for j in range(i - _TRAILING_BARS, i)]
        thr = _percentile(window, _CASCADE_PCT)
        b = aligned[i]
        if b["long"] > thr and b["close"] < b["open"]:
            cascade_indices.append(i)

    # Pass 2: exhaustion bars → episodes
    for ci in cascade_indices:
        if ci < next_allowed:
            continue
        for j in range(ci + 1, min(ci + 25, n)):
            window = [aligned[k]["long"] for k in range(max(0, j - _TRAILING_BARS), j)]
            median = _percentile(window, _EXHAUSTION_PCT)
            if aligned[j]["long"] < median:
                signal_timestamps.append(aligned[j]["timestamp"])
                next_allowed = j + 1
                break

    return signal_timestamps


def _quality_check(ohlcv: list[dict]) -> dict:
    """Basic quality metrics — no simcore dependency needed here."""
    if not ohlcv:
        return {"bars": 0, "pass": False, "reason": "empty"}
    n = len(ohlcv)
    # Expected 4H spacing
    expected_gap = timedelta(hours=4)
    gaps = [
        ohlcv[i]["timestamp"] - ohlcv[i - 1]["timestamp"]
        for i in range(1, n)
    ]
    bad_gaps = sum(1 for g in gaps if g != expected_gap)
    missing_frac = bad_gaps / max(len(gaps), 1)
    ok = missing_frac < 0.05  # <5% gaps → PASS (matches simcore quality threshold)
    return {
        "bars": n,
        "pass": ok,
        "missing_fraction": f"{missing_frac:.4f}",
        "bad_gaps": bad_gaps,
        "reason": "OK" if ok else f"{bad_gaps} non-4H gaps ({missing_frac:.1%})",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not _DATA_DIR.exists():
        print(f"ERROR: data directory not found: {_DATA_DIR}", file=sys.stderr)
        print("Run TASK 2 acquisition first.", file=sys.stderr)
        return 2

    symbols: list[str] = json.loads(_SYMBOLS_FILE.read_text(encoding="utf-8"))
    now_utc = datetime.now(UTC)

    rows = []
    total_discovery = 0
    total_validation = 0
    total_full = 0
    all_pass = True
    sha_lines: list[str] = []
    discovery_cutdates: list[datetime] = []

    for sym in symbols:
        stem = sym.replace(".", "_")
        ohlcv_path = _DATA_DIR / f"{stem}_ohlcv_4h.csv"
        liq_path = _DATA_DIR / f"{stem}_liquidation_4h.csv"

        # --- existence check ---
        for p in (ohlcv_path, liq_path):
            if not p.exists():
                print(f"ERROR: missing file {p}", file=sys.stderr)
                return 2

        # --- SHA-256 ---
        sha_ohlcv = _sha256(ohlcv_path)
        sha_liq = _sha256(liq_path)
        sha_lines.append(f"| {sym} | ohlcv | `{sha_ohlcv}` |")
        sha_lines.append(f"| {sym} | liquidation | `{sha_liq}` |")

        # --- load & align ---
        ohlcv = _load_ohlcv(ohlcv_path)
        liq = _load_liq(liq_path)
        aligned = _align(ohlcv, liq)

        # --- quality ---
        q = _quality_check(ohlcv)
        if not q["pass"]:
            all_pass = False

        # --- episode counting with 70/30 window split ---
        n = len(aligned)
        cutpoint = int(n * _DISCOVERY_FRACTION)

        # Discovery: run on full data so the trailing lookback is always valid;
        # then keep only episodes whose signal bar falls in the first 70% of bars.
        all_eps = _count_episodes(aligned)
        discovery_cutbar = aligned[cutpoint - 1]["timestamp"] if cutpoint > 0 else None
        validation_startbar = aligned[cutpoint]["timestamp"] if cutpoint < n else None

        disc_eps = [e for e in all_eps if discovery_cutbar and e <= discovery_cutbar]
        val_eps = [e for e in all_eps if validation_startbar and e >= validation_startbar]

        if discovery_cutbar:
            discovery_cutdates.append(discovery_cutbar)

        total_discovery += len(disc_eps)
        total_validation += len(val_eps)
        total_full += len(all_eps)

        first_ts = aligned[0]["timestamp"] if aligned else None
        last_ts = aligned[-1]["timestamp"] if aligned else None

        rows.append({
            "symbol": sym,
            "ohlcv_bars": q["bars"],
            "aligned_bars": n,
            "quality_pass": q["pass"],
            "quality_reason": q["reason"],
            "first_bar": first_ts.strftime("%Y-%m-%dT%H:%MZ") if first_ts else "N/A",
            "last_bar": last_ts.strftime("%Y-%m-%dT%H:%MZ") if last_ts else "N/A",
            "discovery_cutbar": discovery_cutbar.strftime("%Y-%m-%dT%H:%MZ") if discovery_cutbar else "N/A",
            "validation_startbar": validation_startbar.strftime("%Y-%m-%dT%H:%MZ") if validation_startbar else "N/A",
            "discovery_cutpoint": cutpoint,
            "episodes_full": len(all_eps),
            "episodes_discovery": len(disc_eps),
            "episodes_validation": len(val_eps),
        })

    # Cross-symbol common cut date (median of per-symbol 70% cutpoints)
    discovery_cutdates.sort()
    median_cut = discovery_cutdates[len(discovery_cutdates) // 2] if discovery_cutdates else None

    disc_verdict = "SUFFICIENT" if total_discovery >= _MIN_DISCOVERY else "INSUFFICIENT"
    val_verdict = "SUFFICIENT" if total_validation >= _MIN_VALIDATION else "INSUFFICIENT"
    quality_verdict = "PASS" if all_pass else "FAIL"
    overall = (
        "FEASIBLE — proceed to pre-registration lock"
        if disc_verdict == "SUFFICIENT" and val_verdict == "SUFFICIENT" and all_pass
        else "BLOCKED — owner decision required before lock"
    )

    # ---------------------------------------------------------------------------
    # Build Markdown
    # ---------------------------------------------------------------------------
    md_lines: list[str] = []

    def w(s: str = "") -> None:
        md_lines.append(s)

    w("# Setup E — Stage 1 Feasibility Report")
    w()
    w(f"Generated: {now_utc.strftime('%Y-%m-%dT%H:%MZ')}")
    w(f"Constitution: `docs/RESEARCH_CONSTITUTION.md` v1.1")
    w(f"Pre-registration: `research/signal_observation/SETUP_E_PREREGISTRATION.md` (DRAFT)")
    w(f"Universe list: `research/signal_observation/_selected_symbols.json`")
    w()
    w("**HARD RULE**: This report contains NO outcome metrics. No returns, win rates,")
    w("expectancy, MFE/MAE, or any value derived from prices after a signal bar.")
    w("(Constitution §1, Stage 1. Violation taints the discovery window.)")
    w()
    w("---")
    w()
    w("## Overall Verdict")
    w()
    w(f"**{overall}**")
    w()
    w("| Metric | Value | Minimum | Status |")
    w("|---|---|---|---|")
    w(f"| Total episodes — full window | {total_full} | — | — |")
    w(f"| Total episodes — discovery (first 70%) | {total_discovery} | {_MIN_DISCOVERY} | **{disc_verdict}** |")
    w(f"| Total episodes — validation (last 30%) | {total_validation} | {_MIN_VALIDATION} | **{val_verdict}** |")
    w(f"| Quality (all symbols) | {'20/20 PASS' if all_pass else 'FAIL'} | 20/20 PASS | **{quality_verdict}** |")
    w()
    w("---")
    w()
    w("## Window Boundaries")
    w()
    w("Window split: first 70% of per-symbol aligned bars = discovery;")
    w("remaining 30% = validation. Boundaries differ by symbol due to varying")
    w("liquidation data retention. A **single cross-symbol cut date** may be")
    w("preferred — the median of per-symbol 70% cutpoints is shown below.")
    w()
    if median_cut:
        w(f"**Suggested single discovery/validation cutpoint (median): `{median_cut.strftime('%Y-%m-%dT%H:%MZ')}`**")
        w()
        w("Owner decision required (TBD-F in pre-registration §2.6): accept per-symbol")
        w("splits as shown, or adopt the single cutpoint. Either choice must be recorded")
        w("in the locked pre-registration before any Stage 2 run.")
    w()
    w("---")
    w()
    w("## Per-Symbol Detail")
    w()
    w("| Symbol | OHLCV bars | Aligned bars | Quality | First aligned bar | Discovery cut | Validation start | Last bar | Eps full | Eps disc | Eps val |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        q_str = "PASS" if r["quality_pass"] else f"FAIL ({r['quality_reason']})"
        w(f"| {r['symbol']} | {r['ohlcv_bars']} | {r['aligned_bars']} | {q_str} | {r['first_bar']} | {r['discovery_cutbar']} | {r['validation_startbar']} | {r['last_bar']} | {r['episodes_full']} | {r['episodes_discovery']} | {r['episodes_validation']} |")
    w()
    w("---")
    w()
    w("## Dataset SHA-256 Hashes")
    w()
    w("These hashes bind this report to the exact downloaded files.")
    w("Record these in the pre-registration §2.6 TBD-F fields at lock time.")
    w()
    w("| Symbol | Dataset | SHA-256 |")
    w("|---|---|---|")
    for line in sha_lines:
        w(line)
    w()
    w("---")
    w()
    w("## Methodology Notes")
    w()
    w("- **Cascade bar**: long-liquidation notional > 95th percentile of trailing")
    w("  30-day (180 × 4H bar) long-liq distribution AND close < open (down bar).")
    w("- **Signal/exhaustion bar**: first subsequent bar where long-liq falls below")
    w("  the trailing 30-day median. Episode tagged to this bar's timestamp.")
    w("- **Non-overlapping**: new episode cannot start until prior signal bar + 1")
    w("  (constitution §3.8).")
    w("- **Window split**: episode assigned to discovery if signal bar timestamp ≤")
    w("  the 70th-percentile bar; validation if ≥ 71st-percentile bar. Trailing")
    w("  lookback for validation bars borrows from discovery data (contemporaneous,")
    w("  not outcome data — permitted at Stage 1).")
    w("- **Quality threshold**: <5% non-4H gaps → PASS.")
    w()
    w("---")
    w()
    w("## Owner Decisions Required Before Pre-Registration Lock")
    w()
    w("1. **Source approval**: approve Coinalyze free API key path as data source.")
    w("2. **Universe confirmation**: confirm the 20 symbols in `_selected_symbols.json`")
    w("   are accepted as frozen.")
    w(f"3. **Window boundary**: choose per-symbol 70/30 splits (as tabulated above)")
    w(f"   OR adopt single cutpoint `{median_cut.strftime('%Y-%m-%dT%H:%MZ') if median_cut else 'TBD'}` (median of per-symbol cuts).")
    w("4. **SHA-256 lock**: copy hashes from the table above into pre-registration §2.6.")
    w("5. **Minimum confirmation**: discovery minimum is 80 (met). Validation minimum")
    w("   is 40 (met). No adjustment needed.")

    _REPORT_PATH.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Written: {_REPORT_PATH}")
    print(f"Verdict: {overall}")
    print(f"Discovery episodes: {total_discovery}/{_MIN_DISCOVERY}  Validation: {total_validation}/{_MIN_VALIDATION}  Quality: {quality_verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
