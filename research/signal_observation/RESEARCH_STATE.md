# Signal Observation - Research State

Purpose: compact current state for Stage 54-SQ signal-quality research. Full
artifacts and historical docs remain available, but routine startup should begin
here plus `docs/CURRENT_STATE.md` and `docs/BOUNDARIES.md`.

## Current Track

- Stage 54-SQ is research-only signal-quality observation.
- Data source: local/public OHLCV artifacts only unless a future owner-approved
  task explicitly authorizes download.
- Active family: Setup E / Post-Liquidation Exhaustion Reversal source-access
  decision. Setup C / TSMOM volatility-targeted is parked from active
  progression.
- Current status: Setup C was **PASS_CANDIDATE research-only** through C7
  evidence; after DR1 Binance recent rerun LOW it remains historical research
  evidence only and is not a paper-candidate progression lane. C1–C5 diagnostics complete.
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
  are pushed and remote-visible on `origin/main`.

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

## Current Research Gate

All items below require Owner decision or are on HOLD. No research action is
currently authorized without Owner approval.

- **Harness proposal** (PROPOSED): independent review and Owner authorization
  required before any screening or D1 analysis.
  `docs/STAGE_54_SQ_REUSABLE_CHEAP_FALSIFICATION_HARNESS_PROPOSAL.md`
- **Sideways family note** (PROPOSED / CANDIDATE MAP ONLY): sideways family is
  GO to map; sideways screening remains HOLD until harness methodology is
  authorized; sideways acquisition/analysis is NO-GO.
  `research/signal_observation/SIDEWAYS_FAMILY_NOTE.md`
- **Setup D D1 analysis** (HOLD): SOL interval policy decision + harness review
  + separate D1 analysis design lock all required before any D1 analysis.
- **Setup E E1 source** (HOLD): Hyperliquid/The Graph free plan blocked.
  Owner decision: upgrade plan or authorize Research Scout for alternative source.
  Preferred contact: data@hydromancer.xyz (Hydromancer Reservoir).
- **OKX C7** (deferred): Cloudflare 1010 block on current host. Do not retry
  without Owner confirmation of reachability change.

## Research Progression Log

- **C8 direction-call agreement diagnostic review**. The Bitget/Binance
  diagnostic has been implemented and reported; next step is independent
  review before any follow-up research decision. Not runtime, paper, trading,
  probe, or live readiness.
- C8 direction-call agreement design lock written:
  `docs/STAGE_54_SQ_C8_DIRECTION_CALL_AGREEMENT_DESIGN_LOCK.md`. It locks
  Bitget/Binance only, BTCUSDT/ETHUSDT/SOLUSDT only, 4H only, the same C7
  development and expanded windows, frozen Setup C detector, primary 40-bar
  comparison, no new downloads/API calls/data mutation, and no gate/filter/
  readiness change. Independent review is the next step before implementation.
- C8 direction-call agreement implementation and report written:
  `research/signal_observation/setup_c_c8_direction_agreement.py`,
  `research/signal_observation/run_setup_c_c8_direction_agreement.py`, and
  `research/signal_observation/output/cross_venue/setup_c_c8_direction_agreement_report.{txt,json}`.
  Headline result: aligned direction agreement is high (combined all-symbol
  98.83%), but missing alignment coverage is material (combined all-symbol
  89.92%), so the locked interpretation is `mixed_or_inconclusive`.
  Observational only; C7 Bitget/Binance PASS verdicts remain read-only inputs;
  no gate, filter, or readiness change.
- C8 post-review decision record written:
  `research/signal_observation/SETUP_C_C8_POST_REVIEW_DECISION.md`.
  Verdict: PASS WITH NOTES. C8 is closed; do not open C8b or continue
  direction-call diagnostics unless the owner explicitly reopens them with a
  new decision gate. Next fork: define paper-prerequisites docs-only, without
  approving paper trading.
