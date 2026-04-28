# AI Hot Commands - Trading System

These commands work across all AI agents (Claude, GPT, Codex).
Any AI receiving these commands must respond with the relevant context.

## Working Protocol

### Environment defaults
- Windows PowerShell (not Bash)
- Use ; not && between commands
- Always use: python -m pytest, python -m alembic, python -m uvicorn
- Project path: E:\trading-system
- Env vars: always Process scope, never Machine

### Verify before proceed
After every file edit:
  Get-Content <file>
  Select-String <file> '<key>'
After every service start:
  Invoke-RestMethod http://127.0.0.1:<port>/health
After every migration:
  python -m alembic current
After every test run:
  Show full output — N passed, N warnings

Do not claim success from write/run alone.
Verify with independent command first.

### Operating lanes
Canonical policy: `docs/HOW_WE_WORK.md`.

Use the strictest matching lane:
- Fast Lane: docs-only, report-only, typo/status cleanup, static docs checks; no code/test/config/infra/runtime/secret/trading behavior change. QA optional if scope is bounded and no readiness is promoted.
- Standard Lane: approved focused code/test/docs work that does not touch Protected criteria. Compact QA required with targeted tests/checks.
- Protected Lane: live/probe readiness, GO/NO-GO, authenticated/private exchange client work, secrets, orders/cancels/balances/positions, live execution/reconcile, safety authority, source-of-truth boundaries, runtime wiring, deployments, infra, migrations/schema, dependencies, or runtime-behavior config. Explicit Human Owner authorization and mandatory QA required.

Lane rules:
- Human Owner keeps final authority for accept/reject, START/HOLD, GO/NO-GO, stage transitions, and risk acceptance.
- Lanes do not collapse docs-ready, code-ready, test-ready, and runtime-ready into one claim.
- A docs-only change cannot approve trading readiness, live readiness, probe readiness, implementation readiness, or runtime readiness.

### Definition of Done
Every agent report must include:
1. Agent
2. Task Type
3. Scope
4. Lane
5. Changed Files
6. Commands Run
7. Readiness Claims
8. Not Verified
9. Decision Needed

Commands Run must list exact commands and results.
Readiness Claims must separate docs/code/test/runtime.
Not Verified must explicitly state skipped tests, runtime checks, deployment checks, external review, or QA.
Decision Needed belongs to the Human Owner; use `None` only when no owner decision is needed.

### Tool roles
- Claude (Sasha) — strategy, architecture, risk analysis
- Claude Code — code review, reading files, focused fixes
- Codex — code changes and tests
- PowerShell directly — runtime, env, docker, service startup

## Commands

`!status`
Returns: current stage, last completed step, next step, pytest count, alembic head

`!rules`
Returns: all 8 authority rules verbatim

`!td`
Returns: open technical debt table with ID, problem, priority, blocker

`!stages`
Returns: completed stages and upcoming stages table

`!stack`
Returns: tech stack - Python, FastAPI, SQLAlchemy, Alembic, Docker, OKX, Redis, Postgres

`!hypothesis`
Returns: current hypotheses summary from `research/hypothesis_agent/output/HYPOTHESIS.md`
Current hypotheses are LOW confidence.
Research output is exploratory and not used in execution decisions.

`!context`
Returns: full project summary - architecture, status, rules, hypothesis, next steps

`!review`
Signals: this output needs code review by Claude (browser session)

`!checkpoint`
Signals: save current progress to `docs/PROGRESS.md` with timestamp

## Current State

