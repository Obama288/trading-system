# Signal Observation - Research State

Purpose: compact current state for Stage 54-SQ signal-quality research. Full
artifacts and historical docs remain available, but routine startup should begin
here plus `docs/CURRENT_STATE.md` and `docs/BOUNDARIES.md`.

## Current Track

- Stage 54-SQ is research-only signal-quality observation.
- Data source: local/public OHLCV artifacts only unless a future owner-approved
  task explicitly authorizes download.
- Active family: Setup C / TSMOM volatility-targeted.
- Current status: PASS_CANDIDATE research-only after C2 diagnostics.
- C3 diagnostics are present in local commit `866f201`, not pushed relative to
  `origin/main` at time of writing.

## Retired Family

- Price-action continuation family is retired as primary direction.
- Retired attempts include Setup A breakout-retest continuation, Setup B trend
  pullback BOS / continuation, high-vol Setup B branches, and SR1 family review.
- Do not restart BOS, breakout-retest, or pullback-continuation variants without
  explicit owner approval and a new design lock.

## Setup C Summary

- Family: TSMOM / trend-following + volatility targeting.
- Primary: 40-bar close-to-close lookback return.
- Sensitivity: 20-bar and 60-bar only.
- Rebalance: every 6 bars on 4H data.
- Volatility proxy: ATR(20) / close.
- Gate metric: volatility-targeted post-cost moderate.
- Random baseline: volatility-targeted primary metric.
- Raw metrics: diagnostics only.

## C3 Diagnostics

- Funding stress scenarios were added as deterministic diagnostics only.
- Regime decomposition was added as observational only; no strategy filter was
  introduced.
- Sensitivity robustness separates discovery strength from validation
  non-negative behavior.
- Autocorrelation interpretation states overlapping lookback autocorrelation is
  expected and does not prove edge.
- Direction-change frequency is reported at rebalance points.

Current concern:
- C3 shows material regime dependence for the 40-bar primary. The high_vol
  bucket is negative and the low_vol bucket is strongly positive.

## Next Research Action

- Independent review / decision on C3 diagnostics.
- No paper, runtime, trading, or live escalation from Setup C without explicit
  owner approval and additional gates.

Deferred useful work is tracked only in the compact Deferred / Watchlist section
of `docs/CURRENT_STATE.md`; those items are not authorization to implement.
