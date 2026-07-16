# H1 Phase A Historical Funding Coverage Lock - 2026-07-17

Status: LOCKED / BOUNDED PUBLIC RUN AUTHORIZED / NO ANALYSIS

Family: H1 / Cross-Venue Perpetual Funding Dispersion
Purpose: blind structural coverage acquisition for historical funding records
Scope: BTC linear USDT perpetual contracts only

This document authorizes exactly one bounded unauthenticated public-data run
under acquisition ID h1_phase_a_coverage_20260717_v1. It does not authorize
Phase B, outcome inspection, venue substitution, analysis, testnet use, paper
trading, or live trading.

## 1. Allowed Question

The bounded run may answer only whether each frozen official public endpoint
can structurally cover the exact locked windows with the expected contract,
timestamps, pagination, and immutable raw provenance.

It must not compute, print, log, summarize, rank, or compare funding rates,
funding spreads, prices, basis, returns, fees, PnL, or any other economic
outcome. Coverage success is data-feasibility evidence only. It is not evidence
of edge and does not authorize discovery or validation analysis.

The prior latest-page transport result passed for all four frozen endpoints.
That result established only current transport and envelope/schema handling; it
did not prove historical coverage for any locked window.

## 2. Frozen Instrument And Venue Roster

Underlying and contract class are fixed as BTC linear USDT perpetuals:

| Priority | Venue | Contract ID | Official unauthenticated public endpoint |
|---:|---|---|---|
| 1 | Binance | `BTCUSDT` | `GET https://fapi.binance.com/fapi/v1/fundingRate` |
| 2 | Bitget | `BTCUSDT` with `productType=USDT-FUTURES` | `GET https://api.bitget.com/api/v2/mix/market/history-fund-rate` |
| 3 | Bybit | `BTCUSDT` with `category=linear` | `GET https://api.bybit.com/v5/market/funding/history` |
| 4 | OKX | `BTC-USDT-SWAP` | `GET https://www.okx.com/api/v5/public/funding-rate-history` |

Only these HTTPS hosts, paths, contract identifiers, and public
unauthenticated methods are allowed. Redirects, fallback hosts, archives,
mirrors, third-party sources, authenticated endpoints, API keys, cookies,
accounts, alternate symbols, and alternate venues are forbidden.

## 3. Exact UTC Windows

All intervals are half-open and use funding settlement timestamps in UTC:

| Class | Exact interval |
|---|---|
| Discovery | `[2023-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` |
| Validation | `[2024-07-01T00:00:00Z, 2025-07-01T00:00:00Z)` |
| Sealed holdout | `[2025-07-01T00:00:00Z, 2026-07-01T00:00:00Z)` |

No boundary may move after the first request. Records outside these intervals
may remain in an opaque raw response when imposed by page boundaries, but they
must not be used to replace missing in-window coverage. Structural metadata may
report only requested/actual minimum and maximum timestamps, row counts,
duplicates, ordering, gaps, and coverage booleans.

Structural continuity is locked as follows for each venue across the complete
sorted, deduplicated acquisition:

- maximum adjacent funding timestamp gap: 24 hours;
- start-boundary tolerance: the first timestamp must be no later than 24 hours
  after `2023-01-01T00:00:00Z`;
- end-boundary tolerance: the last timestamp must be no earlier than 24 hours
  before `2026-07-01T00:00:00Z`;
- records near only the outer boundaries do not establish coverage: a
  boundary-only dataset fails even when both boundary tolerances pass;
- continuity must hold through discovery, validation, and sealed-holdout
  boundary crossings as well as within each interval.

## 4. Exact Pagination Contract

The request budget is frozen at the sum of the per-venue maxima: 80 requests.
Pagination stops earlier only after the endpoint has structurally crossed the
oldest requested boundary or returned an empty terminal page.

Every non-empty page must demonstrate cross-page progression in the locked
direction. Repeated pages, repeated cursors, cursor reversal, or a next page
that does not extend the previously observed timestamp range fails closed.

### 4.1 Binance

- Query is `symbol=BTCUSDT`, ascending from the locked discovery start.
- Use `startTime` in ascending order and `limit=1000`.
- Maximum: 6 requests.
- The next `startTime` is the greatest returned funding timestamp plus one
  millisecond.
- A repeated or non-increasing cursor, duplicate page, empty page before the
  requested end, or failure to cover the full interval is a structural fail.

### 4.2 Bitget

