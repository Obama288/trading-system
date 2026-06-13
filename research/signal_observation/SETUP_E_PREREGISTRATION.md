# Setup E — Pre-Registration

Family: Post-Liquidation Exhaustion Reversal (Setup E, branch per
SETUP_E_HYPOTHESIS.md)
Status: LOCKED 2026-06-13 — no changes permitted; any modification requires a
new pre-registration (constitution Stage 1).
Governed by: docs/RESEARCH_CONSTITUTION.md v1.1.

## 2.1 Hypothesis and mechanism

Hypothesis (one sentence): after a liquidation cascade — a burst of forced
liquidations in one direction that then subsides — price mean-reverts against
the cascade direction over the following 1–2 days, because the forced flow
that drove the move is exhausted while the dislocation it created remains.

Mechanism / who pays: liquidated traders transact at forced, non-discretionary
prices (they pay the dislocation); late momentum entrants who chase the
cascade move provide the exit liquidity for the reversal. Both counterparties
are structurally constrained: the first cannot choose timing, the second
systematically enters after forced flow has already peaked.

Scope note: this pre-registration tests ONLY the exhaustion-reversal branch.
Continuation and overshoot branches remain separate candidates requiring
their own pre-registrations (per the hypothesis note's explicit separation).

## 2.2 Primary metric and gate

- Primary metric: post-cost expectancy_R (simcore, NEXT_BAR_OPEN fill,
  moderate cost scenario 8 bps/side), flats marked-to-market, computed on the
  non-overlapping observation set (constitution 3.7/3.8).
- Gate threshold (discovery, Stage 2): expectancy_R ≥ +0.10R AND above the
  random-baseline margin in 2.4.
- Gate threshold (validation, Stage 3): expectancy_R ≥ 0 with direction
  consistent with discovery.
- Everything else (per-symbol splits, MFE/MAE, cascade-size sensitivity,
  session breakdowns) is diagnostic-only.

## 2.3 Signal definition (frozen at lock)

All parameters below are part of the lock; sensitivity values are listed in
the variant budget (2.5), not tuned post hoc.

- Universe: the 20 symbols frozen in
  `research/signal_observation/_selected_symbols.json` (Coinalyze perpetual
  IDs): BTCUSDT_PERP.A, ETHUSDT_PERP.A, SOLUSDT_PERP.A, BNBUSDT_PERP.A,
  XRPUSDT_PERP.A, DOGEUSDT_PERP.A, ADAUSDT_PERP.A, AVAXUSDT_PERP.A,
  LINKUSDT_PERP.A, DOTUSDT_PERP.A, LTCUSDT_PERP.A, UNIUSDT_PERP.A,
  ATOMUSDT_PERP.A, FILUSDT_PERP.A, ARBUSDT_PERP.A, OPUSDT_PERP.A,
  APTUSDT_PERP.A, SUIUSDT_PERP.A, TRXUSDT_PERP.A, TONUSDT_PERP.A.
- Timeframe: 4H (aligned with simcore conventions and Coinalyze retention).
- Cascade bar (for LONG reversal signal): long-liquidation notional in the
  bar > 95th percentile of that symbol's trailing 30-day long-liquidation
  distribution, AND bar close < bar open (forced selling visible in price).
  SHORT reversal is the mirror (short-liquidation burst, up bar).
- Exhaustion/signal bar (LONG): the first subsequent bar where long-liquidation
  notional falls below the trailing 30-day **25th percentile** of that symbol's
  long-liq distribution. signal_index = that bar; entry per constitution at
  next bar open. SHORT mirror: short-liq notional falls below the trailing
  30-day 25th percentile of that symbol's short-liq distribution.
  Rationale: the hypothesis is about exhaustion of forced flow; a deeper liq
  drop (25th pct) operationalizes the mechanism better than the median.
  Feasibility diagnostic confirmed this retains 544 discovery / 410 validation
  episodes, well above the 80/40 minimums
  (SETUP_E_FEASIBILITY_REPORT.md §Episode Structure Diagnostic §5).
- Stop: cascade extreme (lowest low of the cascade-to-signal span for LONG;
  mirror for SHORT) minus/plus the setup_b-style buffer
  min(0.1% of entry, 0.25×ATR20).
- Targets: 1R / 1.5R / 2R (primary gate evaluated at 1.5R; 1R and 2R
  diagnostic).
- Outcome window: 12 bars (48h) — exhaustion is hypothesized as short-horizon.
- One observation per cascade episode; overlap removed per constitution 3.8.

## 2.4 Random baseline

Per symbol: N_signal random entry bars drawn uniformly from bars that are NOT
within 5 bars of any cascade episode, same direction mix, same stop/target/
window machinery via simcore. 1000 resamples, fixed seed recorded at lock.
Margin requirement: primary-variant expectancy_R must exceed the 95th
percentile of the baseline expectancy distribution.

## 2.5 Multiple-testing budget

Pre-named PRIMARY variant: pooled across the full universe, both directions
(symmetric logic), thresholds exactly as in 2.3, target 1.5R.
Planned non-primary looks (diagnostic only): cascade percentile ∈ {90, 99};
exhaustion threshold ∈ {25th pct, median}; window ∈ {6, 18} bars; per-symbol
and per-direction splits; BTC+ETH-only subset.
V = 1 primary + 8 sensitivity + 2 splits family ≈ 11 declared looks. Any
non-primary look may be promoted only via a fresh pre-registration treating
its evidence as Stage 0 (constitution 2.5).

## 2.6 Windows and sample minimums

- Discovery window: signal bar timestamp ≤ 2026-03-09T00:00Z. Single
  cross-symbol cutpoint (adopted over per-symbol 70/30 splits for cleaner
  bookkeeping; represents the median of per-symbol 70% cutpoints across the
  universe).
- Validation window: signal bar timestamp > 2026-03-09T00:00Z, non-overlapping
  with discovery.
- Recent-rerun: the most recent ~3 months of Coinalyze 4H data available at
  rerun time. KNOWN LIMITATION (decided by owner at lock): the constitution
  default of 12 months is impossible — Coinalyze free-plan liquidation history
  starts ~mid-2025, leaving only ~3 months of data beyond the validation window
  at lock time. Because this is a weakened Stage 4, final out-of-regime
  confirmation shifts additional weight onto Stage 5 paper trading results.
- Dataset SHA-256 hashes: recorded in
  `research/signal_observation/SETUP_E_FEASIBILITY_REPORT.md` §Dataset
  SHA-256 Hashes (40 hashes, 20 symbols × 2 datasets), binding to commit
  f03bc6b. Constitution v1.1 hash-binding requirement satisfied.
- Sample minimums: discovery ≥ 80, validation ≥ 40 non-overlapping
  observations (constitution defaults). Both met under the locked exhaustion
  definition (25th pct): 544 discovery / 410 validation episodes. Lowering
  minimums after seeing outcome metrics is prohibited.

## 2.7 Kill criteria

- Stage 2: gate miss → family parked; one re-registration permitted only with
  a materially different mechanism statement.
- Stage 3: validation expectancy < 0 or sign flip vs discovery → RETIRE.
- Stage 4: recent-rerun expectancy < 0 → park as historical-only (Setup C
  precedent).
- Stage 5 (paper): constitution v1.1 defaults (−0.15R after 30 trades / 10R
  drawdown / 90 days) + execution audit on frozen commit + runtime hash check.
