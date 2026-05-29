# Hephaestus - Current State

Purpose: short current-status entry point for Tower Control, Codex, Claude, and
Auditor sessions. Historical docs remain available, but routine startup should
begin here, `docs/BOUNDARIES.md`, recent commits, and only then role-specific
docs as needed.

## Current Gate

- Mode: paper trading only.
- Live: NO-GO.
- Runtime readiness: no new readiness promoted by this file.
- Primary exchange planning lane: Stage 54-BG / Bitget Demo planning.
- Primary research lane: Setup E / E1 held-out source-access decision; Setup C
  is parked from active progression after DR1 Binance recent rerun LOW.
- Source protocol: GitHub docs, commits, code, tests, and relevant PR metadata
  are primary; project memory is orientation only.

## Recent Commits

The commit list below records recent pushed milestones visible on `origin/main`.

- `e355aff` docs: add C7 cross-venue design lock.
- `775d739` research: add Binance C7 evidence report.
- `583e724` research: add Binance cross-venue holdout data.
- `d770a05` research: add Binance public kline downloader.
- `bb6ab90` research: fix OKX bounded history pagination.

Recent HEAD records the C7 cross-venue design lock (governance
reconciliation; research-only); it does not alter the current
paper-only / live NO-GO safety state.

Do not claim remote visibility for local commits unless verified by GitHub or
remote refs.

## Exchange Track

- Stage 54-BG / Bitget Demo is the current planning candidate lane.
- Stage 54-BG2-C private read-only preflight runbook is docs-only / planning.
- Bybit Stage 53-B2c.1c / B2d private real testnet path remains blocked because
  usable Bybit testnet API access is unavailable.
- No private Bitget smoke, wallet/balance/positions real smoke, order_status,
  write/live methods, or service wiring are authorized.

## Research Track

- Stage 54-SQ is research-only signal-quality observation.
- Price-action continuation family is retired after Setup A, Setup B, and SR1
  family review.
- Active research family: Setup E / Post-Liquidation Exhaustion Reversal
  source-access decision. Setup C / TSMOM volatility-targeted is parked from
  active progression.
- Setup C was **PASS_CANDIDATE research-only** through C7 evidence; after DR1
  Binance recent rerun LOW it remains historical research evidence only and is
  not a paper-candidate progression lane. C1–C5 diagnostics complete.
- C5 (discovery/validation regime split): interpretation
  `validation_only_or_discovery_only`. High_vol weakness is concentrated in
  the validation window; discovery had positive high_vol and low_vol.
- C6 evidence summary and decision record written:
  `research/signal_observation/SETUP_C_EVIDENCE_SUMMARY.md`.
- C7 expanded validation analyzer implemented at `61ad028`
  (`research/signal_observation/setup_c_c7_expanded_validation.py` plus
  `tests/research/test_signal_observation_setup_c_c7_expanded_validation.py`).
  Independent review verdict: PASS.
- C7 expanded Bitget holdout data committed at `16ae508`
  (BTCUSDT/ETHUSDT/SOLUSDT 4H, 4272 rows each, locked backward window
  2022-01-01T00:00:00Z to 2023-12-17T12:00:00Z, public-source-only).
- C7 evidence artifact helpers (`format_c7_report`, `write_c7_artifacts`)
  added at `37e28ec`.
- C7 evidence run completed and persisted at `c108197`
  (`research/signal_observation/output/bitget/setup_c_c7_expanded_report.{txt,json}`).
- C7 decision: **C7_PASS**. All five gate conditions pass: expanded
  vt-post-cost-moderate > 0, expanded beats random p75, funding-adjusted
  high_cost > 0, ≥ 2 of 3 symbols non-negative, combined-retention
  ratio ≥ 50%.
- C7 post-review decision record written:
  `research/signal_observation/SETUP_C_C7_POST_REVIEW_DECISION.md`.
  Independent post-C7 review verdict: PASS. Caveats recorded: SOL ≈ 53%
  of expanded headline; expanded backward window stronger than recent
  dev/validation period; expanded high_vol and low_vol both positive
  (differs from C5 dev-validation finding); single-venue, 3-symbol
  universe.
