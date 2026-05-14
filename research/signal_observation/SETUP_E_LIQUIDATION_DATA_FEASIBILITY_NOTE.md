# Setup E Liquidation Data Feasibility Note

## Purpose

This note evaluates whether Setup E can honestly proceed to a bounded
non-evidence EXPLORE pass, based on data-source feasibility only.

It is not an EXPLORE run, not data acquisition, not a design lock, and not an
implementation task.

## Current Setup E State

- Liquidation Cascades triage: Advance to hypothesis note
- Setup E hypothesis note exists
- No EXPLORE run authorized or performed yet

## Feasibility Question

Can the project obtain liquidation-cluster history suitable for a quick
EXPLORE pass without fabricating a data path or silently changing the
candidate?

## Candidate Data Paths

1. Official exchange historical liquidation data
   - status: requires verification before EXPLORE authorization

2. Third-party vendor liquidation history
   - status: plausible path, but may require paid/API access and therefore
     needs explicit owner awareness before use

3. Proxy path
   - liquidation intensity proxies derived from other public data
   - status: not equivalent to true liquidation-event history and must not be
     silently substituted without a separate owner-approved decision

## Decision Outcomes

1. `PROCEED_TO_SETUP_E_EXPLORE_SOURCE_SELECTION`
   - a plausible historical liquidation-data path exists strongly enough to
     specify one bounded EXPLORE source next

2. `HOLD_FOR_SOURCE_VERIFICATION`
   - the idea remains promising, but source feasibility is not yet concrete
     enough to authorize an EXPLORE run

3. `PARK_LIQUIDATION_CANDIDATE_FOR_NOW`
   - no acceptable data path is available under current constraints

## Recommended Outcome

`HOLD_FOR_SOURCE_VERIFICATION`

Reason:

- hypothesis quality is sufficient;
- but the project has not yet locked a clear, low-friction historical
  liquidation data source suitable for EXPLORE;
- source clarification should occur before authorizing the off-repo scan.

## What This Does Not Authorize

- no API calls
- no data downloads
- no paid subscription decision
- no proxy substitution
- no EXPLORE run
- no hypothesis promotion
- no design lock
- no implementation
- no readiness claims

## Next Allowed Step

A bounded source-verification decision may compare concrete
liquidation-history source options and recommend whether Setup E EXPLORE can
proceed.
