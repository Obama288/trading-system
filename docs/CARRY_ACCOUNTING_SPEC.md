# Delta-Neutral Carry Paper Accounting Specification

Status: DRAFT / PROTECTED LANE DESIGN INPUT

This document specifies the intended authoritative accounting contract for
delta-neutral carry in paper mode. It does not authorize schema changes,
migrations, runtime wiring, exchange access, paper-readiness promotion, or live
trading. Implementation requires a separate Protected Lane design decision and
Human Owner approval.

## 1. Purpose And Scope

The accounting authority must answer, reproducibly and after restart:

- what each carry trade owns and owes on every venue and instrument;
- which requested orders produced which fills;
- which fees and funding cash flows were incurred;
- how execution slippage and basis movement contributed to PnL;
- how much PnL is realized versus unrealized;
- why paper account equity changed between any two points in time; and
- whether replaying duplicate or reordered observations changes the result.

The target is delta-neutral carry with at least two economic legs. The model
must support cross-venue perpetual funding dispersion and spot-perpetual carry
without encoding either strategy into the accounting engine.

Out of scope:

- signal generation, opportunity selection, and expected-return estimates;
- risk admission, sizing policy, leverage selection, and kill-switch policy;
- order routing and exchange-specific API implementation;
- tax accounting and fiat conversion outside the account reporting currency;
- migrations, production repositories, service wiring, and runtime behavior.

## 2. Accounting Authority And Boundaries

PostgreSQL is the only authoritative store. Redis, process memory, logs,
exchange/testnet UI, and strategy output are non-authoritative observations.

Accounting consumes immutable facts and produces deterministic projections.
It must not infer fills from orders, infer funding from advertised rates, or
manufacture closes from a missing venue snapshot. An unknown amount remains
unknown and blocks authoritative economic claims.

Recommended ownership boundary for later design review:

- execution authority records accepted orders and observed fills;
- accounting authority owns fees, funding, lot matching, PnL, cash, and equity;
- position authority owns operational position lifecycle and exit rules;
- reconciliation compares external observations with authoritative state and
  emits discrepancies; it does not silently rewrite accounting history;
- risk consumes committed accounting projections but cannot edit them.

No LLM output may create or alter an accounting fact.

## 3. Terminology And Identity

### 3.1 Carry trade

A `carry_trade` is the economic parent that groups all legs opened to capture a
carry source. It has a stable `carry_trade_id`, reporting currency, strategy
family/version, creation time, and lifecycle status.

Suggested lifecycle:

`planned -> opening -> open | imbalanced -> closing -> closed | failed`

`closed` requires every leg quantity to be flat and every known fee/funding
event through the close boundary to be booked. A trade with pending or
unavailable funding remains `closing` or `closed_pending_settlement`, subject to
the migration decision in section 16.

### 3.2 Leg

A `leg` is one venue/instrument/side exposure belonging to one carry trade.
Each leg requires:

- stable `leg_id` and `carry_trade_id`;
- venue, account scope, instrument, contract type, settlement asset;
- side (`long` or `short`), quantity unit, contract multiplier, and inverse or
  linear payoff rule;
- target quantity and current signed quantity;
- order and fill linkage;
- opened, reduced, and closed timestamps derived from fills, not requests.

Two legs are the minimum normal case, not a hard schema limit. Hedge repairs,
rolls, and fee-token conversions may require additional legs or cash events.

### 3.3 Order, fill, lot, and cash event

- An order is an execution instruction and never proof of exposure.
- A fill is an immutable executed quantity at one price and time.
- A lot is an accounting unit created by one or more opening fills and consumed
  by opposite fills under the locked lot-matching method.
- A cash event is an immutable fee, funding, adjustment, or transfer-like paper
  movement with explicit provenance. Arbitrary adjustments require a reason,
  operator identity, correlation ID, and audit event.

Internal IDs must remain stable across retries. External venue IDs are
qualified by venue and account scope; they are never globally unique by
assumption.

## 4. Canonical Event Model

The source ledger should be append-only. Updates from a venue are represented
as new observations or explicit correction/reversal events, never destructive
edits to prior booked facts.

Minimum event families:

