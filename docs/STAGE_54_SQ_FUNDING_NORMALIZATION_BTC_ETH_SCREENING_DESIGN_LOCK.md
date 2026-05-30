# Stage 54-SQ Funding Normalization — BTC/ETH-Only Screening Design Lock

> **Status: SCREENING DESIGN LOCK / NO SCREENING EXECUTION AUTHORIZED**
> This document converts the Funding Normalization pre-registration into a
> parameter-locked screening specification for a bounded BTC/ETH-only discovery
> run. It does not authorize screening execution, data acquisition, data
> inspection, statistical analysis, validation, implementation, readiness, paper,
> probe, runtime, live activity, or capital use. Screening execution requires a
> separate Owner GO decision after this design lock is reviewed.

---

## 1. Status and Boundary

**Status:** SCREENING DESIGN LOCK / NO SCREENING EXECUTION AUTHORIZED.

This document converts the committed pre-registration
(`research/signal_observation/FUNDING_NORMALIZATION_PREREGISTRATION.md`,
commit `1d91532`) into a fully parameter-locked screening specification. All
screening parameters are fixed in this document without any data inspection. No
screening run has been conducted. No raw data has been opened or analyzed in
this design step.

**What this document does:**
Locks all parameters needed for a bounded BTC/ETH-only discovery screening run,
so that if Owner later authorizes execution, no parameter can be changed or
selected after data is opened.

**What this document does not authorize:**
- Screening execution or data inspection.
- Data acquisition (no new data of any kind).
- D1 analysis (see §3 — D1 HOLD remains in effect).
- Validation of any kind (held-out slice is protected).
- Readiness promotion (paper, probe, runtime, live).
- Capital use or allocation decisions.
- SOLUSDT inclusion.
- Any future pair inclusion.
- Any new stage creation.

**Screening execution requires a separate explicit Owner GO decision** (see §12).
Absence of that decision means no screening proceeds.

---

## 2. Candidate Identity

- **Candidate name:** Funding Normalization
- **Branch:** Sideways Carry / Normalization (Branch A)
- **Harness family:** Continuous-State (Family B)
- **Pre-registration source:**
  `research/signal_observation/FUNDING_NORMALIZATION_PREREGISTRATION.md`
  (commit `1d91532`)
- **Harness methodology source:**
  `docs/STAGE_54_SQ_REUSABLE_CHEAP_FALSIFICATION_HARNESS_PROPOSAL.md`
  (AUTHORIZED METHODOLOGY / NO SCREENING AUTHORIZED)

**Scope — in this design lock:**
- BTCUSDT perpetual (Binance USDT-M): in scope.
- ETHUSDT perpetual (Binance USDT-M): in scope.

**Scope — explicitly excluded from this design lock:**
- SOLUSDT perpetual (Binance USDT-M): **excluded from first-pass screening.**
  SOLUSDT remains RETAINED/FLAGGED NON_STANDARD_INTERVALS_FOUND. A separate
  SOL handling decision and separate Owner authorization are required before SOL
  can be included in any screening run. Nothing in this document changes that
  status.
- No future pairs: no instrument beyond BTCUSDT and ETHUSDT may be added to
  screening scope without a separate design lock amendment and Owner
  authorization.

**Relationship to Setup D:** Setup D (Funding Carry / Funding Stress) covers
directional stress and carry branches in a trend-agnostic or stress-event
framing. This design lock is scoped to the sideways-regime normalization
sub-hypothesis, which requires an explicit sideways price regime as a mandatory
condition. These are structurally separate hypotheses. D1 analysis remains HOLD
and is not affected by this document.

---

## 3. Data Boundary

**Data permitted for screening (if later authorized):**

| Source | Description | Status |
|---|---|---|
| BTCUSDT D1 funding | Binance USDT-M, 8H intervals, 2022-01-01 to 2023-12-17, 2147 rows | PASS — eligible |
| ETHUSDT D1 funding | Binance USDT-M, 8H intervals, 2022-01-01 to 2023-12-17, 2147 rows | PASS — eligible |
| Binance 4H OHLCV (C7 artifact, commit `583e724`) | Binance USDT-M, 4H bars, BTCUSDT and ETHUSDT, same window | Candidate OHLCV source — alignment confirmation required (see §11) |
| SOLUSDT D1 funding | Binance USDT-M, 2222 rows, non-standard intervals | EXCLUDED from this design lock |

