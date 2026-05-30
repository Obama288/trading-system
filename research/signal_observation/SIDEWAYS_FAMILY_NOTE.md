# Sideways Family Note

## Status And Boundary

Status: PROPOSED / CANDIDATE MAP ONLY.

Tower Control / Owner decision:

- Sideways family: GO to map.
- Sideways screening: HOLD until harness methodology is authorized.
- Sideways acquisition/analysis: NO-GO.

This note expands the research candidate map toward sideways-market structural
edges. It does not authorize screening, acquisition, analysis, EXPLORE,
validation, implementation, readiness, paper/probe/runtime/live activity, or
capital use. It does not authorize harness execution. It does not authorize D1
analysis. It does not create a new stage.

The reusable cheap-falsification harness remains PROPOSED only. Harness
authorization remains HOLD. D1 analysis remains HOLD. Setup E remains HOLD
pending Hydromancer reply/date-range source resolution.

## Why Sideways

Sideways regimes are a large share of market time and may increase sample
availability for structurally motivated candidates. A sideways-family map is
therefore worth maintaining before any screening authorization.

This is not naive range trading. Naive "buy bottom / sell top" range trading is
not accepted as an edge hypothesis. A candidate must describe a mechanism,
counterparty, context layer, and failure mode before it can be considered for
future harness pre-registration.

## Required Context Layers

Every future sideways candidate must specify:

- Regime confirmation: why the market is statistically sideways, not merely a
  trend retracement.
- Flow / microstructure / positioning confirmation: why the boundary,
  convergence, or normalization pressure should hold.
- Regime-break risk: what can invalidate the sideways state.

## Primary Branches

### A. Sideways Carry / Normalization

Cashflow, payment, or positioning-normalization driven candidates. Examples:
funding normalization, basis/cash-and-carry, and volatility carry.

Main risk: carry earns small repeated payments but can suffer tail loss on
regime change.

### B. Sideways Relative-Value / Range Behavior

Convergence or relative-value driven candidates. Examples: cross-asset spread
mean reversion, false breakout re-entry, and open-interest divergence during
flat price.

Main risk: structural break and path dependency.

## Ranked Candidate Subfamilies

### Tier 1

#### Funding Normalization

- Mechanism: elevated or compressed perpetual funding normalizes after crowded
  positioning pressure while price remains broadly sideways.
- Likely counterparty: leveraged traders paying for directional exposure or
  participants holding crowded positions through funding resets.
- Data/source feasibility: D1 funding data already exists as a possible future
  input, but D1 analysis remains HOLD; OHLCV context exists from prior research
  artifacts. No new acquisition is authorized.
- Harness template assignment: Continuous-State.
- Why included or deferred: included as the cleanest Branch A prototype; deferred
  from screening until harness methodology, SOLUSDT interval policy, and a
  separate D1 analysis design lock are authorized.
- Latency classification: latency-tolerant; signal half-life hours to days;
  human-in-loop acceptable; first-prototype selection partly due to operational fit.

#### Basis / Cash-And-Carry

- Mechanism: spot-perpetual or spot-futures dislocations normalize when
  financing demand, leverage pressure, or arbitrage imbalance mean-reverts.
- Likely counterparty: leveraged directional traders paying for synthetic
  exposure, or participants slow to arbitrage spot/derivative dislocations.
- Data/source feasibility: requires spot and derivative prices plus derived
  basis series; feasibility is plausible but not confirmed for a locked source
  path in this note.
- Harness template assignment: Continuous-State or Cross-Venue Dislocation.
- Why included or deferred: included as a core Branch A/B bridge; deferred until
  source feasibility and harness authorization exist.
- Latency classification: latency-tolerant; signal half-life hours to days;
  human-in-loop likely acceptable pending source and framing confirmation.

#### Cross-Asset Spread Mean Reversion BTC/ETH/SOL

- Mechanism: relative-value spreads among BTC, ETH, and SOL may normalize during
  sideways regimes when idiosyncratic displacement is not supported by broader
  market direction.
