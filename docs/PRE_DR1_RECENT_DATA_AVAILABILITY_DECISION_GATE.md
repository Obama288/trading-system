# Pre-DR1 Recent-Data Availability Decision Gate

## Current State

- Setup C = PASS_CANDIDATE research-only.
- DR1 = INCONCLUSIVE due failed freshness eligibility.
- Missing recent-data requirement is locked.
- Paper-candidate design lock remains closed.

## Decision Question

Is there a clearly approved path to obtain or assemble a recent 4H candle window that satisfies the locked DR1 freshness requirement?

## Decision Unlocked

This gate determines whether the next step should be:

- a concrete recent-data acquisition design lock;
- parking/deferment of Setup C until eligible recent data exists;
- or a missing-source clarification before either.

## Outcome Map

- AVAILABLE:
  A viable approved source/path exists for a window that can meet the locked recent-data requirement.
  Next step: recent-data acquisition design lock.
- UNAVAILABLE:
  No acceptable source/path is currently identified.
  Next step: park/defer Setup C freshness reopening; do not design acquisition.
- INCONCLUSIVE:
  A possible path exists but source, venue, window, or contiguity feasibility is not sufficiently defined.
  Next step: clarify the missing source/window requirement; no acquisition design lock yet.

## Candidate Source / Path Questions

Decision questions only; no implementation is authorized here.

- Can an approved public source provide the required contiguous 4H recent window?
- Should the future acquisition path target Bitget, Binance, or another explicitly owner-approved venue?
- Can the source/window satisfy:
  - at least 6 contiguous months;
  - end no earlier than 30 calendar days before the future rerun;
  - no gap larger than one expected 4H step?
- Can the exact source, venue, and window be locked before download?

## Stop Rule

If this gate cannot produce different actions under AVAILABLE / UNAVAILABLE / INCONCLUSIVE, do not proceed to acquisition planning.

## What This Does Not Authorize

- data download
- network calls
- DR1 rerun
- paper-candidate design lock
- paper trading
- runtime wiring
- private API
- exchange operations
- readiness claims
