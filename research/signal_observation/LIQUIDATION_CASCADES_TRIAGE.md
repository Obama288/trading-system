# Liquidation Cascades Triage

## Purpose

This is a candidate triage note only.

It decides whether the candidate deserves advancement to a mechanism-first
hypothesis note or should stay on watchlist / be rejected for now.

## Candidate

- Candidate:
  Liquidation Cascades
- Signal family:
  Forced deleveraging / liquidation
- One-line mechanism:
  Large forced liquidations may create short-lived directional continuation
  or overshoot because positions are closed mechanically rather than
  discretionarily.

## Triage Questions

1. Mechanism clarity:
   Pass. Forced liquidations are mechanical flows rather than discretionary
   entries or exits, so the candidate has a clear imbalance mechanism.

2. Counterparty clarity:
   Pass. Candidate payers are overleveraged traders being forcibly liquidated;
   counterparties are liquidity takers and liquidity providers absorbing
   one-sided forced flow.

3. Data feasibility:
   Pass with note. Public liquidation history or liquidation intensity proxies
   may exist, but source quality, coverage, and historical accessibility require
   later feasibility or EXPLORE confirmation.

4. Cheap falsifiability:
   Pass. An EXPLORE-style crude check could inspect whether liquidation clusters
   show short-horizon continuation, overshoot, or reversal structure.

5. Distinctness:
   Pass. This is not TSMOM, not price-action continuation, and not funding
   carry; the signal family is forced deleveraging / liquidation.

6. Expected edge above cost floor:
   Pass as plausible, not proven. Forced-flow effects could be sharp enough to
   matter, but this requires empirical falsification before any setup path is
   justified.

## Triage Result

Advance to hypothesis note

## Why

Liquidation Cascades is mechanistic, distinct from prior exhausted families,
and cheaply falsifiable enough to deserve a mechanism-first hypothesis note.
Data feasibility remains a later verification issue and is not resolved by this
triage note.

## What This Does Not Authorize

- no EXPLORE run;
- no data download;
- no network/API work;
- no hypothesis implementation;
- no design lock;
- no formal Setup E or stage label yet;
- no readiness claims.

## Next Allowed Step

A mechanism-first hypothesis note for Liquidation Cascades may be prepared,
subject to owner/Tower Control approval.
