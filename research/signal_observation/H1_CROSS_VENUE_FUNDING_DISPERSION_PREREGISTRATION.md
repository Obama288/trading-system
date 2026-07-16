# H1 Cross-Venue Funding Dispersion Preregistration

Status: PARKED / DATA FEASIBILITY / NO OUTCOME INSPECTION

Family: H1 / cross-venue perpetual funding dispersion
Research class: delta-neutral carry / relative value
Governing law: `docs/RESEARCH_CONSTITUTION.md` and `docs/BOUNDARIES.md`
Current gate: `docs/CURRENT_STATE.md` and
`research/signal_observation/RESEARCH_STATE.md`

This preregistration stopped at metadata-only data feasibility. The locked
coverage result found no admissible clean venue pair: Binance and Bybit passed
structural coverage, but Binance is ineligible because prior Setup D/F work
inspected its funding outcomes; Bitget and OKX had insufficient coverage. No H1
funding, spread, return, fee, or PnL outcome was inspected.

Coverage lock:
`research/signal_observation/H1_PHASE_A_COVERAGE_LOCK_2026_07_17.md`.
Coverage result:
`research/signal_observation/H1_PHASE_A_COVERAGE_RESULT_2026_07_17.md`.
Phase B and further H1 acquisition or analysis are forbidden under this record.
Unresolved `LOCK REQUIRED` fields are retained as historical preregistration
placeholders; they do not authorize reopening.

## 1. Hypothesis And Mechanism

### 1.1 One-sentence hypothesis

When economically equivalent linear perpetual contracts exhibit a persistent,
point-in-time observable difference in funding paid by the same directional
side, a matched long on the lower-cost venue and short on the higher-paying
venue will earn positive net carry over a locked holding rule after four-leg
fees, slippage, rebalancing, asynchronous settlements, and basis-tail losses.

### 1.2 Economic mechanism

Funding transfers arise because leveraged directional demand is unevenly
distributed across venues. Traders concentrated on the expensive side of one
venue pay to retain leveraged exposure. The proposed position supplies that
exposure while hedging common underlying-price delta on another venue.

The plausible payer is therefore the venue-specific population maintaining the
more expensive leveraged position, including traders constrained by collateral,
venue access, existing positions, or unwillingness to move exposure. The
strategy is not premised on predicting the absolute direction of the asset.

The mechanism is rejected as insufficient if the observed spread is merely a
measurement artifact caused by different contracts, settlement intervals,
index definitions, stale timestamps, delisting stress, or future-known funding.

## 2. Unit Of Analysis And Position Contract

One observation is one non-overlapping, fully closed two-venue episode:

1. both contracts pass the equivalence and data-quality gates;
2. a signal is computed using only information available at `decision_time`;
3. matched underlying delta is opened on both venues using the locked execution
   convention;
4. all funding cash flows and rebalances during the locked holding rule accrue;
5. both positions close under the locked exit rule;
6. net PnL is marked only after all four opening/closing fills and residual
   liabilities are accounted for.

No new episode may open for the same underlying and venue pair until the prior
episode is fully resolved. Episodes with an unclosed leg are operational
failures, not flats or missing observations.

The primary exposure unit is matched underlying quantity, not equal exchange
contract count. Initial target deltas must satisfy:

`abs(delta_long + delta_short) / mean(abs(delta_long), abs(delta_short)) <= D_max`

`D_max`: **LOCK REQUIRED before acquisition**.

Leverage, collateral allocation, rebalance tolerance, maximum holding duration,
and maximum unhedged interval are also **LOCK REQUIRED**. No liquidation-based
leverage optimization is permitted during research.

## 3. Venue Selection Without Outcome Shopping

### 3.1 Frozen candidate roster

The candidate venue roster is frozen to the venues already named in project
research and exchange work: Binance, Bitget, Bybit, and OKX. Adding, removing,
or substituting a venue after funding, basis, or return outcomes are inspected
requires a new preregistration and consumes another same-class attempt.

### 3.2 Metadata-only eligibility