**Acquisition metadata source (used in this design step without opening raw data):**
`research/signal_observation/setup_d_d1_funding_acquisition/d1_funding_acquisition_summary.txt`
and `d1_funding_validation_report.json` — used as metadata only.

**Data boundary rules:**
- No 2024+ data.
- No reserved or recent windows beyond 2023-12-17T08:00:00Z.
- No private endpoint data, API keys, credentials, account data, or signed
  payloads.
- No SOLUSDT, no new pairs.
- Raw funding data files: not opened in this design step. Opened only if
  screening is authorized by Owner.

**D1 analysis HOLD:** The D1 analysis HOLD (SOL interval policy decision +
separate D1 analysis design lock) remains in effect and applies to the D1
dataset as a Setup D analysis artifact. This Funding Normalization design lock
is a separate document and does not satisfy or lift any D1 HOLD conditions.

---

## 4. Discovery / Held-Out Split

**Locked split:** Chronological 70/30, row-count-based (mechanically corrected
from pre-registration approximation).

**Correction note:** The pre-registration (§7, Option A) listed approximate
dates of "2022-01-01 to 2023-01-25 (~70%)" for the discovery window. Those
dates represent approximately 54% of the full calendar window, not 70%. This
design lock supersedes those approximate dates with a mechanically correct
row-count-based 70/30 definition derived from the D1 acquisition metadata
(2147 rows, 8H intervals) without opening raw data.

**Locked discovery / held-out boundary:**

| Parameter | Value |
|---|---|
| Total rows per symbol (BTC, ETH) | 2147 |
| Discovery rows | 1502 (first 70.0% in fundingTime ascending order) |
| Held-out rows | 645 (remaining 30.0%) |
| Discovery start | 2022-01-01T00:00:00Z (row 1) |
| Discovery end (approx.) | 2023-05-15T08:00:00Z (row 1502, derived: row 1 + 1501 × 8H) |
| Held-out start (approx.) | 2023-05-15T16:00:00Z (row 1503) |
| Held-out end | 2023-12-17T08:00:00Z (row 2147) |

Approximate calendar dates are derived from D1 metadata without opening raw
data. The authoritative boundary definition is **row count in fundingTime
ascending order: rows 1–1502 = discovery; rows 1503–2147 = held-out.** If
screening is authorized, the screener must report the actual fundingTime values
of rows 1502 and 1503 as confirmation that the boundary was applied correctly.

**Held-out protection rules:**
- Rows 1503–2147 must not be opened, loaded, filtered, or used in any
  computation during screening.
- All percentile thresholds (§5) are computed from discovery rows only.
- The sideways regime classifier (§5) is applied only to discovery rows during
  screening.
- No state label, forward return value, or regime classification is computed for
  held-out rows during screening.
- Held-out validation is a separate protected-lane step that requires explicit
  Owner authorization after screening is complete and reviewed. Labeling a
  sub-segment of already-inspected discovery rows as "held-out" is not
  permitted.

**SOLUSDT split:** Not defined. SOLUSDT is excluded from this design lock.

---

## 5. State Definitions — Locked Thresholds

All thresholds below are pre-registered from structural rationale only. No raw
data was inspected to derive them. These definitions must be applied exactly as
stated if screening is authorized. No threshold may be revised after data is
opened.

### Condition 1 — Funding Displacement State

Funding state is assigned per symbol, per discovery-slice row, using percentile
boundaries computed from the discovery-slice fundingRate series for that symbol:

| State label | Boundary rule |
|---|---|
| HIGH | fundingRate ≥ p80 of discovery-slice fundingRate for this symbol |
| TRANSITION_HIGH | fundingRate in (p70, p80) — excluded from active and baseline comparisons |
| NEUTRAL | fundingRate in [p30, p70] — baseline comparison bucket |
| TRANSITION_LOW | fundingRate in (p20, p30) — excluded from active and baseline comparisons |
| LOW | fundingRate ≤ p20 of discovery-slice fundingRate for this symbol |

**Transition bands (p20–p30 and p70–p80) are excluded** from all state
comparisons. This prevents borderline observations from contaminating either
active or baseline buckets.

