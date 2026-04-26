# Stage 53-B Owner Decisions

## Status

- Status: OPEN
- Current mode: paper trading only
- Live trading: NO-GO
- Stage 53-A: CLOSED, commit 3b3b06f
- Stage 53-B design lock: CLOSED, commit 5e5eb48
- Stage 53-B implementation: BLOCKED until all decisions are answered

## Owner decision tracker

| ID | Decision | Status | Owner answer | Evidence required | Notes |
|---|---|---|---|---|---|
| OI-1 | Account type: Unified or Classic | OPEN | TBD | Owner confirmation of whether the Bybit account is Unified Trading Account or Classic. | Notes must not contain secrets. |
| OI-2 | Market type for first live: linear or spot | OPEN | TBD | Owner confirmation that the first live market type is linear or spot. | Notes must not contain secrets. |
| OI-3 | Position mode: One-way required | OPEN | TBD | Owner confirmation that One-way mode is active before Stage 53-B implementation begins. | Notes must not contain secrets. |
| OI-4 | Leverage for first live if using linear perpetuals | OPEN | TBD | Owner confirmation of the configured leverage value if OI-2 is linear. | Notes must not contain secrets. |
| OI-5 | API key permissions: Futures read+write, NO withdrawal | OPEN | TBD | Owner confirmation that API key permissions are Futures read+write and withdrawal is disabled. | Notes must not contain secrets. |
| OI-6 | IP whitelist for VPS | OPEN | TBD | Owner decision plus redacted evidence that the VPS IP whitelist is enabled if selected. | Notes must not contain secrets. |
| OI-7 | First live order type: market or limit | OPEN | TBD | Owner confirmation that the first live order type is market or limit. | Notes must not contain secrets. |
| OI-8 | First live maximum notional size | OPEN | TBD | Owner confirmation of the maximum first live notional amount. | Notes must not contain secrets. |
| OI-9 | Manual stop-loss procedure on Bybit UI | OPEN | TBD | Owner-confirmed step checklist for manual stop-loss procedure in Bybit UI. | Notes must not contain secrets. |

## Decision rules

- No 53-B implementation until all rows are ANSWERED.
- No API keys or secrets in this file.
- No signed request payloads in this file.
- No account UID, email, personal data, or sensitive balances in this file.
- Screenshots must redact keys, secrets, balances if sensitive, UID, email, and personal data.
- If an answer changes, update this file in a new commit.
- Live trading remains NO-GO even after decisions are answered.

## Recommended conservative defaults

- Market type: linear
- Position mode: One-way
- Leverage: 1x or lowest practical
- API permissions: Futures read+write, NO withdrawal
- IP whitelist: enabled for VPS IP
- First live max notional: minimum practical amount
- Stop-loss: manual on Bybit UI for first live

## Non-goals

- Do not define implementation details for authenticated Bybit client.
- Do not define live order execution flow.
- Do not change runtime mode.
- Do not modify safety authority.
- Do not modify risk, review, orchestrator, execution_service, or position_manager.
- Do not store credentials.