- C7 cross-venue replication on Binance USDT-M Futures completed at
  `775d739`: decision **C7_PASS**, all five gate conditions independently
  satisfied. Artifacts:
  `research/signal_observation/output/binance/setup_c_c7_expanded_report.{txt,json}`.
  Observational deltas vs Bitget (not gate violations): Binance dev-only
  vt-post-cost-moderate ≈ 25% of Bitget's; SOL ≈ 70% concentration on
  Binance vs ~53% on Bitget.
- Cross-venue both-PASS **math** is supported by the C7 gate replication
  on Bitget and Binance independently. The cross-venue design lock at
  `docs/STAGE_54_SQ_C7_CROSS_VENUE_DESIGN_LOCK.md` reconciled the prior
  governance gap.
- C7 cross-venue decision record written:
  `research/signal_observation/SETUP_C_C7_CROSS_VENUE_DECISION.md`.
  Verdict: **cross-venue both-PASS accepted as research evidence**.
  Caveats recorded: Binance dev magnitude ≈ 25% of Bitget dev; Binance
  combined-retention ratio (`4.98×`) is inflated by small denominator,
  not a stronger venue edge; SOL concentration ~70% on Binance vs ~53%
  on Bitget; 3-symbol universe; OKX deferred / Cloudflare 1010 blocked.
- OKX remains authorized by the cross-venue design lock but **deferred**
  until reachability is restored.
- Setup C remains research-only PASS_CANDIDATE. Per design lock §"What C7
  Does Not Authorize", neither single-venue nor cross-venue C7 PASS
  promotes paper readiness, runtime readiness, trading readiness, probe
  readiness, or live readiness.
- Escalation: **HOLD**.

## Currently Allowed Next Work

1. **Harness methodology** (AUTHORIZED METHODOLOGY / NO SCREENING AUTHORIZED):
   `docs/STAGE_54_SQ_REUSABLE_CHEAP_FALSIFICATION_HARNESS_PROPOSAL.md`.
   Authorized for candidate pre-registration and bounded screening task design.
   No candidate screening task is authorized. Each candidate requires its own
   pre-registration, data availability confirmation, held-out split, and separate
   Owner authorization before any screening begins.

   Sideways family candidate-map note (PROPOSED / CANDIDATE MAP ONLY):
   `research/signal_observation/SIDEWAYS_FAMILY_NOTE.md`. Sideways screening
   remains HOLD — candidate pre-registration design may begin, screening
   execution is not authorized. Sideways acquisition/analysis is NO-GO.

   **Funding Normalization pre-registration design** (PRE-REGISTRATION DESIGN /
   NO SCREENING AUTHORIZED):
   `research/signal_observation/FUNDING_NORMALIZATION_PREREGISTRATION.md`.
   Continuous-State harness; BTC/ETH core pairs (PASS); SOL flagged (handling
   decision required). State definition thresholds not yet locked. Cost floor:
   9 bps. Next gate: Owner selects A/B/C/D (screening design lock, OHLCV source
   feasibility, SOL handling, or hold).

2. **Setup D D1 analysis** (HOLD — two conditions unmet):
   - SOL interval policy decision (variable 2h/4h intervals during FTX stress period).
   - Harness methodology authorization: MET (Owner-authorized).
   - Separate D1 analysis design lock.
   Do not run D1 analysis, DR1b, or new data downloads until all conditions are resolved.

3. **Setup E E1 source decision** (HOLD — Hyperliquid / The Graph access blocked):
   Free plan does not permit Hyperliquid liquidations endpoint.
   Owner decision required: upgrade account plan or authorize Research Scout
   to identify an alternative liquidation data source path.

4. **OKX C7 evidence** (deferred — Cloudflare 1010 blocked from this host):
   Authorized by cross-venue design lock. Do not retry without Owner confirmation
   that reachability has changed.

## Research Artifact Index

