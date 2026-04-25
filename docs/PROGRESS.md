# Progress Log

## Current Gate Status

Date: 2026-04-25

Stage:
LH-1 live-hardening / pre-probe hardening.

Target:
Controlled paper probe with live market data.

Not target:
- Real live exchange execution
- Unsupervised production live
- Signal quality work
- Media/AI advisory work
- LH-2 accumulation/stats work

Readiness levels:
- Docs-ready: GO — Current Gate Status reflects confirmed reality
- Code-ready: GO for controlled paper probe with live market data
- Test-ready: GO — 215 passed, 5 warnings
- Runtime-ready: PENDING — VPS proof blocked, access not yet provided

Current verdict:
- Real live execution: NO-GO
- Controlled paper probe with live market data: CONDITIONALLY GO
- Unsupervised production live: NO-GO

Last accepted evidence:
- Final Gate Diff Review completed
- pytest: 215 passed, 5 warnings
- alembic head: 0008_unique_tc_signal_id
- docker-compose binds postgres/redis to 127.0.0.1
- .env.example uses postgresql+psycopg
- EXECUTION_MODE guard raises RuntimeError at startup if not paper/dry_run (code-verified)
- validate_startup_auth enforces ≥32 char tokens + denylist at startup (code-verified)
- secrets.compare_digest used for all token comparisons (code-verified)
- kill-switch fail-closed for all 4 error classes (AUTH_FAILURE / TIMEOUT / UNAVAILABLE / ERROR) — test-proven
- open_position and close_position journal/alert failures are fail-soft after authoritative DB commit
- halt/resume state + operator_action + journal use one DB commit
- halt/resume failure-injection tests added
- execution-boundary kill-switch typed errors preserved and journaled
- stop-loss / take-profit direction validation enforced at execution boundary
- recover_position journal/alert failures are fail-soft after authoritative DB commit
- no active production call-sites remain for old commit-based position repo methods

Open owner decision:
- H-1 recover_position_use_case: CLOSED.
- Remaining owner decision: START / HOLD after VPS Runtime Proof.

Allowed work:
- VPS runtime proof (requires owner to provide access)
- docs checkpoint

Blocked work:
- VPS Runtime Proof — BLOCKED: owner has not yet provided VPS IP/hostname, SSH username, SSH key, repo path, service launch method
- LH-2 paper accumulation
- Stage 53 real exchange integration
- signal quality
- AI/media analysis
- real live execution

Next gate:
VPS Runtime Proof.

Required owner input to unblock:
- VPS IP or hostname
- SSH username
- SSH key (which key from ~/.ssh/)
- repo path on VPS
- service launch method (docker compose / systemd / uvicorn manually)

Next owner decision:
START / HOLD controlled paper probe after runtime proof.

Constraints:
- Do not claim Runtime-ready.
- Do not claim live-ready.
- Do not start paper probe.
- Do not mark LH-1 fully closed until VPS runtime proof is done.
- Keep docs consistent with source-of-truth rules.

---

## Session: 2026-04-25 (updated — VPS Runtime Proof partial)
pytest: 215 passed, 5 warnings — H-1 closed (recover_position fail-soft fix + 2 regression tests)

### VPS Runtime Proof — Static Proof Complete / Runtime Checks Pending

**Scope limitation:** Docker and Linux system commands are not available in the current Windows dev environment.
Static/code-level proof is complete. VPS-level runtime checks require direct VPS access.

---

#### SECTION 1 — Repo Proof (VERIFIED)

| Check | Result |
|-------|--------|
| `git status` | 19 expected session files modified/untracked. No unwanted changes. |
| `git diff --check` | CLEAN. LF warning on .env.example only (not a blocker). |
| `git diff --stat` | 644 insertions, 81 deletions — matches session scope. |
| `uv run pytest` | **215 passed, 5 warnings, 0 failed** |
| `uv run alembic heads` | **0008_unique_tc_signal_id** |

---

#### SECTION 2 — Network / Container Topology (PARTIALLY VERIFIED)

