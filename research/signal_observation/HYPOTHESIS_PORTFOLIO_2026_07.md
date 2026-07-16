# Hypothesis Portfolio - July 2026

Status: DRAFT / PLANNING

Purpose: compare genuinely different trading mechanisms before opening another
research family. This note authorizes no data acquisition, screening, exchange
call, testnet action, implementation, paper progression, or trading.

Governing documents:

- `docs/RESEARCH_CONSTITUTION.md`
- `docs/BOUNDARIES.md`
- `docs/CURRENT_STATE.md`
- `research/signal_observation/RESEARCH_STATE.md`

## Decision Principle

The project has tested many directional crypto-perpetual families and has not
established a current edge. The next candidate should preferably earn from a
contractual transfer or relative-value dislocation rather than another forecast
of absolute price direction.

Every candidate must identify:

1. the economic transfer or forced behavior;
2. the party plausibly paying;
3. point-in-time information available before the decision;
4. a conservative all-in cost floor;
5. a cheap condition that kills the idea before a full backtest.

## Evidence Lanes

The following lanes answer different questions and must not be merged.

| Lane | Question answered | Valid evidence |
|---|---|---|
| Historical real-market data | Did the mechanism exist after costs? | Mainnet public or committed point-in-time data |
| Local replay/simulation | Is the test look-ahead clean and reproducible? | Deterministic code, locked inputs, conservative cost model |
| Live paper on real public data | Does signal timing work prospectively? | Mainnet market observations with simulated fills |
| Testnet/demo | Can the system execute and recover safely? | API, orders, partial fills, positions, funding events, reconnect, reconciliation |
| Live capital | Does deployable net PnL survive real execution? | Not authorized |

Testnet/demo results are implementation evidence, not evidence of edge. A demo
environment using live-looking prices still may have simulated fills, different
participants, different liquidity, and non-representative funding or basis.

## Shortlist

Scores use 1 = poor and 5 = strong. They are planning judgments, not research
results.

| ID | Candidate | Class | Mechanism | Free-data path | Cheap falsification | Testnet value | Operational fit |
|---|---|---|---:|---:|---:|---:|---:|
| H1 | Cross-venue perpetual funding dispersion | Delta-neutral carry | 5 | 3 | 4 | 5 | 3 |
| H2 | Single-venue spot-perpetual funding harvest | Delta-neutral carry | 5 | 4 | 4 | 5 | 3 |
| H3 | Beta-neutral cross-sectional residual reversion | Relative value | 3 | 5 | 5 | 4 | 4 |
| H4 | Funding-settlement event dislocation | Event-driven directional | 3 | 4 | 5 | 3 | 4 |
| H5 | Price/order-flow divergence (Setup I) | Directional microstructure | 4 | 3 | 3 | 3 | 3 |
| H6 | Thin-alt cash-and-carry basis | Delta-neutral carry | 4 | 3 | 3 | 5 | 2 |

H1, H2, and H6 share a carry/basis search surface. They are not three
independent discoveries. Testing one and then selecting another after seeing
its outcome consumes the same-family multiplicity budget and requires a fresh
preregistration.

## H1 - Cross-Venue Perpetual Funding Dispersion

Hypothesis: when equivalent perpetual contracts have a persistent funding-rate
difference across venues, a delta-neutral long on the lower-paying side and
short on the higher-paying side earns the funding spread after all four legs,
rebalancing, and basis risk.

Economic transfer: venue-specific leveraged demand pays funding.

Plausible payer: traders concentrated on the venue and side with more expensive
leveraged exposure.

Required real-market data:

- point-in-time funding rates and settlement intervals for at least two venues;
- synchronized mark/index/perpetual prices;
- contract specifications and symbol lifecycle;
- conservative fee and slippage assumptions per venue;
- one untouched venue or later time window for validation.

Cheap kill conditions:

- no free point-in-time aligned history with a protected holdout;
- median available spread cannot clear four-leg round-trip costs plus a safety
  margin;
- spread half-life is too short for non-HFT two-leg execution;
- apparent yield is concentrated in delisting, outage, or extreme basis events;
- practical capacity is too small to matter.

Testnet role:

- two-leg sequencing and maximum unhedged interval;
- partial-fill hedge behavior;
- cancel/replace and idempotency;
- independent collateral and position reconciliation;
- funding-event ingestion;
- disconnect and one-leg recovery.

Testnet cannot establish the real funding distribution, fill probability,
slippage, capacity, or counterparty risk.

## H2 - Single-Venue Spot-Perpetual Funding Harvest

Hypothesis: hold spot and the opposite perpetual leg only when expected funding
over a locked holding horizon exceeds entry, exit, rebalance, and basis-tail
costs by a preregistered margin.

Economic transfer: leveraged perpetual traders pay funding to the hedged
position.

