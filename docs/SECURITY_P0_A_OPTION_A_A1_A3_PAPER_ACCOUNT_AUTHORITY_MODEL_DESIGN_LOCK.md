# Security P0-A Option A Design Lock - A1 + A3 Paper Account Authority Model

> **Status: PARKED** — Deferred during research throughput focus. Reopen only by explicit Owner decision when paper account authority/security work becomes active.

## Purpose

This design lock records the owner-approved A1 + A3 paper account authority
direction for P0-A Option A.

It locks the source-model intent before any implementation scope.

It does not implement code.

It does not authorize migrations, tables, or schema changes.

It does not claim P0-A is fixed.

## Current Accepted State

- Option B containment is complete and accepted.
- P0-A remains open.
- Option A source design is accepted.
- Human Owner approved A1 + A3 direction.
- `open_positions` already has a repo-grounded DB-backed authority candidate.
- `equity_usdt` and `daily_pnl_usdt` do not yet have authoritative
  repo-grounded sources.
- Option C remains adjacent and out of scope.

## Locked Direction

Hephaestus will proceed on the Option A source-model assumption that:

1. Paper `equity_usdt` must come from a dedicated persisted paper account
   authority, not from caller payloads, CLI parameters, or config defaults.
2. Paper `daily_pnl_usdt` must be derived or maintained from authoritative
   paper/account/position/execution facts under explicit reset boundaries, not
   supplied by callers.
3. Future Option A implementation scope must preserve this split:
   - equity authority base;
   - daily PnL authority semantics.
4. This direction supersedes generic-storage-by-default thinking.
   `system_state` is not selected as the account authority by this design lock.

## A1 - Paper Equity Authority Base

A dedicated persisted paper account authority is the chosen source-model
direction for paper equity.

It must have a clear owner/component boundary.

It must not be confused with generic state, runner input, or config defaults.

It should be suitable for protected risk admission to retrieve equity
service-side.

Exact schema/table fields are not locked here and belong to a later
implementation-scope/design step.

## A3 - Daily PnL Authority Semantics

Daily PnL must not remain caller-supplied for protected admission.

It must be derived or maintained from authoritative state under explicit reset
semantics.

It may depend on later-defined paper account, position, execution, close, fee,
and reset-window rules.

It must be integration-testable.

Exact formula/reset timing is not locked here and belongs to a later bounded
design step.

## Open Positions And Portfolio Exposure Relationship

`open_positions` already has a repo-grounded authority candidate through
DB-backed position state, but exact capacity semantics remain later design
detail.

`portfolio_exposure_pct` must not remain caller-authoritative.

It should later be derived from authoritative equity and position state or
remain non-gating/informational until that derivation exists.

This design lock does not promote `portfolio_exposure_pct` into a new rejection
gate.

## Why A2 Is Not Selected

Generic `system_state` storage is not selected as the paper account authority
path.

Existing table presence is not sufficient evidence of proper account ownership
semantics.

Any future reconsideration of `system_state` would require a separate explicit
owner-approved decision.

No implementation may silently substitute generic state for the A1 direction
locked here.

## Required Properties For Future Implementation Scope

Future implementation-scope design must answer:

- What component owns the paper account authority?
- What persisted state is required to represent paper equity safely?
- How does protected risk admission retrieve that equity without caller
  override?
- How is daily PnL derived or maintained from authoritative events/state?
- What reset boundary governs daily PnL?
- What integration tests prove caller-provided equity/PnL cannot override
  protected admission?
- How are open-position authority and future exposure derivation aligned with
  this account model?

Do not answer these fully here.

## Closure Discipline

This design lock does not close P0-A.

P0-A remains open until:

- caller-supplied account-state authority is removed from protected admission;
- A1/A3 authority model is implemented;
- integration-level evidence confirms callers cannot override authoritative
  equity/PnL;
- independent review passes;
- docs/status do not overclaim closure.

## Relationship To Option C

Option C orchestrator risk-decision provenance remains adjacent and out of
scope.

Option C may be revisited after this A1 + A3 account authority model is
implementation-scoped or implemented.

Option C must not be used to bypass the need for A1 + A3 account-state
authority.

## Stop Rules

- Stop if implementation scope tries to use config defaults as paper equity
  authority.
- Stop if implementation scope tries to keep caller-supplied daily PnL in
  protected admission.
- Stop if `system_state` is silently substituted for the selected A1 direction.
- Stop if a proposal claims P0-A closure without integration-level evidence.
- Stop if work drifts into Option C, private API, live readiness, or exchange
  operations without a separate owner-approved prompt.

## Review Requirement Before Implementation Scope

Because this design lock directly opens a future Protected Lane code scope,
independent review is required before implementation scope begins.

Human Owner approval is required after review before any code task.

Tower Control must verify that the future implementation scope remains faithful
to A1 + A3.

## What This Does Not Authorize

- No code changes.
- No migrations.
- No new tables.
- No schema changes.
- No system_state repurposing.
- No risk-engine implementation.
- No paper-runner changes.
- No Option C implementation.
- No private API.
- No exchange calls.
- No P0-A closure claim.
- No readiness promotion.
