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
- Current test baseline: Q1 regression PASS on main 1bd8e2a; broader suite 269 passed, 5 warnings
- Alembic head: 0008
- execution-service confirmed ready in paper mode
- Live exchange layer: NOT IMPLEMENTED

Latest known commits:
- 1bd8e2a fix: implement true EMA in snapshot builder
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

- Q1-FIX-1 recover_position payload validation: MERGED
- Q1-FIX-2 freshness naive datetime handling: MERGED
- Q1-FIX-3 true EMA in snapshot builder: MERGED, regression-validated on main 1bd8e2a
- Stage 53-A: CLOSED, commit 3b3b06f
- Stage 53-B design lock: CLOSED, commit 5e5eb48
- Status docs after 53-B design lock: CLOSED, commit 69176ed
- Stage 53-B owner decision tracker: ADDED, commit e814031
- Stage 53-B1 architecture plan: ADDED in docs/STAGE_53B1_ARCHITECTURE.md
- Live Path Audit completed
- Legacy 11-item live blocker audit completed; canonical current taxonomy is 14 live blockers.

---

## Current gate

Current gate:
Stage 53-B1 planning / architecture gate.

Stage 53-B implementation:
NOT STARTED.

Block reason:
Implementation still requires separate explicit approval after Stage 53-B1 planning.

Owner decisions OI-1..OI-9 are ANSWERED / APPROVED in docs/STAGE_53B_OWNER_DECISIONS.md.
No runtime implementation is authorized by the decision-sync PR.
No live trading enablement is allowed.

Next safe work:
Stage 53-B1 architecture review, planning follow-up, and docs/status cleanup.

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
- Docs-only plan; implementation has not started.
- B1-OI-1..B1-OI-6 are ANSWERED / APPROVED for future implementation planning.
- This does not authorize runtime implementation, live trading, production private endpoints, orders, cancels, leverage changes, live reconcile, or live execution.

Q1 regression evidence:
- python -m pytest apps/market_data/tests -q: 8 passed
- python -m pytest apps/position_manager/tests -q: 36 passed
- python -m pytest apps -q: 163 passed
- python -m pytest -q --ignore=research with project-local temp isolation: 269 passed, 5 warnings
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
