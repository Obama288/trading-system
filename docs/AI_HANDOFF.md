# AI Handoff - Hephaestus

## Current project status

Project:
Hephaestus - Python async microservice trading system.

Current mode:
paper trading only.

Live trading:
NO-GO.

Runtime status:
- Local paper runtime: GO
- VPS paper runtime: GO
- 9 services healthy
- Current test baseline: HEAD a511e2f PASS for mocked B2a server_time smoke harness behavior only; direct no-flag latch exits 3 with authorization_required JSON; B2a tests 14 passed; tests/libs/exchange 78 passed; tests/libs/config 19 passed
- Alembic head: 0008
- execution-service confirmed ready in paper mode
- Live exchange layer: NOT IMPLEMENTED
- B1-CONFIG config-only slice: CODE/TEST COMPLETE, no runtime wiring
- Stage 53-B1 Slice 1 server-time skeleton: ACCEPTED / PUSHED at 828b64a; mocked tests only; not runtime-ready
- Stage 53-B1 Slice 2 wallet_balance: ACCEPTED / PUSHED at 66a898d; mocked tests only; not runtime-ready
- Stage 53-B1 Slice 3 open_positions: ACCEPTED / PUSHED / REMOTE-VISIBLE at 0596afb; mocked tests only; not runtime-ready
- Stage 53-B2a server_time smoke harness: ACCEPTED / PUSHED / REMOTE-VISIBLE at a511e2f; mocked tests only; direct no-flag latch exits 3; not runtime-ready; no real smoke or credentials use authorized
- Stage 53-B2b real server_time smoke: SUCCESS for server_time only; Human Owner executed exactly one real Bybit testnet server_time smoke locally after safe credential presence and hygiene checks; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only; not runtime-ready
- Stage 53-B2 permanent real-smoke preflight: safe credential presence check, safe credential hygiene check, and Human Owner external 7-day key validity confirmation are required before any real Bybit smoke gate; any missing required env var, hygiene warning, expired/uncertain key, or missing owner confirmation stops the smoke

Latest known commits:
- a511e2f feat: add Stage 53-B2 server-time smoke harness
- 0596afb feat: add Bybit B1 read-only open positions
- 66a898d feat: add Bybit B1 read-only wallet balance
- 828b64a feat: add Bybit B1 read-only server-time skeleton
- d6045ad docs: add three-lane operating model
- 43940c8 docs: sync Stage 53-B1 B1-CONFIG status
- c17c7d0 feat: add Bybit B1 read-only config settings
- 67c37f6 Merge pull request #10 from Obama288/docs/stage-53b1-owner-inputs
- 93e7767 docs: record Stage 53-B1 implementation owner inputs
- 63d14f0 docs: add Stage 53-B1 architecture plan
- 19e00a8 docs: record Stage 53-B owner decisions
- 1bd8e2a fix: implement true EMA in snapshot builder
- 5e5eb48 docs: add stage 53-B design lock
- 3b3b06f feat: add Bybit public market data adapter

---

## Closed work

- Q1-FIX-1 recover_position payload validation: MERGED
- Q1-FIX-2 freshness naive datetime handling: MERGED
- Q1-FIX-3 true EMA in snapshot builder: MERGED, regression-validated on main 1bd8e2a
- Stage 53-A: CLOSED, commit 3b3b06f
- Stage 53-B design lock: CLOSED, commit 5e5eb48
- Status docs after 53-B design lock: CLOSED, commit 69176ed
- Stage 53-B owner decision tracker: ADDED, commit e814031
- Stage 53-B1 architecture plan: ADDED in docs/STAGE_53B1_ARCHITECTURE.md
- Stage 53-B1 owner inputs: ADDED, commit 93e7767
- B1-CONFIG config-only settings: ADDED, commit c17c7d0
- Stage 53-B1 Slice 1 server-time skeleton: ACCEPTED / PUSHED, commit 828b64a
- Stage 53-B1 Slice 2 wallet_balance: ACCEPTED / PUSHED, commit 66a898d
- Stage 53-B1 Slice 3 open_positions: ACCEPTED / PUSHED / REMOTE-VISIBLE, commit 0596afb
- Stage 53-B2a server_time smoke harness: ACCEPTED / PUSHED / REMOTE-VISIBLE, commit a511e2f
- Stage 53-B2b real server_time smoke: SUCCESS, local owner-run; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only; no wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
- Live Path Audit completed
- Legacy 11-item live blocker audit completed; canonical current taxonomy is 14 live blockers.

---

## Current gate

Current gate:
Stage 53-B2b real server_time smoke checkpoint.

Stage 53-B implementation:
BLOCKED beyond accepted Slice 3 open_positions.