**Active-state displacement buckets:** HIGH and LOW. These are treated as two
separate branches evaluated independently: the HIGH branch (elevated funding in
sideways regime) and the LOW branch (compressed funding in sideways regime).
Results from HIGH and LOW branches may not be combined into one label.

**Neutral baseline:** rows with Condition 1 = NEUTRAL serve as the within-
instrument, within-discovery-slice baseline comparison group.

**Percentile computation rule:** p20, p30, p70, p80 are computed from the
discovery-slice fundingRate series for each symbol separately, sorted
ascending. No percentile computation is applied to held-out rows or performed
before screening is authorized.

**Structural rationale for 20th/80th percentile boundaries:**
- Top and bottom 20% capture a material displacement without being so extreme
  that the sample collapses to a handful of observations. At 20%, each symbol
  contributes approximately 300 active-state observations from the discovery
  slice (1502 rows × 0.20 = ~300).
- Excluding the 10%-wide transition bands on each side (p20–p30 and p70–p80)
  ensures the active and neutral groups are cleanly separated. This reduces the
  risk that near-threshold noise contaminates either comparison bucket.
- These boundaries are conventional percentile anchors chosen before inspection;
  they are not calibrated from data.

### Condition 2 — Sideways Regime State

**Pre-registered classifier** (applied to OHLCV aligned to funding timestamps):

| Parameter | Locked value | Rationale |
|---|---|---|
| Input price field | Close price of the 4H kline whose interval ends at fundingTime t; Binance OHLCV CSV timestamps are kline open times, so the aligned CSV row has open timestamp t − 4H | Do not use any CSV row with open timestamp ≥ t as price context for observation at fundingTime t |
| Lookback | 20 consecutive 8H funding periods (prior 20 observations) | ≈6.7 days of funding-interval-aligned price context; one week of carry structure |
| Flatness threshold | \|close_t − close_{t−20}\| / close_{t−20} < 0.05 | 5% net price change over lookback; conservative flatness criterion for major crypto perps |
| Minimum duration | 3 consecutive 8H observations where flatness condition holds at t | Prevents brief consolidations during active trends from classifying as sideways |
| Exclusion — insufficient history | First 20 rows of discovery slice: regime = UNDEFINED | Cannot compute lookback; these rows are excluded from all comparisons |

**Regime value assignments:**

| Regime label | Rule |
|---|---|
| SIDEWAYS | Flatness condition holds at t AND has held for at least 3 consecutive 8H periods ending at t |
| NON_SIDEWAYS | Flatness condition fails at t (net move ≥ 5%) |
| UNDEFINED | Fewer than 20 prior discovery-slice rows available for lookback |

**OHLCV dependency:** The candidate OHLCV source is the Binance 4H kline data
committed at `583e724` (Binance C7 replication artifact), covering BTCUSDT and
ETHUSDT, Binance USDT-M perpetuals, window 2022-01-01 to 2023-12-17.

**Timestamp convention (locked — timestamp convention patch; see §11):**
Binance OHLCV CSV timestamps are kline open times. For fundingTime t, the
aligned 4H OHLCV context row is the kline whose interval ends at t, represented
in the CSV by open timestamp t − 4H. No CSV row with open timestamp at or after
t may be used as price context for observation at t. For any lookback ending at
t, all aligned close values are drawn from CSV rows with open timestamps
strictly before t.

Cadence alignment: 8H funding settlement times (00:00, 08:00, 16:00 UTC) are
4H kline close boundaries; a kline opening at t − 4H closes exactly at t.
**If OHLCV source or coverage confirmation fails, screening is blocked (see §11).**

**Threshold rationale (no data inspection):**
- A 5% net move threshold over 160H is conservative for BTC and ETH. These
  assets routinely move 10–20% during trending weeks. A 5% cap separates
  flat sideways from even modest trending.
- A 20-period lookback (160H) captures approximately one week of funding
  intervals, which is the natural carry accumulation horizon for 8H-cadence
  funding.
- A 3-period minimum duration prevents a single period of transient flatness
  (e.g., a pause inside a trend) from being classified as a sideways regime.

