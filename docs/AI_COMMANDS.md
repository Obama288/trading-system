# AI Hot Commands - Trading System

These commands work across all AI agents (Claude, GPT, Codex).
Any AI receiving these commands must respond with the relevant context.

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

Last updated: 2026-04-22
Current pytest: 88 passed
Alembic head: 0007_create_executions

## Readiness

- Shadow trading: READY
- Paper trading: NEXT
- Live trading: NOT READY

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
| TD-11 | DbJournalClient → libs/messaging/ | P1 OPEN, blocker Live |
| TD-12 | journal gap after candidate persistence — candidate row exists without matching journal event. This is a data consistency issue, not response consistency. | P1 OPEN, blocker Live |
| TD-13 | response consistency under downstream failure — candidate may persist while runner receives timeout/error. No idempotent key per signal -> runner retry creates duplicate. | P1 OPEN, blocker Live |
| TD-14 | sync httpx audit across money-path — all sync httpx calls in async handlers must be audited. Any blocking call = potential hang under downstream failure. | P1 OPEN, blocker Live |