| Check | Result |
|-------|--------|
| docker-compose.yml postgres binding | `127.0.0.1:5432:5432` — loopback only ✅ |
| docker-compose.yml redis binding | `127.0.0.1:6379:6379` — loopback only ✅ |
| `docker compose ps` (running containers) | **PENDING — requires VPS** |
| `docker ps` (port runtime verification) | **PENDING — requires VPS** |
| `ss -lntup` (actual listening ports) | **PENDING — requires VPS (Linux only)** |
| `sudo ufw status` (firewall rules) | **PENDING — requires VPS (Linux only)** |

---

#### SECTION 3 — Env Safety (STATICALLY VERIFIED)

| Check | Result |
|-------|--------|
| POSTGRES_DSN driver | `.env.example` uses `postgresql+psycopg` (psycopg3 correct) ✅ |
| PAPER_MODE | `.env.example` has `PAPER_MODE=true` ✅ |
| EXECUTION_MODE guard | Startup `lifespan` raises `RuntimeError` if not `paper` or `dry_run` ✅ |
| Token min length | `validate_startup_auth()` enforces ≥ 32 chars + denylist, raises at startup ✅ |
| Token comparison | `secrets.compare_digest` used for all three token types ✅ |
| Service base URLs | Internal container names in .env.example (no public exposure) ✅ |
| EXECUTION_MODE at runtime | Actual VPS env vars **PENDING — requires VPS** |
| Token values at runtime | **PENDING — requires VPS** |

---

#### SECTION 4 — Kill-Switch Safety (STATICALLY VERIFIED)

| Check | Result |
|-------|--------|
| AUTH_FAILURE blocks execution | ✅ confirmed by test |
| KILL_SWITCH_TIMEOUT blocks execution | ✅ confirmed by test |
| KILL_SWITCH_UNAVAILABLE blocks execution | ✅ confirmed by test |
| KILL_SWITCH_ERROR blocks execution | ✅ confirmed by test |
| All 4 error paths write `kill_switch_check_failed` journal event | ✅ confirmed by test |
| halt route writes `kill_switch_halted` in one DB commit | ✅ confirmed by test |
| resume route writes `kill_switch_resumed` in one DB commit | ✅ confirmed by test |
| kill-switch HTTP smoke test (halt→verify→resume) | **PENDING — requires VPS** |

---

#### SECTION 5 — DB Consistency (PENDING)

- Orphan executions (filled, no position) count: **PENDING — requires VPS**
- Open positions with closed executions: **PENDING — requires VPS**
- Candidate stuck in approved/submitted: **PENDING — requires VPS**
- DB accessible and alembic current at runtime: **PENDING — requires VPS**

---

#### SECTION 6 — Service Health (PENDING)

- `systemctl list-units` for uvicorn services: **PENDING — requires VPS**
- `/ready` endpoint for each service: **PENDING — requires VPS**
- `/health` and `/version` responses: **PENDING — requires VPS**

---

#### Static Proof Verdict

**Code-level / static runtime proof: COMPLETE**

All code-derivable safety controls verified:
- EXECUTION_MODE guard enforced at startup
- Token strength enforced at startup (not request-time)
- Kill-switch fail-closed for all 4 error classes
- postgres/redis bound to loopback in compose config
- alembic at correct head
- 215 tests passing

**Runtime-ready: STILL PENDING**

VPS-specific items that must be verified on the actual deployed environment before Runtime-ready can be claimed:
1. `docker compose ps` — containers actually up
2. `ss -lntup` — no unintended external port exposure
3. `sudo ufw status` — firewall active and configured
4. EXECUTION_MODE and token values in actual deployed `.env`
5. Kill-switch HTTP smoke test (halt → verify `kill_switch_active=true` → resume)
6. DB consistency queries (no orphan executions, no stuck candidates)
7. Service `/ready` endpoints returning 200

**Owner decision required:** The human operator must run these 7 checks directly on the VPS before making the START / HOLD decision for the controlled paper probe.

## Session: 2026-04-24 (updated end-of-session)
pytest: 213 passed, 5 warnings (updated from 181 after final session fixes)
alembic head: 0008_unique_tc_signal_id
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
