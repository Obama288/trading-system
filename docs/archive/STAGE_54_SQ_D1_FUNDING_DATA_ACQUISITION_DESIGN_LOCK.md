# Stage 54-SQ D1 Funding Data Acquisition Design Lock

## Purpose

Lock the requirements, candidate sources, held-out discipline, and acquisition
boundaries for public funding-rate history needed to enable the D1
cheap-falsification reconnaissance step under Setup D / Funding Carry / Funding
Stress.

This document authorizes planning only. It does not authorize acquisition,
downloads, network calls, API probing, processing, analysis, or backtesting.

## Gate Ancestry

- Setup D hypothesis note:
  `research/signal_observation/SETUP_D_HYPOTHESIS.md`
- Pre-D1 decision gate:
  `docs/PRE_D1_DECISION_GATE.md`
- D1 cheap-falsification design lock (review verdict: PASS):
  `docs/STAGE_54_SQ_D1_FUNDING_CHEAP_FALSIFICATION_DESIGN_LOCK.md`
- Pre-D1 funding data path availability decision gate
  (Owner-accepted outcome: `PROCEED_TO_D1_PUBLIC_DATA_ACQUISITION_DESIGN`):
  `docs/PRE_D1_FUNDING_DATA_PATH_AVAILABILITY_DECISION_GATE.md`

---

## 1. Objective

D1 is a cheap-falsification reconnaissance step. Its purpose is to determine
whether mechanism-consistent observational evidence exists for either or both
of the following branches before heavier formal Setup D research is justified:

**Branch A — Funding Carry / Compensation**
After materially positive funding states, do forward market-response
observations show any stable carry-related skew that is directionally coherent,
not obviously dominated by trend, and not immediately economically trivial?

**Branch B — Funding Stress / Unwind Vulnerability**
After extreme positive funding states, do forward observations show any
distinct reversal, stress, or unwind-like skew that is separable from the
ordinary carry-continuation behavior in Branch A?

D1 must preserve these as two distinct branches. It must not collapse carry
and stress into one vague "funding effect."

**Decision D1 enables (after analysis, review, and Owner decision):**

- `D1_SUPPORTS_CARRY_BRANCH` → may justify tighter carry-focused next-stage
  design lock if Owner decides to advance.
- `D1_SUPPORTS_STRESS_BRANCH` → may justify tighter stress-focused next-stage
  design lock if Owner decides to advance.
- `D1_MIXED_OR_INCONCLUSIVE` → refine hypothesis or define missing evidence;
  do not escalate.
- `D1_WEAK_OR_REJECT` → park or reject Setup D before heavier work.

No D1 result label is a PASS_CANDIDATE or automatic promotion. Every outcome
still requires independent review and Owner decision before any next step.

---

## 2. Data Requirements

### Funding-Rate History

- **Type:** event-level funding-rate observations, one per settlement interval
  per symbol.
- **Venue:** public perpetual futures exchange, no private account required.
- **Symbols:** BTCUSDT, ETHUSDT, SOLUSDT (USDT-M / USDT-margined perpetual
  futures).
- **Granularity:** 8-hour settlement intervals (one funding-rate observation
  per 8 hours per symbol).
- **Minimum historical depth:** 18 months of contiguous 8-hour funding
  observations covering at least two distinct funding-regime types (e.g.,
  elevated-positive, near-zero, and negative/oscillating periods). This is a
  minimum floor; the locked window below targets approximately 24 months.
- **Required fields per observation:**
  - `symbol` — asset identifier (e.g., BTCUSDT).
  - `fundingTime` — UTC timestamp of the settlement event (milliseconds or
    ISO-8601).
  - `fundingRate` — numeric funding rate at settlement (e.g., 0.0001 = 0.01%).
  - `markPrice` — mark price at the settlement time, if available from the
    same public endpoint without additional calls. Optional but preferred for
    later alignment checks.

### OHLCV Alignment