**If screening reveals fewer than 50 SIDEWAYS observations per symbol in the
discovery slice:** label result NORMALIZATION_SCREEN_INCONCLUSIVE; do not revise
the classifier within the same run. Flag to Owner for review.

### Combined State Assignment

Each discovery-slice observation row is assigned one combined state:

| Combined state | Rule |
|---|---|
| ACTIVE_HIGH | Condition 1 = HIGH AND Condition 2 = SIDEWAYS |
| ACTIVE_LOW | Condition 1 = LOW AND Condition 2 = SIDEWAYS |
| BASELINE | Condition 1 = NEUTRAL AND Condition 2 = SIDEWAYS — regime-matched baseline |
| NEUTRAL_NON_SIDEWAYS | Condition 1 = NEUTRAL AND Condition 2 = NON_SIDEWAYS — excluded from comparisons; reported as observational note |
| EXCLUDED_TRANSITION | Condition 1 = TRANSITION_HIGH or TRANSITION_LOW |
| EXCLUDED_UNDEFINED | Condition 2 = UNDEFINED (first 20 rows) |
| INACTIVE_DISPLACED | Condition 1 = HIGH or LOW AND Condition 2 = NON_SIDEWAYS — displaced funding in a trending regime |

**Note on INACTIVE_DISPLACED:** rows where funding is displaced but the price
regime is not sideways are intentionally excluded from both active and baseline
comparisons. These rows may belong to the Setup D directional stress or carry
framing (trend-agnostic). Mixing them into the Funding Normalization sideways
hypothesis would contaminate the sideways-specific signal test. Their count
must be reported in screening output as an observational note.

**Note on NEUTRAL_NON_SIDEWAYS:** rows where funding is neutral but the price
regime is NON_SIDEWAYS are excluded from the regime-matched baseline. These
rows are not INACTIVE_DISPLACED (funding is not displaced), but they are not
comparable to the treatment group (which requires SIDEWAYS regime). Excluding
them ensures that the only differing variable between ACTIVE and BASELINE groups
is the funding state, not the regime mix. Their count must be reported in
screening output as an observational note.

---

## 6. Observation Windows

Forward response windows are in units of the native 8H funding cadence. All
windows are pre-registered. No window may be added after screening results are
seen.

| Window label | Duration | Approximate calendar |
|---|---|---|
| W1 — short | +1 funding period | +8H from observation t |
| W3 — medium | +3 funding periods | +24H from observation t (~1 day) |
| W8 — extended | +8 funding periods | +64H from observation t (~2.7 days) |

These windows are taken from the Continuous-State Family B harness primary
windows (+1 interval, +3 intervals, +8 intervals from state observation).

**Response variable:** the forward funding rate change at each window:

```
Δf(t, t+N) = fundingRate_{t+N} − fundingRate_t
```

Expected sign by branch:
- ACTIVE_HIGH branch: Δf < 0 (rate decreases toward neutral = normalization).
- ACTIVE_LOW branch: Δf > 0 (rate increases toward neutral = normalization).

For the normalization magnitude floor check, the relevant magnitude is
|Δf(t, t+N)| expressed in bps, compared against the 9 bps normalization
magnitude floor (§8). This screen tests the funding-normalization phenomenon,
not realized trade PnL; see §8 for the distinction.

**State entry vs. state duration:** each observation row classified as
ACTIVE_HIGH or ACTIVE_LOW is a candidate observation regardless of whether it
is the first period of a consecutive state run or a continuation. Consecutive
runs of the same state are not deduplicated; each row generates a separate
forward window. This approach maximizes sample size but must be noted in output
(consecutive observations within the same regime run are not independent events;
this is a screening limitation, not a validation design).

**No price return window is pre-registered in this design lock.** Price return
as a secondary response variable may be added only by a separate pre-registered
amendment with Owner authorization before any screening begins. No price return
is computed under this design lock.

**All three windows are evaluated independently per branch and per symbol.** No
cross-window averaging or optimization.

---

## 7. Null and Baseline

**Baseline group:** BASELINE observations — rows where Condition 1 = NEUTRAL
**AND** Condition 2 = SIDEWAYS — within the same symbol and discovery slice.
Rows where Condition 1 = NEUTRAL and Condition 2 = NON_SIDEWAYS are assigned
NEUTRAL_NON_SIDEWAYS and are excluded from the baseline (see §5 combined state
table).

