# Funding Normalization — Pre-Registration Design

> **Status: DISCOVERY DONE / NORMALIZATION_SCREEN_WEAK / HOLD_FOR_BROADER_PAIRS**
> BTC/ETH discovery screening committed at `d770553`. Overall label:
> NORMALIZATION_SCREEN_WEAK. Strong anomaly: false. Validation: NO-GO.
> Held-out: protected. Future broader-pairs work requires new pre-registration
> and separate Owner authorization. This document is a design record only. It
> does not authorize screening execution, data inspection, statistical analysis,
> backtesting, implementation, readiness, paper, probe, runtime, or live activity.

---

## 1. Status

DISCOVERY DONE / NORMALIZATION_SCREEN_WEAK / HOLD_FOR_BROADER_PAIRS.

BTC/ETH discovery screening committed at `d770553`. Overall label:
NORMALIZATION_SCREEN_WEAK. Strong anomaly: false. Blockers: none. Held-out
rows 1503–2147 protected and unused. SOLUSDT not decoded or used. No PnL,
returns, Sharpe, or trading metrics computed.

Reviewer verdict: NO-GO for validation. HIGH branch cap-contaminated
(p70=p80=0.0001; median Δf=0 for HIGH in all windows). LOW branch
directionally coherent across BTC and ETH but all windows below 9 bps
normalization magnitude floor (largest: ETH LOW W8 = 1.18 bps).

Validation: NO-GO. Held-out: protected. Future broader-pairs work:
candidate/source-feasibility only — requires new pre-registration and
separate Owner authorization. No screening, acquisition, validation,
readiness, or pair expansion authorized by this update.

This file records the pre-registration design for the Funding Normalization
candidate. It is a docs-only artifact.

Harness methodology: AUTHORIZED METHODOLOGY (see
`docs/STAGE_54_SQ_REUSABLE_CHEAP_FALSIFICATION_HARNESS_PROPOSAL.md`).
Validation: NO-GO. Held-out: protected.

---

## 2. Candidate Identity

- **Candidate name:** Funding Normalization
- **Signal family:** Sideways Carry / Normalization (Branch A)
- **Harness template:** Continuous-State (Family B)
- **Source backlog entry:** `research/signal_observation/RESEARCH_CANDIDATE_BACKLOG.md`
  — Sideways Candidate Map Addendum, Funding Normalization entry
- **Sideways family note:** `research/signal_observation/SIDEWAYS_FAMILY_NOTE.md`
  — Tier 1 candidate
- **Relationship to Setup D:**
  Setup D (Funding Carry / Funding Stress) covers the directional stress and
  carry branches in a trend-agnostic or stress-event context. Funding
  Normalization is a distinct sideways-regime sub-hypothesis: it requires the
  market to be statistically sideways and the edge is the normalization of
  displaced funding, not directional continuation or stress shock. These are
  structurally separate hypotheses. D1 data may be a shared future input, but
  D1 analysis remains HOLD pending the SOL interval policy decision and a
  separate D1 analysis design lock. This pre-registration does not authorize
  D1 analysis.

---

## 3. Hypothesis and Mechanism

**Core hypothesis:** In statistically sideways price regimes, elevated or
compressed perpetual funding rates that reflect crowded leveraged positioning
pressure will normalize over a measurable horizon as that pressure decays. The
edge hypothesis is funding-displacement normalization driven by positioning
mechanics, not naive range trading or directional continuation.

**Mechanism:**
- Perpetual funding is a contractual transfer paid from the long side to the
  short side (or vice versa) at each funding interval.
- When directional positioning is crowded — especially leveraged long
  concentration — funding can become persistently elevated above a neutral
  state. This is a financing/crowding signal, not purely a price signal.
- In a sideways price regime where there is no broad directional trend to
  sustain the crowded positioning, the cost of holding that leverage accumulates
  and the crowding pressure is expected to decay.
- As the crowding unwinds, funding normalizes toward its neutral state (near
  zero or equilibrium for the asset).
- The payment stream during normalization and the position dynamics of unwind
  constitute the candidate edge mechanism.