| Event | Required economic content |
|---|---|
| `carry_trade_created` | parent identity, reporting currency, strategy version |
| `leg_registered` | venue/instrument/side/contract specification |
| `order_accepted` | internal and venue order IDs, leg, requested quantity/type |
| `fill_booked` | venue fill ID, order, quantity, price, trade time, liquidity role |
| `fee_booked` | fill or order reference, amount, asset, fee type, valuation |
| `funding_booked` | leg, settlement interval, rate if observed, position basis, cash amount/asset |
| `mark_observed` | instrument, mark type, price, source time, received time |
| `cash_adjustment_booked` | signed amount, asset, reason, actor, evidence reference |
| `event_reversed` | target event, reason, replacement reference if any |
| `reconciliation_discrepancy` | expected, observed, tolerance, severity, evidence time |
| `trade_accounting_closed` | close boundary and projection version/hash |

Every event requires:

- immutable `accounting_event_id`;
- account scope and reporting currency;
- event type and schema version;
- economic time (`effective_at`) and ingestion time (`recorded_at`) in UTC;
- producer, source, source reference, correlation ID, and causation ID;
- idempotency key and canonical payload hash;
- exact decimal payload values represented without binary float;
- optional carry trade, leg, order, fill, and settlement-interval references.

Ordering must use explicit economic time plus a deterministic tie-breaker. DB
insertion order alone is insufficient. Late events must trigger projection
rebuild from the earliest affected boundary.

## 5. Fill And Position Accounting

### 5.1 Signed quantities

Use one sign convention everywhere:

- buy fill quantity is positive;
- sell fill quantity is negative;
- leg position is the exact sum of signed booked fills;
- flat means exact zero after instrument-quantum normalization.

No epsilon comparison is permitted for authoritative quantity state. Values
must already be quantized to the instrument's valid quantity quantum.

### 5.2 Partial fills

Every partial fill is booked separately. Weighted average price is a projection,
not a replacement for fill history:

`average_open_price = sum(open_quantity * fill_price) / sum(open_quantity)`

The projection must preserve each fill's fee, timestamp, liquidity role, and
venue identity. A partially filled order can leave the carry trade imbalanced;
the unfilled requested quantity has no position or PnL.

### 5.3 Lot matching

The implementation must lock one deterministic matching policy before use.
FIFO is the recommended default because it preserves an auditable link between
opening and closing fills. Weighted-average cost is acceptable only if selected
explicitly and applied consistently across realized and unrealized PnL.

A fill that crosses through zero must be split deterministically into:

1. quantity closing existing lots; and
2. residual quantity opening exposure in the opposite direction.

### 5.4 Contract payoff

Linear contracts and spot use quote-currency payoff:

`price_pnl = signed_open_quantity * multiplier * (mark_or_exit - entry)`

The later implementation must define a separate exact formula for inverse and
quanto contracts. Such instruments fail closed until their payoff and
reporting-currency conversion are implemented and tested.

## 6. Fees

Fees are booked from observed fill/settlement facts when available. A configured
fee schedule may produce an explicitly labelled estimate for simulation, but
estimated and observed fees must never be merged without provenance.

Each fee requires:

- signed amount, fee asset, and fee category;
- associated venue/order/fill when applicable;
- maker/taker role when known;
- conversion price, source, and timestamp when fee asset differs from the
  reporting currency;
- status: `estimated`, `observed`, `corrected`, or `reversed`.

Cash convention: costs are negative; rebates are positive.

An observed fee replaces an estimate through reversal plus a new event or
through a deterministic estimate-to-observed state transition backed by an
immutable audit trail. It must not be added on top of the estimate.

Total fees for a trade are the sum of all leg fees, including opening, hedge
repair, rebalancing, closing, and fee-asset conversion costs.

## 7. Funding Accrual And Settlement

Funding becomes authoritative only when a settlement cash flow is observed or
when the paper simulator emits a deterministic settlement fact from a locked
input dataset. A displayed or predicted funding rate alone is not cash PnL.

Each funding event requires:

- venue, instrument, leg, and unique settlement interval;
- interval start/end and settlement time;
- signed funding rate if supplied by the source;
- exact position quantity and reference price/notional used by that venue rule;
- signed funding amount and settlement asset;
- source status: observed or simulated;
- conversion into reporting currency at the locked conversion mark.

