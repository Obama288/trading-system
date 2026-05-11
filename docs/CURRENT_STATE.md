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

All commits below are pushed and remote-visible on `origin/main` at `775d739`.

- `775d739` research: add Binance C7 evidence report.
- `583e724` research: add Binance cross-venue holdout data.
- `d770a05` research: add Binance public kline downloader.
- `bb6ab90` research: fix OKX bounded history pagination.
- `d41799d` docs: add concise AI handoff.

Recent HEAD records the Binance cross-venue C7 evidence run
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
- C7 cross-venue replication on Binance USDT-M Futures completed at
  `775d739`: decision **C7_PASS**, all five gate conditions independently
  satisfied. Artifacts:
  `research/signal_observation/output/binance/setup_c_c7_expanded_report.{txt,json}`.
  Observational deltas vs Bitget (not gate violations): Binance dev-only
  vt-post-cost-moderate ≈ 25% of Bitget's; SOL ≈ 70% concentration on
  Binance vs ~53% on Bitget.
- Cross-venue both-PASS **math** is supported by the C7 gate replication
  on Bitget and Binance independently. The **cross-venue decision record**
  is pending governance reconciliation: the Binance evidence was produced
  before a cross-venue design lock existed, while the post-C7 review
  record had stated that cross-venue validation required a separate design
  lock.
- C7 cross-venue design lock written to reconcile governance:
  `docs/STAGE_54_SQ_C7_CROSS_VENUE_DESIGN_LOCK.md`. It does not alter
  data, code, gates, or evidence; it records the locked envelope the
  Binance run is retroactively measured against and locks the same
  envelope for any future cross-venue work. OKX is authorized but
  deferred (Cloudflare 1010 ASN block on current host).
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
- Next step: **cross-venue decision record** after this governance
  reconciliation, parallel to `SETUP_C_C7_POST_REVIEW_DECISION.md`,
  covering Bitget + Binance both-PASS, the Binance dev-magnitude
  divergence, the SOL concentration delta, and OKX-deferred status.
  Owner-only research decision.
- Recommended next research gate after the decision record: OKX C7
  evidence if reachability is restored (currently blocked by Cloudflare
  1010 ASN from this host), or a direction-call agreement diagnostic
  comparing per-rebalance direction sign across Bitget and Binance —
  observational only, no gate or readiness change.
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