Plausible payer: persistent directional leverage demand.

Why it is not "always collect funding": entry requires a locked yield margin,
minimum persistence, and explicit basis/liquidation stress limits.

Cheap kill conditions:

- historical net carry is below the cost and safety floor;
- returns depend on a few extreme funding events;
- basis blowouts or leg-liquidation scenarios erase ordinary carry;
- the required accounting cannot be made point-in-time and reproducible.

Testnet is highly useful for spot/perpetual leg orchestration and recovery, but
its funding economics are not validation evidence.

## H3 - Beta-Neutral Cross-Sectional Residual Reversion

Hypothesis: after removing common crypto-market beta, a large idiosyncratic
displacement between liquid assets reverts when it is not supported by a
persistent asset-specific flow proxy.

Economic transfer: crowded single-asset chasers and forced rebalancers pay the
relative-value portfolio.

Candidate universe: begin with a small liquid set such as BTC, ETH, and SOL.
The exact universe, beta estimator, lookback, rebalance interval, and residual
threshold must be locked before outcome inspection.

Cheap kill conditions:

- residual definition is unstable across reasonable training windows;
- apparent reversion disappears after two-leg costs;
- half-life is too short for the intended execution cadence;
- result does not beat a timestamp- and exposure-matched random baseline;
- one asset or one regime explains the pooled result.

Testnet can validate paired orders, hedge drift, and rebalance logic. Real
mainnet OHLCV is still required for the hypothesis test.

## H4 - Funding-Settlement Event Dislocation

Hypothesis: a preregistered extreme funding state immediately before a scheduled
settlement creates a short-lived post-settlement price or basis adjustment.

Economic transfer: participants unwilling or unable to rebalance before the
contractual funding event.

This remains directional or event-directional and therefore receives a strict
multiplicity penalty.

Cheap kill conditions:

- the effect occurs before the observable decision timestamp;
- event count is below the preregistered minimum;
- the effect is sub-cost;
- results depend on selecting thresholds or settlement windows after inspection.

Testnet can verify scheduler timing and funding-event handling, but not whether
the economic effect exists on mainnet.

## H5 - Setup I

Setup I remains a distinct order-flow data-class candidate, but it is another
directional family and requires a large, contamination-safe aggTrades path. It
is not the recommended first choice while non-directional mechanisms remain
untested.

Existing draft:
`research/signal_observation/SETUP_I_PREREGISTRATION.md`.

## H6 - Thin-Alt Cash-and-Carry

The wider visible basis may be compensation for exactly the risks that make the
instrument thin: spread, slippage, low capacity, delisting, outages, and basis
blowouts. It remains a later candidate, not an early cheap test.

Kill before research if realistic point-in-time book-depth or conservative fill
evidence is unavailable. Testnet order success cannot substitute for thin-alt
mainnet liquidity.

## Parked From This Round

- Market making and latency arbitrage: no defensible latency or queue-position
  advantage.
- Listing front-run: point-in-time announcement and selection contamination are
  structurally dangerous.
- Vesting-wallet tracking: no-spend policy, point-in-time wallet labels, chain
  fragmentation, and build cost make it a poor current fit.
- Options positioning: current local state classifies the required data path as
  paid/ineligible.
- Generic technical-indicator direction: repeats the exhausted search surface
  without a new economic transfer.

## Recommended Order

1. Prepare an H1 feasibility/preregistration note without downloading or
   inspecting candidate outcomes.
2. Require a free aligned-data inventory, a protected holdout, and a
   conservative four-leg cost equation.
3. If H1 data feasibility fails before outcome inspection, move to H3.
4. Treat H2 as an architecture variant of the carry family, not an automatic
   rescue after H1 results.
5. Keep H4 and Setup I as later bounded directional candidates.
6. Keep H6 parked until realistic thin-book cost evidence is feasible.

## H1 Preregistration Inputs Still Needed

Before H1 can become active, lock:

- venue pair selection rule without outcome-based venue shopping;
- contract equivalence and symbol mapping;
- funding settlement normalization;
- entry and exit timestamps;
- maximum unhedged interval;
- rebalance rule and leverage cap;
- fees, slippage, funding, and basis-tail model;
- minimum opportunity count and capacity floor;
- discovery/validation split and untouched holdout;
- random or matched baseline;
- STOP/PARK criteria;
- testnet acceptance tests, separate from the economic gate.

## Current Decision Boundary

This note recommends H1 only for the next preregistration decision. It does not
authorize data acquisition, feasibility probing, exchange credentials, private
API calls, testnet orders, implementation, or paper progression.

Current exchange state remains unchanged:

- Bybit private testnet access is blocked by unavailable usable credentials.
- Bitget demo remains a parked planning path.
- Reopening either path requires a separate explicit Protected Lane decision.
