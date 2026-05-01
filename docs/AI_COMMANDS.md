# AI Hot Commands - Trading System

These commands work across all AI agents (Claude, Tower Control Architect, Codex).
Any AI receiving these commands must respond with the relevant context.

## Working Protocol

### Context recovery order
1. Read `docs/PROGRESS.md` first.
2. Read `docs/AI_COMMANDS.md`.
3. Read `docs/HOW_WE_WORK.md`.
4. Read `docs/AI_HANDOFF.md` and `docs/CONTEXT.md`.
5. Read current-stage docs only as needed.
6. Treat chat memory as secondary.
7. If chat memory conflicts with `docs/PROGRESS.md`, `docs/PROGRESS.md` wins.

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
- Tower Control Architect - GPT project-control architect, context recovery, gate discipline, prompt architecture, and readiness separation only
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

`!startup`
Returns: repo, primary source of truth, current gate, mode, live status, key blockers, next allowed lane, and no-edit/no-branch/no-commit/no-probe/no-secrets reminder

`!sync`
Returns: branch/head, dirty files, dirty-file classification, current `docs/PROGRESS.md` gate, allowed files, blocked files, and GO/HOLD before edits

## Current State

Last updated: 2026-04-29 (B2c.1c/B2d blocked - unavailable usable Bybit testnet API access)
Current stage: Stage 54-BG planning active; Bybit Stage 53-B2c.1c/B2d private real testnet path remains blocked due unavailable usable Bybit testnet API access
Stage 53-B owner decisions: ANSWERED / APPROVED
Stage 53-B implementation beyond B2a: BLOCKED; separate explicit approval required
B1-CONFIG config-only slice: CLOSED on c17c7d0; no client, private API calls, service startup wiring, runtime behavior, or live enablement
Stage 54-BG planning boundary: Bitget Demo / Simulated Trading is the primary planning candidate; proposed env namespace = `BITGET_BG1_ENVIRONMENT`, `BITGET_BG1_API_KEY`, `BITGET_BG1_API_SECRET`, `BITGET_BG1_PASSPHRASE`; no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback in the first implementation; production/mainnet must fail closed; no private Bitget smoke, wallet/balance/positions real smoke, order_status, write/live methods, service wiring, or readiness claims are authorized
Stage 53-B1 Slice 1 server-time skeleton: ACCEPTED / PUSHED on 828b64a; code-ready candidate / accepted implementation checkpoint; mocked server-time skeleton tests only; not runtime-ready
Stage 53-B1 Slice 2 wallet_balance: ACCEPTED / PUSHED on 66a898d; code-ready candidate / accepted implementation checkpoint; mocked wallet_balance tests only; not runtime-ready
Stage 53-B1 Slice 3 open_positions: ACCEPTED / PUSHED / REMOTE-VISIBLE on 0596afb; code-ready candidate / accepted implementation checkpoint; mocked open_positions tests only; not runtime-ready
Stage 53-B2a server_time smoke harness: ACCEPTED / PUSHED / REMOTE-VISIBLE on a511e2f; code-ready candidate / accepted implementation checkpoint; mocked tests only; direct no-flag latch exits 3; not runtime-ready; no real smoke or credentials use authorized
Stage 53-B2b real server_time smoke: SUCCESS for server_time only; Human Owner executed exactly one real Bybit testnet server_time smoke locally after safe credential presence and hygiene checks; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only; credentials used locally only and must not be stored or disclosed; not runtime-ready
Stage 53-B2c wallet_balance smoke harness: ACCEPTED / PUSHED / REMOTE-VISIBLE on c9b1337; code-ready candidate / accepted implementation checkpoint; mocked tests only; direct no-flag latch exits 3; --allow-real-smoke required for real-capable path; not runtime-ready; no real wallet_balance smoke or credentials use for B2c implementation
Stage 53-B2c.1a authenticated readiness hardening: ACCEPTED / PUSHED / REMOTE-VISIBLE on 189cb0a; code-ready/test-ready only for mocked/local hardening; server_time now uses unsigned public /v5/market/time; get_server_time no longer requires credentials; private reads fail closed without credentials; private signed reads include X-BAPI-SIGN-TYPE: 2; signed GET query handling is deterministic and consistent with what is sent; wallet_balance signs/sends accountType=UNIFIED; safe retCode classifications added for 10002/10003/10004/10005/10006/10007/10010; 10006 remains exit code 2 / inconclusive; no query-api, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
Stage 53-B2c.1b query-api read-only preflight harness: ACCEPTED / PUSHED / REMOTE-VISIBLE on 00d84d8; code-ready/test-ready only for mocked query-api preflight behavior; get_query_api_info() supports signed read-only GET /v5/user/query-api; sanitized ApiKeyInfo model; scripts/smoke_query_api.py exists; no-flag latch exits 3 with sanitized authorization_required JSON; success output exact approved field set; operation and endpoint_family absent from success output; unsafe readOnly/permissions/expiry metadata fail closed; stale/malformed expiredAt regression tests exist; rate limit remains exit 2 / inconclusive; no real query-api execution, credentials use, Bybit call, real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
Stage 53-B2c.1c real query-api preflight: BLOCKED; attempted once and failed safely with retCode=10003, error_category=invalid_key_or_environment, LASTEXITCODE=1; likely ordinary/mainnet Bybit key used against testnet API endpoint, or no usable Bybit testnet API access; no further query-api retry is authorized
Stage 53-B2d real wallet_balance testnet smoke: BLOCKED / NO-GO because usable Bybit testnet API credentials are unavailable; ordinary/mainnet Bybit key must not be substituted into the testnet flow; any mainnet read-only smoke requires a new separately authorized stage, not continuation of B2d
Stage 53-B2 testnet API access runbook: DOCUMENTED in docs/STAGE_53B2_SMOKE_PLAN.md; use https://testnet.bybit.com and https://testnet.bybit.com/app/user/api-management; keys from www.bybit.com / ordinary Bybit mainnet must not be used in the Stage 53-B2 testnet flow; use API Transaction / Транзакция API, read-only only, withdrawal/transfer/trade/order/write disabled; BYBIT_B1_ENVIRONMENT=testnet; BYBIT_B1_API_KEY and BYBIT_B1_API_SECRET must come from the same testnet key pair; BYBIT_API_KEY / BYBIT_API_SECRET should be missing during B2 flow; retCode 10003 troubleshooting and safe restart path are documented
Stage 53-B2 Pit-stop audit: RECORDED as audit-only, not an implementation gate; repo aligned at 8153c61; full local regression 408 passed / 5 warnings; targeted suites passed with tests/scripts 60, tests/libs/exchange 99, tests/libs/config 19; server_time, wallet_balance, and query_api no-flag latches exited 3; checked BYBIT env names were missing; `.pytest-temp-run/` generated artifact was removed; no runtime/trading/live/probe readiness is claimed
Stage 53-B2c.1 authenticated readiness audit / query-api preflight decision: B2c.1a and B2c.1b are mocked/local implementation checkpoints only; private real testnet path is blocked due unavailable usable Bybit testnet API access
Current mode: paper trading only
Live trading: NO-GO
Current B2c.1a pytest: HEAD 189cb0a PASS for mocked/local authenticated-readiness hardening only; server_time no-flag latch LASTEXITCODE=3; wallet_balance no-flag latch LASTEXITCODE=3; tests/scripts 40 passed; tests/libs/exchange 86 passed; tests/libs/config 19 passed
Alembic head: 0008_unique_trade_candidates_signal_id
Canonical live blocker taxonomy: 14 canonical live blockers from docs/STAGE_53_DESIGN_LOCK.md
Owner decisions OI-1..OI-9: answered/approved in docs/STAGE_53B_OWNER_DECISIONS.md
Next allowed lane: Stage 53-B2 docs/status cleanup and local/mocked architecture improvements; B2c.1c query-api retry, B2d real wallet_balance smoke, mainnet read-only smoke, open_positions smoke, order_status, or any write/live implementation requires separate explicit approval
Stage 53-B1 architecture plan: docs/STAGE_53B1_ARCHITECTURE.md
Stage 53-B1 implementation owner inputs B1-OI-1..B1-OI-6: ANSWERED / APPROVED
Stage 53-B1 first implementation scope: Bybit testnet authenticated read-only server time/connectivity, wallet balance, and open positions only; order status deferred; no place order; no cancel order; no set_leverage; no withdraw; no transfer; no live reconcile; no live execution; no production private endpoint access
Slice 1 exists: Bybit auth/signing helper; timestamp / recv_window handling; redaction helpers; minimal ServerTime model; read-only client skeleton; get_server_time() only; mocked tests
Slice 2 exists: get_wallet_balance(); wallet balance read-only models; Decimal numeric values; redacted repr() / model_dump(); sanitized wallet errors; mocked tests
Slice 3 exists: get_open_positions(); open-position read-only models; Decimal numeric values; redacted repr() / model_dump(); sanitized open-position errors; mocked tests
B2a exists: server_time smoke harness; mocked tests; direct no-flag latch exits 3 with authorization_required JSON
B2b exists: real testnet server_time smoke success; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only
B2b does not include / authorize: wallet_balance smoke; open_positions smoke; order_status; place_order; cancel_order; set_leverage; withdraw; transfer; live_reconcile; live_execution; service startup wiring; runtime readiness; trading readiness; live readiness; probe readiness
B2c exists: wallet_balance smoke harness; tests/scripts/test_smoke_wallet_balance.py; mocked tests only; direct no-flag latch exits 3 with authorization_required JSON; --allow-real-smoke required; mocked success output includes only endpoint/status/exchange/account_type/coins_count/elapsed_ms
B2c does not include / authorize: real wallet_balance smoke; credentials use for B2c implementation; open_positions smoke; order_status; place_order; cancel_order; set_leverage; withdraw; transfer; live_reconcile; live_execution; service startup wiring; runtime readiness; trading readiness; live readiness; probe readiness
B2c.1a exists: unsigned public server_time methodology; get_server_time no longer requires credentials; private reads fail closed without credentials; signed private reads include X-BAPI-SIGN-TYPE: 2; deterministic signed/sent GET query handling; wallet_balance signs/sends accountType=UNIFIED; safe retCode categories for 10002/10003/10004/10005/10006/10007/10010; server_time no-flag latch LASTEXITCODE=3; wallet_balance no-flag latch LASTEXITCODE=3; tests/scripts 40 passed; tests/libs/exchange 86 passed; tests/libs/config 19 passed
B2c.1a does not include / authorize: query-api; real wallet_balance smoke; open_positions smoke; order_status; place_order; cancel_order; set_leverage; withdraw; transfer; live_reconcile; live_execution; service startup wiring; runtime readiness; trading readiness; live readiness; probe readiness
B2c.1b exists: get_query_api_info() signed read-only GET /v5/user/query-api support; sanitized ApiKeyInfo model; scripts/smoke_query_api.py; tests/scripts/test_smoke_query_api.py; direct no-flag latch exits 3; exact success output field set; unsafe readOnly/permissions/expiry metadata fail closed; stale/malformed expiredAt tests; rate limit exit 2 / inconclusive
B2c.1b does not include / authorize: real query-api execution; credentials use; Bybit call; real wallet_balance smoke; open_positions smoke; order_status; place_order; cancel_order; set_leverage; withdraw; transfer; live_reconcile; live_execution; service startup wiring; runtime readiness; trading readiness; live readiness; probe readiness
B2c.1c attempted once: real query-api preflight failed safely with retCode=10003 invalid_key_or_environment and LASTEXITCODE=1; likely mainnet/testnet key-environment mismatch or no usable Bybit testnet API access; no query-api retry is authorized
B2d blocked: real wallet_balance testnet smoke is NO-GO because usable Bybit testnet API credentials are unavailable; ordinary/mainnet key must not be substituted into the testnet flow; any mainnet read-only smoke requires a new separately authorized stage
B2 testnet access runbook exists: safe restart path is safe env presence/hygiene check, no-flag latch LASTEXITCODE=3, explicit Human Owner authorization, exactly one real query-api preflight, and no automatic retry; B2d remains blocked until query-api preflight succeeds or Human Owner explicitly accepts a documented alternative
B2 Pit-stop backlog: clean async mock warnings; add env-isolation guard tests; add static guard for generic BYBIT_API_KEY/BYBIT_API_SECRET in B2 flow; follow-up audit on transaction ownership; follow-up audit on handler-level log redaction; future authority map / reconciliation / TradingState / OMS planning; dependency and secret-scan review; periodic docs source-of-truth audit
B2c.1 required before any future B2d reconsideration: audit signing/query-string behavior, signed vs unsigned server_time, X-BAPI-SIGN-TYPE: 2, query-api scope decision, safe retCode classification, key active/not expired wording, and usable testnet API access
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
Stage 53-B1 Slice 2 wallet_balance: CLOSED, commit 66a898d
Stage 53-B1 Slice 3 open_positions: CLOSED, commit 0596afb
Stage 53-B2a server_time smoke harness: CLOSED, commit a511e2f
Stage 53-B2b real server_time smoke: CLOSED, local owner-run success
Stage 53-B2c wallet_balance smoke harness: CLOSED, commit c9b1337
Stage 53-B2c.1a authenticated readiness hardening: CLOSED, commit 189cb0a
Stage 53-B2c.1b query-api read-only preflight harness: CLOSED, commit 00d84d8
Stage 53-B2c.1c real query-api preflight: BLOCKED, local owner-run retCode=10003 invalid_key_or_environment
Stage 53-B2d real wallet_balance testnet smoke: BLOCKED / NO-GO, usable testnet API credentials unavailable
Stage 53-B2 testnet API access runbook: DOCUMENTED, no real retry authorized
Stage 53-B2 Pit-stop audit: RECORDED, audit-only, no readiness promoted
Q1-FIX-3 true EMA: MERGED, commit 1bd8e2a
B1-CONFIG / current regression gate:
- python -m pytest tests\libs\config -q: 19 passed
- python -m pytest tests\libs\exchange -q: 39 passed
- python -m pytest apps/market_data/tests -q: 8 passed
- python -m pytest apps -q: 163 passed
- python -m pytest -q --ignore=./research --basetemp=.pytest_tmp: 288 passed, 5 warnings
No live/exchange/private endpoints/orders/cancels/balances/live execution/live reconcile were enabled or observed.
No trading readiness, live readiness, probe readiness, real query-api retry, real wallet_balance smoke, mainnet smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness is approved by B2c.1c/B2d blocked-state docs.

