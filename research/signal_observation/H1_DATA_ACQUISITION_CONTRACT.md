# H1 Public Data Acquisition Contract

Status: DRAFT / NOT LOCKED FOR PHASE B / PHASE A TRANSPORT LOCKED

Contract version: `h1-acquisition-contract/0.1-draft`
Family: H1 / cross-venue perpetual funding dispersion
Parent preregistration:
`research/signal_observation/H1_CROSS_VENUE_FUNDING_DISPERSION_PREREGISTRATION.md`

This contract specifies a bounded, blind, two-phase acquisition process for
public data from the frozen venue roster: Binance, Bitget, Bybit, and OKX. It
does not perform or authorize outcome analysis.

The Human Owner authorizes acquisition from unauthenticated public data sources
only. This authorization does **not** include API keys, authenticated/private
endpoints, account data, testnet/demo access, orders, cancels, leverage changes,
transfers, withdrawals, runtime wiring, deployment, or paper/live trading.

No network call is made by this document. Exact public source paths, underlying,
contract identifiers, and UTC windows remain `LOCK REQUIRED`; until they are
filled and committed, this contract cannot authorize Phase B. The explicit narrow Phase A lock below is the only current network exception.

## Phase A Transport Lock - 2026-07-17

This lock authorizes one schema-and-transport probe only. It does not establish
historical coverage, venue eligibility, the selected pair, or Phase B
readiness.

- acquisition ID: h1_phase_a_transport_20260717_v1;
- implementation commit: 39ba91f;
- implementation: research/signal_observation/h1_phase_a_probe.py;
- operator and structural reviewer: Codex;
- owner authorization: the owner's 2026-07-17 instruction permits parallel
  acquisition of free public data under the locked no-outcome controls;
- underlying: BTC;
- contracts: Binance BTCUSDT, Bitget BTCUSDT, Bybit BTCUSDT, and OKX
  BTC-USDT-SWAP, all intended as linear USDT perpetuals;
- requests: exactly the four frozen REQUEST_SPECS in implementation commit
  39ba91f; no pagination, alternate parameters, fallback hosts, or redirects;
- resource bounds: four sequential requests, one attempt each, 15-second
  timeout each, 2 MiB maximum response each, 8 MiB maximum raw body total;
- output root:
  research/signal_observation/data/h1/phase_a/h1_phase_a_transport_20260717_v1/;
- Git storage: raw and metadata output remain ignored by the committed
  research/signal_observation/data/h1/ rule;
- allowed human-readable result: envelope status, byte and row counts, field
  names, contract identity, and minimum/maximum returned funding timestamps;
- forbidden result: funding values, prices, spreads, returns, PnL, rankings, or
  any outcome-based venue decision.

This latest-page probe is deliberately insufficient for the intended 2023-2026
research windows. A successful result permits a separately committed bounded
coverage/pagination lock; it does not permit Phase B or outcome inspection.

## 1. Purpose And Non-Purpose

The acquisition process may answer only:

- can the required public artifact classes be obtained for every locked window;
- are schemas, timestamps, pagination, and contract metadata reconstructable;
- can immutable raw artifacts and a sealed holdout be produced reproducibly;
- do structural quality checks pass without inspecting economic outcomes.

It must not answer:

- whether funding spreads are large, persistent, or profitable;
- which venue pair, symbol, period, threshold, or direction performs best;
- whether prices, funding, basis, volatility, liquidity, or returns predict PnL;
- whether H1 passes any Stage 2-4 economic gate.

Acquisition success means only that a bounded dataset exists under quarantine.
It is not research evidence, edge evidence, or readiness evidence.

## 2. Frozen Scope

### 2.1 Venue roster

The only allowed venues are:

1. Binance
2. Bitget
3. Bybit
4. OKX

No fallback venue may be added during a run. An unavailable venue produces an
eligibility failure; it does not permit source shopping.

### 2.2 Source restrictions

An allowed source must be one of the following after its exact path is locked:

- an official unauthenticated public REST endpoint;
- an official unauthenticated static historical-data archive;
- an official public metadata/specification page with machine-readable output.

Third-party aggregators, paid plans, requester-pays storage, scraped account
pages, browser sessions, cookies, API keys, signed requests, and secret-bearing
URLs are excluded. Redirects to a different host fail closed unless the final
host is explicitly locked in the source manifest.

### 2.3 Required lock fields

Before any request, commit:

- one exact underlying and canonical contract mapping per venue;
- exact source base URLs, endpoint paths, archive prefixes, and expected hosts;
- discovery, validation, and recent-holdout UTC start/end boundaries;
- timestamp boundary convention, expected cadence, and pagination direction;
- artifact classes available from each source;
- bounded request/page/byte/retry/time budgets;
- acquisition code commit hash and schema versions;
- storage root and confirmed Git ignore rule;
- acquisition operator and independent reviewer.

Changing any field after the first request requires aborting the run and issuing
a new contract version. Previously acquired artifacts remain immutable.

## 3. Two-Phase Blind Quarantine

### Phase A - Metadata-only eligibility

Phase A may query only locked public documentation, schema, contract metadata,
archive listings, and minimal bounded probes needed to establish transport and
coverage. It may record the fields allowed by Section 7. It must not compute,
display, log, summarize, rank, or compare outcome values.

If an endpoint cannot prove its schema without returning rows, the probe may
store the opaque response directly in quarantine. Human-readable logs may show
only HTTP/envelope facts, byte count, row count, field names, timestamp coverage,
and structural validation status. Funding, price, depth, basis, volume, fee PnL,
or return values must never be printed.

Phase A publishes a metadata-only eligibility artifact for all four venues in
the frozen roster. The deterministic pair rule in the parent preregistration is
applied only to allowed metadata fields. Outcome magnitude cannot influence
eligibility or rank.

### Phase B - Blind bounded acquisition

Phase B starts only after Phase A passes, the exact pair and windows are locked,
and the owner authorizes the bounded run. A non-analytical acquisition worker:

1. requests only locked source paths and ranges;
2. writes each response body as opaque raw bytes;
3. validates only transport, schema, timestamps, ordering, uniqueness, gaps,
   nullability, and declared contract identity;
4. publishes immutable discovery and validation quarantine artifacts;
5. publishes recent-holdout artifacts into a separately sealed namespace;
6. emits manifests and structural quality reports containing no outcome values.

The worker must not import strategy, simulator, signal, PnL, plotting, notebook,
statistics, or dataframe-profiling modules. It must not calculate funding
spreads, basis, returns, correlations, quantiles of economic fields, or venue
rankings based on outcome data.

## 4. Artifact Classes

Every published file belongs to exactly one class.

| Class | Contents | Human-readable before release |
|---|---|---|
| `CONTROL` | Contract, run manifest, schemas, code/version identity | Yes |
| `REQUEST_LEDGER` | One transport record per request, no response body | Yes |
| `SOURCE_METADATA` | Allowed Phase A eligibility fields | Yes |
| `RAW_DISCOVERY` | Byte-exact public responses for discovery | No |
| `RAW_VALIDATION` | Byte-exact public responses for validation | No |
| `RAW_HOLDOUT` | Byte-exact public responses for recent holdout | Sealed |
| `STRUCTURAL_QA` | Counts, timestamps, gaps, duplicates, schema failures | Yes |
| `ARTIFACT_MANIFEST` | Path, class, byte size, SHA-256, publication state | Yes |
| `ACCESS_LEDGER` | Every quarantine/holdout access or release decision | Yes |
| `FAILURE_RECORD` | Fail-closed reason and affected request/artifact IDs | Yes |

Raw artifacts are never committed to Git. Only reviewed schemas, source
contracts, manifests without local absolute paths, and redacted structural
reports may later be proposed for commit under a separate file-ownership scope.

## 5. Schema And Version Contract

