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

- `866f201 research: add Setup C funding and regime diagnostics` - local commit
  on `main`, not pushed relative to `origin/main` at time of writing.
- `0e1454a research: add Setup C TSMOM diagnostics` - pushed.
- `dd5c8bb docs: add Tower Control GitHub source protocol` - pushed.

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
- Setup C reached PASS_CANDIDATE research-only after C2 diagnostics.
- C3 diagnostics are present in local commit `866f201` and add funding stress,
  regime decomposition, sensitivity robustness, autocorrelation interpretation,
  and direction-change frequency.
- Setup C remains research-only. No paper readiness, runtime readiness, trading
  readiness, or live readiness is claimed.
- Current research concern: material regime dependence in C3 diagnostics. The
  40-bar primary high_vol bucket is negative and low_vol is strongly positive.

## Next Allowed Work

- Review or decide on C3 diagnostics before any escalation.
- If C3 is accepted, next work should remain research-only unless the Human
  Owner explicitly authorizes a different lane.

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
