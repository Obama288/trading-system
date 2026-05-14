# Security P0-A Option A Design - Authoritative Account-State Source

## Purpose

This document defines the authoritative account-state source model needed to
resolve P0-A.

It follows accepted Option B containment, which did not close P0-A.

This document does not implement Option A.

This document does not authorize code changes.

This document does not claim P0-A is fixed.

## Current P0-A State

- Risk admission still requires account-state facts that are not yet fully
  authority-side.
- Paper harness request shape is now structurally labeled as non-authoritative,
  but risk admission itself still needs an authoritative state model.
- Option A is mandatory before any higher readiness claim.
- Option C orchestrator risk-decision provenance remains adjacent and out of
  scope here.

## Account-State Fields Under Decision

| Field | Current supply/use | Repo-grounded authoritative source today | Current risk effect | Required Option A direction |
| --- | --- | --- | --- | --- |
| `equity_usdt` | Supplied by paper harness CLI/local caller state and passed into risk evaluation. | No authoritative persisted/runtime source found in the inspected repo. | Used in max-loss sizing, risk percentage, and daily-loss calculations. | Create or select a service-side paper account/equity authority; later live-capable authority must be separately approved. |
| `daily_pnl_usdt` | Supplied by paper harness CLI/local caller state and passed into risk evaluation. | No authoritative persisted/runtime source found in the inspected repo. | Used in daily loss-limit gating. | Create or select a service-side daily PnL authority derived from authoritative account/position/execution state. |
| `open_positions` | Paper harness currently derives it from `PositionRepository.list_open_positions()`; risk route schema still permits caller-supplied value. | A plausible repo-grounded source exists through DB-backed position state and `PositionRepository`; exact admission definition still needs design detail. | Used in max-open-position gating. | Retrieve service-side from DB-backed position authority, including a decision on pending admissions/orphan recovery handling. |
| `portfolio_exposure_pct` | Supplied by paper harness local caller state and returned through risk output. | No complete authoritative source found because exposure needs authoritative positions and equity. | In inspected `evaluate_risk.py`, returned in risk output but not used as a rejection gate. | Derive server-side from authoritative positions and equity, or classify as non-gating/informational until derivation exists. |

## Repo-Grounded Source Findings

- `apps/risk_engine/main.py` still exposes `RiskRequest.account_state` on the
  protected risk route.
- `apps/risk_engine/application/evaluate_risk.py` still notes that
  `account_state` is caller-supplied in the MVP pass.
- `ops/paper_pipeline_runner.py` now uses paper-harness-only request models,
  but the harness still supplies `equity_usdt`, `daily_pnl_usdt`, and
  `portfolio_exposure_pct` from local caller inputs.
- `ops/paper_pipeline_runner.py` derives `open_positions` from
  `PositionRepository.list_open_positions()`.
- `apps/position_manager/infrastructure/position_repo.py` provides
  `list_open_positions()`, `count_open_positions()`,
  `count_pending_open_admissions()`, and recovery-oriented helpers over
  DB-backed `PositionModel` and `ExecutionModel`.
- `libs/db/models/position.py` stores position rows with status, quantity,
  entry price, open/close timestamps, and close reason.
- `libs/db/models/execution.py` stores executions with status, mode, payload,
  and idempotency key.
- `libs/db/models/system_state.py` stores generic key/value JSON state, but no
  inspected code establishes it as an authoritative account equity or daily PnL
  source.
- Read-only exchange wallet/balance/open-position client models exist in the
  repo, but this document does not authorize private API use, exchange calls,
  or treating those paths as current runtime authority for risk admission.

Repo-grounded conclusion:

- `open_positions` appears derivable from persisted position state through
  `PositionRepository` or an equivalent DB-backed service-side path.
- `equity_usdt` does not appear to have a current authoritative persisted or
  runtime source in the repo.
- `daily_pnl_usdt` does not appear to have a current authoritative persisted or
  runtime source in the repo.
- `portfolio_exposure_pct` requires server-side derivation after positions and
  equity authority are defined, or it should remain non-authoritative and
  informational until then.