All control artifacts use UTF-8 JSON or JSON Lines with sorted object keys and
an explicit schema identifier. Timestamps are RFC 3339 UTC with a `Z` suffix.
Decimals remain source text in raw data and decimal strings in control records;
they must not pass through binary floating point during acquisition.

Required schema IDs:

- `h1.run-manifest/1`
- `h1.source-contract/1`
- `h1.request-ledger/1`
- `h1.eligibility/1`
- `h1.structural-qa/1`
- `h1.artifact-manifest/1`
- `h1.access-ledger/1`
- `h1.failure-record/1`

Each record includes `schema_id`, `contract_version`, `acquisition_id`, and
`created_at_utc`. Source-native payloads are not normalized in quarantine.
Any later normalization is a separate, versioned transformation with raw input
hashes and is outside this acquisition authorization.

A source schema change is never accepted silently. Unknown fields may be stored
in opaque raw bytes, but a missing, renamed, type-changed, or semantically
ambiguous required field fails the affected source contract.

## 6. Storage And Git Exclusion

The proposed local storage root is:

`research/signal_observation/data/h1/`

Required layout:

```text
research/signal_observation/data/h1/
  staging/<acquisition_id>.partial/
  published/<acquisition_id>/
    control/
    metadata/
    discovery/raw/
    validation/raw/
    holdout/raw/
    manifests/
    qa/
    ledgers/
    SEALED
```

The current `.gitignore` does not yet declare this H1 path. Because this task
owns only this document, it does not modify `.gitignore`. Adding the exact rule
below and verifying it with `git check-ignore` is a hard precondition to any
future network run:

```gitignore
research/signal_observation/data/h1/
```

An acquisition must refuse to start unless:

- the resolved storage root is inside the exact locked H1 data directory;
- `git check-ignore` confirms every staging and publication path is ignored;
- no raw target path is tracked by Git;
- available disk space exceeds the locked byte budget plus atomic-publication
  reserve;
- staging and publication directories are on the same filesystem.

Control manifests intended for later review must be exported separately and
must not contain raw rows, response samples, secrets, query signatures, local
usernames, or machine-specific absolute paths.

## 7. Metadata-Only Eligibility Schema

One eligibility record per venue must contain only:

- `venue_id` and canonical venue name;
- locked source ID, host, endpoint/archive path template, and source type;
- public unauthenticated access: boolean;
- terms/license review status and review timestamp;
- expected artifact classes available;
- field names, declared types, units, and timestamp semantics;
- declared funding sign convention and settlement schedule availability;
- contract type, quote/settlement asset, multiplier metadata availability;
- symbol lifecycle and effective-dated specification availability;
- fee schedule and capacity/depth evidence availability;
- earliest/latest timestamp coverage and record count;
- cadence, page size, pagination rule, rate-limit headers, and compression;
- missing required fields, schema ambiguity, and structural gap count;
- discovery/validation/holdout coverage booleans;
- request IDs and raw artifact hashes supporting the record;
- eligibility result and enumerated structural reasons.

Allowed values describe availability and structure only. Specifically forbidden
are funding-rate values, funding-spread values, price/mark/index/depth values,
volume, basis, volatility, min/max/mean/median/quantiles of economic fields,
returns, PnL, Sharpe, drawdown, hit rate, or any performance-derived ranking.

Timestamp coverage may be computed from timestamp fields only. Gap detection
may use expected cadence, but may not condition gaps on market outcomes.

## 8. Request Ledger

Every attempted request receives a monotonically increasing `request_seq` and
a random `request_id` before transmission. The append-only JSONL record includes:

- schema and contract versions, acquisition ID, phase, venue, and source ID;
- request sequence, request ID, previous-ledger-record SHA-256;
- method, canonical host/path, redacted ordered query parameters;
- requested UTC range, page/cursor token hash, and artifact class;
- attempt number, start/end UTC, timeout, and elapsed milliseconds;
- HTTP status, redirect chain hosts, selected non-secret response headers;
- byte count, structural row count, content type, and content encoding;
- raw response SHA-256 and final relative artifact path;
- retry decision, terminal state, and failure code.

