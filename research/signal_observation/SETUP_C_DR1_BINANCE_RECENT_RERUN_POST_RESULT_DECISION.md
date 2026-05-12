# Setup C DR1 Binance Recent Rerun Post-Result Decision

## Decision

DR1 Binance recent rerun result is LOW.
Do not open a Setup C paper-candidate design lock.
Do not open DR1b or any rescue rerun.
Park Setup C from active progression.

## Why

- Freshness eligibility is now satisfied on the committed Binance recent 4H window.
- With the freshness blocker removed, DR1 does not support continued progression:
  - autocorrelation is weak;
  - variance-ratio is weak;
  - lead-lag is inconclusive;
  - Setup C recent persistence is weak;
  - volatility-targeted post-cost moderate persistence is negative.
- This is a substantive fresh-window LOW result, not a data-eligibility failure.
- Earlier C7 Bitget/Binance PASS findings remain valid historical research
  evidence, but they are not sufficient to override the recent DR1 LOW result
  for progression purposes.

## Alternatives Considered

- Open a paper-candidate design lock anyway.
- Launch DR1b / rescue diagnostics to reinterpret the LOW result.
- Keep Setup C active while postponing the decision.

## Why Alternatives Were Not Chosen

- Paper-candidate progression is not justified after a fresh-window LOW result.
- Rescue diagnostics would violate the decision-gate discipline and risk
  post-hoc salvage behavior.
- Keeping Setup C active without a justified next decision would create false
  momentum.

## What This Does Not Authorize

- paper trading
- paper-candidate approval
- runtime wiring
- private API
- exchange operations
- new diagnostics
- DR1b / rescue rerun
- readiness claims

## Next Process Lane

Future new setup-family work should follow the already approved
hypothesis-first process: mechanism-first hypothesis note before any new setup
design lock. A funding carry / funding stress family remains a leading
candidate for future owner discussion, but is not opened by this decision
record.
