# Stage 53-B Design Lock
# Authenticated Bybit Exchange Client Foundation

## Status

- Stage 53-B design lock: CLOSED
- Stage 53-B implementation: NOT STARTED; separate explicit approval required after Stage 53-B1 planning
- Current mode: paper trading only
- Live trading: NO-GO
- Stage 53-A closed: 3b3b06f (feat: add Bybit public market data adapter)
- Owner decisions tracker: docs/STAGE_53B_OWNER_DECISIONS.md
- Owner decisions OI-1..OI-9: ANSWERED / APPROVED in docs/STAGE_53B_OWNER_DECISIONS.md
- Current gate: Stage 53-B1 planning / architecture; implementation is not authorized by the owner-decision sync

## Stage 53-B1 Approved Maximum Scope

- Bybit only
- Testnet/demo only
- Authenticated client
- Read-only balances and positions
- Optional order status read-only
- No place order
- No cancel order
- No live reconcile
- Withdrawal permission is forbidden
- No secrets belong in repo, prompts, docs, or logs
- Live trading remains NO-GO

---

## Purpose

Stage 53-B adds an authenticated Bybit exchange client as a standalone library component.

Goal: provide a typed, authenticated HTTP client for Bybit V5 private endpoints, with correct
HMAC-SHA256 request signing, ready for future wiring into the execution path.

Stage 53-B does NOT wire this client into execution_service or any live execution path.
Stage 53-B does NOT place orders from runtime.
Stage 53-B does NOT enable live trading of any kind.

---

## What 53-B is NOT

- Not a live trading enablement step
- Not an execution_service integration
- Not an order placement feature
- Not a stop-loss automation feature
- Not a strategy filter feature
- Not an Event Bus implementation
- Not a Redis Pub/Sub implementation
- The client will exist as a library; it will not be called from any service startup path

---

## Blocked on Owner Decisions

The following decisions are answered in docs/STAGE_53B_OWNER_DECISIONS.md.
This does not start implementation work.

### OI-1: Exchange Venue

Approved answer: Bybit only.

Impact: Stage 53-B1 planning is limited to Bybit.

Status: ANSWERED / APPROVED

### OI-2: Environment / Market Access Mode

Approved answer: Testnet/demo only.

Impact: No production live access is authorized.

Status: ANSWERED / APPROVED

### OI-3: Endpoint Permission Scope

Approved answer: Read-only balances + positions; optional order status read-only; no place/cancel orders.

Impact: Stage 53-B1 has no write endpoint authorization.

Status: ANSWERED / APPROVED

### OI-4: Secret Handling

Approved answer: Env vars for local testnet; secret manager/GitHub secrets later; no secrets in repo/prompts/docs.

Impact: No API keys, account UID, email, balances, or signed payloads belong in repo, prompts, docs, or logs.

Status: ANSWERED / APPROVED

### OI-5: API Key Permission Ceiling

Approved answer: Read-only API key only; withdrawal permission forbidden.

Impact: Any key with withdrawal permission is unacceptable.

Status: ANSWERED / APPROVED

### OI-6: Live Trading Authorization Gate

Approved answer: Live trading only after full implementation + QA + regression + external review + separate explicit owner approval.

Impact: Live trading remains NO-GO.

Status: ANSWERED / APPROVED

### OI-7: Authority Model

Approved answer: Keep current authority model exactly.

Impact: No risk/orchestrator/execution_service/position_manager authority changes are approved.

Status: ANSWERED / APPROVED

### OI-8: Stage 53-B1 Maximum Scope

Approved answer: Authenticated client + testnet read-only balances and positions only.

Impact: Optional order status read-only is permitted; no place order, cancel order, live execution, or live reconcile.

Status: ANSWERED / APPROVED

### OI-9: Delivery Protocol

Approved answer: Full protocol: architect -> plan -> implement -> QA -> external review if needed -> PR -> merge.

Impact: Implementation still requires separate approval.

Status: ANSWERED / APPROVED

---

## Stage 53-B1 Allowed Client Methods (future implementation scope)

These are the only Bybit V5 methods the Stage 53-B1 client may implement if a
separate implementation task is explicitly approved after planning.
Any method not in this list requires a separate design decision before it may be added.

| Method              | Endpoint                          | Type        |
|---------------------|-----------------------------------|-------------|
| get_server_time     | GET /v5/market/time               | read-only   |
| get_wallet_balance  | GET /v5/account/wallet-balance    | read-only   |
| get_open_positions  | GET /v5/position/list             | read-only   |
| get_order_status    | GET /v5/order/realtime            | read-only, optional |

Note: get_server_time is a public endpoint but is included here as a connectivity check
for the authenticated client initialization path.

No place_order or cancel_order method is authorized for Stage 53-B1.
No live execution, live reconcile, or production balance flow is authorized.

---

## Forbidden in Stage 53-B

- No wiring into execution_service startup or request path
- No automatic order placement from any service
- No live trading of any kind
- No stop-loss automation
- No strategy quality filters
- No Event Bus implementation
- No Redis Pub/Sub implementation
- No changes to apps/execution_service
- No changes to apps/position_manager
- No changes to apps/orchestrator
- No changes to apps/risk_engine
- No changes to config/
- No changes to infra/
- No changes to alembic/

