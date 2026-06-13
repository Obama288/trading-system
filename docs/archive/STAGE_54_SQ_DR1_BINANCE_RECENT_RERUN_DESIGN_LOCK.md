# Stage 54-SQ DR1 Binance Recent Rerun Design Lock

## Purpose

- Define the exact rules for rerunning DR1 using the already committed Binance
  recent 4H window that passed the locked recent-data requirement.
- This design lock authorizes planning only, not rerun implementation.

## Locked Rerun Inputs

- Use only the committed Binance recent 4H data artifacts already validated as
  `DATA_REQUIREMENT_PASS`.
- Symbols: BTCUSDT, ETHUSDT, SOLUSDT.
- Timeframe: 4H.
- Window: 2025-11-12T12:00:00+00:00 to 2026-05-12T12:00:00+00:00.
- No data substitution.
- No window change.
- No symbol/timeframe change.

## Rerun Objective

- Re-evaluate DR1 freshness / predictability reconnaissance now that the
  freshness blocker has been removed at the data layer.
- Determine whether the DR1 result becomes:
  - HIGH
  - LOW
  - INCONCLUSIVE
  under the existing DR1 decision logic.

## Analyses To Rerun

Use the same DR1 analyses and thresholds already locked:

- recent-data freshness eligibility;
- non-overlapping return autocorrelation;
- variance-ratio style predictability check;
- BTC -> ETH/SOL lead-lag check;
- Setup C recent/out-of-window persistence check.

No new analyses.

## Decision Interpretation

- HIGH:
  all required DR1 conditions are supportive under the existing locked rules;
  next step may be a paper-candidate design-lock decision.
- LOW:
  freshness is eligible but one or more substantive DR1 analyses are weak; do
  not open a paper-candidate design lock; return to owner decision on parking
  or structural review.
- INCONCLUSIVE:
  rerun remains underpowered, contradictory, or blocked by a locked
  classification rule; define the remaining blocker; do not open a
  paper-candidate design lock.

## Anti-Cherry-Picking

- No reselecting window after rerun.
- No changing symbols/timeframe.
- No threshold changes.
- No dropping weak analyses.
- No adding post-hoc diagnostics.
- No reclassifying LOW as INCONCLUSIVE to avoid a negative result.

## What This Does Not Authorize

- DR1 rerun now
- new downloads
- network calls
- data mutation
- paper-candidate design lock
- paper trading
- runtime wiring
- private API
- exchange operations
- readiness claims

## Next Step

- Independent review of this rerun design lock.
- If accepted, Codex may receive a bounded DR1 rerun implementation task using
  only the committed Binance recent data.