- Setup C paper-prerequisites design lock created:
  `docs/STAGE_54_SQ_SETUP_C_PAPER_PREREQUISITES_DESIGN_LOCK.md`.
  C8 remains closed; no C8b. Review is pending. The lock defines prerequisites
  only and does not approve paper, runtime, trading, probe, or live readiness.
- Setup C paper-prerequisites proposal created:
  `research/signal_observation/SETUP_C_PAPER_PREREQUISITES_PROPOSAL.md`.
  Review is pending. It defines prerequisites only and does not approve paper,
  runtime, trading, probe, or live readiness.
- Pre-DR1 Decision Gate created:
  `docs/PRE_DR1_DECISION_GATE.md`. Review / owner
  decision is pending before any Data Recency / Predictability Reconnaissance
  design lock or implementation.
- DR1 data recency / predictability design lock created:
  `docs/STAGE_54_SQ_DR1_DATA_RECENCY_PREDICTABILITY_DESIGN_LOCK.md`.
  DR1 implementation/report written:
  `research/signal_observation/setup_c_dr1_data_recency_predictability.py`,
  `research/signal_observation/run_setup_c_dr1_data_recency_predictability.py`,
  and
  `research/signal_observation/output/recon/setup_c_dr1_data_recency_predictability_report.{txt,json}`.
  Headline result: `INCONCLUSIVE`; freshness eligibility fails because Bitget
  recent six-month 4H data is not contiguous (max gap 8h), while lead-lag is
  inconclusive and variance-ratio / recent Setup C persistence are weak.
  Observational only; no paper, runtime, trading, probe, or live readiness.
- DR1 post-result decision record written:
  `research/signal_observation/SETUP_C_DR1_POST_RESULT_DECISION.md`.
  DR1 is closed as `INCONCLUSIVE`; do not open a paper-candidate design lock
  and do not park Setup C yet. Next fork: define the missing recent-data
  requirement before any attempt to resolve DR1 freshness eligibility.
- DR1 missing recent-data requirement design lock created:
  `docs/STAGE_54_SQ_DR1_MISSING_RECENT_DATA_REQUIREMENT_DESIGN_LOCK.md`.
  Review is next; it does not authorize downloads, data substitution, DR1
  rerun, paper-candidate design lock, or readiness promotion.
- Pre-DR1 recent-data availability decision gate created:
  `docs/PRE_DR1_RECENT_DATA_AVAILABILITY_DECISION_GATE.md`.
  Review / owner decision is next; no download, DR1 rerun, paper-candidate
  design lock, or readiness promotion is authorized.
- DR1 recent-data availability decision record written:
  `research/signal_observation/SETUP_C_DR1_RECENT_DATA_AVAILABILITY_DECISION.md`.
  Outcome: `INCONCLUSIVE`; source/window clarification is next before any
  acquisition design lock, download, or DR1 rerun.
- DR1 recent-data source/window clarification created:
  `research/signal_observation/SETUP_C_DR1_RECENT_DATA_SOURCE_WINDOW_CLARIFICATION.md`.
  Preferred next planning candidate is Binance public recent 4H feasibility
  clarification. No data download, API probing, acquisition implementation,
  DR1 rerun, paper-candidate design lock, or readiness promotion is authorized.
- DR1 Binance recent 4H feasibility design lock created:
  `docs/STAGE_54_SQ_DR1_BINANCE_RECENT_4H_FEASIBILITY_DESIGN_LOCK.md`.
  Planning only; review is next before any feasibility check, network call,
  download, data mutation, DR1 rerun, or readiness promotion.
- DR1 Binance recent 4H feasibility note created:
  `research/signal_observation/SETUP_C_DR1_BINANCE_RECENT_4H_FEASIBILITY_NOTE.md`.
  Outcome: `FEASIBLE` in principle for acquisition-design planning; no API
  calls, endpoint probing, downloads, DR1 rerun, paper-candidate design lock,
  or readiness promotion are authorized.
