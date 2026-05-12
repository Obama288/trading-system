# Stage 54-SQ-D1 Funding Carry / Funding Stress Cheap Falsification Design Lock

## Purpose

D1 exists to determine whether Funding Carry / Funding Stress shows enough
mechanism-consistent early observational evidence to justify any tighter
formal Setup D research path.

D1 must decide whether:

- Setup D deserves further formalization;
- the hypothesis needs refinement because carry and stress remain
  insufficiently separated;
- or Setup D should be parked/rejected before heavier work.

Planning only. This does not implement D1. This does not authorize downloads,
API/network calls, or backtesting.

## Current State

- Setup C is parked from active progression.
- Funding Carry / Funding Stress is the active advanced-to-hypothesis
  candidate.
- `research/signal_observation/SETUP_D_HYPOTHESIS.md` exists.
- `docs/PRE_D1_DECISION_GATE.md` passed independent review with required
  HOLD-path clarification applied.
- Human Owner authorized opening D1 design-lock work.
- No Setup D data work, implementation, or backtest is authorized by current
  state.

## D1 Question

Does a bounded first reconnaissance check around positive funding states and
funding extremes show a mechanism-consistent observational skew strong enough
to justify further Setup D research, while keeping carry-related and
stress-related interpretations explicitly separated?

## Locked Research Intent

D1 is reconnaissance / cheap falsification only. It is pre-backtest, not a
trading strategy, not a profitability claim, and not a paper-candidate test.

The intent is to weaken or support mechanism plausibility early, not to
optimize a setup.

## Locked Branch Separation

D1 must preserve two distinct branches.

### Branch A - Funding Carry / Compensation

Question:
Do materially positive funding states show observational evidence consistent
with carry-related compensation, persistence, or economically meaningful
transfer conditions that are not immediately incoherent?

### Branch B - Funding Stress / Unwind Vulnerability

Question:
Do extreme positive funding states show observational evidence consistent with
reversal, stress, or unwind vulnerability distinct from the carry
interpretation?

Explicit rules:

- D1 may find support for A, B, both, neither, or an inconclusive split.
- D1 must not collapse these into one generic "funding effect."
- Evidence that supports continuation/persistence must not be mislabeled as
  stress/unwind evidence.

## Locked Scope

- Setup family: Setup D / Funding Carry / Funding Stress only.
- Signal family: Carry / funding.
- Research type: cheap-falsification reconnaissance only.
- Inputs conceptually in scope:
  - funding-rate history;
  - aligned OHLCV / market-response observations needed to evaluate simple
    post-funding behavior.
- Open interest is explicitly out of D1 unless a future owner-approved
  gate/design lock expands scope.
- No private exchange data.
- No private endpoints.
- No account/balance/position/order data.
- No execution realism modeling at D1.
- No strategy entry/exit logic.
- No optimization.

D1 does not lock exact venues, symbols, time windows, funding thresholds,
statistics, event windows, or dataset acquisition source. Those belong to a
later bounded feasibility/acquisition or implementation planning step if this
design lock is approved.

## Data Availability Rule

- This design lock does not authorize new data downloads.
- D1 implementation cannot begin until the required public funding/OHLCV data
  path is explicitly authorized through a later owner-approved step if needed.
- If suitable committed data already exists, later work may propose using it,
  but this design lock itself does not assume that it exists.
- No fabricated, substituted, or silently approximated funding data.

## Candidate D1 Observations

Candidate observations only; not implementation and not final statistics.

### 1. Positive Funding State Forward-Response Check

Observe whether materially positive funding states are followed by any stable,
mechanism-consistent forward market-response skew that could plausibly support
a carry/persistence branch.

### 2. Extreme Positive Funding Stress Check

Observe whether extreme positive funding states are followed by any stable
stress/reversal/unwind-like response distinct from ordinary positive-funding
continuation behavior.

### 3. Funding Normalization Check

Observe whether elevated funding tends to normalize in a way that adds
mechanism-consistent information beyond price-only behavior.

### 4. Branch Separation Check

Assess whether carry-like and stress-like interpretations remain empirically
distinguishable enough to justify tighter future Setup D work rather than
collapsing into one vague funding narrative.

For each observation, D1 must keep wording observational, must not lock
thresholds or methods, and must not specify exact metrics yet.

## Interpretation Rules

D1 uses four possible result labels:

- D1_SUPPORTS_CARRY_BRANCH:
  Early observations are coherent enough for the carry/compensation branch to
  justify further formal research consideration, while stress remains
  unsupported or separate.
- D1_SUPPORTS_STRESS_BRANCH:
  Early observations are coherent enough for the stress/unwind branch to
  justify further formal research consideration, while carry remains
  unsupported or separate.
- D1_MIXED_OR_INCONCLUSIVE:
  Observations are weak, internally mixed, underpowered, or do not separate
  carry and stress cleanly enough to justify a tighter Setup D research path
  without refinement.
- D1_WEAK_OR_REJECT:
  Observations materially fail to support either branch, are economically
  trivial, or reduce Setup D to a vague narrative not worth heavier work.

D1 does not produce PASS_CANDIDATE. D1 does not approve implementation
progression automatically. Any result still requires review and owner decision.

## Decision Unlocked

- D1_SUPPORTS_CARRY_BRANCH:
  May justify a future owner decision on whether to create a tighter
  carry-focused next-stage gate/design lock.
- D1_SUPPORTS_STRESS_BRANCH:
  May justify a future owner decision on whether to create a tighter
  stress-focused next-stage gate/design lock.
- D1_MIXED_OR_INCONCLUSIVE:
  Refine hypothesis or define the missing evidence requirement; do not
  escalate.
- D1_WEAK_OR_REJECT:
  Park or reject Setup D before heavier work.

None of those later documents are pre-authorized by this design lock.

## Anti-Cherry-Picking Rules

- No post-result branch relabeling.
- No claiming stress support from continuation-only observations.
- No claiming carry support from reversal-only observations.
- No threshold/window/venue/symbol selection after seeing results.
- No excluding inconvenient symbols/venues later without a pre-approved lock.
- No converting a reconnaissance observation into a strategy rule.
- No reading inconclusive as supportive.
- No economic/trading readiness inference from D1.

## Stop Rules

- Stop if D1 cannot plausibly produce distinct decisions across support /
  mixed / weak outcomes.
- Stop if the proposed next step requires private endpoints, secrets, account
  data, execution flows, or readiness promotion.
- Stop if required data access is not explicitly authorized in a later step.
- Stop if carry and stress are being collapsed into one vague effect.
- Stop if the proposed check becomes a hidden strategy backtest or parameter
  search.

## Review Requirement Before Any D1 Execution

- Independent review of this design lock is required before any D1 data-path
  step, acquisition step, implementation, processing, or artifact generation.
- Human Owner approval is required before any later D1 data-path / acquisition
  / implementation scope.
- No D1 execution from this document alone.

## What D1 Does Not Authorize

- No data downloads.
- No API/network calls.
- No private exchange endpoints.
- No implementation.
- No backtesting.
- No strategy rules.
- No parameter optimization.
- No execution realism claims.
- No Setup D candidate promotion.
- No paper/runtime/trading/probe/live readiness claims.