**Rationale for regime-matched baseline:** The treatment group (ACTIVE_HIGH,
ACTIVE_LOW) requires both funding displacement and SIDEWAYS regime. The baseline
is restricted to SIDEWAYS rows so that the only differing variable between
treatment and baseline is the funding state. Without regime matching, an observed
Δf difference could reflect sideways mean-reversion behavior rather than funding
normalization, creating an inseparable confound. This patch supersedes the prior
unmatched baseline (NEUTRAL regardless of regime). Baseline sample size is
smaller than under the prior construction but the comparison is clean.
NEUTRAL_NON_SIDEWAYS row counts are reported as an observational note (see §10).

**Null hypothesis:** Displaced funding in a statistically sideways price regime
carries no additional information about subsequent funding normalization beyond
what is observed in neutral-funding sideways-regime periods for the same symbol
and discovery slice. The distribution of Δf(t, t+N) for ACTIVE_HIGH and
ACTIVE_LOW observations is identical to the distribution for BASELINE
(NEUTRAL AND SIDEWAYS) observations.

**Falsification criterion:** If ACTIVE_HIGH or ACTIVE_LOW forward funding
changes are not directionally separated from BASELINE changes above the 9 bps
normalization magnitude floor (§8), the hypothesis is FALSIFIED at this
cheap-screening level for that branch and window. A NORMALIZATION_SCREEN_ABSENT
or NORMALIZATION_SCREEN_WEAK result does not advance. An inconclusive result
does not advance without resolving the underlying issue.

**Baseline is fixed.** No alternate null or baseline construction may be
introduced after screening begins.

---

## 8. Cost Floor

Per HD2 (harness safeguard), the cost floor is locked here and cannot be
revised downward after any data is opened.

**Harness family:** Continuous-State (Family B).
**Family-level floor:** 9 bps round-trip.
**Candidate-level floor (this design lock):** 9 bps round-trip.

**Application to funding-rate response variable:** This screen's response
variable is Δf(t, t+N) — a funding rate change, not a realized trade PnL. The
9 bps figure is applied here as a **normalization magnitude floor**: if
|Δf(t, t+N)| < 9 bps, the normalization magnitude is too small to be
economically interesting at the screening stage, even if directionally
consistent. This does not constitute a cost-coverage proof or evidence of
tradeability. Any future trading or PnL cost model must be designed and
validated separately. A gross normalization of |Δf(t, t+N)| < 9 bps does not
clear the normalization magnitude floor condition. The candidate result cannot
receive NORMALIZATION_SCREEN_POSITIVE if the normalization magnitude floor
condition fails.

**Floor lock statement:** This 9 bps floor is locked as of this design lock.
Any request to lower it after any data has been opened is a governance
violation and must be flagged to Owner before proceeding.

**Upward revision:** permitted only if a documented structural rationale (wider
spreads for the specific pairs, documented higher fee tier, known cost increase)
is pre-registered before screening begins. Upward revision after results are
seen is not permitted.

---

## 9. Result Labels

Labels are assigned per branch (ACTIVE_HIGH and ACTIVE_LOW separately), per
symbol, per observation window. All labels are **discovery-only orientation**.
No label constitutes readiness, evidence, PASS_CANDIDATE, or authorization for
paper, probe, runtime, or live activity.

| Label | Condition |
|---|---|
| NORMALIZATION_SCREEN_POSITIVE | ACTIVE state Δf is directionally consistent with normalization for this branch (sign condition met); median |Δf| exceeds 9 bps normalization magnitude floor; and directional consistency holds in at least 2 of 3 pre-registered windows |
| NORMALIZATION_SCREEN_WEAK | Directionally consistent in expected direction but median |Δf| is below 9 bps normalization magnitude floor; or consistent in only 1 of 3 windows |
| NORMALIZATION_SCREEN_ABSENT | No directional normalization detected; ACTIVE state Δf distribution is indistinguishable from or opposite to BASELINE; hypothesis FALSIFIED at this screening level |
| NORMALIZATION_SCREEN_INCONCLUSIVE | Fewer than 30 ACTIVE observations for this branch per symbol; SIDEWAYS regime too sparse; OHLCV alignment unresolved; held-out contamination risk; or any §11 blocker was triggered |
| STRONG_ANOMALY_CANDIDATE | All five mechanical harness §2.1 conditions met (see below) |

