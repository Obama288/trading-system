# Stage 54-SQ-SR1 - Price-Action Continuation Structural Review

## Status

Stage: 54-SQ-SR1
Status: structural review / research stop-loss
Scope: docs-only review of the price-action continuation signal family

This document records a research conclusion only. It does not change project
readiness, runtime scope, detector logic, data, or execution policy.

Live trading remains NO-GO.

## Executive Verdict

The price-action continuation family is retired as the primary
signal-research direction for now.

This is not a project failure. It is a family-level research stop-loss result:
multiple related hypotheses were tested, compared against random baselines,
checked against costs, and failed to produce durable evidence.

Paper trading, runtime wiring, probe readiness, and live trading remain NO-GO.

Final next-family decision: OWNER_DECISION_REQUIRED.

## Family Definition

For this review, the price-action continuation family includes:

- breakout-retest continuation;
- trend pullback BOS / continuation;
- high-volatility continuation branches built on the same entry family;
- fixed-R exit variants built on the same continuation entries.

## Attempts Reviewed

### Setup A - Breakout-Retest-Continuation

Setup A was too rare on the Bitget USDT-FUTURES BTCUSDT, ETHUSDT, and SOLUSDT
4H/1H research dataset.

Baseline output produced 6 observations total:

- BTCUSDT: 4 observations;
- ETHUSDT: 1 observation;
- SOLUSDT: 1 observation.

The main funnel drop-off was range/touch scarcity, followed by limited breakout
opportunity. Sensitivity variants increased frequency, but the best frequency
variant still reached only 23 observations and aggregate expectancy remained
negative. This did not provide adequate evidence for continuation.

### Setup B General - Trend Pullback BOS / Continuation

Setup B solved the frequency problem better than Setup A, producing 68
research-valid 4H observations across symbols and directions.

However, general Setup B did not meaningfully beat a matched random-entry
baseline:

- 1R expectancy: 0R, random median: 0R;
- 1.5R expectancy: -0.0441R, only above random median and below random p75;
- 2R expectancy: -0.2059R, worse than random median.

Flat rate was worse than random across targets. General Setup B was retired.

### Setup B High-Vol 1.5R

The high-volatility branch formally passed a weak validation gate at 1.5R:

- validation high-vol subset: n=62;
- raw 1.5R expectancy: +0.0081R;
- conditional random p75 was below the raw result.

Cost-aware review showed the edge was too thin:

- optimistic 0.04R cost: -0.0319R;
- moderate 0.08R cost: -0.0719R;
- conservative 0.12R cost: -0.1119R.

The branch failed cost-aware reality checks and did not authorize paper trading
or live trading.

### Setup B High-Vol 1R Exit

B7 tested the bounded exit variants from the B7 design lock. Variant A, fixed
1R, passed as a weak research candidate on the validation window:

- validation n: 62;
- post-cost moderate expectancy: +0.0168R;
- conditional random p75 post-cost moderate: -0.0316R.

B8 then ran the required discovery-window cross-check. The discovery high-vol
subset had n=16 and positive post-cost moderate expectancy, but did not beat
conditional random p75:

- discovery post-cost moderate expectancy: +0.045R;
- discovery conditional random p75 post-cost moderate: +0.1075R.

B8 final decision: RETIRE_HIGH_VOL_SETUP_B.

## Common Failure Modes

- Pattern logic did not show enough durable mechanism after random comparison.
- Setup A exposed the frequency problem; Setup B exposed the edge problem.
- The observed edge was too thin relative to crypto futures cost assumptions.
- Exit changes improved raw results in places, but random entries improved as
  much or more under comparable logic.
- The 4H / 3-symbol universe was too thin for narrow conditional
  price-action continuation branches.
- Conditional branches created low sample sizes and high uncertainty.

## Lessons Learned

- Random-entry baseline should be included early, not after several variants.
- Cost-aware metrics should be included early, not after a formal raw pass.
- MFE and MAE diagnostics are useful, but they cannot create edge by
  themselves.
- Conditional diagnostics need conditional random baselines.
- A formal research pass is not tradeability.
- No paper or live stage should proceed without post-cost validated edge.
- Positive expectancy alone is insufficient when random p75 is higher.
- Analysis stages should verify whether artifacts contain row-level data before
  asking for implementation. If row-level data is absent, authorize
  deterministic reconstruction with exact-match checks or require STOP.

## Why Not Continue With Similar Setup C

Setup C should not be another BOS, breakout-retest, pullback-continuation, or
continuation-price-action variant.

Any next setup must come from a materially different signal family. Continuing
inside the same family would violate the family-level research stop-loss.

## Next Family Selection Criteria

The next family must pass all three pre-design filters.

### A. Mechanism

The family must have an explicit market mechanism explaining why an edge should
exist and why it could persist.

### B. Frequency / Data Sufficiency

The family must plausibly generate enough observations for evaluation on the
available data.

### C. Cost Floor

The expected edge magnitude must plausibly exceed the crypto futures cost floor.
The first implementation/evaluation stage must include cost-aware metrics.

## Trader / Research Input

Best next family recommendation:

- TSMOM / trend-following + volatility targeting.

Reason:

- stronger market mechanism;
- higher expected frequency;
- materially different from failed price-action continuation;
- public OHLCV is sufficient for a base version;
- random baseline and cost model can be included from the first evaluation
  stage.

Backup:

- mean reversion after overextension.

Not recommended as the next primary family:

- volatility expansion as a primary signal, because it is too close to Setup B
  high-volatility logic;
- BTC-led alt continuation as a primary Setup C, because it is narrower and
  better suited as a later context layer;
- any BOS, breakout, pullback-continuation, or continuation-price-action
  variant.

## Tower Control Recommendation

Recommended next family for Owner approval:

- TSMOM / trend-following + volatility targeting.

Backup:

- mean reversion after overextension.

Setup C must not begin until Owner gives GO.

Final next-family decision: OWNER_DECISION_REQUIRED.

## Recommended Next Stage

Stage 54-SQ-C0 may begin only after Owner approval.

C0 must be design-lock only. It must not be a price-action continuation design.
It must include random baseline and cost model requirements in the first
implementation/evaluation stage.

## Boundaries

- No paper trading.
- No live trading.
- No private API.
- No runtime wiring.
- No execution work.
- No Setup C design lock is started by this review.
- Live trading remains NO-GO.
