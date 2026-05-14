# Setup E Hypothesis - Liquidation Cascades

## Purpose

This note formalizes the market-mechanism hypothesis for a triaged research
candidate before any Pre-E1 gate, design lock, data work, or implementation.

It is a mechanism-first hypothesis note only. It does not authorize data
acquisition, EXPLORE work, implementation, or backtesting.

## Candidate Status

- Candidate: Liquidation Cascades
- Signal family: Forced deleveraging / liquidation
- Backlog status: triage-ready; triage result advance to hypothesis note
- Research status: hypothesis note only; no setup opened yet

## Core Hypothesis

Liquidation clusters represent forced, non-discretionary flow.

Such flow may produce short-horizon continuation, overshoot, or post-cascade
reversal. These possibilities must remain distinct and must not be collapsed
into one vague "liquidations matter" claim.

This note does not assume any of those effects exists. Each possibility must be
weakened or supported by evidence before any setup path is justified.

## Mechanism

Positions are closed mechanically under margin and liquidation rules.

When many leveraged positions are forced out near the same time, order flow may
become one-sided. Thin liquidity, crowded leverage, stop cascades, or reactive
momentum can amplify the move beyond ordinary discretionary trading pressure.

The mechanism is not that liquidations are merely interesting labels on large
price moves. The candidate claim is that forced, mechanical flow may create
observable short-horizon behavior around cascade conditions.

## Forced or Predictable Behavior

The hypothesis depends on plausible constrained behavior, not guaranteed
outcomes:

- liquidated traders are forced out rather than choosing execution timing;
- liquidity takers and providers absorb aggressive forced flow;
- if cascades propagate, directional pressure may persist briefly;
- if forced flow exhausts available imbalance, overshoot or reversal may
  follow.

These behaviors are candidate mechanisms. They are not proven facts and must be
tested before any setup design work.

## Potential Payer / Counterparty

Candidate payers include:

- overleveraged traders being liquidated;
- late momentum entrants around cascade conditions;
- participants transacting into forced-flow dislocations.

The payer is not verified by this note. The point of the hypothesis is that
liquidation pressure provides a plausible place to look for who may be forced
to trade and why a short-lived edge might exist.

## Data Needed

Evidence categories that may later be needed:

- liquidation event history or liquidation intensity proxies;
- OHLCV aligned to event windows;
- optional later feasibility question: open interest, only if justified after
  the first cheap falsification step.

This note does not verify data availability. It does not authorize data
acquisition, API probing, network calls, or dataset changes.

## Prior Support / Plausibility

Forced liquidation is an economically concrete mechanism. It is stronger than
indicator-first pattern hunting because it starts from mechanical market
behavior rather than a price transform alone.

Liquidation clusters plausibly mark moments when one side has lost discretion
over execution. That does not prove a tradable edge. It only makes the
candidate mechanism concrete enough to deserve cheap falsification.

No tradable edge is established by this note.

## Main Failure Modes

- Liquidation data may be incomplete, vendor-specific, or not historically
  accessible.
- Observed moves may be contemporaneous rather than predictive.
- Effects may be too short-lived after costs, spread, slippage, and latency.
- Results may be dominated by a few crisis episodes.
- Continuation and reversal interpretations may conflict.
- Public proxies may be too noisy.

## First Cheap Falsification

The first cheap falsification should be a bounded pre-backtest question, not a
strategy test:

After materially large liquidation clusters, do simple short-horizon
forward-return, continuation/overshoot, or reversal observations show a
coherent skew worth formalizing?

Or is the relation weak, unstable, or contemporaneous only?

This first check should stay intentionally bounded. It should not lock exact
thresholds, instruments, windows, venues, or implementation rules yet. Those
belong later only if the hypothesis survives enough to justify a formal
decision gate.

## Decision Unlocked

If the relation is weak, incoherent, contemporaneous only, or the data path is
implausible, Setup E should be parked or rejected before heavier design work.

If the relation shows a coherent and non-trivial mechanism-consistent signal,
a Pre-E1 Decision Gate may be considered later.

This note does not authorize Pre-E1 by itself.

## What This Hypothesis Note Does Not Authorize

- Setup E design lock
- Pre-E1 gate creation in this task
- EXPLORE run
- data downloads
- API/network calls
- implementation
- backtesting
- readiness claims
