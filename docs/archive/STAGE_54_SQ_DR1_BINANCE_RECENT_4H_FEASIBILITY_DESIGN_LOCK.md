# Stage 54-SQ DR1 Binance Recent 4H Feasibility Design Lock

## Purpose

- Define the exact feasibility/acquisition planning rules for a future Binance public recent 4H data step.
- Goal: determine whether Binance can provide a window that satisfies the locked DR1 freshness requirement.
- This document does not perform feasibility checks or downloads.

## Locked Target Requirement

- 4H candles;
- BTCUSDT, ETHUSDT, SOLUSDT unless a later owner decision changes scope;
- at least 6 contiguous months;
- window ending no earlier than 30 calendar days before the future DR1 rerun date;
- no gap larger than one expected 4H step;
- exact source, endpoint/archive path, venue, symbols, and window locked before download;
- no post-result window changes.

## Planned Feasibility Questions

Before any acquisition implementation, a future task must verify:

- which Binance public source/path is intended;
- whether it supports the required recent 4H depth;
- whether it can cover the locked symbols;
- whether the exact target window can plausibly satisfy contiguity;
- whether timestamp convention is compatible with later DR1 use;
- whether the path is public and research-only.

Feasibility verification must be docs-only and based on existing Binance public API documentation and committed downloader code. No network calls, no API probing, no live endpoint testing.

## If Feasibility Is Positive

- Next step may be a concrete Binance recent-data acquisition implementation design lock, subject to independent review and owner approval.
- No download is authorized by this design lock.

## If Feasibility Is Negative

- Do not force Binance.
- Return to owner decision: alternative approved public source/window or park freshness reopening.

## If Feasibility Is Inconclusive

- Clarify the unresolved source/window/coverage question first.
- No acquisition implementation.

## Anti-Cherry-Picking

- No changing window after seeing availability/result.
- No symbol substitution.
- No adding/removing symbols post hoc.
- No relaxing contiguity after feasibility evidence.
- No reclassifying partial coverage as sufficient.

## What This Does Not Authorize

- network calls
- API probing
- data download
- data mutation
- DR1 rerun
- paper-candidate design lock
- paper trading
- runtime wiring
- private API
- exchange operations
- readiness claims
