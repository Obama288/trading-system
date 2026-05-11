# Pre-DR1 Decision Gate - Data Recency / Predictability Reconnaissance

## Purpose

Define whether DR1 is justified before any Data Reconnaissance design lock or
implementation.

## Current State

- Setup C is PASS_CANDIDATE research-only.
- Paper-prerequisites proposal accepted.
- C7 Bitget/Binance PASS.
- C8 closed; no C8b.
- Escalation remains HOLD.

## Diagnostic Question

Does a Data Recency / Predictability Reconnaissance stage unlock a decision
that cannot be made from current Setup C evidence?

## Decision Unlocked

DR1 would decide whether Setup C can proceed toward a future paper-candidate
design lock discussion, or whether Setup C should be parked / require
structural review due stale or insufficient predictability evidence.

## Outcome Map

- HIGH / supportive evidence:
  Proceed to Data Reconnaissance design lock, then if passed,
  paper-candidate design lock may be considered.
- LOW / weak evidence:
  Park Setup C or trigger structural review before any paper-candidate design
  lock.
- INCONCLUSIVE:
  Define the missing data requirement; do not proceed to paper-candidate
  design lock.

## Candidate DR1 Questions

Candidate questions only; not implementation:

- Is there enough recent data after the current evidence windows to test
  freshness?
- Does Setup C retain directional predictability on recent / out-of-window
  data?
- Are non-overlapping return autocorrelation / variance-ratio / lead-lag tests
  supportive of the signal family?

## Stop Rule

If DR1 cannot produce different decisions under HIGH / LOW / INCONCLUSIVE, do
not run DR1.

## What This Does Not Authorize

- No paper trading.
- No paper-candidate approval.
- No runtime wiring.
- No private API.
- No exchange operations.
- No new downloads.
- No code.
- No readiness claims.
