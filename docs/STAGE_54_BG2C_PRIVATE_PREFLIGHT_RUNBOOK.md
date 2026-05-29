# Stage 54-BG2-C Private Read-Only Preflight Runbook

> **Status: PARKED** — Bitget demo planning not active. Reopen only by explicit Owner decision.

Purpose:
- Stage 54-BG2-C is docs-only.
- It designs a future Bitget Demo private read-only preflight.
- It does not authorize implementation, credentials use, API calls, smoke, probe, runtime wiring, or a private client.

Authoritative status:
- `docs/PROGRESS.md` remains the source of truth for the current stage and gate.
- This runbook is planning only and does not approve any real preflight.

## Candidate future endpoint

- Candidate future endpoint for discussion only: `GET /api/v3/account/info`.
- This is not an approved call.
- The intent is a future private read-only preflight that could summarize account, permission, and IP-whitelist posture without exposing raw sensitive data.

Future sanitized output should stay at a high level only:
- `status`
- `exchange`
- `endpoint`
- `read_only` / `permissions_safe` summary
- `ip_whitelist_present` summary
- `elapsed_ms`, only if a future smoke is separately approved

Forbidden in logs, docs, prompts, screenshots, fixtures, and output:
- raw uid
- raw permissions
- raw IPs
- raw response body
- raw error messages
- API keys
- secrets
- passphrases
- signatures
- account IDs
- balances
- positions
- signed payloads

## Demo/private request boundary

- Any future demo private request must include explicit demo marker/header handling for `paptrading: 1`.
- REST auth headers for a future private request are expected to include:
  - `ACCESS-KEY`
  - `ACCESS-SIGN`
  - `ACCESS-TIMESTAMP`
  - `ACCESS-PASSPHRASE`
  - `Content-Type: application/json`
- A future REST signature is expected to use timestamp + uppercased method + requestPath + optional query string + body, HMAC-SHA256, Base64.
- No `paptrading` runtime behavior is implemented in BG2-C.
- No private client is implemented in BG2-C.

## Required future preflight guardrails

- Safe env presence check.
- Safe env hygiene check.
- No generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback.
- `BITGET_BG1_` namespace only unless the Human Owner later changes naming.
- Fail closed if credentials are missing or empty.
- Fail closed if environment is not `demo` or `simulated`.
- Fail closed if permissions include `trade`, `transfer`, `withdraw`, or any write-like capability.
- Fail closed if the response cannot prove a safe read-only posture.
- Rate-limited or inconclusive results must not become success.
- No automatic retry after a real preflight failure.

## Forbidden scope

- No orders.
- No cancels.
- No set_leverage.
- No withdraw.
- No transfer.
- No balances or positions smoke.
- No private smoke.
- No runtime or service wiring.
- No generic exchange adapter.
- No real network, API, exchange, or Beget operations.
- No readiness claim beyond docs-ready.

## Open owner decisions

- Whether to use `GET /api/v3/account/info` as the first future private read-only preflight endpoint.
- Whether Bitget Demo private API access is available and desired at all.
- Whether any later real preflight is authorized.
- Exact future output contract.
- Whether the first future implementation should be:
  - A. mocked private preflight parser/client skeleton
  - B. smoke harness with no-flag latch only
  - C. docs-only runbook extension

## Next allowed lane

- After BG2-C, only the Human Owner may authorize BG2-D implementation.
- The likely next safe implementation, if separately approved, is a mocked private read-only preflight parser/client skeleton only.
- No real private smoke is authorized.

## Not authorized by this runbook

- Code implementation.
- Test implementation.
- Runtime readiness.
- Trading readiness.
- Live readiness.
- Probe readiness.
