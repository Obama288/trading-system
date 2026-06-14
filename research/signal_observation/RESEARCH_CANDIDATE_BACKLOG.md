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
- parked-stage2 (Stage 2 discovery complete; gate miss; family parked per §2.7)

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
  parked-stage2

- Stage 2 result (2026-06-13):
  Tested as "Setup E / Post-Liquidation Exhaustion Reversal" on Coinalyze 4H
  liquidation data, 20-symbol universe, discovery window ≤ 2026-03-09T00:00Z.
  GATE PARK: primary expectancy_R = −0.1085R at 1.5R (moderate 8 bps),
  non-overlapping N=824. Both gate criteria unmet. Decision record:
  `SETUP_E_DECISION_RECORD.md`. One re-registration permitted only with a
  materially different mechanism statement (e.g. continuation, not reversal).

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

---

## Selected Candidate Set — 2026-06-14

Status: owner-selected post-Setup-I plan. Four candidates advanced (#1, #4, #6,
#7). Two considered-and-parked for the v1.4 comparison budget (see below). Total
ideas considered this round: 7; plus 8 prior families = large cumulative look-count;
gates must reflect it.

Sequencing rationale: #6/#7 are fast (data mostly on hand, simcore nearly fits)
and give an early read on whether the funding/leverage angle has any life. #1 is
the deep bet with the real edge but needs an on-chain pipeline built first (weeks).
#4 needs new measurement (continuous PnL). Proposed order: start #7 or #6 first;
build #1's pipeline in parallel as background work; #4 after.

### Considered-and-parked (v1.4 comparison budget)

- **#2 Stablecoin emission / macro:** Parked — macro signal without a forced-flow
  counterparty; mechanism too diffuse to distinguish from broad risk-off; no clean
  falsification path available.
- **#5 Listing front-run:** Parked — look-ahead contamination is structural; clean
  point-in-time listing-date data is unavailable; edge is likely already arbitraged
  by better-informed parties.

### #1 — Vesting-wallet on-chain tracking (event-driven + on-chain)

THE edge bet. Mechanism: track actual movement of tokens FROM vesting contracts TO
exchange deposit addresses on-chain, ahead of the price effect of an unlock.
Counterparty: early investor preparing to sell. Data: raw blockchain (Dune/nodes,
free but laborious) + vesting-contract registry.

**Difficulties, thought through before starting**

- **Look-ahead in wallet labeling is the killer.** An address is "an exchange
  deposit wallet" only as labeled TODAY. Using today's labels on past data embeds
  knowledge that did not exist then. Must reconstruct labels as-of the decision
  time — extremely easy to get wrong, extremely hard to detect once wrong. This
  single issue can silently invalidate the whole family.
- **Vesting schedules get revised retroactively.** Projects move vesting. A backtest
  on current schedules trades on revised dates. Need point-in-time schedule
  snapshots, which may not exist historically.
- **Data engineering is the project, not a step.** Parsing, clustering, normalizing
  raw chain data is weeks of work before the FIRST hypothesis test. Risk of sinking
  time into a pipeline that then shows no edge.
- **Chain coverage fragmentation.** Tokens live on Ethereum, BSC, Solana, Arbitrum,
  Base — each a different data source. Scope to one chain (likely Ethereum) first.
- **Free-tier limits.** Dune/RPC free tiers throttle hard; full historical queries
  may hit limits or need paid tiers — re-introducing the cost question.
- **Survivorship in the token set.** Backtesting only on tokens that still exist
  ignores the ones that died — dead tokens are exactly where unlocks dumped hardest.
  Must include delisted/dead tokens or the result is rosy-biased.

### #4 — Funding harvest, delta-neutral carry (class #4)

Portfolio stabilizer, not alpha. Mechanism: long spot / short perp (or inverse) to
capture funding while staying direction-neutral. Counterparty: whoever pays for
leveraged exposure. Data: funding + spot + perp (mostly on hand).

**Difficulties, thought through before starting**

- **simcore cannot measure this.** Continuous PnL + inventory + funding accrual, no
  entry/stop/target. Needs a NEW measurement module, not a detector. Decide if it is
  worth building before committing.
- **The carry is not free money — it has a fat left tail.** Funding harvest looks like
  steady income until a violent move blows out the basis or one leg gets liquidated.
  The risk is rare large loss, exactly what a naive "collect funding" backtest
  understates. Must model leg-liquidation and basis-blowout explicitly.
- **Execution is two-legged.** Requires holding spot AND perp simultaneously,
  rebalancing both, on possibly different venues — operationally heavier than a single
  directional position. Slippage on both legs.
- **Funding is already harvested by many.** The plain trade is crowded; residual yield
  may be thin after costs. Edge, if any, is in selection (which instrument, when),
  which reintroduces a search and its multiplicity cost.

### #6 — Cash-and-carry basis on thin alts (class #3)

Mechanism: carry (spot vs perp) as a hold on less-liquid alts where basis is wider
than the cost-killed 4 bps of majors (Setup F). Counterparty: leveraged longs on an
overheated thin-alt perp. Data: spot+perp alts (free).

**Difficulties, thought through before starting**

- **The cost wall moves WITH you on thin alts.** Wider basis is offset by wider spread
  and worse slippage — the very thinness that gives edge also taxes entry/exit. The
  cost test must use REALISTIC fills on thin books, not the 8 bps major assumption.
  Likely the make-or-break issue.
- **Capital ceiling is low.** Thin alts can absorb little size before you move the
  market against yourself. Even a real edge may be uninvestable above a small notional.
- **Liquidation / delisting risk on the alt itself.** Thin alts get delisted, have
  funding spikes, exchange-specific halts. The "neutral" position is not neutral to
  instrument-specific blowups.
- **Same simcore-fit problem as #4** (continuous carry PnL).

### #7 — Funding-extreme as contrarian squeeze signal (class #1, directional)

Fast first test. Mechanism: at historical funding extremes one side of the perp is
maximally overheated and squeeze-prone; catch the reversal. Counterparty: the
over-leveraged crowd at peak positioning. Data: funding + OHLCV (on hand).

**Difficulties, thought through before starting**

- **It is the 9th directional family.** Red review applies in full: the class is under
  heavy suspicion. The v1.4 multiplicity-adjusted gate will be strict — a modest edge
  may not clear it. Go in expecting a high bar.
- **"Funding extreme" is a tunable threshold.** Percentile choice is a
  selection-bias surface. Must pre-register the threshold, not tune it.
- **Overlaps conceptually with Setup E (liquidations).** Risk of re-testing the same
  forced-flow reversal under a different trigger and calling it new. Be honest that
  the mechanism family is adjacent; the budget counts it.
- **Cheapest to run, so cheapest to mislead.** Easy data + easy signal = easy to fool
  yourself with an overfit. The discipline (baseline, held-out) matters most exactly
  where the test is easiest.

### Cross-cutting difficulties (apply to all four)

1. **Look-ahead is the recurring assassin.** It appears in every class: wallet labels
   (#1), revised schedules (#1), tuned thresholds (#7), survivorship (#1, #6). It is
   subtle, silent, and invalidates results after the fact. Every feasibility from now
   on must include an explicit look-ahead audit step.
2. **Cost/slippage realism breaks the cheap assumption.** The 8 bps flat is fine for
   BTC/ETH majors and wrong everywhere else (#6 thin alts, #4 two-legged). Real fills
   must replace the assumption once any of these advances.
3. **simcore measures only signal-stop-target.** #4 and #6 (continuous carry) need new
   measurement infrastructure. Choosing only what simcore fits would be
   lamppost-searching (red review #3). Budget for building measurement, not just
   detectors.
4. **Crowdedness vs edge.** #4, #6, #7 are variations of known trades; their residual
   edge after crowding may be thin. Only #1 has a structural edge (self-collected data)
   and #1 is the most expensive to build. There is no free lunch here.
5. **Time/attention is the real scarce resource.** Four candidates + an on-chain
   pipeline is a lot. Running too many in parallel inflates the comparison budget AND
   splits focus. Discipline: one fast track (#7 or #6) + one slow build (#1) at a
   time; do not open all four at once.
6. **The motivation trap (red review #6).** Building elaborate pipelines feels like
   progress. A perfect on-chain pipeline that finds no edge is still no edge. Set a
   kill-date on #1's build so love of the work does not become a sunk-cost trap.

### Proposed order (owner decides after Setup I)

1. **#7 first** — fastest, data on hand, early read on the funding/leverage angle.
   Accept the strict v1.4 gate; expect possible PARK.
2. **#1 pipeline build in parallel** — slow background, with a kill-date.
3. **#6 after #7** — needs realistic thin-alt cost modeling built first.
4. **#4 last** — needs continuous-PnL measurement; treat as portfolio stabilizer.
