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

## Sideways Candidate Map Addendum

These entries are triage-ready / candidate-map only. They do not authorize
screening, acquisition, analysis, EXPLORE, validation, implementation, or
readiness. See `research/signal_observation/SIDEWAYS_FAMILY_NOTE.md`.

### Funding Normalization

- Branch:
  Sideways Carry / Normalization
- Mechanism:
  In statistically sideways regimes, displaced perpetual funding may normalize
  as crowded leverage pressure decays; this is funding/positioning
  normalization, not naive range trading.
- Counterparty:
  Leveraged directional traders paying funding and crowded participants holding
  exposure through funding resets.
- Data/source feasibility:
  Already-acquired D1 funding data is a possible future input, but D1 analysis
  remains HOLD; SOLUSDT variable intervals remain retained/flagged.
- Harness template:
  Continuous-State.
- Status:
  DISCOVERY_DONE_WEAK_HOLD_FOR_BROADER_PAIRS
- Discovery result:
  Overall label NORMALIZATION_SCREEN_WEAK (commit d770553). Strong anomaly:
  false. Blockers: none. Held-out protected. Reviewer verdict: NO-GO for
  validation. HIGH branch cap-contaminated (p70=p80=0.0001; median Δf=0).
  LOW branch directionally coherent but below 9 bps normalization magnitude
  floor (largest: ETH LOW W8 = 1.18 bps). Future broader-pairs work requires
  source feasibility, new pre-registration, and separate Owner authorization.
- LOW-side broader-pairs source feasibility:
  `research/signal_observation/LOW_SIDE_FUNDING_NORMALIZATION_BROADER_PAIRS_FEASIBILITY.md`.
  Label: BROADER_PAIRS_FEASIBILITY_PLAUSIBLE (qualified; new acquisition required
  for any broader pair; per-pair coverage unconfirmed).
- Signal half-life: hours to days.
- Maximum acceptable decision delay: hours to days; human-in-loop acceptable.
- Human-in-loop allowed: yes.
- Automation required before paper/live: not required for research phase.
- Missed-signal impact: low to moderate; missed cycles are recoverable.
- Operational fit: latency-tolerant.

### Basis / Cash-and-Carry

- Branch:
  Sideways Carry / Normalization or Cross-Venue Dislocation
- Mechanism:
  Spot-perpetual or spot-futures dislocations may normalize when financing
  demand, leverage pressure, or arbitrage imbalance mean-reverts in sideways
  regimes.
- Counterparty:
  Leveraged directional traders paying for synthetic exposure and/or
  participants slow to arbitrage spot-versus-derivative dislocations.
- Data/source feasibility:
  Requires spot prices, derivative prices, derived basis or spread series, and
  OHLCV regime context; source feasibility is not authorized by this entry.
- Harness template:
  Continuous-State or Cross-Venue Dislocation.
- Status:
  triage-ready / candidate-map only
- Signal half-life: hours to days.
- Maximum acceptable decision delay: hours to days; human-in-loop likely
  acceptable pending source and framing confirmation.
- Human-in-loop allowed: likely yes pending framing.
- Automation required before paper/live: not required for research phase.
- Missed-signal impact: low to moderate.
- Operational fit: latency-tolerant.

### Cross-Asset Spread Mean Reversion BTC/ETH/SOL

- Branch:
  Sideways Relative-Value / Range Behavior
- Mechanism:
  Relative-value spreads among BTC, ETH, and SOL may normalize during sideways
  regimes when idiosyncratic displacement is not supported by broader market
  direction.
- Counterparty:
  Crowded single-asset allocators, relative-value laggards, or hedgers paying to
  rebalance under flat index conditions.
- Data/source feasibility:
  BTC/ETH/SOL OHLCV and derived spread or ratio series may be plausible future
  inputs, but no spread construction or analysis is authorized.
- Harness template:
  Continuous-State.
- Status:
  triage-ready / candidate-map only
- Signal half-life: hours to days.
- Maximum acceptable decision delay: hours to days; human-in-loop likely
  acceptable pending framing confirmation.
- Human-in-loop allowed: likely yes pending framing.
- Automation required before paper/live: not required for research phase.
- Missed-signal impact: low to moderate.
- Operational fit: latency-tolerant to medium.

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