- DR1 Binance recent-data acquisition design lock created:
  `docs/STAGE_54_SQ_DR1_BINANCE_RECENT_DATA_ACQUISITION_DESIGN_LOCK.md`.
  Planning only; independent review is next before any bounded acquisition
  implementation task.
- DR1 Binance recent-data acquisition/validation completed:
  `research/signal_observation/output/binance_recent/setup_c_dr1_binance_recent_4h_acquisition_report.{txt,json}`.
  Result: `DATA_REQUIREMENT_PASS` for BTCUSDT/ETHUSDT/SOLUSDT 4H on the
  locked 2025-11-12T12:00:00+00:00 to 2026-05-12T12:00:00+00:00 window.
  No DR1 rerun, gate change, or readiness promotion.
- DR1 Binance recent rerun design lock created:
  `docs/STAGE_54_SQ_DR1_BINANCE_RECENT_RERUN_DESIGN_LOCK.md`.
  Planning only; independent review is next before any bounded DR1 rerun
  implementation task.
- DR1 Binance recent rerun completed:
  `research/signal_observation/output/recon/setup_c_dr1_binance_recent_rerun_report.{txt,json}`.
  Result: `LOW`; freshness is eligible, but autocorrelation, variance-ratio,
  and Setup C recent persistence are weak. No paper-candidate design lock,
  gate change, or readiness promotion.
- DR1 Binance recent rerun post-result decision written:
  `research/signal_observation/SETUP_C_DR1_BINANCE_RECENT_RERUN_POST_RESULT_DECISION.md`.
  Setup C is parked from active progression; do not open paper-candidate design
  lock, DR1b, or rescue rerun. Next lane is hypothesis-first future setup
  discussion.
- Research candidate backlog created:
  `research/signal_observation/RESEARCH_CANDIDATE_BACKLOG.md`. Current entries:
  Funding Carry / Funding Stress = `advanced-to-hypothesis`; Liquidation
  Cascades, Basis / Cash-and-Carry Dislocation, and Options Expiry / Dealer
  Hedging Pressure = `triage-ready`.
- Signal idea generator created:
  `research/signal_observation/SIGNAL_IDEA_GENERATOR.md`.
- Setup D hypothesis note created:
  `research/signal_observation/SETUP_D_HYPOTHESIS.md`.
- Pre-D1 decision gate created:
  `docs/PRE_D1_DECISION_GATE.md`.
- D1 funding cheap-falsification design lock created:
  `docs/STAGE_54_SQ_D1_FUNDING_CHEAP_FALSIFICATION_DESIGN_LOCK.md`.
  Independent review verdict: PASS.
- Pre-D1 funding data path availability decision gate created:
  `docs/PRE_D1_FUNDING_DATA_PATH_AVAILABILITY_DECISION_GATE.md`.
  Gate recommendation: `PROCEED_TO_D1_PUBLIC_DATA_ACQUISITION_DESIGN` because
  repo inspection found no committed reusable D1-ready funding-rate history
  aligned with OHLCV. Owner has accepted this gate outcome.
- D1 public funding data acquisition design lock:
  `docs/STAGE_54_SQ_D1_FUNDING_DATA_ACQUISITION_DESIGN_LOCK.md`.
  Accepted and committed (`10617b7`). No download, API call, or D1 analysis
  authorized by design lock alone.
- D1 funding data acquisition completed (`93f4d0f`):
  `research/signal_observation/setup_d_d1_funding_acquisition/`.
  Result: `FUNDING_DATA_ACQUIRED`. BTCUSDT/ETHUSDT: quality PASS (2,147 rows
  each, 8h intervals, no gaps). SOLUSDT: RETAINED / FLAGGED —
  `NON_STANDARD_INTERVALS_FOUND` (2,222 rows; 101 sub-8h gaps, 98×2h and 3×4h,
  2022-11-09 to 2022-11-18 / FTX collapse period). SOLUSDT variable intervals
  are a genuine funding-stress marker, not a data defect. Must not be silently
  normalized, discarded, or mixed into clean 8h carry analysis without an
  explicit harness design decision. Full `FUNDING_DATA_PASS` and D1 analysis
  design lock remain HOLD pending SOLUSDT interval policy and harness design.