No authorization header, cookie, API key, signature, account identifier, full
cursor value, response sample, or outcome value may enter the ledger. Query
parameters containing opaque cursors are represented by SHA-256 only.

Ledger records form a hash chain. At finalization, the manifest stores the hash
of the final ledger record and the SHA-256 of the complete ledger file.

## 9. SHA-256 And Provenance

SHA-256 is computed over exact response bytes before decompression or parsing.
If a source supplies a compressed archive, record both:

- transport-object SHA-256 over downloaded bytes;
- extracted-object SHA-256 for each exact extracted file.

No line-ending conversion, CSV rewrite, JSON formatting, decompression overwrite,
or timestamp normalization may alter raw artifacts. Every derived structural
record references all input hashes and the acquisition code commit hash.

Artifact filenames use the form:

`<request_seq>_<request_id>_<sha256>.<source_extension>`

The final artifact manifest is sorted by relative path and records artifact
class, source request ID, byte size, SHA-256, schema ID where applicable, and
publication state. A manifest hash mismatch is a terminal integrity failure.

## 10. Immutable Atomic Publication

All writes occur under `<acquisition_id>.partial`. For each artifact:

1. stream into a unique temporary file with exclusive creation;
2. finalize the SHA-256 and byte count;
3. flush file contents and required directory metadata;
4. close the file;
5. atomically rename it to its content-addressed staging name;
6. fail if the destination already exists, even when hashes match.

Publication occurs only after all required requests and structural checks for
the bounded run reach a terminal PASS. The worker writes final manifests, closes
the request ledger, creates `SEALED` last, and atomically renames the entire
staging directory to `published/<acquisition_id>` on the same filesystem.

Publication is create-only:

- no overwrite, append, in-place repair, delete-and-replace, or resume into a
  published acquisition;
- no mutable `latest` directory or symlink;
- a retry uses a new acquisition ID and preserves the failed staging evidence;
- duplicate payloads may be referenced by hash but never silently substituted;
- published permissions are read-only for normal analysis users/processes.

An acquisition ID is UUIDv4 plus UTC creation timestamp. It is never reused.

## 11. Sealed Holdout Policy

The recent holdout is acquired in Phase B to prove availability but published
under `RAW_HOLDOUT` in a separate directory. Before Stage 4 release:

- no human, notebook, strategy, simulator, dataframe profiler, plotting tool,
  result agent, or exploratory process may open or parse holdout payloads;
- acquisition code may inspect only envelope, schema, timestamp, ordering,
  uniqueness, gap, nullability, and contract-identity fields;
- logs and QA reports expose no economic values or response samples;
- filesystem permissions should deny the normal analysis identity where the
  operating system permits;
- `SEALED` and the artifact manifest bind all holdout hashes;
- every open, copy, permission change, integrity check, or release attempt is
  appended to `ACCESS_LEDGER` with actor, purpose, UTC time, and owner decision.

Release requires all of the following: Stage 3 PASS, owner authorization for
one Stage 4 look, frozen analysis commit, matching contract/dataset hashes, and
an independent access-ledger review. Release is read-only and one-time. An
unauthorized or unexplained holdout access contaminates the holdout and forces
PARK pending a new independent path; resealing does not restore validity.

Validation is also quarantined from discovery analysis. It may be released only
once after Stage 2 PASS under the same hash and access-ledger controls.

## 12. Bounded Resource And Retry Policy

The locked manifest must set finite maxima for:

- total requests and requests per venue;
- total compressed and uncompressed bytes;
- pages/files per artifact class;
- wall-clock duration;
- request timeout;
- attempts per request;
- backoff ceiling and rate per host;
- concurrent requests, defaulting to one per host.

The worker must stop before exceeding any bound. HTTP 429 and transient 5xx may
use the locked bounded backoff. Authentication challenges, 401/403 responses,
unexpected redirects, CAPTCHA, paywalls, changed hosts, or key requirements are
not bypassed and are terminal for that source. No proxy rotation, scraping
evasion, alternate account, or unregistered mirror is permitted.

