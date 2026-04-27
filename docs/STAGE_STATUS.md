# Stage Status

## Current summary

- Current stage: Stage 53-B1 planning / architecture gate
- Last completed operational milestone: Stage 53-A (Bybit public market data adapter)
- Current mode: paper trading only
- Live readiness: NO-GO
- Current test baseline: Q1 regression PASS on main 1bd8e2a; broader suite 269 passed, 5 warnings
- Stage 53-A closed: 3b3b06f
- Stage 53-B design lock closed: 5e5eb48
- Stage 53-B owner decisions OI-1..OI-9: ANSWERED / APPROVED
- Stage 53-B implementation: NOT STARTED; separate explicit approval required after Stage 53-B1 planning
- Stage 53-B1 maximum scope: Bybit testnet/demo authenticated read-only balances and positions; optional order status read-only; no place order; no cancel order; no live reconcile
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
| Stage 53-B Owner Decision Tracker | CLOSED | e814031 | owner decisions OI-1..OI-9 tracker added |
| Stage 53-B Gate Handoff Cleanup | CLOSED | 3d72ba8 | handoff status aligned to blocked 53-B implementation gate |
| Stage 53 Design Lock Decisions Cleanup | CLOSED | ff2f30c | design lock decisions aligned: 14 blockers, BYBIT env vars, client_order_id rule, deferred 0009, canonical adapter path |
| Q1 Fixes Regression Gate | CLOSED | 1bd8e2a | Q1-FIX-1, Q1-FIX-2, and Q1-FIX-3 merged; main regression PASS; live trading remains NO-GO |
| Stage 53-B Owner Decisions | CLOSED | pending | OI-1..OI-9 answered/approved; live trading remains NO-GO |
| Stage 53-B1 Planning / Architecture | NEXT | pending | Bybit testnet/demo read-only authenticated client plan only; implementation requires separate approval |
| Stage 53-B Implementation | BLOCKED | pending | not started; no place/cancel/live execution/live reconcile |
| Stage 53-C | BLOCKED | pending | Live execution path |
| Stage 53-D | BLOCKED | pending | Live reconcile |
| Stage 53-E | BLOCKED | pending | Tests + read-only smoke |
| Stage 53-E2 | BLOCKED | pending | Dry live smoke, no orders |
| Stage 53-F | BLOCKED | pending | Controlled live, one trade, manual approval |

## Owner decisions before 53-B1 planning

All nine are ANSWERED / APPROVED in docs/STAGE_53B_OWNER_DECISIONS.md.

1. OI-1: Bybit only.
2. OI-2: Testnet/demo only.
3. OI-3: Read-only balances + positions; optional order status read-only; no place/cancel orders.
4. OI-4: Env vars for local testnet; secret manager/GitHub secrets later; no secrets in repo/prompts/docs.
5. OI-5: Read-only API key only; withdrawal permission forbidden.
6. OI-6: Live trading only after full implementation + QA + regression + external review + separate explicit owner approval.
7. OI-7: Keep current authority model exactly.
8. OI-8: Authenticated client + testnet read-only balances and positions only.
9. OI-9: Full protocol: architect -> plan -> implement -> QA -> external review if needed -> PR -> merge.

This does not authorize Stage 53-B implementation or live trading.

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
