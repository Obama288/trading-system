# Setup C Evidence Summary

Stage 54-SQ-C6 decision record. Consolidates C1–C5 research diagnostics.

---

## 1. Status

- Setup C / TSMOM remains **PASS_CANDIDATE research-only**.
- This is not paper readiness, runtime readiness, trading readiness, or live
  readiness.
- Escalation remains **HOLD** pending owner decision on next fork.

---

## 2. Evidence Reviewed

| Stage | Description |
|-------|-------------|
| C1 / C1F | Volatility-targeted gate evaluation and gate correction. Primary metric corrected to `volatility_targeted_post_cost_return`. Gate passes all six conditions on 40-bar primary. |
| C2 | Sensitivity lookbacks (20, 60), turnover/cost diagnostics, skipped vol-proxy rows documented, baseline autocorrelation, direction-change frequency. |
| C3 | Funding stress scenarios (diagnostic only), regime decomposition (observational only), sensitivity robustness separation, autocorrelation interpretation added, direction-change frequency at rebalance. |
| C4 | Raw non-volatility-targeted regime-normalization diagnostic. Confirmed high_vol raw negative and low_vol raw positive; interpretation `real_regime_dependence`. No filter introduced. |
| C5 | Discovery/validation split of high_vol / low_vol regime. Interpretation `validation_only_or_discovery_only`: pattern appears in validation split only; discovery had positive high_vol and low_vol. |

C5 independent review verdict: **PASS WITH NOTES**.

---

## 3. What Appears Supported

- 40-bar TSMOM with volatility targeting passes the current research gate on the
  available dataset (BTC/ETH/SOL 4H, ~17 months discovery + ~8 months
  validation).
- Aggregate volatility-targeted post-cost moderate return is positive in both
  discovery and validation splits.
- Funding stress does not invalidate the primary 40-bar candidate under the
  tested scenarios.
- Raw and volatility-targeted diagnostics are separated correctly throughout.
- No strategy filter has been introduced at any stage.
- Cost model (bps-per-turnover) is applied consistently; costs do not dominate
  the volatility-targeted gross return.

---

## 4. What Is Not Proven

- No paper readiness.
- No live / trading readiness.
- No proof of durable edge outside the current dataset.
- No slippage or liquidity model beyond fixed bps turnover cost.
- Funding is stress-estimated, not fully historical realized funding.
- No production or runtime behavior has been tested.
- No regime filter has been validated; regime decomposition is observational
  only.
- No out-of-dataset validation beyond the current discovery/validation split on
  the same CSVs.
- Sensitivity lookbacks (20-bar, 60-bar) are not robust: validation is negative
  for both.

---

## 5. Known Concerns

- **Regime dependence**: low_vol is consistently strong across both splits;
  high_vol is weak.
- **C4**: full-window high_vol weakness is confirmed real in both raw and
  volatility-targeted metrics (`real_regime_dependence`).
- **C5**: high_vol weakness is not a simple stable structural rule. It is absent
  in discovery (high_vol VT post-cost ≈ +2.5) and pronounced in validation
  (high_vol VT post-cost ≈ −13.1). Interpretation: `validation_only_or_discovery_only`.
- **Sensitivity robustness**: 20-bar discovery beats primary but validation is
  negative; 60-bar validation is also negative. Neither sensitivity lookback is a
  robust candidate.
- **Autocorrelation**: return-sign autocorrelation is high (~0.86) due to
  overlapping 40-bar lookback windows. This is expected and does not prove edge.
- **Dataset scope**: three symbols, single exchange, single timeframe, no
  cross-asset or multi-exchange validation.

---

## 6. Decision Point

**Current state**: PASS_CANDIDATE is maintained. Escalation remains HOLD.

The next step is a fork. Owner chooses one:

**Fork A — Expand dataset / out-of-time validation**
- Extend CSV history further or add symbols/timeframes.
- Run the same frozen research evaluation on the extended data.
- Validate whether the regime pattern and overall edge are stable.
- This is the recommended fork (see §7).

**Fork B — Define paper-trading prerequisites (without approving paper trading)**
- Document what conditions would be required before paper trading could be
  considered.
- Does not authorize paper execution; is a planning-only exercise.
- Useful only if the owner is confident enough in the current evidence.

**Fork C — Park Setup C**
- If the owner decides current evidence is insufficient, park this setup.
- No further work on TSMOM without a new design lock and explicit reactivation.

---

## 7. Recommended Next Step

**Recommendation: Fork A — expand dataset / out-of-time validation.**

Rationale:
- The current evidence is promising (gate passes, both splits positive in
  aggregate) but is single-dataset and regime-sensitive.
- C5 shows the high_vol weakness is concentrated in the validation window
  (recent ~8 months), which may reflect a genuine regime shift or data-specific
  behavior.
- A longer history or additional symbols would materially increase confidence
  before any paper-prerequisite discussion.
- Fork A is lower risk than Fork B because it does not move the discussion
  toward execution prerequisites prematurely.

Owner may choose Fork B or C instead. This is a recommendation, not a
decision.

---

## 8. Boundaries

- No paper / runtime / trading / live readiness is claimed or implied.
- No strategy filter is introduced or approved.
- No private endpoints, API keys, account access, order submission, or
  execution of any kind.
- No sizing with capital.
- Research-only scope is unchanged.

---

## 9. Post-C7 Future Fork Notes

- If C7 fails or parks Setup C: run a Data Reconnaissance (DR1) design lock
  before designing any new setup family. Do not design Setup D directly.
- Future setup evaluation should use a compressed path: pre-filter, Stage 1
  with all key metrics, at most one same-dataset diagnostic, then out-of-time
  or FAIL/PARK. Avoid repeating the C1–C6 diagnostic chain length.
- See `docs/STAGE_54_SQ_C7_EXPANDED_VALIDATION_DESIGN_LOCK.md` §§ Future
  Setup Evaluation Process Principles / Post-C7 Fork: Data Reconnaissance.
