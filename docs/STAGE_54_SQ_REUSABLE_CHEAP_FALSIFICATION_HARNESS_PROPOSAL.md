# Stage 54-SQ Reusable Cheap-Falsification Harness — Methodology Proposal

## Status

PROPOSED. Requires independent review and Owner authorization before reuse in
any candidate screening task.

This document is a planning proposal only. It does not authorize data
acquisition, EXPLORE, validation, backtesting, implementation, readiness
promotion, paper/probe/live use, or capital deployment.

---

## 1. Objective

### 1.1 Why a Reusable Harness

Each new research candidate currently requires building screening infrastructure
from scratch. A shared, reviewed harness reduces per-candidate overhead,
standardizes the pre-registration and held-out discipline, and allows multiple
candidates to be screened in parallel after a single harness review.

The goal is to improve discovery throughput without weakening validation quality.
A faster screening step is only valuable if it preserves the integrity of the
formal held-out evidence that follows.

### 1.2 Portfolio Default

The project's default search target is a portfolio of weak, structurally
motivated, low-correlation edges. No single setup is assumed to be the answer.
Screening is the mechanism for deciding which candidates merit the cost of formal
validation — it is not the mechanism for declaring that a candidate is ready.

Screening results are non-evidence. They cannot promote readiness, advance a
candidate to `PASS_CANDIDATE`, or authorize paper/probe/live activity. They can
only produce orientation labels that inform the next Owner-level planning
decision.

### 1.3 Single-Candidate Depth vs. Portfolio Breadth

The harness is not a replacement for deep, careful validation. A candidate that
survives screening still requires a formal held-out validation step under
independent review and Owner authorization. The harness exists to avoid spending
formal held-out resources on candidates that would have collapsed at cheap
falsification.

---

## 2. Grail / Anomaly Philosophy

> **Do not depend on finding a grail. Do not ignore a grail-like anomaly.**

The project is built for robustness across a portfolio of modest edges, not for
the discovery of an exceptional single signal. That orientation is correct and
should be maintained.

However, an unusually strong screening result must not be discarded, normalized
away, or explained away by assumption. If a result looks too clean, the correct
response is elevated skepticism and forensic review, not promotion.

### 2.1 STRONG_ANOMALY_CANDIDATE Label

**`STRONG_ANOMALY_CANDIDATE`** is a **protected escalation trigger**, not proof
of edge. It may be assigned only when **all five** of the following mechanical
conditions are satisfied. Each condition must be pre-registered before data
inspection; no condition may be relaxed or reinterpreted after results are seen.

1. **Effect-size condition:** the observed response is at or above the 95th
   percentile of the pre-registered null distribution in the favorable direction.
2. **Consistency condition:** the favorable direction appears in at least 2 of 3
   pre-registered sub-periods; or, for rare-event candidates, in at least 60% of
   eligible event buckets.
3. **Breadth condition:** the favorable direction appears in at least 2 eligible
   instruments or venues, unless the candidate is explicitly pre-registered as
   single-instrument only.
4. **Economic floor condition:** the gross effect exceeds the pre-registered cost
   floor estimate (see §2.2).
5. **Forensic sanity condition:** no known leakage, lookahead bias, timestamp
   misalignment, duplicate-event inflation, reserved-window contamination, or
   post-hoc threshold/window selection is present.

If the event set is too sparse to satisfy the consistency or breadth conditions,
`STRONG_ANOMALY_CANDIDATE` cannot be assigned. The candidate may instead receive:

**`RARE_EVENT_PROMISING / NEEDS_MORE_EVENTS`** — directional skew is present and
passes the effect-size and economic floor conditions, but event count is
insufficient to satisfy consistency or breadth. Not proof of edge; requires
Owner decision on whether additional data or a longer window is justified before
any escalation.

When all five conditions are met, `STRONG_ANOMALY_CANDIDATE` triggers a mandatory
forensic review pass covering at least:

- Data leakage (future data accessible at signal time)
- Lookahead bias in timestamp alignment
- Realistic cost inclusion (spread, fees, slippage, funding timing)
- Vendor artifact or de-duplication failure in the source data
- Duplicated event counts inflating the event sample
- Post-hoc threshold or window selection (was this the best of many tested?)
- Regime one-offs (does the result concentrate in one or two episodes?)
- Survivorship, listing, and delisting effects

Forensic review for a `STRONG_ANOMALY_CANDIDATE` must be performed by an
agent/reviewer who did not run the screening and did not choose the candidate
pre-registration. The screener may provide artifacts, but cannot self-clear the
forensic review. Forensic review output is input only; Owner decision is
required for escalation.

