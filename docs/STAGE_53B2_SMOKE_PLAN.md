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

Stage 53-B2b real Bybit testnet `server_time` smoke was executed locally by the
Human Owner after safe credential presence and hygiene checks.

B2b result:
- command: `python scripts\smoke_server_time.py --allow-real-smoke`
- `LASTEXITCODE=0`
- `elapsed_ms=1534`
- sanitized output only
- endpoint family: `server_time`
- status: success

Credentials were used locally only for the owner-authorized B2b smoke and must
not be stored, disclosed, logged, committed, or pasted into chat.

No wallet_balance smoke, open_positions smoke, `order_status`, write/live
methods, service wiring, runtime readiness, trading readiness, live readiness, or
probe readiness were authorized or confirmed by B2b.

Stage 53-B2c wallet_balance smoke harness is implemented, committed, pushed, and
remote-visible at:

`c9b1337 feat: add Stage 53-B2 wallet-balance smoke harness`

B2c includes:
- `scripts/smoke_wallet_balance.py`
- `tests/scripts/test_smoke_wallet_balance.py`
- wallet_balance smoke harness
- mocked tests only
- direct no-flag latch that exits 3 with sanitized `authorization_required` JSON
- `--allow-real-smoke` required for the real-capable path
- mocked success output limited to endpoint, status, exchange, account_type,
  coins_count, and elapsed_ms

B2c did not run real wallet_balance smoke, did not use credentials, did not add
open_positions smoke, did not add `order_status`, did not add write/live methods,
and did not add service wiring.

B2c is code-ready/test-ready only for mocked wallet_balance smoke harness
behavior. It did not run real wallet_balance smoke, did not use credentials, and
does not authorize B2d. Runtime readiness, trading readiness, live readiness, and
probe readiness remain not approved.

Stage 53-B2c.1a authenticated readiness hardening is implemented, committed,
pushed, and remote-visible at:

`189cb0a feat: harden Stage 53-B2 authenticated smoke readiness`

B2c.1a includes:
- unsigned public `/v5/market/time` methodology for `server_time`
- `get_server_time()` no longer requires credentials
- private reads still fail closed without credentials
- private signed reads include `X-BAPI-SIGN-TYPE: 2`
- deterministic signed GET query handling consistent with what is sent
- `wallet_balance` signs/sends `accountType=UNIFIED`
- safe retCode classification for `10002`, `10003`, `10004`, `10005`, `10006`,
  `10007`, and `10010`
- `10006` remains exit code 2 / inconclusive in smoke harnesses
- no raw `retMsg` or raw response body exposure
- wallet smoke output remains sanitized

B2c.1a test evidence:
- server_time no-flag latch: `LASTEXITCODE=3`
- wallet_balance no-flag latch: `LASTEXITCODE=3`
- `tests/scripts`: 40 passed
- `tests/libs/exchange`: 86 passed
- `tests/libs/config`: 19 passed

B2c.1a is code-ready/test-ready only for mocked/local authenticated-readiness
hardening. It did not add query-api support, open_positions smoke,
`order_status`, write/live methods, service wiring, runtime readiness, trading
readiness, live readiness, or probe readiness.

Stage 53-B2c.1b query-api read-only preflight harness is implemented,
committed, pushed, and remote-visible at:

`00d84d8 feat: add Stage 53-B2 query-api preflight harness`

B2c.1b includes:
- `get_query_api_info()` signed read-only support for `GET /v5/user/query-api`
- sanitized `ApiKeyInfo` boolean/status summary model
- `scripts/smoke_query_api.py`
- direct no-flag latch that exits 3 with sanitized `authorization_required` JSON
- no-flag path that does not load settings/client/credentials or call Bybit
- mocked tests only

Query-api success output is exactly:
- endpoint
- status
- exchange
- read_only
- permissions_safe
- key_active
- deadline_days_present
- expired_at_present
- elapsed_ms

`operation` and `endpoint_family` are absent from query-api success output.
Unsafe `readOnly`, unsafe permissions, expired/non-positive/missing/stale/
malformed expiry metadata, including stale and malformed `expiredAt`, fail
closed. Rate limit remains exit code 2 / inconclusive.

B2c.1b did not run real query-api execution, did not use credentials, did not
call Bybit, did not run real wallet_balance smoke, did not add open_positions
smoke, did not add `order_status`, did not add write/live methods, and did not
add service wiring. B2d real wallet_balance smoke remains unauthorized pending a
separate Human Owner decision. Runtime readiness, trading readiness, live
readiness, and probe readiness remain not approved.

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
- B2b: completed successful real testnet server_time smoke after explicit Human Owner authorization
- B2c: implemented wallet_balance smoke harness + mocked tests only at c9b1337
- B2c.1: authenticated readiness audit / query-api preflight decision; no real wallet smoke
- B2c.1a: implemented authenticated readiness hardening at 189cb0a; mocked/local
  hardening only; no real wallet smoke