Committed Binance 4H OHLCV data (BTCUSDT, ETHUSDT, SOLUSDT; backward window
`2022-01-01T00:00:00Z` to `2023-12-17T12:00:00Z`, committed at `583e724`) is
the candidate OHLCV source for D1 cheap-falsification alignment.

A future acquisition task must verify this artifact's coverage aligns with the
funding-rate window before use. If the OHLCV artifact does not cover the full
locked funding window, the acquisition task must STOP and return for an Owner
decision rather than silently extending or substituting OHLCV data.

No new OHLCV acquisition is authorized by this design lock. No OHLCV
substitution or silent extension.

Open interest is explicitly out of scope for D1 unless a future owner-approved
gate expands scope.

---

## 3. Candidate Public Sources

### Classification Key

- **PRIMARY-CONFIRMED:** verified against primary project docs or direct repo
  evidence.
- **DOC-ONLY:** documented but not independently verified by direct access in
  this project.
- **UNVERIFIED:** existence or suitability not confirmed in any project session.
- **THIRD-PARTY:** from an external provider, not an exchange's own API.
- **CONTRADICTED:** conflicts with another verified source.

### Free / Public Sources (no credentials required)

| # | Source | Classification | Notes |
|---|--------|----------------|-------|
| 1 | **Binance USDT-M Futures public REST** `GET /fapi/v1/fundingRate` | DOC-ONLY (funding-specific endpoint); Binance public access PRIMARY-CONFIRMED via repo (`d770a05`, `583e724`) | Standard public endpoint; no auth; BTC/ETH/SOL perpetuals available from 2021; pagination via `startTime`/`endTime`; returns `symbol`, `fundingTime`, `fundingRate`, `markPrice`. **Selected primary candidate.** |
| 2 | **Binance public data archive** `data.binance.vision` (bulk CSV downloads) | UNVERIFIED for funding-rate data specifically | Kline data confirmed available in bulk; funding-rate CSV availability not verified in this project. If available, would be a convenient batch alternative to paginated REST. Requires verification before use. |
| 3 | **Bybit USDT-M public funding API** | UNVERIFIED | Alternative venue; public funding-rate history endpoint exists per general knowledge; not proven accessible in this project; different settlement timing conventions possible. Not the selected candidate at this stage. |

### Paid / Subscription Sources (not in scope for D1 under current constraint)

| # | Source | Classification | Notes |
|---|--------|----------------|-------|
| 4 | **Coinglass** | THIRD-PARTY / DOC-ONLY | Funding rate history available; free tier exists but may be limited in depth or resolution; full history likely requires paid plan. Not in scope unless Owner explicitly relaxes free constraint. |
| 5 | **Laevitas** | THIRD-PARTY / DOC-ONLY | Funding analytics platform; paid subscription required. Not in scope. |
| 6 | **Kaiko** | THIRD-PARTY / DOC-ONLY | Institutional paid data provider. Not in scope. |

### Requester-Pays / Infrastructure-Cost Sources

None identified for public funding-rate data. AWS requester-pays paths are not
applicable here.

### Private / Exchange-Account-Required Sources

Not applicable. All major public exchanges expose funding-rate history without
authentication.

### Selected Primary Candidate

**Binance USDT-M Futures public REST API** (`GET /fapi/v1/fundingRate`).

Justification:
- Binance public access is PRIMARY-CONFIRMED via existing repo artifacts
  (kline downloader at `d770a05`, OHLCV data at `583e724`).
- Same venue as the committed OHLCV data, minimizing alignment complexity.
- No credentials, no paid subscription, no infrastructure costs.
- BTC/ETH/SOL perpetual markets available with full history from at least 2021.
- No alternative source may be substituted without a new owner-approved design
  lock.

---

## 4. Held-Out / Contamination Discipline

### Locked D1 Reconnaissance Window

Window for D1 cheap-falsification: `2022-01-01T00:00:00Z` to
`2023-12-17T12:00:00Z`.

