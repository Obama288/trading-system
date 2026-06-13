# Setup E — Stage 2 Discovery Result

**GATE: PARK**

Generated: 2026-06-13T07:14:52Z
Pre-registration: LOCKED 2026-06-13 — commit 0b71d9b
Discovery window: signal bar timestamp ≤ 2026-03-09T00:00Z
Baseline seed: **42** (CANONICAL — fixed at first run, §2.4)
Baseline iterations: 1000

## Gate Verdict

Primary metric: expectancy_R @ 1.5R, post-cost moderate (8 bps/side),
pooled LONG+SHORT, non-overlapping set.

| Criterion | Required | Actual | Met? |
|---|---|---|---|
| expectancy_R ≥ +0.10R | +0.10R | -0.1085 | NO ✗ |
| above baseline p95 | > -0.0776 | -0.1085 | NO ✗ |

**GATE: PARK**

## Signal Counts

| | Count |
|---|---|
| Raw signals detected (discovery window, both directions) | 961 |
| &nbsp;&nbsp;LONG | 517 |
| &nbsp;&nbsp;SHORT | 444 |
| Valid simulations (after simcore filtering) | 961 |
| Non-overlapping set (primary metric) | 824 |

## Primary Metric — Expectancy by Cost Scenario

Non-overlapping set, 1.5R target.

| Cost scenario | bps/side | N | expectancy_R | Win% | Loss% | Flat% |
|---|---|---|---|---|---|---|
| Optimistic | 5 | 824 | -0.0821 | 22.5% | 44.7% | 32.9% |
| Moderate [PRIMARY] | 8 | 824 | -0.1085 | 22.5% | 44.7% | 32.9% |
| Conservative | 15 | 824 | -0.1702 | 22.5% | 44.7% | 32.9% |

## Random Baseline (§2.4)

1000 resamples, seed=42 (canonical). Per symbol/direction: same N as
raw signal count, random entry bars NOT within 5 bars of any cascade episode,
risk distances drawn from actual signal pool, same 1.5R target and 12-bar window.

| Statistic | Expectancy_R |
|---|---|
| min | -0.2570 |
| p5 | -0.1885 |
| p25 | -0.1542 |
| median | -0.1331 |
| p75 | -0.1120 |
| p95 | -0.0776 |
| max | -0.0303 |

Actual expectancy_R -0.1085 is at the **79th percentile** of the baseline.
Gate requires > p95 (-0.0776): NOT MET ✗

## Target-R Diagnostics (moderate cost, non-overlapping)

| Target | N | Win% | Loss% | Flat% | expectancy_R |
|---|---|---|---|---|---|
| 1R | 824 | 34.6% | 40.2% | 25.2% | -0.1023 |
| 1.5R **[PRIMARY]** | 824 | 22.5% | 44.7% | 32.9% | -0.1085 |
| 2R | 824 | 16.0% | 46.2% | 37.7% | -0.0845 |

## MFE / MAE Diagnostics (primary metric, 1.5R, non-overlapping)

Diagnostic only — no trading conclusions at Stage 2.

| Metric | Mean | Median | p25 | p75 |
|---|---|---|---|---|
| MAE_R (max adverse) | +1.0117 | +0.8053 | +0.3446 | +1.2979 |
| MFE_R (max favourable) | +0.9235 | +0.6870 | +0.2719 | +1.4212 |

## Per-Direction Breakdown (diagnostic)

| Direction | Raw signals | Valid sims | Non-overlapping | expectancy_R @ 1.5R |
|---|---|---|---|---|
| LONG | 517 | 517 | 453 | -0.2092 |
| SHORT | 444 | 444 | 371 | +0.0145 |
| Combined | 961 | 961 | 824 | -0.1085 |

## Methodology Notes

- Signal definition: §2.3 of locked pre-registration.
- Discovery window: signal bar timestamp ≤ 2026-03-09T00:00Z (single cross-symbol cutpoint).
- Non-overlapping: `simcore.selection.select_non_overlapping` at 1.5R, per symbol.
- Baseline: raw signal count per bucket (before non-overlapping selection), 1000 iterations,
  seed=42 (canonical, recorded here per §2.4 since no seed was fixed at pre-registration lock).
- Cost formula: `cost_in_r(entry_price, initial_r, bps) = 2×bps/10000 × entry_price / initial_r`.
- All outcomes via `research.simcore.simulator.simulate_trade` (NEXT_BAR_OPEN).

---

Constitution stage: 2 (Discovery). Do NOT proceed to Stage 3 without owner review.