- Reusable cheap-falsification harness proposal created (PROPOSED; requires
  independent review and Owner authorization):
  `docs/STAGE_54_SQ_REUSABLE_CHEAP_FALSIFICATION_HARNESS_PROPOSAL.md`.
  Defines Event-Triggered, Continuous-State, and Cross-Venue Dislocation
  template families; pre-registration; held-out discipline; multiple-comparisons
  policy; STRONG_ANOMALY_CANDIDATE escalation; grail/anomaly philosophy; and
  batch candidate table. D1 funding carry/stress is prototype candidate. D1
  analysis design lock remains HOLD until SOL interval policy, harness review,
  and a separate D1 analysis design lock are all authorized.
- Sideways family candidate-map note created:
  `research/signal_observation/SIDEWAYS_FAMILY_NOTE.md`. Status: PROPOSED /
  CANDIDATE MAP ONLY. It maps funding normalization, basis/cash-and-carry,
  cross-asset spread mean reversion, volatility carry, OI divergence, false
  breakout re-entry, and microstructure mean reversion to existing proposed
  harness families. It authorizes no screening, acquisition, analysis, EXPLORE,
  validation, implementation, readiness, or new stage.
- Off-repo Setup D funding EXPLORE completed as non-evidence /
  non-validation; orientation label: `EXPLORE_MIXED`. No formal Setup D status
  promotion occurred.
- Liquidation Cascades triage created:
  `research/signal_observation/LIQUIDATION_CASCADES_TRIAGE.md`.
  Triage result: `Advance to hypothesis note`.
- Setup E branch is now `Post-Liquidation Exhaustion Reversal`.
- Setup E hypothesis note created:
  `research/signal_observation/SETUP_E_HYPOTHESIS.md`.
- Off-repo Setup E BTC daily coarse EXPLORE completed as non-evidence /
  non-validation using the verified free GitHub BTC daily liquidation JSON path
  plus public BTC daily OHLCV. Result label: `EXPLORE_WEAK`. Interpretation:
  weak coarse BTC daily forward-return structure; no formal Setup E status
  promotion; does not disprove the short-horizon liquidation-cascade hypothesis
  because the dataset is BTC-only and daily aggregate.
- Off-repo Setup E Coinalyze liquidation EXPLORE completed as non-evidence /
  non-validation using Coinalyze liquidation-history API, 20 selected liquid
  perpetual/futures symbols, 4h interval, combined comparable window
  2025-09-06T00:00:00Z to 2026-05-15T12:00:00Z. Orientation label:
  `EXPLORE_MIXED`.
- Setup E Coinalyze interpretation: generic all-elevated liquidation bucket was
  not compelling. Directional split was more interpretable and reversal-like:
  long-dominant liquidation intervals showed weaker recovery-like tendency;
  short-dominant liquidation intervals showed clearer negative follow-through /
  exhaustion-reversal-like structure at +12h and +24h. Exploratory only; not
  evidence and not a formal Setup E verdict.
- Pre-E1 decision gate exists:
  `docs/PRE_E1_DECISION_GATE.md`.
- E1 reversal cheap-falsification design lock exists:
  `docs/STAGE_54_SQ_E1_REVERSAL_CHEAP_FALSIFICATION_DESIGN_LOCK.md`.
  Independent review verdict: `PASS WITH NOTES`. The reviewed design lock is
  accepted as the current formal research specification, but E1 implementation
  is blocked by held-out-window availability.