- B2c.1b: implemented query-api read-only preflight harness + mocked tests at
  00d84d8; no real query-api execution; no real wallet smoke
- B2d: execute real wallet_balance smoke only after explicit Human Owner authorization
- B2e: implement open_positions smoke harness + mocked tests only
- B2f: execute real open_positions smoke only after explicit Human Owner authorization

Each gate requires a separate Human Owner decision.

No automatic progression is allowed. Passing B2a does not authorize B2b. Passing
B2b does not authorize B2c, and B2c does not authorize B2d. Passing any gate does
not authorize trading, live, probe, runtime readiness, service wiring,
`order_status`, or write/live methods.

B2b real server_time smoke is complete for `server_time` only. B2c mocked
wallet_balance harness is complete for mocked behavior only. B2d real
wallet_balance smoke is NO-GO and remains unauthorized until B2c.1 is completed
and the Human Owner makes a separate B2d decision. No automatic progression from
B2c to B2d and no automatic retry are allowed.

## 3A. Stage 53-B2c.1 Authenticated Readiness Audit

Stage 53-B2c.1 is an intermediate protected planning/audit gate before B2d.

B2c.1 is not real wallet smoke. B2c.1 must not call `wallet_balance`, must not
call `open_positions`, must not authorize `order_status`, and must not authorize
write/live methods.

B2c.1 purpose:
- audit current signing and query-string behavior
- audit whether `server_time` is unsigned or signed
- audit whether `X-BAPI-SIGN-TYPE: 2` is present or intentionally omitted
- decide whether to add `/v5/user/query-api` as a new read-only preflight
  endpoint
- verify docs wording around key active/not expired checks

External research and expert review confirm that direct transition from B2c to
B2d should be blocked until this audit and Human Owner decision are complete.
B2d real wallet_balance smoke remains NO-GO.

B2c.1a closed the first hardening sub-slice of B2c.1. It does not complete or
replace any Human Owner decision about query-api, and it does not authorize B2d.
Query-api remains a separate Human Owner decision and was not implemented.

## 3B. Query-API Scope Boundary

`GET /v5/user/query-api` is not currently part of the existing B1/B2 endpoint
set unless separately authorized.

Adding query-api requires an explicit Human Owner decision. If authorized,
query-api is read-only preflight only. Its purpose is to verify `readOnly`,
permissions, key active/not expired status, and testnet environment before
authenticated private smoke.

Query-api output must not print:
- API key
- API secret
- raw permissions payload
- user IDs
- account IDs
- raw response body
- raw `retMsg`

## 3C. Server-Time Semantics

`/v5/market/time` is public and should be treated as an unsigned
connectivity/time endpoint.

If the current implementation uses a signed `server_time` path, record that as an
audit finding / backlog issue, not as the ideal future methodology. B2b success
remains valid as a real testnet connectivity checkpoint, but future methodology
should separate public unsigned smoke from authenticated private smoke.

## 3D. Signing Audit Before B2d

Before B2d can be authorized:
- GET query string construction must be deterministic.
- The query string used for signing must exactly match what is sent.
- Official pybit behavior sorts GET params by key; the project should audit
  whether current behavior is deterministic and equivalent.
- `X-BAPI-SIGN-TYPE: 2` should be audited before authenticated smoke.
- raw `retMsg` and raw response body remain forbidden unless separately reviewed
  and sanitized.

Safe retCode classification should cover at least:
- `10002`: timestamp / recv_window issue
- `10003`: invalid key or environment
- `10004`: bad signature
- `10005`: permission denied
- `10006`: rate limit / inconclusive / exit 2
- `10007`: authentication failed
- `10010`: IP mismatch

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

Permanent preflight rule:

Before any real Bybit smoke execution, the active shell/session must pass all of
the following:
- safe credential presence check
- safe credential hygiene check
- Human Owner external key active/not expired confirmation

The 7-day note is not treated as verified API key expiry. It may reflect secret
visibility or demo/order-retention confusion unless verified. The required
operational rule is key active/not expired confirmation via Bybit UI or a future
owner-authorized query-api preflight.

Before any real smoke, the Human Owner must externally confirm:
- key is still active
- key has not expired
- key is testnet-only
- key is read-only
- withdrawal is disabled
- transfer/write/order permissions are disabled

The assistant must not inspect secret values, inspect the Bybit UI, or ask the
Human Owner to paste credentials into chat.

If secret availability is uncertain, recreate the testnet key rather than
exposing, guessing, or attempting to recover the secret.

Safe credential presence check output is limited to:
- `OK: VARIABLE_NAME is set`
- `MISSING: VARIABLE_NAME is not set`