An anomaly that survives forensic review may justify deeper formal investigation.
An anomaly that does not survive it protects the project from false confidence.
Either outcome has value.

### 2.2 Cost Floor Definition

Every candidate screening task must pre-register a cost floor estimate before
data inspection. The cost floor is a rough screening reproducibility floor, not
a formal execution model.

**Pre-registered cost floor = estimated fees + spread + slippage buffer (in bps)**

The cost floor formula is locked at the harness family level and referenced by
each candidate pre-registration. It is a conservative screening reproducibility
floor, not a formal execution model.

- **Fees:** exchange taker fee for the relevant instrument and venue tier.
- **Spread:** half-spread estimate for the instrument at typical size, based on
  publicly available order-book context or prior research notes.
- **Slippage buffer:** a conservative additional allowance for market impact and
  partial fills; typically 1–3× the spread estimate for liquid perps.

Default family-level floors are: Event-Triggered, 14 bps round-trip, equal to
estimated fees plus spread plus slippage buffer, unless a more conservative
value is pre-registered; Continuous-State, 9 bps round-trip, equal to estimated
fees plus spread plus slippage buffer, unless a more conservative value is
pre-registered; Cross-Venue Dislocation, venue A fees plus venue B fees plus
two spreads plus transfer/borrow/slippage buffer where applicable, with no
fixed default if venue mechanics are unresolved.

The cost floor figure must be a single scalar in bps committed before screening
begins. It may not be revised downward after results are seen. Upward revision
is permitted if a known error in the original estimate is documented.
Candidate-level floors may be more conservative than the family-level floor,
but cannot be revised downward after data inspection.

A result whose gross effect is below the pre-registered cost floor cannot
receive `EVENT_SCREEN_POSITIVE`, `CARRY_SCREEN_POSITIVE`,
`STRESS_SCREEN_POSITIVE`, `DISLOCATION_SCREEN_POSITIVE`, or
`STRONG_ANOMALY_CANDIDATE`, regardless of statistical properties.

---

## 3. Harness Template Families

Three reusable template families cover the candidates currently in the project
backlog. Each template defines inputs, trigger logic, forward windows, null
concept, result labels, and forbidden scope.

---

### Family A — Event-Triggered

**Candidate use cases:** liquidation cascades, funding-stress episodes, exchange
outages, options expiry, unlock/cliff events, macro news shocks, large-OI unwind.

#### Input Format

- Per-event records: event timestamp (UTC ms), instrument, event magnitude or
  classification, optional ancillary fields (e.g., liquidation side, funding
  rate at event).
- One row per event; no aggregation before screening.

#### Trigger / State Definition

A Boolean or threshold classification applied to a scalar series or event stream:

```
trigger = (event_magnitude >= threshold) AND (prior_N_period_cooldown satisfied)
```

- Threshold must be pre-registered and not adjusted after data inspection.
- Cooldown prevents overlapping events from inflating the sample.
- Trigger definition must be stated in instrument-agnostic terms so the same
  logic applies across all screened instruments.

#### Forward-Return / Response Windows

- Primary: +4H, +8H, +24H forward return from trigger timestamp.
- Secondary (optional, if pre-registered): +1H, +48H.
- All windows pre-registered. No window added after results are seen.

#### Null / Baseline Concept

Two options are available. The exact null must be selected in candidate
pre-registration before data inspection and cannot be changed mid-task (see §4).

- **Option 1 — Rolling matched-percentile null:** randomly drawn timestamps from
  the same instrument and calendar period, matched to the trigger's percentile
  rank in the event series, but not classified as triggers. Preserves
  instrument-specific autocorrelation structure.
- **Option 2 — Shuffled-label null:** shuffle trigger labels within a rolling
  window of the same instrument and calendar period.

#### Result Labels

- `EVENT_SCREEN_POSITIVE` — forward-return distribution shows mechanism-consistent
  directional skew, statistically separable from null at pre-registered threshold.
- `EVENT_SCREEN_WEAK` — directional skew present but not separable from null, or
  economic magnitude below cost floor estimate.
- `EVENT_SCREEN_INCONCLUSIVE` — insufficient events, dominant regime concentration,
  or structural ambiguity prevents reliable separation.
- `EVENT_SCREEN_NULL` — no directional structure; carry and stress branch (if
  applicable) both negative.
- `STRONG_ANOMALY_CANDIDATE` — if result is materially stronger than null across
  multiple dimensions; triggers forensic review before escalation (see §2.1).

