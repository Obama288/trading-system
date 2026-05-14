# Security P0-A Option A Decision - Paper Account Authority

## Purpose

This document frames the owner decision on the paper-lane authority model for
`equity_usdt` and `daily_pnl_usdt`.

It follows the accepted Option A source design.

This is required before any Option A implementation scope can be prepared.

This document does not implement code.

This document does not authorize migrations, new tables, or schema changes.

This document does not claim P0-A is fixed.

## Current Accepted State

- Option B containment is complete and accepted, but P0-A remains open.
- Option A source design is accepted.
- `open_positions` already has a repo-grounded DB-backed authority candidate.
- `equity_usdt` and `daily_pnl_usdt` still lack a repo-grounded authoritative
  source.
- `portfolio_exposure_pct` remains derivative/non-gating until equity and
  position authority are established.
- Option C orchestrator provenance remains adjacent and out of scope.

## Decision Question

Which paper-lane authority model should Hephaestus adopt for authoritative
`equity_usdt` and `daily_pnl_usdt` in protected risk admission?

## Decision Criteria

The owner should choose a direction that:

- fixes the authority-boundary problem rather than relabeling it;
- gives a clear owning component/source;
- supports deterministic risk admission;
- does not depend on caller-provided equity/PnL;
- supports integration-testable protected admission semantics;
- does not silently over-authorize live/private-exchange behavior;
- fits current paper-only posture without pretending to be live-ready.

## Option A1 - Dedicated Persisted Paper Account Authority

Introduce a dedicated paper account/equity/PnL authority model later through a
separate design lock and implementation scope.

This authority would explicitly own:

- current paper equity;
- daily PnL basis or derived daily PnL state;
- reset semantics or daily accounting boundaries as later design details.

Protected risk admission would read from this authority, not caller input.

Security value:

- Creates a clear service-side owner for risk-critical paper account facts.
- Removes caller control over equity and daily PnL in protected admission.
- Gives P0-A closure work a concrete authority boundary to test.

Architectural clarity:

- Best matches the requirement that paper risk authority must be explicit.
- Avoids treating generic state, config defaults, or harness parameters as an
  accidental account ledger.

Likely impact:

- A future schema/migration design is likely required.
- Later implementation scope must define update rules, ownership, reset
  semantics, and integration tests.

Downside:

- More work than reusing an existing generic state table, but the ownership
  model is cleaner.

Classification:

- Preferred clean architecture candidate.

## Option A2 - Explicit Extension Of Existing Generic State Storage

Deliberately evaluate whether `system_state` or another existing generic state
mechanism should be extended to hold paper account authority.

This is not currently approved and must not be inferred from existing table
presence.

Using generic state would require explicit owner approval, field ownership
semantics, update rules, and testability guarantees.

It must not become ad hoc JSON dumping.

Security value if tightly governed:

- Could move equity/PnL authority away from caller payloads.
- Could reduce implementation surface if strong ownership and update rules are
  designed first.

Migration/speed tradeoff:

- May be faster than creating a dedicated account table.
- May avoid an immediate schema addition if the owner accepts the weaker
  semantic model.

Downside:

- Weaker semantic clarity than a dedicated paper-account model.
- Higher risk of ambiguous ownership and future misuse.
- Risk of turning generic state into an ambiguous pseudo-ledger.

Classification:

- Possible but higher ambiguity / needs strong justification.

## Option A3 - Derive Daily PnL From Position/Execution History Plus Separate Equity Authority

Paper equity authority is defined separately.

Daily PnL is not stored directly as caller-provided state. It is derived from
authoritative position/execution/close history using explicit reset
boundaries.

This may combine with A1 or another approved equity source.

This is not implementation; it is a decision option on accounting shape.

Security value:

- Removes caller-provided daily PnL from protected admission.
- Ties daily loss gating to service-side state instead of operator input.
- Makes false-but-plausible caller PnL unable to override protected admission.

Why it avoids trusting caller daily PnL:

- The daily PnL value would be computed or maintained from authoritative
  account/position/execution facts under defined reset boundaries.
- The caller would not supply the risk-critical daily loss state.

Dependencies:

- Position and execution semantics must be sufficient for the chosen PnL
  definition.
- Closed-position, open-position, fee, slippage, partial-fill, and reset-window
  treatment must be designed later before implementation.

Downside:

- Accounting definition and reset logic require careful design.
- It is not a complete equity-source answer by itself.

Classification:

- Strong daily-PnL design direction, but not a complete equity-source answer by
  itself.

## Option A4 - HOLD / Narrower Paper Account Analysis

Do not choose an authority model yet.

Perform a narrower bounded analysis first if the owner believes repo evidence
is insufficient to choose between A1/A2/A3 combinations.

This delays implementation but avoids premature architecture commitment.

## Tower Control Recommended Direction

Recommended owner direction:

- Prefer **A1 as the equity authority base**: a dedicated persisted paper
  account authority model is the cleanest source-of-truth candidate.
- Combine with **A3 for daily PnL semantics**: daily PnL should be derived or
  maintained from authoritative account/position/execution facts under explicit
  reset boundaries, not accepted from callers.
- Do **not** choose A2 by default: `system_state` may only be reconsidered
  through explicit owner-approved justification, not as a convenience shortcut.
- If the owner is not ready to choose this, select HOLD / narrower analysis
  rather than silently falling back to generic state.

## Owner Decision Needed

Decision requested:

- APPROVE A1 + A3 DIRECTION:
  dedicated persisted paper equity/account authority as base, with daily PnL
  authority derived/defined from authoritative state under later design.
- CHOOSE A2 EXPLORATION:
  explicitly investigate extending generic existing state storage as a paper
  account authority, with no implementation authorized yet.
- HOLD:
  request narrower analysis before choosing the paper account authority
  direction.

No Option A implementation scope should begin until the owner chooses one of
these directions.

## Integration-Test Requirement To Preserve

Future P0-A closure cannot rely on unit tests alone.

Any implementation path claiming progress toward protected risk-admission
authority must later include integration-level evidence that caller-supplied
equity/PnL cannot override service-side authoritative state.

This document does not design those tests yet; it records the requirement for
later implementation scope.

## Rejected Non-Solutions

- Using caller-supplied equity or daily PnL in protected admission while
  claiming P0-A progress.
- Using config defaults as authoritative paper equity.
- Silently repurposing `system_state` without explicit owner-approved
  authority design.
- Deriving daily PnL from incomplete/non-authoritative data while claiming risk
  authority.
- Treating Option B containment as Option A completion.

## What This Decision Does Not Resolve Yet

- Exact DB schema or table layout.
- Exact daily PnL reset timestamp/window.
- Exact position/execution formula for daily PnL.
- Whether generic state storage is ever acceptable.
- Exact risk-engine retrieval mechanism.
- Exact integration test shape.
- Option C provenance design.

## Review Requirement

Independent review of this decision document is required before the Human Owner
selects a path.

If the owner approves A1 + A3 direction, Tower Control should prepare the next
bounded design lock for that source model.

If the owner chooses A2 exploration, Tower Control should prepare a narrower
source-analysis task instead.

No implementation should begin from this document alone.

## What This Does Not Authorize

- No code changes.
- No migrations.
- No new tables.
- No schema changes.
- No use of `system_state` as account authority.
- No risk-engine implementation.
- No paper-runner changes.
- No private API.
- No exchange calls.
- No Option C implementation.
- No P0-A closure claim.
- No readiness promotion.
