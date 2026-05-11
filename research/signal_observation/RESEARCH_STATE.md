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
  validation analyzer implemented and single-venue (Bitget) evidence run
  completed; decision: **C7_PASS** on the locked backward expanded window
  (2022-01-01T00:00:00Z to 2023-12-17T12:00:00Z). Post-C7 review verdict:
  PASS (see `research/signal_observation/SETUP_C_C7_POST_REVIEW_DECISION.md`).
  Cross-venue replication on Binance USDT-M Futures also completed:
  decision **C7_PASS**.
- Cross-venue both-PASS math is supported (Bitget and Binance each
  independently satisfy the locked C7 gate). The cross-venue design lock
  at `docs/STAGE_54_SQ_C7_CROSS_VENUE_DESIGN_LOCK.md` reconciled the prior
  governance gap; the cross-venue decision record at
  `research/signal_observation/SETUP_C_C7_CROSS_VENUE_DECISION.md`
  accepts cross-venue both-PASS as research evidence with caveats
  recorded.
- All C1–C7 artifacts (single-venue and cross-venue design locks,
  analyzer, helpers, Bitget data + evidence, Binance data + evidence,
  post-C7 single-venue decision record, cross-venue decision record)
  are pushed and remote-visible on `origin/main` as of HEAD `e355aff`.

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
- C7 single-venue (Bitget) evidence run completed and persisted at `c108197`:
  `research/signal_observation/output/bitget/setup_c_c7_expanded_report.{txt,json}`.
- C7 single-venue decision: **C7_PASS**. All five gate conditions pass:
  expanded vt-post-cost-moderate > 0, expanded beats random p75,
  funding-adjusted high_cost > 0, ≥ 2 of 3 symbols non-negative,
  combined-retention ratio ≥ 50%.
- C7 post-review decision record written:
  `research/signal_observation/SETUP_C_C7_POST_REVIEW_DECISION.md`.
  Independent post-C7 review verdict: PASS. Caveats recorded:
  SOL ≈ 53% of expanded headline; expanded backward window stronger
  than recent dev/validation period; expanded high_vol and low_vol both
  positive (differs from C5 dev/validation high_vol weakness); single-venue,
  3-symbol universe.

## C7 Cross-Venue Replication

- Cross-venue C7 design lock written to govern cross-venue evidence
  without altering data, code, gates, or evidence:
  `docs/STAGE_54_SQ_C7_CROSS_VENUE_DESIGN_LOCK.md`.
- Authorized venues: Bitget (done), Binance USDT-M Futures (done), OKX
  (authorized but deferred — Cloudflare 1010 ASN block on current host).
- Binance public kline downloader added at `d770a05`; Binance dev +
  expanded holdout data committed at `583e724`; Binance C7 evidence run
  persisted at `775d739`:
  `research/signal_observation/output/binance/setup_c_c7_expanded_report.{txt,json}`.
- Binance C7 decision: **C7_PASS**. All five gate conditions
  independently satisfied on the same locked windows.
- Cross-venue observational deltas (not gate violations): Binance dev-only
  vt-post-cost-moderate ≈ 25% of Bitget's; SOL concentration ≈ 70% on
  Binance vs ~53% on Bitget. Both venues' headline magnitudes pass.
- Cross-venue decision record written:
  `research/signal_observation/SETUP_C_C7_CROSS_VENUE_DECISION.md`.
  Verdict: **cross-venue both-PASS accepted as research evidence**.
  Decision: keep Setup C active as research-only PASS_CANDIDATE; do not
  promote readiness. Caveats recorded: Binance dev magnitude ≈ 25% of
  Bitget dev; Binance combined-retention ratio (`4.98×`) is inflated by
  small denominator, not a stronger venue edge; SOL concentration ~70%
  on Binance vs ~53% on Bitget; 3-symbol universe; OKX deferred.
- Per design lock §"What C7 Does Not Authorize" (single-venue and
  cross-venue), no C7 PASS — single-venue or cross-venue — promotes
  paper, runtime, trading, probe, or live readiness.

## Next Research Action

- **Direction-call agreement diagnostic** between Bitget and Binance over
  the dev window. Purpose: determine whether the Binance dev-magnitude
  divergence is driven by direction-call flips between venues or by
  volatility / micro-pricing differences. Observational only;
  public-source-only; same frozen detector and symbol set; separate
  diagnostic design lock and explicit owner approval required before any
  code, data, or analysis. Not runtime, paper, trading, probe, or live
  readiness.
- Secondary next option: OKX C7 evidence if reachability is restored
  (currently blocked by Cloudflare 1010 ASN-level block on the current
  host).
- Wider symbol universe and execution realism (slippage, latency,
  liquidity, partial fills, fee tiers) remain deferred.
- No paper, runtime, trading, probe, or live escalation from Setup C without
  explicit owner approval and additional gates.

Deferred useful work is tracked only in the compact Deferred / Watchlist section
of `docs/CURRENT_STATE.md`; those items are not authorization to implement.
