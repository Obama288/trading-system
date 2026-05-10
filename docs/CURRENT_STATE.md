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
- Primary research lane: Stage 54-SQ / Setup C TSMOM volatility-targeted.
- Source protocol: GitHub docs, commits, code, tests, and relevant PR metadata
  are primary; project memory is orientation only.

## Recent Commits

All commits below are pushed and remote-visible on `origin/main` at `eaa9a9d`.

- `eaa9a9d` docs: record Setup C C7 evidence pass.
- `c108197` research: add C7 expanded validation evidence report.
- `37e28ec` research: add C7 evidence artifact helpers.
- `16ae508` research: add C7 expanded Bitget holdout data.
- `c3d15d0` research: fix Bitget bounded history pagination.

Recent HEAD records the compact-state docs update for the C7 evidence pass
(decision `C7_PASS`, research-only); it does not alter the current
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
- Active research family: Setup C / TSMOM volatility-targeted.
- Setup C is **PASS_CANDIDATE research-only**. C1–C5 diagnostics complete.
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
- Setup C remains research-only PASS_CANDIDATE. Per design lock §"What C7
  Does Not Authorize", C7 PASS does not promote paper readiness, runtime
  readiness, trading readiness, probe readiness, or live readiness.
- Escalation: **HOLD**.

## Next Allowed Work

- C7 design lock written:
  `docs/STAGE_54_SQ_C7_EXPANDED_VALIDATION_DESIGN_LOCK.md`.
- C7 analyzer, expanded data, helpers, and evidence report are all
  remote-visible (analyzer `61ad028`; data `16ae508`; helpers `37e28ec`;
  evidence report `c108197`). C7 decision: **C7_PASS**.
- C7 post-review decision record:
  `research/signal_observation/SETUP_C_C7_POST_REVIEW_DECISION.md`.
- Next step: cross-venue validation of Setup C (separate design lock and
  explicit owner approval required; public-source-only; no credentials,
  no private endpoints, no paper / runtime / live readiness). Wider symbol
  universe and execution realism are deferred until cross-venue validation
  is completed and reviewed.
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