**Why sideways regime is required:**
- In a strong uptrend, elevated funding can persist because directional returns
  justify the carry cost. The normalization hypothesis requires the directional
  support to be absent.
- Sideways regime classification is therefore a mandatory context layer, not an
  optional filter.
- This condition must be operationalized mechanically in the state definition
  before any screening run is authorized.

**Why this is not naive range trading:**
- The state is defined by funding displacement plus regime classification, not
  merely by price level within a historical range.
- The mechanism is counterparty and flow driven (leveraged positioning pressure
  and its decay), not "price near the bottom of the range."

---

## 4. Hypothesis Prior Sources (HD1 Declaration)

Per HD1 (harness safeguard), this pre-registration must declare prior sources
that informed the hypothesis. This is not blind discovery.

| Prior source | Content used | Source confidence |
|---|---|---|
| `research/signal_observation/SETUP_D_HYPOTHESIS.md` | Funding Carry / Funding Stress mechanism, two branches (carry/compensation and stress/reversal), counterparties = leveraged long-side demand, contractual nature of funding transfers | DOC-ONLY |
| `research/signal_observation/setup_d_d1_funding_acquisition/d1_funding_acquisition_summary.txt` | D1 data availability and quality metadata (PASS/FLAGGED status, row counts, interval audit, SOLUSDT flagged period). Not used for analysis — metadata only | DOC-ONLY |
| `research/signal_observation/SIDEWAYS_FAMILY_NOTE.md` | Sideways branch A / normalization framing, required context layers (regime confirmation, flow/positioning confirmation, regime-break risk), Tier 1 status, Continuous-State harness assignment | DOC-ONLY |
| `research/signal_observation/RESEARCH_CANDIDATE_BACKLOG.md` | Sideways Candidate Map Addendum entry for Funding Normalization | DOC-ONLY |
| `docs/STAGE_54_SQ_REUSABLE_CHEAP_FALSIFICATION_HARNESS_PROPOSAL.md` | Continuous-State Family B template structure, 9 bps cost floor default, result label system, HD1-HD3 safeguards, STRONG_ANOMALY_CANDIDATE label and conditions | DOC-ONLY |
| Trader / QA design inputs from prior conversations | General mechanism framing, sideways-versus-trend distinction, cost-floor rationale | DOC-ONLY |

No raw data was inspected. No statistical patterns from live or historical data
were observed prior to writing this pre-registration. The hypothesis is
structural and mechanism-first.

**Undeclared borrowed priors:** None known. The sideways-normalization framing
and its separation from Setup D were developed in prior design conversations
and are declared above. There are no undeclared priors from academic or
practitioner literature embedded in the hypothesis without citation.

---

## 5. Universe and Pairs

**Core clean pairs (D1 data acquired, PASS):**

- BTCUSDT perpetual (Binance): 2147 rows, all 8h intervals, 2022-01-01 to
  2023-12-17. PASS. Eligible for screening subject to Owner authorization.
- ETHUSDT perpetual (Binance): 2147 rows, all 8h intervals, 2022-01-01 to
  2023-12-17. PASS. Eligible for screening subject to Owner authorization.

**Flagged pair (D1 data acquired, RETAINED/FLAGGED):**

- SOLUSDT perpetual (Binance): 2222 rows, 101 non-8h gaps (98×2h gaps, 3×4h
  gaps) concentrated in 2022-11-09 to 2022-11-18 (FTX collapse period).
  RETAINED/FLAGGED NON_STANDARD_INTERVALS_FOUND. See Section 12 for handling
  options.

**Future expansion (not authorized, source-feasibility first):**
- Other major perpetuals (other exchanges, other assets) are candidates for
  future universe expansion, subject to source-feasibility confirmation and
  separate data acquisition authorization.
- See Section 13.

---

## 6. Data Status

- **D1 funding data:** Acquired. BTCUSDT and ETHUSDT PASS. SOLUSDT
  RETAINED/FLAGGED. Acquisition summary at:
  `research/signal_observation/setup_d_d1_funding_acquisition/d1_funding_acquisition_summary.txt`