**Branch independence:** ACTIVE_HIGH-branch and ACTIVE_LOW-branch results are
labeled and reported separately. A positive result on one branch and a negative
on the other cannot be combined or averaged. Each branch stands independently.

**Window independence:** result labels are assigned per window separately.
A single summary label (per branch per symbol) may be reported as:
- NORMALIZATION_SCREEN_POSITIVE: positive in ≥ 2 of 3 windows above cost floor.
- NORMALIZATION_SCREEN_WEAK: positive in only 1 window, or all below cost floor.
- NORMALIZATION_SCREEN_ABSENT: no directional structure in any window.
- NORMALIZATION_SCREEN_INCONCLUSIVE: any window-level inconclusive.
- STRONG_ANOMALY_CANDIDATE: all five conditions met across windows.

**STRONG_ANOMALY_CANDIDATE — five conditions (from harness §2.1, applied here):**

1. **Effect-size condition:** observed Δf is at or above the 95th percentile of
   the discovery BASELINE distribution in the expected direction.
2. **Consistency condition:** directional sign condition holds in at least 2 of
   3 pre-registered windows (W1, W3, W8).
3. **Breadth condition:** directional sign condition holds in both BTCUSDT and
   ETHUSDT (2 of 2 eligible instruments).
4. **Economic floor condition:** median |Δf| exceeds 9 bps normalization
   magnitude floor in the windows satisfying conditions 1–3.
5. **Forensic sanity condition:** no data artifact, lookahead, timestamp
   misalignment, held-out contamination, or post-hoc threshold selection is
   present.

**Verified against harness §2.1:** These five conditions map directly to the
harness §2.1 mechanical trigger — no candidate-specific divergence. The
consistency condition maps W1/W3/W8 observation windows to the harness
"sub-periods" concept for Continuous-State candidates; the breadth condition
uses both eligible instruments (BTC and ETH); the economic floor condition
applies the normalization magnitude floor (§8) as a proxy for economic
significance.

**STRONG_ANOMALY_CANDIDATE triggers mandatory HD3 independent forensic review.**
The screener may not self-clear the forensic review. Forensic review output is
input only; Owner decision required for any escalation. No result label
constitutes evidence.

---

## 10. Output Constraints for Later Screening

If screening is later authorized by Owner, the screening output is strictly
bounded:

**Permitted outputs:**

- Data coverage confirmation: rows loaded per symbol; first and last fundingTime
  of discovery slice as loaded (confirms boundary was applied correctly).
- Discovery row boundary confirmation: actual fundingTime values of rows 1502
  and 1503 for each symbol.
- Observation counts per symbol: total discovery rows, ACTIVE_HIGH count,
  ACTIVE_LOW count, BASELINE count, NEUTRAL_NON_SIDEWAYS count,
  EXCLUDED_TRANSITION count, EXCLUDED_UNDEFINED count, INACTIVE_DISPLACED count.
- SIDEWAYS regime observation count per symbol (rows classified SIDEWAYS within
  discovery slice).
- Interval check: confirmation that all loaded BTC and ETH discovery-slice rows
  are 8H intervals (no non-standard intervals).
- OHLCV alignment confirmation: confirmed or BLOCKED with specific reason.
- Discovery-only result label per branch, per symbol, per window (from §9
  vocabulary only).
- Non-evidence notes: observations about regime sparsity, state distribution
  concentration, number of INACTIVE_DISPLACED rows, consecutive-run count
  within state buckets.
- Blocker flags: any §11 condition triggered, with specific details.

**Forbidden outputs — never produced or reported:**

- PnL, Sharpe ratio, maximum drawdown, or any strategy performance metric.
- Win rate, profit factor, or trade-level statistics.
- Any computation derived from held-out rows (rows 1503–2147).
- Held-out results of any kind.
- Trading recommendations, position sizing, or capital allocation advice.
- Readiness statements of any kind (paper, probe, runtime, live).
- Any computation derived from SOLUSDT.
- Any computation derived from instruments beyond BTCUSDT and ETHUSDT.
- Any result derived from an informal or exploratory run not conducted under
  this design lock specification.