Cash convention: funding received is positive; funding paid is negative.

The accounting engine must not assume all venues use the same interval,
timestamp, mark, or formula. Venue funding calculation rules are versioned
inputs. If the source publishes only the final cash amount, that amount is
authoritative and the reconstructed rate calculation is diagnostic.

Uniqueness must prevent double booking the same venue/account/instrument/
settlement interval/source record. Late funding after a leg closes is booked at
its actual effective time and updates the parent trade and account projections.

Accrued but unsettled funding may be displayed only as `estimated_funding` and
must not enter authoritative realized PnL or cash. Whether it enters a separate
economic equity estimate is an explicit policy decision, not a default.

## 8. Slippage

Slippage is an execution attribution metric, not an independent cash movement.
Booking it as both price PnL and a cash cost would double count it.

For each fill, lock a decision-time benchmark that was available before the
order action. Recommended benchmark precedence is strategy decision mid, then
submission-time mid, with benchmark type recorded explicitly.

Adverse slippage in reporting currency:

`slippage = -signed_fill_quantity * multiplier * (fill_price - benchmark_price)`

Under this convention, a worse buy above benchmark and a worse sell below
benchmark both produce negative slippage. For inverse/quanto contracts, use the
contract payoff function rather than this linear formula.

Slippage contributes to execution-quality attribution. Net PnL already reflects
actual fill prices, so the PnL equation must not subtract slippage again.

If no valid pre-action benchmark exists, slippage is `unknown`, not zero.

## 9. Basis And Price PnL

For delta-neutral carry, price PnL must be calculated per leg first and then
summed. The portfolio's basis PnL is the change in relative leg valuation after
respecting contract multipliers, quantities, and currency conversion.

For a linear two-leg trade:

`basis_price_pnl = long_leg_price_pnl + short_leg_price_pnl`

This is exact even when legs have unequal notional. A separate hedge residual
diagnostic reports the remaining directional exposure:

`net_delta_notional = sum(signed_quantity * multiplier * current_mark)`

Do not label all combined leg price PnL as convergence alpha. It can include
temporary directional exposure, imperfect sizing, hedge repair, and conversion
effects. Attribution should expose at least:

- basis/relative-price movement;
- residual directional movement;
- FX or settlement-asset conversion movement, if applicable;
- execution slippage diagnostic.

The exact decomposition for unequal or dynamically rebalanced legs must be
chosen before implementation and reconcile back to total price PnL without a
residual unexplained bucket beyond configured rounding tolerance.

## 10. PnL Definitions

All account and trade reports must name both scope and time boundary.

### 10.1 Gross realized PnL

`gross_realized_pnl = realized_price_pnl + settled_funding`

Realized price PnL is created only by quantity-closing fills under the locked
lot method. Settled funding is realized cash regardless of whether the related
leg remains open.

### 10.2 Net realized PnL

`net_realized_pnl = realized_price_pnl + settled_funding + booked_fees`

`booked_fees` includes negative costs and positive rebates. Slippage is not
subtracted separately because realized price PnL uses actual fill prices.

### 10.3 Gross unrealized PnL

`gross_unrealized_pnl = sum(open_lot_price_pnl_at_valid_marks)`

Unsettled funding estimates are excluded. If any required mark or conversion
rate is stale or absent, authoritative unrealized PnL is unavailable for the
affected scope rather than silently carried forward.

### 10.4 Net unrealized PnL

By default:

`net_unrealized_pnl = gross_unrealized_pnl`

Projected exit fees, projected slippage, and unsettled funding may be reported
as separate scenario estimates. They must not be mixed into authoritative PnL.

### 10.5 Total economic PnL

`net_total_pnl = net_realized_pnl + net_unrealized_pnl`

Every displayed total must be exactly reconstructible from its components at
the same as-of boundary.

## 11. Cash, Equity, And Movement Bridge

Cash changes only through booked cash events: fees, funding settlements,
explicit adjustments, and any modeled collateral/settlement flows. Opening or
closing a derivative position does not itself create PnL cash beyond associated
fees and settlement rules. Spot principal movement must be modeled separately
from PnL because buying spot exchanges quote cash for an asset.

The implementation must distinguish:

