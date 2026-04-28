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
- Tests: HEAD 828b64a PASS for mocked Slice 1 server-time skeleton behavior only; focused Slice 1 tests 28 passed; tests/libs/exchange 67 passed
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
- Runtime/client implementation: Slice 1 server-time skeleton accepted/pushed at 828b64a; no runtime/service wiring

## Q1 fix and regression status

- Q1-FIX-1 recover_position payload validation: MERGED
- Q1-FIX-2 freshness naive datetime handling: MERGED
- Q1-FIX-3 true EMA in snapshot builder: MERGED
- Regression gate: PASS on main 1bd8e2a; B1-CONFIG green at c17c7d0; Slice 1 mocked server-time skeleton tests green at 828b64a
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

## Current stage

- Current gate: Stage 53-B1 planning / architecture + Slice 1 server-time skeleton checkpoint
- Status: owner decisions OI-1..OI-9 ANSWERED / APPROVED; B1-CONFIG config-only slice complete on c17c7d0; Slice 1 accepted/pushed at 828b64a; Stage 53-B implementation beyond Slice 1 BLOCKED
- Stage 53-B1 architecture plan: docs/STAGE_53B1_ARCHITECTURE.md
- Stage 53-B1 implementation owner inputs B1-OI-1..B1-OI-6: ANSWERED / APPROVED
- Next allowed task: Stage 53-B1 docs/status cleanup and static safety checks; wallet balance/open positions or further implementation requires separate approval
- Live trading: NO-GO
- Stage 53-B1 first implementation scope: Bybit testnet authenticated read-only server time/connectivity, wallet balance, and open positions only; order status deferred; no place order; no cancel order; no set_leverage; no live reconcile
- B1-CONFIG scope already present: config-only settings; no client, no private API calls, no service startup wiring, no runtime behavior change
- Slice 1 scope already present: Bybit auth/signing helper; timestamp / recv_window handling; redaction helpers; minimal ServerTime model; read-only client skeleton; get_server_time() only; mocked tests; not runtime-ready
- Withdrawal permission: forbidden
- Secrets: no secrets in repo, prompts, docs, or logs

## Current forbidden scope

- No API keys in repo, prompts, docs, logs, or committed fixtures
- No real Bybit connectivity or real credential use
- No orders
- No cancels
- No balances
- No positions
- No wallet_balance implementation without separate Human Owner authorization
- No open_positions implementation without separate Human Owner authorization
- No order_status
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
