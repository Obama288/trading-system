# Setup H Discovery Result

Run timestamp: 2026-06-13T15:54:11Z
Pre-registration: `research/signal_observation/SETUP_H_PREREGISTRATION.md` (LOCKED 2026-06-13)
Dataset SHA-256 (verified): `30d2027f9af6f191dfa7ff0e572b60c28b91f0c68ea8f28ec021f292b5788d05`
Discovery cutoff: `2024-09-24T04:00:00Z`
Seed: 69 | Resamples: 1000 | Primary cost: moderate (8 bps/side)

## GATE: PARK

| Condition | Required | Observed | Met? |
|-----------|----------|----------|------|
| Gated expectancy_R | ≥ +0.05R | +0.0370R | NO |
| Gated − ungated | ≥ +0.05R | -0.0481R | NO |
| Gated vs shuffled p95 | > +0.0470R | +0.0370R | NO |

PARK rationale: one or more gate conditions not met. This is family #6 tested on this data class; a miss here strengthens the H1/H2 hypothesis (crypto-perp patterns exploitable at 4H scale may be exhausted within this universe). No Stage 3 run.

---

## Primary metrics (moderate 8 bps/side)

| Metric | Value |
|--------|-------|
| Gated expectancy_R | +0.0370R |
| Ungated expectancy_R | +0.0851R |
| Difference (primary) | -0.0481R |
| Pooled obs (discovery) | 14,160 |
| LOW-VOL obs (gated active) | 7,808 |
| HIGH-VOL obs (gated flat) | 6,352 |

## Shuffled-regime baseline

1000 resamples; per symbol, same LOW-VOL bar count chosen randomly from all rebalance bars; seed = 69.

| Baseline stat | Value |
|---------------|-------|
| Shuffled mean | +0.0348R |
| Shuffled p5   | +0.0220R |
| Shuffled p50  | +0.0348R |
| Shuffled p95  | +0.0470R |
| Observed gated percentile | 60.9th |

## Cost scenario diagnostics

| Scenario | Gated | Ungated | Difference |
|----------|-------|---------|------------|
| optimistic | +0.0413R | +0.0893R | -0.0481R |
| moderate *(primary)* | +0.0370R | +0.0851R | -0.0481R |
| conservative | +0.0270R | +0.0752R | -0.0482R |

## Per-symbol breakdown (diagnostic)

| Symbol | N obs | N LOW | N HIGH | Gated exp | Ungated exp | Difference |
|--------|-------|-------|--------|-----------|-------------|------------|
| SOLUSDT | 1433 | 782 | 651 | +0.0452R | +0.1125R | -0.0673R |
| BNBUSDT | 1654 | 940 | 714 | +0.0399R | +0.0916R | -0.0517R |
| XRPUSDT | 1684 | 925 | 759 | +0.0289R | +0.0813R | -0.0524R |
| DOGEUSDT | 1503 | 881 | 622 | +0.0460R | +0.1150R | -0.0690R |
| ADAUSDT | 1664 | 893 | 771 | +0.0223R | +0.0552R | -0.0329R |
| AVAXUSDT | 1429 | 783 | 646 | +0.0563R | +0.1213R | -0.0650R |
| LINKUSDT | 1678 | 936 | 742 | +0.0412R | +0.0731R | -0.0319R |
| DOTUSDT | 1461 | 803 | 658 | +0.0152R | +0.0545R | -0.0393R |
| ZECUSDT | 1654 | 865 | 789 | +0.0402R | +0.0697R | -0.0294R |

## High-vol bucket diagnostic

Ungated TSMOM expectancy on HIGH-VOL bars only (mechanism check: should be negative if gate is filtering bad bars).

| HIGH-VOL obs | Ungated exp (moderate) |
|--------------|------------------------|
| 6,352 | +0.1004R |

---

*Report produced by `run_setup_h_discovery.py`. Do not modify manually.*