Stage 53-B1 implementation state:
B1-CONFIG config-only slice is complete on c17c7d0. Slice 1 server-time skeleton is accepted and pushed on 828b64a. Slice 2 wallet_balance is accepted and pushed on 66a898d. Slice 3 open_positions is accepted, pushed, and remote-visible on 0596afb. It includes get_open_positions(), open-position read-only models, Decimal numeric values, redacted repr() / model_dump(), sanitized open-position errors, and mocked tests.

Stage 53-B2a implementation state:
B2a server_time smoke harness is accepted, pushed, and remote-visible on a511e2f. It includes a server_time smoke harness, mocked tests, and a direct CLI no-flag safety latch that exits 3 with authorization_required JSON.

Stage 53-B2b smoke state:
B2b real server_time smoke succeeded for server_time only. Human Owner executed exactly one real Bybit testnet server_time smoke locally after safe credential presence and hygiene checks. Result: LASTEXITCODE=0; elapsed_ms=1534; sanitized output only. Credentials were used locally only and must not be stored or disclosed. No wallet_balance smoke, open_positions smoke, order_status, write/live methods, or service wiring was run or authorized. Runtime readiness is not confirmed.

Slice 3 classification:
- Code-ready candidate / accepted implementation checkpoint for open_positions only.
- Test-ready for mocked open_positions behavior only.
- Not runtime-ready.

Still not implemented:
- wallet_balance smoke
- open_positions smoke
- order_status
- place_order
- cancel_order
- set_leverage
- withdraw
- transfer
- live_reconcile
- live_execution
- service startup wiring
- wallet_balance/open_positions real Bybit connectivity verification
- real credential verification

Block reason:
Any implementation beyond B2a and any real smoke beyond B2b server_time requires separate explicit approval. B2d real wallet_balance smoke, open_positions smoke, order_status, and all write/live methods require separate Human Owner authorization.

Owner decisions OI-1..OI-9 are ANSWERED / APPROVED in docs/STAGE_53B_OWNER_DECISIONS.md.
No runtime implementation is authorized by the decision-sync PR, B1-CONFIG, Slice 1, Slice 2, or Slice 3.
No live trading enablement is allowed.

Next safe work:
Stage 53-B2 docs/status cleanup and static safety checks; B2c wallet_balance smoke harness implementation, B2d real wallet_balance smoke, open_positions smoke, order_status, or any write/live implementation only after explicit approval.

Stage 53-B1 maximum scope:
- Bybit only
- Testnet/demo only; first target = testnet
- Authenticated client
- First implementation endpoints: server time/connectivity, wallet balance read-only, open positions read-only
- Order status read-only deferred to a later slice
- No place order
- No cancel order
- No set_leverage
- No live reconcile
- Withdrawal permission is forbidden
- No secrets in repo, prompts, docs, or logs

Architecture plan:
- docs/STAGE_53B1_ARCHITECTURE.md
- B1-CONFIG config-only slice exists.
- Slice 1 server-time skeleton exists at 828b64a; read-only client remains library-only and exposes get_server_time() only.
- Slice 2 wallet_balance exists at 66a898d; read-only client exposes get_wallet_balance() with mocked tests only.
- Slice 3 open_positions exists at 0596afb; read-only client exposes get_open_positions() with mocked tests only.
- B2a server_time smoke harness exists at a511e2f; direct no-flag latch exits 3 with authorization_required JSON; mocked tests only.
- B1-OI-1..B1-OI-6 are ANSWERED / APPROVED for future implementation planning.
- This does not authorize runtime implementation, live trading, production private endpoints, orders, cancels, leverage changes, live reconcile, or live execution.

Current regression evidence:
- python scripts\smoke_server_time.py: LASTEXITCODE=3 with sanitized authorization_required JSON
- python -m pytest tests\scripts\test_smoke_server_time.py -q --basetemp=.pytest-temp-run: 14 passed
- python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 39 passed
- python -m pytest tests\libs\exchange -q: 78 passed
- python -m pytest tests\libs\config -q: 19 passed
- python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 33 passed
- python -m pytest tests\libs\exchange -q: 72 passed
- python -m pytest tests\libs\config -q: 19 passed
- python -m pytest tests\libs\exchange -q: 39 passed
- python -m pytest apps/market_data/tests -q: 8 passed
- python -m pytest apps -q: 163 passed
- python -m pytest -q --ignore=./research --basetemp=.pytest_tmp: 288 passed, 5 warnings
- No secrets observed.
- No live/exchange/private endpoints/orders/cancels/balances/live execution/live reconcile were enabled or observed.

---

## Current forbidden scope

- API keys
- Private endpoints
- Orders
- Cancels
- Production balances
- Live positions
- Authenticated exchange client implementation beyond separately approved Slice 3 read-only library scope
- Service startup wiring for Bybit private/read-only client
- Live execution
- Live trading enablement
- Runtime implementation
- Risk pipeline rewrites
- Orchestrator rewrites
- Position manager rewrites
- Event Bus implementation
- Redis Pub/Sub implementation
- Strategy quality filters
- News filters
- Pair ranking
- Regime detector
- Signal quality gate