- Single-venue C7 design lock:
  `docs/STAGE_54_SQ_C7_EXPANDED_VALIDATION_DESIGN_LOCK.md`.
- Cross-venue C7 design lock:
  `docs/STAGE_54_SQ_C7_CROSS_VENUE_DESIGN_LOCK.md`.
- C7 single-venue (Bitget) evidence: data `16ae508`, evidence report
  `c108197`, decision `C7_PASS`. C7 post-review decision record:
  `research/signal_observation/SETUP_C_C7_POST_REVIEW_DECISION.md`.
- C7 cross-venue (Binance) evidence: data `583e724`, evidence report
  `775d739`, decision `C7_PASS`.
- C7 cross-venue decision record:
  `research/signal_observation/SETUP_C_C7_CROSS_VENUE_DECISION.md`.
- C8 direction-call agreement design lock:
  `docs/STAGE_54_SQ_C8_DIRECTION_CALL_AGREEMENT_DESIGN_LOCK.md`.
  Next step is independent review before any implementation, data processing,
  or analysis.
- C8 direction-call agreement implementation/report exists:
  `research/signal_observation/output/cross_venue/setup_c_c8_direction_agreement_report.{txt,json}`.
  Result: `mixed_or_inconclusive` because missing alignment coverage is
  material, despite high agreement on aligned rows; observational-only and no
  readiness promotion.
- C8 post-review decision record:
  `research/signal_observation/SETUP_C_C8_POST_REVIEW_DECISION.md`.
  Verdict: PASS WITH NOTES; C8 closed; do not open C8b unless owner explicitly
  reopens it with a new decision gate.
- Pre-DR1 Decision Gate:
  `docs/PRE_DR1_DECISION_GATE.md`. Next step is
  independent review / owner decision before any Data Reconnaissance design
  lock or implementation.
- DR1 data recency / predictability design lock:
  `docs/STAGE_54_SQ_DR1_DATA_RECENCY_PREDICTABILITY_DESIGN_LOCK.md`.
  DR1 implementation/report exists:
  `research/signal_observation/output/recon/setup_c_dr1_data_recency_predictability_report.{txt,json}`.
  Result: `INCONCLUSIVE`; committed recent data fails the locked freshness
  eligibility because Bitget recent 4H candles are not contiguous in the
  required six-month window. Observational-only; no readiness promotion.
- DR1 post-result decision record:
  `research/signal_observation/SETUP_C_DR1_POST_RESULT_DECISION.md`.
  DR1 is closed as `INCONCLUSIVE`; do not open a paper-candidate design lock.
  Next allowed work is defining the missing recent-data requirement.
- DR1 missing recent-data requirement design lock:
  `docs/STAGE_54_SQ_DR1_MISSING_RECENT_DATA_REQUIREMENT_DESIGN_LOCK.md`.
  Governance only; next step is independent review before any acquisition
  decision gate, download, or DR1 rerun.
- Pre-DR1 recent-data availability decision gate:
  `docs/PRE_DR1_RECENT_DATA_AVAILABILITY_DECISION_GATE.md`.
  Review / owner decision is next; it does not authorize downloads or DR1
  rerun.
- DR1 recent-data availability decision:
  `research/signal_observation/SETUP_C_DR1_RECENT_DATA_AVAILABILITY_DECISION.md`.
  Outcome: `INCONCLUSIVE`; do not open acquisition design yet. Next work is
  source/window clarification.
- DR1 recent-data source/window clarification:
  `research/signal_observation/SETUP_C_DR1_RECENT_DATA_SOURCE_WINDOW_CLARIFICATION.md`.
  Preferred candidate for next planning step: Binance public recent 4H
  feasibility clarification; no download or acquisition design is authorized.
- DR1 Binance recent 4H feasibility design lock:
  `docs/STAGE_54_SQ_DR1_BINANCE_RECENT_4H_FEASIBILITY_DESIGN_LOCK.md`.
  Planning only; review is next before any feasibility check, network call,
  download, or DR1 rerun.