- E1 held-out-window availability decision:
  `docs/STAGE_54_SQ_E1_HELD_OUT_WINDOW_AVAILABILITY_DECISION.md`.
  The Coinalyze 20-symbol 4h EXPLORE used the full available contiguous window
  (`2025-09-06T00:00:00Z` to `2026-05-15T12:00:00Z`), so the selected
  Coinalyze 4h path currently lacks an immediately usable non-overlapping
  formal held-out historical window. Post-hoc internal splitting of the already
  inspected window is rejected.
- E1 alternative held-out source/window decision:
  `docs/STAGE_54_SQ_E1_ALTERNATIVE_HELD_OUT_SOURCE_WINDOW_DECISION.md`.
  Outcome: `PROCEED_TO_NARROW_ALTERNATIVE_SOURCE_ACCESS_DEPTH_CHECK`.
  Preferred candidate: `The Graph / Hyperliquid liquidation event path`.
- E1 Hyperliquid / The Graph access-depth verification:
  `docs/STAGE_54_SQ_E1_HYPERLIQUID_THEGRAPH_ACCESS_DEPTH_VERIFICATION.md`.
  Token-level check performed. JWT format confirmed correct; The Graph Token
  API endpoint is live. Blocker: FREE plan / nft-only endpoint group does not
  permit Hyperliquid markets/liquidations endpoint. Outcome:
  `ACCESS_BLOCKED_PLAN_RESTRICTION`. Historical depth, BTC/ETH/SOL coverage,
  and held-out window remain unconfirmed. No records retrieved; no
  contamination risk. No source pivot, design-lock revision, or readiness
  promotion authorized.
- Next owner-level action: upgrade thegraph.market account to include
  Hyperliquid/markets endpoint access and re-enter bounded check, or authorize
  Research Scout to identify alternative liquidation data source paths.
- Secondary next option: OKX C7 evidence if reachability is restored
  (currently blocked by Cloudflare 1010 ASN-level block on the current
  host).
- Wider symbol universe and execution realism (slippage, latency,
  liquidity, partial fills, fee tiers) remain deferred.
- No paper, runtime, trading, probe, or live escalation from Setup C without
  explicit owner approval and additional gates.

Deferred useful work is tracked only in the compact Deferred / Watchlist section
of `docs/CURRENT_STATE.md`; those items are not authorization to implement.

---

## Setup E — Source-Candidate Parking / Status Register

This section parks investigated and partially investigated liquidation data-source
paths so they do not reappear as active work items. Parked paths must not be
reopened without new evidence or explicit Owner decision.

Governance note: Research Scout and reviewer reports are inputs only. Tower
Control must independently verify load-bearing external claims before converting
them into operational commands. No source pivot, EXPLORE, validation,
design-lock, readiness, or implementation is authorized by this section.

### 1. The Graph / Hyperliquid
**Status: HOLD / ACCESS_BLOCKED_PLAN_RESTRICTION**
Endpoint is live; JWT credential type confirmed correct. FREE / NFT-only plan
blocks Hyperliquid markets/liquidations endpoint access. No records retrieved;
no contamination introduced. Reopen only if Owner authorizes paid-plan
investigation.

### 2. Hydromancer Reservoir
**Status: PROMISING / BLOCKED ON DATE-RANGE VERIFICATION**
Schema documentation confirms event-level fills with explicit liquidation fields
(`is_liquidation`, `liquidation_mark_px`, `liquidation_method`), BTC/ETH/SOL
perp coverage, and no subscription or private-endpoint requirement. No data
contents opened. S3 filename listing was not completed: AWS credentials were not
configured and the AWS path was paused by Owner instruction.
AWS requester-pays path has now been attempted twice and is parked. Do not retry
AWS setup or listing without explicit Owner re-authorization.
Preferred non-invasive path: direct Hydromancer contact (data@hydromancer.xyz)
to obtain earliest/latest dates and filename/date convention before any
further access attempt.
Next possible Owner choices: authorize direct Hydromancer contact, or hold.
Do not open parquet contents or inspect rows before design-lock.

