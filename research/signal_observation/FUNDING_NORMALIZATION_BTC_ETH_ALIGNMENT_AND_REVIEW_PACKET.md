# Funding Normalization BTC/ETH Alignment And Review Packet

## Status

Status: PATCHED_REVIEW_REQUIRED.

Patches applied to design lock and pre-registration (baseline confound,
timestamp worked example + first-usable-period rule, normalization magnitude
floor distinction, STRONG_ANOMALY_CANDIDATE harness alignment). Design lock and
pre-registration require re-review before screening execution is authorized.
Screening execution remains NO-GO.

This packet supports two bounded planning/review tasks:

- prepare an independent/trader review packet for the Funding Normalization
  BTC/ETH screening design lock;
- perform metadata-only OHLCV alignment confirmation.

This packet does not authorize screening execution, acquisition, analysis,
EXPLORE, validation, backtests, strategy logic, implementation, readiness,
runtime, paper/probe/live activity, capital use, D1 analysis, data acquisition,
or a new stage.

Screening execution remains NO-GO. D1 analysis remains HOLD. Setup E remains
HOLD pending Hydromancer. Readiness/runtime/live remains NO-GO.

## Documents Reviewed

- `docs/STAGE_54_SQ_FUNDING_NORMALIZATION_BTC_ETH_SCREENING_DESIGN_LOCK.md`
- `research/signal_observation/FUNDING_NORMALIZATION_PREREGISTRATION.md`
- `docs/STAGE_54_SQ_REUSABLE_CHEAP_FALSIFICATION_HARNESS_PROPOSAL.md`
- `research/signal_observation/SIDEWAYS_FAMILY_NOTE.md`
- `research/signal_observation/setup_d_d1_funding_acquisition/d1_funding_acquisition_summary.txt`
- `research/signal_observation/setup_d_d1_funding_acquisition/d1_funding_validation_report.json`
- `docs/CURRENT_STATE.md`
- `research/signal_observation/RESEARCH_STATE.md`
- `docs/BOUNDARIES.md`
- `research/signal_observation/SETUP_C_DR1_BINANCE_RECENT_4H_FEASIBILITY_NOTE.md`
- Committed C7/Binance/DR1 references found in current docs and research notes.

## A. Independent / Trader Review Packet

### What The Design Lock Authorizes

The design lock authorizes a parameter-locked screening specification only. It
locks the candidate identity, universe, discovery/held-out split, state
definitions, observation windows, baseline, cost floor, result labels, output
constraints, and blocker conditions for a possible future bounded BTC/ETH-only
discovery screening run.

It also authorizes reviewer preparation and Owner consideration of a later
bounded screening decision after review and OHLCV alignment resolution.

### What The Design Lock Does Not Authorize

The design lock does not authorize screening execution, raw data inspection for
analysis, data acquisition, validation, held-out use, D1 analysis, SOLUSDT
inclusion, pair expansion, implementation, readiness, paper/probe/runtime/live
activity, capital use, or a new stage.

### Candidate Identity

- Candidate: Funding Normalization.
- Branch: Sideways Carry / Normalization.
- Harness family: Continuous-State.
- Universe: BTCUSDT and ETHUSDT only on Binance USDT-M.
- SOLUSDT: retained/flagged and excluded from this design lock.

### Locked Parameters

- Instruments: BTCUSDT and ETHUSDT only.
- SOLUSDT: retained/flagged and excluded.
- Split: chronological 70/30 row-count split.
  - Discovery rows: 1-1502 in fundingTime ascending order.
  - Held-out rows: 1503-2147.
- Funding state thresholds:
  - HIGH: fundingRate >= p80.
  - TRANSITION_HIGH: fundingRate in (p70, p80), excluded.
  - NEUTRAL: fundingRate in [p30, p70], baseline bucket.
  - TRANSITION_LOW: fundingRate in (p20, p30), excluded.
  - LOW: fundingRate <= p20.
- Sideways classifier:
  - 5% net move threshold.
  - 20-period lookback in funding-aligned periods.
  - 3-period minimum duration.
- Response windows:
  - W1: +1 funding period.
  - W3: +3 funding periods.
  - W8: +8 funding periods.
- Baseline:
  - NEUTRAL funding rows, currently regardless of sideways regime.
- Cost floor:
  - 9 bps, Continuous-State family default and candidate-level floor.

### Known Advisory Issue

The current baseline uses NEUTRAL rows regardless of sideways regime. The
reviewer should assess whether the design lock should be patched before any
screening so that the baseline is regime-matched, i.e. NEUTRAL AND SIDEWAYS.

Reason for review: the active state requires both funding displacement and
SIDEWAYS regime, while the current baseline controls only for funding neutrality.
This may be acceptable under the existing Continuous-State harness wording, but
it may also dilute the sideways-specific comparison. No screening should run
until the reviewer and Owner accept or patch this baseline choice.

### Known Blocker

OHLCV alignment confirmation is required before any screening execution.

The design lock requires confirming that the committed Binance 4H OHLCV artifact
contains BTCUSDT and ETHUSDT, overlaps the discovery window, uses a compatible
4H cadence, and can align to 8H funding settlement timestamps without a new
acquisition.

### Reviewer Questions

1. Is the baseline acceptable as NEUTRAL funding rows regardless of sideways
   regime, or should it be patched to NEUTRAL AND SIDEWAYS before screening?
2. Are the p80/p20 active thresholds and p30/p70 neutral thresholds defensible
   without data inspection?
3. Is the 70/30 row-count split appropriate for a discovery-only screening run?
4. Are the result labels non-evidence enough, and do they avoid readiness
   promotion?
5. Does the OHLCV alignment requirement sufficiently protect against accidental
   analysis or timestamp/lookahead mistakes?
