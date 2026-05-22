# Stage 54-SQ-E1 Hyperliquid / The Graph Access-Depth Verification

## Purpose

This note verifies whether The Graph / Hyperliquid liquidation event route is
credible enough to remain the preferred alternative held-out source/window
candidate for E1.

It does not authorize retrieval, bearer-token use, source pivot,
implementation, or formal validation.

## Current E1 Blocker

The E1 reversal design lock passed independent review.

Coinalyze 4h EXPLORE consumed the full currently available historical window:
`2025-09-06T00:00:00Z` to `2026-05-15T12:00:00Z`.

A clean immediate held-out window under the selected Coinalyze 4h path is
unavailable.

The alternative held-out path decision recommended checking:

`The Graph / Hyperliquid liquidation event path`

## Verification Questions

### 1. Access

Does the route require a bearer token?

Yes. The endpoint examples require an `Authorization: Bearer YOUR_JWT` header.

Is a free or low-friction access tier documented clearly enough to justify a
later owner decision?

Partially yes. The Graph pricing/docs describe a free tier and paid higher
tiers, but a later owner decision is still required before any token creation
or use.

Are rate/plan restrictions visible enough to assess bounded feasibility?

Partially yes. The Graph pricing/docs expose tiered monthly request limits, but
the exact practical limit for this Hyperliquid historical-depth task still
needs a token-level check.

### 2. Historical Depth

Do docs state, imply, or fail to clarify how far back historical liquidation
events can be paginated?

The docs show time filters and pagination, but do not clearly state the
earliest available historical liquidation timestamp or guaranteed retention
depth for this endpoint.

Is there enough documentary basis to believe a non-overlapping pre-2025-09-06
or otherwise clean held-out window may exist?

There is enough basis to treat the route as plausible because it exposes
historical event pagination and time filtering. There is not enough basis to
confirm that a pre-2025-09-06 or otherwise clean held-out window actually
exists.

If depth is not documented, state that clearly.

Historical depth is not documented clearly enough for E1 use.

### 3. Asset Coverage

Does the route support coin filtering or market-level filtering?

Yes. The documented request parameters include `coin`, and examples show coin
filters such as `BTC`.

Are BTC / ETH / SOL or comparable core perps plausibly available?

BTC is directly plausible from docs/examples. ETH, SOL, or comparable core
perps are plausible for Hyperliquid but not fully verified by the checked
liquidations endpoint docs alone.

If docs do not verify exact coverage, state what remains unresolved.

Exact supported coin coverage for BTC/ETH/SOL and any replacement core perp
universe remains unresolved until a later market/access check.

### 4. Data Fields

Are liquidation direction/kind fields documented?

Yes. The documented response includes `direction` and `liquidation_kind`.

Are timestamp and notional/price fields present?

Yes. The documented response includes timestamp fields plus liquidation value,
fill price, mark price, size, and other event metadata.

Is the field set plausibly adequate for long/short sub-hypothesis separation?

Yes. The documented direction/kind fields are plausibly adequate for separating
long-dominant and short-dominant liquidation events, subject to later schema
confirmation with authorized access.

### 5. Held-Out E1 Fit

Could this path plausibly support the locked E1 reversal question without
silently changing it into a different mechanism?

Yes. The path remains liquidation-event based and directional, so it preserves
the core forced-flow liquidation mechanism more cleanly than raw archive
reconstruction or proxy liquidation maps.

Could matched-volatility OHLCV alignment plausibly be handled later using a
separate public market-price source, or is that unresolved?

Plausibly yes, but unresolved. A later design or token-level check must confirm
that event timestamps can be aligned to a compatible public OHLCV/candle source
inside the same untouched held-out window.

## Sources Checked

- The Graph Hyperliquid market liquidations endpoint:
  https://thegraph.com/docs/en/token-api/hyperliquid-markets/liquidations/
- The Graph pricing / plan information:
  https://thegraph.com/pricing/
- Setup E richer liquidation source survey:
  `research/signal_observation/SETUP_E_RICHER_LIQUIDATION_SOURCE_SURVEY.md`
- E1 alternative held-out source/window decision:
  `docs/STAGE_54_SQ_E1_ALTERNATIVE_HELD_OUT_SOURCE_WINDOW_DECISION.md`

## Findings

### Confirmed

