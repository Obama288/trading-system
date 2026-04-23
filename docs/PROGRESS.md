# Progress Log
## Session: 2026-04-22
pytest: 88 passed
alembic head: 0007_create_executions
Shadow trading: COMPLETE
Paper trading: VALIDATED CONTOUR (Stage 52B.41)
Live trading: NOT READY

## Completed stages
23-42, 38c, 38d, 43, 44, 45, 46, 47, 48, 49, 50, 51
52A, 52C, 52B.3, 52B.4, 52B.23, 52B.27
Research: B1, B4, B4.1, B4.2

## Active
Stage 52B - live paper trading
Next: live-readiness hardening on open TDs

## Shared Rules (Project-wide Code Discipline)
1. Expand Critical Findings
- After any critical bug, inspect adjacent paths for the same failure class.
2. Enforce on Authoritative Boundaries
- Money-relevant controls must be enforced at authoritative boundaries, not only pre-checks.
3. Fix Root Cause, Not Only Symptom
- Do not treat symptom removal as full resolution.
4. Require Code + Tests + Runtime Proof
- Runtime-critical acceptance requires code, tests, and runtime confirmation.
5. Keep Shared Project Memory
- Confirmed bottlenecks, acceptance facts, and operational lessons must be written to shared docs.
6. Change One Variable at a Time
- Runtime experiments should change only one variable per test.
7. Prefer Safety Over Throughput
- Integrity/safety wins over throughput tuning.
8. Advisory Must Not Become Authority
- AI/research/advisory context must not silently become execution authority.
9. Use Minimal Safe Fixes First
- First close risk with minimal safe changes, then refactor if needed.
10. Mandatory Review After Integrity Gaps
- After critical integrity findings, review both the fix and adjacent same-class paths.
11. Docs Must Reflect Confirmed Reality
- Explicitly separate planned / implemented / runtime-validated.
12. Separate Active Issues from Residue
- Distinguish active problems from historical residue and harmless noise.

## Long-range roadmap (post current paper validation)
Planning stages below are not immediate execution steps. They are sequenced after current Stage 52B / 53A history and preserve authority boundaries.

Execution order principle:
- first hardening
- then accumulation/stats
- then offline/advisory intelligence
- then shadow portfolio control
- then authoritative portfolio control

LH-1 - live-hardening baseline
- Purpose: close live-risk TDs and stabilize runtime/response/idempotency/HTTP/health discipline before new AI roles.

LH-2 - paper history + stats truth accumulation
- Purpose: accumulate enough paper trades and stable statistics to support later analyst layers.

53A - extension points for future intelligence
- Purpose: add placeholders/config hooks/feature flags without changing authority behavior.

53B - post-trade analyst MVP
- Purpose: offline/batch analytics over journal, executions, positions, closes.

53C - ops copilot / incident analyst MVP
- Purpose: advisory ops summaries, incident grouping, operator briefing.

54A - regime analyst advisory
- Purpose: advisory-only regime context generation.

54B - review enrichment by regime
- Purpose: optional advisory regime context in review, no hard reject from AI alone.

55A - portfolio manager shadow mode
- Purpose: compute heat/concentration/correlation limits in shadow only.

55B - portfolio manager authoritative mode
- Purpose: real portfolio gating only after shadow validation.

## Accepted result
Stage 52B.27 accepted:
- orchestrator no longer hangs on unreachable journal host
- journal failure is fail-fast and surfaced explicitly

Stage 52B.39 checkpoint:
- Validated paper contour end-to-end:
  - candidate created
  - candidate approved
  - execution created (paper filled)
  - position opened
  - manual close
  - reconcile close on missing exchange snapshot
- Remaining unvalidated close-trigger branches (require exchange snapshot scenarios):
  - stop-loss trigger close
  - take-profit trigger close
  - ttl expiry trigger close
  - cancel/external exchange status branches (`cancelled` / `expired`)
- Known non-blocking issues from review:
  - close_price can be null on reconcile close -> downstream stats may compute PnL as 0
  - `PositionCloseRequest` contract/comment should be tightened before live (non-manual closes)

Stage 52B.41 final checkpoint:
- Validated paper contour:
  - candidate creation
  - approve
  - execution
  - position open
  - manual close
  - reconcile close on missing snapshot
  - stop-loss close
  - take-profit close
  - ttl expiry close
  - external cancelled close
  - external expired close
- Known non-blocking issues (paper):
  - `position_repo.to_dict` missing `@staticmethod`
  - `HttpAlertClient` uses sync `httpx.post()` (TD-14 applies; not a paper blocker with `NoopAlertClient`)
  - `close_price` nullable in some close paths can skew stats/PnL interpretation
  - `PositionCloseRequest` contract/comment should be tightened before live
- Live-only risk focus (see `docs/AI_COMMANDS.md` TD table):
  - TD-11 through TD-16 remain open before live-oriented confidence
- Status:
  - paper contour validated
  - live not ready

Stage 53A.12 confirmed risk:
- `max_open_positions` enforcement gap confirmed under paper runtime burst.
- Mechanism:
  - stale runner-side open-position snapshot (TOCTOU window)
  - max-open check applied only in pre-risk runner path
  - no authoritative re-check in approve / execution / position-open stages
- Observed result:
  - 6 open paper positions were created while config cap remained `max_open_positions: 1`
- Classification:
  - live-risk issue
  - requires explicit TD tracking before live-oriented confidence

## Open TD
TD-11: DbJournalClient -> libs/messaging/ (P1, blocker Live)
TD-12: journal gap on failure after candidate persistence (P1, blocker Live)
TD-19: max-open authoritative enforcement gap (TOCTOU / stale state) — cap checked only in runner pre-risk flow, not re-enforced transactionally at approve/execution/position-open boundary; burst can exceed `max_open_positions` (confirmed with 6 opens under cap=1). (P1, blocker Live)
