"""Setup E — Stage 2 Discovery Run.

Implements the discovery pipeline exactly per the LOCKED pre-registration
(research/signal_observation/SETUP_E_PREREGISTRATION.md, 2026-06-13).

Discovery window: signal bar timestamp ≤ 2026-03-09T00:00Z
Primary metric:  expectancy_R @ 1.5R, post-cost moderate 8 bps,
                 pooled LONG+SHORT, non-overlapping set.
Gate:            expectancy_R ≥ +0.10R  AND  above 95th pct of random baseline
                 → PASS;  else PARK.
Baseline seed:   42 (CANONICAL — fixed at first run, §2.4).
"""
from __future__ import annotations

import json
import random
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import mean
from typing import NamedTuple

from research.signal_observation.indicators import atr as _compute_atr
from research.signal_observation.setup_e_detector import (
    LOOKAHEAD_CAP,
    ATR_PERIOD,
    OUTCOME_WINDOW_BARS,
    TARGET_R_VALUES,
    _ATR_BUFFER_MULT,
    _PERCENT_BUFFER,
    LiqBar,
    SetupESignal,
    detect_setup_e_signals,
    load_liq_csv,
)
from research.signal_observation.csv_loader import load_ohlcv_csv
from research.simcore.candles import Candle
from research.simcore.costs import SCENARIOS, cost_in_r
from research.simcore.models import Direction, FillPolicy, TradeSpec, TradeSim, InvalidTrade
from research.simcore.selection import select_non_overlapping
from research.simcore.simulator import simulate_trade
from research.simcore.timeutil import bar_duration

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _REPO_ROOT / "research" / "signal_observation" / "data" / "setup_e"
_SYMBOLS_FILE = _REPO_ROOT / "research" / "signal_observation" / "_selected_symbols.json"
_OUT_FILE = _REPO_ROOT / "research" / "signal_observation" / "SETUP_E_DISCOVERY_RESULT.md"

DISCOVERY_CUTOFF = datetime(2026, 3, 9, 0, 0, 0, tzinfo=UTC)
BASELINE_SEED: int = 42          # CANONICAL — recorded in output per §2.4
N_BASELINE_ITERS: int = 1_000
PRIMARY_TARGET_R = Decimal("1.5")
MODERATE_BPS = SCENARIOS["moderate"]    # Decimal("8")
GATE_MIN_EXPECTANCY = Decimal("0.10")
GATE_BASELINE_PCT = 95
_EXCLUDE_RADIUS = 5   # bars to exclude around each cascade bar


# ---------------------------------------------------------------------------
# Small data containers
# ---------------------------------------------------------------------------

class _SymSims(NamedTuple):
    symbol: str
    candles: list[Candle]
    signals_long: list[SetupESignal]
    signals_short: list[SetupESignal]
    all_sims: list[TradeSim]            # all valid sims before non-overlapping
    cascade_bars: set[int]              # all cascade aligned indices (full array)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sym_to_prefix(sym: str) -> str:
    """BTCUSDT_PERP.A → BTCUSDT_PERP_A (filename convention)."""
    return sym.replace(".", "_")


def _stop_price(
    cascade_extreme: Decimal,
    direction: Direction,
    entry_price: Decimal,
    atr20: Decimal | None,
) -> Decimal:
    atr_val = atr20 if atr20 is not None else Decimal("0")
    buffer = min(_PERCENT_BUFFER * entry_price, _ATR_BUFFER_MULT * atr_val)
    if direction == Direction.LONG:
        return cascade_extreme - buffer
    return cascade_extreme + buffer


def _percentile(vals: list[Decimal], pct: int) -> Decimal:
    if not vals:
        return Decimal("0")
    s = sorted(vals)
    rank = max(0, int(len(s) * pct / 100) - 1)
    return s[rank]


def _mean(vals: list[Decimal]) -> Decimal | None:
    if not vals:
        return None
    return sum(vals, Decimal("0")) / Decimal(len(vals))