- Likely counterparty: crowded single-asset allocators, relative-value laggards,
  or hedgers paying to rebalance under flat index conditions.
- Data/source feasibility: OHLCV availability appears plausible from existing
  research universe history, but no spread construction or analysis is
  authorized here.
- Harness template assignment: Continuous-State.
- Why included or deferred: included because it may reuse a familiar
  BTC/ETH/SOL universe while remaining structurally distinct from Setup C;
  deferred until pre-registration and harness authorization.
- Latency classification: latency-tolerant to medium; spread signals typically
  hours to days; human-in-loop likely acceptable pending framing confirmation.

### Tier 2

#### Volatility Carry / Options-Driven Sideways Behavior

- Mechanism: realized compression, pinning, or options-related hedging pressure
  may create sideways behavior or carry-like payoffs around known positioning
  regimes.
- Likely counterparty: options buyers paying premium, dealers hedging gamma, or
  participants positioned into expiry-related flows.
- Data/source feasibility: underlying OHLCV is plausible; options open interest,
  expiry, and volatility source feasibility require later verification.
- Harness template assignment: Continuous-State.
- Why included or deferred: included as a structurally different sideways
  candidate; deferred because options data feasibility is unresolved.

#### Open-Interest Divergence During Flat Price

- Mechanism: rising or falling open interest while price remains flat may reveal
  hidden buildup, absorption, or positioning stress that later normalizes or
  breaks.
- Likely counterparty: leveraged participants building positions into a flat
  market and liquidity providers absorbing that flow.
- Data/source feasibility: requires OI history plus OHLCV; public feasibility
  remains candidate-specific and unconfirmed here.
- Harness template assignment: Event-Triggered or Continuous-State depending on
  framing.
- Why included or deferred: included because it adds positioning context to
  sideways classification; deferred until OI source feasibility and framing are
  locked.

### Tier 3

#### False Breakout Re-Entry

- Mechanism: failed boundary breaks in a confirmed sideways regime may force
  breakout participants to unwind, creating re-entry pressure.
- Likely counterparty: breakout buyers/sellers caught outside the range and
  forced to cover or exit.
- Data/source feasibility: OHLCV may be enough for a crude event definition, but
  the context-layer burden is high and must avoid naive range trading.
- Harness template assignment: Event-Triggered.
- Why included or deferred: included as a possible Branch B event candidate;
  deferred because it is closest to naive range trading and needs strict
  pre-registration.

#### Microstructure Mean Reversion

- Mechanism: order-book imbalance, spread, or short-horizon liquidity shocks may
  revert inside flat regimes.
- Likely counterparty: liquidity takers crossing spread during temporary
  imbalance or participants forced by short-horizon execution needs.
- Data/source feasibility: likely requires order-book/trade microstructure data,
  which is outside current source scope.
- Harness template assignment: Event-Triggered or separate future
  high-frequency scope; deferred.
- Why included or deferred: included only as a map item; deferred because it is
  likely a separate high-frequency research scope, not a current harness target.
- Latency classification: highly latency-sensitive; signal half-life seconds to
  minutes; automation required; deferred until operational infrastructure exists.

## Harness Mapping

- Funding normalization: Continuous-State.
- Basis/cash-and-carry: Continuous-State or Cross-Venue Dislocation.
- Cross-asset spread mean reversion: Continuous-State.
- Volatility carry: Continuous-State.
- False breakout re-entry: Event-Triggered.
- OI divergence: Event-Triggered or Continuous-State depending on framing.
- Microstructure mean reversion: Event-Triggered or separate future
  high-frequency scope; deferred.

No separate sideways harness is authorized or needed at this stage. Future
sideways candidates should map into the existing proposed reusable harness
families unless a later Owner decision explicitly creates a new reviewed
methodology.

## Candidate Backlog-Entry Template

Every future sideways candidate entry should include:

