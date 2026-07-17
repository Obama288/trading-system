# H3 - Beta-Neutral Residual Reversion Pre-Registration

Status: DRAFT / PLANNING ONLY
Family: Beta-neutral cross-sectional residual reversion
Governed by: `docs/RESEARCH_CONSTITUTION.md` and `docs/BOUNDARIES.md`

This document is a planning draft only. It does not authorize data acquisition,
data inspection, discovery, validation, testnet activity, paper trading, or live
trading.

## Gate State

H3 is the next preregistration candidate after H1 was parked at the free-data
feasibility gate with no outcome inspection. The active research family remains
none until this draft is reviewed, locked, committed as an active
pre-registration, and separately authorized by the Owner.

## Campaign Comparison-Budget Note

This campaign has already inspected or parked multiple crypto-perp families:
Setup A, Setup B, Setup C, funding/carry variants, Setup E, Setup H, and H1.
H3 must therefore be treated as a late-campaign attempt, not as a fresh
statistical slate.

H3 is still worth preregistering because it is mechanism-first and uses a
different effect framing from simple trend, liquidation, funding carry, and
venue-funding dispersion: it asks whether asset-specific displacement remains
after removing common crypto-market beta.

Any PASS would be evidence only, not proof, and must be read against the full
campaign comparison budget.

## 2.1 Hypothesis And Mechanism

Hypothesis: after removing common crypto-market beta, a large idiosyncratic
displacement in a liquid perp asset partially reverts over the next holding
window when the displacement is not confirmed by persistent asset-specific flow
or relative-strength continuation.

Mechanism / who pays: short-horizon relative-value participants and hedgers
trade the common crypto factor, while single-asset price dislocations can be
created by temporary inventory pressure, stop-runs, liquidations, or crowded
single-name attention. The counterparty is the trader extrapolating the
single-asset move as asset-specific information when it is mostly transient
residual noise after the market factor has been removed.

Mechanism risk: this can easily become disguised mean reversion or overfit
cross-sectional price action. The final lock must name the residual estimator,
holding rule, cost model, and baseline tightly enough that no post-hoc
"relative value" interpretation can rescue a weak result.

## 2.2 Primary Metric And Gate

Primary metric: post-cost expectancy_R using the canonical simulator where a
trade outcome can be represented as a two-leg beta-neutral position with costs
charged on both legs.

Primary gate: LOCK REQUIRED.

The lock must define one numeric discovery pass threshold before any H3 data
inspection. The threshold must include:

- moderate cost scenario;
- two-leg taker/slippage costs;
- funding treatment if the holding window crosses funding timestamps;
- non-overlapping observations;
- a required margin over the random or matched baseline.

No win-rate, Sharpe, spread chart, regression coefficient, per-symbol split, or
best-regime result may promote H3 unless it is the single locked primary metric.

## 2.3 Candidate Signal Definition

Primary universe: LOCK REQUIRED.

Initial candidate universe for review:

- BTCUSDT perpetual;
- ETHUSDT perpetual;
- SOLUSDT perpetual.

Candidate interval: 4h bars, subject to final lock.

Candidate beta model:

- market factor: BTCUSDT return, or an equal-weight BTC/ETH/SOL market basket;
- rolling lookback: LOCK REQUIRED;
- estimator: LOCK REQUIRED, with no future bars and no centered windows;
- residual: actual asset return minus beta-implied market return.

Candidate entry rule:

- compute trailing normalized residual displacement per asset;
- enter contrarian to the largest absolute residual only when it exceeds the
  locked threshold;
- hedge with the locked market factor or matched asset leg to target beta
  neutrality;
- no position may open while a prior H3 observation for that asset is unresolved.

Candidate exit rule:

- fixed holding window: LOCK REQUIRED;
- optional residual mean-cross exit: diagnostic only unless selected as primary
  before lock;
- stop, target, and mark-to-market convention: LOCK REQUIRED.

The final lock must decide whether H3 is expressed as:

- single residual asset versus beta hedge;
- pair trade against the most beta-matched peer;
- basket residual trade.

Only one expression may be primary.

## 2.4 Free-Data And Holdout Path

No H3 acquisition or analysis is authorized by this draft.

