# Setup C DR1 Binance Recent 4H Feasibility Note

## Purpose

This is a docs-only feasibility verification note for the Binance public recent 4H candidate path. It is not acquisition, implementation, endpoint probing, data download, or a DR1 rerun.

## Locked Requirement Recap

- 4H candles;
- BTCUSDT, ETHUSDT, SOLUSDT;
- at least 6 contiguous months;
- window ending no earlier than 30 calendar days before a future DR1 rerun;
- no gap larger than one expected 4H step;
- source/window must be locked before download.

## Feasibility Evidence Reviewed

- Candidate Binance public source/path:
  - Binance USDT-M Futures public kline path represented in committed code as `https://fapi.binance.com/fapi/v1/klines`.
  - Existing committed project context: `research/signal_observation/binance_public_downloader.py`.
- 4H support:
  - The committed downloader declares supported intervals `1h` and `4h`.
- Symbol / market scope:
  - The candidate market is Binance USDT-M Futures.
  - Existing committed Binance artifacts already use BTCUSDT, ETHUSDT, and SOLUSDT 4H CSVs under `research/signal_observation/data/binance/`.
- Historical depth:
  - The committed downloader supports bounded `startTime` / `endTime` retrieval.
  - Existing committed Binance C7 development and expanded CSV artifacts show the project has previously represented Binance 4H history for the locked symbols.
  - This note does not empirically test whether a future exact recent window is available.
- Pagination / history retrieval:
  - The committed downloader includes bounded pagination with `startTime`, `endTime`, `limit`, and `max_pages`.
  - The committed code enforces a maximum page limit of 1500 rows.
  - A six-month 4H window is plausibly within the retrieval model in principle, subject to later owner-approved acquisition design.
- Timestamp convention:
  - The committed downloader parses Binance kline open time from millisecond epoch and writes ISO timestamps to CSV.
  - That convention appears suitable for later DR1 contiguity validation, which requires ordered 4H candles and gap checks.

No actual Binance endpoint availability, response shape, current symbol status, current history depth, or exact recent-window contiguity was tested in this task.

## Feasibility Result

FEASIBLE.

Rationale: Binance public USDT-M Futures kline documentation as represented by the committed downloader code, plus existing committed Binance 4H artifacts for the locked symbols, strongly support a plausible acquisition path in principle. Actual recent-window availability and contiguity still require a later owner-approved acquisition design and execution step.

## Decision Implication

Binance recent-data acquisition implementation design lock may be opened.

## What This Does Not Authorize

- API calls
- endpoint probing
- downloads
- data mutation
- DR1 rerun
- paper-candidate design lock
- paper trading
- runtime wiring
- private API
- exchange operations
- readiness claims
