# Stage 54-SQ-E1 Alternative Held-Out Source / Window Decision

## Purpose

This document evaluates whether a non-overlapping held-out source/window path
exists that could eventually support the locked E1 reversal design without
violating anti-contamination rules.

It does not authorize retrieval, implementation, source pivot, interval pivot,
design-lock revision, or formal validation.

## Current Blocker

Accepted E1 branch:

`Post-Liquidation Exhaustion Reversal`

The E1 design lock passed independent review.

The Coinalyze 20-symbol 4h EXPLORE consumed the full currently available
contiguous 4h window:
`2025-09-06T00:00:00Z` to `2026-05-15T12:00:00Z`.

Therefore immediate formal E1 implementation on the selected Coinalyze 4h path
is blocked by held-out-window unavailability.

Post-hoc internal splitting of the already inspected Explore window is
rejected.

## Decision Question

Is there an alternative held-out source/window path sufficiently plausible to
justify a bounded next step, or should Setup E remain waiting/parked?

## Candidate Paths To Evaluate

### Path A - The Graph / Hyperliquid Liquidation Event Route

Documentation checked:

- The Graph Hyperliquid market-liquidations endpoint:
  https://thegraph.com/docs/en/token-api/hyperliquid-markets/liquidations/
- Existing Setup E richer-source survey:
  `research/signal_observation/SETUP_E_RICHER_LIQUIDATION_SOURCE_SURVEY.md`

Assessment:

- Machine-readable historical liquidation event rows: plausible. The endpoint
  returns one row per liquidation event with timestamp, coin, liquidation kind,
  direction, notional, fill price, mark price, method, and related fields.
- Time filters / pagination: plausible. The docs expose `start_time`,
  `end_time`, `limit`, and `page`; an empty `data` array marks the end of
  results.
- Asset coverage: plausible for Hyperliquid core perps. The docs describe core
  perp symbols such as `BTC`; BTC/ETH/SOL or comparable core perps require a
  later market-lookup/access check.
- Access blocker: unresolved. Requests require a bearer token and limits are
  plan restricted.
- Historical depth: not documented enough to rely on yet. The route is credible
  enough for a narrow access/depth check, but not enough for direct E1 use.

Criteria:

- Non-overlapping held-out runway plausibility: Medium, pending depth check.
- Preservation of liquidation-direction structure: High.
- Preservation of short-horizon reversal question: High.
- Ability to support matched-volatility baseline: Medium, likely needs matched
  OHLCV/candle availability in the same untouched window.
- Long/short sub-hypothesis separation: High, via liquidation direction/kind.
- Access friction: Medium, bearer token and plan limits unresolved.
- New owner-approved source-selection or design revision required: Yes before
  any source pivot; a narrow access/depth check may precede that decision.

### Path B - Hyperliquid Official Historical Raw Data Route

Documentation checked:

- Hyperliquid historical data docs:
  https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
- Existing Setup E richer-source survey:
  `research/signal_observation/SETUP_E_RICHER_LIQUIDATION_SOURCE_SURVEY.md`

Assessment:

- Official archives plausibly contain raw information that may support
  liquidation reconstruction through fills/node data, but the official route is
  not a ready liquidation-history table.
- This is a reconstruction/data-engineering path, not a low-friction historical
  liquidation endpoint.
- Requester-pays transfer, S3 archive handling, possible missing data, monthly
  update cadence, and reconstruction complexity make it unsuitable as the next
  cheap research step.

Criteria:

- Non-overlapping held-out runway plausibility: Medium, but costly to verify.
- Preservation of liquidation-direction structure: Medium, likely
  reconstructable but not ready-made.
- Preservation of short-horizon reversal question: Medium.
- Ability to support matched-volatility baseline: Medium.
- Long/short sub-hypothesis separation: Medium, reconstruction dependent.
- Access friction: High.
- New owner-approved source-selection or design revision required: Yes.

### Path C - Coinalyze Interval / Source Revision Route

Assessment:

- A different Coinalyze interval or untouched historical range could
  theoretically provide a non-overlapping held-out runway, especially if a
  coarser interval has deeper retention.
- This cannot be treated as a quiet continuation of the accepted E1 path. The
  accepted lock is built around the selected Coinalyze 4h path and requires
  out-of-window validation relative to the explored 4h range.
- Any interval/source revision would need an explicit owner-approved
  source/interval redesign and likely design-lock impact review before it could
  support E1.

Criteria:

- Non-overlapping held-out runway plausibility: Medium, but design-impact
  dependent.
- Preservation of liquidation-direction structure: High if Coinalyze
  directional fields remain available.
- Preservation of short-horizon reversal question: Medium, interval changes may
  weaken short-horizon alignment.
- Ability to support matched-volatility baseline: Medium.
- Long/short sub-hypothesis separation: High if directional fields remain.
- Access friction: Medium, still credential/API dependent.
- New owner-approved source-selection or design revision required: Yes.

## Decision Outcomes

1. `PROCEED_TO_NARROW_ALTERNATIVE_SOURCE_ACCESS_DEPTH_CHECK`
   - A specific alternative path is promising enough to justify one more
     bounded access/depth verification step before any implementation.

2. `PROCEED_TO_REVISED_SOURCE_OR_INTERVAL_SELECTION_DECISION`
   - An alternative may exist, but adopting it would clearly require a separate
     owner-approved source/interval redesign before it can support E1.

3. `NO_ACCEPTABLE_ALTERNATIVE_PATH_IDENTIFIED`
   - No path is promising enough right now; Setup E should return to wait/park
     decision rather than spending more cycles.

## Recommended Decision

`PROCEED_TO_NARROW_ALTERNATIVE_SOURCE_ACCESS_DEPTH_CHECK`

Recommended route:

`The Graph / Hyperliquid liquidation event path`

Reason:

- It is the most plausible candidate for a genuinely new, non-overlapping
  held-out source/window.
- It stays closer to the liquidation mechanism than raw archive reconstruction.
- It avoids a quiet Coinalyze interval pivot.
- Documentation supports event rows, direction/kind fields, time filters, and
  pagination, while leaving access and historical depth unresolved.

This recommendation does not mean The Graph / Hyperliquid is accepted as the E1
source. It only means the path is strong enough to justify a narrow
access/depth verification note.

## What A Later Narrow Access/Depth Check Would Need To Prove

A later docs-only or bounded verification step must confirm:

- free or acceptable access conditions;
- historical depth;
- supported assets;
- whether the untouched historical window is genuinely non-overlapping with the
  already explored Coinalyze range;
- whether the path can support the locked E1 reversal logic without needing a
  hidden redesign.

It should also confirm whether matched OHLCV/candle data can be aligned inside
the same untouched window for the mandatory volatility baseline.

## What This Does Not Authorize

- no retrieval;
- no API market-data calls;
- no implementation;
- no source pivot;
- no interval pivot;
- no design-lock revision;
- no post-hoc split;
- no formal validation;
- no evidence claim;
- no readiness promotion.

## Next Allowed Step

Because the outcome is
`PROCEED_TO_NARROW_ALTERNATIVE_SOURCE_ACCESS_DEPTH_CHECK`, a bounded
access/depth verification note for The Graph / Hyperliquid liquidation event
path may be prepared.
