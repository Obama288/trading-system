# Stage 54-BG2 Design Lock

Purpose:
- Stage 54-BG2 is a Bitget Demo API design lock only.
- No implementation is authorized by this document.
- No client, smoke, or runtime wiring is authorized by this document.

Authoritative status:
- `docs/PROGRESS.md` remains the source of truth for the current stage and gate.
- Stage 54-BG1 remains the accepted config-only checkpoint that precedes any BG2 implementation decision.

## Locked facts

- Bitget Demo REST uses the Bitget API shape with a demo/simulated boundary.
- Future demo private REST requests must account for the `paptrading: 1` header.
- Auth shape uses API key, secret key, and passphrase.
- Private requests require signing.
- Public endpoints are separate from private/authenticated endpoints.
- WebSocket demo endpoints are future work and remain out of scope unless explicitly authorized later.

## Locked safety boundaries

- No API, exchange, Beget, or other network operations.
- No private smoke.
- No orders.
- No cancels.
- No set_leverage.
- No withdraw.
- No transfer.
- No runtime or service wiring.
- No generic exchange adapter.
- No generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback.
- `production`, `mainnet`, `live`, and `testnet` remain fail-closed for the current BG1/BG2 path.
- No readiness claim beyond docs-ready for this BG2 design lock.

## Locked design decisions

- Keep Bitget under an exchange-specific namespace, not a generic exchange adapter.
- Keep env namespace `BITGET_BG1_` for the current config-only slice unless a later Human Owner decision changes naming.
- Passphrase remains `SecretStr`.
- Any future signing helper must redact all secret-bearing data.
- Any future client must split public unsigned methods from private signed methods.
- Any future private read-only path must fail closed without credentials.
- Any future demo private path must include explicit demo/paper-trading marker/header handling.
- No raw response body or raw error message containing sensitive values in logs or docs.

## Open owner decisions before any BG implementation

- BG2-A: whether to authorize a public connectivity skeleton first.
- BG2-B: whether to authorize a private signing helper first.
- BG2-C: whether to authorize a read-only account/query preflight path.
- Whether to use Bitget demo private endpoints at all.
- Whether any later network smoke is allowed.
- Which exact first endpoint is authorized if implementation is later approved.

## Next allowed lane

- After this docs-only design lock, only the Human Owner may authorize implementation.
- The likely next implementation candidate, if separately approved, is:
  - Bitget public connectivity skeleton, or
  - Bitget signing helper with mocked tests only.
- No private smoke or runtime wiring is authorized.

## BG2-C follow-up

- A separate BG2-C docs-only runbook may define a future private read-only preflight path.
- Candidate future endpoint for discussion: `GET /api/v3/account/info`.
- BG2-C does not approve implementation, credentials use, real API calls, private smoke, runtime wiring, or any readiness claim beyond docs-ready.

## Not authorized by this document

- Code implementation.
- Test implementation beyond already accepted BG1 config tests.
- Runtime readiness.
- Trading readiness.
- Live readiness.
- Probe readiness.
