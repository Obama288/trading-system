# Stage 54-SQ-E1 Held-Out Window Availability Decision

## Purpose

This document records the held-out-window availability blocker discovered after
the E1 reversal cheap-falsification design lock passed review.

It decides which path should be considered next without violating the accepted
E1 design lock.

It does not authorize data retrieval, implementation, source pivot, interval
pivot, formal validation, or readiness claims.

## Current Accepted State

Setup E has advanced through:

- hypothesis note;
- BTC daily coarse EXPLORE `EXPLORE_WEAK`;
- richer-source survey;
- Coinalyze 20-symbol 4h EXPLORE `EXPLORE_MIXED`;
- Pre-E1 decision gate;
- E1 reversal cheap-falsification design lock;
- independent review of the design lock: PASS WITH NOTES.

The locked E1 branch is:

`Post-Liquidation Exhaustion Reversal`

The E1 lock requires:

- held-out-window validation;
- no reuse of the explored Coinalyze window as validation evidence;
- no new validation data access before reviewed design;
- no further tuning on the explored Coinalyze window.

## Newly Identified Blocker

The prior Coinalyze EXPLORE used the full contiguous currently available 4h
historical window at the time of retrieval:
`2025-09-06T00:00:00Z` to `2026-05-15T12:00:00Z`.

Therefore, under the currently selected Coinalyze 4h path, there is no
immediately available non-overlapping historical held-out window for formal E1
cheap falsification.

Proceeding directly to implementation would risk violating the reviewed design
lock or silently changing the source/interval path.

## Why Post-Hoc Internal Splitting Is Not Acceptable

Splitting the already fully inspected Coinalyze EXPLORE window after the fact
into "discovery" and "validation" would not produce a clean held-out window.

The reversal/exhaustion branch was identified after observing that range.

A post-hoc internal split would undermine the anti-contamination discipline
accepted in the E1 design lock and review.

This option is rejected.

## Decision Question

What path should Hephaestus consider next so that Setup E can proceed, pause,
or park without violating the reviewed E1 lock?

## Decision Options

1. `WAIT_FOR_NEW_COINALYZE_HELD_OUT_WINDOW`
   - Do not proceed to E1 implementation now.
   - Recheck later after enough non-overlapping new 4h Coinalyze history has
     accumulated.
   - Any such path needs a separately defined minimum future window requirement
     before implementation is reopened.

2. `SEARCH_ALTERNATIVE_HELD_OUT_SOURCE_OR_WINDOW_PATH`
   - Open a bounded docs-only source/window decision next.
   - Evaluate whether another source, a different already-uncontaminated
     window, or another explicitly designed path can support the existing E1
     lock or whether a revised owner-approved source-selection step is needed.
   - No direct source pivot is authorized by this decision alone.

3. `PARK_SETUP_E_UNTIL_VALID_HELD_OUT_RUNWAY_EXISTS`
   - Do not spend more immediate effort on E1.
   - Park the candidate until a valid held-out source/window path becomes
     reasonably available.

## Recommended Decision

`SEARCH_ALTERNATIVE_HELD_OUT_SOURCE_OR_WINDOW_PATH`

Setup E is not being held by a signal-quality rejection but by a held-out runway
availability blocker.

Immediate parking would be premature after a reviewed E1 design lock.

Waiting months for Coinalyze 4h accumulation may damage research throughput.

A bounded alternative source/window decision is the cleanest next route before
choosing wait or park.

## What The Next Alternative-Path Decision Must Clarify

Any later docs-only alternative-path decision must answer:

- Is there a non-overlapping held-out source/window path suitable for the locked
  E1 reversal design?
- Does that path preserve the key design assumptions:
  - directional liquidation data;
  - short-horizon structure;
  - matched-volatility baseline feasibility;
  - long/short sub-hypothesis separation?
- Would using it require a new owner-approved source-selection or design
  revision?
- If no acceptable path exists, should Setup E be parked or placed on timed
  wait?

## Process Lesson Recorded

This blocker is exactly why the new Held-Out Window Preservation Requirement
was added to `HOW_WE_WORK.md` and `AGENT_PROMPTS.md`.

Future triage-cleared EXPLORE or pre-formal data inspection must preserve
validation runway or explicitly obtain owner approval for the tradeoff.

## What This Does Not Authorize

- no E1 implementation;
- no data retrieval;
- no API calls;
- no Coinalyze rerun;
- no post-hoc internal held-out split;
- no source pivot;
- no interval pivot;
- no design lock revision;
- no formal validation;
- no evidence claim;
- no readiness promotion.

## Next Allowed Step

A docs-only alternative held-out source/window decision may be prepared,
subject to Human Owner acceptance of the recommended decision.
