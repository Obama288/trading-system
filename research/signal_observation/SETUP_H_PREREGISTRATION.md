# Setup H — Pre-Registration (DRAFT)

Family: Regime-Gated Time-Series Momentum (TSMOM restricted to low-volatility
regime). Successor hypothesis to Setup C; NOT a restart of Setup C.
Status: DRAFT — blocked on feasibility pass (alt-coin data availability +
quality + per-symbol regime/observation counts; ZEC perp liquidity check).
Governed by: docs/RESEARCH_CONSTITUTION.md v1.2. Follows §2 template.

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

Universe (held-out — symbols Setup C never used): liquid USDT perpetuals
EXCLUDING BTC and ETH. Proposed: SOL, BNB, XRP, DOGE, ADA, AVAX, LINK, DOT,
plus ZEC (long history; INCLUDE only if feasibility confirms adequate perp
liquidity — flag a cost caveat if thin). Final list frozen at lock from the
feasibility pass.

Timeframe: 4H (matches Setup C and simcore conventions).
Outcome handling: TSMOM is a continuous-exposure signal, not a stop/target
setup; evaluate per-rebalance forward return to next rebalance via simcore
exposure accounting, post-cost. Cost charged on every position change (entering
or flipping), so the gate's reduction in trade count is correctly credited/
debited. (Implementation detail for the runner; the cost test below depends on
it being correct.)

## 2.4 Random baseline
Baseline = the UNGATED Setup C TSMOM on the same universe and period (this is
the thing the gate must beat), PLUS a shuffled-regime control: the same number
of "active" bars chosen at random instead of by the low-vol rule, 1000
resamples, fixed integer seed recorded here at lock [TBD-LOCK]. The gate must
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
- Discovery: earliest ~70% of available 4H history for the frozen universe
  [TBD-F at lock].
- Validation: following ~30%, non-overlapping [TBD-F].
- Recent-rerun (Stage 4): last 12 months at rerun time (full history available
  for these alts, so the constitution default holds — unlike Setup E).
- Dataset SHA-256: recorded at lock [TBD-F].
- Minimums: constitution defaults, counted as non-overlapping rebalance
  observations (discovery ≥ 80, validation ≥ 40). With 9 symbols and 6-bar
  rebalance over years of history this is comfortable; feasibility confirms.

## 2.7 Kill criteria
- Discovery gate miss → PARK. Given this is family #6, a miss is a strong
  signal toward H1/H2 (data class exhausted) — record that reading.
- Validation: gated ≤ ungated, or sign flip → RETIRE.
- Stage 4: recent-rerun gated expectancy < 0 → historical-only.
- Stage 5: constitution v1.1/v1.2 defaults + execution audit + hash check.

## Owner decisions required before lock
1. Confirm universe after feasibility (esp. ZEC liquidity / cost caveat).
2. Confirm the cost-test result: before locking, the feasibility/diagnostic
   must show the gated signal's per-rebalance edge can plausibly exceed
   round-trip cost — if not, do not lock (the Setup F lesson).
3. Fix the integer baseline seed (2.4) at lock.
