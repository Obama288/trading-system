# Stage Status

## Current summary

- Current stage: Stage 54-BG planning - Bitget Demo primary candidate; Bybit Stage 53 private real testnet path remains blocked
- Last completed operational milestone: Stage 53-A (Bybit public market data adapter)
- Last completed code/test slice: Stage 53-B2c.1b query-api read-only preflight harness, 00d84d8
- Current mode: paper trading only
- Live readiness: NO-GO
- Stage 54-BG planning decision: Bitget Demo / Simulated Trading is the primary candidate for the next exchange-specific read-only sandbox track; start with docs-only architecture planning, then `BitgetBg1Settings` plus mocked tests only
- Stage 54-BG proposed env namespace: `BITGET_BG1_ENVIRONMENT`, `BITGET_BG1_API_KEY`, `BITGET_BG1_API_SECRET`, `BITGET_BG1_PASSPHRASE`
- Stage 54-BG config boundary: no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback in the first implementation; Bitget production/mainnet must fail closed by default
- Stage 54-BG implementation boundary: no private Bitget smoke before config, environment, and passphrase guardrails are locked; no real wallet/balance/positions smoke, order_status, write/live methods, or service wiring are authorized
- Stage 54-AP planning boundary: Alpaca Paper remains fallback-only and must stay a separate architecture track; do not fold Alpaca into a crypto-CEX abstraction
- Generic exchange adapter boundary: do not create a generic exchange adapter yet
- Current B2c.1a test baseline: HEAD 189cb0a PASS for mocked/local authenticated-readiness hardening only; server_time no-flag latch LASTEXITCODE=3; wallet_balance no-flag latch LASTEXITCODE=3; tests/scripts 40 passed; tests/libs/exchange 86 passed; tests/libs/config 19 passed
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
- Stage 53-B2b real server_time smoke: SUCCESS for server_time only; Human Owner executed exactly one real Bybit testnet server_time smoke locally after safe credential presence and hygiene checks; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only; not runtime-ready
- Stage 53-B2c wallet_balance smoke harness: CLOSED on c9b1337; accepted implementation checkpoint; mocked tests only; direct no-flag latch exits 3; --allow-real-smoke required for real-capable path; no real wallet_balance smoke, credentials use for B2c implementation, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
- Stage 53-B2c.1a authenticated readiness hardening: CLOSED on 189cb0a; server_time now uses unsigned public /v5/market/time methodology; get_server_time no longer requires credentials; private reads still fail closed without credentials; signed private reads include X-BAPI-SIGN-TYPE: 2; signed GET query handling is deterministic and consistent with what is sent; wallet_balance signs/sends accountType=UNIFIED; safe retCode classifications added for 10002/10003/10004/10005/10006/10007/10010; 10006 remains exit code 2 / inconclusive; no raw retMsg/raw response body exposure; no query-api, open_positions smoke, order_status, write/live methods, service wiring, or readiness approval
- Stage 53-B2c.1b query-api read-only preflight harness: CLOSED on 00d84d8; get_query_api_info() supports signed read-only GET /v5/user/query-api; sanitized ApiKeyInfo model; scripts/smoke_query_api.py no-flag latch exits 3 with sanitized authorization_required JSON; no-flag path does not load settings/client/credentials or call Bybit; success output exact approved field set with no operation or endpoint_family; unsafe readOnly/permissions/expiry metadata fail closed including stale/malformed expiredAt; rate limit remains exit code 2 / inconclusive; no real query-api execution, credentials use, Bybit call, real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or readiness approval
- Stage 53-B2c.1c real query-api preflight: BLOCKED; attempted once and failed safely with retCode=10003, error_category=invalid_key_or_environment, LASTEXITCODE=1; likely ordinary/mainnet Bybit key against testnet endpoint or no usable testnet API access; no further query-api retry is authorized
- Stage 53-B2d real wallet_balance testnet smoke: BLOCKED / NO-GO because usable Bybit testnet API credentials are unavailable; ordinary/mainnet Bybit key must not be substituted into the testnet flow; any mainnet read-only smoke requires a new separately authorized stage, not continuation of B2d
- Stage 53-B2 testnet API access runbook: DOCUMENTED in docs/STAGE_53B2_SMOKE_PLAN.md; use testnet Bybit API Management, API Transaction / Транзакция API key type, read-only permissions only, no generic BYBIT_API_KEY/BYBIT_API_SECRET aliases during B2 flow, and safe restart path with explicit Human Owner authorization for exactly one query-api preflight
- Stage 53-B2 Pit-stop audit: RECORDED as audit-only, not an implementation gate; repo was aligned at 8153c61; full local regression passed with 408 passed and 5 warnings; targeted suites passed with tests/scripts 60, tests/libs/exchange 99, tests/libs/config 19; server_time, wallet_balance, and query_api no-flag latches all exited 3; checked BYBIT env names were missing; no runtime/trading/live/probe readiness is claimed
- Stage 53-B2c.1 authenticated readiness audit / query-api preflight decision: B2c.1a and B2c.1b implementation checkpoints are code/test ready for mocked/local behavior only; B2c.1c/B2d private testnet smokes are blocked due unavailable usable Bybit testnet API access
- Stage 53-B2 permanent real-smoke preflight: safe credential presence check, safe credential hygiene check, and Human Owner external key active/not expired confirmation are required before any real Bybit smoke gate; any missing required env var, hygiene warning, expired/uncertain key, or missing owner confirmation stops the smoke
- Query-api `/v5/user/query-api`: not in the current B1/B2 endpoint set; adding it requires explicit Human Owner decision and may only be read-only preflight
- Server-time semantics: `/v5/market/time` is public and now uses unsigned connectivity/time methodology as of 189cb0a; B2b remains a valid earlier connectivity checkpoint
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
| Stage 53-B2b Real Server-Time Smoke | CLOSED | local owner-run | successful real Bybit testnet server_time smoke; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only; no wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness |
| Stage 53-B2c Wallet-Balance Smoke Harness | CLOSED | c9b1337 | wallet_balance smoke harness, mocked tests only, direct no-flag latch exits 3 with authorization_required JSON, --allow-real-smoke required; sanitized mocked success output includes endpoint/status/exchange/account_type/coins_count/elapsed_ms only; no real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness |
| Stage 53-B2c.1a Auth Readiness Hardening | CLOSED | 189cb0a | unsigned public server_time methodology; get_server_time no longer requires credentials; private reads fail closed without credentials; signed reads include `X-BAPI-SIGN-TYPE: 2`; deterministic signed/sent GET query handling; safe retCode categories for 10002/10003/10004/10005/10006/10007/10010; mocked/local tests only; no query-api, real wallet smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness |
| Stage 53-B2c.1b Query-API Preflight Harness | CLOSED | 00d84d8 | get_query_api_info() signed read-only `/v5/user/query-api`; sanitized ApiKeyInfo; smoke_query_api no-flag latch exits 3; exact success output field set; unsafe readOnly/permissions/expiry metadata fail closed; stale/malformed expiredAt covered; rate limit exit 2 / inconclusive; mocked tests only; no real query-api execution, real wallet smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness |
| Stage 53-B2c.1c Real Query-API Preflight | BLOCKED | local owner-run | attempted once; failed safely with retCode=10003 invalid_key_or_environment and LASTEXITCODE=1; likely mainnet/testnet key-environment mismatch or no usable testnet API access; no retry authorized |
| Stage 53-B2d Real Wallet Balance Testnet Smoke | BLOCKED / NO-GO | pending | usable Bybit testnet API credentials unavailable; ordinary/mainnet key must not be substituted into testnet flow; any mainnet read-only smoke requires a new separately authorized stage |
| Stage 54-BG Planning | PLANNED | pending | Bitget Demo / Simulated Trading is the primary candidate replacement track; begin with docs-only architecture planning, then `BitgetBg1Settings` and mocked tests only; no generic `BITGET_API_KEY` fallback in first implementation; production/mainnet must fail closed; no private Bitget smoke, wallet/balance/positions real smoke, order_status, write/live methods, or service wiring authorized |
| Stage 54-AP Fallback Planning | PLANNED | pending | Alpaca Paper remains fallback-only and must stay a separate architecture track; do not fold Alpaca into a crypto-CEX abstraction or a generic exchange adapter |
| Stage 53-B2 Testnet API Access Runbook | DOCUMENTED | pending | testnet URL/API Management URL, API Transaction / Транзакция API key type, read-only permissions, retCode 10003 troubleshooting, and safe restart path documented; no real retry authorized |
| Stage 53-B2 Pit-stop Audit | RECORDED | 8153c61 | audit-only checkpoint; repo aligned at 8153c61; no-flag latches exited 3; targeted suites passed; full local regression 408 passed / 5 warnings; B2d remains blocked / NO-GO; no readiness promoted |
| Stage 53-B2c.1 Auth Readiness Audit | BLOCKED | pending | B2c.1a/B2c.1b mocked/local readiness complete; private real testnet path blocked due unavailable usable Bybit testnet API access |
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

B2c.1c/B2d private real testnet smokes are blocked because usable Bybit testnet API credentials are unavailable. The ordinary/mainnet Bybit key must not be substituted into the testnet flow. Any mainnet read-only smoke would require a new separately authorized stage. Open_positions smoke, order_status, and all write/live methods require separate Human Owner authorization.

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
Repo: `Obama288/trading-system`
Check branch/ref first.
Read in source-of-truth order: `docs/PROGRESS.md`, `docs/AI_COMMANDS.md`, `docs/HOW_WE_WORK.md`, `docs/AI_HANDOFF.md`, `docs/CONTEXT.md`, then `docs/STAGE_STATUS.md`.
Then give me:
1. current gate
2. latest relevant commit and checked branch/ref
3. current runtime mode
4. live status
5. key blockers
6. tests status
7. next allowed lane
8. next allowed task
9. forbidden scope
Do not modify files until I approve the plan.
```

Every agent report must identify: Agent, Task Type, Scope, Lane, Changed Files, Commands Run, Readiness Claims, Not Verified, and Decision Needed.
