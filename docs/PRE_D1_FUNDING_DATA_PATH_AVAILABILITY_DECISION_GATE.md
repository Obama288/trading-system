# Pre-D1 Funding Data Path Availability Decision Gate

## Purpose

This gate resolves the immediate D1 data-path question before any D1
implementation scope.

It follows the independently reviewed D1 cheap-falsification design lock.

It does not authorize downloads, APIs, implementation, processing, artifact
generation, backtesting, or readiness claims.

## Current Setup D / D1 State

- Funding Carry / Funding Stress is advanced-to-hypothesis.
- Setup D hypothesis note exists.
- Pre-D1 decision gate exists.
- D1 cheap-falsification design lock exists and passed review.
- D1 now requires an explicit data-path availability decision before any later
  implementation scope.

## D1 Data Need Under Decision

D1 conceptually requires:

- public funding-rate history;
- aligned OHLCV / market-response observations sufficient for the
  cheap-falsification checks locked in D1;
- no open interest;
- no private exchange data;
- no account, order, position, or private endpoint data.

## Repo-Grounded Inspection Result

Bounded repo inspection searched for committed artifacts that might plausibly
satisfy D1 data needs across:

- `research/signal_observation/`
- `research/`
- `docs/`
- `tests/`

Inspection found committed OHLCV CSV artifacts and Setup C reports/diagnostics
that mention funding stress, funding assumptions, or fixed funding scenarios.
Examples include Setup C report fields such as `funding_rate_per_8h`,
`funding_scenario`, `funding_stress`, and
`funding_adjusted_expanded_vt_post_cost_moderate_high_cost`.

No committed repo artifact was found that appears sufficient to provide
reusable D1-ready public funding-rate history aligned with OHLCV for the
intended cheap-falsification step.

Funding references, reports, diagnostics, and synthetic funding-stress
assumptions are not equivalent to reusable D1 input data.

Therefore the next likely step would be a separate bounded public data-path /
acquisition design lock, subject to owner decision.

## Gate Outcomes

1. `PROCEED_TO_D1_EXISTING_DATA_USE_SCOPE`

   Suitable committed public funding/OHLCV data exists strongly enough to
   justify a later bounded scope proposing D1 use of existing artifacts.
   This does not authorize D1 implementation by itself.

2. `PROCEED_TO_D1_PUBLIC_DATA_ACQUISITION_DESIGN`

   No suitable committed D1-ready funding/OHLCV data exists.
   A later bounded design lock may propose public data source/acquisition
   requirements.
   No download or API call is authorized by this gate itself.

3. `HOLD_FOR_D1_DATA_SOURCE_CLARIFICATION`

   Repo inspection is insufficient or ambiguous.
   A narrower source/window/data-shape clarification is needed before choosing
   existing-data use or acquisition design.

## Decision Rule

Choose `PROCEED_TO_D1_EXISTING_DATA_USE_SCOPE` only if committed repo artifacts
plausibly satisfy the D1 data need without silently substituting reports or
synthetic diagnostics for real funding history.

Choose `PROCEED_TO_D1_PUBLIC_DATA_ACQUISITION_DESIGN` if no such committed
artifacts exist.

Choose `HOLD_FOR_D1_DATA_SOURCE_CLARIFICATION` if the inspection result cannot
support either route honestly.

## Recommended Gate Outcome

Recommended outcome:

`PROCEED_TO_D1_PUBLIC_DATA_ACQUISITION_DESIGN`

Reason:

Committed OHLCV data exists, and committed reports contain funding-stress
diagnostics, but no committed reusable D1-ready public funding-rate history
aligned with OHLCV was found.

## What Each Outcome Unlocks

- Existing-data route:
  future owner decision on a bounded D1 existing-data use scope.
- Acquisition-design route:
  future owner decision on a bounded public funding-data acquisition design
  lock.
- Hold route:
  narrower source clarification only.

## Non-Authorization Boundaries

- No data downloads.
- No API/network calls.
- No endpoint probing.
- No funding data substitution.
- No D1 implementation.
- No data processing.
- No artifact generation.
- No backtesting.
- No Setup D promotion.
- No paper/runtime/trading/probe/live readiness claims.

## Stop Rules

- Stop if a report/diagnostic is being treated as reusable funding input data
  without underlying history artifacts.
- Stop if data-path selection requires private endpoints, secrets, or account
  data.
- Stop if the proposed next step jumps directly to implementation without
  resolving data path.
- Stop if the gate tries to pick thresholds, windows, symbols, or venues that
  belong to a later data/acquisition design step unless repo evidence makes a
  purely availability classification impossible without mentioning the
  limitation.

## Review Requirement

Independent review is required before the owner acts on this gate.

Human Owner decides which gate outcome to accept.

No later D1 data-path/acquisition/implementation scope opens from this document
alone without owner approval.

## What This Does Not Authorize

- no download;
- no API/network;
- no implementation;
- no processing;
- no artifacts;
- no backtest;
- no readiness promotion.
