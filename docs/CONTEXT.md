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
- Tests: 211 passing
- Alembic head: 0008
- execution-service: ready, mode=paper

## Current stage

- Current gate: Stage 53-A
- Task: Bybit public market data adapter
- Scope: public/read-only only

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
- docs/architecture/STATE_AND_EVENTS_DRAFT.md
- docs/architecture/SERVICE_OWNERSHIP.md
- docs/architecture/INTERACTION_MODEL.md

## Agent roles

- GPT: senior architect / final reviewer
- Claude: independent reviewer
- Claude Code / Codex: executor
- Commit only after reviewer approval

## Next action

Implement Stage 53-A:
Bybit public market data adapter with:
- symbol mapping BTC-USDT -> BTCUSDT
- market_type config required: spot or linear
- instrument rules
- ticker/orderbook/kline public reads
- liquidity/spread guard
- Decimal-only normalized models
- typed errors
- mocked tests first
