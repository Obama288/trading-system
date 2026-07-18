# H3 - Beta-Neutral Residual Reversion Pre-Registration

Status: DRAFT / PLANNING ONLY / LOCK CANDIDATE
Family: Beta-neutral cross-sectional residual reversion
Governed by: `docs/RESEARCH_CONSTITUTION.md` and `docs/BOUNDARIES.md`

This document is a lock candidate, not an active research authorization. It
does not authorize data acquisition, data inspection, discovery, validation,
testnet activity, paper trading, or live trading.

## Gate State

H3 is the next preregistration candidate after H1 was parked at the free-data
feasibility gate with no outcome inspection. The active research family remains
none until the Owner explicitly accepts a locked pre-registration and separately
authorizes a bounded coverage/acquisition step.

This candidate is not lockable until a coverage-only data path confirms
non-overlapping discovery, validation, and recent-rerun windows without
computing H3 residuals, returns, spreads, fees, PnL, or trade outcomes.

## Campaign Comparison-Budget Note

This is a late-campaign crypto-perp attempt after multiple failed, parked, or
ineligible families: Setup A, Setup B, Setup C, funding/carry variants, Setup
E, Setup H, and H1. A positive result must be interpreted against that full
comparison budget.

The reason H3 remains worth one tightly bounded attempt is that it targets a
relative-value residual after removing BTC market beta. It is not allowed to
become another broad price-action search over assets, thresholds, windows, and
regimes.

## 2.1 Hypothesis And Mechanism

Hypothesis: when ETH or SOL makes a large positive or negative return residual
versus BTC market beta on a closed 4h bar, that residual partially reverts over
the next 12 hours after two-leg costs.

Mechanism / who pays: single-asset attention, forced inventory pressure,
stop-runs, and local liquidations can temporarily move ETH or SOL more than the
common crypto factor justifies. The counterparty is the trader extrapolating a
single-name move as durable information while relative-value traders and hedgers
continue to anchor exposure to the common BTC factor.

Required falsifiable claim: the edge must exist in the beta-hedged residual leg,
not in the outright direction of ETH, SOL, or BTC. If the result depends on
unhedged directional drift, H3 fails.

## 2.2 Primary Variant

Only one primary variant is eligible to promote the family:

- signal assets: ETHUSDT perpetual and SOLUSDT perpetual;
- market factor and hedge: BTCUSDT perpetual;
- bar interval: 4h;
- returns: log returns from closed candles only;
- beta estimator: rolling OLS of asset log return on BTC log return;
- beta lookback: 180 calendar days of 4h bars;
- minimum beta-fit history: 900 closed bars;
- residual scale: rolling median absolute deviation of residuals over 90
  calendar days, using only bars closed before the signal bar;
- signal threshold: absolute residual z-score at the signal bar close is at
  least 2.25;
- direction: contrarian to the residual;
- entry: next 4h bar open after the signal bar close;
- hedge: BTC notional equals locked beta times asset notional, opposite the
  estimated market exposure;
- exit: mark both legs at the open 3 bars after entry, giving a 12h holding
  window;
- overlap: per asset, no new observation may enter before the prior H3
  observation exits.

No stop, target, residual mean-cross exit, per-regime split, session split,
alternative threshold, alternative lookback, alternative market basket, or
single-asset-only result is primary.

## 2.3 Primary Metric And Gate

Primary metric: post-cost mean `expectancy_R` over all non-overlapping primary
observations.

`1R` is the pre-cost absolute adverse move that would occur if the residual
z-score widens by another 1.0 z unit from entry while beta is held fixed. The
trade PnL is the two-leg beta-hedged mark-to-market return from entry to exit,
converted to R with this initial risk denominator.

Cost model:

- moderate primary cost: 8 bps per side per leg for taker fee plus slippage;
- round trip charges four sides: asset entry, BTC hedge entry, asset exit, BTC
  hedge exit;
- funding is included if any holding interval crosses a funding timestamp;
- zero-cost and optimistic-cost runs are diagnostic only.

Discovery pass gate:

- primary expectancy_R at least +0.07R after moderate costs;
- primary expectancy_R exceeds the matched random baseline p95;
- at least 80 non-overlapping observations pooled across ETH and SOL;
- both ETH and SOL must have at least 25 observations and non-negative
  expectancy_R after moderate costs.

Validation pass gate:

- expectancy_R is non-negative after moderate costs;
- effect direction matches discovery;
- at least 40 non-overlapping observations pooled across ETH and SOL;
- neither asset is worse than -0.05R expectancy_R after moderate costs.

Stage 4 recent-rerun gate:

- last 12 months available at run time;
- expectancy_R is non-negative after moderate costs;
- no pre-registered kill criterion is triggered.

These thresholds are intentionally strict because H3 is a late-campaign price
data-class attempt and uses two legs.

## 2.4 Windows And Data Path