A venue is eligible only if all of the following can be established without
inspecting strategy outcomes:

- free public point-in-time funding settlements and required price fields exist
  for every locked window;
- a separate named, non-overlapping holdout path is available before discovery;
- timestamps, revisions, symbol lifecycle, and contract specifications can be
  reconstructed without future information;
- the contract passes Section 4 equivalence;
- data can be acquired within the owner's no-spend constraint;
- terms permit the intended local research use;
- a conservative fee schedule and capacity evidence can be bound point in time.

### 3.3 Deterministic pair rule

Exactly one primary venue pair is tested. Before any candidate funding or price
outcome is downloaded, an eligibility table must be committed for the frozen
roster. Rank eligible pairs by these metadata-only keys, in order:

1. complete overlap across all locked windows;
2. fewest missing or ambiguous required fields;
3. fewest contract-specification changes requiring reconstruction;
4. lexical order of the canonical venue tuple as the final tie-breaker.

The first pair is the primary pair. Funding magnitude, spread, historical PnL,
volatility, basis behavior, popularity, and testnet convenience must not enter
selection. If fewer than two venues qualify, H1 is PARKED before outcome
inspection. A runner-up pair is holdout metadata only and cannot become a rescue
variant after the primary result.

The metadata-only coverage decision selected no pair. Bybit was the only clean
venue with full structural coverage. Binance passed coverage but was already
contaminated for H1 validation/holdout; Bitget and OKX lacked coverage. The
required clean `Bitget + Bybit` pair was therefore unavailable and H1 was
parked before outcome inspection.

## 4. Contract Equivalence

The primary variant uses exactly one underlying and one contract type.
Underlying: **LOCK REQUIRED**. The choice must be made before outcome download
using operational relevance and complete free-data eligibility, not observed
funding spread.

Both legs must be:

- perpetual, linear, and quoted/settled in USDT;
- referenced to the same underlying asset and economically comparable index;
- free of delivery or expiry optionality;
- mapped to underlying quantity using point-in-time contract multipliers;
- active and normally tradable at the decision and exit timestamps;
- supported by point-in-time tick size, quantity step, minimum notional,
  funding schedule, fee schedule, and symbol-status history.

Inverse, coin-margined, dated futures, quanto, leveraged-token, and differently
collateralized contracts are excluded from the primary variant. A contract
rename or multiplier change is a boundary: it must be reconstructed from
point-in-time metadata or the affected interval is excluded before locking
window hashes. Survivorship-only symbol lists are forbidden.

Equivalence does not mean identical mark/index construction. Differences must
be recorded and treated as basis risk. If index constituents or mark formulas
cannot be reconstructed sufficiently to prevent false spread signals, PARK H1.

## 5. Funding Normalization

### 5.1 Canonical sign

For each venue and settlement event, store the actual interval rate `r` as a
decimal and normalize the sign so positive `r` means longs pay shorts:

- long cash flow: `CF_long = -r * funding_notional`;
- short cash flow: `CF_short = +r * funding_notional`.

Venue-native signs must be mapped explicitly and tested. Raw rates, normalized
rates, settlement timestamps, interval duration, funding notional definition,
and source timestamp must all be retained.

### 5.2 Time normalization

Annualized rates may be used only for comparability and diagnostics:

`r_annualized = r_interval * (24 / interval_hours) * 365`

Economic PnL uses actual settlement cash flows on each venue's actual schedule,
never an annualized-rate approximation. Asynchronous settlements remain
separate events. Rates must not be forward-filled through an unknown schedule
or silently converted to a nominal eight-hour interval.

### 5.3 Point-in-time signal

The signal may use only funding information published and knowable by
`decision_time`. A final settled rate cannot be used to enter before its own
settlement timestamp. If free history contains only final rates and cannot
prove when a predictive value was observable, the primary signal must use only
prior completed settlements. Using retrospectively finalized next-funding
estimates is forbidden.

The exact persistence estimator, entry threshold, decision cadence, holding
rule, and exit rule are **LOCK REQUIRED** after metadata feasibility and before
outcome acquisition. There will be one primary setting only. No threshold grid,
best interval, or best settlement alignment may be searched.

