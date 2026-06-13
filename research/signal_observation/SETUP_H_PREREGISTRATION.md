# Setup H — Pre-Registration

Family: Regime-Gated Time-Series Momentum (TSMOM restricted to low-volatility
regime). Successor hypothesis to Setup C; NOT a restart of Setup C.
Status: LOCKED 2026-06-13 — no changes permitted; any modification requires
a new pre-registration (constitution Stage 1).
Governed by: docs/RESEARCH_CONSTITUTION.md v1.3. Follows §2 template.

## Campaign comparison-budget note (constitution §2.5, v1.2)
This is the SIXTH hypothesis family tested on crypto-perp data in this campaign
(after A, B, C, funding-normalization, E). Five failed. Per the cumulative
comparison budget, a PASS here must be read against that count: with six
independent looks, the probability that one clears a gate by chance is
non-trivial. The gate margins and baseline below are set with that in mind, and
a PASS should be treated as "promising, not proven" pending Stage 4.

## 2.1 Hypothesis and mechanism

Hypothesis (one sentence): time-series momentum (Setup C's 40-bar signal)
produces positive post-cost expectancy ONLY in a low-volatility regime, and
gating it to that regime yields higher expectancy than the ungated signal.

Mechanism / who pays: in calm markets, trends develop and persist gradually —
the momentum signal captures genuine continuation. In high-volatility regimes,
moves are sharp and mean-reverting (liquidation cascades, squeezes, panic
reversals); the same momentum signal enters late and is run over by whoever is
reversing the move. The regime gate removes the environment where the TSMOM
mechanism structurally breaks, rather than removing "bad numbers".

Why this is a hypothesis and not a fit: Setup C's C4/C5 diagnostics observed
high_vol-negative / low_vol-positive returns — BUT C5 found this pattern in the
validation split only, not discovery. Therefore C4/C5 are treated here as
REASON FOR PLAUSIBILITY ONLY, never as evidence. The hypothesis is tested on
symbols Setup C never touched (see 2.3), so the BTC/ETH-derived observation
cannot be the thing being confirmed.

## 2.2 Primary metric and gate

- Primary metric: the DIFFERENCE in post-cost expectancy_R between the
  regime-gated signal and the ungated signal, on the same symbols/period
  (simcore, moderate 8 bps, flats marked-to-market, non-overlapping).
  The hypothesis is about the gate's *improvement*, not absolute TSMOM return.
- Discovery gate: gated expectancy_R ≥ +0.05R AND gated minus ungated ≥ +0.05R
  AND gated above the random-baseline 95th percentile (see 2.4).
- Validation gate: gated expectancy_R ≥ 0 AND gated > ungated, direction
  consistent with discovery.
- Diagnostics only: per-symbol breakdown, the high_vol bucket's own
  expectancy, sensitivity to lookback/threshold.

## 2.3 Signal definition (frozen at lock)

Base signal (inherited from Setup C design lock, unchanged):
- 40-bar close-to-close lookback return; long if > 0, short if < 0.
- Rebalance every 6 bars; signal evaluated only on rebalance bars.
- Volatility targeting via ATR20/close (as Setup C).

Regime gate (the new, pre-registered element):
- Regime proxy = ATR20/close (same vol measure the family already uses).
- A rebalance bar is LOW-VOL if its ATR20/close is below the trailing 180-bar
  median of ATR20/close for that symbol; HIGH-VOL otherwise.
- Gated signal: take the TSMOM position ONLY on low-vol rebalance bars; flat
  on high-vol bars. Relative-to-own-median (not an absolute threshold) so the
  gate transfers across symbols of different baseline volatility.

Universe (held-out — symbols Setup C never used): SOL, BNB, XRP, DOGE, ADA,
AVAX, LINK, DOT, ZEC. Final. ZEC INCLUDED: avg daily quote vol $158.9M
(feasibility commit 7412f1a confirmed adequate liquidity).

Timeframe: 4H (matches Setup C and simcore conventions).
Outcome handling: TSMOM is a continuous-exposure signal, not a stop/target
setup; evaluate per-rebalance forward return to next rebalance via simcore
exposure accounting, post-cost. Cost charged on every position change (entering
or flipping), so the gate's reduction in trade count is correctly credited/
debited. (Implementation detail for the runner; the cost test below depends on
it being correct.)

Cost assumption: 8 bps/side moderate is taken as a written assumption (not a
measured spread). Justified because TSMOM rebalances every 6 bars (~daily) and
the regime gate further reduces trade count, so round-trip cost is amortized
over multi-day holds — the intraday cost wall that sank Setup F does not apply
here.

## 2.4 Random baseline
Baseline = the UNGATED Setup C TSMOM on the same universe and period (this is
the thing the gate must beat), PLUS a shuffled-regime control: the same number
of "active" bars chosen at random instead of by the low-vol rule, 1000
resamples, fixed integer seed = 69 (constitution v1.3 default). The gate must
beat BOTH: the ungated signal (shows the gate adds value) and the
random-active-bar control at p95 (shows it's the *regime*, not just trading
fewer bars).

## 2.5 Multiple-testing budget
Primary variant: 40-bar lookback, 180-bar median regime split, low-vol-only,
pooled across the frozen universe. V (declared looks): 1 primary + sensitivity
{lookback 20/60; median window 120/240; threshold 25th/75th pct} = 1 + 6
diagnostic. Non-primary looks are diagnostic; promotion requires a fresh
Stage-0 pre-registration AND adds to the campaign budget above.

## 2.6 Windows and sample minimums
- Discovery: bars with open_time ≤ 2024-09-24T04:00:00Z.
- Validation: bars with open_time > 2024-09-24T04:00:00Z, non-overlapping.
- Recent-rerun (Stage 4): last 12 months at rerun time (full history available
  for these alts, so the constitution default holds — unlike Setup E).
- Dataset SHA-256: 30d2027f9af6f191dfa7ff0e572b60c28b91f0c68ea8f28ec021f292b5788d05
  (combined hash of all 9 CSVs, sorted by symbol; bound to commit 7412f1a).
- Minimums: constitution defaults, counted as non-overlapping rebalance
  observations (discovery ≥ 80, validation ≥ 40). Feasibility confirmed:
  pooled discovery 14,160 obs / pooled validation 5,640 obs; per-symbol
  minimums all exceeded by ≥ 15×.

## 2.7 Kill criteria
- Discovery gate miss → PARK. Given this is family #6, a miss is a strong
  signal toward H1/H2 (data class exhausted) — record that reading.
- Validation: gated ≤ ungated, or sign flip → RETIRE.
- Stage 4: recent-rerun gated expectancy < 0 → historical-only.
- Stage 5: constitution v1.3 defaults + execution audit + hash check.
