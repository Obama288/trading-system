# Security P0-A Decision - Risk Account State Authority

> **Status: PARKED** — Deferred during research throughput focus. Reopen only by explicit Owner decision when paper account authority/security work becomes active.

## Purpose

This document frames the owner decision for the unresolved P0-A security
finding.

The issue is not merely malformed input. The issue is authority:
risk-critical account state is currently caller-supplied while risk is treated
as authoritative for admissibility.

This document does not authorize code changes.

## Confirmed Problem

- `apps/risk_engine/main.py` accepts `RiskRequest.account_state`.
- Caller-supplied values materially affect admission and sizing decisions.
- `equity_usdt` affects max loss, risk percentage, and sizing calculations.
- `daily_pnl_usdt` affects loss-limit gating.
- `portfolio_exposure_pct` and `open_positions` affect exposure or capacity
  interpretation where applicable.
- `apps/risk_engine/application/evaluate_risk.py` explicitly documents that
  `account_state` is caller-supplied in the MVP pass.
- `ops/paper_pipeline_runner.py` supplies `equity_usdt`, `daily_pnl_usdt`, and
  `portfolio_exposure_pct` from CLI arguments, while deriving `open_positions`
  from the caller-side paper runner flow.
- The orchestrator consumes an already-computed `RiskDecision` rather than
  reconstructing account-state authority itself.

## Why Validation-Only Does Not Close P0-A

Sanity checks and numeric bounds can reject impossible values. They cannot
distinguish false-but-plausible values from authoritative values.

Examples:

- inflated but positive equity;
- zero daily loss despite real losses;
- plausible but understated exposure.

Therefore validation-only may be useful hygiene, but it does not resolve the
trust-boundary P0.

Validation-only is not a P0-A closure path.

## Decision Requirement

The owner must choose the intended remediation direction before implementation.

Decision question:

Which account-state authority model should Hephaestus adopt for protected risk
admission?

## Option A - Server-Side Authoritative Reconstruction

Risk admission no longer treats caller-supplied account state as authoritative.
The risk engine or an explicitly trusted service-side authority reconstructs
account state from authoritative persisted or runtime sources.

The caller payload may request an evaluation context, but it must not supply
authoritative equity, PnL, exposure, or position state.

Security value:

- Places risk-critical account state under a service-side authority boundary.
- Removes caller control over fields that materially affect admission and
  sizing.
- Creates a cleaner basis for any later higher-readiness claim.

Likely impact:

- Risk request schemas and risk use-case inputs may need to change.
- A trusted source for equity, PnL, exposure, and positions must be defined.
- Paper-mode behavior needs an explicit authoritative paper-state model.

Key unresolved design question:

- What exact authoritative source owns equity, PnL, exposure, and positions in
  paper mode versus later live-capable modes?

Classification:

- Architecture-correct target.

## Option B - Explicit Paper Harness Split

Caller-supplied account state remains allowed only in an explicit local or
paper-harness path. Protected risk-admission semantics are separated from
harness semantics.

The harness must not be mistaken for authoritative money-path admission. This
preserves current paper tooling while reducing ambiguity about what is and is
not authoritative.

Security value:

- Contains caller-supplied account state to a clearly named harness boundary.
- Prevents paper-runner convenience inputs from being treated as protected
  admission semantics.
- Creates a safer transition path toward authoritative reconstruction.

Likely impact:

- Paper runner and risk entry points may need clearer separation.
- Tests and docs must identify harness-only behavior explicitly.
- Protected risk admission must not silently reuse the harness authority model.

Key downside:

- This separates semantics, but it does not itself create the final
  authoritative source for full protected admission.

Classification:

- Transitional containment path.

## Option C - Orchestrator Risk Provenance Hardening

The orchestrator should not accept an arbitrary positive `RiskDecision` without
a trustworthy provenance path. It either calls authoritative risk evaluation
itself or accepts only a verifiable risk decision produced through an approved
service boundary.

Security value:

- Reduces the chance that a non-authoritative caller can inject a positive risk
  decision into candidate creation.
- Aligns orchestrator behavior with the risk engine's authority role.

Likely impact:

- Orchestrator evaluation flow and schemas may need to change.
- A risk service client or verifiable decision provenance mechanism may be
  required.
- Existing paper pipeline flow may need adaptation.

Why this is adjacent:

- It protects risk-decision provenance, but the primary P0-A decision is still
  the authority model for account state itself. It may be sequenced after the
  account-state authority direction is chosen.

Classification:

- Adjacent authority-boundary hardening.

## Rejected As Closure Path - Validation-Only Mitigation

Additive sanity validation may still be approved later as hygiene or paper
guardrails. It must not be recorded as closing P0-A.

Validation-only may only accompany, not replace, an authority-model decision.

## Recommended Staged Path

1. Adopt Option B as the near-term containment direction: explicitly separate
   paper-harness caller-supplied state from protected risk-admission semantics.
2. Treat Option A as the architecture-correct target: define the authoritative
   account-state source before any higher readiness claim.
3. Treat Option C as an adjacent follow-up: assess orchestrator risk-decision
   provenance after the account-state authority direction is chosen.
4. Do not claim P0-A closed until an owner-approved architecture path is
   implemented and reviewed.

## Owner Decision Needed

Decision requested:

- APPROVE STAGED PATH:
  B now as containment direction, A as target architecture, C as follow-up.
- CHOOSE OPTION A DIRECTLY:
  proceed straight to authoritative reconstruction design.
- HOLD:
  request narrower analysis before deciding.

No implementation should begin until the owner chooses one of these directions.

## What This Does Not Authorize

- No code changes.
- No risk schema changes.
- No paper harness changes.
- No orchestrator contract changes.
- No readiness promotion.
- No claim that P0-A is fixed.
- No implementation design lock yet unless separately authorized.

## Review Requirement

Because this is a Protected Lane authority-boundary decision, independent
review should occur before any implementation scope is opened.

If the Human Owner chooses a remediation path, Tower Control should prepare a
bounded design-lock or implementation-scope prompt next, depending on the
chosen path.