6. Assuming OHLCV alignment passes or is patched cleanly, is this ready for
   Owner to consider bounded screening execution?

## B. OHLCV Alignment Confirmation Only

### Candidate OHLCV Source Paths Found

Candidate committed Binance 4H OHLCV paths:

- `research/signal_observation/data/binance/expanded/BTCUSDT_USDT-FUTURES_4H.csv`
- `research/signal_observation/data/binance/expanded/ETHUSDT_USDT-FUTURES_4H.csv`

Related committed paths were also present under
`research/signal_observation/data/binance/`, but the expanded paths are the
candidate source matching the design lock's C7/Binance artifact reference.

### Metadata Inspected

Metadata-only inspection covered:

- file existence and committed path names;
- CSV header;
- data row count;
- first timestamp sequence shape;
- last timestamp for coverage metadata;
- presence of the locked discovery-end timestamp
  `2023-05-15T08:00:00Z`;
- committed documentation of Binance CSV timestamp convention.

The CSV header is:

```text
timestamp,open,high,low,close,volume
```

Both BTCUSDT and ETHUSDT expanded files have 4H timestamp cadence visible in
the opening sequence:

```text
2022-01-01T00:00:00Z
2022-01-01T04:00:00Z
2022-01-01T08:00:00Z
2022-01-01T12:00:00Z
2022-01-01T16:00:00Z
2022-01-01T20:00:00Z
```

Both files report 4,294 data rows and last timestamp
`2023-12-17T12:00:00Z`. Both files contain `2023-05-15T08:00:00Z`, the
approximate locked discovery end from the funding design lock.

### BTCUSDT / ETHUSDT Presence

BTCUSDT and ETHUSDT are present and match the design lock's symbol scope.
SOLUSDT also exists in the broader C7 artifact family, but SOLUSDT is excluded
from this design lock and was not used for alignment confirmation.

### Timeframe Compatibility

The OHLCV files are 4H CSVs. A 20-period sideways classifier in funding-aligned
8H periods can plausibly be supported by a 4H source because each 8H funding
step corresponds to two 4H bars.

### Coverage Overlap

The candidate OHLCV files cover the locked funding discovery period in
principle:

- funding discovery start: `2022-01-01T00:00:00Z`;
- approximate funding discovery end: `2023-05-15T08:00:00Z`;
- candidate OHLCV first timestamp: `2022-01-01T00:00:00Z`;
- candidate OHLCV contains `2023-05-15T08:00:00Z`;
- candidate OHLCV last timestamp: `2023-12-17T12:00:00Z`.

This is sufficient coverage for the future BTC/ETH-only discovery screening
window, assuming timestamp convention is patched or accepted.

### Timestamp Alignment Assessment

Timestamps can plausibly align to fundingTime without inventing a new
acquisition, but alignment is not fully confirmed because of a timestamp
convention ambiguity.

Supporting facts:

- Funding timestamps for BTCUSDT and ETHUSDT are 8H cadence around
  `00:00`, `08:00`, and `16:00` UTC.
- Candidate OHLCV timestamps are 4H cadence and include `00:00`, `08:00`, and
  `16:00` UTC timestamps.
- The design lock wants close-price context aligned to fundingTime.

Review-required ambiguity:

- `research/signal_observation/SETUP_C_DR1_BINANCE_RECENT_4H_FEASIBILITY_NOTE.md`
  states that the committed downloader parses Binance kline open time and
  writes ISO timestamps to CSV.
- The Funding Normalization design lock describes "4H bar close timestamps"
  coinciding with 8H funding settlement times.
- If CSV timestamps are open times, then the row timestamp equal to fundingTime
  is the opening timestamp of the next 4H bar, not necessarily the close of the
  immediately preceding 4H bar.

This does not require new data acquisition, but it likely requires a design-lock
patch or reviewer-approved alignment rule before screening. The clean future
rule may be: for fundingTime `t`, use the close of the 4H kline whose interval
ends at `t`, which may be represented in the CSV by open timestamp `t - 4H`.
That rule is not authorized here; it is listed for reviewer consideration only.

### Blocker Assessment

| Blocker | Assessment |
|---|---|
| OHLCV source not found | Not blocked. Candidate paths found. |
| Symbol mismatch | Not blocked. BTCUSDT and ETHUSDT paths found. |
| Timeframe mismatch | Not blocked. Candidate files are 4H. |
| Coverage insufficient | Not blocked for discovery coverage. |
| Timestamp alignment unclear | Blocker remains. Open-time vs close-time convention needs review/patch. |
| Would require new data acquisition | Not blocked. No new acquisition appears required. |
| Would require raw analysis beyond this confirmation | Not blocked for metadata confirmation; screening remains NO-GO. |

### Final OHLCV Alignment Label

`OHLCV_ALIGNMENT_CONFIRMED_METADATA_ONLY_AFTER_TIMESTAMP_RULE`

Rationale: source, symbols, timeframe, and coverage confirmed by metadata
(BTCUSDT and ETHUSDT paths found, 4H cadence confirmed, discovery window
covered). The sole remaining blocker was the open-time versus close-time
timestamp convention ambiguity. That convention is now locked by the timestamp
convention patch in §11 of the design lock: for fundingTime t, use the CSV row
with open timestamp t − 4H (the kline whose interval ends at t). This label
reflects metadata-only confirmation; screening execution remains NO-GO pending
Owner GO decision.

## Final Boundary Restatement

No screening, acquisition, analysis, EXPLORE, validation, backtest, strategy
logic, implementation, readiness, runtime, paper/probe/live activity, capital
use, harness execution, D1 analysis, data acquisition, or new stage is
authorized by this packet.