- cash balance by asset;
- collateral or spot inventory by asset;
- realized PnL;
- unrealized PnL;
- reserved margin, if modeled;
- reporting-currency equity.

At an as-of time:

`equity = reporting_currency_cash`
`       + converted_non_reporting_cash_and_spot_inventory`
`       + derivative_unrealized_pnl`
`       + other_explicitly_modeled_assets_or_liabilities`

The equity movement bridge between two committed snapshots must reconcile:

`ending_equity - starting_equity`
`  = realized_price_pnl`
`  + change_in_unrealized_price_pnl`
`  + settled_funding`
`  + fees_and_rebates`
`  + conversion_effect`
`  + external_or_operator_adjustments`

Transfers between internal buckets do not change total equity. Any unexplained
difference above tolerance is a blocking discrepancy, never `other PnL`.

The existing single `equity_usdt` value is insufficient as an accounting
ledger. Until an authoritative bridge exists, it must not be treated as proof
of paper-economic performance.

## 12. Marks, Time, And Valuation

- All timestamps are timezone-aware UTC.
- Economic time and ingestion time are stored separately.
- Mark type is explicit: venue mark, index, bid/ask liquidation value, mid, or
  locked simulator mark.
- Mark freshness policy is defined per instrument and cadence.
- A stale mark never becomes fresh because the process restarted.
- Cross-asset conversion uses a named source, side convention, and timestamp.
- Reports state `as_of`, maximum source age, and completeness status.

Closed-trade realized PnL must not change due to later market marks. It may
change only through late/corrected fills, fees, funding, conversion facts, or
explicit reversals, all of which remain auditable.

## 13. Decimal And Precision Contract

Binary floating point is forbidden for authoritative money, price, quantity,
rate, and PnL calculations.

- Parse external decimal strings directly to `Decimal`; never through `float`.
- Persist exact fixed-point decimals with deliberate precision and scale.
- Store asset amount, price, quantity, rate, multiplier, and reporting amount
  as distinct typed values.
- Quantize quantities to instrument quantity step and prices to tick size using
  locked venue rules.
- Do not quantize intermediate PnL unnecessarily; quantize only at defined
  settlement/reporting boundaries.
- Define rounding mode per operation. Recommended default is `ROUND_HALF_EVEN`
  for reporting, while venue-specific execution/fee rounding follows the venue
  rule exactly.
- Never compare authoritative monetary values using float epsilon.
- Persist the unrounded calculation inputs needed to reproduce each result.

Precision must accommodate small funding rates, high-priced instruments,
contract multipliers, and cumulative sums without overflow. Exact SQL numeric
precision/scale is a migration decision requiring data-range analysis.

## 14. Idempotency And Transaction Semantics

Idempotency is required at each external and internal boundary.

- The same source fill cannot create two fill events.
- The same funding settlement cannot create two cash events.
- Retrying an accepted command returns the existing result when payload hash
  matches.
- Reusing an idempotency key with a different canonical payload is a hard
  conflict and incident.
- Projection replay from the same ordered event set produces byte-equivalent
  normalized decimal outputs and the same projection version/hash.
- Event insert and the required projection update occur in one DB transaction,
  or projection processing uses a durable exactly-once checkpoint with a
  deterministic replay path.
- Out-of-order events are accepted only as immutable late facts and trigger a
  rebuild; they must not be ignored because a position is already closed.

The design must specify transaction ownership in the application use case.
Repositories must not commit independently unless an explicit exception is
approved.

## 15. Reconciliation

Reconciliation compares authoritative projections to a complete, time-bounded
observation set. Absence from an incomplete snapshot is not proof of closure.

Required comparison dimensions:

- open signed quantity per venue/account/instrument;
- cumulative fills per order and venue fill identity;
- fees and rebates;
- funding settlements and intervals;
- cash/collateral balances when an authoritative paper source exists;
- order status and carry-trade leg status;
- account equity bridge.

Each reconciliation run records source, completeness claim, snapshot time,
received time, cursor/page coverage, compared projection version, tolerances,
and result hash.

Discrepancies are classified:

