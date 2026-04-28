# Stage 53-B2 Real Bybit Read-Only Connectivity Smoke Plan

## 1. Current State

Stage 53-B1 mocked authenticated read-only foundation is complete and accepted.

Existing mocked endpoint set:
- `get_server_time()`
- `get_wallet_balance()`
- `get_open_positions()`

Current readiness:
- Docs-ready: yes for Stage 53-B1 mocked foundation.
- Code-ready: yes for mocked read-only foundation only.
- Test-ready: yes for mocked behavior only.
- Runtime-ready: no.
- Live/probe/trading readiness: not approved.

Stage 53-B2a is implemented, committed, and pushed at:

`a511e2f feat: add Stage 53-B2 server-time smoke harness`

B2a includes a `server_time` smoke harness, mocked tests, and a direct no-flag
safety latch that exits 3 with sanitized `authorization_required` JSON.

Real credentials, real Bybit calls, runtime smoke, service wiring,
`order_status`, wallet_balance smoke, open_positions smoke, and write/live
methods are not authorized by this document or by B2a.

## 2. Stage 53-B2 Scope

Stage 53-B2 is a plan for real Bybit testnet read-only connectivity smoke.

Allowed future smoke candidates:
- `get_server_time()`
- `get_wallet_balance()`
- `get_open_positions()`

This document authorizes no implementation and no real smoke execution. Each
implementation or real-smoke step requires a separate Human Owner decision.

## 3. Gate Structure

- B2a: implemented server_time smoke harness + mocked tests only at a511e2f
- B2b: execute real server_time smoke only after explicit Human Owner authorization
- B2c: implement wallet_balance smoke harness + mocked tests only
- B2d: execute real wallet_balance smoke only after explicit Human Owner authorization
- B2e: implement open_positions smoke harness + mocked tests only
- B2f: execute real open_positions smoke only after explicit Human Owner authorization

Each gate requires a separate Human Owner decision.

No automatic progression is allowed. Passing B2a does not authorize B2b. Passing
B2b does not authorize B2c. Passing any gate does not authorize trading, live,
probe, runtime readiness, service wiring, `order_status`, or write/live methods.

B2b real server_time smoke remains not authorized and not executed.

## 4. Forbidden Scope

Stage 53-B2 must not include:
- `order_status`
- `place_order`
- `cancel_order`
- `set_leverage`
- `withdraw`
- `transfer`
- `live_reconcile`
- `live_execution`
- service startup wiring
- production private endpoint use
- execution_service integration
- position_manager integration
- orchestrator integration
- risk_engine integration
- dashboard integration
- storing credentials
- logging credentials
- logging signatures
- logging raw wallet payloads
- logging raw position payloads
- treating exchange wallet/positions as internal authoritative state
- trading readiness claims
- probe readiness claims
- live readiness claims
- runtime readiness claims

## 5. Credential Safety

Required environment variable names only:
- `BYBIT_B1_ENVIRONMENT`
- `BYBIT_B1_API_KEY`
- `BYBIT_B1_API_SECRET`

Accepted alias names already supported by settings:
- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`

Rules:
- Do not print values.
- Do not print secret lengths.
- Do not use `env | grep BYBIT`.
- Do not store `.env` files.
- Do not paste credentials into prompts, docs, logs, command history, screenshots,
  or issue comments.
- Human Owner verifies read-only/no-withdrawal/testnet key permissions externally
  before any real smoke.

## 6. Read-Only / No-Withdrawal Permission Verification Plan

Before any real smoke gate, the Human Owner must externally verify:
- key is for Bybit testnet only
- key has read-only permissions only
- withdrawal permission is disabled
- transfer permission is disabled
- order/write permission is disabled unless a future separately approved stage
  changes the permission model
- key is not production

The repository must not attempt to infer or print permission details from raw API
responses unless a future owner-approved harness exposes only sanitized success,
failure, and typed error category.

## 7. Secret Redaction / Logging Rules

The smoke harness must never log:
- raw credentials
- auth headers
- signatures
- signed payloads
- raw request headers
- raw response body
- raw `retMsg`
- account IDs
- balances
- position symbols by default
- position sides
- position sizes
- position prices
- PnL
- margin values
- wallet payloads
- position payloads

The smoke harness may log only the safe output fields listed in Section 11.

## 8. Smoke Execution Procedure

General procedure for each real-smoke gate:
1. Confirm Human Owner explicitly authorized exactly one gate.
2. Confirm `git status --short --branch` is clean and synced.
3. Confirm no runtime/service wiring is part of the gate.
4. Confirm environment variable names are present without printing values or
   lengths.
5. Run only the owner-authorized smoke operation.
6. Emit only safe output fields.
7. Stop after the single operation.
8. Record result as inconclusive/failure/success for that smoke only.
9. Do not progress to the next gate without separate Human Owner authorization.

The first real smoke is testnet only. Demo requires a separate owner decision and
explicit URL mapping verification.

## 9. Allowed Commands

Planning-only commands:
- `git status --short --branch`
- `git log -1 --oneline`
- `git diff --check`
- `python -m pytest tests\libs\exchange -q`
- `python -m pytest tests\libs\config -q`

Future implementation-gate commands, if separately authorized:
- targeted mocked tests for the smoke harness
- `python -m pytest tests\libs\exchange -q`
- `python -m pytest tests\libs\config -q`

Future real-smoke commands must be defined in the implementation PR and approved
by the Human Owner before execution. They must not print environment values and
must not call more than one endpoint family per gate.

## 10. Required Environment Variables

Names only:
- `BYBIT_B1_ENVIRONMENT`
- `BYBIT_B1_API_KEY`
- `BYBIT_B1_API_SECRET`

Supported aliases:
- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`

