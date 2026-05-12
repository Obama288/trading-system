# Stage 54-SQ DR1 Missing Recent-Data Requirement Design Lock

## Purpose

- Define the exact recent-data requirement needed to resolve DR1 freshness eligibility.
- This does not reopen DR1 implementation yet.
- This does not authorize a paper-candidate design lock.

## Current Problem

- DR1 freshness requirement is locked: at least 6 contiguous months of candles ending no earlier than 30 calendar days before the DR1 implementation date.
- Existing committed Bitget recent window failed contiguity due max gap = 8h.
- Therefore DR1 result is INCONCLUSIVE.

## Required Future Data Condition

Any future attempt to reopen DR1 freshness eligibility must have:

- 4H candles;
- at least 6 contiguous months;
- a window ending no earlier than 30 calendar days before the future DR1 rerun date;
- no candle gap larger than one expected 4H step;
- exact start/end timestamps documented before rerun;
- source/venue documented before rerun;
- no post-result window adjustment.

## Scope Decision

- DR1 freshness may be reopened only with an explicitly approved recent-data window documented in advance.
- Venue/source choice must be owner-approved in a later owner-approved data-acquisition decision gate before any download or rerun.
- This design lock does not choose Bitget-only, Binance-only, or any substitute venue/window by itself.

## Allowed Next Step After This Design Lock

- Independent review of this design lock.
- If accepted, next task may be a concrete recent-data acquisition / availability decision gate.
- No data download is authorized by this document.

## What This Does Not Authorize

- new data download
- data substitution
- DR1 rerun
- paper-candidate design lock
- paper trading
- runtime wiring
- private API
- exchange operations
- readiness claims