The authenticated client lives in libs/exchange/ only.
It is tested in tests/libs/exchange/ only.
It is not imported by any app in Stage 53-B.

---

## Security Rules

### API Key Handling

- API key and secret are loaded exclusively from environment variables
- Key names: BYBIT_API_KEY and BYBIT_API_SECRET
- No API key or secret may appear in any source file, config file, or log output
- Authenticated client initialization fails closed if credentials are missing
- No service startup path is changed in Stage 53-B
- Credential validation and private smoke are explicit, not automatic service startup wiring

### Request Signing

- All private requests use HMAC-SHA256 with timestamp + recv_window + params
- Timestamp drift > recv_window causes immediate fail-closed rejection
- Signature errors from Bybit (retCode 10003, 10004) raise a typed AuthError
- AuthError is not retried - it propagates immediately to the caller

### Rate Limits

- retCode 10006 raises ExchangeRateLimited (already defined in libs/exchange/errors.py)
- ExchangeRateLimited is fail-closed - the caller must decide whether to retry
- No automatic retry with backoff is implemented in Stage 53-B (Stage 53-C concern)

### Key Permission Guard

- Key must NOT have withdrawal permission
- This is checked at client construction time via the key metadata endpoint
  GET /v5/user/query-api
- If the key has withdrawal permission, a typed error is raised and the client refuses
  to initialize

---

## Deferred Order Idempotency Design (Beyond Stage 53-B1)

Order placement is not authorized for Stage 53-B1. The notes below are retained as future
design context only and require separate approval before any implementation.

### Client Order ID

- All place_order calls receive a client_order_id parameter
- client_order_id = execution_id
- Rationale: direct DB/exchange/journal/operator traceability
- A hash-derived client_order_id is non-canonical and may be considered only as a
  future fallback if an exchange format constraint is discovered and explicitly approved
- client_order_id is used as exchange-level idempotency key where supported by Bybit
- Duplicate or ambiguous client_order_id responses must halt and require manual review
- HTTP 200 is not sufficient confirmation of order state; order status must be confirmed
  by polling get_order_status before the placement is considered complete
- This is exchange-level idempotency layered on top of the existing DB-level idempotency
  in execution_service

### Order Status

- get_order_status accepts either orderId (Bybit) or orderLinkId (client_order_id)
- The client stores and returns both IDs in the response model

---

## Deferred Order Status Policy (Beyond Stage 53-B1 Writes)

Stage 53-B1 may optionally query order status read-only. Order placement and polling for
newly placed live orders are not authorized in Stage 53-B1.

- Order placement is not complete until exchange order status is known
- Runtime must not assume success from HTTP 200 alone
- get_order_status polling is required; this is a prerequisite before Stage 53-C can be complete
- Unknown order status must halt further orders for the affected symbol or system depending
  on severity
- Ambiguous order state must create an incident and require manual review before any
  further automated action is taken

---

## Balance and Margin Policy

- Before any live order placement, account equity and available balance must be checked
- Balance and margin checks are live blockers before Stage 53-F
- Missing, stale, or failed balance data must fail closed - no order may be placed
- Risk sizing must not assume available balance from config or memory; it must be read
  from the exchange at order time

---

## Partial Fill Handling

Partial fills are treated as HALT + manual review in Stage 53 scope.

- A partially filled order is not automatically closed or amended
- The execution_service (future wiring, not in 53-B) must detect the partial fill via
  get_order_status polling
- On partial fill detection: halt further orders for that symbol, log at ERROR level,
  alert through the existing alerting mechanism, wait for operator resolution
- No automatic fill completion or averaging is implemented in Stage 53

---

## First Private Smoke (read-only only)

Before any write endpoint is tested, a private read-only smoke must pass.
This is a manual verification step, not automated in 53-B.

Smoke sequence:
1. Client instantiates with API key from environment
2. get_server_time - confirms connectivity and clock sync
3. get_wallet_balance - confirms key has read access to account
4. get_open_positions - confirms key has read access to position data
5. All three must return valid non-error responses
6. No place_order or cancel_order is called in the smoke

If any read-only call fails, the key configuration is corrected before proceeding.

---

## Definition of Done for Stage 53-B Design Lock

- [x] This document exists at docs/STAGE_53B_DESIGN_LOCK.md
- [x] All nine owner decisions are listed with their constraints
- [x] Allowed client methods are enumerated
- [x] Forbidden scope is explicit
- [x] Security rules documented
- [x] Idempotency design documented
- [x] Order status policy documented
- [x] Balance and margin policy documented
- [x] Partial fill policy documented
- [x] First private smoke sequence documented
- [x] Owner decisions answered
- [ ] Stage 53-B1 planning approved
- [ ] Stage 53-B1 implementation may begin

No runtime files were changed to produce this document.
No secrets were added.
No code was written.

---

## Stage Dependency Chain

53-A CLOSED (3b3b06f) -> 53-B BLOCKED (owner input) -> 53-C BLOCKED -> 53-D BLOCKED -> 53-E BLOCKED -> 53-F BLOCKED

Live execution remains forbidden until 53-F is complete and all canonical Stage 53 live blockers are closed.