#### Forbidden Scope

- No threshold or window adjustment after data inspection.
- No mixing carry and stress branches into one result label.
- No result label constitutes readiness, PASS_CANDIDATE, or formal evidence.

---

### Family B — Continuous-State

**Candidate use cases:** funding carry / compensation, basis / cash-and-carry
dislocation, realized vs. implied volatility premium, funding regime persistence.

#### Input Format

- Time series: timestamp (UTC ms), instrument, state scalar (e.g., funding rate,
  basis spread, vol ratio).
- Regular or event-aligned cadence; cadence must be stated and consistent.

#### Trigger / State Definition

A scalar exceeds a pre-registered percentile or absolute threshold, held for a
pre-registered minimum duration, classified as `HIGH`, `NEUTRAL`, or `LOW`
regime:

```
state = HIGH  if scalar >= p_high AND held for >= N consecutive intervals
state = LOW   if scalar <= p_low  AND held for >= N consecutive intervals
state = NEUTRAL otherwise
```

Thresholds (`p_high`, `p_low`, `N`) pre-registered per candidate.

#### Forward-Return / Response Windows

- Primary: +1 interval, +3 intervals, +8 intervals from state entry.
- All windows in units of the native cadence (e.g., 8h for funding).
- No window addition after results are seen.

#### Null / Baseline Concept

- NEUTRAL-state forward returns as within-instrument baseline.
- Preserves the same instrument, same calendar period, same cadence.

#### Result Labels

- `CARRY_SCREEN_POSITIVE` — HIGH-state forward returns show carry-consistent
  skew above cost floor.
- `STRESS_SCREEN_POSITIVE` — HIGH-state forward returns show reversal / stress
  skew separable from NEUTRAL.
- `CARRY_SCREEN_WEAK` / `STRESS_SCREEN_WEAK` — effect directionally consistent
  but below cost floor or not separable from null.
- `CARRY_SCREEN_NULL` / `STRESS_SCREEN_NULL` — no directional structure.
- `STRONG_ANOMALY_CANDIDATE` — as defined in §2.1.

**Note:** Carry and stress must always be evaluated as separate branches.
Collapsing them into one label is forbidden.

#### Forbidden Scope

- No threshold selection after inspecting forward-return distributions.
- No carry/stress collapse.
- No result label constitutes readiness or formal evidence.

---

### Family C — Cross-Venue Dislocation

**Candidate use cases:** cross-venue lead-lag, venue spread normalization,
exchange-specific stress / basis dislocation, OKX vs. Binance vs. Bitget
relative pricing.

#### Input Format

- Synchronized multi-venue time series: timestamp (UTC ms), instrument,
  venue A price/rate, venue B price/rate, derived spread or ratio.
- Venues aligned to a common UTC cadence; alignment method pre-registered.

#### Trigger / State Definition

A dislocation metric (e.g., abs(spread) > threshold, or price ratio outside
N-sigma band) held for at least one cadence interval:

```
dislocation = |venue_A_rate - venue_B_rate| >= pre_registered_threshold
lead_lag    = cross_correlation peak lag (unsigned, pre-registered max lag)
```

#### Forward-Return / Response Windows

- Primary: +1, +4, +24 intervals from dislocation onset.
- Secondary: time-to-mean-reversion (measured, not optimized).

#### Null / Baseline Concept

- Matched non-dislocation intervals from the same pair and calendar period.
- Controls for common time-of-day and regime effects.

#### Result Labels

- `DISLOCATION_SCREEN_POSITIVE` — dislocation onset predicts mean reversion
  within pre-registered window at pre-registered threshold.
- `DISLOCATION_SCREEN_WEAK` — directional but below cost floor or inconsistent
  across instruments.
- `DISLOCATION_SCREEN_NULL` — no predictive structure.
- `STRONG_ANOMALY_CANDIDATE` — as defined in §2.1.

#### Forbidden Scope

- No venue addition or removal after data inspection.
- No result label constitutes readiness or formal evidence.

---

## 4. Pre-Registration Requirements

Every candidate must complete a pre-registration record before any data
inspection. The record must lock:

| Field | Content |
|---|---|
| Hypothesis | Mechanism statement; why the effect might exist |
| Hypothesis prior sources | Internal repo docs or reviews that motivated the hypothesis; external publications, dashboards, vendor docs, community claims, or trader priors; whether any prior came from data already inspected by the project |
| Signal family | Event-Triggered / Continuous-State / Cross-Venue |
| Harness template | Which Family A / B / C template is being applied |
| Trigger / state definition | Exact threshold, percentile, or logic |
| Instruments | Exact instrument list; no addition after inspection |
| Cadence | Exact interval; no change after data is seen |
| Discovery slice | Date range used for screening; must be stated before first data open |
| Held-out slice | Date range reserved for formal validation; must be stated and preserved |
| Forward windows | Exact windows; no addition after inspection |
| Null / baseline | Exact null construction method |
| Result labels | Exact labels and their definitions |
| What is forbidden | Specific forbidden actions for this candidate |

Undeclared borrowed priors cannot be treated as blind discovery. If a hypothesis
was motivated by internal prior work, external publications, dashboards, vendor
docs, community claims, trader priors, or data already inspected by the project,
that influence must be declared before discovery-slice inspection.

Pre-registration must be committed before the screening task begins. No
post-hoc threshold or window selection. No post-hoc splitting of an inspected
window into "exploration" and "validation" sub-segments.

Where a template offers multiple null/baseline options, the exact null
construction method must be selected and committed in the candidate
pre-registration record before data inspection begins. The null selection
cannot be changed mid-task.

---

## 5. Discovery / Held-Out Split

### 5.1 General Rule

The discovery slice must be identified and committed before the first data file
is opened. The held-out slice must remain completely untouched until a formal
validation step is explicitly authorized by the Owner after an independent
review of screening results.

Post-hoc splitting of a window that has already been inspected is rejected.
Labelling a sub-segment of an inspected window as "held-out" does not restore
its held-out status.

### 5.2 Rare Event-Triggered Candidates

For candidates where events are rare (e.g., extreme funding episodes, large
liquidation cascades, significant OI unwinds), naive chronological splitting
may place all or most events in one side of the split, rendering either the
discovery or held-out slice analytically useless.

For such candidates, the pre-registration must explicitly address this risk and
propose one of the following:

- **Event-stratified split:** select held-out events before inspection, ensuring
  at least a minimum number of events fall in each side. Event selection must
  be deterministic and pre-registered.
- **Alternate held-out design:** reserve a geographically or venue-separated
  source as held-out (different venue, different instrument tier, or a source
  not yet opened), rather than a time-based split.
- **Accept thin held-out:** if events are too rare for a stratified split and no
  alternative source exists, the pre-registration must explicitly acknowledge
  that formal validation will be limited; do not proceed to formal validation
  on this basis without Owner authorization.

The rare-event risk must be stated and resolved in pre-registration — not
discovered mid-task.

---

## 6. Multiple Comparisons

Batch screening — screening multiple candidates, timeframes, or instrument tiers
in one pass — constitutes multiple comparisons. All of the following apply:

- Each additional tested combination increases the probability that at least one
  result appears positive by chance.
- Screening results across a batch are orientation only. They are not evidence
  of edge for any individual candidate, even if one result is strong.
- A `STRONG_ANOMALY_CANDIDATE` result arising from a large batch must receive
  more skeptical forensic review than one arising from a single pre-registered
  test, because the number of comparisons directly raises the prior probability
  of a false positive.
- Any later formal validation must be clean and held-out: only one pre-registered
  test on data that was never inspected during screening.

No post-hoc reduction of the batch is permitted after results are seen (e.g.,
reporting only the positive result and discarding negative results from the
same batch).

---

## 7. Batch Screening Model

After the harness methodology receives independent review and Owner
authorization, multiple candidates may be screened in parallel using the same
reviewed infrastructure. Each candidate still requires its own pre-registration
record before data inspection.

### Candidate Batch — Current Backlog

| Candidate | Family | Data Status | Blocker |
|---|---|---|---|
| Setup D — Funding Carry (Branch A) | Continuous-State (Family B) | D1 funding data acquired | SOL interval policy; harness design lock |
| Setup D — Funding Stress (Branch B) | Event-Triggered (Family A) or Continuous-State (Family B) | D1 funding data acquired | SOL interval policy; harness design lock |
| Setup E — Liquidation Reversal / Forced-Flow | Event-Triggered (Family A) | No suitable held-out source confirmed | Source access decision pending |
| Basis / Cash-and-Carry Dislocation | Continuous-State (Family B) or Cross-Venue (Family C) | No data acquired | Triage-ready; data path not authorized |
| Options Expiry / Dealer Hedging Pressure | Event-Triggered (Family A) | No data acquired | Triage-ready; hypothesis note not yet created |
| Cross-Venue Dislocation | Cross-Venue (Family C) | No data acquired | Triage-ready; data path not authorized |

