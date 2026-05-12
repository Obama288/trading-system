# Setup D Hypothesis - Funding Carry / Funding Stress

## Purpose

This note formalizes the market-mechanism hypothesis for a triaged research
candidate before any Pre-Cn decision gate, design lock, data work, or
implementation.

It is a hypothesis note only. It is meant to make the candidate falsifiable
early, before the project spends heavier effort on setup design, data
acquisition, or backtesting.

## Candidate Status

- Candidate: Funding Carry / Funding Stress
- Signal family: Carry / funding
- Backlog status: advanced-to-hypothesis
- Research status: hypothesis note only; no setup opened yet

## Core Hypothesis

Perpetual funding is a contractual transfer between long and short sides.
Persistent or extreme positive funding may reflect crowded leveraged long
demand rather than a harmless settlement detail.

That condition may support at least two related but distinct research
possibilities:

1. Carry-related pressure / compensation effect:
   short-side participants may receive funding as compensation for taking the
   other side of crowded long demand, but must bear adverse trend risk.
2. Stress / reversal or deleveraging vulnerability:
   crowded long exposure may become vulnerable to unwind behavior after
   funding reaches persistent or extreme positive states.

This note does not assume both effects exist. It also does not collapse carry
and stress into one unexamined thesis. Each possibility must be weakened or
supported by evidence before any setup path is justified.

## Mechanism

The candidate imbalance is created by leveraged participants willing to pay
positive funding to maintain long perpetual exposure. If that demand is
persistent or extreme, the funding rate may encode positioning pressure:
participants are not only agreeing on a price path, they are paying a repeated
contractual cost to keep exposure open.

The imbalance may persist long enough to be measurable when directional demand,
leverage constraints, benchmark chasing, hedging needs, or behavioral momentum
keep traders in crowded exposure despite recurring funding payments.

Funding may therefore carry information beyond price alone. It can be a direct
economic transfer and a possible marker of which side is crowded, which side is
being compensated, and when exposure may be vulnerable to unwind.

## Forced or Predictable Behavior

The hypothesis depends on plausible constrained behavior, not guaranteed
outcomes:

- long-side funding payers may continue holding crowded exposure because
  exiting would abandon the directional thesis or crystallize losses;
- shorts may receive funding but still face adverse trend risk while crowded
  long demand persists;
- crowded positions may become more fragile when funding is extreme, because a
  reversal, volatility shock, or margin pressure can push late longs to reduce
  exposure.

These behaviors are candidate mechanisms. They are not proven facts and must be
tested before any setup design work.

## Potential Payer / Counterparty

Candidate payers include:

- leveraged long-side demand paying funding to maintain exposure;
- crowded directional participants exposed to adverse unwind;
- traders entering late into already crowded directional pressure.

The payer is not verified by this note. The point of the hypothesis is that
funding provides a plausible place to look for who may be paying for the edge
and why the edge might persist.

## Data Needed

Evidence categories that may later be needed:

- funding-rate history;
- OHLCV aligned to funding intervals or suitable event windows;
- optional later feasibility question: open-interest history, only if justified
  after the first cheap falsification step.

Open interest is not required to write this hypothesis note. This note does
not authorize data acquisition, API probing, network calls, or dataset changes.

## Prior Support / Plausibility

Funding is an economically real transfer, so the carry side is not a purely
price-derived artifact. Positive funding means one side is paying another side
under the perpetual contract mechanics.

Funding extremes are plausibly related to crowded positioning because recurring
positive payments can indicate sustained long-side demand for leverage. That
does not prove a tradable edge. It only makes the candidate mechanism concrete
enough to deserve cheap falsification.

Whether funding states produce a robust post-cost directional, carry-related,
or stress-related edge is not established by this note.

## Main Failure Modes

- Funding extremes may mostly confirm trend continuation rather than forecast
  unwind.
- Funding payments may be too small or too infrequent versus adverse price
  moves, fees, spread, slippage, and funding timing risk.
- Apparent effects may be regime-specific, symbol-specific, venue-specific, or
  concentrated in a small number of historical stress episodes.
- Realized edge may disappear after realistic costs and execution constraints.
- Funding stress may be descriptive rather than predictive.
- Positive funding may identify crowded demand but not provide useful timing.
- Carry and stress effects may conflict, leaving no coherent first setup path.

## First Cheap Falsification

The first cheap falsification should be a pre-backtest reconnaissance question,
not a strategy test:

After materially positive funding states or positive funding extremes, do
simple forward return, reversal/stress proxy, or funding-normalization
observations show a stable directional or carry-related skew worth
formalizing?

Or is the relation weak, inconsistent, regime-bound, or economically trivial?

This first check should stay intentionally bounded. It should not lock exact
thresholds, instruments, windows, venues, or implementation rules yet. Those
belong later only if the hypothesis survives enough to justify a formal
decision gate.

## Decision Unlocked

If the effect is directionally or economically weak, incoherent, or clearly
dominated by costs and noise, Setup D should be parked or rejected before any
expensive design-lock cycle.

If the effect shows a coherent and non-trivial mechanism-consistent signal, the
next step may become a Pre-D1 Decision Gate to decide whether a tightly scoped
reconnaissance or design-lock path is justified.

This note does not directly authorize Pre-D1. It only defines what a cheap
falsification would need to clarify before Pre-D1 could become justifiable.

## What This Hypothesis Note Does Not Authorize

- Setup D design lock
- Pre-D1 gate creation in this task
- data downloads
- API/network calls
- implementation
- backtesting
- paper/runtime/trading/probe/live readiness claims