Last updated: 2026-04-28 (Slice 1 server-time skeleton checkpoint)
Current stage: Stage 53-B1 planning / architecture gate + Slice 1 server-time skeleton checkpoint
Stage 53-B owner decisions: ANSWERED / APPROVED
Stage 53-B implementation beyond Slice 1: BLOCKED; separate explicit approval required
B1-CONFIG config-only slice: CLOSED on c17c7d0; no client, private API calls, service startup wiring, runtime behavior, or live enablement
Stage 53-B1 Slice 1 server-time skeleton: ACCEPTED / PUSHED on 828b64a; code-ready candidate / accepted implementation checkpoint; mocked server-time skeleton tests only; not runtime-ready
Current mode: paper trading only
Live trading: NO-GO
Current Slice 1 pytest: HEAD 828b64a PASS for mocked server-time skeleton behavior only; focused Slice 1 tests 28 passed; tests/libs/exchange 67 passed
Alembic head: 0008_unique_trade_candidates_signal_id
Canonical live blocker taxonomy: 14 canonical live blockers from docs/STAGE_53_DESIGN_LOCK.md
Owner decisions OI-1..OI-9: answered/approved in docs/STAGE_53B_OWNER_DECISIONS.md
Next allowed lane: Stage 53-B1 docs/status cleanup and static safety checks; wallet balance/open positions or further implementation requires separate explicit approval
Stage 53-B1 architecture plan: docs/STAGE_53B1_ARCHITECTURE.md
Stage 53-B1 implementation owner inputs B1-OI-1..B1-OI-6: ANSWERED / APPROVED
Stage 53-B1 first implementation scope: Bybit testnet authenticated read-only server time/connectivity, wallet balance, and open positions only; order status deferred; no place order; no cancel order; no set_leverage; no withdraw; no transfer; no live reconcile; no live execution; no production private endpoint access
Slice 1 exists: Bybit auth/signing helper; timestamp / recv_window handling; redaction helpers; minimal ServerTime model; read-only client skeleton; get_server_time() only; mocked tests
Slice 1 does not include: wallet_balance; open_positions; order_status; place_order; cancel_order; set_leverage; withdraw; transfer; live_reconcile; live_execution; service startup wiring; real Bybit connectivity verification; real credential verification
Withdrawal permission: forbidden
Secrets: no secrets in repo, prompts, docs, or logs
Stage 53-A: CLOSED, commit 3b3b06f
Stage 53-B design lock: CLOSED, commit 5e5eb48
Stage 53-B owner decision tracker: ADDED, commit e814031
Stage 53-B gate/status cleanup: ADDED, commit 3d72ba8
Stage 53 design lock decisions cleanup: ADDED, commit ff2f30c
Stage 53-B1 architecture plan: ADDED
Stage 53-B1 B1-CONFIG: CLOSED, commit c17c7d0
Stage 53-B1 Slice 1 server-time skeleton: CLOSED, commit 828b64a
Q1-FIX-3 true EMA: MERGED, commit 1bd8e2a
B1-CONFIG / current regression gate:
- python -m pytest tests\libs\config -q: 19 passed
- python -m pytest tests\libs\exchange -q: 39 passed
- python -m pytest apps/market_data/tests -q: 8 passed
- python -m pytest apps -q: 163 passed
- python -m pytest -q --ignore=./research --basetemp=.pytest_tmp: 288 passed, 5 warnings
No live/exchange/private endpoints/orders/cancels/balances/live execution/live reconcile were enabled or observed.
No trading readiness, live readiness, probe readiness, or runtime readiness is approved by Slice 1.

> **Source of truth**: `docs/PROGRESS.md` is authoritative. If this file conflicts with PROGRESS.md, PROGRESS.md wins.

## Readiness

- Shadow trading: COMPLETE
- Paper trading: VALIDATED CONTOUR (Stage 52B.41)
- Live trading: NO-GO
- Stage 53-B implementation beyond Slice 1: BLOCKED; separate explicit approval required

## Stage Map

- Stage 43 - Dashboards MVP
- Stage 44 - Operator audit hardening
- Stage 45 - Approve -> execution rollback (MVP)
- Stage 46 - Kill switch enforcement in orchestrator
- Stage 47 - Execution store DB migration
- Stage 48 - End-to-end pipeline tests
- Stage 49 - Observability
- Stage 50 - Statistics MVP
- Stage 51 - Statistics breakdown
- Stage 52 - Paper trading validation
- Stage 53 - Real exchange integration
- Stage 54 - Reconciliation layer
- Stage 55 - Advanced observability

## Database

The system database currently contains exactly these 8 tables:

1. `journal_events`
2. `system_state`
3. `trade_candidates`
4. `operator_actions`
5. `positions`
6. `position_events`
7. `incidents`
8. `executions`

## SOURCE OF TRUTH (CRITICAL)

- admissibility -> `risk_engine`
- kill state -> `system_state` / `kill_switch`
- execution state -> `executions`
- position state -> `positions`
- audit -> `operator_actions` + `journal_events`
- stats truth -> `positions` + `executions`

## Statistics Truth

Dashboard and performance statistics must be derived only from authoritative trading data.

- Source: `positions` + `executions`
- Not source: `research/hypothesis_agent`

Research statistics are advisory and must not be used for performance evaluation.

PnL must be defined as:
- LONG: `(close_price - entry_price) * quantity`
- SHORT: `(entry_price - close_price) * quantity`

The dashboard stats endpoint must reflect:
- `total_trades`
- `win_rate`
- `pnl`
- `avg_rr`

## Authority Mapping (Source of Truth)

| Field | Source of Truth | Service | Notes |
|------|----------------|--------|------|
| entry_price | RiskDecision | risk_engine | midpoint(entry_zone) |
| approved | operator_action_repo | orchestrator | never inferred |
| kill_switch | system_state | kill_switch | must be checked before execution |
| execution_status | executions table | execution_service | authoritative |
| position_state | positions table | position_manager | authoritative |
| freshness | market_data | market_data | single implementation |