Safe credential hygiene check may check only:
- empty/missing
- leading/trailing whitespace
- newline/carriage return/tab
- accidental surrounding quote characters

Safe credential hygiene output is limited to:
- `OK: VARIABLE_NAME basic hygiene check passed`
- `WARNING: VARIABLE_NAME is empty or missing`
- `WARNING: VARIABLE_NAME has leading/trailing whitespace`
- `WARNING: VARIABLE_NAME contains newline or tab`
- `WARNING: VARIABLE_NAME appears to include surrounding quote characters`

Credential preflight output must never include:
- values
- lengths
- masked values
- prefixes or suffixes
- hashes
- `env | grep BYBIT`
- echoed secret variables
- screenshots containing secrets

Recommended PowerShell preflight snippet:

```powershell
@("BYBIT_B1_ENVIRONMENT","BYBIT_B1_API_KEY","BYBIT_B1_API_SECRET") | ForEach-Object {
    if ([Environment]::GetEnvironmentVariable($_)) {
        Write-Output "OK: $_ is set"
    } else {
        Write-Output "MISSING: $_ is not set"
    }
}

@("BYBIT_B1_API_KEY","BYBIT_B1_API_SECRET") | ForEach-Object {
    $v = [Environment]::GetEnvironmentVariable($_)

    if ($null -eq $v -or $v -eq "") {
        Write-Output "WARNING: $_ is empty or missing"
        return
    }

    if ($v -ne $v.Trim()) {
        Write-Output "WARNING: $_ has leading/trailing whitespace"
    }

    if ($v.Contains("`n") -or $v.Contains("`r") -or $v.Contains("`t")) {
        Write-Output "WARNING: $_ contains newline or tab"
    }

    if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
        Write-Output "WARNING: $_ appears to include surrounding quote characters"
    }

    if (($v -eq $v.Trim()) -and -not ($v.Contains("`n") -or $v.Contains("`r") -or $v.Contains("`t")) -and -not (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'")))) {
        Write-Output "OK: $_ basic hygiene check passed"
    }
}
```

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
- any credential hygiene `WARNING`
- expired or uncertain key status
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

Successful credential presence, hygiene, and key-validity preflight does not mean
runtime-ready, trading-ready, live-ready, or probe-ready. It does not authorize
wallet_balance smoke, open_positions smoke, `order_status`, service wiring, or
write/live methods.

## 14. Rollback / Cleanup Plan

No temp files are created by default.

If output capture is explicitly requested, the owner must provide the path. Cleanup
may remove only the owner-provided path after verifying the resolved absolute path.

No credentials, `.env` files, raw payloads, headers, signatures, or account data
may be written to disk.

## 15. Engineering Rules v2 Impact And Architecture Adaptations

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

Project-specific planning constraints:
- Current authorized state: `READ_ONLY_TESTNET_SMOKE`.
- Future docs/code concepts may include `READ_ONLY_ACTIVE`,
  `READ_ONLY_DEGRADED`, and `READ_ONLY_HALTED`.
- `BybitReadOnlyClient` must remain permanently read-only.
- A future write client, if ever authorized, must be a separate object/module/gate.
- Exchange is authoritative for actual balances, actual positions, fills/trades,
  and final exchange-side order state.
- The local system is authoritative for intended commands, client order IDs,
  audit trail, and local lifecycle state.
- No component may treat read-only exchange observations as internal trading
  authority without reconciliation.
- Reconciliation is required before any `order_status`, write, or live path.
- Unknown/lost order state in a future OMS must lead to halt plus Human Owner
  review.
- Kill switch, idempotency, OMS, risk controls, and runbook remain future gates
  before any write path.

These are planning constraints, not immediate implementation requirements. This
document does not authorize a TradingState enum in code, ExchangePort refactor,
OMS, RiskEngine, kill switch, reconciliation framework, log handler-level
scrubber, dependency changes, CI secret scanning, or service wiring.

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
- Whether to accept the B2c wallet_balance smoke harness checkpoint.
- Whether to authorize B2c.1 authenticated readiness audit / query-api preflight
  decision.
- Whether to authorize adding query-api as a read-only preflight endpoint.
- Whether to authorize B2d real wallet_balance smoke after B2c.1 is completed
  and reviewed.
- Whether wallet_balance and open_positions smoke gates remain in scope after
  server_time results.
- Whether demo environment is ever allowed, with explicit URL mapping.
- Whether any output capture is allowed and, if so, the exact path.

## 18. Recommended Next Step

Accept or revise this docs-only B2c wallet_balance smoke harness checkpoint.

If accepted, the next possible protected action is B2c.1 only: authenticated
readiness audit / query-api preflight decision. B2d real wallet_balance smoke is
NO-GO until B2c.1 is completed and a separate Human Owner decision authorizes
B2d.
