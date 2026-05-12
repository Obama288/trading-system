# Setup C DR1 Recent-Data Source / Window Clarification

## Purpose

Clarify the concrete candidate venue/source/window that could potentially satisfy the locked DR1 freshness requirement before any recent-data acquisition design lock is considered.

## Locked Requirement

- 4H candles;
- at least 6 contiguous months;
- window ending no earlier than 30 calendar days before a future DR1 rerun;
- no gap larger than one expected 4H step;
- exact source, venue, and window must be locked before download;
- no post-result window adjustment.

## Candidate Paths Considered

### 1. Bitget Public Historical Path

- Current known issue: the committed recent Bitget window already failed contiguity with max gap = 8h.
- Classification: currently not preferred unless a clearly different source/window can be pre-specified later.

### 2. Binance Public Historical Path

- Classification: candidate path to investigate later.
- Feasibility is not claimed here.
- A later decision/design step must check:
  - source endpoint or archive;
  - available 4H depth;
  - window contiguity;
  - same symbols.

### 3. Other Owner-Approved Public Source

- Allowed only as a later owner-approved fork.
- Not selected now.

## Proposed Clarification Outcome

- Preferred candidate source/window path for next planning step: Binance public recent 4H window feasibility clarification.
- Bitget is not selected as first candidate because the currently committed recent Bitget window already failed the locked contiguity rule.
- Other sources are deferred until the owner explicitly chooses them.

## What This Unlocks

If accepted, the next step may be:

- a dedicated recent-data acquisition / feasibility design lock focused on the chosen candidate path,

not an immediate download.

## What This Does Not Authorize

- data download
- network calls
- API probing
- DR1 rerun
- acquisition implementation
- paper-candidate design lock
- paper trading
- runtime wiring
- private API
- exchange operations
- readiness claims
