# Setup E Coinalyze EXPLORE Source Selection

## Purpose

This note decides whether and how a bounded non-evidence Setup E EXPLORE should
use the Coinalyze liquidation-history API as the next richer-source step.

It does not authorize retrieval, API calls, EXPLORE execution, implementation,
or any formal Setup E promotion.

## Current Setup E State

- Setup E hypothesis note exists.
- BTC daily coarse EXPLORE completed off-repo with result `EXPLORE_WEAK`.
- Richer-source survey outcome: `RICHER_SOURCE_PATH_FOUND`.
- Strongest candidate richer path: Coinalyze liquidation-history API.
- Current task is source-selection / EXPLORE design only.

## Source Decision

`SELECT_COINALYZE_FOR_BOUNDED_SETUP_E_EXPLORE_DESIGN`

Coinalyze is recommended for the next bounded source path because it provides:

- a multi-asset path;
- directional long/short liquidation history;
- machine-readable API output;
- a free API-key path rather than a paid subscription decision;
- better mechanism fit than BTC-only daily liquidation aggregates.

## Owner-Aware API-Key Boundary

Later retrieval would require explicit owner approval to use a free Coinalyze
API key.

This note does not authorize creating, storing, or using credentials. No secret
handling is opened in this task.

## Proposed Explore Universe

Initial bounded universe rule:

- use up to 20 supported Coinalyze perpetual/futures symbols if available;
- prefer the most liquid broadly relevant perpetual markets supported by
  Coinalyze;
- include BTC, ETH, and SOL if supported, but do not make them the whole
  universe;
- do not silently substitute unrelated or illiquid instruments merely to fill a
  quota.

Reason for revision:

- the project learned that 3-symbol research is too narrow for family-level
  assessment;
- Coinalyze was selected partly because it offers a broader multi-asset path;
- a richer Setup E EXPLORE should use that advantage rather than repeating the
  earlier narrow-universe limitation.

The exact final asset list is not locked by this note. The later retrieval task
must resolve the actual supported Coinalyze symbol identifiers and report the
final selected universe.

## Proposed Interval Decision

`4h`

Reason:

- richer than daily and better aligned with liquidation stress than daily
  aggregates;
- less starved than very short intraday intervals given Coinalyze retention
  constraints;
- still only an exploratory compromise, not proof of ideal mechanism
  alignment.

The later retrieval task must verify actual available 4h historical coverage
before proceeding.

If 4h availability is materially too short or unsuitable, STOP and report
rather than silently switching intervals.

## Proposed Explore Window

Do not pre-invent an exact calendar window before retention is verified.

Locked window rule:

- use the full contiguous 4h history actually available from Coinalyze at
  retrieval time, bounded only by what the API legitimately exposes;
- report the exact window used;
- do not silently mix intervals or backfill with another source.

## Proposed Future EXPLORE Question

At a coarse pre-validation level, the later EXPLORE should ask:

After unusually large long- or short-liquidation 4h intervals across the
bounded supported liquid-perpetual universe, do forward returns over fixed
short horizons show:

- continuation-like behavior;
- reversal-like behavior;
- mixed structure;
- weak/no structure?

This note does not lock exact thresholds or horizons. Those may be fixed in the
later EXPLORE implementation prompt.

## Interpretation Limits

Any later Coinalyze EXPLORE:

- remains non-evidence and non-validation;
- cannot prove or disprove Setup E;
- cannot establish live tradability;
- cannot substitute for formal held-out validation;
- may still be limited by interval/history retention and source construction.

## Decision Outcome

`PROCEED_TO_SETUP_E_COINALYZE_EXPLORE_AUTHORIZATION`

## What This Does Not Authorize

- no API calls
- no credential creation or use
- no data retrieval
- no EXPLORE run
- no implementation
- no formal Setup E gate
- no readiness promotion
- no use of paid vendors

## Next Allowed Step

A bounded off-repo Setup E Coinalyze EXPLORE authorization may be prepared,
subject to owner approval.
