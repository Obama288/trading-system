"""Setup H Stage 2 — Discovery runner.

Governed by: research/signal_observation/SETUP_H_PREREGISTRATION.md (LOCKED).

Primary metric: (gated expectancy_R) - (ungated expectancy_R), pooled,
non-overlapping rebalance observations, moderate 8 bps/side cost assumption.

Gate (all three required for PASS):
  gated expectancy_R >= +0.05R
  gated - ungated   >= +0.05R
  gated             >  shuffled-regime p95 (seed 69, 1000 resamples)

Run from project root:
    python -m research.signal_observation.run_setup_h_discovery
"""
from __future__ import annotations

import hashlib
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from research.signal_observation.candles import Candle
from research.signal_observation.csv_loader import load_ohlcv_csv
from research.signal_observation.setup_h_detector import (
    COST_BPS,
    DISCOVERY_CUTOFF,
    GATE_DIFF_MIN,
    GATE_GATED_MIN,
    GATE_SHUFFLED_PCT,
    LOOKBACK,
    N_RESAMPLES,
    PRIMARY_COST,
    RANDOM_SEED,
    GatedObs,
    build_gated_obs,
    obs_expectancy,
    obs_expectancy_scenarios,
    percentile_of,
    shuffled_regime_baseline,
    _pct,
)

# ---------------------------------------------------------------------------
# Locked identifiers
# ---------------------------------------------------------------------------

DATA_DIR = ROOT / "research" / "signal_observation" / "data" / "setup_h"
REPORT_PATH = ROOT / "research" / "signal_observation" / "SETUP_H_DISCOVERY_RESULT.md"

SYMBOLS = [
    "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT", "ZECUSDT",
]

