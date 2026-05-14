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

## Candidate: Liquidation Cascades

- Candidate:
  Liquidation Cascades

- Signal family:
  Forced deleveraging / liquidation

- One-line mechanism:
  Large forced liquidations may create short-lived directional flow and
  continuation or overshoot effects because positions are closed mechanically
  rather than discretionarily.

- Potential payer / counterparty:
  Leveraged traders being forcibly liquidated and liquidity takers absorbing
  one-sided forced flow.

- Likely data:
  - liquidation event history or liquidation intensity proxies;
  - OHLCV;
  - possibly open interest later if feasibility supports it.

- Why it may matter:
  - forced behavior is more mechanistic than generic indicator drift;
  - structurally distinct from TSMOM and funding carry;
  - plausible public-data path may exist, but must be verified later.

- Status:
  triage-ready

## Candidate: Basis / Cash-and-Carry Dislocation

- Candidate:
  Basis / Cash-and-Carry Dislocation

- Signal family:
  Basis / cross-market carry

- One-line mechanism:
  Spot-perpetual or spot-futures dislocations may reflect leverage demand,
  financing stress, or arbitrage pressure that creates testable mean-reversion
  or persistence behavior.

- Potential payer / counterparty:
  Leveraged directional traders paying for synthetic exposure and/or
  participants slow to arbitrage spot-versus-derivative dislocations.

- Likely data:
  - spot prices;
  - perpetual/futures prices;
  - derived basis or spread series;
  - OHLCV.

- Why it may matter:
  - not purely price trend;
  - related to structural market segmentation and financing pressure;
  - distinct from funding-only Setup D.

- Status:
  triage-ready

## Candidate: Options Expiry / Dealer Hedging Pressure

- Candidate:
  Options Expiry / Dealer Hedging Pressure

- Signal family:
  Options / hedging-flow

- One-line mechanism:
  Concentrated options expiry positioning may create predictable hedging or
  pinning pressure in underlying markets around expiry windows.

- Potential payer / counterparty:
  Dealers or market makers dynamically hedging concentrated gamma exposure,
  and participants positioned into expiry-related flows.

- Likely data:
  - options expiry calendar;
  - options open interest / positioning summaries if publicly available;
  - underlying OHLCV;
  - data feasibility requires later verification.

- Why it may matter:
  - structurally distinct from TSMOM, funding, and liquidation flow;
  - mechanism is tied to forced or semi-forced hedging behavior;
  - may open a genuinely new family if public data feasibility is acceptable.

- Status:
  triage-ready

## Backlog Intake Note

- Backlog status does not mean data feasibility is confirmed.
- No candidate is promoted to hypothesis note by this edit alone.
- Future Tower Control must triage before advancing any candidate.
- This backlog edit does not authorize data work, network calls, EXPLORE runs,
  design locks, implementation, or readiness claims.
