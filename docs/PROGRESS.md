# Progress Log
## Session: 2026-04-24 (updated end-of-session)
pytest: 181 passed, 5 warnings
alembic head: 0008_unique_trade_candidates_signal_id
Shadow trading: COMPLETE
Paper trading: VALIDATED CONTOUR (Stage 52B.41)
Live trading: NOT READY — P1 items pending

## Completed stages
23-42, 38c, 38d, 43, 44, 45, 46, 47, 48, 49, 50, 51
52A, 52C, 52B.3, 52B.4, 52B.23, 52B.27
53A.1, 53A.3
Research: B1, B4, B4.1, B4.2

## Active
Stage LH-1 live-hardening — P1 items remaining before full live-readiness audit

## Security fixes (2026-04-24)

Security audit completed — 9 fixes implemented (S-1 through S-9). `docs/SECURITY.md` created.

S-1: Duplicate-execution path now emits `position_open_failed` journal event (was silent)
S-2: `validate_startup_auth()` enforces token minimum length (32 chars) and denylist at startup
S-3: `OrphanDetector` now runs on 60 s schedule via `orphan_scheduler` (was on-demand only)
S-4: `/halt` endpoint now writes `kill_switch_halted` journal event atomically with state change
S-5: E2E auth money-path proof — 8 test scenarios passing (`tests/test_auth_money_path.py`)
S-6: Network boundary and inter-service topology documented in `docs/SECURITY.md`
S-7: Token rotation runbook (generate → update → rolling restart → verify) in `docs/SECURITY.md`
S-8: Kill-switch error taxonomy — `AUTH_FAILURE` / `KILL_SWITCH_TIMEOUT` / `KILL_SWITCH_UNAVAILABLE` / `KILL_SWITCH_ERROR`
S-9: Kill-switch block and error paths now write `kill_switch_blocked` / `kill_switch_check_failed` journal events

## Today's fixes (2026-04-24)

TD-14 CLOSED — sync httpx converted to async across money-path:
- `libs/messaging/journal_client.py` and `apps/position_manager/infrastructure/journal_client.py` converted
- 23 additional files updated

TD-16 CLOSED — DB startup health check added to 8 services via `libs/db/startup_health.py`

TD-18 CLOSED — `OkxMarketDataFetcher` moved from `research/` to `libs/clients/okx_market_data_fetcher.py`

TD-19 (53A.12) CLOSED — DB-backed `max_open_positions` cap gate with advisory lock (closed last session, confirmed)

TD-20 CLOSED — approve/reject journaling now DB-atomic (Option A: same-transaction pattern as TD-12)

Additional fixes:
- `approve_candidate.py` HTTPError early-commit bug fixed
- `execution_service` direct import of `position_manager` replaced with `HttpPositionManagerClient`
- Execution persisted without position open: added `position_open_failed` status + journal event

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

### Deferred option: Transactional Outbox (Journal Reliability)

- Problem addressed: cross-service journal reliability when an HTTP write can fail after an authoritative DB write.
- Pattern: in one DB transaction persist `trade_candidates` plus an `outbox_events` row; a separate deliverer loop/job
  publishes outbox → `journal_events` (via HTTP or direct DB) with retries and idempotency.
- Why deferred: higher implementation surface area (schema + deliverer + operational lifecycle).
- When to revisit: after current P1 live blockers are closed, or if we move journal storage behind a true service boundary
  (no shared DB) and need guaranteed delivery semantics.
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
  - TD-14 through TD-16 remain open before live-oriented confidence
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

TD-11 closed:
- `DbJournalClient` now lives in `libs/messaging/journal_client.py`.
- Service layers use the shared client directly or thin re-export wrappers only.

TD-12 closed (LH-1.2):
- Candidate creation + `candidate_created` journaling are now atomic in DB.
- If the journal event cannot be written, the candidate is not persisted.

TD-13 closed (LH-1.3):
- `/v1/pipeline/evaluate` is retry-safe and idempotent on `signal_id`.
- `trade_candidates.signal_id` is now unique; retries return `CANDIDATE_EXISTS` instead of creating duplicates.

## Open P1 items (next session — required before live-readiness audit)

| ID | Problem | Priority |
|----|---------|----------|
| P1-1 | Dashboard hardcoded paper mode | ✅ closed |
| P1-2 | `correlation_id` lost in error responses | ✅ closed |
| P1-3 | `reconcile_scheduler` swallows exceptions silently | ✅ closed |
| P1-4 | `journal_client` dead parameter + incorrect wiring in `main.py` | ✅ closed (fixed pre-LH-1.6) |
| P1-5 | FastAPI `on_event` deprecation — migrate to `lifespan` | ✅ closed (all services use lifespan) |

## Pre-live checklist

- [x] All P0 TDs closed
- [x] P1 items resolved (see table above)
- [ ] Full audit (Claude + Codex + GPT-4)
- [x] Security audit
- [ ] Live

## TD history

TD-12: journal gap after candidate persistence ✅ closed (LH-1.2)
TD-13: response consistency / duplicate candidate ✅ closed (LH-1.3)
TD-14: sync httpx audit across money-path ✅ closed (2026-04-24)
TD-16: DB startup health check absent ✅ closed (2026-04-24)
TD-18: paper runtime fetcher coupling ✅ closed (2026-04-24)
TD-19 (53A.12): max_open_positions enforcement gap ✅ closed (2026-04-24)
TD-20: approve/reject journaling not DB-atomic ✅ closed (2026-04-24)
