# Stage Status

## Current summary

- Current stage: 53-A
- Last completed operational milestone: LH-1 / VPS Runtime Proof
- Current mode: paper trading only
- Live readiness: NO-GO
- Repo status at time of writing: clean before this doc task

## Stage table

| Stage / Milestone | Status | Commit | Notes |
|---|---|---|---|
| LH-1 | CLOSED | 6c3be0b | VPS runtime proof complete, LH-1 closed |
| State and Events Draft | CLOSED | 8827f4b | Stage 54+ state ownership and domain events draft |
| Stage 53 Design Lock | CLOSED | 04ea0eb | Stage 53 constraints and safety-vs-signal-quality roadmap |
| AI Handoff | CLOSED | 93bc643 | Agent handoff guide |
| Service Ownership Map | CLOSED | e7cecc7 | Stage 54+ ownership map |
| Interaction Model Draft | CLOSED | 65c7204 | Commands / Queries / Events model |
| Stage 53-A | NEXT | pending | Bybit public market data adapter |
| Stage 53-B | BLOCKED | pending | Authenticated Bybit exchange client; owner inputs required |
| Stage 53-C | BLOCKED | pending | Live execution path |
| Stage 53-D | BLOCKED | pending | Live reconcile |
| Stage 53-E | BLOCKED | pending | Tests + read-only smoke |
| Stage 53-E2 | BLOCKED | pending | Dry live smoke, no orders |
| Stage 53-F | BLOCKED | pending | Controlled live, one trade, manual approval |

## Owner decisions required before 53-B

1. Confirm Bybit account type: Unified or Classic
2. Confirm position mode: One-way required
3. Confirm or set account leverage for linear perpetuals
4. Confirm Bybit API key has Futures read+write and NO withdrawal permission

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
