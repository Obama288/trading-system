# Stage Status

## Current summary

- Current stage: Stage 53-B2a server_time smoke harness checkpoint
- Last completed operational milestone: Stage 53-A (Bybit public market data adapter)
- Last completed code/test slice: Stage 53-B2a server_time smoke harness, a511e2f
- Current mode: paper trading only
- Live readiness: NO-GO
- Current B2a test baseline: HEAD a511e2f PASS for mocked server_time smoke harness behavior only; direct no-flag latch exits 3 with authorization_required JSON; B2a tests 14 passed; tests/libs/exchange 78 passed; tests/libs/config 19 passed
- Stage 53-A closed: 3b3b06f
- Stage 53-B design lock closed: 5e5eb48
- Stage 53-B owner decisions OI-1..OI-9: ANSWERED / APPROVED
- Stage 53-B1 architecture plan: ADDED in docs/STAGE_53B1_ARCHITECTURE.md
- Stage 53-B1 implementation owner inputs B1-OI-1..B1-OI-6: ANSWERED / APPROVED
- B1-CONFIG config-only slice: CLOSED on c17c7d0; no runtime/service wiring
- Stage 53-B1 Slice 1 server-time skeleton: CLOSED on 828b64a; accepted implementation checkpoint; no runtime/service wiring
- Stage 53-B1 Slice 2 wallet_balance: CLOSED on 66a898d; accepted implementation checkpoint; mocked wallet_balance tests only; not runtime-ready
- Stage 53-B1 Slice 3 open_positions: CLOSED on 0596afb; accepted implementation checkpoint; mocked open_positions tests only; not runtime-ready
- Stage 53-B2a server_time smoke harness: CLOSED on a511e2f; accepted implementation checkpoint; mocked tests only; direct no-flag latch exits 3; not runtime-ready; no real smoke or credentials use authorized
- Stage 53-B implementation beyond Slice 3: BLOCKED; separate explicit approval required
- Stage 53-B1 first client implementation scope: Bybit testnet authenticated read-only server time/connectivity, wallet balance, and open positions only; order status deferred
- Q1-FIX-3 true EMA: MERGED and regression-validated on main 1bd8e2a
- Live/exchange/private endpoints/orders/cancels/live execution/live reconcile: not enabled by Q1 fixes, B1-CONFIG, Slice 1, Slice 2, Slice 3, or B2a
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
| Stage 53-B1 Planning / Architecture | PLANNED | pending | docs/STAGE_53B1_ARCHITECTURE.md added; implementation requires separate approval |
| Stage 53-B1 Owner Inputs | CLOSED | pending | B1-OI-1..B1-OI-6 answered/approved; first implementation excludes order status and all write/live actions |
| Stage 53-B1 B1-CONFIG | CLOSED | c17c7d0 | config-only Bybit B1 settings and tests; no client, private API calls, service wiring, runtime behavior, or live enablement |
| Stage 53-B1 Slice 1 Server-Time Skeleton | CLOSED | 828b64a | Bybit auth/signing helper, timestamp/recv_window handling, redaction helpers, minimal ServerTime model, read-only client skeleton, get_server_time() only, mocked tests; not runtime-ready |
| Stage 53-B1 Slice 2 Wallet Balance | CLOSED | 66a898d | get_wallet_balance(), wallet balance read-only models, Decimal values, redacted repr/model_dump, sanitized wallet errors, mocked tests; no open_positions, service wiring, real connectivity, or runtime readiness |
| Stage 53-B1 Slice 3 Open Positions | CLOSED | 0596afb | get_open_positions(), open-position read-only models, Decimal values, redacted repr/model_dump, sanitized open-position errors, mocked tests; no order_status, service wiring, real connectivity, or runtime readiness |
| Stage 53-B2a Server-Time Smoke Harness | CLOSED | a511e2f | server_time smoke harness, mocked tests, direct no-flag latch exits 3 with authorization_required JSON; no real smoke, credentials use, wallet/open_positions smoke, order_status, service wiring, or runtime readiness |
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