---

## 11. Failure and Blocker Conditions

If any condition below is present, the relevant BLOCKED flag is raised to Owner
before any further screening computation proceeds:

| Blocker flag | Trigger condition | Required action |
|---|---|---|
| SCREENING_BLOCKED_PENDING_OHLCV_ALIGNMENT_CONFIRMATION | Committed Binance 4H OHLCV (`583e724`) cannot be confirmed as covering BTCUSDT and ETHUSDT within the discovery window; or the locked timestamp convention (open timestamp t − 4H = bar closing at fundingTime t) was not applied correctly | Halt; Owner must authorize OHLCV alignment confirmation before screening proceeds |
| SCREENING_BLOCKED_RAW_DATA_EXTENDS_OUTSIDE_LOCKED_WINDOW | Any loaded funding or OHLCV row has a fundingTime or close-bar timestamp outside 2022-01-01T00:00:00Z to 2023-12-17T08:00:00Z | Halt; report contamination; do not proceed |
| SCREENING_BLOCKED_NON_8H_INTERVALS_IN_BTC_ETH | Any BTC or ETH discovery-slice funding row has a non-8H interval (indicates data loading error or cross-contamination with SOLUSDT file) | Halt; report data integrity issue; do not proceed |
| SCREENING_BLOCKED_THRESHOLD_APPLICATION_FAILURE | Funding percentile thresholds (p20, p30, p70, p80) cannot be computed cleanly from discovery rows due to format errors, NaN values, or missing records | Halt; report specific error; do not proceed |
| SCREENING_BLOCKED_HELD_OUT_CONTAMINATION_RISK | Any computation accessed or could have accessed rows 1503–2147 of either symbol before the boundary was enforced | Halt; invalidate entire run; report to Owner; do not report any result labels |
| SCREENING_BLOCKED_SOL_DATA_INCLUDED | SOLUSDT data appeared in any loaded file or computation | Halt; invalidate run; report to Owner |
| SCREENING_BLOCKED_NEW_PAIR_INCLUDED | Any instrument beyond BTCUSDT and ETHUSDT appeared in any loaded data or computation | Halt; invalidate run; report to Owner |
| SCREENING_BLOCKED_PRIVATE_ENDPOINT_OR_KEY_REQUIRED | Screening requires any private API key, signed request, account credential, or non-public data source | Halt; never use; report to Owner |
| SCREENING_INSUFFICIENT_ACTIVE_OBSERVATIONS | Fewer than 30 ACTIVE_HIGH or ACTIVE_LOW rows for a branch per symbol after all state filtering | Do not halt; label that branch NORMALIZATION_SCREEN_INCONCLUSIVE; report count |

**Primary current blocker: OHLCV alignment confirmation.**

Before screening execution is authorized, the following must be confirmed and
documented:

1. The committed Binance 4H kline data (`583e724`) contains BTCUSDT and ETHUSDT
   funding-aligned OHLCV.
2. The data window covers at least 2022-01-01T00:00:00Z to 2023-05-15T08:00:00Z
   (the discovery slice end).
3. The locked timestamp convention is applied: for fundingTime t, the CSV row
   with open timestamp t − 4H is used as the aligned price context row (its bar
   closes at t); no CSV row with open timestamp ≥ t is used as context at t.
   This convention is locked by the timestamp convention patch below; the
   screener must confirm application, not re-derive the rule.

Items 1 and 2 were confirmed by metadata-only inspection documented in
`research/signal_observation/FUNDING_NORMALIZATION_BTC_ETH_ALIGNMENT_AND_REVIEW_PACKET.md`.
Item 3 (timestamp convention) is locked by the timestamp convention patch below.
The screener must confirm at execution time that the convention was applied
correctly. If item 1 or 2 fails at execution, screening is BLOCKED pending a
separate data sourcing decision.

### Timestamp Convention Patch

This patch replaces all prior design-lock wording that referred to "4H bar
close timestamps" coinciding with 8H funding settlement times. This is a
timestamp convention clarification only; it does not authorize screening
execution.

Locked convention:
- Binance OHLCV CSV timestamps are kline open times (confirmed by DR1
  downloader documentation in
  `research/signal_observation/SETUP_C_DR1_BINANCE_RECENT_4H_FEASIBILITY_NOTE.md`).
