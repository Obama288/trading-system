# Setup C Paper-Prerequisites Proposal

Governed by: docs/STAGE_54_SQ_SETUP_C_PAPER_PREREQUISITES_DESIGN_LOCK.md

## Purpose

- Define concrete prerequisites that must be satisfied before Setup C can be
  considered for any future paper-candidate discussion.
- This is not paper approval.
- This is not runtime approval.
- This is not trading approval.
- This is not live approval.

## Status

- Setup C / TSMOM remains PASS_CANDIDATE research-only.
- C7 Bitget PASS and Binance PASS are accepted research evidence.
- C8 is closed as observational inconclusive; no C8b.
- Escalation remains HOLD.

## Non-Readiness Statement

- Paper readiness: NO.
- Runtime readiness: NO.
- Trading readiness: NO.
- Probe readiness: NO.
- Live readiness: NO-GO.

## Prerequisite Categories

### A. Evidence Prerequisites

- C7 Bitget/Binance PASS evidence remains accepted.
- C8 caveat is recorded and not treated as a C7 failure.
- No unresolved blocker contradicts C7 evidence.
- No new same-dataset diagnostics unless a Pre-Cn Decision Gate is explicitly
  approved.
- Any future new diagnostic must unlock a decision, not just explain a caveat.

### B. Data-Recency Prerequisite

- Additional recent data is not required before creating this docs-only
  proposal.
- Any future paper-candidate proposal must define a separate data-recency
  requirement before implementation can be discussed.
- The future data-recency requirement should minimally contain:
  - Exact date/window rule.
  - Venue/source.
  - Minimum candles/intervals.
  - No post-result window changes.
  - Review requirement.

### C. Execution Realism Prerequisites

Before any paper-candidate implementation, specify:

- Slippage model.
- Spread/liquidity assumptions.
- Fees and funding assumptions.
- Expected turnover/trade frequency.
- Max adverse excursion / drawdown constraints.
- Position sizing policy.
- Stop-loss / exit-risk policy must be defined explicitly in the
  paper-candidate design lock. For volatility-targeted strategies, position
  sizing and exposure controls are primary risk controls unless a separate
  stop policy is explicitly approved.
- Rejection criteria if expected edge is below cost/slippage/funding floor.

### D. Runtime Architecture Prerequisites

Required boundaries:

- Research code must not call exchange write endpoints.
- Paper environment must be isolated.
- Deterministic signal export contract required.
- Risk remains authoritative for admissibility.
- Kill Switch remains highest authority.
- `execution_service` remains non-live unless separately authorized.
- Journal/audit trail required.
- Fail-closed policy required for unavailable upstream services.

### E. Safety and Operations Prerequisites

Required policies:

- Idempotency for candidate/review/order-like actions.
- Timeout policy between services.
- Kill-switch unavailable behavior.
- Monitoring/alerting requirements.
- Operator approval rules if applicable.
- No private API or exchange operation without separate protected-lane design.

### F. Review Prerequisites

- Independent review required before any paper-candidate design.
- Owner explicit approval required before any paper implementation design.
- No automatic promotion from research PASS_CANDIDATE to paper candidate.
- Any readiness claim must cite exact evidence and commit.

## Decision Gate Before Any New Diagnostic

Before any new diagnostic stage, require:

- Question answered.
- Decision unlocked.
- Action if HIGH.
- Action if LOW.
- Action if INCONCLUSIVE.

If all outcomes lead to the same action, do not run the diagnostic; move it to
watchlist.

## Weakest-Link Rule

New slices must target the weakest link in the evidence chain, not the most
interesting caveat.

Gap > caveat.

If a slice only explains a caveat but does not change the next decision, defer
it.

## Proposed Next Decision

- This proposal should be independently reviewed.
- If accepted, next step is not paper implementation.
- Next step would be a separate paper-candidate design-lock decision, only if
  the owner explicitly chooses to continue.
- That later design lock must address data-recency, execution realism, runtime
  safety, and review prerequisites.

## What This Proposal Does Not Authorize

- Paper trading.
- Live trading.
- Runtime wiring.
- Private API.
- Exchange operations.
- Order_status.
- Orders.
- Cancels.
- Set_leverage.
- Probes.
- Strategy filters.
- Parameter optimization.
- Readiness claims.