No H3 data path is accepted yet.

Before lock, a coverage-only contract must identify a free, contamination-safe
source for BTCUSDT, ETHUSDT, and SOLUSDT perpetual 4h OHLCV and must bind raw
or normalized files by SHA-256. The coverage-only step may check only:

- source, venue, symbol, interval, and file/request availability;
- timestamp order, duplicate bars, missing bars, zero-volume bars, and OHLC
  sanity;
- date bounds and dataset hashes.

It must not compute H3 beta, residuals, z-scores, trade entries, trade exits,
costs, returns, PnL, expectancy, Sharpe, drawdown, or baseline metrics.

Candidate windows for Owner review, subject to coverage-only confirmation:

- discovery: `[2022-01-01, 2024-01-01)`;
- validation: `[2024-01-01, 2025-01-01)`;
- recent rerun: `[2025-07-01, 2026-07-01)` or the latest full 12 calendar
  months available at lock time.

If these exact windows cannot be confirmed cleanly before H3 outcome
inspection, H3 parks or returns to the Owner for a new pre-registration. The
windows must not be moved after any H3-relevant result is observed.

## 2.5 Matched Random Baseline

Primary baseline: matched timestamp-and-volatility random residual trades.

For each real signal asset, direction, and window, draw random entry timestamps
from bars where:

- the same asset has enough beta and residual-scale history;
- no real H3 signal is active;
- the 30-day realized volatility bucket matches the real signal bucket;
- the BTC 4h return sign matches the real signal bar's BTC return sign.

Each baseline trade uses the same asset, the same locked beta estimator, the
same 12h holding window, the same two-leg cost model, and the same non-overlap
rule. Direction is shuffled within the matched sample while preserving the
long/short count by asset.

Seed: 69. Resamples: 1000. Discovery must beat baseline p95. Validation must
report the same baseline summary but promotes only by the validation gate in
section 2.3.

## 2.6 Multiple-Testing Budget

Primary variant count for this lock candidate: 1.

The following are declared diagnostic only and cannot promote H3:

- per-asset ETH and SOL splits;
- residual threshold sensitivity around 2.0, 2.5, and 3.0;
- beta lookback sensitivity at 90 and 365 calendar days;
- holding-window sensitivity at 1, 2, 6, and 12 bars;
- alternative BTC/ETH/SOL equal-weight market basket;
- volatility-regime and session summaries;
- zero-cost, optimistic-cost, and conservative-cost tables.

Any diagnostic result selected after inspection requires a new
pre-registration and treats the inspected evidence as Stage 0 material only.

## 2.7 Look-Ahead Audit

The implementation must prove these points before any Stage 2 result is
accepted:

- beta uses only bars closed before the signal bar;
- residual scale excludes the current signal residual and all future residuals;
- entry is next-bar open, never signal-bar close;
- recent data excludes unclosed candles;
- all symbol joins use only timestamps present for all required legs;
- funding, if charged, is applied only by timestamps known at or before the
  trade interval;
- no universe member is added or removed after seeing H3 results;
- local contaminated Setup C/H price-action outputs are not used to choose H3
  thresholds or windows;
- quality gaps inside a locked window either park the attempt or are documented
  before analysis.

## 2.8 Cheap STOP / PARK Criteria Before Discovery

H3 parks before discovery if any condition is true:

- no free coverage-only path confirms all three required symbols and all three
  windows;
- fewer than 80 discovery or 40 validation observations are plausible under
  the locked signal without changing the threshold;
- the required two-leg cost model cannot be represented in the simulator or
  result artifact without ambiguity;
- beta estimates are unstable enough that hedge notional becomes operationally
  unrealistic under a pre-run beta-quality report;
- any candidate data file needed for H3 has already been opened for
  H3-relevant residual, return, spread, or outcome inspection before lock.

## 2.9 Testnet Role

Testnet can validate only implementation mechanics:

- two-leg order construction;
- hedge sizing and drift;
- cancel/replace behavior;
- partial-fill recovery;
- fee, funding, and realized-PnL accounting in paper infrastructure.

Testnet cannot validate H3 edge because it is not a held-out economic sample of
mainnet fills, liquidity, funding, and participant behavior. A testnet pass must
not promote research, paper, runtime, trading, or live readiness.

## 2.10 Owner Decisions Required Before Lock

The Owner must explicitly decide:

1. Accept or reject this single primary variant.
2. Authorize a coverage-only data contract for the candidate windows, or park
   H3 before acquisition.
3. Confirm that no H3 outcome inspection may occur until coverage passes and a
   separate Stage 2 run is authorized.
4. Confirm that diagnostics cannot rescue H3 after a primary gate miss.

## Current Recommendation

Proceed only to a coverage-only H3 data contract if the Owner accepts the
single primary variant above. Do not start discovery, validation, testnet, paper
execution, or implementation work from this document.