- DR1 Binance recent 4H feasibility note:
  `research/signal_observation/SETUP_C_DR1_BINANCE_RECENT_4H_FEASIBILITY_NOTE.md`.
  Outcome: `FEASIBLE` in principle for acquisition-design planning; no API
  call, download, DR1 rerun, or readiness promotion is authorized.
- DR1 Binance recent-data acquisition design lock:
  `docs/STAGE_54_SQ_DR1_BINANCE_RECENT_DATA_ACQUISITION_DESIGN_LOCK.md`.
  Planning only; independent review is next before any bounded acquisition
  implementation task.
- DR1 Binance recent-data acquisition/validation:
  `research/signal_observation/output/binance_recent/setup_c_dr1_binance_recent_4h_acquisition_report.{txt,json}`.
  Result: `DATA_REQUIREMENT_PASS` for BTCUSDT/ETHUSDT/SOLUSDT 4H on the
  locked 2025-11-12T12:00:00+00:00 to 2026-05-12T12:00:00+00:00 window.
  No DR1 rerun, gate change, or readiness promotion.
- DR1 Binance recent rerun design lock:
  `docs/STAGE_54_SQ_DR1_BINANCE_RECENT_RERUN_DESIGN_LOCK.md`.
  Planning only; independent review is next before any bounded DR1 rerun
  implementation task.
- DR1 Binance recent rerun:
  `research/signal_observation/output/recon/setup_c_dr1_binance_recent_rerun_report.{txt,json}`.
  Result: `LOW`; freshness is eligible, but autocorrelation, variance-ratio,
  and Setup C recent persistence are weak. No paper-candidate design lock,
  gate change, or readiness promotion.
- DR1 Binance recent rerun post-result decision:
  `research/signal_observation/SETUP_C_DR1_BINANCE_RECENT_RERUN_POST_RESULT_DECISION.md`.
  Setup C is parked from active progression; do not open paper-candidate design
  lock, DR1b, or rescue rerun. Next lane is hypothesis-first future setup
  discussion.
- Research candidate backlog:
  `research/signal_observation/RESEARCH_CANDIDATE_BACKLOG.md`. Current entries:
  Funding Carry / Funding Stress = `advanced-to-hypothesis`; Liquidation
  Cascades, Basis / Cash-and-Carry Dislocation, and Options Expiry / Dealer
  Hedging Pressure = `triage-ready`.
- Sideways family candidate-map note:
  `research/signal_observation/SIDEWAYS_FAMILY_NOTE.md`. PROPOSED /
  CANDIDATE MAP ONLY; no screening, acquisition, analysis, EXPLORE,
  validation, implementation, readiness, or new stage authorized.
- Signal idea generator:
  `research/signal_observation/SIGNAL_IDEA_GENERATOR.md`.
- Setup D hypothesis note:
  `research/signal_observation/SETUP_D_HYPOTHESIS.md`.
- Pre-D1 decision gate:
  `docs/PRE_D1_DECISION_GATE.md`.
- D1 funding cheap-falsification design lock:
  `docs/STAGE_54_SQ_D1_FUNDING_CHEAP_FALSIFICATION_DESIGN_LOCK.md`.
  Independent review verdict: PASS.
- Pre-D1 funding data path availability decision gate:
  `docs/PRE_D1_FUNDING_DATA_PATH_AVAILABILITY_DECISION_GATE.md`.
  Gate recommendation: `PROCEED_TO_D1_PUBLIC_DATA_ACQUISITION_DESIGN` because
  repo inspection found no committed reusable D1-ready funding-rate history
  aligned with OHLCV. Owner has accepted this gate outcome.
- D1 public funding data acquisition design lock:
  `docs/STAGE_54_SQ_D1_FUNDING_DATA_ACQUISITION_DESIGN_LOCK.md`.
  Accepted and committed (`10617b7`). Selected candidate: Binance USDT-M public
  funding REST API, BTCUSDT/ETHUSDT/SOLUSDT, 8h interval, locked window
  2022-01-01T00:00:00Z to 2023-12-17T12:00:00Z. Reserved future formal
  validation window: 2024-01-01 onwards.
