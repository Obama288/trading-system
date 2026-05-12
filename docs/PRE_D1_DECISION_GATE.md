# Pre-D1 Decision Gate - Funding Carry / Funding Stress Cheap Falsification

## Purpose

This gate decides whether a bounded D1 cheap-falsification reconnaissance stage
is justified before any D1 design lock, data acquisition, implementation, or
backtest.

## Current State

- Setup C is parked from active progression.
- Funding Carry / Funding Stress is the advanced-to-hypothesis candidate.
- `research/signal_observation/SETUP_D_HYPOTHESIS.md` exists and separates:
  1. funding carry / compensation possibility;
  2. funding stress / unwind vulnerability possibility.
- No Setup D stage is open beyond the hypothesis note.
- Research lane remains hypothesis-first and cheap-falsification-first.

## Diagnostic Question

Can a bounded first D1 reconnaissance check, based on funding-state
observations plus aligned market response observations, materially weaken or
support the Setup D mechanism before expensive setup work?

## Why This Gate Exists

The project now prioritizes research throughput and early falsification. Setup
D should not jump from hypothesis note to expensive design work.

This gate confirms whether D1 would unlock a decision that cannot already be
made from the hypothesis note alone.

## Decision Unlocked

D1, if authorized later through its own design lock, would decide whether Setup
D should:

- proceed toward a tighter formal research path;
- be refined because carry vs stress is still insufficiently separated;
- or be parked/rejected before expensive work.

## Outcome Map

- PROCEED_TO_D1_DESIGN_LOCK:
  The D1 cheap-falsification question is bounded, mechanism-consistent, and
  capable of supporting/refuting at least one of the two Setup D branches
  enough to justify a formal D1 design lock.
- HOLD_REFINE_HYPOTHESIS:
  The D1 question is still too broad, or carry and stress remain insufficiently
  separated for a useful cheap falsification. Refine the hypothesis before
  opening D1.
- PARK_OR_REJECT_BEFORE_D1:
  The proposed cheap falsification would not unlock a meaningful next decision,
  or the mechanism is too incoherent to justify further Setup D work now.

## Candidate D1 Questions

Candidate questions only; not implementation and not locked thresholds:

- After materially positive funding states or funding extremes, is there a
  stable forward-return skew consistent with carry-related compensation or
  continuation pressure?
- After extreme positive funding states, is there a stable reversal / stress /
  unwind proxy signal that is distinct from the carry interpretation?
- Do funding states normalize in a way that provides any mechanism-consistent
  observational value beyond price-only behavior?
- Are the carry and stress branches empirically distinguishable enough to avoid
  collapsing into one vague "funding effect"?

D1 candidate questions do not lock exact venues, symbols, time windows,
thresholds, statistics, or implementation details.

## Stop Rule

If D1 cannot plausibly produce different decisions under
PROCEED_TO_D1_DESIGN_LOCK / HOLD_REFINE_HYPOTHESIS /
PARK_OR_REJECT_BEFORE_D1, do not open D1.

## What This Does Not Authorize

- No D1 design lock in this task.
- No data downloads.
- No API/network calls.
- No implementation.
- No backtest.
- No Setup D setup opening beyond the hypothesis note.
- No paper/runtime/trading/probe/live readiness claims.