def _expectancy(sims: list[TradeSim], target_r: Decimal, bps: Decimal) -> Decimal | None:
    """Mean post-cost R at target_r across sims."""
    vals: list[Decimal] = []
    for sim in sims:
        t = sim.targets.get(target_r)
        if t is None:
            continue
        c = cost_in_r(entry_price=sim.entry_price, initial_r=sim.initial_r, bps_per_side=bps)
        vals.append(t.final_r_gross - c)
    if not vals:
        return None
    return sum(vals, Decimal("0")) / Decimal(len(vals))


def _win_loss_flat(sims: list[TradeSim], target_r: Decimal) -> tuple[int, int, int]:
    wins = losses = flats = 0
    for sim in sims:
        t = sim.targets.get(target_r)
        if t is None:
            continue
        if t.outcome == "win":
            wins += 1
        elif t.outcome == "loss":
            losses += 1
        else:
            flats += 1
    return wins, losses, flats


# ---------------------------------------------------------------------------
# Data loading and signal detection
# ---------------------------------------------------------------------------

def _load_symbol(sym: str) -> tuple[list[Candle], list[LiqBar]] | None:
    pfx = _sym_to_prefix(sym)
    ohlcv_path = _DATA_DIR / f"{pfx}_ohlcv_4h.csv"
    liq_path = _DATA_DIR / f"{pfx}_liquidation_4h.csv"
    if not ohlcv_path.exists() or not liq_path.exists():
        print(f"  SKIP {sym}: missing data files", file=sys.stderr)
        return None
    candles = load_ohlcv_csv(ohlcv_path)
    liq = load_liq_csv(liq_path)
    return candles, liq


def _build_sym_sims(sym: str, candles: list[Candle], liq: list[LiqBar]) -> _SymSims:
    """Detect signals, build TradeSpecs, simulate, return per-symbol package."""
    dur = bar_duration(candles)
    atr_vals = _compute_atr(candles, period=ATR_PERIOD)

    sigs_long = detect_setup_e_signals(
        sym, candles, liq, Direction.LONG, discovery_cutoff_ts=DISCOVERY_CUTOFF
    )
    sigs_short = detect_setup_e_signals(
        sym, candles, liq, Direction.SHORT, discovery_cutoff_ts=DISCOVERY_CUTOFF
    )

    # Collect all cascade indices (from both directions, for baseline exclusion).
    # Re-detect without cutoff to get ALL cascade bars (used for exclusion only).
    sigs_long_all = detect_setup_e_signals(sym, candles, liq, Direction.LONG)
    sigs_short_all = detect_setup_e_signals(sym, candles, liq, Direction.SHORT)
    cascade_bars: set[int] = set()
    for s in sigs_long_all + sigs_short_all:
        cascade_bars.add(s.cascade_index)

    all_sims: list[TradeSim] = []
    for sig in sigs_long + sigs_short:
        entry_idx = sig.signal_index + 1
        if entry_idx >= len(candles):
            continue
        entry_price = candles[entry_idx].open
        stop = _stop_price(
            sig.cascade_extreme, sig.direction, entry_price, atr_vals[sig.signal_index]
        )
        spec = TradeSpec(
            symbol=sym,
            direction=sig.direction,
            signal_index=sig.signal_index,
            stop_price=stop,
            target_r_values=TARGET_R_VALUES,
            outcome_window_bars=OUTCOME_WINDOW_BARS,
            fill=FillPolicy.NEXT_BAR_OPEN,
        )
        result = simulate_trade(candles, spec, dur)
        if isinstance(result, TradeSim):
            all_sims.append(result)

    return _SymSims(
        symbol=sym,
        candles=candles,
        signals_long=sigs_long,
        signals_short=sigs_short,
        all_sims=all_sims,
        cascade_bars=cascade_bars,
    )


# ---------------------------------------------------------------------------
# Random baseline (§2.4)
# ---------------------------------------------------------------------------

def _eligible_bars(
    candles: list[Candle],
    cascade_bars: set[int],
    cutoff_ts: datetime,
    window_bars: int,
) -> list[int]:
    """Bars eligible for random entry: in discovery window, not near cascade."""
    excluded: set[int] = set()
    for ci in cascade_bars:
        for offset in range(-_EXCLUDE_RADIUS, _EXCLUDE_RADIUS + 1):
            excluded.add(ci + offset)
    eligible = [
        i for i in range(len(candles))
        if candles[i].timestamp <= cutoff_ts
        and i + window_bars + 1 <= len(candles)   # room for entry + window
        and i not in excluded
    ]
    return eligible


