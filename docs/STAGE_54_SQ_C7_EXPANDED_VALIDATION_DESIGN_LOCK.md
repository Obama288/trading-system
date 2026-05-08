# Stage 54-SQ-C7 Expanded Validation Design Lock

## Purpose

Setup C / TSMOM passed C1–C6 on the current Bitget 4H dataset as
PASS_CANDIDATE research-only.

C7 tests whether the candidate survives expanded public data outside the
current C1–C6 sample.

This is research-only and does not authorize paper trading, runtime wiring,
live trading, private API access, or readiness promotion.

---

## Dataset Expansion Definition

Out-of-time data is defined as data outside both the current discovery and
validation windows used in C1–C6.

**Allowed expansion directions:**
- backward extension before the current discovery start;
- forward extension after the current validation end;
- or both, if boundaries are locked before analysis.

**Current Development Window (from C1–C6 report artifacts):**
- Full candle range used: 2023-12-17T16:00:00+00:00 to 2026-05-06T08:00:00+00:00.
- First rebalance bar (discovery start): 2023-12-27T16:00:00+00:00.
- Last discovery bar / first validation bar: 2025-08-19T16:00:00+00:00 / 2025-08-20T16:00:00+00:00.
- Last rebalance bar (validation end): 2026-05-04T20:00:00+00:00.
- Last candle used: 2026-05-06T08:00:00+00:00.

No candle within 2023-12-17T16:00:00+00:00 to 2026-05-06T08:00:00+00:00 (inclusive)
may be counted as expanded holdout data. Expanded holdout must be strictly outside
this range.

**Rules:**
- No interval from the current C1–C6 dataset may be counted as expanded
  holdout data.
- Current dataset is treated as development evidence.
- Expanded data is treated as holdout evidence.
- No mixing, no re-splitting, no moving boundaries after download.

**Allowed source:**
- Public Bitget 4H OHLCV only.
- Offline/local analysis after one approved public download.

**Symbols:** BTCUSDT, ETHUSDT, SOLUSDT (unchanged).

**Timeframe:** 4H (unchanged).

**One download, one run:**
- Data must be downloaded once before analysis.
- No iterative expansion after seeing results.

---

## Frozen Components

The following must remain unchanged in C7:

- Setup C detector (no code changes).
- 40-bar primary lookback.
- 20-bar and 60-bar sensitivity lookbacks (if reported).
- Rebalance every 6 bars.
- Volatility proxy ATR(20) / close.
- Same existing cost tiers (optimistic 2 bps, moderate 4 bps, conservative
  6 bps per turnover unit).
- Moderate cost scenario remains the primary non-funding cost scenario.
- Random baseline methodology and deterministic seed policy.
- Symbols and timeframe.

**No parameter optimization is allowed in C7.**

---

## Vol Proxy Threshold Policy

**Decision:** high_vol / low_vol thresholds for expanded holdout diagnostics
use the expanded window only.

**Rationale:** this simulates what would be computed on available out-of-time
data without carrying development-set thresholds into the holdout.

This is a design decision and must not be changed after seeing expanded
results.

Regime diagnostics remain observational only and do not introduce filters.

---

## Funding Stress In Gate

Funding stress is **no longer diagnostic-only** for C7.

C7 PASS requires funding-adjusted volatility-targeted post-cost return to
remain positive under the **high_cost** funding scenario on the expanded
holdout window.

The exact high_cost scenario must match C3 (0.0003 per 8H) unless separately
owner-approved before implementation.

---

## C7 PASS Gate

All five conditions must hold on the expanded holdout window:

1. Expanded holdout volatility-targeted post-cost moderate return **> 0**.
2. Expanded holdout beats conditional random **p75** on the
   volatility-targeted primary metric.
3. Expanded holdout funding-adjusted volatility-targeted post-cost return
   **> 0** under high_cost funding stress.
4. At least **2 of 3 symbols** are non-negative on the expanded holdout
   window.
5. Volatility-targeted post-cost moderate return recomputed on the **union**
   of development and expanded holdout intervals is at least **50% of the
   development-only value**. (This is not the arithmetic sum of separately
   reported development and expanded headline values; it requires a single
   recomputation over the combined interval set.)

The 50% combined-retention threshold is provisional and owner-approved for
this C7 design lock only. It must not be adjusted after seeing expanded
results.

---

## C7 HOLD Gate

HOLD if:
- expanded holdout volatility-targeted post-cost moderate return **> 0**, but
- random p75, funding stress, symbol count, or combined-retention gate fails.

HOLD requires independent review before any next step.

---

## C7 FAIL Gate

FAIL if:
- expanded holdout volatility-targeted post-cost moderate return **≤ 0**.

FAIL means Setup C leaves active PASS_CANDIDATE status and requires a
research decision / structural review before any new setup family or
continuation work.

**No C7b / C7c rescue stages are authorized by default.**

---

## Anti-Cherry-Picking Rules

- One approved public data download before analysis.
- No re-download after seeing results.
- No lookback changes.
- No rebalance changes.
- No symbol additions.
- No timeframe additions.
- No threshold changes after results.
- No subgroup filtering.
- No regime filter introduction.
- No gate criteria changes after seeing expanded results.
- Expanded window boundaries are locked at download time.

---

## Regime Diagnostics

Report high_vol / low_vol split on the expanded holdout window.

Compare expanded regime behavior to C4/C5 development findings:
- full-window high_vol weakness (C4: `real_regime_dependence`);
- low_vol strength (consistent across both C4 and C5 splits);
- validation-only / variable high_vol weakness (C5:
  `validation_only_or_discovery_only`).

This is observational only and does not introduce a filter.

---

## What C7 Does Not Authorize

C7 does not authorize:
- paper trading;
- live trading;
- runtime wiring;
- private API access;
- exchange operations;
- parameter optimization;
- strategy filters;
- order_status, orders, cancels, set_leverage, live reconcile, or live
  execution;
- readiness claims of any kind.

---

## Future Setup Evaluation Process Principles

Approved for record only. Not authorization to implement any new setup.

For future setup families evaluated after C7:

- **Pre-filter before code**: confirm mechanism, expected signal frequency, and
  cost floor before writing any evaluation code.
- **Stage 1 must include**: observations, random baseline, post-cost metrics,
  funding estimate, and regime tags.
- **At most one** targeted same-dataset diagnostic after Stage 1.
- **Then out-of-time validation or FAIL/PARK.** Do not add further same-dataset
  diagnostic rounds.
- Avoid repeating the C1–C6 same-dataset diagnostic chain for future setups.

---

## Post-C7 Fork: Data Reconnaissance

If C7 fails or parks Setup C, do not design Setup D directly.

First run a Data Reconnaissance design lock to identify whether the data
contains predictability before committing to a new signal family.

Data Reconnaissance candidate tests (for a future DR1 design lock only):
- non-overlapping return autocorrelation across lags and horizons;
- Lo–MacKinlay variance ratio;
- BTC → ETH/SOL cross-asset lead-lag;
- public funding / open interest feasibility.

Do not implement DR1 now. Do not create a DR1 design lock now.
This is future-fork guidance only.

---

## Required Review Before Implementation

This design lock must be independently reviewed before any C7 implementation
prompt is created.

Reviewer should confirm:
- holdout separation is unambiguous and non-leaking;
- frozen components are complete and sufficient;
- vol proxy threshold policy is stated and locked;
- funding stress gate condition is clear and matches C3;
- PASS / HOLD / FAIL gates are unambiguous;
- anti-cherry-picking rules are sufficient;
- no readiness promotion is present or implied.
