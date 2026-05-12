# Research Candidate Backlog

## Purpose

A lightweight backlog for raw and triaged future signal-family candidates.
Backlog entries are not active project stages and do not authorize
implementation.

## Status Vocabulary

- watchlist
- triage-ready
- rejected
- advanced-to-hypothesis

## Candidate: Funding Carry / Funding Stress

- Candidate:
  Funding Carry / Funding Stress

- Signal family:
  Carry / funding

- One-line mechanism:
  Persistent or extreme positive perpetual funding may reflect crowded
  leveraged long demand; the contractual funding transfer and associated
  deleveraging pressure may create testable carry or stress effects.

- Potential payer / counterparty:
  Leveraged long-side demand paying funding and/or participants exposed to
  crowded directional positioning.

- Likely data:
  - funding-rate history;
  - OHLCV;
  - open-interest history if a later feasibility step supports it.

- Why it may matter:
  - structurally distinct from TSMOM / trend continuation;
  - not purely price-derived;
  - public data path appears plausible for at least funding history;
  - candidate mechanism is clearer than "indicator first" setup selection.

- Status:
  advanced-to-hypothesis

## Triage Result: Advance to hypothesis note

1. Mechanism clarity:
   Pass - funding transfers are contractual and positive extremes plausibly
   encode crowded leveraged long demand.

2. Counterparty clarity:
   Pass - long-side funding payers / crowded long participants are identifiable
   candidate payers.

3. Data feasibility:
   Pass with note - public funding history appears plausible; open-interest
   history requires later feasibility confirmation if used.

4. Cheap falsifiability:
   Pass - before a full backtest, check whether returns, liquidation-like
   stress proxies, or funding normalization behavior after funding extremes
   show a stable directional or carry-related skew.

5. Distinctness:
   Pass - this is a different signal family from Setup C TSMOM and the earlier
   price-action continuation family.

6. Expected edge above cost floor:
   Pass as plausible, not proven - funding magnitudes can be economically
   material enough to justify a hypothesis note, but this must be falsified
   later rather than assumed.

## What This Backlog Entry Does Not Authorize

- Setup D design lock
- SETUP_D_HYPOTHESIS.md creation in this task
- data downloads
- network calls
- API probing
- implementation
- paper/runtime/trading/live readiness claims

## Next Allowed Step

A mechanism-first hypothesis note may be created for this candidate:
`SETUP_D_HYPOTHESIS.md` subject to normal owner/Tower Control scope approval.
