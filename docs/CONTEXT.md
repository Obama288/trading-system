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
- Tests: Q1 regression PASS on main 1bd8e2a; broader suite 269 passed, 5 warnings
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
- Implementation: BLOCKED on owner decisions (9 required, none yet answered)

## Q1 fix and regression status

- Q1-FIX-1 recover_position payload validation: MERGED
- Q1-FIX-2 freshness naive datetime handling: MERGED
- Q1-FIX-3 true EMA in snapshot builder: MERGED
- Regression gate: PASS on main 1bd8e2a
- Results:
  - python -m pytest apps/market_data/tests -q: 8 passed
  - python -m pytest apps/position_manager/tests -q: 36 passed
  - python -m pytest apps -q: 163 passed
  - python -m pytest -q --ignore=research with project-local temp isolation: 269 passed, 5 warnings
- No secrets observed.
- No live/exchange/private endpoints/orders/cancels/balances/live execution/live reconcile were enabled or observed.

## Current stage

- Current gate: Stage 53-B1 planning / architecture
- Status: owner decisions OI-1..OI-9 ANSWERED / APPROVED; Stage 53-B implementation NOT STARTED
- Stage 53-B1 architecture plan: docs/STAGE_53B1_ARCHITECTURE.md
- Next allowed task: Stage 53-B1 architecture review, planning follow-up, and docs/status cleanup
- Live trading: NO-GO
- Stage 53-B1 maximum scope: Bybit testnet/demo authenticated read-only balances and positions; optional order status read-only; no place order; no cancel order; no live reconcile
- Withdrawal permission: forbidden
- Secrets: no secrets in repo, prompts, docs, or logs

## Current forbidden scope

- No API keys
- No private Bybit endpoints
- No orders
- No cancels
- No balances
- No positions
- No live execution
- No Event Bus implementation
- No Redis Pub/Sub implementation
- No strategy quality filters in Stage 53

## Current architecture docs

- docs/PROGRESS.md
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
- Commit only after reviewer approval