- `late_observation`: known source lag, no mutation;
- `missing_internal_fact`: external fact not yet booked;
- `missing_external_fact`: internal fact absent externally;
- `amount_mismatch`: same identity, different exact amount;
- `identity_conflict`: duplicate ID with conflicting payload;
- `valuation_mismatch`: quantities agree but marks/conversion differ;
- `unexplained_equity`: bridge does not reconcile.

Automatic repair may append a fact only when source identity and provenance are
unambiguous and the repair rule has explicit approval. Otherwise reconciliation
fails closed, emits an incident, and blocks economic-readiness claims.

## 16. Failure Modes And Required Behavior

| Failure mode | Required behavior |
|---|---|
| One leg fills and the hedge leg does not | Book actual fill; mark trade `imbalanced`; expose delta and duration; never invent hedge fill |
| Partial fill then cancel | Book fills only; leave remainder unfilled; preserve cancel observation |
| Duplicate fill/funding delivery | Deduplicate by qualified source identity and payload hash |
| Same source ID, conflicting payload | Reject mutation, raise blocking identity-conflict incident |
| Fee arrives after fill | Book late fee and rebuild affected projections |
| Funding arrives after close | Book against original leg/trade and update realized PnL/equity bridge |
| Missing or stale mark | Unrealized PnL/equity status becomes incomplete; do not substitute zero |
| Missing snapshot row | Do not close or flatten unless snapshot completeness proves absence semantics |
| Process crash between fact and projection | Transaction rollback or deterministic replay from durable checkpoint |
| Unsupported contract payoff | Reject authoritative valuation for that instrument |
| Invalid precision or non-quantized quantity | Reject event before booking and preserve raw evidence separately |
| Currency conversion unavailable | Keep native amount; reporting total is incomplete |
| Manual correction requested | Append audited adjustment or reversal; never edit history in place |
| Negative or impossible balance | Raise incident; do not conceal with synthetic adjustment |
| Projection hash differs on replay | Stop accounting publication and treat as deterministic-integrity failure |

## 17. Invariants

An implementation must enforce and test at least these invariants:

1. Sum of signed fills equals authoritative leg quantity.
2. Sum of open-lot quantities equals authoritative leg quantity.
3. Closed leg quantity and open-lot quantity are exactly zero.
4. A fill belongs to exactly one account, order, leg, and carry trade.
5. A source fill or funding settlement is booked at most once.
6. No realized price PnL exists without a quantity-closing fill.
7. Advertised or estimated funding never enters authoritative realized PnL.
8. Slippage attribution is not separately subtracted from fill-price PnL.
9. Trade PnL equals the exact sum of its leg and cash-event components.
10. Account PnL equals the exact sum of trade and account-level components.
11. Equity movement equals the explicit movement bridge within the configured
    reporting quantum; there is no unexplained balancing bucket.
12. Replaying the same events produces the same state and projection hash.
13. A reversal preserves both the original event and the reversing event.
14. All authoritative decimals originate without binary-float conversion.
15. Unknown or stale valuation input produces incomplete status, not zero.
16. Operational `closed` and economically settled status cannot be conflated.
17. A carry trade cannot be economically complete while any leg is imbalanced,
    any required conversion is missing, or a blocking discrepancy is open.

## 18. Migration And Architecture Questions

These questions must be decided in a separate Protected Lane design review
before any migration is written:

1. Should accounting use new normalized ledger/projection tables, or can any
   existing `executions`, `positions`, and `position_events` fields be retained
   as operational projections only?
2. Which service owns the accounting transaction and public read API?
3. Is `carry_trade` a new parent aggregate, and how does it relate to current
   one-candidate/one-execution/one-position assumptions?
4. Are fills and cash events separate tables, one typed event table, or both an
   immutable ledger and normalized projections?
5. What exact `NUMERIC(precision, scale)` is required for each value class after
   instrument-range analysis?
6. What is the reporting currency contract: USDT only initially, or arbitrary
   reporting currency with explicit conversion?
7. Are spot principal and inventory needed for the first H1 scope, or can the
   first authorized implementation cover perpetual/perpetual only?
8. Which lot method is locked: FIFO or weighted average?
9. How are inverse and quanto contracts gated until payoff support exists?
10. When is a trade `closed` versus `closed_pending_settlement` versus
    `settled`, and what is the funding lateness boundary?
