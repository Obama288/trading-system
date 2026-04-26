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
- Current test baseline according to current status/context docs: 250 passed, 5 warnings
- Alembic head: 0008
- execution-service confirmed ready in paper mode
- Live exchange layer: NOT IMPLEMENTED

Latest known commits:
- e6008c3 docs: align status docs with stage 53-B gate
- ff2f30c docs: align stage 53 design lock decisions
- 3d72ba8 docs: align stage 53-B gate handoff status
- e814031 docs: add stage 53-B owner decision tracker
- 69176ed docs: update status after stage 53-B design lock
- 5e5eb48 docs: add stage 53-B design lock
- 3b3b06f feat: add Bybit public market data adapter
- 04ea0eb docs: add stage 53 design lock

---

## Closed work

- Stage 53-A: CLOSED, commit 3b3b06f
- Stage 53-B design lock: CLOSED, commit 5e5eb48
- Status docs after 53-B design lock: CLOSED, commit 69176ed
- Stage 53-B owner decision tracker: ADDED, commit e814031
- Live Path Audit completed
- Legacy 11-item live blocker audit completed; canonical current taxonomy is 14 live blockers.

---

## Current gate

Current gate:
Stage 53-B implementation gate.

Stage 53-B implementation:
BLOCKED.

Block reason:
Owner decisions OI-1..OI-9 are not answered.

No runtime implementation is allowed until owner decisions are answered.
No live trading enablement is allowed.

Next safe work:
Docs-only cleanup and decision tracking.

---

## Current forbidden scope

- API keys
- Private endpoints
- Orders
- Cancels
- Balances
- Positions
- Authenticated exchange client implementation
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

## Owner decisions needed before 53-B

1. Confirm Bybit account type: Unified or Classic
2. Confirm market type for first live: linear or spot
3. Confirm position mode: One-way required
4. Confirm or set leverage for first live if using linear perpetuals
5. Confirm Bybit API key permissions: Futures read+write, NO withdrawal
6. Decide whether to enable IP whitelist for the VPS
7. Confirm first live order type preference: market or limit
8. Confirm first live maximum notional size
9. Confirm manual stop-loss procedure on Bybit UI

All OI-1..OI-9 rows remain OPEN / TBD unless the owner explicitly updates them.

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
