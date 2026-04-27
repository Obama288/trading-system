# Stage Status

## Current summary

- Current stage: 53-B implementation
- Last completed operational milestone: Stage 53-A (Bybit public market data adapter)
- Current mode: paper trading only
- Live readiness: NO-GO
- Current test baseline: Q1 regression PASS on main 1bd8e2a; broader suite 269 passed, 5 warnings
- Stage 53-A closed: 3b3b06f
- Stage 53-B design lock closed: 5e5eb48
- Stage 53-B implementation: BLOCKED until owner decisions OI-1..OI-9 are answered
- Q1-FIX-3 true EMA: MERGED and regression-validated on main 1bd8e2a
- Live/exchange/private endpoints/orders/cancels/balances/live execution/live reconcile: not enabled by Q1 fixes
- Canonical live blocker taxonomy: 14 canonical live blockers from docs/STAGE_53_DESIGN_LOCK.md

## Stage table

| Stage / Milestone | Status | Commit | Notes |
|---|---|---|---|
| LH-1 | CLOSED | 6c3be0b | VPS runtime proof complete, LH-1 closed |
| State and Events Draft | CLOSED | 8827f4b | Stage 54+ state ownership and domain events draft |
| Stage 53 Design Lock | CLOSED | 04ea0eb | Stage 53 constraints and safety-vs-signal-quality roadmap |
| AI Handoff | CLOSED | 93bc643 | Agent handoff guide |
| Service Ownership Map | CLOSED | e7cecc7 | Stage 54+ ownership map |
| Interaction Model Draft | CLOSED | 65c7204 | Commands / Queries / Events model |
| Stage 53-A | CLOSED | 3b3b06f | Bybit public market data adapter; 39 Stage 53-A tests passed; 250 total tests passed; read-only public smoke PASS |
| Stage 53-B Design Lock | CLOSED | 5e5eb48 | authenticated Bybit client design locked; implementation blocked on owner decisions |
| Stage 53-B Status Docs | CLOSED | 69176ed | status docs updated after 53-B design lock |
| Stage 53-B Owner Decision Tracker | CLOSED | e814031 | owner decisions OI-1..OI-9 tracker added; all remain OPEN / TBD unless owner updates them |
| Stage 53-B Gate Handoff Cleanup | CLOSED | 3d72ba8 | handoff status aligned to blocked 53-B implementation gate |
| Stage 53 Design Lock Decisions Cleanup | CLOSED | ff2f30c | design lock decisions aligned: 14 blockers, BYBIT env vars, client_order_id rule, deferred 0009, canonical adapter path |
| Q1 Fixes Regression Gate | CLOSED | 1bd8e2a | Q1-FIX-1, Q1-FIX-2, and Q1-FIX-3 merged; main regression PASS; live trading remains NO-GO |
| Stage 53-B | BLOCKED | pending | owner decisions required before code |
| Stage 53-C | BLOCKED | pending | Live execution path |
| Stage 53-D | BLOCKED | pending | Live reconcile |
| Stage 53-E | BLOCKED | pending | Tests + read-only smoke |
| Stage 53-E2 | BLOCKED | pending | Dry live smoke, no orders |
| Stage 53-F | BLOCKED | pending | Controlled live, one trade, manual approval |

## Owner decisions required before 53-B implementation

All nine must be confirmed before Stage 53-B implementation begins.

1. Confirm Bybit account type: Unified or Classic
2. Confirm market type for first live: linear or spot
3. Confirm position mode: One-way required
4. Confirm or set leverage for first live if using linear perpetuals
5. Confirm Bybit API key permissions: Futures read+write, NO withdrawal
6. Decide whether to enable IP whitelist for the VPS
7. Confirm first live order type preference: market or limit
8. Confirm first live maximum notional size
9. Confirm manual stop-loss procedure on Bybit UI

## Live blockers

Canonical current taxonomy: 14 canonical live blockers from docs/STAGE_53_DESIGN_LOCK.md.

Legacy summarized list below: not the current authoritative blocker count.

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

## Session startup prompt

```
Read docs/CONTEXT.md, docs/STAGE_STATUS.md, docs/PROGRESS.md, docs/AI_HANDOFF.md, and docs/AI_COMMANDS.md first.
Then give me:
1. current stage
2. latest relevant commit
3. current runtime mode
4. tests status
5. next allowed task
6. forbidden scope
Do not modify files until I approve the plan.
```