## 6. Primary Metric And Economic Gate

Exactly one primary metric will be used:

`mean_net_return_bps_on_gross_notional` over all non-overlapping completed
episodes under the moderate cost scenario.

For episode `i`:

`net_return_bps_i = 10,000 * net_pnl_i / initial_gross_notional_i`

where `initial_gross_notional` is the sum of absolute opening notionals of both
legs. Unresolved episodes are conservatively closed using the locked failure
rule and cannot be dropped.

The numeric Stage 2 promotion threshold and required margin over the random
baseline are **LOCK REQUIRED**. They must be economically positive after the
capacity floor and may not be chosen after seeing any H1 outcome. Until those
numbers are committed, this document cannot pass Stage 1.

Diagnostics such as annualized return, Sharpe ratio, hit rate, maximum drawdown,
funding-only PnL, basis-only PnL, venue breakdowns, and optimistic/conservative
cost scenarios cannot promote H1.

## 7. Four-Leg Cost And PnL Contract

Every episode includes two opening fills and two closing fills. For matched
notional `N`, the minimum round trip is:

`net_pnl = funding_cashflows`
`          + long_perp_price_pnl + short_perp_price_pnl`
`          - open_long_cost - open_short_cost`
`          - close_long_cost - close_short_cost`
`          - rebalance_costs - residual_liabilities`

Each fill cost includes the point-in-time fee plus modeled slippage on that
venue. The constitutional all-in floors apply per fill:

| Scenario | Taker fee plus slippage floor per fill |
|---|---:|
| Optimistic | 5 bps of fill notional |
| Moderate / primary | 8 bps of fill notional |
| Conservative | 15 bps of fill notional |

If the point-in-time venue fee plus defensible slippage assumption is higher
than the scenario floor, the higher value is used. Maker rebates are zero in
the primary test. A maker-fill variant is not permitted. Transfer costs are not
assumed away: the primary design uses pre-positioned collateral and records
collateral opportunity/operational constraints separately; any actual transfer
required by the rule must be costed.

Rebalances add their own fee and slippage on every fill. Funding is calculated
from venue-defined funding notional at each settlement. Liquidations, clawbacks,
ADL, outage exits, stale marks, and stranded collateral are not ordinary
slippage; they belong to explicit stress and STOP/PARK gates.

No zero-cost result may appear except as a labeled diagnostic.

## 8. Basis-Tail And Capacity Gates

These gates are feasibility and survivability requirements, not post-hoc
filters for improving returns.

### 8.1 Basis-tail gate

Before Stage 2, lock:

- maximum allowed entry cross-venue basis;
- maximum adverse basis move compatible with collateral buffers;
- stale-mark and venue-outage treatment;
- forced-close price rule when one venue is unavailable;
- maximum tolerated unhedged interval;
- whether an observed ADL, delisting, or contract discontinuity retires the
  episode or the family.

Numeric limits are **LOCK REQUIRED**. If a conservative joint stress of adverse
basis movement, one-leg outage, fees, and slippage can liquidate either leg at
the locked leverage, H1 is PARKED until a safer unlevered/collateral design is
preregistered. Tail episodes may not be removed merely because they dominate
losses; concentration in outage, delisting, or extreme-basis events is a cheap
kill condition for the mechanism as deployable carry.

### 8.2 Capacity gate

`C_min`, the minimum executable matched notional per leg, is **LOCK REQUIRED**
before outcome acquisition and must reflect an economically meaningful future
deployment size chosen by the owner, not the best size visible in history.

At every simulated entry and exit, both legs must support `C_min` under the
locked conservative fill model. Capacity is the minimum executable capacity of
the two legs, after quantity steps and minimum notionals. If point-in-time depth
or a defensible conservative proxy is unavailable, H1 is PARKED; testnet fills
cannot substitute for mainnet capacity evidence.

Capacity failures remain failures. Reducing size, changing asset, changing
venue pair, or selecting only liquid-looking outcomes after inspection requires
a new preregistration.