> **Source of truth**: `docs/PROGRESS.md` is authoritative. If this file conflicts with PROGRESS.md, PROGRESS.md wins.

## Readiness

- Shadow trading: COMPLETE
- Paper trading: VALIDATED CONTOUR (Stage 52B.41)
- Live trading: NO-GO
- Stage 53-B implementation beyond B2a: BLOCKED; separate explicit approval required

## Stage Map

Official current stage and gate remain defined by `docs/PROGRESS.md`.

## Historical Stage Groups

These groups preserve pre-Stage-43 project chronology without assigning exact
stage numbers that are not recorded in this file.

- Stage Group A - Architecture foundation: money-path, authority rules, service boundaries, deterministic control, advisory-only LLM boundary.
- Stage Group B - Paper trading core: signal, risk, review, orchestrator, paper execution, position manager, journal/audit flow.
- Stage Group C - Safety and authority hardening: kill-switch authority, DB source-of-truth rules, operator actions, idempotency, max_open_positions guard, fail-closed behavior.
- Stage Group D - Paper runtime validation: local paper runtime, VPS paper runtime, 9 services healthy, execution-service paper mode.
- Stage Group E - Quality and regression cleanup: Q1 audit backlog, recover_position payload validation, freshness datetime handling, true EMA, regression baseline.
- Stage Group F - Exchange-readiness preparation: Stage 53 design lock, Bybit public adapter, Bybit read-only/private-testnet planning, smoke harnesses, blocked Bybit B2 real private testnet path.

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
