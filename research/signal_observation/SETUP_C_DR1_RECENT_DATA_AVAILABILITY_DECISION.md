# Setup C DR1 Recent-Data Availability Decision

## Decision

The Pre-DR1 Recent-Data Availability Gate outcome is INCONCLUSIVE.
Do not open a recent-data acquisition design lock yet.
Next fork: clarify the candidate source / venue / window that could satisfy the locked DR1 freshness requirement.

## Why

- The already committed Bitget recent window failed the locked contiguity requirement; max gap = 8h.
- No alternative approved recent-data source/window has yet been defined with:
  - venue/source;
  - exact window timestamps;
  - feasibility of at least 6 contiguous months;
  - end no earlier than 30 calendar days before a future DR1 rerun;
  - no gap larger than one expected 4H step.
- Without that clarification, an acquisition design lock would be premature.

## Alternatives Considered

- Open a recent-data acquisition design lock immediately.
- Park Setup C freshness reopening immediately.

## Why Alternatives Were Not Chosen

- Acquisition design is premature because the source/window is not defined tightly enough.
- Immediate parking is too strong because a viable approved source/window may still exist.

## What This Does Not Authorize

- data download
- network calls
- DR1 rerun
- paper-candidate design lock
- paper trading
- runtime wiring
- private API
- exchange operations
- readiness claims

## Next Step

Create a source/window clarification document or decision gate that identifies the concrete candidate venue/source/window before any acquisition design lock.