LOCKED_COMBINED_SHA256 = (
    "30d2027f9af6f191dfa7ff0e572b60c28b91f0c68ea8f28ec021f292b5788d05"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _fmt(v: Decimal | None, places: int = 4) -> str:
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{float(v):.{places}f}R"


def _fmtf(v: float, places: int = 4) -> str:
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.{places}f}R"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    lines: list[str] = []
    emit = lines.append
    run_ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ------------------------------------------------------------------
    # 1. Data loading and SHA-256 verification
    # ------------------------------------------------------------------
    missing = [s for s in SYMBOLS if not (DATA_DIR / f"{s}_4h.csv").exists()]
    if missing:
        print(f"ABORT: missing CSV files: {missing}")
        print("Run _acquire_setup_h.py first.")
        sys.exit(1)

    file_hashes: dict[str, str] = {}
    candles_by_sym: dict[str, list[Candle]] = {}

    for sym in SYMBOLS:
        path = DATA_DIR / f"{sym}_4h.csv"
        file_hashes[sym] = _sha256_file(path)
        candles_by_sym[sym] = load_ohlcv_csv(path)

    combined_hash = hashlib.sha256(
        "".join(file_hashes[s] for s in sorted(SYMBOLS)).encode()
    ).hexdigest()

    if combined_hash != LOCKED_COMBINED_SHA256:
        print(
            f"ABORT: dataset hash mismatch.\n"
            f"  expected: {LOCKED_COMBINED_SHA256}\n"
            f"  computed: {combined_hash}\n"
            "Data has changed since pre-registration; cannot run discovery on modified data."
        )
        sys.exit(1)

    print(f"SHA-256 verified: {combined_hash}")

    # ------------------------------------------------------------------
    # 2. Build observations
    # ------------------------------------------------------------------
    obs_by_sym: dict[str, list[GatedObs]] = {}
    for sym in SYMBOLS:
        obs_by_sym[sym] = build_gated_obs(
            candles_by_sym[sym],
            symbol=sym,
            cutoff=DISCOVERY_CUTOFF,
        )
        print(f"  {sym}: {len(obs_by_sym[sym])} obs")

    all_obs = [o for obs in obs_by_sym.values() for o in obs]
    n_total = len(all_obs)
    n_low = sum(1 for o in all_obs if o.regime == "LOW")
    n_high = sum(1 for o in all_obs if o.regime == "HIGH")

    print(f"Pooled obs: {n_total} (LOW={n_low}, HIGH={n_high})")

    # ------------------------------------------------------------------
    # 3. Primary metrics (primary = moderate 8 bps)
    # ------------------------------------------------------------------
    primary_bps = COST_BPS[PRIMARY_COST]

    gated_exp = obs_expectancy(all_obs, gated=True, cost_bps=primary_bps)
    ungated_exp = obs_expectancy(all_obs, gated=False, cost_bps=primary_bps)
    diff_exp = (
        gated_exp - ungated_exp
        if gated_exp is not None and ungated_exp is not None
        else None
    )

    # High-vol bucket diagnostic: ungated TSMOM on HIGH-VOL bars only
    high_obs = [o for o in all_obs if o.regime == "HIGH"]
    high_ungated_exp = obs_expectancy(high_obs, gated=False, cost_bps=primary_bps)

    # ------------------------------------------------------------------
    # 4. Cost-scenario diagnostics
    # ------------------------------------------------------------------
    gated_scenarios = obs_expectancy_scenarios(all_obs, gated=True)
    ungated_scenarios = obs_expectancy_scenarios(all_obs, gated=False)

    # ------------------------------------------------------------------
    # 5. Shuffled-regime baseline
    # ------------------------------------------------------------------
    print(f"Running shuffled-regime baseline ({N_RESAMPLES} resamples, seed {RANDOM_SEED})...")
    baseline_dist = shuffled_regime_baseline(
        obs_by_sym,
        cost_bps=primary_bps,
        seed=RANDOM_SEED,
        n_resamples=N_RESAMPLES,
    )

    gated_exp_float = float(gated_exp) if gated_exp is not None else 0.0
    observed_pct = percentile_of(gated_exp_float, baseline_dist)
    p95_threshold = _pct(baseline_dist, 95.0)
    shuffled_mean = sum(baseline_dist) / len(baseline_dist) if baseline_dist else 0.0

    print(f"Baseline done. Observed gated pct vs shuffled: {observed_pct:.1f}%")

    # ------------------------------------------------------------------
    # 6. Gate evaluation
    # ------------------------------------------------------------------
    cond_gated_min = (
        gated_exp is not None and gated_exp >= GATE_GATED_MIN
    )
    cond_diff_min = (
        diff_exp is not None and diff_exp >= GATE_DIFF_MIN
    )
    cond_shuffled = gated_exp_float > p95_threshold

    gate_pass = cond_gated_min and cond_diff_min and cond_shuffled
    verdict = "PASS" if gate_pass else "PARK"

    # ------------------------------------------------------------------
    # 7. Write report
    # ------------------------------------------------------------------
    emit("# Setup H Discovery Result")
    emit("")
    emit(f"Run timestamp: {run_ts}")
    emit(f"Pre-registration: `research/signal_observation/SETUP_H_PREREGISTRATION.md` (LOCKED 2026-06-13)")
    emit(f"Dataset SHA-256 (verified): `{combined_hash}`")
    emit(f"Discovery cutoff: `{DISCOVERY_CUTOFF.strftime('%Y-%m-%dT%H:%M:%SZ')}`")
    emit(f"Seed: {RANDOM_SEED} | Resamples: {N_RESAMPLES} | Primary cost: {PRIMARY_COST} (8 bps/side)")
    emit("")
    emit(f"## GATE: {verdict}")
    emit("")
    emit("| Condition | Required | Observed | Met? |")
    emit("|-----------|----------|----------|------|")
    emit(
        f"| Gated expectancy_R | ≥ +0.05R | {_fmt(gated_exp)} | "
        f"{'YES' if cond_gated_min else 'NO'} |"
    )
    emit(
        f"| Gated − ungated | ≥ +0.05R | {_fmt(diff_exp)} | "
        f"{'YES' if cond_diff_min else 'NO'} |"
    )
    emit(
        f"| Gated vs shuffled p95 | > {_fmtf(p95_threshold)} | {_fmt(gated_exp)} | "
        f"{'YES' if cond_shuffled else 'NO'} |"
    )
    emit("")
    if verdict == "PARK":
        emit(
            "PARK rationale: one or more gate conditions not met. "
            "This is family #6 tested on this data class; a miss here strengthens "
            "the H1/H2 hypothesis (crypto-perp patterns exploitable at 4H scale may "
            "be exhausted within this universe). No Stage 3 run."
        )
    else:
        emit(
            "PASS: all three gate conditions met. Proceed to Stage 3 validation "
            "only after owner review of this report."
        )
    emit("")
    emit("---")
    emit("")
    emit("## Primary metrics (moderate 8 bps/side)")
    emit("")
    emit("| Metric | Value |")
    emit("|--------|-------|")
    emit(f"| Gated expectancy_R | {_fmt(gated_exp)} |")
    emit(f"| Ungated expectancy_R | {_fmt(ungated_exp)} |")
    emit(f"| Difference (primary) | {_fmt(diff_exp)} |")
    emit(f"| Pooled obs (discovery) | {n_total:,} |")
    emit(f"| LOW-VOL obs (gated active) | {n_low:,} |")
    emit(f"| HIGH-VOL obs (gated flat) | {n_high:,} |")
    emit("")
    emit("## Shuffled-regime baseline")
    emit("")
    emit(
        f"1000 resamples; per symbol, same LOW-VOL bar count chosen randomly "
        f"from all rebalance bars; seed = {RANDOM_SEED}."
    )
    emit("")
    emit("| Baseline stat | Value |")
    emit("|---------------|-------|")
    emit(f"| Shuffled mean | {_fmtf(shuffled_mean)} |")
    emit(f"| Shuffled p5   | {_fmtf(_pct(baseline_dist, 5.0))} |")
    emit(f"| Shuffled p50  | {_fmtf(_pct(baseline_dist, 50.0))} |")
    emit(f"| Shuffled p95  | {_fmtf(p95_threshold)} |")
    emit(f"| Observed gated percentile | {observed_pct:.1f}th |")
    emit("")
    emit("## Cost scenario diagnostics")
    emit("")
    emit("| Scenario | Gated | Ungated | Difference |")
    emit("|----------|-------|---------|------------|")
    for sc in ("optimistic", "moderate", "conservative"):
        g = gated_scenarios[sc]
        u = ungated_scenarios[sc]
        d = (g - u) if (g is not None and u is not None) else None
        primary_mark = " *(primary)*" if sc == PRIMARY_COST else ""
        emit(f"| {sc}{primary_mark} | {_fmt(g)} | {_fmt(u)} | {_fmt(d)} |")
    emit("")
    emit("## Per-symbol breakdown (diagnostic)")
    emit("")
    emit("| Symbol | N obs | N LOW | N HIGH | Gated exp | Ungated exp | Difference |")
    emit("|--------|-------|-------|--------|-----------|-------------|------------|")
    for sym in SYMBOLS:
        sym_obs = obs_by_sym[sym]
        n_sym = len(sym_obs)
        n_sym_low = sum(1 for o in sym_obs if o.regime == "LOW")
        n_sym_high = sum(1 for o in sym_obs if o.regime == "HIGH")
        g = obs_expectancy(sym_obs, gated=True, cost_bps=primary_bps)
        u = obs_expectancy(sym_obs, gated=False, cost_bps=primary_bps)
        d = (g - u) if (g is not None and u is not None) else None
        emit(
            f"| {sym} | {n_sym} | {n_sym_low} | {n_sym_high} | "
            f"{_fmt(g)} | {_fmt(u)} | {_fmt(d)} |"
        )
    emit("")
    emit("## High-vol bucket diagnostic")
    emit("")
    emit(
        "Ungated TSMOM expectancy on HIGH-VOL bars only "
        "(mechanism check: should be negative if gate is filtering bad bars)."
    )
    emit("")
    emit(f"| HIGH-VOL obs | Ungated exp (moderate) |")
    emit(f"|--------------|------------------------|")
    emit(f"| {len(high_obs):,} | {_fmt(high_ungated_exp)} |")
    emit("")
    emit("---")
    emit("")
    emit("*Report produced by `run_setup_h_discovery.py`. Do not modify manually.*")
    emit("")

    report_text = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    print(f"\nReport written: {REPORT_PATH}")
    print(f"GATE: {verdict}")


if __name__ == "__main__":
    main()
