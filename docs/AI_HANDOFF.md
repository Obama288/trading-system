# AI Handoff — Hephaestus

## Current project status

Project:
Hephaestus — Python async microservice trading system.

Current mode:
Paper trading only.

Runtime status:
- Local paper runtime: GO
- VPS paper runtime: GO
- 9 services healthy
- 211 tests passing
- Alembic head: 0008
- execution-service confirmed ready in paper mode
- Live exchange layer: NOT IMPLEMENTED

Latest known commits:
- 04ea0eb docs: add stage 53 design lock
- 8827f4b docs: draft state ownership and domain events
- 6c3be0b LH-1.11 VPS runtime proof complete, LH-1 CLOSED

---

## Closed work

- LH-1 closed
- VPS Runtime Proof complete
- Stage 53 design lock added
- State ownership and domain events draft added
- Live Path Audit completed
- 11 live blockers confirmed
- Operator Runbook created
- Working protocol adopted

---

## Current gate

Stage 53-A:
Bybit public market data adapter.

Stage 53-A is allowed to begin.

---

## Stage 53-A allowed scope

- Public Bybit REST market data only
- Symbol mapping: BTC-USDT -> BTCUSDT
- market_type config required: spot or linear
- Bybit public ticker/orderbook/kline/instrument rules reads
- Instrument rules normalization
- Liquidity / spread guard
- Decimal-only price and quantity normalization
- Typed exchange/market-data errors
- Mocked tests first
- Read-only smoke later

---

## Stage 53-A forbidden scope

- API keys
- Private endpoints
- Orders
- Cancels
- Balances
- Positions
- Authenticated exchange client
- Live execution
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

## Stage 53 constraints — must not change

1. Pipeline order: signal → risk → review → orchestrator → execution_service → position_manager
2. Kill-switch fail-closed: all 4 error classes (AUTH_FAILURE, KILL_SWITCH_TIMEOUT, KILL_SWITCH_UNAVAILABLE, KILL_SWITCH_ERROR) must continue to block execution
3. RiskDecision.entry_price midpoint rule: (entry_zone.min + entry_zone.max) / 2
4. execution_idempotency_key deduplication: DB-level idempotency must remain for the paper path; live adds exchange-level idempotency on top
5. Journal fail-soft after authoritative DB commit: journal write failure must not roll back a committed position or execution
6. operator_actions audit trail: every approve/reject must continue to write to operator_actions table atomically
7. max_open_positions DB cap gate with advisory lock: must remain at execution admission boundary
8. Token validation at startup: validate_startup_auth() must not be weakened

---

## Live blockers

11 confirmed live blockers that must be resolved before any live execution attempt:

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

## Owner decisions needed before 53-B

1. Confirm Bybit account type: Unified or Classic
2. Confirm position mode: One-way required
3. Confirm or set account leverage for linear perpetuals
4. Confirm Bybit API key has Futures read+write and NO withdrawal permission

---

## Working protocol

- Windows PowerShell uses ; not &&
- Always use python -m pytest
- Always use python -m alembic
- Always use python -m uvicorn
- Verify file edits with Get-Content after writing
- Definition of Done: changed + verified + tests + git status
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