## Stage 53-B1 Slice 1 checkpoint

Commit: 828b64a feat: add Bybit B1 read-only server-time skeleton.

Classification:
- Code-ready candidate / accepted implementation checkpoint for Slice 1 only.
- Test-ready for mocked server-time skeleton behavior only.
- Not runtime-ready.

Exists:
- Bybit auth/signing helper.
- Timestamp / recv_window handling.
- Redaction helpers.
- Minimal ServerTime model.
- Read-only client skeleton.
- get_server_time() only.
- Mocked tests.

Does not exist:
- wallet_balance.
- open_positions.
- order_status.
- place_order.
- cancel_order.
- set_leverage.
- withdraw.
- transfer.
- live_reconcile.
- live_execution.
- service startup wiring.
- real Bybit connectivity verification.
- real credential verification.

Future wallet/open positions slices require separate Human Owner authorization.

## Stage 53-B1 Slice 2 checkpoint

Commit: 66a898d feat: add Bybit B1 read-only wallet balance.

Classification:
- Code-ready candidate / accepted implementation checkpoint for Slice 2 wallet_balance only.
- Test-ready for mocked wallet_balance behavior only.
- Not runtime-ready.

Exists:
- get_wallet_balance().
- Wallet balance read-only models.
- Decimal numeric values.
- Redacted repr() / model_dump().
- Sanitized wallet errors.
- Mocked tests.

Does not exist:
- open_positions.
- order_status.
- place_order.
- cancel_order.
- set_leverage.
- withdraw.
- transfer.
- live_reconcile.
- live_execution.
- service startup wiring.
- real Bybit connectivity verification.
- real credential verification.

Future order_status and any write/live methods require separate Human Owner authorization.

## Stage 53-B1 Slice 3 checkpoint

Commit: 0596afb feat: add Bybit B1 read-only open positions.

Classification:
- Code-ready candidate / accepted implementation checkpoint for Slice 3 open_positions only.
- Test-ready for mocked open_positions behavior only.
- Not runtime-ready.

Exists:
- get_open_positions().
- Open-position read-only models.
- Decimal numeric values.
- Redacted repr() / model_dump().
- Sanitized open-position errors.
- Mocked tests.

Does not exist:
- order_status.
- place_order.
- cancel_order.
- set_leverage.
- withdraw.
- transfer.
- live_reconcile.
- live_execution.
- service startup wiring.
- real Bybit connectivity verification.
- real credential verification.

Order_status and all write/live methods require separate Human Owner authorization.

## Stage 53-B2a checkpoint

Commit: a511e2f feat: add Stage 53-B2 server-time smoke harness.

Classification:
- Code-ready candidate / accepted implementation checkpoint for B2a server_time smoke harness only.
- Test-ready for mocked B2a behavior only.
- Not runtime-ready.

Exists:
- server_time smoke harness.
- Mocked tests.
- Direct no-flag latch exits 3 with authorization_required JSON.

Does not exist / is not authorized:
- B2b real server_time smoke execution.
- Credentials use.
- wallet_balance smoke.
- open_positions smoke.
- order_status.
- place_order.
- cancel_order.
- set_leverage.
- withdraw.
- transfer.
- live_reconcile.
- live_execution.
- service startup wiring.
- real Bybit connectivity verification.
- real credential verification.

B2b real server_time smoke, credentials use, wallet_balance smoke, open_positions smoke, order_status, and all write/live methods require separate Human Owner authorization.

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
Read docs/CONTEXT.md, docs/STAGE_STATUS.md, docs/PROGRESS.md, docs/HOW_WE_WORK.md, docs/AI_HANDOFF.md, and docs/AI_COMMANDS.md first.
Then give me:
1. current stage
2. latest relevant commit
3. current runtime mode
4. tests status
5. next allowed task
6. forbidden scope
7. operating lane for the requested task
Do not modify files until I approve the plan.
```

Every agent report must identify: Agent, Task Type, Scope, Lane, Changed Files, Commands Run, Readiness Claims, Not Verified, and Decision Needed.
