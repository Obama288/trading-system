# Security P0-A Option A A1+A3 Implementation Scope

> **Status: PARKED** — Deferred during research throughput focus. Reopen only by explicit Owner decision when paper account authority/security work becomes active.

## Purpose

This document defines the next bounded implementation scope for the accepted
A1 + A3 account authority direction.

It does not implement code.

It does not itself close P0-A.

It does not authorize Option C.

It exists to prevent the next code task from expanding beyond a reviewable,
architecture-faithful Protected Lane slice.

## Current Accepted State

- Option B containment is complete and accepted.
- P0-A remains open.
- Option A source design is accepted.
- Human Owner approved A1 + A3 direction.
- A1 + A3 design lock is accepted.
- `open_positions` has a repo-grounded DB-backed authority candidate.
- `equity_usdt` still requires a dedicated persisted paper authority.
- `daily_pnl_usdt` still requires authoritative derivation/maintenance
  semantics.
- Option C remains adjacent and out of scope.

## Scope Decision

The first implementation slice should focus on:

1. introducing the dedicated persisted paper equity/account authority
   foundation required by A1;
2. wiring protected risk admission to retrieve paper equity from that authority
   rather than trusting caller-supplied equity;
3. enforcing fail-closed behavior if that authority is unavailable;
4. preparing the surface for future A3 daily-PnL authority without pretending
   full A3 derivation is already solved.

Daily PnL:

- A complete, bounded, honest A3 derivation is not ready for the same first
  implementation slice based on the inspected repo state.
- Existing persisted `PositionModel` and `ExecutionModel` records are candidate
  factual bases, but the accounting semantics for daily PnL are not yet locked.
- Full A3 implementation must be deferred to a separate later scope.
- Do not fake A3 progress by keeping caller daily PnL or adding placeholder
  "authoritative" PnL with no accounting semantics.

## First Implementation Slice - In Scope

A future code implementation may be allowed to:

- add a dedicated persisted paper account/equity authority model and its
  minimal repository/service access pattern, if the later implementation prompt
  approves exact files;
- add or adapt migration/model/repository code needed only for that paper
  equity authority foundation;
- modify protected risk admission so caller-supplied `equity_usdt` is no
  longer authoritative for protected route semantics;
- introduce fail-closed handling when authoritative equity cannot be retrieved;
- add tests proving caller-supplied equity cannot override protected risk
  admission;
- add integration-level evidence for the protected route path;
- preserve existing paper harness semantics as non-authoritative and separate.

Likely directories/components for later exact scoping:

- `libs/db/models/**`
- current migration path, if a migration is required by the later code prompt;
- a repository/service layer for paper account authority;
- `apps/risk_engine/main.py`
- `apps/risk_engine/application/evaluate_risk.py`
- risk-engine route/use-case tests;
- integration tests for protected risk admission;
- limited supporting config/docs only if strictly required in the later
  implementation prompt.

Exact allowed files must be re-locked in the future implementation prompt.

## Explicitly Deferred From First Slice

The following remain out of scope for the first implementation slice:

- full A3 daily PnL derivation/maintenance;
- daily PnL reset formula/window;
- portfolio exposure derivation;
- Option C orchestrator provenance;
- private API/exchange-based account state;
- live-ready reconciliation semantics;
- any readiness promotion;
- full P0-A closure claim.

Because A3 is deferred, P0-A remains partially open and must not be claimed
closed after the first slice.

## A3 Daily PnL Grounding Requirement

Any later A3 implementation scope must ground daily PnL in repo-verified
authoritative facts.

Candidate factual bases may include persisted position/execution records, but
only under a separately explicit accounting design that defines:

- what realized/unrealized components count, if any;
- which timestamps/statuses qualify;
- fee/slippage treatment if relevant;
- daily reset boundary.

A3 must not be implemented as:

- caller-provided daily PnL;
- config default;
- opaque generic JSON state;
- arbitrary number copied into storage without defined provenance.

## Fail-Closed Requirement

Protected risk admission must fail closed if authoritative paper equity is:

- absent;
- unavailable;
- invalid;
- unreadable due to dependency failure.

Protected risk admission must fail closed if an implemented A3 daily-PnL
authority is absent, unavailable, invalid, or cannot be derived.

No fallback to caller-supplied `equity_usdt` or `daily_pnl_usdt` is allowed in
protected admission semantics.

Fail-closed behavior must be covered by tests.

## Likely Future Code Touchpoints

Likely later implementation touchpoints include:

- `libs/db/models/**` for the dedicated persisted paper account/equity model;
- the current migration path, if a new persisted model requires schema change;
- a repository/service layer for paper account authority;
- `apps/risk_engine/main.py` for protected route request/authority handling;
- `apps/risk_engine/application/evaluate_risk.py` for use-case input semantics;
- risk-engine route/use-case tests;
- integration tests for protected risk admission;
- limited supporting config/docs only if strictly required in the later
  implementation prompt.

This map is non-authorizing. The future code prompt must name exact allowed
files and may narrow this list.

## Required Tests For Future Implementation

The future code task must include tests proving:

1. Protected risk admission ignores/rejects caller-supplied equity authority in
   favor of service-side paper equity authority.
2. Missing/unavailable/invalid authoritative equity causes fail-closed
   rejection.
3. Caller cannot increase position sizing by inflating request equity.
4. Integration-level route test proves caller body equity cannot override
   service-side authority.
5. Existing harness-only flow remains non-authoritative and separated.
6. If any A3 part is implemented in that slice, equivalent fail-closed and
   no-caller-override tests for daily PnL are required.
7. No readiness promotion is implied by tests/docs.

## Non-Closure Discipline

The first implementation slice may materially reduce P0-A exposure for equity,
but it does not close P0-A unless the full accepted closure conditions are met.

If A3 daily PnL remains deferred, P0-A remains open.

Even if equity authority is implemented, docs/status must not claim full P0-A
closure until all required authority fields are addressed, integration evidence
exists, and independent review passes.

## Stop Rules

- Stop if the implementation plan tries to use config defaults as paper equity
  authority.
- Stop if it tries to use `system_state` silently instead of the selected A1
  direction.
- Stop if it keeps caller-supplied equity authoritative for protected
  admission.
- Stop if it treats placeholder daily PnL storage as A3 completion.
- Stop if it permits fallback from missing authority to caller request values.
- Stop if it drifts into Option C, private API, exchange calls, live readiness,
  or unrelated money-path rewrites.
- Stop if it claims P0-A closure after only partial first-slice work.

## Review Requirement Before Code

Because this implementation scope directly opens a Protected Lane code task,
independent review of this scope document is required before code
implementation.

Human Owner approval is required after review before Codex receives the code
task.

Tower Control must verify that the future code prompt:

- preserves the A1 + A3 direction;
- preserves fail-closed requirements;
- does not fabricate A3 authority;
- does not overclaim P0-A closure.

## What This Does Not Authorize

- No code changes.
- No migrations yet.
- No new tables yet.
- No schema changes yet.
- No `system_state` repurposing.
- No caller-equity fallback.
- No caller-daily-PnL fallback.
- No Option C implementation.
- No private API.
- No exchange calls.
- No P0-A closure claim.
- No readiness promotion.