## 9. Windows, Holdout, And Data Binding

The exact UTC date boundaries are **LOCK REQUIRED** after metadata-only coverage
inspection and before candidate outcome acquisition. The required structure is:

| Stage | Locked path | Rule |
|---|---|---|
| Discovery | Primary pair, earliest locked window | Used only for Stage 2 |
| Validation | Same pair, later non-overlapping window | Touched exactly once |
| Recent holdout | Same pair, most recent complete 12 months | Stage 4; untouched until Stage 3 passes |

All three paths must be named and confirmed available before discovery. No
post-hoc split of an inspected window is allowed. If prior project work has
already exposed a proposed window or influenced its specification, that window
must be recorded as contaminated and cannot serve as validation or recent
holdout.

Every venue/contract dataset and metadata file will be SHA-256 bound. Required
quality reports cover UTC ordering, duplicates, gaps, settlement schedule,
unclosed records, symbol lifecycle, mark/index sanity, funding sign, revisions,
and cross-venue timestamp alignment. Any gap inside a locked window is resolved
before outcome calculation or causes the affected window to fail.

Stage minimums default to at least 80 non-overlapping discovery episodes and 40
validation episodes. The recent holdout must also meet a numeric minimum:
**LOCK REQUIRED**. Failure to reach a minimum is a failure, not permission to
expand symbols, venues, thresholds, or dates.

## 10. Random Baseline

Seed: `69`.

The exact baseline is **LOCK REQUIRED**, with the intended form being a
timestamp-, duration-, venue-pair-, and gross-exposure-matched placebo that
randomly assigns the economically feasible long/short venue orientation without
using future funding. Number of resamples and the numeric required margin are
also **LOCK REQUIRED**.

The baseline must preserve funding schedules, tradability, costs, and basis
exposure. A baseline that omits four-leg costs or samples impossible timestamps
is invalid.

## 11. Discovery, Validation, And Holdout Procedure

### Stage 2 - Discovery

Run the single locked primary variant once on the discovery window. Promotion
requires all of the following:

- the primary metric clears its locked, multiplicity-adjusted threshold;
- it clears the locked baseline margin;
- `N >= 80` non-overlapping completed episodes;
- capacity and basis-tail gates pass;
- no look-ahead or data-quality red flag remains unresolved.

### Stage 3 - Validation

Run once on the locked validation window without changing code, parameters,
pair, contract, costs, or accounting. Promotion requires non-negative post-cost
primary expectancy, consistent effect direction, `N >= 40`, and no red flag.
A second look is a new preregistration.

### Stage 4 - Recent holdout

Run once on the untouched most recent complete 12-month window. Promotion
requires non-negative post-cost primary expectancy, the locked minimum count,
capacity/basis-tail compliance, and no concentration red flag. A PASS means
not-yet-rejected, not proven profitability or readiness.

No paper stage is permitted until authoritative paper accounting can represent
fees, funding, slippage, gross/net realized PnL, and equity movement.

## 12. Multiplicity Budget

H1, H2, and H6 share the carry/basis search surface and are not independent.
Prior funding normalization work and Setup D funding carry-stress work must be
entered in the campaign ledger before lock. The following counts are therefore
**LOCK REQUIRED**:

- `N_attempts`: all locked attempts on this data class;
- `N_considered_discarded`: material carry/funding ideas considered but not
  locked;
- the Bonferroni-style discovery adjustment required by the constitution.

The primary H1 variant budget is intended to be exactly:

- one underlying;
- one deterministic venue pair;
- one contract type;
- one decision cadence;
- one persistence estimator;
- one entry threshold;
- one exit/holding rule;
- one rebalance rule;
- one moderate-cost primary scenario.

Thus the within-document primary `V = 1`. Diagnostics do not create promotion
rights. Any alternate symbol, pair, threshold, holding duration, funding
estimator, maker assumption, regime, session, or capacity tier is another look.
It may be described only as Stage 0 material under a new preregistration and
cannot rescue H1.