- **D1 OHLCV context:** Not confirmed acquired as a locked path. OHLCV
  availability for sideways-regime classification requires a separate source
  feasibility confirmation before screening can be authorized.
- **Raw data opened for analysis:** NO. No data file has been opened, loaded,
  or analyzed in this pre-registration design step.
- **D1 analysis gate:** HOLD. Two conditions remain unmet: (1) SOL interval
  policy decision; (2) separate D1 analysis design lock. This pre-registration
  does not satisfy those conditions. D1 analysis is not authorized by this
  document.

---

## 7. Discovery / Held-Out Split

**D1 data window:** 2022-01-01 to 2023-12-17 (BTCUSDT/ETHUSDT).

**Proposed split design (Owner decision required before screening):**

The split must be declared before any data is opened for analysis.

| Option | Discovery window | Held-out window | Rationale |
|---|---|---|---|
| A — Chronological 70/30 | 2022-01-01 to 2023-01-25 (~70%) | 2023-01-26 to 2023-12-17 (~30%) | Simple chronological split; held-out contains post-FTX normalization regime |
| B — Event-anchored split | 2022-01-01 to 2022-11-08 (pre-FTX) | 2022-11-09 to 2023-12-17 (FTX collapse onward) | Discovery avoids the stress episode entirely; held-out includes the stressed and recovery periods |
| C — Stress-period bridge | 2022-01-01 to 2022-10-31 | 2023-01-01 to 2023-12-17 | Excludes FTX collapse window (2022-11 to 2022-12) from both splits; cleaner regime definition but reduces total sample |

**Owner must select one option before screening execution is authorized.**
If no option is acceptable, a different split design may be proposed.

**SOLUSDT split:** If SOL is included under any handling option (see Section
12), its split must be declared separately and match or be more conservative
than the BTC/ETH split.

---

## 8. State Definition

The Continuous-State harness requires a state variable that is measured at
each observation point rather than a binary event trigger. For Funding
Normalization, the state is a composite of two required conditions:

**Condition 1 — Funding displacement:**
Perpetual funding at the observation timestamp is displaced from a neutral
baseline. Direction (elevated / compressed) and magnitude must be defined
mechanically before screening. No threshold has been calculated from the data.
The threshold must be pre-registered in the next gate step before any data
is opened.

**Condition 2 — Sideways regime classification:**
Price is in a statistically sideways regime at the observation timestamp. This
requires a mechanical definition of sideways (not merely "no recent breakout").
The definition must include:
- A price-based regime classifier (e.g., rolling trend magnitude below a
  threshold, or a statistical range test) applied to OHLCV at the observation
  window.
- A minimum regime duration requirement so that brief consolidations are not
  classified as sideways.
- An explicit exclusion of windows where a directional trend is above the
  flatness threshold.

Both conditions must be met simultaneously for the state to be active.

**What is not yet defined and must be pre-registered before screening:**
- Exact funding displacement threshold (absolute, percentile, or z-score
  relative to rolling baseline).
- Exact sideways classifier method and lookback.
- Exact minimum regime duration.
- Observation interval (8h aligned to D1 funding ticks; OHLCV must match or
  be resampled consistently).

These definitions must be locked in writing before any data is opened for
measurement. No data-driven calibration of these thresholds is permitted; they
must be set from structural rationale or locked before inspection.

---

## 9. Null and Baseline

**Null hypothesis:** Funding displacement in a sideways regime carries no
predictive information about subsequent funding normalization or associated
return patterns. Any observed pattern is consistent with noise.

**Baseline:**
Per the Continuous-State Family B harness template, the baseline is the
neutral-state return distribution. For this candidate, the baseline is
restricted to observations where **Condition 1 = NEUTRAL AND Condition 2 =
SIDEWAYS** (regime-matched baseline). Observations where Condition 1 = NEUTRAL
but Condition 2 = NON_SIDEWAYS are excluded from the baseline and assigned
NEUTRAL_NON_SIDEWAYS state (see screening design lock §5 and §7). This ensures
the only differing variable between treatment and baseline is the funding state,
not the regime mix.

