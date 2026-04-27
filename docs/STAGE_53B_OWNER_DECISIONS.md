# Stage 53-B Owner Decisions

## Status

- Status: ANSWERED / APPROVED
- Current mode: paper trading only
- Live trading: NO-GO
- Stage 53-A: CLOSED, commit 3b3b06f
- Stage 53-B design lock: CLOSED, commit 5e5eb48
- Stage 53-B implementation: NOT STARTED by this decision-sync PR
- Next allowed lane: Stage 53-B1 planning / architecture, not implementation unless separately approved
- Stage 53-B1 maximum scope: Bybit only; testnet/demo only; authenticated client; read-only balances and positions; optional order status read-only; no place order; no cancel order; no live reconcile

## Owner decision tracker

| ID | Decision | Status | Owner answer | Evidence required | Notes |
|---|---|---|---|---|---|
| OI-1 | Exchange venue | ANSWERED / APPROVED | Bybit only. | Owner approval recorded in decision-sync request. | Notes must not contain secrets. |
| OI-2 | Environment / market access mode | ANSWERED / APPROVED | Testnet/demo only. | Owner approval recorded in decision-sync request. | No production live access authorized. |
| OI-3 | Endpoint permission scope | ANSWERED / APPROVED | Read-only balances + positions; optional order status read-only; no place/cancel orders. | Owner approval recorded in decision-sync request. | No write endpoints authorized. |
| OI-4 | Secret handling | ANSWERED / APPROVED | Env vars for local testnet; secret manager/GitHub secrets later; no secrets in repo/prompts/docs. | Owner approval recorded in decision-sync request. | No API keys, account UID, email, balances, or signed payloads in repo/prompts/docs/logs. |
| OI-5 | API key permission ceiling | ANSWERED / APPROVED | Read-only API key only; withdrawal permission forbidden. | Owner approval recorded in decision-sync request. | Any key with withdrawal permission is unacceptable. |
| OI-6 | Live trading authorization gate | ANSWERED / APPROVED | Live trading only after full implementation + QA + regression + external review + separate explicit owner approval. | Owner approval recorded in decision-sync request. | Live trading remains NO-GO. |
| OI-7 | Authority model | ANSWERED / APPROVED | Keep current authority model exactly. | Owner approval recorded in decision-sync request. | No risk/orchestrator/execution_service/position_manager authority changes. |
| OI-8 | Stage 53-B1 maximum scope | ANSWERED / APPROVED | Authenticated client + testnet read-only balances and positions only. | Owner approval recorded in decision-sync request. | Optional order status read-only is permitted; no place order, cancel order, live execution, or live reconcile. |
| OI-9 | Delivery protocol | ANSWERED / APPROVED | Full protocol: architect -> plan -> implement -> QA -> external review if needed -> PR -> merge. | Owner approval recorded in decision-sync request. | Implementation still requires separate approval. |

## Decision rules

- This PR records decisions only; it does not start Stage 53-B implementation.
- Stage 53-B1 planning / architecture is the next allowed lane.
- Stage 53-B1 implementation requires separate explicit approval after planning.
- Stage 53-B1 maximum scope is Bybit testnet/demo authenticated read-only balances and positions, with optional order status read-only.
- Stage 53-B1 must not place orders, cancel orders, enable live reconcile, enable live execution, or enable live trading.
- No API keys or secrets in this file.
- No signed request payloads in this file.
- No account UID, email, personal data, or sensitive balances in this file.
- Screenshots must redact keys, secrets, balances if sensitive, UID, email, and personal data.
- If an answer changes, update this file in a new commit.
- Live trading remains NO-GO even after decisions are answered.
- Withdrawal permission is forbidden.
- No secrets belong in repo, prompts, docs, or logs.

## Recommended conservative defaults

- Exchange venue: Bybit only
- Environment: testnet/demo only
- Endpoint scope: read-only balances and positions; optional order status read-only
- API permissions: read-only only; NO withdrawal
- Secret handling: environment variables for local testnet; secret manager/GitHub secrets later
- Live trading: separate explicit owner approval required after full implementation, QA, regression, and external review

## Non-goals

- Do not define implementation details for authenticated Bybit client.
- Do not define live order execution flow.
- Do not change runtime mode.
- Do not modify safety authority.
- Do not modify risk, review, orchestrator, execution_service, or position_manager.
- Do not store credentials.
- Do not implement exchange client code in this PR.
- Do not add private endpoints in this PR.
- Do not enable order placement, order cancellation, production balances, live positions, live execution, or live reconcile.
