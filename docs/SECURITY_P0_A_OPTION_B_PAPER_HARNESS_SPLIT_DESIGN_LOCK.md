# Security P0-A Option B Design Lock - Paper Harness / Protected Risk Admission Split

## Purpose

This design lock defines the near-term containment direction for P0-A.

It formalizes the separation between:

1. explicit paper-harness flows that may still use caller-supplied account state;
2. protected risk-admission semantics that must not be represented as
   authoritative if they depend on caller-supplied account state.

This is planning only.

This does not implement Option B.

This does not close P0-A.

## Current State

- P0-A remains open: risk admission currently relies on caller-supplied
  account-state fields.
- The P0-A authority decision document was created and independently reviewed.
- Human Owner approved the staged path: Option B now, Option A mandatory
  target, Option C adjacent follow-up.
- P0-B auto-approve paper guards were handled separately.
- No Option B code changes are authorized by this design lock alone.

## Core Boundary Rule

Caller-supplied `account_state` may remain only in a clearly identified
local/paper-harness path.

Any flow using caller-supplied `account_state` must be semantically labeled and
treated as harness-only, not as protected authoritative risk admission.

Protected risk-admission claims must not be made from a flow whose
account-state authority remains caller-supplied.

No docs, tests, or runtime claims may blur this distinction.

## What Counts As Paper Harness

- `ops/paper_pipeline_runner.py` is the known paper-harness caller path.
- It may use explicit owner/operator-provided local inputs to exercise the
  paper pipeline.
- Those inputs are not authoritative account-state truth.
- Harness output may be useful for paper workflow testing, but it must not be
  described as resolving production-capable risk authority.

Do not redesign the runner here.

Do not authorize code changes here.

## What Counts As Protected Risk Admission

Protected risk admission is the system role that determines trade
admissibility under authoritative state assumptions.

If account-state authority is caller-supplied, that path cannot be treated as
fully authoritative protected admission.

The current P0-A finding exists precisely because this semantic separation is
not yet explicit enough in code/contracts.

Option B implementation must prevent harness semantics from being confused
with protected admission semantics.

## Locked Containment Direction

Future Option B implementation scope, if separately approved, should aim to:

- make paper-harness semantics explicit in naming, code structure, tests,
  and/or call paths;
- make it difficult to accidentally treat harness inputs as authoritative risk
  state;
- clearly label any caller-supplied account-state path as non-authoritative /
  paper-harness-only;
- preserve the fact that Option A remains required for true authoritative
  account-state resolution.

Do not lock exact filenames or code edits in this design lock.

Those belong to a later implementation-scope prompt.

## Required Non-Claims

- Option B does not prove risk-engine authority.
- Option B does not make caller-supplied account state safe for protected
  admission.
- Option B does not close P0-A.
- Option B does not authorize higher paper/runtime/trading/probe/live readiness
  claims.
- Option B does not replace Option A.

## Option A Remains Mandatory

Option A - Server-Side Authoritative Reconstruction remains the
architecture-correct target.

Option B is a containment bridge, not the final fix.

No future higher readiness claim may rely on Option B alone.

Before any claim beyond the current constrained paper/harness semantics, the
project must define and implement an authoritative account-state source under
Option A or an owner-approved equivalent that truly resolves the authority
boundary.

P0-A must remain open until that occurs and is independently reviewed.

## Relationship To Option C

Option C - Orchestrator Risk Provenance Hardening remains related but not a
substitute for account-state authority.

Option C may be sequenced after the account-state authority direction is
selected, or revisited in a dedicated follow-up decision.

Option C must not be used to claim P0-A is closed while caller-supplied account
state remains authoritative upstream.

## Design Questions For Later Option B Implementation

A future implementation scope must answer:

- Which current entrypoints are explicitly harness-only?
- Where should harness-only semantics be named or enforced?
- What interface/contract distinction prevents accidental reuse as protected
  admission?
- Which tests must assert that harness-only paths are not represented as
  authoritative?
- What docs/comments/status language must avoid readiness overclaim?

Do not answer these implementation questions fully here.

## Stop Rules

- Stop if Option B implementation begins to look like a silent permanent
  replacement for Option A.
- Stop if a proposed change only renames things but leaves the semantic
  boundary unclear.
- Stop if a proposed change implies that validation-only or labels alone close
  P0-A.
- Stop if implementation scope drifts into Option A or Option C without a new
  owner-approved prompt.
- Stop if any change implies readiness promotion.

## Review Requirement Before Implementation

Independent review of this design lock is required before any Option B
implementation scope is opened.

Human Owner approval is required before any Option B code/task prompt.

Because this is Protected Lane authority-boundary work, Tower Control must
review for scope drift before implementation.

## What This Does Not Authorize

- No code changes.
- No schema changes.
- No paper-runner changes.
- No risk-engine changes.
- No orchestrator changes.
- No tests added.
- No Option A implementation.
- No Option C implementation.
- No readiness promotion.
- No claim that P0-A is fixed.