**Falsification criterion:**
If the active-state distribution (both conditions met) is not statistically
and economically distinguishable from the regime-matched neutral-state baseline
above the 9 bps normalization magnitude floor (see §10), the hypothesis is
FALSIFIED at this screening level. An inconclusive result does not advance to
implementation or paper readiness.

---

## 10. Cost Floor (HD2)

Per HD2 (harness safeguard), the cost floor is locked at the family level and
cannot be revised downward after data inspection.

**Harness family:** Continuous-State (Family B).
**Family-level default cost floor:** 9 basis points (bps) round-trip.

**Candidate-level floor:** 9 bps round-trip (matching family default). This
floor may be made more conservative if structural rationale (e.g., known
execution costs for the specific pairs, wider spreads in stress periods)
supports a higher floor. It cannot be revised downward after any data has been
opened.

**Application to this screen:** This screen's response variable is Δf(t, t+N) —
a funding rate change, not a realized trade PnL. The 9 bps figure is applied
here as a **normalization magnitude floor**: if |Δf| < 9 bps, the normalization
magnitude is too small to be economically interesting at the screening stage,
even if directionally consistent. This does not constitute a cost-coverage proof
or evidence of tradeability. Any future trading or PnL cost model requires
separate design and validation.

**What the floor covers:**
- Exchange taker fee (both legs).
- Estimated slippage for the trade size.
- Funding costs on the position during the holding period (where applicable).

**What the floor does not cover:**
- Carry payments received during the holding period (these are part of the edge
  calculation, not a cost offset at pre-registration stage).
- Operational costs, financing costs beyond exchange funding, or impact beyond
  the position window.

**Floor lock statement:** This 9 bps floor is locked as of this pre-registration
document. Any request to lower this floor after data inspection must be treated
as a governance violation and flagged to Owner.

---

## 11. Result Labels

Results at screening stage will be labeled using the harness standard vocabulary
adapted for Funding Normalization:

| Label | Condition |
|---|---|
| NORMALIZATION_SCREEN_POSITIVE | Active-state distribution shows directional and economically meaningful pattern above the 9 bps cost floor; statistical separation from neutral-state baseline meets pre-registered thresholds |
| NORMALIZATION_SCREEN_WEAK | Pattern is present but magnitude is below cost floor, or statistical separation is marginal; does not advance |
| NORMALIZATION_SCREEN_ABSENT | No directional pattern detected; active state is indistinguishable from neutral baseline; hypothesis FALSIFIED at this screening level |
| NORMALIZATION_SCREEN_INCONCLUSIVE | Sample too small, regime too rare, or data quality issues (e.g., SOL flagged gaps) prevent a clean determination; does not advance without resolving the underlying issue |
| STRONG_ANOMALY_CANDIDATE | Result is unusually strong under the governing patched design-lock trigger; triggers mandatory HD3 forensic review by an independent reviewer; screener cannot self-clear |

**STRONG_ANOMALY_CANDIDATE governing trigger:** The governing
STRONG_ANOMALY_CANDIDATE trigger for screening execution is the patched design
lock §9. If this pre-registration conflicts with design lock §9, design lock
§9 governs.

**HD3 reminder:** A STRONG_ANOMALY_CANDIDATE result triggers mandatory
independent forensic review. The screener cannot self-clear. Output of forensic
review is input only; Owner decision required for escalation.

---

## 12. SOLUSDT Handling Options

SOLUSDT is RETAINED/FLAGGED due to 101 non-8h gaps (98×2h, 3×4h) concentrated
in 2022-11-09 to 2022-11-18 (FTX collapse period). Owner must select a handling
option before SOLUSDT is included in any screening run.

| Option | Description | Risk |
|---|---|---|
| A — Exclude entirely | SOLUSDT is excluded from all screening; core pairs are BTC and ETH only | Reduces universe; simplest clean path |
| B — Separate flagged branch | SOLUSDT runs in a separate isolated screening branch with an explicit label noting the flagged data; results reported separately; cannot be merged with clean BTC/ETH results | Allows later reuse if SOL issue is resolved; adds complexity |
| C — Conditional inclusion with gap policy | SOL included only if a formal gap-handling policy is declared and pre-registered (e.g., gaps filled by forward-carry, gaps excluded, sub-period only) | Requires separate design lock for gap policy before use |
| D — Defer | SOL decision deferred to a future event-triggered design where the FTX episode is a candidate event rather than a data defect | May be better fit for stress-branch framing |

