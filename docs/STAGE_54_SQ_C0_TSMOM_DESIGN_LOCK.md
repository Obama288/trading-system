# Stage 54-SQ-C0 - TSMOM / Volatility Targeting Design Lock

## Status

Stage: 54-SQ-C0
Status: design lock / research spec only
Scope: docs-only Setup C design

Human Owner decision:

- GO Setup C = TSMOM / trend-following + volatility targeting.
- Backup family = mean reversion after overextension.

This document does not implement Setup C, run metrics, modify data, or change
runtime behavior.

Live trading remains NO-GO.

## Executive Verdict

Setup C family is TSMOM / trend-following + volatility targeting.

This is a materially different family from the retired price-action
continuation family. The signal is based on recent return persistence and
volatility-normalized exposure, not visual chart-pattern continuation.

This stage is design-only. It does not authorize paper trading, live trading,
runtime wiring, private API use, or execution work.

## Background

Stage 54-SQ-SR1 retired price-action continuation as the primary
signal-research direction.

Reviewed evidence:

- Setup A failed because Breakout-Retest-Continuation was observation-starved.
- Setup B general produced more observations but did not meaningfully beat
  random-entry baselines.
- Setup B high-volatility branches were either too thin after costs or failed
  conditional random cross-checks.
- SR1 concluded that another BOS, breakout-retest, pullback-continuation, or
  continuation-price-action setup should not become Setup C.

Two independent trade-research reviews and Tower Control recommended TSMOM /
trend-following + volatility targeting as the next family. The Human Owner gave
GO for Setup C on that family.

## Market Hypothesis

Recent returns may contain directional persistence over intermediate horizons.
Trend-following attempts to capture that persistence.

Volatility targeting normalizes research exposure across changing crypto
regimes so that performance is not dominated only by high-volatility periods.

The hypothesized edge source is return persistence after volatility
normalization, not chart-pattern continuation.

## Difference From Retired Family

Setup C must not use:

- BOS;
- breakout-retest;
- pullback-continuation;
- structure-break entry;
- visual chart-pattern triggers.

Setup C signal is a continuous function of recent returns. Evaluation focuses on
directional persistence and volatility-normalized performance.

## Universe And Data

Frozen for C1:

- Venue/data source: existing Bitget public OHLCV.
- Symbols: BTCUSDT, ETHUSDT, SOLUSDT.
- Product type: USDT-FUTURES where existing data applies.
- Timeframe: 4H first.
- No new symbols in C1.
- No 1H in C1.
- No private data.
- No new data download during C0.

## Primary Signal Definition

Primary Setup C signal:

- Compute close-to-close lookback return over 40 bars.
- Direction:
  - long if lookback return > 0;
  - short if lookback return < 0;
  - flat only for insufficient-data warmup or exactly zero return.
- Rebalance every 6 bars, approximately daily on 4H data.
- Signal is evaluated only on rebalance bars.
- No intrabar execution assumption.

Rebalance provenance:

- the 6-bar rebalance period is a pre-specified design choice;
- it was not selected from C1 results;
- it must not be changed during C1 based on observed performance.

Sensitivity lookbacks:

- 20-bar lookback;
- 60-bar lookback.

Rules:

- 40-bar is the primary design.
- 20 and 60 are sensitivity only.
- Do not choose the best C1 lookback as final.
- No grid search.
- No extra lookbacks.

## Volatility Targeting Definition

Initial C1 volatility estimate:

- 20-bar ATR normalized by close: `ATR(20) / close`.

Reason:

- the current research stack already has deterministic ATR utilities;
- normalized ATR gives a simple local OHLCV-based risk proxy;
- it avoids introducing a new realized-volatility implementation in the design
  lock.

Rules:

- Position/risk scaling is inverse to the volatility estimate.
- Volatility targeting is part of the baseline signal design, not a post-hoc
  filter.
- Do not optimize the volatility window in C1.
- No leverage or account sizing.
- C1 should output normalized research returns or R-style metrics only, not
  live position sizes.

## Exit / Holding Model

TSMOM is not fixed-R price-action trading.

Primary exit:

- signal reversal or rebalance-driven direction change.

Research accounting:

- if signal changes from long to short, close long and open short in the
  research series;
- if signal changes from short to long, close short and open long in the
  research series;
- if signal remains the same, maintain the position;
- if signal is flat during warmup or exact zero-return state, hold no position.

Forbidden in C1:

- stop-loss overlays;
- take-profit overlays;
- trailing stops;
- fixed 1R / 1.5R / 2R targets;
- trade-management optimization.

## Cost Model

C1 must include cost-aware metrics from the first evaluation.

Because TSMOM uses return accounting rather than fixed-R trade outcomes, C1
should use bps-per-turnover costs:

| Scenario | Cost Assumption |
| --- | --- |
| optimistic | 2 bps per side / 4 bps round trip |
| moderate | 4 bps per side / 8 bps round trip |
| conservative | 6 bps per side / 12 bps round trip |