## 13. Mandatory Look-Ahead Audit

Before acquisition and again before every result, independently verify:

- funding used by the signal was published before `decision_time`;
- revised or final next-funding values did not replace point-in-time values;
- settlement schedules and interval changes are effective-dated;
- contract multipliers, fees, tick sizes, and symbol status are point in time;
- current exchange metadata did not leak into historical eligibility;
- no delisted symbol or failed venue interval was removed by survivorship;
- marks, indices, and depth snapshots precede the simulated order;
- execution uses the next actionable timestamp, not the signal-defining price;
- asynchronous venue clocks do not use the later venue's future event;
- window, pair, underlying, threshold, and costs were not selected from outcomes;
- validation and recent holdout hashes were not opened during discovery;
- capacity and tail filters were fixed before return inspection.

Any unresolved item blocks the run. A surprising positive result triggers a
fresh audit before interpretation.

## 14. STOP, PARK, And Retirement Rules

### PARK before outcomes

PARK H1 without backtesting if any of the following occurs:

- fewer than two equivalent venues have a free aligned point-in-time path;
- discovery, validation, and recent holdout cannot all be named upfront;
- funding observability cannot be made look-ahead clean;
- contract or symbol lifecycle cannot be reconstructed;
- four-leg cost, capacity, or basis-tail parameters cannot be locked;
- point-in-time capacity evidence or a defensible conservative proxy is absent;
- Stage 1 numeric fields, multiplicity ledger, hashes, or independent review are
  incomplete;
- required work would violate the no-spend or safety constraints.

### STOP after a run is authorized

STOP and RETIRE this preregistered variant if:

- the Stage 2 primary gate or baseline margin fails;
- discovery has fewer than 80 valid non-overlapping episodes;
- Stage 3 expectancy is negative, direction reverses, or `N < 40`;
- Stage 4 expectancy is negative or its locked minimum count fails;
- apparent profit depends on excluded tail losses, a few outages/delistings, or
  capacity below `C_min`;
- a material look-ahead, accounting, sign, or contract-equivalence error makes
  the evidence non-reconstructable.

A correctable implementation defect discovered before outcomes may return the
document to DRAFT. After outcomes are seen, changing a substantive rule requires
a new preregistration and increments the cumulative attempt budget.

## 15. Separate Role Of Testnet / Demo

Testnet is an implementation and recovery lane, not an economic evidence lane.
It may eventually test:

- authenticated API signing and point-in-time contract filters;
- two-leg sequencing and the locked maximum unhedged interval;
- partial fill, reject, cancel/replace, and idempotent retry behavior;
- hedge repair after one-leg success and second-leg failure;
- funding-event ingestion and normalized sign handling;
- independent collateral, position, and execution reconciliation;
- disconnect, restart, stale order, and kill-switch behavior;
- safe refusal when contract equivalence or account state is uncertain.

Testnet cannot validate real funding distributions, mainnet spread persistence,
queue position, fill probability, slippage, depth, capacity, basis tails,
counterparty risk, or net edge. A green testnet cannot promote Stage 2-4 and a
failed testnet does not falsify the economic hypothesis; it blocks engineering
readiness until corrected.

Any testnet credential use, private endpoint call, order, cancel, runtime wiring,
or smoke run requires a separate explicit Protected Lane owner authorization.
Current Bybit testnet and Bitget demo gates remain unchanged by this parked record.

## 16. Data-Feasibility Decision Boundary

H1 is `PARKED / DATA FEASIBILITY / NO OUTCOME INSPECTION`. Binance and Bybit
passed structural coverage, but Binance cannot supply untouched validation or
holdout evidence after prior funding-outcome inspection. Bitget and OKX had
insufficient historical coverage, so the locked clean `Bitget + Bybit` pair is
unavailable.

Phase B, H1 analysis, pair substitution, shifted windows, shortened holdout,
paper progression, and readiness claims are forbidden. Reopening H1 requires a
genuinely new contamination-safe free source or a new owner decision changing
the no-spend constraint, followed by a new preregistration gate.