- Query is `symbol=BTCUSDT`, `productType=USDT-FUTURES`, `pageSize=100`.
- Request `pageNo` exactly from 1 through 45.
- Pagination direction is reverse chronological.
- Maximum: 45 requests.
- Stop only when the oldest returned timestamp crosses the discovery start or
  an empty terminal page follows complete coverage.
- Repeated pages, chronology reversal inconsistent with the contract, or
  incomplete coverage are structural failures.

### 4.3 Bybit

- Query is `category=linear`, `symbol=BTCUSDT`, `limit=200`.
- Pagination is reverse chronological using `endTime`.
- Maximum: 24 requests.
- The next `endTime` is the smallest returned funding timestamp minus one
  millisecond.
- A repeated or non-decreasing cursor, duplicate page, empty page before the
  requested start, or incomplete coverage is a structural fail.

### 4.4 OKX

- Query is `instId=BTC-USDT-SWAP`, `limit=400`.
- Pagination is reverse chronological using `after`.
- Maximum: 5 requests.
- The next `after` value is derived from the oldest returned funding timestamp
  according to the official reverse-pagination contract.
- The official endpoint contract states approximately three months of funding
  history retention. Therefore OKX is expected to be structurally ineligible
  for the locked 2023-2026 windows. This is an eligibility result, not
  permission to substitute another source, archive, host, venue, symbol, or
  window.

## 5. Global Resource Bounds

- Maximum requests: 80 total across all four venues.
- Execution: sequential only; concurrency is 1 globally.
- Minimum pause between live-network page requests: 0.1 seconds; requests
  remain sequential.
- Timeout: 15 seconds per request.
- Maximum response body: 2 MiB per request.
- Maximum response bytes: 64 MiB total across the acquisition.
- Retries: none; exactly one attempt per request.
- Redirects: rejected.
- Required response `Content-Type`: `application/json`, optionally followed by
  a `charset` parameter; any other media type fails closed.
- Budget expansion, cursor recovery by guessing, and resume into an existing
  acquisition are forbidden.
- HTTP 401, 403, 407, 429, 5xx, timeout, truncation, unexpected content type,
  schema ambiguity, or unexpected final host/path fails closed.

The implementation must stop before exceeding any bound. A failed run keeps
its immutable evidence but cannot be resumed or published as passing.

## 6. Prior Contamination Register

This lock distinguishes transport availability from untouched research
evidence.

| Venue | Prior local funding-outcome status | Consequence for this H1 attempt |
|---|---|---|
| Binance | Funding outcomes were already inspected locally in Setup D and Setup F work. | Binance cannot provide untouched validation or holdout evidence for this H1 attempt, even if historical coverage passes. It cannot rescue a failed clean venue. |
| Bitget | Local inventory found no prior Bitget funding outcomes. | Eligible for untouched validation/holdout only if this blind coverage run passes and access controls remain intact. |
| Bybit | Local inventory found no prior Bybit funding outcomes. | Eligible for untouched validation/holdout only if this blind coverage run passes and access controls remain intact. |
| OKX | No local outcome claim is made here; the official endpoint contract has only approximately three months retention. | Structurally insufficient for the locked windows; no source substitution is allowed. |

Downloading Binance again, changing its file hash, or sealing a new copy does
not remove prior contamination. Re-sealing never restores an untouched window.

## 7. Deterministic Metadata-Only Venue Decision

Eligibility uses only contract identity, unauthenticated public access,
timestamp coverage, ordering, uniqueness, schema stability, pagination
completion, contamination status, and integrity controls. Funding magnitudes
and all economic fields are excluded.

The deterministic result is:

1. Evaluate all four frozen venues under this exact contract.
2. Mark Binance ineligible for untouched validation/holdout regardless of
   coverage because its relevant funding outcomes were previously inspected.
3. Mark OKX ineligible if the official retention-limited endpoint cannot cover
   every locked window; do not substitute a source.
4. If both Bitget and Bybit pass all structural and no-access checks, the only
   admissible clean pair is `Bitget + Bybit`.
5. If either Bitget or Bybit fails, fewer than two untouched venues remain and
   the verdict is `PARK H1 / DATA FEASIBILITY`.

There is no ranking, best-pair search, source shopping, or fallback to Binance
or OKX after observing metadata or outcomes.

## 8. Blind Raw Quarantine

Every response body is handled as opaque bytes and written create-only under a
new ignored acquisition directory. The implementation must verify before the
first request that the resolved directory is inside
`research/signal_observation/data/h1/`, is ignored by Git, is not tracked, and
does not already exist.

