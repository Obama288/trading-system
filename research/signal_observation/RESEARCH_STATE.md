# Signal Observation - Research State

Purpose: compact current state for Stage 54-SQ signal-quality research. Full
artifacts and historical docs remain available, but routine startup should begin
here plus `docs/CURRENT_STATE.md` and `docs/BOUNDARIES.md`.

## Current Track

- Stage 54-SQ is research-only signal-quality observation.
- Data source: local/public OHLCV artifacts only unless a future owner-approved
  task explicitly authorizes download.
- Active family: Setup C / TSMOM volatility-targeted.
- Current status: **PASS_CANDIDATE research-only**. C1–C5 diagnostics complete.
  C6 evidence summary and decision record written (see
  `research/signal_observation/SETUP_C_EVIDENCE_SUMMARY.md`). C7 expanded
  validation analyzer implemented and evidence run completed; decision:
  **C7_PASS** on the locked backward expanded window
  (2022-01-01T00:00:00Z to 2023-12-17T12:00:00Z).
- All C1–C7 artifacts (design lock, analyzer, helpers, expanded data, and
  evidence report) are pushed and remote-visible on `origin/main` as of
  HEAD `c108197`.

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

## C4 Diagnostics

- Raw non-volatility-targeted high_vol / low_vol regime split added for the
  40-bar primary only.
- Diagnostic uses same regime bucket definitions as C3.
- Interpretation: `real_regime_dependence` — raw high_vol negative, raw low_vol
  positive.
- C4 is observational only; no filter, no gate change.

## C5 Diagnostics

- Discovery/validation split of high_vol / low_vol regime metrics for the 40-bar
  primary.
- Interpretation: `validation_only_or_discovery_only` — pattern (high_vol
  negative, low_vol positive) appears in validation split only. Discovery had
  positive high_vol and low_vol.
- C5 is observational only; no filter, no gate change.
- C5 independent review verdict: PASS WITH NOTES.

## C6 Decision Record

- Evidence summary written: `SETUP_C_EVIDENCE_SUMMARY.md`.
- Setup C remains PASS_CANDIDATE research-only.
- Escalation remains HOLD.
- Recommended next step: Fork A — expand dataset / out-of-time validation,
  because evidence is promising but single-dataset and regime-sensitive.
- Owner may choose Fork B (define paper prerequisites, no approval) or Fork C
  (park Setup C) instead.

## C7 Design Lock, Analyzer, and Evidence

- C7 expanded validation design lock written:
  `docs/STAGE_54_SQ_C7_EXPANDED_VALIDATION_DESIGN_LOCK.md`.
- Design lock independent review verdict: PASS WITH NOTES. Reviewer fixes
  applied.
- C7 design lock includes: future setup evaluation process principles and
  post-C7 Data Reconnaissance fork guidance.
- C7 analyzer added at `61ad028`:
  `research/signal_observation/setup_c_c7_expanded_validation.py` and
  `tests/research/test_signal_observation_setup_c_c7_expanded_validation.py`.
- C7 analyzer independent review verdict: PASS.
- C7 expanded Bitget holdout data committed at `16ae508`
  (BTCUSDT/ETHUSDT/SOLUSDT 4H, 4272 rows per symbol, locked backward window
  2022-01-01T00:00:00Z to 2023-12-17T12:00:00Z, public Bitget 4H OHLCV only).
- C7 evidence artifact helpers (`format_c7_report`, `write_c7_artifacts`)
  added at `37e28ec`.
- C7 evidence run completed and persisted at `c108197`:
  `research/signal_observation/output/bitget/setup_c_c7_expanded_report.{txt,json}`.
- C7 decision: **C7_PASS**. All five gate conditions pass: expanded
  vt-post-cost-moderate > 0, expanded beats random p75, funding-adjusted
  high_cost > 0, ≥ 2 of 3 symbols non-negative, combined-retention
  ratio ≥ 50%.
- Per design lock §"What C7 Does Not Authorize", the C7 PASS verdict
  does not promote paper, runtime, trading, probe, or live readiness.

## Next Research Action

- Owner decision on next research gate / post-C7 decision record. Not
  runtime, paper, trading, probe, or live readiness.
- No paper, runtime, trading, probe, or live escalation from Setup C without
  explicit owner approval and additional gates.

Deferred useful work is tracked only in the compact Deferred / Watchlist section
of `docs/CURRENT_STATE.md`; those items are not authorization to implement.