Candidate free path to review before lock:

- use already committed local OHLCV only for source inventory and hash binding,
  not for outcome inspection during draft work;
- if existing local data is contaminated by prior same-window price-action
  research, identify a clean venue/source/window before Stage 2;
- if public exchange downloads are needed, first create a coverage-only
  acquisition contract that checks availability, chronology, gaps, and hashes
  without computing residuals, returns, spreads, fees, or PnL.

Candidate windows: LOCK REQUIRED.

The final pre-registration must name non-overlapping discovery, validation, and
recent-rerun windows before any H3-relevant data is opened for signal or outcome
analysis. A plausible split is not enough under `docs/BOUNDARIES.md`; the path
must be confirmed and named.

## 2.5 Random Or Matched Baseline

Baseline: LOCK REQUIRED.

Candidate baseline options for review:

- same timestamps with shuffled trade direction while preserving symbol and
  holding window;
- same number of entries sampled from matched volatility and market-return
  regimes;
- residual-threshold timestamps with residual signs randomized.

The lock must choose exactly one primary baseline, seed, resample count, and
required margin. Default seed should remain 69 unless a different integer is
recorded at lock.

## 2.6 Multiple-Testing Budget

Primary variant: LOCK REQUIRED.

All of the following are potential variants and must be counted before lock if
examined:

- universe choices;
- interval choices;
- beta estimator choices;
- beta lookback lengths;
- residual normalization windows;
- residual thresholds;
- holding windows;
- exit rules;
- hedge expression;
- cost and funding assumptions;
- market-regime splits.

Any non-primary variant that looks better after inspection must return to
Stage 1 as a new pre-registration and cannot inherit H3 discovery evidence as a
confirmation result.

## 2.7 Sample Size Minimums

Defaults from the constitution:

- discovery: at least 80 non-overlapping observations;
- validation: at least 40 non-overlapping observations.

If H3 cannot reach these counts under a realistic cost-aware signal definition,
it should be parked before discovery rather than loosened after inspection.

## 2.8 Look-Ahead Audit

The final lock must explicitly audit at least these leak paths:

- beta estimated with future bars or centered windows;
- residual z-score using future distribution data;
- universe selected after seeing which asset mean-reverts best;
- thresholds chosen after inspecting residual/outcome plots;
- funding charged with information unavailable at entry time;
- using candle close as fill when the signal is defined by that same close;
- unclosed candles included in recent data;
- validation windows influenced by earlier Setup C/H price-action results;
- survivorship bias from only keeping currently liquid symbols.

## 2.9 Testnet Role

Testnet can validate mechanics only:

- two-leg order construction;
- hedge sizing drift;
- rebalance behavior;
- cancel/replace safety;
- accounting of fees, funding, and realized PnL in paper infrastructure.

Testnet cannot validate H3 edge because fills and order-book behavior are not a
held-out economic outcome sample. A testnet pass must not promote research
readiness or trading readiness.

## 2.10 Kill And Park Criteria

Park before discovery if:

- no clean free-data path exists for discovery, validation, and recent rerun;
- existing local windows are too contaminated for a defensible H3 test;
- the locked signal cannot produce the minimum observation counts;
- realistic two-leg costs dominate the expected residual movement;
- beta neutrality cannot be defined without broad implementation risk.

Park or retire after discovery if the locked primary metric misses its gate or
does not beat the locked baseline by the required margin.

Retire after validation if expectancy is negative, effect direction flips, or
the result depends on one symbol, one regime, or one unstable estimator.

Stage 5 paper entry remains forbidden until the constitution's paper-entry
requirements, authoritative paper accounting, owner sign-off, and execution
audit are satisfied.

## Owner Decisions Required Before Lock

1. Select the primary H3 expression: residual asset versus beta hedge, pair
   trade, or basket residual.
2. Lock universe, interval, beta estimator, lookback, residual normalization,
   threshold, holding window, exit rule, and costs.
3. Confirm a free, contamination-safe discovery/validation/holdout path without
   opening H3 outcome data.
4. Confirm baseline, seed, resample count, primary gate, and multiplicity
   budget.
5. Authorize any acquisition contract separately if new data is needed.