- Candidate name:
- Branch A/B:
- Hypothesis / mechanism:
- Counterparty / who pays:
- Regime applicability:
- Required context layers:
- Data/source feasibility:
- Harness template assignment:
- Rough capacity / execution fit:
- Key failure modes:
- Forbidden next actions:
- Current status:
- Signal half-life:
- Maximum acceptable decision delay:
- Human-in-loop allowed:
- Automation required before paper/live:
- Missed-signal impact:
- Operational fit:

## Latency Tolerance Guidance

Latency-tolerant candidates (hours-days signal half-life; human-in-loop
acceptable) fit the current solo-operator research stage better than
latency-sensitive candidates. Latency-sensitive candidates should be deferred
until automation and operational infrastructure are in place.

Classification levels:
- latency-tolerant: signal half-life hours to days; human-in-loop acceptable
  for research and screening; automation not required for research phase.
- medium: signal half-life minutes to hours; execution timing matters but
  human review is still acceptable for research; automation required before
  paper/live.
- latency-sensitive: signal half-life seconds to minutes; automation required;
  not appropriate for current solo-operator stage.

## Filled Example: Funding Normalization

- Candidate name: Funding Normalization.
- Branch A/B: A. Sideways Carry / Normalization.
- Hypothesis / mechanism: in statistically sideways regimes, elevated,
  compressed, or displaced perpetual funding can normalize as crowded leverage
  pressure decays; the edge hypothesis is payment/positioning normalization, not
  naive range trading.
- Counterparty / who pays: leveraged directional traders paying funding,
  crowded participants holding exposure through funding resets, and late
  entrants forced to reduce exposure when carry becomes expensive.
- Regime applicability: only after a future pre-registration defines why the
  market is statistically sideways rather than a trend retracement.
- Required context layers: sideways-regime confirmation; funding/positioning
  confirmation; regime-break risk such as volatility expansion, liquidation
  cascade, macro shock, or directional breakout.
- Data/source feasibility: uses already-acquired D1 funding data as possible
  future input. D1 analysis remains HOLD. SOLUSDT variable intervals are
  retained/flagged and may be relevant to funding-stress/event-triggered
  handling, not a data defect. No analysis is authorized.
- Harness template assignment: Continuous-State by default; event-triggered
  framing may be considered only for explicit funding-stress interval events
  after separate authorization.
- Rough capacity / execution fit: likely better for liquid perps and lower
  turnover than microstructure candidates, but capacity is not assessed here.
- Key failure modes: funding does not normalize; gross edge is below
  pre-registered cost floor; signal is concentrated in one stress episode;
  regime break dominates small carry payments; SOLUSDT interval handling is
  mixed into clean carry analysis without an explicit design decision.
- Forbidden next actions: no screening, acquisition, analysis, EXPLORE,
  validation, implementation, readiness, paper/probe/runtime/live activity, or
  capital use from this example.
- Current status: PROPOSED / CANDIDATE MAP ONLY; D1 analysis HOLD.
- Signal half-life: hours to days; funding normalization persists across
  multiple 8H cycles.
- Maximum acceptable decision delay: hours to days; human-in-loop acceptable.
- Human-in-loop allowed: yes.
- Automation required before paper/live: not required for research phase.
- Missed-signal impact: low to moderate; missed cycles are recoverable.
- Operational fit: latency-tolerant; intentionally selected as first prototype
  for human-in-loop fit at current solo-operator stage.

## Relationship To Existing Candidates

- Setup E post-liquidation exhaustion reversal can be reframed as partly
  sideways-class / forced-flow reversal, but remains HOLD pending source.
- Setup D splits into funding stress and funding normalization, but D1 analysis
  remains HOLD.
- Setup C remains parked/retired as trend/momentum; do not revive.
- Basis and options expiry remain candidate-map items only until harness
  authorization and source feasibility.

## Boundary Restatement

This note is a candidate-map expansion only. It authorizes no data work, no
network calls, no EXPLORE, no screening, no statistics, no backtests, no
strategy logic, no implementation, no readiness, and no new stage.