- The route is machine-readable.
- Endpoint examples require bearer-token authorization.
- Request parameters include time filters, pagination, limit, and coin filter.
- The response schema includes event-level liquidation rows.
- Fields include direction/kind, timestamps, liquidation value, size, fill
  price, and mark price.
- The endpoint remains mechanism-aligned with E1 because it concerns
  Hyperliquid liquidation events rather than proxy levels or dashboard views.

### Unresolved

- Earliest available liquidation timestamp / historical depth.
- Whether the accessible free or acceptable tier is sufficient for bounded
  historical-depth verification.
- Exact BTC/ETH/SOL coverage and any acceptable core-perp replacement universe.
- Whether a clean non-overlapping held-out window exists relative to
  `2025-09-06T00:00:00Z` onward.
- Whether matched OHLCV/candle data can be aligned cleanly in the same
  untouched held-out window.

### Negative / Limiting

- The route is not public unauthenticated data; bearer-token use would need
  explicit owner approval.
- Documentation alone does not prove historical depth.
- The endpoint is Hyperliquid-specific, so any later use would be a source path
  change requiring owner-level source/design consideration before E1 use.

## Verification Outcome

`ACCESS_DEPTH_PATH_PLAUSIBLE_REQUIRES_TOKEN_LEVEL_CHECK`

Documentation supports the route conceptually: event-level liquidation rows,
directional structure, time filtering/pagination, and plausible asset fit are
present.

Historical depth and practical access tier are unresolved, so the route cannot
be accepted as an E1 held-out source yet.

## Recommended Decision

`ACCESS_DEPTH_PATH_PLAUSIBLE_REQUIRES_TOKEN_LEVEL_CHECK`

This is recommended because the documentation genuinely supports:

- event-level liquidation rows;
- directional structure;
- time filtering/pagination;
- plausible asset fit;

while leaving historical depth and actual access tier unresolved.

## What A Later Token-Level Check Would Need To Confirm

A later owner-approved bounded token-level check must verify:

- free or acceptable access tier actually works;
- historical depth and earliest available liquidation timestamps;
- BTC/ETH/SOL or core perp coverage;
- whether a non-overlapping held-out window exists relative to
  `2025-09-06T00:00:00Z` onward;
- whether pagination and field coverage are sufficient for the locked E1 logic.

It must not inspect candidate results or forward returns.

## What This Does Not Authorize

- no bearer-token acquisition or use;
- no event retrieval;
- no market-data extraction;
- no source pivot;
- no implementation;
- no E1 run;
- no formal validation;
- no design-lock revision;
- no evidence or readiness claim.

## Next Allowed Step

Because the outcome is `ACCESS_DEPTH_PATH_PLAUSIBLE_REQUIRES_TOKEN_LEVEL_CHECK`,
a bounded owner decision on whether to perform a token-level access/depth check
may be prepared.

## Token-Level Check Result

A bounded token-level access-depth check was owner-authorized and executed.

### Execution Summary

- Credential type: JWT from thegraph.market (dfuse.io issuer) — correct format
  for The Graph Token API.
- Plan tier encoded in token: FREE.
- Allowed endpoint group encoded in token: nft only.
- Hyperliquid markets/liquidations endpoint: NOT accessible on FREE / nft plan.
- HTTP response on all queries (BTC recent, ETH, SOL, BTC 2023 window,
  pre-2025-09-06 window): `401 Unauthorized` —
  `{"error":{"status":401,"code":"unauthorized"}}`.
- Service status: endpoint is live (structured JSON error returned, not 404).
- No records retrieved; no candidate-relevant data inspected; no contamination
  risk introduced.

### Revised Outcome

`ACCESS_BLOCKED_PLAN_RESTRICTION`

The endpoint exists, the JWT format is correct, and the service is live. The
FREE plan restricted to nft endpoint group does not permit access to Hyperliquid
markets/liquidations. Historical depth, BTC/ETH/SOL coverage, and held-out
window existence remain unconfirmed.

### Path Forward

To complete the access-depth check, the owner must upgrade the thegraph.market
account to a plan that includes Hyperliquid / DeFi / markets endpoint access,
then re-enter the bounded check with a new JWT.

Alternatively, a Research Scout may be authorized to identify other candidate
liquidation data source paths for E1, subject to separate owner decision.

### What This Does Not Authorize

- no E1 implementation;
- no source pivot without a new owner-level source/design decision;
- no design-lock revision;
- no evidence or readiness claim.
