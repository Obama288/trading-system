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
- Primary research lane: hypothesis-first future setup discussion; Setup C is
  parked from active progression after DR1 Binance recent rerun LOW.
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
- Active research family: none. Setup C / TSMOM volatility-targeted is parked
  from active progression.
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

## Next Allowed Work

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
- Next fork: define paper-prerequisites docs-only, without approving paper
  trading. Not runtime, paper, trading, probe, or live readiness.
- Setup C paper-prerequisites design lock:
  `docs/STAGE_54_SQ_SETUP_C_PAPER_PREREQUISITES_DESIGN_LOCK.md`.
  Next step is independent review; it defines prerequisites only and does not
  approve paper trading.
- Setup C paper-prerequisites proposal:
  `research/signal_observation/SETUP_C_PAPER_PREREQUISITES_PROPOSAL.md`.
  Next step is independent review; it does not approve paper trading or any
  readiness promotion.
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
  `research/signal_observation/RESEARCH_CANDIDATE_BACKLOG.md`. Funding Carry /
  Funding Stress is triaged as `advanced-to-hypothesis`.
- Setup D hypothesis note:
  `research/signal_observation/SETUP_D_HYPOTHESIS.md`.
- Pre-D1 decision gate:
  `docs/PRE_D1_DECISION_GATE.md`. Next step is independent review / owner
  decision on the gate; do not open D1 design lock, data acquisition,
  implementation, or backtest before that review/decision.
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
is missing, stale, or conflicting. If this file conflicts with `docs/PROGRESS.md`
or latest commits/code, report the conflict before proposing work.

`docs/PROGRESS.md` and `docs/STAGE_STATUS.md` are historical/deeper context. Use
them only when `docs/CURRENT_STATE.md` is missing, stale, conflicting with
commits/code, or insufficient for the owner's question.