- D1 funding data acquisition completed (`93f4d0f`):
  `research/signal_observation/setup_d_d1_funding_acquisition/`.
  Result: `FUNDING_DATA_ACQUIRED`. BTCUSDT and ETHUSDT: quality PASS (2,147 rows
  each, all 8h intervals, no gaps, window-bounded). SOLUSDT: RETAINED /
  FLAGGED — `NON_STANDARD_INTERVALS_FOUND` (2,222 rows; 101 sub-8h gaps, 98×2h
  and 3×4h, clustered 2022-11-09 to 2022-11-18 / FTX collapse period). SOLUSDT
  variable intervals are a genuine funding-stress marker, not a data defect.
  SOLUSDT must not be silently normalized, discarded, or mixed into clean 8h
  carry analysis without an explicit analysis/harness design decision. Full
  `FUNDING_DATA_PASS` label and D1 analysis design lock remain HOLD pending
  SOLUSDT interval policy and harness design.
- Reusable cheap-falsification harness proposal created (PROPOSED; requires
  independent review and Owner authorization before any screening task):
  `docs/STAGE_54_SQ_REUSABLE_CHEAP_FALSIFICATION_HARNESS_PROPOSAL.md`.
  Defines three template families (Event-Triggered, Continuous-State,
  Cross-Venue Dislocation), pre-registration and held-out discipline,
  multiple-comparisons policy, STRONG_ANOMALY_CANDIDATE escalation label,
  grail/anomaly philosophy, and batch screening model for current backlog
  candidates. D1 funding carry / stress is the prototype candidate. D1 analysis
  design lock remains HOLD until SOL interval policy, harness review, and a
  separate D1 analysis design lock are all authorized.
- Off-repo Setup D funding EXPLORE completed as non-evidence /
  non-validation; orientation label: `EXPLORE_MIXED`. No formal Setup D status
  promotion occurred.
- Liquidation Cascades triage:
  `research/signal_observation/LIQUIDATION_CASCADES_TRIAGE.md`.
  Triage result: `Advance to hypothesis note`.
- Setup E branch is now `Post-Liquidation Exhaustion Reversal`.
- Setup E hypothesis note:
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
  permit Hyperliquid markets/liquidations endpoint access. Outcome:
  `ACCESS_BLOCKED_PLAN_RESTRICTION`. Historical depth, BTC/ETH/SOL coverage,
  and held-out window remain unconfirmed. No records retrieved; no
  contamination risk.
- Next owner-level action: upgrade thegraph.market account to a plan that
  includes Hyperliquid/markets endpoint access and re-enter bounded check. Or
  authorize Research Scout to identify alternative liquidation data source
  paths for E1.
- Process docs updated: Hard Research Boundaries and Research Integrity Rules
  added to `docs/BOUNDARIES.md` and `docs/HOW_WE_WORK.md`. Research Scout /
  Data Source Investigator role added to `docs/AGENT_PROMPTS.md` and
  `docs/HOW_WE_WORK.md`.
- Secondary next option: OKX C7 evidence if reachability is restored
  (currently blocked by Cloudflare 1010 ASN from this host).
- All work remains research-only unless the Human Owner explicitly authorizes
  a different lane.

## Deferred / Watchlist

These backlog items are not authorization to implement.

- no-network guard tests across all research modules.
- downloader isolation in high_vol_validation.
- Setup/Family Registry doc.
- signal_observation README expansion.
- config/exchange.yaml venue check/change.
- lightweight post-push consistency-check routine.
- Codex local workflow smoke: verified on Windows VS Code with .venv activation and targeted config/exchange tests.

## Startup Rule

Routine startup should not require reading full historical docs unless this file
is missing, stale, or conflicting. If this file conflicts with latest commits/code,
report the conflict before proposing work.

`docs/PROGRESS.md` and `docs/STAGE_STATUS.md` are historical/deeper context. Use
them only when `docs/CURRENT_STATE.md` is missing, stale, conflicting with
commits/code, or insufficient for the owner's question.