11. Are paper fees/funding observed from testnet, simulated from public data,
    or supported as explicitly separate source modes?
12. What projection strategy is used: synchronous transactional projections,
    asynchronous durable projector, or calculated-on-read?
13. How are late events versioned so historical as-of reports remain
    reproducible while current truth incorporates corrections?
14. What mark source/freshness policy is valid for each venue and contract?
15. Which reconciliation source can assert a complete snapshot, and how are
    pagination/cursor completeness and source outages represented?
16. How is current `paper_account_authority.equity_usdt` migrated or retired
    without treating its float value as reconstructible ledger history?
17. Is historical float data rejected, imported as explicitly low-confidence
    opening adjustments, or preserved outside authoritative performance?
18. Which roles may append adjustments and reversals, and what approval/audit
    requirements apply?
19. What retention and partitioning strategy supports event replay without
    weakening auditability?
20. Which accounting snapshot is consumed by authoritative risk, and what
    freshness/completeness failures make risk fail closed?

## 19. Acceptance Criteria For A Future Implementation

No implementation is paper-economically ready until all criteria below have
objective evidence on a frozen commit.

### 19.1 Calculation tests

- Exact Decimal tests cover long/short, linear spot/perpetual, multiple partial
  fills, reductions, full close, and a fill crossing through zero.
- Realized/unrealized PnL matches hand-calculated fixtures under the locked lot
  method.
- Maker rebate, taker fee, fee in another asset, and late corrected fee are
  covered without double counting.
- Funding paid/received, mixed venue intervals, late settlement, and duplicate
  settlement are covered.
- Slippage signs are correct for buys and sells and never double-counted in net
  PnL.
- Basis PnL plus residual/FX attribution reconciles exactly to total price PnL.
- Equity movement bridge reconciles exactly for derivative/derivative and any
  authorized spot/derivative scenario.

### 19.2 State and replay tests

- Duplicate commands and duplicate source events are no-ops with the same
  response; conflicting reuse fails hard.
- Randomized event delivery order followed by rebuild yields the canonical
  projection where economic ordering permits it.
- Crash injection at every transaction boundary produces either no committed
  effect or one recoverable committed fact, never half-booked economics.
- Full ledger replay after process restart reproduces all projection hashes.
- Reversal and late-event replay preserve historical audit facts and update
  current projections deterministically.

### 19.3 Failure and reconciliation tests

- One-leg fill, second-leg rejection, partial fill/cancel, stale mark, missing
  conversion, unsupported contract, and unavailable funding all fail visibly.
- Incomplete snapshots cannot create synthetic closes.
- Complete snapshot mismatches create durable discrepancies and incidents.
- Approved automatic repair is idempotent and append-only.
- Unexplained equity movement blocks publication of authoritative performance.

### 19.4 Integration evidence

- A deterministic paper scenario opens both legs through separate fills,
  books all opening fees, books at least two venue funding settlements, marks
  both legs, partially closes, fully closes, books closing fees, restarts, and
  reproduces the same final cash, realized PnL, and equity bridge.
- A deterministic imbalance scenario proves that actual exposure and hedge
  duration remain visible across restart and reconciliation.
- Current operational position state and accounting state agree through
  explicit IDs without either authority silently overwriting the other.
- PostgreSQL constraints demonstrate source-event uniqueness and exact numeric
  persistence on the supported Python 3.12 runtime.

### 19.5 Readiness gate

Completion of these tests proves only accounting implementation correctness in
the tested paper environment. Paper-economic readiness additionally requires
accepted architecture review, migration review, security/authority review,
end-to-end runtime evidence, complete cost inputs, and Human Owner approval.
It does not prove strategy edge, testnet realism, or live readiness.

## 20. Required Design Outputs Before Implementation

A Protected Lane implementation proposal must provide:

- accepted aggregate and authority diagram;
- table/column/key/index proposal with Decimal range analysis;
- event schemas and versioning policy;
- exact formulas and lot/rounding policies;
- transaction and idempotency design;
- reconciliation completeness contract;
- migration/backfill/rollback plan that preserves owner data;
- threat and failure analysis;
- focused test matrix mapped to section 19;
- independent review record; and
- explicit Human Owner authorization naming the approved scope.

Until those outputs are accepted, this file remains design input only.