## Enforcement Rules

1. No service may override authoritative fields downstream.
2. Redis must never be used as a source of truth for:
   - execution state
   - candidate status
   - kill switch
3. LLM outputs must be treated as advisory and validated.
4. All execution-relevant decisions must originate from DB-backed data.
5. Any mismatch between DB and cache must default to DB.

## Pipeline

`signal_engine -> risk_engine -> review_gateway -> orchestrator -> execution_service -> position_manager`

Authority boundaries remain unchanged:
- `risk_engine` decides admissibility
- `review_gateway` does not recompute risk
- `orchestrator` cannot bypass risk or kill switch
- `execution_service` makes no strategic decisions

## WHAT MUST NOT BE CHANGED

These invariants are critical and must remain unchanged unless there is an explicit architectural decision to replace them end-to-end.

- Authority rules must remain intact.
- Pipeline order must remain: `signal_engine -> risk_engine -> review_gateway -> orchestrator -> execution_service -> position_manager`
- `RiskDecision.entry_price` logic must remain the midpoint rule: `midpoint(entry_zone)`
- Advisory vs authoritative separation must remain intact:
  - research, hypotheses, LLM reasoning, and summaries are advisory only
  - risk, kill state, executions, positions, operator audit, and journal data are authoritative in their defined domains

## Journal as Memory Backbone

All critical events must be recorded in `journal_events`:
- `candidate_created`
- `risk_decision`
- `review_result`
- `operator_approve/reject`
- `execution_started`
- `execution_completed`

Journal is the primary source for:
- post-trade analysis
- debugging
- performance evaluation

## LLM Safety Boundary

LLM outputs:
- cannot directly trigger execution
- cannot modify authoritative fields
- must be validated before use

Allowed:
- reasoning
- summaries
- recommendations

Forbidden:
- direct trade decisions
- overriding risk decisions

## Research Status

Current hypotheses are LOW confidence.
Research output is exploratory and not used in execution decisions.
Reference file: `research/hypothesis_agent/output/HYPOTHESIS.md`

Research and hypotheses are advisory only, not authoritative.
They can inform analysis, filtering, and future paper-trading work, but they are not allowed to override execution authority or risk decisions.

## Technical Debt

| ID | Description | Status |
|----|-------------|--------|
| TD-01 | execution rollback | ✅ closed |
| TD-02 | kill switch enforcement | ✅ closed |
| TD-03 | InMemoryExecutionStore → DB | ✅ closed |
| TD-04 | journal write best-effort | ✅ closed |
| TD-05 | Risk↔Review price contract | ✅ closed |
| TD-06 | httpx AsyncClient | ✅ closed |
| TD-07 | journal persistence | ✅ closed |
| TD-08 | freshness duplicate | ✅ closed |
| TD-09 | hardcoded URLs | ✅ closed |
| TD-10 | JournalClient duplicate | ✅ closed |
| TD-11 | DbJournalClient → libs/messaging/ | ✅ closed |
| TD-12 | journal gap after candidate persistence — candidate row exists without matching journal event. Fixed by making candidate + `candidate_created` journal event atomic in DB (no silent success). | CLOSED (LH-1.2) |
| TD-13 | response consistency under downstream failure — retry-safe evaluate: de-duplicate `trade_candidates` by `signal_id` (unique) and return `CANDIDATE_EXISTS` instead of creating duplicates. | CLOSED (LH-1.3) |
| TD-14 | sync httpx audit across money-path � all external HTTP calls in money-path async handlers (evaluate, approve, execution) must use fail-fast async client. Any blocking sync call = potential hang under downstream failure. | ✅ closed (2026-04-24) |
| TD-15 | evaluate_pipeline response contract undefined — caller cannot distinguish success vs partial journal failure (TD-12). Fixed by removing the partial-success state and returning explicit error codes. | CLOSED (LH-1.2) |
| TD-16 | DB startup health check absent � services start without verifying DB reachability. First request fails instead of startup failing fast. | ✅ closed (2026-04-24) |
| TD-17 | reconcile scheduler absent � position_manager has no background loop for periodic reconcile_positions_use_case calls. Without it: stop_loss, take_profit, ttl do not trigger automatically. Open positions accumulate without closing. Stats endpoint shows 0 closed trades. | ? CLOSED (Stage 53A.1) |
| TD-18 | paper runtime fetcher coupling — position_manager scheduler imports OkxMarketDataFetcher from research.hypothesis_agent. Move to libs/clients or apps/market_data before live hardening. | ✅ closed (2026-04-24) |
| TD-19 | max_open_positions TOCTOU — cap-gate at execution admission | ✅ closed |
