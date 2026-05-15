# Pre-E1 Decision Gate

## Purpose

This gate decides whether Setup E may advance to a later formal E1
cheap-falsification design-lock step.

It does not authorize E1 design lock creation in this task, data retrieval,
implementation, backtesting, or readiness claims.

## Current Setup E State

- Liquidation Cascades triage advanced to a hypothesis note.
- `SETUP_E_HYPOTHESIS.md` exists.
- Free-source verification found a coarse BTC daily path.
- BTC daily off-repo EXPLORE returned `EXPLORE_WEAK`.
- Richer-source survey found Coinalyze as a better mechanism-aligned path.
- Coinalyze source-selection note exists.
- Coinalyze 20-symbol 4h off-repo EXPLORE completed with orientation:
  `EXPLORE_MIXED`.
- Generic all-elevated liquidation bucket was not compelling.
- Directional split was more interpretable:
  - long-dominant liquidation intervals showed weaker recovery-like tendency;
  - short-dominant liquidation intervals showed clearer
    reversal/exhaustion-like negative follow-through at +12h and +24h.
- Independent recommendation:
  `GO_TO_PRE_E1_DECISION_GATE_WITH_REVERSAL_FOCUS`.

## Reframed Candidate Under Gate

The candidate now under decision is not generic "liquidations matter", but
specifically:

`Post-Liquidation Exhaustion Reversal`

Mechanism framing:

- after unusually large directional liquidation intervals, one-sided forced
  flow may become exhausted;
- post-event short-horizon price behavior may show reversal-like structure;
- this must be evaluated separately for:
  - long-dominant liquidation intervals;
  - short-dominant liquidation intervals.

## Why This Is Not Yet Evidence

- Both prior EXPLORE passes were non-evidence / non-validation.
- The Coinalyze result was exploratory, recent-window only, and
  source/interval bounded.
- Narrowing toward reversal/exhaustion occurred after exploratory observation
  and therefore must be formalized before any further data inspection.
- No evidence label or setup progression claim exists yet.

## Decision Question

Should Hephaestus open a formal E1 cheap-falsification design-lock path for
Post-Liquidation Exhaustion Reversal?

## Decision Outcomes

1. `PROCEED_TO_E1_REVERSAL_CHEAP_FALSIFICATION_DESIGN`
   - The reversal/exhaustion branch is mechanistically clear enough and
     exploratory enough to justify a later tightly scoped E1 design lock.

2. `HOLD_SETUP_E_FOR_ADDITIONAL_NON_DATA_CLARIFICATION`
   - The branch is still promising, but the research question or confound
     framing is not yet clean enough to open E1 design work.

3. `PARK_SETUP_E_AFTER_EXPLORE`
   - The exploratory findings are too weak or too ambiguous to justify a
     formal E1 path now.

## Gate Criteria

1. Mechanism clarity
   - Does post-liquidation exhaustion reversal have a concrete forced-flow
     story?

2. Branch clarity
   - Are long-dominant and short-dominant intervals distinct enough to preserve
     as separate sub-hypotheses rather than one pooled claim?

3. Explore support
   - Did the Coinalyze 20-symbol 4h EXPLORE provide enough directional
     structure to justify formalization, without treating it as evidence?

4. Confound awareness
   - Is the volatility/regime-proxy risk explicitly recognized as a mandatory
     formal-test control?

5. Data-path plausibility
   - Is there a plausible source path already identified for later formal E1
     planning, without authorizing retrieval here?

6. Falsifiability
   - Can a first cheap falsification be framed without becoming a hidden
     strategy backtest or open-ended optimization exercise?

## Required Future E1 Design Properties

If the gate recommends proceeding, any later E1 design lock must:

- commit to the reversal/exhaustion framing before further data inspection;
- treat long-dominant and short-dominant liquidation intervals as separate
  sub-hypotheses;
- specify a volatility/regime confound-control method or matched baseline;
- pre-specify gap-handling rules;
- require held-out / out-of-window and/or held-out-symbol validation before
  any evidence claim;
- avoid tuning on the already explored Coinalyze window;
- remain cheap-falsification reconnaissance, not a strategy backtest.

## Recommended Gate Outcome

`PROCEED_TO_E1_REVERSAL_CHEAP_FALSIFICATION_DESIGN`

This is recommended because the generic liquidation effect was weak, while the
directional reversal/exhaustion branch is more coherent and worth
formalization. Running further exploratory tuning first would raise
branch-selection bias, so a formal decision/design path is now cleaner than
more EXPLORE.

## What This Does Not Authorize

- no E1 design lock creation in this task
- no data retrieval
- no API call
- no Coinalyze rerun
- no additional EXPLORE on the same data
- no implementation
- no backtesting
- no evidence label
- no Setup E readiness promotion
- no paper/runtime/trading/probe/live claims

## Next Allowed Step

A docs-only E1 reversal cheap-falsification design lock may be prepared,
subject to Human Owner approval.
