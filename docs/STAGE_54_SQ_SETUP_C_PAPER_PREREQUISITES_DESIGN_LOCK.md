# Stage 54-SQ Setup C Paper-Prerequisites Design Lock

## Purpose

- Define what must be true before Setup C can be considered for a future
  paper-candidate discussion.
- This document defines prerequisites only.
- It does not approve paper trading.
- It does not authorize runtime wiring, private API access, probes, exchange
  operations, trading, or live readiness.

## Current Evidence Summary

- Setup C / TSMOM is PASS_CANDIDATE research-only.
- C7 Bitget PASS.
- C7 Binance PASS.
- C8 closed as observational inconclusive due material missing alignment
  coverage.
- C8 does not weaken C7 PASS, but does not explain Binance magnitude
  divergence.
- C8b is not authorized.

## Non-Readiness Statement

- Paper readiness: NO.
- Runtime readiness: NO.
- Trading readiness: NO.
- Probe readiness: NO.
- Live readiness: NO-GO.

## Paper-Prerequisites Definition

These prerequisites define what would have to be satisfied before any future
paper-candidate proposal. They do not approve paper trading or implementation.

### A. Evidence Prerequisites

- C7 Bitget and Binance PASS remain accepted.
- C8 caveat is recorded and not treated as a gate failure.
- No unresolved blocker contradicts the C7 gate evidence.
- No new same-dataset diagnostics are required unless the owner opens a new
  decision gate.

### B. Risk / Execution Realism Prerequisites

Before paper-candidate discussion, define but do not implement:

- Slippage model requirement.
- Liquidity / spread assumptions.
- Fees / funding assumptions.
- Minimum trade frequency / turnover expectations.
- Max drawdown / loss-limit paper constraints.
- Kill-switch interaction requirements.
- Fail-closed behavior expectations.
- Monitoring / alerting expectations.

### C. Runtime Architecture Prerequisites

Before paper-candidate implementation, require:

- No direct exchange write calls from research code.
- Paper environment isolation.
- Deterministic signal export contract.
- Risk engine remains authoritative.
- Kill switch remains highest authority.
- Execution service remains non-live unless separately authorized.
- Journal/audit trail required.

### D. Data Prerequisites

- Additional recent data is not required before creating the docs-only
  paper-prerequisites proposal. However, any future paper-candidate proposal
  must define a separate data-recency requirement before implementation can be
  discussed.
- If additional recent data is required, specify it as a future design-lock
  item, not implementation here.
- Do not require another arbitrary Cn diagnostic without a decision gate.

### E. Review Prerequisites

- Independent review of any paper-prerequisites proposal.
- Owner explicit approval before any paper implementation design.
- No automatic promotion from research PASS_CANDIDATE to paper candidate.

## Decision Gate Rule Before New Diagnostics

Before any new diagnostic stage is opened, create a short Pre-Cn Decision Gate:

- Question this diagnostic answers.
- Decision it unlocks.
- If HIGH: what decision follows.
- If LOW: what decision follows.
- If INCONCLUSIVE: what decision follows.

If all outcomes lead to the same decision, do not run the diagnostic; move it
to watchlist.

## Weakest-Link Rule

New slices must target the weakest link in the current evidence chain, not the
most interesting caveat.

Gap > caveat.

If a slice only explains a caveat but does not change the next decision, defer
it.

## Candidate Next Step

- Recommended next step after this design lock is independent review of the
  paper-prerequisites design lock.
- If accepted, next task is a paper-prerequisites proposal document.
- That proposal still must not approve paper trading.

## What This Does Not Authorize

- Paper trading.
- Live trading.
- Runtime wiring.
- Private API.
- Exchange operations.
- Order_status.
- Orders.
- Cancels.
- Set_leverage.
- Probes.
- Strategy filters.
- Parameter optimization.
- Readiness claims.