## Authoritative Source Design Principle

Protected risk admission must not accept caller-supplied values as
authoritative account state.

Risk-critical facts must come from service-side persisted/runtime sources with
a defined owner.

Derived fields must be derived server-side from authoritative base facts.

If a required authority source is unavailable, protected admission should not
pretend it exists.

## Proposed Option A Source Model

### Open Positions

- Candidate authority: position manager / DB-backed position repository or an
  explicitly owned account-state service path.
- Must be retrieved service-side, not caller-supplied.
- The implementation-scope design must decide whether max-open-position
  capacity counts only persisted open positions or also pending admissions and
  orphan filled executions.
- The existing `count_pending_open_admissions()` helper suggests this edge case
  is already recognized in the repo, but this document does not decide the
  final admission formula silently.

### Equity

- No current authoritative source appears to exist in the inspected repo.
- Option A must introduce or select a persisted paper account/equity authority
  for the paper lane.
- A later live-capable authority source must be separately approved when
  relevant.
- Do not fake equity authority with config defaults or caller parameters.

### Daily PnL

- No current authoritative source appears to exist in the inspected repo.
- Option A must define how daily PnL is produced from authoritative
  account/position/execution state.
- The design must define reset boundaries and source ownership in a later
  implementation-scope pass.
- Do not accept caller daily PnL for protected admission.

### Portfolio Exposure

- Must not remain caller-authoritative.
- In the inspected risk use-case today, `portfolio_exposure_pct` is returned in
  output but is not used as a rejection gate.
- Future authoritative form should be server-side derived from authoritative
  positions and equity, or explicitly deferred as non-gating/informational
  until such derivation exists.
- Do not convert it into a fake gate without a separate owner-approved design.

## Paper Mode Versus Future Higher-Readiness Mode

Paper mode still needs a coherent authoritative paper account-state source if
it is to support protected risk-admission claims.

Option B paper harness can continue as harness-only and non-authoritative.

Option A must define the authority model for any lane that wants protected
risk-admission semantics.

Future live-capable mode may use exchange/reconciliation facts, but this
document does not authorize private API, live exchange access, or
implementation.

## What Option A Must Resolve Before P0-A Can Close

- Caller-supplied account-state fields are removed from protected admission
  authority.
- Each risk-critical field has an owner/source or is explicitly removed from
  protected admission.
- Server-side retrieval or derivation is defined.
- Tests verify callers cannot falsify authority state for protected admission.
- Independent review passes.
- Docs/status do not overclaim closure before implementation.

## Relationship To Option C

Option C remains necessary to assess whether the orchestrator may accept only
trusted risk decisions.

Option C is not a substitute for Option A.

Once account-state authority is designed, Tower Control should decide whether
orchestrator provenance needs a separate design lock before implementation or
after Option A source implementation scope.

## Open Design Decisions Before Implementation

- Exact owning component for paper equity/PnL authority.
- Whether the risk engine directly queries repositories/services or receives a
  signed/provenanced authoritative state object from another service.
- Exact definition of open positions for risk capacity, including pending/open
  admission edge cases.
- Exact treatment of `portfolio_exposure_pct` in current risk decision
  semantics.
- Whether any current generic state storage, such as `system_state`, should be
  used, extended, or avoided for paper account authority.

## Rejected Non-Solutions

- Validation-only closure.
- Using config default equity as authoritative risk state.
- Leaving caller-supplied daily PnL in protected admission while claiming P0-A
  closed.
- Relabeling fields without changing authority source.
- Treating Option B containment as Option A completion.

## Review Requirement Before Implementation Scope

Independent review of this Option A source design is required before any
Option A implementation-scope prompt.

Human Owner approval is required before any code task.

Because this is Protected Lane authority work, Tower Control must verify that
future implementation scope matches this source design and does not fabricate
authority.

## What This Does Not Authorize

- No code changes.
- No schema changes.
- No DB migrations.
- No new account-state tables.
- No private API.
- No exchange calls.
- No Option C implementation.
- No P0-A closure claim.
- No readiness promotion.
