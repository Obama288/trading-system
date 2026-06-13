# Stage 54-SQ-DR1 Data Recency / Predictability Design Lock

## Purpose

- Determine whether current Setup C evidence is fresh/predictive enough to
  support moving toward a future paper-candidate design lock discussion.
- Determine whether Setup C should instead be parked or sent to structural
  review due stale or insufficient predictability evidence.
- Planning only. This does not implement DR1 and does not approve paper
  trading.

## Current State

- Setup C remains PASS_CANDIDATE research-only.
- Paper-prerequisites proposal accepted.
- C7 Bitget/Binance PASS.
- C8 closed as observational inconclusive; no C8b.
- Pre-DR1 Decision Gate passed the decision-filter: DR1 can unlock different
  next decisions under HIGH / LOW / INCONCLUSIVE outcomes.
- Escalation remains HOLD.

## DR1 Question

Does Data Recency / Predictability Reconnaissance show enough fresh and
independent predictive evidence for Setup C to proceed toward a future
paper-candidate design lock discussion?

## Locked Scope

- Setup family: Setup C / TSMOM volatility-targeted only.
- Venues: Bitget and Binance only unless a future owner-approved design lock
  changes scope.
- Symbols: BTCUSDT, ETHUSDT, SOLUSDT only.
- Timeframe: 4H only.
- Detector: frozen Setup C detector.
- Primary comparison: 40-bar lookback.
- No OKX work in DR1.
- No funding / open interest expansion in DR1.

## Allowed Data Sources / No New Download Rule

- Use existing committed Bitget and Binance C7 development and expanded CSVs
  only unless the owner separately approves a public-data download design lock.
- No new downloads in this design lock.
- No API calls.
- No private endpoints.
- No data mutation.
- If recent data is unavailable from committed artifacts, DR1 must return
  INCONCLUSIVE and define the missing data requirement rather than fabricating
  or substituting data.

## Candidate Analyses

Candidate analyses only; implementation requires independent review and owner
approval after this design lock.

### Recent Data Availability / Freshness Requirement

- Identify the most recent committed candle available for each venue/symbol.
- Compare available recency against an explicit future freshness window.
- Report whether enough recent out-of-window data exists to test persistence.
- Minimum freshness requirement: DR1 may treat recent-data evidence as
  sufficient only if committed artifacts contain at least 6 contiguous months
  of candles ending no earlier than 30 calendar days before the DR1
  implementation date. If unavailable, report INCONCLUSIVE and define the
  missing data requirement.

### Non-Overlapping Return Autocorrelation

- Evaluate non-overlapping returns consistent with the frozen Setup C lookback
  and rebalance cadence.
- Report whether return signs show supportive, weak, or inconclusive
  persistence without relying on overlapping-window autocorrelation alone.

### Variance-Ratio Style Predictability Check

- Compare multi-bar return variance behavior against shorter-horizon variance.
- Interpret as supportive only if directionally consistent with trend
  persistence and not merely noise amplification.

### BTC -> ETH/SOL Lead-Lag Check

- Test whether BTC directional movement leads ETH/SOL direction in a way that
  supports the Setup C signal family.
- Lead-lag is supportive only if directional agreement exceeds 60% on
  non-overlapping bars. Below 60% or underpowered coverage must be reported as
  inconclusive, not as supportive evidence.
- Observational only; no pair-ranking, filter, or strategy rule may be
  introduced.

### Setup C Recent / Out-of-Window Persistence Check

- If sufficient committed recent/out-of-window data exists, re-evaluate frozen
  Setup C behavior on that segment.
- If sufficient data does not exist, report INCONCLUSIVE and define the exact
  missing data requirement.

## Interpretation Rules

- HIGH / supportive evidence:
  Recent data is available, non-overlapping predictability checks are
  supportive, and frozen Setup C recent/out-of-window behavior does not
  contradict C7 evidence. Proceed to independent review, then a future
  paper-candidate design lock may be considered if the owner explicitly chooses.
- LOW / weak evidence:
  Freshness or predictability checks materially weaken the Setup C evidence.
  Park Setup C or trigger structural review before any paper-candidate design
  lock.
- INCONCLUSIVE:
  Required recent data or predictability evidence is missing, underpowered, or
  internally mixed. Define the missing data requirement and do not proceed to a
  paper-candidate design lock.

## Anti-Cherry-Picking Rules

- No post-result window changes.
- No excluding symbols.
- No excluding venues.
- No adding funding / open interest scope.
- No parameter optimization.
- No changing lookback/rebalance rules.
- No replacing committed CSVs.
- No interpreting exploratory checks as strategy filters.

## Stop Rules

- Stop if DR1 cannot produce different decisions under HIGH / LOW /
  INCONCLUSIVE outcomes.
- Stop if required recent data is unavailable and no owner-approved public-data
  download design lock exists.
- Stop if the implementation would require private endpoints, secrets, exchange
  operations, runtime wiring, or readiness promotion.
- Stop if a proposed analysis only explains a caveat but does not change the
  next decision.

## Review Requirement Before Implementation

- Independent review of this design lock is required before any DR1
  implementation.
- Owner approval is required before any public-data download design lock.
- Owner approval is required before any DR1 code, data processing, or report
  artifact generation.

## What DR1 Does Not Authorize

- Paper trading.
- Paper-candidate approval.
- Live trading.
- Runtime wiring.
- Private API.
- Exchange operations.
- New downloads.
- Code.
- Strategy filters.
- Parameter optimization.
- Gate changes.
- Readiness claims.
