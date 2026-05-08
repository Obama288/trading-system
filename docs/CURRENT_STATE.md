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

All commits below are pushed and remote-visible on `origin/main` at `d7c9106`.

- `d7c9106 research: add Setup C validation regime split diagnostic` - C5.
- `84765ab docs: update compact state after Setup C C4` - pushed.
- `3ca2f76 research: add Setup C regime normalization diagnostic` - C4, pushed.
- `866f201 research: add Setup C funding and regime diagnostics` - C3, pushed.
- `a804e13 docs: add compact agent startup state` - pushed.

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
- Setup C remains research-only. No paper readiness, runtime readiness, trading
  readiness, or live readiness is claimed.
- Escalation: **HOLD**.

## Next Allowed Work

- Owner decision on C6 fork:
  - **Fork A (recommended)**: expand dataset / out-of-time validation.
  - **Fork B**: define paper-trading prerequisites (no paper approval).
  - **Fork C**: park Setup C.
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

## Startup Rule

Routine startup should not require reading full historical docs unless this file
is missing, stale, or conflicting. If this file conflicts with `docs/PROGRESS.md`
or latest commits/code, report the conflict before proposing work.

`docs/PROGRESS.md` and `docs/STAGE_STATUS.md` are historical/deeper context. Use
them only when `docs/CURRENT_STATE.md` is missing, stale, conflicting with
commits/code, or insufficient for the owner's question.
