# Setup E — Pre-Registration (DRAFT)

Family: Post-Liquidation Exhaustion Reversal (Setup E, branch per
SETUP_E_HYPOTHESIS.md)
Status: DRAFT — blocked on (a) owner source-access approval (Coinalyze free
API key path), (b) feasibility pass fields marked TBD-F below.
Governed by: docs/RESEARCH_CONSTITUTION.md v1.1. This document follows the
section 2 template. Once both blockers clear and TBD-F fields are filled,
this file is committed as SETUP_E_PREREGISTRATION.md and LOCKED — any change
afterwards is a new pre-registration.

Sequencing note (constitution 2.x + v1.1 amendment): feasibility-only data
inspection (coverage, retention, quality report via research/simcore/quality)
is permitted before locking; outcome metrics are not. Dataset SHA-256 hashes
are recorded at lock time, before any Stage 2 run.

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

- Universe: top-20 Coinalyze-supported liquid perpetuals (exact instrument
  list resolved and frozen at lock — TBD-F).
- Timeframe: 4H (aligned with simcore conventions and Coinalyze retention).
- Cascade bar (for LONG reversal signal): long-liquidation notional in the
  bar > 95th percentile of that symbol's trailing 30-day long-liquidation
  distribution, AND bar close < bar open (forced selling visible in price).
  SHORT reversal is the mirror (short-liquidation burst, up bar).
- Exhaustion/signal bar: the first subsequent bar where liquidation notional
  falls below the trailing 30-day median. signal_index = that bar; entry per
  constitution at next bar open.
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

- Discovery window: [TBD-F start, TBD-F end] — earliest 70% of available
  contiguous Coinalyze 4H history at lock time.
- Validation window: [TBD-F] — the following 30%, non-overlapping.
- Recent-rerun: last 12 months at rerun time (constitution default).
- Dataset SHA-256 hashes: [TBD-F, recorded at lock per constitution v1.1].
- Sample minimums: constitution defaults (discovery ≥ 80, validation ≥ 40
  non-overlapping observations). Feasibility risk: cascade episodes may be
  too rare on 20 symbols to reach 80. If the feasibility pass shows the
  expected count is below minimums, the OWNER decides before lock: widen the
  universe, lengthen history, or pre-register lower minimums with written
  justification. Lowering minimums after seeing outcome metrics is prohibited.

## 2.7 Kill criteria

- Stage 2: gate miss → family parked; one re-registration permitted only with
  a materially different mechanism statement.
- Stage 3: validation expectancy < 0 or sign flip vs discovery → RETIRE.
- Stage 4: recent-rerun expectancy < 0 → park as historical-only (Setup C
  precedent).
- Stage 5 (paper): constitution v1.1 defaults (−0.15R after 30 trades / 10R
  drawdown / 90 days) + execution audit on frozen commit + runtime hash check.

## Owner decisions required before lock

1. Source access: approve use of the free Coinalyze API key path for
   liquidation history retrieval (gate from
   SETUP_E_COINALYZE_EXPLORE_SOURCE_SELECTION.md).
2. After feasibility pass: confirm universe list, windows, hashes, and the
   2.6 sample-minimum decision if episode counts come up short.