All opaque pages from this Phase A coverage acquisition are stored under
`<acquisition_id>/raw/<venue>/`, with one directory per frozen venue:

```text
<acquisition_id>/
  raw/
    binance/
    bitget/
    bybit/
    okx/
```

The entire acquisition is one sealed feasibility quarantine. Phase A does not
create releasable discovery, validation, or holdout datasets. Separate window
namespaces and their release gates belong to a later Phase B contract and are
outside this lock.

Files are first written to a same-filesystem staging location and atomically
published create-only. No overwrite, append, repair in place, mutable `latest`,
or deletion-and-replacement is allowed. No human or analysis process may open
or inspect any raw page produced by this acquisition.

## 9. SHA-256 And Provenance

Compute SHA-256 over the exact response bytes before parsing or transformation.
Each request ledger record binds:

- acquisition ID, implementation commit, request sequence, venue, host, path,
  and ordered non-secret query parameters;
- requested window and cursor semantics;
- request start/end UTC, HTTP status, byte count, row count, and structural
  timestamp coverage;
- raw response SHA-256 and relative immutable path;
- previous ledger-record SHA-256, terminal status, and sanitized failure code.

The final manifest binds every artifact by class, relative path, byte size, and
SHA-256. It must contain no raw row, response sample, funding value, price,
secret, local username, or absolute machine path. Hash mismatch, duplicate
target, or ledger-chain break is terminal.

## 10. No-Outcome And Access Controls

- Human-readable output is limited to venue/contract identity, HTTP/envelope
  status, field names, byte/row counts, timestamp bounds, ordering, duplicate
  and gap counts, coverage booleans, hashes, and sanitized failure codes.
- Funding rates and all economic values are never printed, sampled, summarized,
  plotted, compared, or included in exception messages.
- Debugging uses synthetic fixtures only. Manual raw-row inspection is
  forbidden.
- Acquisition code must not import strategy, simulator, statistics, plotting,
  notebook, or outcome-analysis modules.
- The entire Phase A raw acquisition remains sealed feasibility quarantine and
  must not be opened by a human or an analysis process.
- Any prohibited display or access marks the entire acquisition `CONTAMINATED`;
  closing or resealing it does not reverse that verdict.

## 11. Coverage Completion Verdicts

Allowed verdicts are limited to:

- `COVERAGE PASS`: the venue covered all three exact windows and passed all
  structural, resource, provenance, and access controls;
- `STRUCTURALLY INELIGIBLE`: endpoint retention, coverage, schema, contract,
  ordering, uniqueness, or pagination failed without outcome inspection;
- `CONTAMINATED`: prohibited output or access occurred;
- `ABORTED`: transport, resource, integrity, or implementation failure
  prevented a structural verdict;
- `PARK H1 / DATA FEASIBILITY`: Bitget and Bybit did not both remain clean and
  structurally eligible.

No verdict authorizes analysis. A coverage pass only permits a separate owner
decision after the remaining H1 preregistration fields are locked.

## 12. Execution Lock

- acquisition implementation:
  research/signal_observation/h1_phase_a_coverage.py;
- implementation commit: 620edab;
- final acquisition ID: h1_phase_a_coverage_20260717_v1;
- focused synthetic evidence: 32 passed covering pagination, budgets, no-leak
  sentinels, create-only quarantine, SHA-256, content type, chronology, gaps,
  and failure behavior;
- full repository evidence at the implementation commit: 1163 passed;
- Ruff on implementation and tests: all checks passed;
- structural reviewer: primary Codex agent, separate from the implementation
  worker;
- owner authorization: the owner's 2026-07-17 instruction go, issued after
  the Phase A transport result and the stated historical-coverage next step;
- execution command:
  python research/signal_observation/h1_phase_a_coverage.py --acquisition-id h1_phase_a_coverage_20260717_v1.

The acquisition directory must not exist before execution. Any code, source,
window, parameter, budget, or acquisition-ID change requires a new lock commit.
The authorized command may run once after this completed lock is committed.

## 13. Official Documentation References

These references identify the official endpoint documentation. This lock makes
no external claim beyond the endpoint and pagination/retention semantics fixed
above.

- Binance, Funding Rate History:
  `https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History`
- Bitget, Get History Funding Rate:
  `https://www.bitget.com/api-doc/classic/contract/market/Get-History-Funding-Rate`
- Bybit, Get Funding Rate History:
  `https://bybit-exchange.github.io/docs/v5/market/history-fund-rate`
- OKX, Get Funding Rate History:
  `https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate-history`
