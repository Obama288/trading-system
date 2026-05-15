# Stage 54-SQ-E1 Reversal Cheap Falsification Design Lock

## Purpose

This document locks the future E1 cheap-falsification design for Setup E.

Setup E is now specifically framed as:

`Post-Liquidation Exhaustion Reversal`

This design lock does not itself authorize retrieval, implementation, evidence
claims, readiness promotion, or trading recommendations.

## Current Accepted State

- Liquidation Cascades passed triage and advanced to hypothesis note.
- BTC daily GitHub coarse EXPLORE returned `EXPLORE_WEAK`.
- Richer-source survey identified Coinalyze as a stronger path.
- Coinalyze 20-symbol 4h EXPLORE returned `EXPLORE_MIXED`.
- Generic all-elevated bucket was not compelling.
- Directional split suggested more coherent reversal/exhaustion structure:
  - long-dominant intervals: weaker recovery-like tendency;
  - short-dominant intervals: clearer negative follow-through /
    reversal-like structure.
- Pre-E1 decision gate passed review and recommends proceeding to this E1
  design path.
- All prior EXPLORE results remain non-evidence / non-validation.

## Locked Research Question

After unusually large directional liquidation intervals, does price behavior
over fixed short forward horizons show a reversal/exhaustion structure that
survives a pre-specified volatility/regime confound-control baseline?

This question is bounded and observational. It must not be converted into a
trading strategy.

## Locked Sub-Hypotheses

### E1-L: Long-Dominant Liquidation Exhaustion

After unusually large long-liquidation-dominant intervals, future returns
should show a reversal/recovery-like tendency, relative to the matched
confound-control baseline.

### E1-S: Short-Dominant Liquidation Exhaustion

After unusually large short-liquidation-dominant intervals, future returns
should show a reversal/decline-like tendency, relative to the matched
confound-control baseline.

E1-L and E1-S must be evaluated separately. They must not be collapsed into
one pooled headline.

A pooled summary may be reported only as descriptive appendix/secondary
context, not as the decisive gate.

## Source and Scope Boundaries

- Coinalyze liquidation-history API is the planned liquidation source.
- E1 should preserve a bounded liquid-perpetual universe, selected before
  retrieval.
- The formal design must not reuse the already explored Coinalyze EXPLORE
  window as evidence or validation.
- The formal validation window must be out-of-window relative to the explored
  2025-09-06 to 2026-05-15 window.

This lock does not define an exact retrieval task because retrieval requires a
later owner-approved task. It locks the rule that validation must be
out-of-window and pre-authorized later.

## Held-Out Window Requirement

Held-out-window validation is required for any E1 evidence claim.

Held-out-symbol validation may be included as an additional robustness check,
but cannot replace held-out-window validation.

The already explored Coinalyze window must not be reused as the formal
validation window.

The E1 design lock and independent review must be finalized before any new
validation window is accessed, retrieved, or inspected.

## Volatility / Regime Confound Control

E1 must include a pre-specified confound-control design that distinguishes
liquidation-specific structure from generic volatility/regime effects.

A result that only reproduces ordinary high-volatility reversal behavior does
not falsify/support the liquidation-specific branch cleanly.

The E1 design is not acceptable without this control. This is blocking.

Recommended control direction:

- use a per-symbol matched-volatility baseline inside the same held-out window;
- match each directional liquidation event bucket against non-event intervals
  from the same symbol and broad time window;
- define volatility buckets from pre-event realized volatility before forward
  returns are inspected;
- compare E1-L and E1-S event results against their corresponding matched
  baseline, not only against all intervals.

This direction is preferred because prior Setup C work already treats regime
sensitivity as a first-class research risk, and Setup E's observed behavior
could otherwise be only a generic high-volatility reversal pattern.

## Gap Handling Requirement

- Timestamp gaps must be detected.
- Rows whose forward horizon crosses a disallowed gap must be handled by a
  pre-specified rule, not repaired after seeing results.
- Gap handling must be reported explicitly.
- No missing intervals may be fabricated.