def _run_baseline(
    sym_sims_list: list[_SymSims],
    seed: int,
    n_iters: int,
) -> list[Decimal]:
    """Return 1000 expectancy_R @ 1.5R values for the random baseline.

    Per symbol/direction: draw same N as raw signal count from eligible bars,
    use actual initial_r values from that bucket as risk distances.
    """
    rng = random.Random(seed)

    # Pre-compute per-symbol eligible bars and risk distance pools.
    sym_data: dict[str, dict] = {}
    for ss in sym_sims_list:
        dur = bar_duration(ss.candles)
        eligible = _eligible_bars(
            ss.candles, ss.cascade_bars, DISCOVERY_CUTOFF, OUTCOME_WINDOW_BARS
        )
        # Build risk_distance pools per direction from actual sims.
        risk_long: list[Decimal] = [s.initial_r for s in ss.all_sims
                                     if s.spec.direction == Direction.LONG]
        risk_short: list[Decimal] = [s.initial_r for s in ss.all_sims
                                      if s.spec.direction == Direction.SHORT]
        sym_data[ss.symbol] = {
            "candles": ss.candles,
            "dur": dur,
            "eligible": eligible,
            "n_long": len(ss.signals_long),
            "n_short": len(ss.signals_short),
            "risk_long": risk_long,
            "risk_short": risk_short,
        }

    results: list[Decimal] = []

    for _ in range(n_iters):
        iter_r_vals: list[Decimal] = []

        for sym, d in sym_data.items():
            candles: list[Candle] = d["candles"]
            eligible: list[int] = d["eligible"]
            dur: timedelta = d["dur"]

            if not eligible:
                continue

            for direction, n, risk_pool in (
                (Direction.LONG, d["n_long"], d["risk_long"]),
                (Direction.SHORT, d["n_short"], d["risk_short"]),
            ):
                if n == 0 or not risk_pool:
                    continue
                for _ in range(n):
                    sig_idx = rng.choice(eligible)
                    initial_r = rng.choice(risk_pool)
                    entry_price = candles[sig_idx + 1].open
                    if direction == Direction.LONG:
                        stop = entry_price - initial_r
                    else:
                        stop = entry_price + initial_r
                    spec = TradeSpec(
                        symbol=sym,
                        direction=direction,
                        signal_index=sig_idx,
                        stop_price=stop,
                        target_r_values=(PRIMARY_TARGET_R,),
                        outcome_window_bars=OUTCOME_WINDOW_BARS,
                        fill=FillPolicy.NEXT_BAR_OPEN,
                    )
                    res = simulate_trade(candles, spec, dur)
                    if isinstance(res, TradeSim):
                        t = res.targets.get(PRIMARY_TARGET_R)
                        if t is not None:
                            c = cost_in_r(entry_price=res.entry_price, initial_r=res.initial_r, bps_per_side=MODERATE_BPS)
                            iter_r_vals.append(t.final_r_gross - c)

        exp = _mean(iter_r_vals)
        if exp is not None:
            results.append(exp)

    return results


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def _pct_rank(val: Decimal, distribution: list[Decimal]) -> int:
    """Fraction of distribution values strictly below val, as percent."""
    if not distribution:
        return 0
    below = sum(1 for v in distribution if v < val)
    return round(100 * below / len(distribution))


def _fmt(d: Decimal | None, places: int = 4) -> str:
    if d is None:
        return "N/A"
    return f"{d:+.{places}f}" if d < 0 else f"+{d:.{places}f}"