### 3. Tardis.dev
**Status: NOT SUITABLE AS PRIMARY TRIGGER / MARKET-DATA CONTEXT ONLY**
Hyperliquid historical data confirmed from 2024-10-29 (trades, L2 book,
funding). Event-level liquidation fields or explicit liquidation trigger support
are not confirmed for Hyperliquid. Without a confirmed liquidation marker,
Tardis cannot be the primary trigger source for Setup E. It may be useful only
as secondary market-data context if another source supplies liquidation triggers.
Requires paid API key for full access.

### 4. Allium
**Status: UNCLEAR / POSSIBLY PAID**
Structured on-chain liquidation fields documented (`liquidated_user`,
`liquidation_mark_px`, `liquidation_method`). Historical depth remains unclear;
prior references to December 2023 may reflect broader Hyperliquid/bridge history
rather than confirmed usable liquidation-fill coverage. Access model is unclear
and likely paid (Snowflake/Databricks datashare). Usable depth requires further
verification. Not investigated as primary path.

### 5. CoinGlass
**Status: UNCLEAR / AGGREGATED**
Hyperliquid listed as supported exchange; liquidation history API endpoints
exist. Data is interval-aggregated (1m–1w), not event-level. Paid API required
($29–$699/month). Not primary for event-level Setup E unless Owner explicitly
relaxes granularity requirement.

### 6. Coinalyze
**Status: NOT SUITABLE**
Hyperliquid coverage limited to HYPE token contract (HYPE/USD, HYPE/USDT).
Does not cover BTC, ETH, or SOL perpetuals on Hyperliquid. Intraday retention
limited to ~1500–2000 datapoints.

### 7. Amberdata
**Status: NOT SUITABLE / NOT PRIMARY**
Hyperliquid futures support confirmed (instruments, OI, trades, OHLCV, order
book, funding). Liquidation event-level dataset was not listed as available for
Hyperliquid and was not confirmed. Not investigated further.

### 8. Hyperliquid Native API
**Status: NOT YET VERIFIED / FREE PRIMARY-CANDIDATE CHECK NEEDED**
Potentially attractive as a first-party free source. Official docs confirm
user-level fills endpoints and rate limits, but a confirmed global historical
liquidation feed for BTC/ETH/SOL perpetuals has not been established. Must
verify whether any official public endpoint provides: event-level liquidation
records or liquidation flags, historical depth sufficient for a non-overlapping
held-out window, BTC/ETH/SOL coverage, and practical backfill without
credentials or private endpoints. No API call, data download, or depth
verification has been performed; no contamination introduced. Requires a bounded
metadata-only access-depth check before any operational or EXPLORE
authorization.

### 9. Dwellir Hyperliquid Index
**Status: NEW CANDIDATE / THIRD-PARTY INDEX / VERIFY FREE + DEPTH**
`liquidationFillsByTime` appears to expose bounded liquidation fills by time via
a Dwellir-hosted Hyperliquid index. This is not the native Hyperliquid API.
Requires source-quality verification for: free access and rate limits, data
depth and earliest available date, BTC/ETH/SOL perpetual coverage, and whether
a contamination-safe metadata-only check is feasible without retrieving
historical candidate data. No API call, data download, or depth verification has
been performed; no contamination introduced.

---

### Register Notes

**Free-path constraint:** Current source search should prioritize free /
no-paid-subscription paths unless the Owner explicitly relaxes this constraint.
Requester-pays infrastructure costs, paid API keys, and hosted paid plans must
be explicitly labeled as paid in this register.

**Governance:** External reviewer and trader review outputs are inputs only.
Tower Control must independently verify load-bearing source claims against
primary docs before any operational commands or API calls. No source pivot,
EXPLORE, validation, design-lock, readiness, or implementation is authorized by
this register.
