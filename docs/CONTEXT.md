# Hephaestus Context

## Project

- Name: Hephaestus
- Type: Python async microservice trading system
- Current mode: paper trading only
- Live trading: forbidden until Stage 53 live blockers are closed

## Current runtime status

- Local paper runtime: GO
- VPS paper runtime: GO
- VPS provider: Beget
- VPS OS: Ubuntu 24.04
- VPS IP: 45.145.5.254
- Python: 3.12.3
- Docker: 29.4.1
- Services: 9 healthy
- Tests: HEAD a511e2f PASS for mocked B2a server_time smoke harness behavior only; direct no-flag latch exits 3 with authorization_required JSON; B2a tests 14 passed; tests/libs/exchange 78 passed; tests/libs/config 19 passed
- Alembic head: 0008
- execution-service: ready, mode=paper

## Stage 53-A result

- Stage 53-A: CLOSED
- Commit: 3b3b06f feat: add Bybit public market data adapter
- Tests added: 39 (Stage 53-A mocked unit tests)
- Total tests: 250 passed, 5 warnings
- Public read-only smoke: PASS (live Bybit API, BTC-USDT/linear)

## Stage 53-B design lock result

- Stage 53-B design lock: CLOSED
- Commit: 5e5eb48 docs: add stage 53-B design lock
- Owner decisions: ANSWERED / APPROVED
- Runtime/client implementation: B2a server_time smoke harness accepted/pushed/remote-visible at a511e2f; no runtime/service wiring; no real smoke executed; no credentials used

## Q1 fix and regression status

- Q1-FIX-1 recover_position payload validation: MERGED
- Q1-FIX-2 freshness naive datetime handling: MERGED
- Q1-FIX-3 true EMA in snapshot builder: MERGED
- Regression gate: PASS on main 1bd8e2a; B1-CONFIG green at c17c7d0; Slice 1 mocked server-time skeleton tests green at 828b64a; Slice 2 mocked wallet_balance tests green at 66a898d; Slice 3 mocked open_positions tests green at 0596afb; B2a mocked server_time smoke harness tests green at a511e2f
- Results:
  - python -m pytest tests\libs\config -q: 19 passed
  - python -m pytest tests\libs\exchange -q: 39 passed
  - python -m pytest apps/market_data/tests -q: 8 passed
  - python -m pytest apps -q: 163 passed
  - python -m pytest -q --ignore=./research --basetemp=.pytest_tmp: 288 passed, 5 warnings
- No secrets observed.
- No live/exchange/private endpoints/orders/cancels/balances/live execution/live reconcile were enabled or observed.
- Slice 1 evidence:
  - python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 28 passed
  - python -m pytest tests\libs\exchange -q: 67 passed
- Slice 2 evidence:
  - python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 33 passed
  - python -m pytest tests\libs\exchange -q: 72 passed
  - python -m pytest tests\libs\config -q: 19 passed
- Slice 3 evidence:
  - python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 39 passed
  - python -m pytest tests\libs\exchange -q: 78 passed
  - python -m pytest tests\libs\config -q: 19 passed
- B2a evidence:
  - python scripts\smoke_server_time.py: LASTEXITCODE=3 with sanitized authorization_required JSON
  - python -m pytest tests\scripts\test_smoke_server_time.py -q --basetemp=.pytest-temp-run: 14 passed
  - python -m pytest tests\libs\exchange -q: 78 passed
  - python -m pytest tests\libs\config -q: 19 passed

## Current stage

- Current gate: Stage 53-B2a server_time smoke harness checkpoint
- Status: owner decisions OI-1..OI-9 ANSWERED / APPROVED; B1-CONFIG config-only slice complete on c17c7d0; Slice 1 accepted/pushed at 828b64a; Slice 2 accepted/pushed at 66a898d; Slice 3 accepted/pushed/remote-visible at 0596afb; B2a accepted/pushed/remote-visible at a511e2f; Stage 53-B implementation beyond B2a BLOCKED
- Stage 53-B1 architecture plan: docs/STAGE_53B1_ARCHITECTURE.md
- Stage 53-B1 implementation owner inputs B1-OI-1..B1-OI-6: ANSWERED / APPROVED
- Next allowed task: Stage 53-B2 docs/status cleanup and static safety checks; B2b real server_time smoke, credentials use, wallet_balance smoke, open_positions smoke, order_status, or any write/live implementation requires separate approval
- Live trading: NO-GO
- Stage 53-B1 first implementation scope: Bybit testnet authenticated read-only server time/connectivity, wallet balance, and open positions only; order status deferred; no place order; no cancel order; no set_leverage; no live reconcile
- B1-CONFIG scope already present: config-only settings; no client, no private API calls, no service startup wiring, no runtime behavior change
- Slice 1 scope already present: Bybit auth/signing helper; timestamp / recv_window handling; redaction helpers; minimal ServerTime model; read-only client skeleton; get_server_time() only; mocked tests; not runtime-ready
- Slice 2 scope already present: get_wallet_balance(); wallet balance read-only models; Decimal numeric values; redacted repr() / model_dump(); sanitized wallet errors; mocked tests; not runtime-ready
- Slice 3 scope already present: get_open_positions(); open-position read-only models; Decimal numeric values; redacted repr() / model_dump(); sanitized open-position errors; mocked tests; not runtime-ready
- B2a scope already present: server_time smoke harness; mocked tests; direct no-flag latch exits 3 with authorization_required JSON; not runtime-ready; no real smoke executed; no credentials used
- Withdrawal permission: forbidden
- Secrets: no secrets in repo, prompts, docs, or logs

## Current forbidden scope

- No API keys in repo, prompts, docs, logs, or committed fixtures
- No real Bybit connectivity or real credential use
- No real smoke execution without separate Human Owner authorization
- No orders
- No cancels
- No balance runtime verification or real account balance use
- No positions runtime verification or real account position use
- No wallet_balance smoke or open_positions smoke without separate Human Owner authorization
- No order_status
- No write/live methods without separate Human Owner authorization
- No live execution
- No service startup wiring
- No Event Bus implementation
- No Redis Pub/Sub implementation
- No strategy quality filters in Stage 53

## Current architecture docs

- docs/PROGRESS.md
- docs/HOW_WE_WORK.md
- docs/AI_COMMANDS.md
- docs/AI_HANDOFF.md
- docs/STAGE_53_DESIGN_LOCK.md
- docs/STAGE_53B_DESIGN_LOCK.md
- docs/STAGE_53B1_ARCHITECTURE.md
- docs/architecture/STATE_AND_EVENTS_DRAFT.md
- docs/architecture/SERVICE_OWNERSHIP.md
- docs/architecture/INTERACTION_MODEL.md

## Agent roles

- GPT: senior architect / final reviewer
- Claude: independent reviewer
- Claude Code / Codex: executor
- All agents use the 3-lane operating model in docs/HOW_WE_WORK.md: Fast Lane, Standard Lane, Protected Lane
- Human Owner keeps final authority for accept/reject, START/HOLD, GO/NO-GO, stage transitions, and risk acceptance
- Commit only after explicit Human Owner instruction
- Every agent report must identify Agent, Task Type, Scope, Lane, Changed Files, Commands Run, Readiness Claims, Not Verified, and Decision Needed