No values belong in the repository, docs, prompts, command output, logs, or final
reports.

## 11. Expected Safe Outputs

Allowed output fields:
- operation name
- success/failure
- endpoint family
- `retCode` only
- typed sanitized error category
- `elapsed_ms`
- counts only

Examples of safe count-only outputs:
- wallet coin count
- open position count

Counts are external observations only. They must not be treated as internal
trading authority.

## 12. Forbidden Outputs

Forbidden outputs:
- raw `retMsg`
- raw response body
- raw wallet payload
- raw position payload
- account IDs
- balances
- position symbols by default
- position sides
- position sizes
- position prices
- PnL
- margin values
- auth headers
- signatures
- signed payloads
- API key
- API secret
- secret length

## 13. Failure Handling

Failure handling must fail closed and stop the phase.

The following outcomes stop the phase:
- missing credentials
- malformed credentials
- auth failure
- permission denied
- timeout
- malformed payload
- unexpected response
- production endpoint detected
- rate limit
- network unavailable
- HTTP error

Rate limit is inconclusive, not success. No automatic retry is allowed unless a
future Human Owner decision explicitly authorizes a bounded retry policy.

There is no automatic progression after failure or success.

## 14. Rollback / Cleanup Plan

No temp files are created by default.

If output capture is explicitly requested, the owner must provide the path. Cleanup
may remove only the owner-provided path after verifying the resolved absolute path.

No credentials, `.env` files, raw payloads, headers, signatures, or account data
may be written to disk.

## 15. Engineering Rules v2 Impact

1. Commit Ownership Lives In Use-Cases
- No database writes or use-case commits are part of B2 smoke planning.

2. Enforce At Authoritative Boundaries
- Smoke output remains observation-only. It must not alter risk, execution, or
  position authority.

3. No Blocking Calls In Async Contexts
- Any future smoke harness must use async HTTP through the existing read-only
  client pattern and must not add sync `httpx.*` calls in async paths.

4. Idempotency Is A Contract
- Smoke operations are read-only and must be safe to rerun. They must not mutate
  exchange or internal state.

5. Side-Effects Must Have Compensation Or Repair
- No side effects are allowed. If future output capture is owner-approved, cleanup
  must be explicit and path-guarded.

6. Architecture Boundaries Are Enforced In Code
- No `apps/*` service wiring, cross-service integration, runtime startup import,
  or position_manager/execution_service/orchestrator/risk/dashboard integration is
  allowed in B2 smoke planning.

7. Failure Must Be Observable
- Failures must be reported as typed sanitized categories with operation name,
  endpoint family, `retCode` when available, and `elapsed_ms`; raw payloads and
  secrets remain forbidden.

## 16. Runtime Readiness Boundary

Successful smoke does not mean runtime-ready.

Successful smoke does not mean trading-ready.

Successful smoke does not mean live-ready.

Successful smoke does not mean probe-ready.

Successful smoke does not authorize service wiring.

Successful smoke does not authorize `order_status` or write/live methods.

Successful smoke does not authorize production private endpoint use.

## 17. Human Owner Decisions Required

Required decisions before any next action:
- Whether to accept this Stage 53-B2 smoke plan.
- Whether to authorize B2a implementation of a server_time smoke harness with
  mocked tests only.
- Whether to authorize B2b real server_time smoke after B2a is reviewed.
- Whether wallet_balance and open_positions smoke gates remain in scope after
  server_time results.
- Whether demo environment is ever allowed, with explicit URL mapping.
- Whether any output capture is allowed and, if so, the exact path.

## 18. Recommended Next Step

Accept or revise this docs-only Stage 53-B2 smoke plan.

If accepted, the next implementation request should be B2a only:
implement server_time smoke harness + mocked tests only, with no real Bybit call,
no credentials, no service wiring, no `order_status`, and no write/live methods.