This window aligns exactly with the committed Binance 4H OHLCV artifact
(`583e724`), eliminating the 14-day OHLCV tail gap present in the prior
`2023-12-31` end date. It covers approximately 23.5 months across multiple
distinct funding regimes:
- Early 2022: elevated positive funding, crowded long demand.
- Mid–end 2022: bear drawdown, funding normalization and negative episodes.
- 2023: range-bound / partial recovery, mixed funding states.

Exact start/end timestamps must be confirmed and locked before any acquisition
begins. No post-acquisition window changes are permitted.

### Reserved Future Formal Validation Windows

The D1 reconnaissance window, once consumed by analysis, cannot serve as
formal held-out validation data for any later Setup D research step.

The following periods remain reserved and must not be opened or inspected
during D1:
- `2024-01-01T00:00:00Z` onwards (future candidate formal window).
- Committed Binance recent window `2025-11-12T12:00:00Z` to
  `2026-05-12T12:00:00Z` (committed at `d770a05`).

If D1 results justify further formal Setup D work, the formal validation window
must be stated and locked upfront before any formal analysis begins, per the
held-out preservation rule in `docs/BOUNDARIES.md`.

### Hard Rules

- No data content may be opened or inspected before source, path, window, and
  symbols are locked in an owner-approved design lock.
- Post-hoc splitting of an analysis-consumed window into "exploration" and
  "validation" sub-segments is rejected. Inspection contamination cannot be
  removed by relabelling.
- Public statistics, vendor claims, or third-party published results about
  funding effects are not evidence of edge for this project. They may inform
  a hypothesis but do not substitute for internal formal evidence.
- If any step would consume the 2024+ or recent window, the acquisition task
  must STOP and return for an Owner decision.

---

## 5. Acquisition Boundaries

### What the Next Acquisition Step May Do

- Download Binance USDT-M public funding-rate data for BTCUSDT, ETHUSDT,
  SOLUSDT on exactly the locked window (`2022-01-01T00:00:00Z` to `2023-12-17T12:00:00Z`).
- Use only the approved REST endpoint (`/fapi/v1/fundingRate`) or, if verified
  before the task, the Binance public data archive bulk CSV path.
- Verify alignment of committed OHLCV artifact with the funding-rate window.
- Perform deterministic validation of acquired funding data.
- Write funding data artifact and validation report to the intended research
  data path.
- Commit validated funding artifact and report (not analysis results).

### What the Next Acquisition Step Must Not Do

- Acquire data from any source other than the approved candidate.
- Acquire data outside the locked window.
- Begin D1 analysis before the funding artifact is validated and committed.
- Acquire open interest data.
- Use private endpoints, credentials, account data, or signed payloads.
- Acquire new OHLCV data without a new design lock.
- Inspect data content for analytical patterns during acquisition.
- Produce D1 result labels or research claims.
- Change source, symbols, or window mid-task after data is seen.

### Owner Gate Required to Move from Design Lock to Acquisition

This design lock alone does not authorize acquisition.

The following Owner-level gate is required before any acquisition begins:

> Owner must accept this design lock after independent review and explicitly
> authorize a bounded acquisition implementation task.

Independent review of this design lock is required before the Owner decides.

---

## 6. Failure Conditions

### HOLD — pause before proceeding

- This design lock has not been independently reviewed or accepted.
- Binance funding-rate API connectivity cannot be confirmed without a live
  check not yet authorized.
- The OHLCV alignment verification finds a gap that cannot be resolved without
  additional data acquisition outside this lock.
- A mid-task blocker requires improvising with an alternative source or window
  not covered by this lock. Return to Owner.
- The acquired data fails validation (`FUNDING_DATA_FAIL` or
  `FUNDING_DATA_BLOCKED`).

### NO-GO — do not proceed further without new Owner decision

- Source requires credentials, private endpoints, or account data.
- Acquisition would require opening or consuming the reserved 2024+ window.
- Setup D is explicitly parked or rejected by Owner before acquisition begins.
- A carry/stress branch cannot be separated at D1 even in principle, reducing
  D1 to a vague unreformable check.