**Default if Owner makes no selection:** Option A (exclude) is used for the
initial screening. SOL is not included until a handling option is explicitly
authorized.

---

## 13. Future Pair Expansion

Future universe expansion beyond BTC and ETH is a candidate-map item only.
No expansion is authorized by this pre-registration.

**Required steps before any expansion:**
1. Source feasibility confirmation for the candidate pair's funding history
   (exchange, coverage window, interval regularity).
2. Separate data acquisition authorization.
3. Pre-registration amendment or new pre-registration for the expanded universe.

**Suggested expansion sequence (priority order, not authorized):**
- High-liquidity majors on the same exchange: additional major perpetuals with
  confirmed funding history and clean intervals.
- High-liquidity alts on confirmed exchanges: assets with sufficient liquidity
  that systematic execution is plausible.
- Lower-liquidity alts: only after evidence that the mechanism holds in higher-
  liquidity pairs and after source feasibility confirms data quality.

No expansion runs before BTC/ETH core screening results are available and
reviewed.

---

## 14. Forbidden Actions

The following actions are explicitly forbidden based on this pre-registration
design and the current authorization state:

- Opening, loading, or inspecting any raw D1 funding data file for analysis
  or statistical measurement.
- Calculating any threshold, return, edge estimate, z-score, percentile, or
  other statistic from the acquired data.
- Running any backtest, screening execution, EXPLORE run, or strategy
  evaluation.
- Treating this pre-registration as authorization for screening. It is not.
  Screening requires a separate Owner authorization at the next gate.
- Revising the cost floor (9 bps) downward after any data has been opened.
- Advancing SOLUSDT to a screening run without a declared handling option
  and separate Owner authorization.
- Treating any result from an informal or exploratory run as a screening result
  under this pre-registration. Only a formally authorized screening run counts.
- Self-clearing a STRONG_ANOMALY_CANDIDATE result. HD3 forensic review must be
  independent.
- Treating this pre-registration as authorization for D1 analysis. D1 analysis
  remains HOLD.
- Promoting any result to implementation, readiness, paper, probe, runtime,
  or live status without a full Owner gate at each stage.
- Acquiring new data, making network calls, or contacting external APIs.
- Creating a new stage or promoting this candidate to an active stage number.

---

## 15. Next Gate (Owner Decision Required)

Screening execution is not authorized. The following options are available for
the next Owner decision:

| Option | Action | Prerequisite |
|---|---|---|
| A — Authorize screening design lock | Owner authorizes the creation of a formal screening design lock document that finalizes the undefined state-definition parameters (funding displacement threshold, sideways classifier, lookback, minimum regime duration) before any data is opened | This pre-registration reviewed and accepted; OHLCV source feasibility confirmed or scoped |
| B — Authorize OHLCV source feasibility first | Owner authorizes a source-feasibility check for OHLCV data needed for sideways regime classification before advancing to screening design lock | Needed if OHLCV path is not already confirmed |
| C — Authorize SOL handling policy | Owner selects a SOLUSDT handling option (Section 12, Options A–D) to resolve the flagged-data question before screening | Can be combined with Option A or B |
| D — Hold pre-registration | Owner puts this pre-registration on hold; no next action until further Owner decision | No prerequisite; freezes all forward progress |

**Owner must explicitly select one or more options before any screening work
begins. Absence of selection = Option D (hold).**

---

## §16 Latency Classification

- Operational fit: latency-tolerant.
- Signal half-life: hours to days; normalization pressure persists across
  multiple 8H funding cycles.
- Human-in-loop: acceptable for research design, screening design review,
  and result review.
- Automation required: no; not required for research phase.
- Intentional first-prototype rationale: Funding Normalization was selected
  partly because its latency profile fits the current solo-operator stage
  without requiring execution automation.
- This section does not authorize screening, analysis, or data inspection.

---

*End of pre-registration design record.*