def _build_report(
    non_overlapping: list[TradeSim],
    all_sims: list[TradeSim],
    sims_long: list[TradeSim],
    sims_short: list[TradeSim],
    baseline: list[Decimal],
    raw_signal_counts: dict[str, int],  # {"long": N, "short": N, "total": N}
) -> str:
    n_all_raw = raw_signal_counts["total"]
    n_no = len(non_overlapping)

    exp_moderate = _expectancy(non_overlapping, PRIMARY_TARGET_R, MODERATE_BPS)
    exp_optimistic = _expectancy(non_overlapping, PRIMARY_TARGET_R, SCENARIOS["optimistic"])
    exp_conservative = _expectancy(non_overlapping, PRIMARY_TARGET_R, SCENARIOS["conservative"])

    baseline_p95 = _percentile(baseline, GATE_BASELINE_PCT)
    pct_rank = _pct_rank(exp_moderate or Decimal("0"), baseline)

    gate_min_met = (exp_moderate is not None) and (exp_moderate >= GATE_MIN_EXPECTANCY)
    gate_baseline_met = (exp_moderate is not None) and (exp_moderate > baseline_p95)
    gate = "PASS" if (gate_min_met and gate_baseline_met) else "PARK"

    wins, losses, flats = _win_loss_flat(non_overlapping, PRIMARY_TARGET_R)
    n_valid = wins + losses + flats

    def pct_str(n: int, total: int) -> str:
        if total == 0:
            return "0%"
        return f"{100*n/total:.1f}%"

    lines: list[str] = []
    a = lines.append

    a("# Setup E — Stage 2 Discovery Result")
    a("")
    a(f"**GATE: {gate}**")
    a("")
    a(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    a(f"Pre-registration: LOCKED 2026-06-13 — commit 0b71d9b")
    a(f"Discovery window: signal bar timestamp ≤ 2026-03-09T00:00Z")
    a(f"Baseline seed: **{BASELINE_SEED}** (CANONICAL — fixed at first run, §2.4)")
    a(f"Baseline iterations: {N_BASELINE_ITERS}")
    a("")

    a("## Gate Verdict")
    a("")
    a("Primary metric: expectancy_R @ 1.5R, post-cost moderate (8 bps/side),")
    a("pooled LONG+SHORT, non-overlapping set.")
    a("")
    a(f"| Criterion | Required | Actual | Met? |")
    a(f"|---|---|---|---|")
    a(f"| expectancy_R ≥ +0.10R | +0.10R | {_fmt(exp_moderate)} | {'YES ✓' if gate_min_met else 'NO ✗'} |")
    a(f"| above baseline p95 | > {_fmt(baseline_p95)} | {_fmt(exp_moderate)} | {'YES ✓' if gate_baseline_met else 'NO ✗'} |")
    a("")
    a(f"**GATE: {gate}**")
    a("")

    a("## Signal Counts")
    a("")
    a(f"| | Count |")
    a(f"|---|---|")
    a(f"| Raw signals detected (discovery window, both directions) | {n_all_raw} |")
    a(f"| &nbsp;&nbsp;LONG | {raw_signal_counts['long']} |")
    a(f"| &nbsp;&nbsp;SHORT | {raw_signal_counts['short']} |")
    a(f"| Valid simulations (after simcore filtering) | {len(all_sims)} |")
    a(f"| Non-overlapping set (primary metric) | {n_no} |")
    a("")

    a("## Primary Metric — Expectancy by Cost Scenario")
    a("")
    a("Non-overlapping set, 1.5R target.")
    a("")
    a(f"| Cost scenario | bps/side | N | expectancy_R | Win% | Loss% | Flat% |")
    a(f"|---|---|---|---|---|---|---|")
    for label, bps in [
        ("Optimistic", SCENARIOS["optimistic"]),
        ("Moderate [PRIMARY]", MODERATE_BPS),
        ("Conservative", SCENARIOS["conservative"]),
    ]:
        exp = _expectancy(non_overlapping, PRIMARY_TARGET_R, bps)
        w, l, f = _win_loss_flat(non_overlapping, PRIMARY_TARGET_R)
        tot = w + l + f
        a(f"| {label} | {bps} | {tot} | {_fmt(exp)} | {pct_str(w,tot)} | {pct_str(l,tot)} | {pct_str(f,tot)} |")
    a("")

    a("## Random Baseline (§2.4)")
    a("")
    a(f"1000 resamples, seed={BASELINE_SEED} (canonical). Per symbol/direction: same N as")
    a("raw signal count, random entry bars NOT within 5 bars of any cascade episode,")
    a("risk distances drawn from actual signal pool, same 1.5R target and 12-bar window.")
    a("")
    if baseline:
        bs = sorted(baseline)
        a(f"| Statistic | Expectancy_R |")
        a(f"|---|---|")
        a(f"| min | {_fmt(bs[0])} |")
        a(f"| p5 | {_fmt(_percentile(baseline, 5))} |")
        a(f"| p25 | {_fmt(_percentile(baseline, 25))} |")
        a(f"| median | {_fmt(_percentile(baseline, 50))} |")
        a(f"| p75 | {_fmt(_percentile(baseline, 75))} |")
        a(f"| p95 | {_fmt(baseline_p95)} |")
        a(f"| max | {_fmt(bs[-1])} |")
        a("")
        a(f"Actual expectancy_R {_fmt(exp_moderate)} is at the **{pct_rank}th percentile** of the baseline.")
        a(f"Gate requires > p95 ({_fmt(baseline_p95)}): {'MET ✓' if gate_baseline_met else 'NOT MET ✗'}")
    else:
        a("_No baseline data._")
    a("")

    a("## Target-R Diagnostics (moderate cost, non-overlapping)")
    a("")
    a(f"| Target | N | Win% | Loss% | Flat% | expectancy_R |")
    a(f"|---|---|---|---|---|---|")
    for tr in TARGET_R_VALUES:
        exp_t = _expectancy(non_overlapping, tr, MODERATE_BPS)
        w, l, f = _win_loss_flat(non_overlapping, tr)
        tot = w + l + f
        marker = " **[PRIMARY]**" if tr == PRIMARY_TARGET_R else ""
        a(f"| {tr}R{marker} | {tot} | {pct_str(w,tot)} | {pct_str(l,tot)} | {pct_str(f,tot)} | {_fmt(exp_t)} |")
    a("")

    a("## MFE / MAE Diagnostics (primary metric, 1.5R, non-overlapping)")
    a("")
    a("Diagnostic only — no trading conclusions at Stage 2.")
    a("")
    maes = [sim.targets[PRIMARY_TARGET_R].mae_r for sim in non_overlapping
            if PRIMARY_TARGET_R in sim.targets]
    mfes = [sim.targets[PRIMARY_TARGET_R].mfe_r for sim in non_overlapping
            if PRIMARY_TARGET_R in sim.targets]
    a(f"| Metric | Mean | Median | p25 | p75 |")
    a(f"|---|---|---|---|---|")
    for label, vals in [("MAE_R (max adverse)", maes), ("MFE_R (max favourable)", mfes)]:
        m = _mean(vals)
        med = _percentile(vals, 50)
        p25 = _percentile(vals, 25)
        p75 = _percentile(vals, 75)
        a(f"| {label} | {_fmt(m)} | {_fmt(med)} | {_fmt(p25)} | {_fmt(p75)} |")
    a("")

    a("## Per-Direction Breakdown (diagnostic)")
    a("")
    a(f"| Direction | Raw signals | Valid sims | Non-overlapping | expectancy_R @ 1.5R |")
    a(f"|---|---|---|---|---|")
    no_long = [s for s in non_overlapping if s.spec.direction == Direction.LONG]
    no_short = [s for s in non_overlapping if s.spec.direction == Direction.SHORT]
    for label, direction, sigs_raw in [
        ("LONG", Direction.LONG, raw_signal_counts["long"]),
        ("SHORT", Direction.SHORT, raw_signal_counts["short"]),
    ]:
        valid = [s for s in all_sims if s.spec.direction == direction]
        no_dir = [s for s in non_overlapping if s.spec.direction == direction]
        exp_dir = _expectancy(no_dir, PRIMARY_TARGET_R, MODERATE_BPS)
        a(f"| {label} | {sigs_raw} | {len(valid)} | {len(no_dir)} | {_fmt(exp_dir)} |")
    a(f"| Combined | {n_all_raw} | {len(all_sims)} | {n_no} | {_fmt(exp_moderate)} |")
    a("")

    a("## Methodology Notes")
    a("")
    a("- Signal definition: §2.3 of locked pre-registration.")
    a("- Discovery window: signal bar timestamp ≤ 2026-03-09T00:00Z (single cross-symbol cutpoint).")
    a("- Non-overlapping: `simcore.selection.select_non_overlapping` at 1.5R, per symbol.")
    a("- Baseline: raw signal count per bucket (before non-overlapping selection), 1000 iterations,")
    a(f"  seed={BASELINE_SEED} (canonical, recorded here per §2.4 since no seed was fixed at pre-registration lock).")
    a("- Cost formula: `cost_in_r(entry_price, initial_r, bps) = 2×bps/10000 × entry_price / initial_r`.")
    a("- All outcomes via `research.simcore.simulator.simulate_trade` (NEXT_BAR_OPEN).")
    a("")
    a("---")
    a("")
    a("Constitution stage: 2 (Discovery). Do NOT proceed to Stage 3 without owner review.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("Setup E — Stage 2 Discovery Run")
    print(f"Discovery cutoff: {DISCOVERY_CUTOFF.isoformat()}")
    print(f"Baseline seed: {BASELINE_SEED} (canonical)")
    print()

    # Load symbols.
    symbols: list[str] = json.loads(_SYMBOLS_FILE.read_text(encoding="utf-8"))
    print(f"Symbols: {len(symbols)}")

    # Process each symbol.
    sym_sims_list: list[_SymSims] = []
    raw_long_total = 0
    raw_short_total = 0

    for sym in symbols:
        loaded = _load_symbol(sym)
        if loaded is None:
            continue
        candles, liq = loaded
        ss = _build_sym_sims(sym, candles, liq)
        sym_sims_list.append(ss)
        n_l = len(ss.signals_long)
        n_s = len(ss.signals_short)
        raw_long_total += n_l
        raw_short_total += n_s
        print(f"  {sym}: LONG={n_l}  SHORT={n_s}  valid_sims={len(ss.all_sims)}")

    all_sims: list[TradeSim] = []
    for ss in sym_sims_list:
        all_sims.extend(ss.all_sims)

    print(f"\nTotal valid sims: {len(all_sims)}")

    # Non-overlapping selection at 1.5R.
    non_overlapping = select_non_overlapping(all_sims, target_r=PRIMARY_TARGET_R)
    print(f"Non-overlapping set: {len(non_overlapping)}")

    # Primary metric.
    exp_mod = _expectancy(non_overlapping, PRIMARY_TARGET_R, MODERATE_BPS)
    print(f"Primary expectancy_R (moderate, 1.5R): {_fmt(exp_mod)}")

    # Baseline.
    print(f"\nRunning random baseline ({N_BASELINE_ITERS} iterations, seed={BASELINE_SEED})...")
    baseline = _run_baseline(sym_sims_list, seed=BASELINE_SEED, n_iters=N_BASELINE_ITERS)
    print(f"Baseline complete: {len(baseline)} iterations.")
    bp95 = _percentile(baseline, GATE_BASELINE_PCT)
    print(f"Baseline p95: {_fmt(bp95)}")

    gate_min_met = (exp_mod is not None) and (exp_mod >= GATE_MIN_EXPECTANCY)
    gate_baseline_met = (exp_mod is not None) and (exp_mod > bp95)
    gate = "PASS" if (gate_min_met and gate_baseline_met) else "PARK"
    print(f"\n*** GATE: {gate} ***")

    # Build and write report.
    sims_long = [s for s in all_sims if s.spec.direction == Direction.LONG]
    sims_short = [s for s in all_sims if s.spec.direction == Direction.SHORT]
    report = _build_report(
        non_overlapping=non_overlapping,
        all_sims=all_sims,
        sims_long=sims_long,
        sims_short=sims_short,
        baseline=baseline,
        raw_signal_counts={
            "long": raw_long_total,
            "short": raw_short_total,
            "total": raw_long_total + raw_short_total,
        },
    )

    _OUT_FILE.write_text(report, encoding="utf-8")
    print(f"\nReport written: {_OUT_FILE}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