Definitions:

- Cost applies when research exposure changes.
- A long-to-short flip is two sides: close old exposure and open new exposure.
- A same-direction maintained position has no new turnover cost.
- Moderate cost is the primary gate.
- C1 bps-per-turnover metrics exclude funding costs.

Rules:

- Report optimistic, moderate, and conservative scenarios.
- No cost-free PASS is allowed.
- Funding-cost exclusion is a known limitation.
- Any C1 PASS is not funding-cost-complete.
- Funding impact must be evaluated in a later stage before any paper or live
  discussion.
- If C1 cannot map turnover costs cleanly, STOP and ask before substituting a
  different model.

## Random Baseline

C1 must include a random baseline from the first evaluation.

The random baseline must preserve:

- same rebalance schedule;
- same volatility targeting/scaling;
- same symbols;
- same available bars;
- same cost model;
- randomized direction.

Random direction sampling:

- use i.i.d. uniform `+1` / `-1` direction;
- sample independently per symbol per rebalance bar;
- preserve the same rebalance schedule, volatility targeting, costs, and bars.

Purpose:

- isolate whether TSMOM direction adds value beyond volatility targeting and
  schedule.

Required:

- deterministic seed;
- 1000 iterations minimum unless runtime makes this impractical, then STOP and
  ask;
- report median, p75, and p90 for primary metrics.

## Metrics

C1 must report at minimum:

- observation / rebalance count;
- number of direction changes / trades;
- gross return or normalized expectancy;
- post-cost return / expectancy under all cost scenarios;
- Sharpe-like metric if meaningful;
- max drawdown-like metric if implemented;
- turnover;
- per-symbol breakdown;
- pooled portfolio-style result;
- random baseline comparison;
- autocorrelation diagnostics for fixed lookbacks 20, 40, and 60 only;
- MFE / MAE if trade segmentation is implemented.

MFE / MAE is diagnostic only and must not become the primary kill gate for
TSMOM.

## C1 Pass / Park / Fail Gates

### Primary PASS Candidate

The primary 40-bar TSMOM design can be marked as a research pass candidate only
if all are true:

- post-cost moderate result > 0;
- beats random p75 under the same cost model;
- at least 2 of 3 symbols individually show post-cost moderate result > 0;
- pooled result alone is insufficient for PASS if only one symbol is positive;
- turnover is not so high that costs dominate gross performance;
- validation post-cost moderate result is >= 0.

A PASS candidate is still research-only. It is not paper-ready or live-ready.

If validation post-cost moderate result is negative, C1 cannot PASS.

### PARK

Park if:

- TSMOM beats random median but not p75;
- or post-cost result is positive but unstable across symbols/windows;
- or sensitivity variants look better than the 40-bar primary while the primary
  does not pass.

PARK means more review is needed. It is not C1 pass.

### FAIL

Fail if:

- post-cost moderate result <= 0;
- does not beat random median;
- random direction with volatility targeting performs similarly or better;
- result only exists in one symbol;
- costs consume most or all gross edge.

## Validation / Split Rule

C1 should use a predefined time split:

- discovery: earlier 70 percent of available data by time;
- validation: most recent 30 percent by time.

Rules:

- no parameter changes after discovery;
- report discovery and validation separately;
- validation post-cost moderate result must be >= 0 for PASS;
- if data length or implementation constraints make this split invalid, STOP
  and ask.

## Anti-Overfitting Rules

- No lookback sweep beyond 20 / 40 / 60.
- Primary is 40, not best-of-three.
- No new filters after seeing C1 results.
- No regime filter promotion from diagnostics in the same window.
- No symbol-specific parameter sets.
- No timeframe expansion in C1.
- No BTC-led overlay in C1.
- No ML or meta-labeling in C1.
- No stop or target overlay in C1.
- No paper or live claims.

## C1 Implementation Note

C1 must implement and test deterministic close-to-close lookback return
calculation if no existing utility exists.

That utility is research-only and must not modify existing detector logic.

## Family Stop-Loss

Setup C is the first attempt in the TSMOM family.

If C1 fails hard, do not tune endlessly. If the primary 40-bar design and the
allowed 20/60 sensitivity variants fail, the next route is Owner / Tower Control
decision, likely toward the mean-reversion backup family.

Any future TSMOM variants count toward the family-level stop-loss.

## Backup Family

Backup family:

- mean reversion after overextension.

It is not implemented or designed in C0. It becomes relevant only after Setup C
results and an Owner / Tower Control decision.

## Boundaries

- No paper trading.
- No live trading.
- No private API.
- No runtime wiring.
- No execution work.
- No account, balance, position, order, cancel, or set_leverage behavior.
- Live trading remains NO-GO.

## Next Allowed Stage

Stage 54-SQ-C1 implementation/evaluation is allowed only after C0 review and
Owner GO.

C1 must be research-only. It must include random baseline and cost-aware metrics
from the first run. C1 must not add runtime wiring, private API use, paper
trading, or live trading.
