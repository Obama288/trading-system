# Stage 54-SQ DR1 Binance Recent Data Acquisition Design Lock

## Purpose

- Define the exact future implementation rules for acquiring a Binance public
  recent 4H data window that may satisfy the locked DR1 freshness requirement.
- This design lock authorizes planning only, not acquisition itself.

## Locked Target Scope

- Venue/source: Binance public USDT-M Futures historical kline path, as selected
  by the feasibility note.
- Symbols: BTCUSDT, ETHUSDT, SOLUSDT.
- Timeframe: 4H.
- Target use: DR1 freshness eligibility reopening only.
- No symbol substitution.
- No timeframe substitution.

## Locked Recent-Data Requirement

- At least 6 contiguous months of 4H candles.
- Window ending no earlier than 30 calendar days before the future DR1 rerun
  date.
- No gap larger than one expected 4H step.
- Exact start/end timestamps must be locked before acquisition.
- No post-result window changes.

## Future Implementation Task Must Do

- Use only the approved Binance public source/path.
- Download or assemble exactly the locked symbols/timeframe/window.
- Write data only to the intended research data path.
- Perform deterministic validation:
  - row count by symbol;
  - start/end timestamp;
  - monotonic timestamps;
  - duplicate timestamp check;
  - max gap check;
  - gap count;
  - contiguity result;
  - exact requirement PASS / FAIL.
- Produce a machine-readable validation artifact plus concise TXT summary.
- Do not rerun DR1 in the acquisition step.

## Data Acceptance Result

- `DATA_REQUIREMENT_PASS`: all locked conditions are satisfied for all three
  symbols.
- `DATA_REQUIREMENT_FAIL`: the window/source is fetched, but one or more locked
  requirements fail.
- `DATA_ACQUISITION_BLOCKED`: the source/path could not be completed under the
  approved constraints.

## Decision Implication

- `DATA_REQUIREMENT_PASS`: a later DR1 rerun design lock may be considered.
- `DATA_REQUIREMENT_FAIL`: do not rerun DR1; return to owner decision on
  alternative window/source or park freshness reopening.
- `DATA_ACQUISITION_BLOCKED`: clarify the blocker; do not improvise with a new
  source/window.

## Anti-Cherry-Picking

- No changing window after data is seen.
- No adding/removing symbols after data is seen.
- No relaxing contiguity requirement.
- No replacing Binance with another source mid-task.
- No using a partially valid window as if it passed.
- No DR1 rerun in the acquisition task.

## What This Does Not Authorize

- data acquisition now
- network calls now
- API probing now
- DR1 rerun
- paper-candidate design lock
- paper trading
- runtime wiring
- private API
- exchange operations
- readiness claims

## Next Step

- Independent review of this design lock.
- If accepted, Codex may receive a bounded acquisition implementation task.