- For fundingTime t, use the CSV row with open timestamp t − 4H; that kline's
  interval ends at t and its close price is the pre-funding context price.
- Do not use any CSV row with open timestamp at or after t as price context
  for observation at t.
- For the 20-period lookback ending at t, all 20 aligned close values are
  drawn from CSV rows with open timestamps strictly before t.

Worked example:
- fundingTime = 2023-05-15T08:00:00Z
- Locate OHLCV row with timestamp 2023-05-15T04:00:00Z (= fundingTime − 4H)
- Use the **close** field of that row
- That close represents price as of 08:00:00Z (close of the 4H bar opening at
  04:00 and closing at 08:00)

First-usable-period rule:
- If fundingTime t − 4H precedes the first OHLCV row timestamp, that funding
  row has no aligned OHLCV context and must be excluded from any discovery
  calculation requiring OHLCV context (e.g., sideways regime classification).
  Do not backfill or substitute.
- Given OHLCV starts 2022-01-01T00:00:00Z, the first usable fundingTime for
  OHLCV-context screening is 2022-01-01T04:00:00Z. Any funding row at
  2022-01-01T00:00:00Z is excluded from regime-classified rows. Estimated
  impact: at most 1 funding row per symbol.

This patch does not authorize screening execution. Owner GO decision for
screening remains required (§12).

---

## 12. Next Gate (Owner Decision Required)

Screening execution is not authorized. Owner must explicitly choose one or more
options. Absence of selection = Option D (hold).

| Option | Action | Pre-condition |
|---|---|---|
| A — Authorize bounded BTC/ETH-only discovery screening execution | Owner authorizes a bounded screening run using this design lock as the full specification; screener confirms OHLCV alignment and executes; output is bounded by §10 | This design lock reviewed and accepted; OHLCV alignment blocker resolved (Option E may be combined) |
| B — Require independent / Trader Reviewer review first | Owner routes this design lock to Trader Reviewer or equivalent independent reviewer before authorizing screening execution | Reviewer identified; no screening until review complete |
| C — Patch this design lock | Owner identifies specific items in this design lock to revise before screening is authorized | Specific patch instruction required; patches applied before data is opened |
| D — Hold; choose another candidate or lane | Owner pauses Funding Normalization screening; focuses on another candidate (Setup E, D1, OKX C7) or research lane | No pre-condition; freezes Funding Normalization forward progress |
| E — Authorize OHLCV alignment confirmation first | Owner authorizes a docs-only OHLCV alignment confirmation check to resolve the §11 primary blocker before authorizing screening | Can be combined with Option A once blocker is resolved |

---

## Relationship to Other Gates

- **D1 analysis HOLD:** Not affected by this design lock. SOL interval policy
  decision and separate D1 analysis design lock remain required. This document
  does not satisfy either condition.
- **Setup E HOLD:** Not affected. Setup E post-liquidation reversal and
  Hydromancer source resolution remain a separate research lane.
- **Harness methodology:** Status remains AUTHORIZED METHODOLOGY / NO SCREENING
  AUTHORIZED. This design lock is a per-candidate implementation of that
  authorized methodology.
- **SOLUSDT:** Status remains RETAINED/FLAGGED NON_STANDARD_INTERVALS_FOUND.
  This design lock does not authorize SOL inclusion, SOL analysis, or SOL
  interval policy resolution.
- **Sideways candidate map:** Status remains PROPOSED / CANDIDATE MAP ONLY for
  other sideways candidates. This design lock advances only Funding
  Normalization to SCREENING DESIGN LOCK. No other sideways candidate is
  advanced by this document.

---

## Latency Classification

- Operational fit: latency-tolerant.
- Signal cadence: 8H funding cycle; changes observable on hours-to-days
  timescale.
- Signal half-life: hours to days; normalization pressure persists across
  multiple 8H cycles.
- Human-in-loop: acceptable for screening design, screening execution
  decision, and result review.
- Automation required: no; not required for research phase.
- Intentional first-prototype rationale: Funding Normalization was selected
  partly because its latency profile fits the current solo-operator stage
  without requiring execution automation.
- This section does not authorize screening execution.

---

*End of design lock.*