---

## 7. Validation Requirements and Result Labels

### Deterministic Validation (required before D1 analysis)

- Row count per symbol.
- Start timestamp per symbol.
- End timestamp per symbol.
- Monotonic timestamp check (no out-of-order records).
- Duplicate timestamp check.
- Maximum gap check: must not exceed one 8-hour interval.
- Coverage result: PASS / FAIL per symbol and combined.

Validation must produce:
- A machine-readable artifact (JSON or equivalent).
- A concise plaintext summary.

Both artifacts must be committed before D1 analysis begins.

### Acquisition Result Labels

- `FUNDING_DATA_PASS` — all locked conditions satisfied for all three symbols;
  a future D1 implementation task may be scoped by Owner.
- `FUNDING_DATA_FAIL` — data fetched but one or more locked requirements fail;
  do not proceed to D1; return to Owner for alternative or park.
- `FUNDING_DATA_BLOCKED` — source or path could not be completed under
  approved constraints; clarify the blocker; do not improvise.

---

## Assumptions and Safeguards

- **D1 analysis design lock required before inspection.** A separate D1
  analysis design lock defining thresholds, statistics, and observation windows
  must pass independent review and Owner authorization before acquired funding
  data is opened or inspected for analysis. This acquisition lock does not
  authorize analysis.
- **8-hour granularity limit.** 8-hour funding settlement granularity may
  limit Branch B (funding-stress) sensitivity if unwind behavior develops within
  sub-8H windows. If D1 results are inconclusive on Branch B, this granularity
  constraint should be noted before attributing failure to the hypothesis.
- **Regime scope.** The 2022–2023 window represents specific historical regimes
  (bull, drawdown, partial recovery). Any D1 support for carry or stress
  branches does not imply cross-regime stability or out-of-sample validity.
- **Funding interval verification.** The acquisition task must verify funding
  interval consistency (expected: exactly 8h between consecutive settlements)
  using `fundingIntervalHours` or an equivalent deterministic gap check. Any
  non-standard interval must be flagged before proceeding.
- **Setup C funding diagnostics isolation.** During D1 analysis, committed
  Setup C reports containing funding diagnostic fields (`funding_rate_per_8h`,
  `funding_scenario`, `funding_stress`, `funding_adjusted_*`) must not be
  inspected for funding-behavior priors. Setup C funding diagnostics are
  synthetic/fixed-assumption inputs, not observed funding history, and must not
  contaminate D1 threshold or framing decisions.

---

## Anti-Cherry-Picking Rules

- No window change after data is seen.
- No symbol addition or removal after data is seen.
- No source substitution mid-task.
- No relaxing validation requirements.
- No using partial coverage as if it passed.
- No D1 analysis in the acquisition task.
- No treating `FUNDING_DATA_PASS` as Setup D research promotion or readiness
  claim of any kind.

---

## Stop Rules

- Stop if source requires credentials, private endpoints, or account data.
- Stop if OHLCV alignment check fails and cannot be resolved within this lock.
- Stop if acquired window cannot satisfy the locked start/end requirement.
- Stop if any step requires opening data beyond the locked window.
- Stop if task attempts D1 analysis before acquisition artifact is validated
  and committed.
- Stop if carry and stress branches are being collapsed mid-task.

---

## Next Gate

**Independent review of this design lock is required.**

After review, if accepted, the Human Owner must explicitly authorize a bounded
acquisition implementation task before any acquisition begins.

This document does not authorize:
- data acquisition or download;
- network calls or API probing;
- D1 cheap-falsification analysis or implementation;
- backtesting or strategy rules;
- open interest acquisition;
- new OHLCV acquisition;
- private exchange endpoints;
- Setup D status promotion;
- paper, runtime, trading, probe, or live readiness claims.

No acquisition begins from this document alone.
