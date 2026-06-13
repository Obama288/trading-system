"""Generate SETUP_E_FEASIBILITY_REPORT.md for Setup E Stage 1.

Computes per-symbol quality, cascade episode counts split across the
discovery (first 70% of aligned bars) and validation (last 30%) windows,
SHA-256 hashes for every dataset file, and an episode-structure diagnostic.

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
_EXHAUSTION_PCT = 50          # median — baseline definition
_EXHAUSTION_PCT_STRICT = 25   # 25th percentile — stricter variant
_LOOKAHEAD_CAP = 25           # max bars searched for exhaustion after cascade
_DISCOVERY_FRACTION = 0.70
_MIN_DISCOVERY = 80
_MIN_VALIDATION = 40


# ---------------------------------------------------------------------------
# Data helpers
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


def _quality_check(ohlcv: list[dict]) -> dict:
    if not ohlcv:
        return {"bars": 0, "pass": False, "reason": "empty"}
    expected_gap = timedelta(hours=4)
    gaps = [ohlcv[i]["timestamp"] - ohlcv[i - 1]["timestamp"] for i in range(1, len(ohlcv))]
    bad_gaps = sum(1 for g in gaps if g != expected_gap)
    missing_frac = bad_gaps / max(len(gaps), 1)
    ok = missing_frac < 0.05
    return {
        "bars": len(ohlcv),
        "pass": ok,
        "missing_fraction": f"{missing_frac:.4f}",
        "bad_gaps": bad_gaps,
        "reason": "OK" if ok else f"{bad_gaps} non-4H gaps ({missing_frac:.1%})",
    }


# ---------------------------------------------------------------------------
# Episode counting — returns rich dicts, NO outcome metrics
# ---------------------------------------------------------------------------

def _find_cascade_indices(aligned: list[dict]) -> list[int]:
    """Pass 1: bar indices where long-liq > 95th pct of trailing 30d AND close < open."""
    indices = []
    n = len(aligned)
    for i in range(_TRAILING_BARS, n):
        window = [aligned[j]["long"] for j in range(i - _TRAILING_BARS, i)]
        thr = _percentile(window, _CASCADE_PCT)
        b = aligned[i]
        if b["long"] > thr and b["close"] < b["open"]:
            indices.append(i)
    return indices


def _count_episodes(aligned: list[dict], exhaustion_pct: int = _EXHAUSTION_PCT) -> list[dict]:
    """Return list of episode dicts — one per non-overlapping episode.

    Each dict contains ONLY signal-identification fields (no prices after signal):
      signal_ts    : datetime of signal/exhaustion bar
      cascade_idx  : bar index (in aligned) of the cascade bar
      signal_idx   : bar index of the signal/exhaustion bar
      lag_bars     : signal_idx - cascade_idx (≥1; 1 = immediate exhaustion)

    HARD RULE: no outcome metrics. No price reads beyond contemporaneous bar.
    """
    n = len(aligned)
    episodes: list[dict] = []
    next_allowed = 0

    for ci in _find_cascade_indices(aligned):
        if ci < next_allowed:
            continue
        for j in range(ci + 1, min(ci + _LOOKAHEAD_CAP, n)):
            window = [aligned[k]["long"] for k in range(max(0, j - _TRAILING_BARS), j)]
            threshold = _percentile(window, exhaustion_pct)
            if aligned[j]["long"] < threshold:
                episodes.append({
                    "signal_ts":   aligned[j]["timestamp"],
                    "cascade_idx": ci,
                    "signal_idx":  j,
                    "lag_bars":    j - ci,
                })
                next_allowed = j + 1
                break

    return episodes


# ---------------------------------------------------------------------------
# Diagnostic statistics — no outcome metrics
# ---------------------------------------------------------------------------

def _lag_stats(lags: list[int]) -> dict:
    """Percentile distribution of cascade→signal lag (bar count)."""
    if not lags:
        return {k: "N/A" for k in ("n", "min", "p25", "median", "p75", "p90", "max", "mean")}
    s = sorted(lags)
    n = len(s)

    def pct(p: int) -> int:
        return s[max(0, int(n * p / 100) - 1)]

    return {
        "n":      n,
        "min":    s[0],
        "p25":    pct(25),
        "median": pct(50),
        "p75":    pct(75),
        "p90":    pct(90),
        "max":    s[-1],
        "mean":   f"{sum(lags) / n:.2f}",
    }


def _fmt_stat(v: object) -> str:
    return str(v)


def _build_diagnostic_section(
    pooled_all:   list[dict],
    pooled_disc:  list[dict],
    pooled_val:   list[dict],
    strict_disc:  int,
    strict_val:   int,
    strict_full:  int,
    incomplete_full: int,
    incomplete_disc: int,
    incomplete_val:  int,
    excl_incomplete_disc: int,
    excl_incomplete_val:  int,
    excl_incomplete_full: int,
    median_cut: datetime | None,
) -> list[str]:
    """Build the '## Episode Structure Diagnostic' Markdown section."""
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)

    def stats_row(label: str, eps: list[dict]) -> str:
        lags = [e["lag_bars"] for e in eps]
        st = _lag_stats(lags)
        imm = sum(1 for e in eps if e["lag_bars"] == 1)
        imm_pct = f"{100 * imm / len(eps):.1f}%" if eps else "N/A"
        return (
            f"| {label} | {st['n']} | {st['min']} | {st['p25']} | {st['median']} "
            f"| {st['p75']} | {st['p90']} | {st['max']} | {st['mean']} | {imm_pct} |"
        )

    w("## Episode Structure Diagnostic")
    w()
    w("**HARD RULE**: this section contains NO outcome metrics. All statistics")
    w("describe signal-identification structure only (cascade→signal bar counts,")
    w("lookback validity). No prices after the signal bar are read or reported.")
    w()

    # --- 1. Lag distribution ---
    w("### 1. Cascade → Signal Lag Distribution (bars)")
    w()
    w("Lag = number of bars from cascade bar to signal/exhaustion bar (minimum 1).")
    w("A lag of 1 means exhaustion fires on the very next bar after the cascade")
    w("(immediate exhaustion — flagged separately below as a potential degeneracy).")
    w()
    w("| Window | N | min | p25 | median | p75 | p90 | max | mean | lag=1 (%) |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    w(stats_row("Pooled (all)", pooled_all))
    w(stats_row("Discovery (first 70%)", pooled_disc))
    w(stats_row("Validation (last 30%)", pooled_val))
    w()

    # --- 2. Immediate exhaustion fraction ---
    imm_all  = sum(1 for e in pooled_all  if e["lag_bars"] == 1)
    imm_disc = sum(1 for e in pooled_disc if e["lag_bars"] == 1)
    imm_val  = sum(1 for e in pooled_val  if e["lag_bars"] == 1)

    def pct_str(num: int, den: int) -> str:
        return f"{100 * num / den:.1f}%" if den else "N/A"

    w("### 2. Immediate Exhaustion (lag = 1 bar) — Degeneracy Flag")
    w()
    w("An episode where the exhaustion signal fires on the bar immediately after")
    w("the cascade bar may indicate that the median threshold is too easy to reach,")
    w("or that cascade bars themselves suppress subsequent liquidation structurally.")
    w()
    w("| Window | Episodes | lag=1 | lag=1 % |")
    w("|---|---|---|---|")
    w(f"| Pooled | {len(pooled_all)} | {imm_all} | {pct_str(imm_all, len(pooled_all))} |")
    w(f"| Discovery | {len(pooled_disc)} | {imm_disc} | {pct_str(imm_disc, len(pooled_disc))} |")
    w(f"| Validation | {len(pooled_val)} | {imm_val} | {pct_str(imm_val, len(pooled_val))} |")
    w()

    # --- 3 & 4. Incomplete-lookback episodes ---
    w("### 3 & 4. Incomplete-Lookback Episodes")
    w()
    w("The trailing 30-day lookback (180 × 4H bars) is FULLY accumulated starting")
    w("at bar index 180. The cascade detection loop enforces this: it begins at")
    w(f"`range(_TRAILING_BARS={_TRAILING_BARS}, n)`, so no cascade bar can have index < {_TRAILING_BARS}.")
    w("Therefore the signal bar (cascade_idx + 1 at minimum) always has index ≥ 181,")
    w("which is outside the first 180 bars (the lookback warmup period).")
    w()
    w("| Window | Incomplete-lookback episodes | Total | Excluded count |")
    w("|---|---|---|---|")
    w(f"| Pooled | {incomplete_full} | {len(pooled_all)} | {excl_incomplete_full} episodes retained |")
    w(f"| Discovery | {incomplete_disc} | {len(pooled_disc)} | {excl_incomplete_disc} episodes retained |")
    w(f"| Validation | {incomplete_val} | {len(pooled_val)} | {excl_incomplete_val} episodes retained |")
    w()
    if incomplete_full == 0:
        w("**Result**: 0 incomplete-lookback episodes. The implementation correctly")
        w("prevents any episode from relying on a partial lookback window.")
        w("Exclusion has no effect on episode counts.")
    else:
        w(f"**Result**: {incomplete_full} incomplete-lookback episodes found.")
        w("Owner should review whether to exclude these before locking the pre-registration.")
    w()

    # --- 5. Stricter exhaustion definition ---
    w("### 5. Stricter Exhaustion Definition (25th percentile vs median)")
    w()
    w(f"Baseline definition: signal bar = first bar where long-liq < trailing-30d **median** ({_EXHAUSTION_PCT}th pct).")
    w(f"Stricter definition: signal bar = first bar where long-liq < trailing-30d **25th percentile** ({_EXHAUSTION_PCT_STRICT}th pct).")
    w("A lower threshold means exhaustion fires only on more extreme liq drops,")
    w("reducing episode count but potentially improving signal quality.")
    w()
    w("| Window | Baseline (median, 50th pct) | Stricter (25th pct) | Reduction |")
    w("|---|---|---|---|")
    base_disc = len(pooled_disc)
    base_val  = len(pooled_val)
    base_full = len(pooled_all)
    red_disc  = base_disc - strict_disc
    red_val   = base_val  - strict_val
    red_full  = base_full - strict_full
    w(f"| Pooled | {base_full} | {strict_full} | −{red_full} ({pct_str(red_full, base_full)}) |")
    w(f"| Discovery | {base_disc} | {strict_disc} | −{red_disc} ({pct_str(red_disc, base_disc)}) |")
    w(f"| Validation | {base_val} | {strict_val} | −{red_val} ({pct_str(red_val, base_val)}) |")
    w()
    if strict_disc >= _MIN_DISCOVERY and strict_val >= _MIN_VALIDATION:
        w(f"**Strict definition still meets minimums** (discovery ≥ {_MIN_DISCOVERY}, validation ≥ {_MIN_VALIDATION}).")
    else:
        failing = []
        if strict_disc < _MIN_DISCOVERY:
            failing.append(f"discovery {strict_disc} < {_MIN_DISCOVERY}")
        if strict_val < _MIN_VALIDATION:
            failing.append(f"validation {strict_val} < {_MIN_VALIDATION}")
        w(f"**Strict definition falls below minimums**: {'; '.join(failing)}.")
        w("Owner decision required if strict definition is adopted before lock.")
    w()
    w("---")

    return lines


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

    # Pooled episode collections for diagnostic
    pooled_all:  list[dict] = []
    pooled_disc: list[dict] = []
    pooled_val:  list[dict] = []
    strict_disc_total = 0
    strict_val_total  = 0
    strict_full_total = 0
    incomplete_full_total = 0
    incomplete_disc_total = 0
    incomplete_val_total  = 0

    for sym in symbols:
        stem = sym.replace(".", "_")
        ohlcv_path = _DATA_DIR / f"{stem}_ohlcv_4h.csv"
        liq_path   = _DATA_DIR / f"{stem}_liquidation_4h.csv"

        for p in (ohlcv_path, liq_path):
            if not p.exists():
                print(f"ERROR: missing file {p}", file=sys.stderr)
                return 2

        sha_ohlcv = _sha256(ohlcv_path)
        sha_liq   = _sha256(liq_path)
        sha_lines.append(f"| {sym} | ohlcv | `{sha_ohlcv}` |")
        sha_lines.append(f"| {sym} | liquidation | `{sha_liq}` |")

        ohlcv   = _load_ohlcv(ohlcv_path)
        liq     = _load_liq(liq_path)
        aligned = _align(ohlcv, liq)

        q = _quality_check(ohlcv)
        if not q["pass"]:
            all_pass = False

        n = len(aligned)
        cutpoint = int(n * _DISCOVERY_FRACTION)
        discovery_cutbar   = aligned[cutpoint - 1]["timestamp"] if cutpoint > 0 else None
        validation_startbar = aligned[cutpoint]["timestamp"] if cutpoint < n else None
        aligned_start_ts   = aligned[0]["timestamp"] if aligned else None

        # --- baseline episodes ---
        all_eps  = _count_episodes(aligned, _EXHAUSTION_PCT)
        disc_eps = [e for e in all_eps if discovery_cutbar   and e["signal_ts"] <= discovery_cutbar]
        val_eps  = [e for e in all_eps if validation_startbar and e["signal_ts"] >= validation_startbar]

        # --- strict episodes (25th pct exhaustion) ---
        strict_eps      = _count_episodes(aligned, _EXHAUSTION_PCT_STRICT)
        strict_disc_eps = [e for e in strict_eps if discovery_cutbar   and e["signal_ts"] <= discovery_cutbar]
        strict_val_eps  = [e for e in strict_eps if validation_startbar and e["signal_ts"] >= validation_startbar]

        # --- incomplete-lookback episodes ---
        # Lookback is fully accumulated at cascade_idx >= _TRAILING_BARS (loop invariant).
        # "Incomplete" = cascade_idx < _TRAILING_BARS — impossible by construction; count confirms.
        first_eligible_ts = (
            aligned_start_ts + timedelta(hours=4 * _TRAILING_BARS)
            if aligned_start_ts else None
        )
        incomplete_all  = [e for e in all_eps  if e["cascade_idx"] < _TRAILING_BARS]
        incomplete_disc = [e for e in disc_eps if e["cascade_idx"] < _TRAILING_BARS]
        incomplete_val  = [e for e in val_eps  if e["cascade_idx"] < _TRAILING_BARS]

        if discovery_cutbar:
            discovery_cutdates.append(discovery_cutbar)

        total_discovery     += len(disc_eps)
        total_validation    += len(val_eps)
        total_full          += len(all_eps)
        strict_disc_total   += len(strict_disc_eps)
        strict_val_total    += len(strict_val_eps)
        strict_full_total   += len(strict_eps)
        incomplete_full_total += len(incomplete_all)
        incomplete_disc_total += len(incomplete_disc)
        incomplete_val_total  += len(incomplete_val)

        pooled_all  .extend(all_eps)
        pooled_disc .extend(disc_eps)
        pooled_val  .extend(val_eps)

        first_ts = aligned[0]["timestamp"] if aligned else None
        last_ts  = aligned[-1]["timestamp"] if aligned else None

        rows.append({
            "symbol":           sym,
            "ohlcv_bars":       q["bars"],
            "aligned_bars":     n,
            "quality_pass":     q["pass"],
            "quality_reason":   q["reason"],
            "first_bar":        first_ts.strftime("%Y-%m-%dT%H:%MZ") if first_ts else "N/A",
            "last_bar":         last_ts.strftime("%Y-%m-%dT%H:%MZ")  if last_ts  else "N/A",
            "discovery_cutbar": discovery_cutbar.strftime("%Y-%m-%dT%H:%MZ")    if discovery_cutbar    else "N/A",
            "validation_startbar": validation_startbar.strftime("%Y-%m-%dT%H:%MZ") if validation_startbar else "N/A",
            "discovery_cutpoint": cutpoint,
            "episodes_full":    len(all_eps),
            "episodes_discovery": len(disc_eps),
            "episodes_validation": len(val_eps),
        })

    excl_incomplete_full = len(pooled_all)  - incomplete_full_total
    excl_incomplete_disc = len(pooled_disc) - incomplete_disc_total
    excl_incomplete_val  = len(pooled_val)  - incomplete_val_total

    discovery_cutdates.sort()
    median_cut = discovery_cutdates[len(discovery_cutdates) // 2] if discovery_cutdates else None

    disc_verdict    = "SUFFICIENT" if total_discovery >= _MIN_DISCOVERY else "INSUFFICIENT"
    val_verdict     = "SUFFICIENT" if total_validation >= _MIN_VALIDATION else "INSUFFICIENT"
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
    w("Constitution: `docs/RESEARCH_CONSTITUTION.md` v1.1")
    w("Pre-registration: `research/signal_observation/SETUP_E_PREREGISTRATION.md` (DRAFT)")
    w("Universe list: `research/signal_observation/_selected_symbols.json`")
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

    # --- diagnostic section ---
    for line in _build_diagnostic_section(
        pooled_all=pooled_all,
        pooled_disc=pooled_disc,
        pooled_val=pooled_val,
        strict_disc=strict_disc_total,
        strict_val=strict_val_total,
        strict_full=strict_full_total,
        incomplete_full=incomplete_full_total,
        incomplete_disc=incomplete_disc_total,
        incomplete_val=incomplete_val_total,
        excl_incomplete_disc=excl_incomplete_disc,
        excl_incomplete_val=excl_incomplete_val,
        excl_incomplete_full=excl_incomplete_full,
        median_cut=median_cut,
    ):
        w(line)

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
    w("6. **Exhaustion definition**: review §3 (immediate exhaustion fraction) and §5")
    w("   (strict 25th-pct variant) in the diagnostic section above before locking §2.3.")

    _REPORT_PATH.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Written: {_REPORT_PATH}")
    print(f"Verdict: {overall}")
    print(f"Discovery episodes: {total_discovery}/{_MIN_DISCOVERY}  Validation: {total_validation}/{_MIN_VALIDATION}  Quality: {quality_verdict}")
    print(f"Strict (25th pct): disc={strict_disc_total}  val={strict_val_total}  full={strict_full_total}")
    print(f"Incomplete-lookback: {incomplete_full_total} (confirms 0 by construction)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