## 13. Failure Semantics

Acquisition is fail-closed. The following rules apply:

- partial downloads remain in staging and are never published as valid;
- timeout, truncation, checksum mismatch, unknown pagination, or non-monotonic
  cursor fails the affected request;
- duplicate pages with different bytes fail source integrity;
- missing window coverage, unknown funding sign, ambiguous timestamp, or
  unreconstructable contract change makes the venue ineligible;
- unexpected schema change fails; it is not coerced or guessed;
- budget exhaustion aborts the acquisition without expanding the budget;
- a failure on one venue does not authorize a different source, venue, symbol,
  contract, or window;
- fewer than two eligible venues results in `PARK H1 / DATA FEASIBILITY`;
- validation or holdout contamination results in `PARK`, not a replacement
  split from already inspected data;
- any private/authenticated endpoint contact is a boundary violation and
  terminates the run immediately;
- any accidental outcome print, summary, plot, ranking, or manual inspection is
  recorded as contamination and escalated before further work.

Failure records preserve request IDs, structural facts, and remediation class,
but no response body or outcome sample. A correctable transport implementation
bug may be fixed only in a new acquisition ID. Substantive source/window/schema
changes require a new committed contract version and owner decision.

## 14. No-Outcome-Inspection Controls

Before execution, the acquisition implementation must demonstrate tests that:

- stdout/stderr and structured logs cannot emit forbidden economic fields;
- raw files are not opened by default desktop/indexing/reporting workflows;
- eligibility ranking receives a schema containing only Section 7 fields;
- holdout and validation ACL/access gates fail closed;
- strategy, simulator, statistics, plotting, and notebook imports are absent;
- manifests are reproducible from raw hashes without reading outcome columns;
- malformed payloads cannot trigger a value dump in an exception message;
- request fixtures containing sentinel outcome values never leak those values.

Manual spot-checking of downloaded rows is prohibited. Debugging must use
synthetic fixtures or envelope/schema-only views. If real payload inspection is
unavoidable, the affected window is contaminated and cannot remain holdout.

## 15. Completion Artifacts And Verdicts

A bounded acquisition may produce only these verdicts:

- `FEASIBLE`: at least two venues pass structural eligibility and all locked
  discovery, validation, and sealed-holdout artifacts publish atomically;
- `INFEASIBLE`: structural requirements fail before outcome inspection;
- `CONTAMINATED`: prohibited access or output occurred;
- `ABORTED`: resource, transport, integrity, or boundary failure prevented a
  complete verdict.

`FEASIBLE` authorizes no analysis by itself. A separate owner gate and locked
Stage 1 preregistration are required before discovery data can be released to an
analysis process.

Required completion artifacts are the run manifest, source contracts, request
ledger, eligibility table, structural QA, artifact manifest, access ledger,
failure records if any, and a one-line verdict. No funding, price, spread,
capacity value, return, or PnL appears in the completion report.

## 16. Lock Checklist And Open Decisions

This contract remains `DRAFT / NOT LOCKED` until the following are committed:

- exact official public source host/path for each artifact class and venue;
- exact underlying and venue contract identifiers;
- exact discovery, validation, and recent-holdout UTC windows;
- source-specific timestamp, funding-sign, pagination, and revision semantics;
- expected schemas and version/change-detection rules;
- bounded request, byte, retry, concurrency, disk, and time limits;
- exact structural gap/null/duplicate acceptance rules;
- selected venue pair after metadata-only eligibility;
- storage root ignore rule added and verified;
- quarantine filesystem identity/ACL mechanism;
- validation and holdout release authority and access-ledger reviewer;
- acquisition implementation commit and synthetic no-leak test evidence;
- explicit owner authorization for the final bounded public-data run.

Until these decisions are locked, no acquisition command may execute. The
current owner authorization is limited to designing and, after lock, acquiring
unauthenticated public data. It grants no private exchange, account, testnet,
order, runtime, paper, live, or outcome-analysis authority.
