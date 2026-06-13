# Setup E — Decision Record: PARKED at Stage 2

Family: Post-Liquidation Exhaustion Reversal
Stage: 2 (Discovery)
Date: 2026-06-13
Verdict: **PARKED**

## Gate Result

Both gate criteria unmet. Primary metric below the hard threshold and below the
random-baseline p95.

| Criterion | Required | Actual | Met? |
|---|---|---|---|
| expectancy_R ≥ +0.10R at 1.5R | +0.10R | −0.1085 R | NO |
| above random-baseline p95 | > −0.0776 | −0.1085 | NO |

Signal counts: 961 raw signals detected (517 LONG + 444 SHORT) in discovery
window; 824 non-overlapping after simcore selection. Win rate at 1.5R: 22.5%
(break-even ≈ 40%). Baseline seed: 42 (canonical, §2.4). All 1000 baseline
iterations also produced negative expectancy — the baseline p95 itself is
negative (−0.0776R), indicating the 12-bar outcome window did not capture a
positive edge for any entry style in this regime.

## Diagnostic Observations (not conclusions)

- SHORT-only direction: expectancy −0.0145R at 1.5R. Not actionable without a
  separate pre-registration treating discovery data as contaminated.
- 2R target: −0.0845R (slightly better than 1.5R; still negative).
- The entire baseline distribution is negative, suggesting the 12-bar window
  is structurally too short or the threshold definitions too loose for this
  data range.

## Reason for Park

Gate miss per pre-registration §2.2 (expectancy_R < +0.10R, below baseline
p95). Per §2.7: "Stage 2: gate miss → family parked; one re-registration
permitted only with a materially different mechanism statement."

## References

- Pre-registration (LOCKED): `research/signal_observation/SETUP_E_PREREGISTRATION.md`
  (commit 0b71d9b, 2026-06-13)
- Discovery result: `research/signal_observation/SETUP_E_DISCOVERY_RESULT.md`
  (commit 6dae9a6, 2026-06-13)
- Feasibility report: `research/signal_observation/SETUP_E_FEASIBILITY_REPORT.md`
- Hypothesis: `research/signal_observation/SETUP_E_HYPOTHESIS.md`

## Re-registration Eligibility (§2.7)

One re-registration is permitted only with a materially different mechanism
statement — for example a continuation or momentum branch of the cascade
signal, not the reversal branch tested here. Requirements for any
re-registration:

1. Mechanism statement must differ materially from §2.1 of the parked
   pre-registration ("price mean-reverts against the cascade direction").
2. The current discovery data (signal bar timestamps ≤ 2026-03-09T00:00Z)
   must be treated as seen data and cannot serve as a fresh held-out window.
   A new non-overlapping held-out window is required.
3. The re-registration must be treated as a fresh Stage 0 candidate entering
   the full pipeline.
4. No outcome metric from this discovery run may be used to select or tune
   parameters in the re-registration (would constitute data snooping).