Screening a candidate from this table requires:
1. This harness proposal reviewed and authorized by Owner.
2. Candidate pre-registration record committed.
3. Data availability confirmed and held-out path preserved.
4. Owner authorization of a bounded screening task.

No candidate in this table is authorized for screening by this proposal alone.

---

## 8. Setup D D1 as Prototype Input

### 8.1 Acquisition Result

D1 funding data acquisition (`93f4d0f`) produced:

- **BTCUSDT:** quality PASS — 2,147 rows, all 8h intervals, no gaps, no
  out-of-window records.
- **ETHUSDT:** quality PASS — 2,147 rows, all 8h intervals, no gaps, no
  out-of-window records.
- **SOLUSDT:** RETAINED / FLAGGED — `NON_STANDARD_INTERVALS_FOUND`. 2,222
  rows; 101 sub-8h gaps (98×2h, 3×4h) concentrated 2022-11-09 to 2022-11-18
  (FTX collapse period). No out-of-window records.

Acquisition label: `FUNDING_DATA_ACQUIRED`.
Full `FUNDING_DATA_PASS` label and D1 analysis design lock: **HOLD**.

### 8.2 SOLUSDT Interval Policy

SOLUSDT's variable intervals during the FTX collapse period are a genuine
market observation, not a data defect. Binance temporarily ran enhanced-frequency
(2h / 4h) SOL funding when the market was under extreme stress.

This is directly relevant to **Family A (Event-Triggered)** harness design for
the funding-stress branch (Branch B): an enhanced-frequency interval is itself
a candidate signal of elevated stress, not noise to be discarded.

The interval policy decision is required before D1 screening analysis begins.
Options:

- **Accept variable intervals natively** — treat each settlement as a signal
  observation regardless of interval; adjust forward windows to be settlement-
  count-based rather than clock-based.
- **Resample to 8h** — aggregate sub-8h settlements to the 8h cadence;
  discard sub-8h granularity.
- **Exclude the flagged period** — drop 2022-11-09 to 2022-11-18 from SOLUSDT
  analysis entirely; acknowledge the exclusion in the result record.

**Branch asymmetry note:** exclusion of the flagged period is more defensible
for Branch A (carry / compensation) screening, where the interest is in stable
8h-cadence carry structure. For Branch B (funding stress / unwind), exclusion
is likely harmful: the 2022-11-09 to 2022-11-18 period is itself a concentrated
funding-stress episode and its removal would reduce the event count for the
precise hypothesis being tested. Branch B pre-registration must explicitly
address this asymmetry and state a justified choice.

No option may be selected after D1 analysis begins. The choice must be
pre-registered separately for Branch A and Branch B if they differ.

### 8.3 D1 Analysis Gate

D1 analysis design lock remains **HOLD** until:

1. SOLUSDT interval policy is decided and pre-registered.
2. This harness proposal (or a successor) receives independent review and Owner
   authorization.
3. A separate D1 analysis design lock is created, reviewed, and authorized.

D1 acquired data must not be opened for analysis without all three conditions
met.

---

## 9. Governance Boundaries

### What the Harness Authorizes (when reviewed and Owner-approved)

- Pre-registration of a candidate screening task.
- Screening of a candidate using the discovery slice only.
- Assignment of orientation result labels.
- Identification of `STRONG_ANOMALY_CANDIDATE` escalation triggers.

### What the Harness Explicitly Does Not Authorize

- Readiness promotion of any kind (paper, probe, runtime, live, or trading).
- Formal validation (held-out validation is a separate protected-lane step).
- Implementation of strategy rules, filters, or execution logic.
- Acquisition of new data without a separate acquisition design lock and
  Owner authorization.
- Opening the held-out slice for any reason during screening.
- Treating a screening hit as edge confirmation or as a `PASS_CANDIDATE`.
- Expanding the candidate instrument list, timeframe, or data source after
  data inspection.
- Capital deployment or allocation decisions.

### Harness Methodology Review

The harness methodology itself must receive independent review before it is
reused for any candidate. A reviewed and authorized harness may be reused for
multiple candidates without re-review of the harness itself, provided the
candidate pre-registration record is new and covers the specific candidate's
instruments, windows, and held-out design.

If the harness templates are materially modified, independent review of the
modified sections is required before further reuse.

---

## Next Gate

Independent review of this harness proposal is required.

After review, if accepted, the Owner must authorize reuse before any candidate
screening task begins.

This proposal does not authorize:
- D1 analysis or D1 harness implementation;
- any data acquisition or download;
- Setup E source resolution;
- any readiness, runtime, paper, probe, or live change;
- any formal validation.
