# Stage 53-B Design Lock
# Authenticated Bybit Exchange Client Foundation

## Status

- Stage 53-B design lock: CLOSED
- Stage 53-B implementation: BLOCKED on owner input / owner decisions
- Current mode: paper trading only
- Live trading: NO-GO
- Stage 53-A closed: 3b3b06f (feat: add Bybit public market data adapter)
- Owner decisions tracker: docs/STAGE_53B_OWNER_DECISIONS.md
- Stage 53-B gate: BLOCKED - all owner decisions below must be confirmed before any implementation begins

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

The following decisions must be confirmed by the owner before Stage 53-B implementation begins.
No implementation work starts until all nine are answered.

### OI-1: Bybit Account Type

Question: Is the Bybit account Unified Trading Account (UTA) or Classic?

Impact: Determines the correct wallet endpoint, margin model, and position structure.
The V5 API differs meaningfully between UTA and Classic for balance and position queries.

Required answer: Unified or Classic

### OI-2: Market Type for First Live

Question: What market type will be used for the first live trade: linear perpetual or spot?

Impact: Determines which category is passed to all V5 order and position endpoints.
Linear perpetuals use margin and have funding rates. Spot uses no margin.
The market type must match the account type confirmed in OI-1.

Required answer: linear or spot

### OI-3: Position Mode

Question: Is the account set to One-way mode or Hedge mode for linear perpetuals?

Constraint: One-way mode is required for Stage 53 execution design.
Hedge mode requires side-aware position tracking which is out of scope for Stage 53.

Required answer: Confirm One-way mode is active

### OI-4: Leverage for First Live Trade

Question: What leverage is configured on the account for BTCUSDT linear perpetual?

Impact: Risk sizing depends on this. Must match what is set in the Bybit UI before any live
order is placed. This value is read at runtime but the decision must be made before Stage 53-F.
Only applies if OI-2 is linear.

Required answer: Numeric value (e.g. 1, 3, 5, 10)

### OI-5: API Key Permissions

Question: Has an API key been created with exactly these permissions?
- Futures: read + write
- NO withdrawal permission

Constraint: The key must never have withdrawal permission. Any key with withdrawal permission
will be rejected by the fail-closed security check at client initialization.

Required answer: Confirm key exists with correct permissions

### OI-6: IP Whitelist Decision

Question: Should the Bybit API key be IP-whitelisted to the VPS IP (45.145.5.254)?

Impact: Whitelisting is strongly recommended. A non-whitelisted key with Futures write
permission represents unnecessary exposure if the key is ever leaked.

Required answer: Yes (whitelist VPS IP) or No (accept the risk, document reason)

### OI-7: First Live Order Type Preference

Question: Should the first live order use a market order or a limit order?

Impact: Market orders guarantee fill but give up price. Limit orders control price but may
not fill. The execution path design and partial fill risk differ significantly between the two.
This decision must be made before Stage 53-C order placement design begins.

Required answer: market or limit

### OI-8: First Live Maximum Notional Size

Question: What is the maximum notional size (in USDT) for the first live trade?

Impact: Sets the hard ceiling for the first controlled live order in Stage 53-F.
Risk engine sizing must not exceed this value regardless of signal strength.
Must be confirmed before Stage 53-F risk sizing is finalized.

Required answer: Numeric USDT value (e.g. 50, 100, 200)

### OI-9: Manual Stop-Loss Procedure

Question: What is the manual stop-loss procedure on the Bybit UI if a live position
moves against the system and the automated path fails?

Impact: Stage 53-F runs with no automated stop-loss. The operator must be able to close
the position manually on Bybit if needed. This procedure must be documented and understood
before any live order is placed.

Required answer: Documented procedure confirmed by owner

---

## Allowed Client Methods (future implementation scope)

These are the only private Bybit V5 methods the Stage 53-B client may implement.
Any method not in this list requires a separate design decision before it may be added.

| Method              | Endpoint                          | Type        |
|---------------------|-----------------------------------|-------------|
| get_server_time     | GET /v5/market/time               | read-only   |
| get_wallet_balance  | GET /v5/account/wallet-balance    | read-only   |
| get_open_positions  | GET /v5/position/list             | read-only   |
| get_order_status    | GET /v5/order/realtime            | read-only   |
| place_order         | POST /v5/order/create             | write       |
| cancel_order        | POST /v5/order/cancel             | write       |

Note: get_server_time is a public endpoint but is included here as a connectivity check
for the authenticated client initialization path.

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

## Idempotency Design

### Client Order ID

- All place_order calls receive a client_order_id parameter
- client_order_id is deterministic: derived from execution_id using a stable hash
- Format: hex(sha256(execution_id))[:32]
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

## Order Status Policy

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
- [ ] Owner decisions answered (BLOCKED)
- [ ] Implementation may begin

No runtime files were changed to produce this document.
No secrets were added.
No code was written.

---

## Stage Dependency Chain

53-A CLOSED (3b3b06f) -> 53-B BLOCKED (owner input) -> 53-C BLOCKED -> 53-D BLOCKED -> 53-E BLOCKED -> 53-F BLOCKED

Live execution remains forbidden until 53-F is complete and all 11 live blockers are closed.