---

## Stage 53 constraints - must not change

1. Pipeline order: signal -> risk -> review -> orchestrator -> execution_service -> position_manager
2. Kill-switch fail-closed: all 4 error classes (AUTH_FAILURE, KILL_SWITCH_TIMEOUT, KILL_SWITCH_UNAVAILABLE, KILL_SWITCH_ERROR) must continue to block execution
3. RiskDecision.entry_price midpoint rule: (entry_zone.min + entry_zone.max) / 2
4. execution_idempotency_key deduplication: DB-level idempotency must remain for the paper path; live adds exchange-level idempotency on top
5. Journal fail-soft after authoritative DB commit: journal write failure must not roll back a committed position or execution
6. operator_actions audit trail: every approve/reject must continue to write to operator_actions table atomically
7. max_open_positions DB cap gate with advisory lock: must remain at execution admission boundary
8. Token validation at startup: validate_startup_auth() must not be weakened

---

## Live blockers

Legacy summarized list (11 items) - not the current authoritative blocker count.
Canonical current taxonomy: 14 canonical live blockers from docs/STAGE_53_DESIGN_LOCK.md.

1. No authenticated exchange client
2. place_order.py hard-rejects non-paper mode
3. No order status polling
4. entry_price from signal not exchange fill
5. Position close is DB-only
6. No balance/margin check
7. No rate limit handling
8. No partial fill handling
9. Live reconcile is paper-only
10. Symbol format is OKX-only
11. Cancel order is DB-only

---

## Owner decisions for Stage 53-B1

OI-1..OI-9 are ANSWERED / APPROVED in docs/STAGE_53B_OWNER_DECISIONS.md.

1. OI-1: Bybit only.
2. OI-2: Testnet/demo only.
3. OI-3: Read-only balances + positions; optional order status read-only; no place/cancel orders.
4. OI-4: Env vars for local testnet; secret manager/GitHub secrets later; no secrets in repo/prompts/docs.
5. OI-5: Read-only API key only; withdrawal permission forbidden.
6. OI-6: Live trading only after full implementation + QA + regression + external review + separate explicit owner approval.
7. OI-7: Keep current authority model exactly.
8. OI-8: Authenticated client + testnet read-only balances and positions only.
9. OI-9: Full protocol: architect -> plan -> implement -> QA -> external review if needed -> PR -> merge.

These decisions authorize planning only. Stage 53-B1 implementation, live trading, order placement, cancellation, live execution, and live reconcile all require separate explicit approval.

---

## Working protocol

- Windows PowerShell uses ; not &&
- Always use python -m pytest
- Always use python -m alembic
- Always use python -m uvicorn
- Verify file edits with Get-Content after writing
- Use the 3-lane operating model in docs/HOW_WE_WORK.md: Fast Lane, Standard Lane, Protected Lane
- Fast Lane: docs/report-only scope checks; QA optional when no readiness is promoted
- Standard Lane: focused approved work; compact QA required with targeted tests/checks
- Protected Lane: live/probe readiness, authenticated/private exchange work, secrets, safety authority, runtime wiring, infra/deploy, migrations/schema, dependencies, or runtime-behavior config; explicit Human Owner authorization and mandatory QA required
- Every report must identify Agent, Task Type, Scope, Lane, Changed Files, Commands Run, Readiness Claims, Not Verified, and Decision Needed
- Definition of Done: changed + verified + commands/results + readiness claims + not verified + git status
- Do not commit without explicit owner instruction

---

## Authority rules

- Kill switch is top safety authority
- Risk is source of truth for trade admissibility
- Orchestrator coordinates but must not bypass risk/review/kill_switch
- Review does not recompute authoritative risk values
- Execution service owns order lifecycle
- Position manager owns internal position state
- Dashboard aggregates and must not mutate trading state
- Journal records and must not become trading authority

---

## Stage 54+ reminder

- State ownership and domain events draft exists at docs/architecture/STATE_AND_EVENTS_DRAFT.md
- Do not implement Event Bus before state ownership, event envelope, idempotency, retry/dead-letter, and failure behavior are accepted
- Redis is optional cache/pub-sub/ephemeral state only, not durable source of truth

---

## Reviewer checklist before any code change

- Does this change touch runtime code?
- Does this change alter pipeline order?
- Does this change weaken kill-switch fail-closed behavior?
- Does this change introduce live execution?
- Does this change use API keys or private endpoints?
- Does this change add hidden defaults for market_type?
- Does this change use float for prices/qty?
- Does this change bypass service ownership?
- Does this change mix Stage 53 safety with Stage 54 signal-quality filters?
- Are tests updated or planned?
- Is git status clean except intended files?