The later implementation prompt must lock the exact maximum allowed timestamp
gap for 4h data and apply it uniformly before result interpretation.

## Candidate Event Definition

Liquidation intervals remain directional:

- long-dominant;
- short-dominant.

The formal cheap-falsification event rule is locked as:

- for each symbol independently, compute `total_liquidation_value`;
- define unusually large liquidation intervals as the top decile of
  `total_liquidation_value` within that symbol's eligible held-out window;
- classify long-dominant events where long liquidation value is greater than
  short liquidation value;
- classify short-dominant events where short liquidation value is greater than
  long liquidation value;
- exclude ties from E1-L and E1-S decisive buckets, but report their count.

This preserves the EXPLORE-style per-symbol top-decile threshold as the formal
cheap-falsification event rule. No multiple threshold sweeps or open-ended
search are allowed.

## Forward Horizons

Locked forward horizons:

- +4h
- +12h
- +24h

These match the previously observed coarse structure enough to formalize, but
are now precommitted for E1.

No extra horizons may be added during result interpretation.

## Primary Metrics

For each sub-hypothesis and locked horizon, report:

- event count;
- mean forward return;
- median forward return;
- positive-return share;
- confound-controlled comparison result.

This does not authorize a strategy PnL backtest.

## Cheap-Falsification Pass / Fail Criteria

E1 must assign exactly one result label:

- `E1_SUPPORTS_REVERSAL_HYPOTHESIS`
- `E1_INCONCLUSIVE`
- `E1_WEAK_OR_FAIL`

`E1_SUPPORTS_REVERSAL_HYPOTHESIS` requires:

- the relevant sub-hypothesis direction is consistent with reversal framing:
  E1-L positive/recovery-like, E1-S negative/decline-like;
- the effect is not merely a sign artifact and compares favorably against the
  mandatory volatility/regime confound-control baseline;
- at least one locked forward horizon shows coherent support without
  contradictory failure across all locked horizons;
- sample size is not trivially thin;
- gap-handling eligibility does not materially invalidate the bucket.

`E1_WEAK_OR_FAIL` applies if:

- directional sign is absent or opposite;
- or the result disappears against the confound-control baseline;
- or the bucket becomes unusable due to sparse data/gaps;
- or the structure is not coherent enough to justify further formal
  progression.

`E1_INCONCLUSIVE` applies to mixed or partially supportive structure that cannot
be cleanly classified as support or fail under the locked criteria.

These criteria intentionally avoid over-precise numeric thresholds at this
stage. They still constrain interpretation by requiring directional
consistency, baseline survival, usable sample size, and gap eligibility before
any support label.

## Anti-Cherry-Picking Rules

- no adding horizons after results;
- no changing thresholds after results;
- no merging E1-L and E1-S post hoc to rescue weakness;
- no selectively quoting only the stronger side;
- no reuse of EXPLORE window as validation evidence;
- no treating matched-volatility weakness as ignorable;
- no reading `E1_INCONCLUSIVE` as positive.

## Expected Outputs of Future E1 Implementation

A later implementation task, if owner-approved, should produce:

- one TXT report;
- one JSON report;
- explicit source/window metadata;
- sub-hypothesis-separated results;
- confound-control comparison;
- gap diagnostics;
- locked result label.

Exact output paths are not locked here.

## Non-Authorization

- no data retrieval now;
- no API calls now;
- no implementation now;
- no strategy backtest;
- no readiness promotion;
- no evidence claim now;
- no paper/runtime/trading/probe/live claim;
- no further Coinalyze exploratory tuning.

## Review Requirement

Independent review of this E1 design lock is required before any retrieval,
implementation, or analysis.

Human Owner approval is required after review.

Tower Control must verify that any future implementation prompt preserves:

- reversal framing;
- sub-hypothesis separation;
- confound-control requirement;
- held-out-window requirement;
- locked pass/fail logic;
- no reuse of the explored Coinalyze window.

## Next Allowed Step

Independent review of this E1 design lock.
