# Q-1 Code Audit Backlog

Status: OPEN
Current mode: paper trading only
Live trading: NO-GO
Stage 53-B implementation: BLOCKED until owner decisions OI-1..OI-9 are answered
Source: Q-1 QA validation report, 2026-04-26
Scope: backlog only, no runtime implementation

## Rules

- This file tracks validated findings only.
- Do not use this file to enable live trading.
- Do not store secrets, API keys, account UID, email, balances, or signed payloads.
- Do not start Stage 53-B implementation from this backlog.
- Each code fix must be a separate isolated task with allowed files, tests, and review.
- Findings that touch money-path architecture require architect approval before code changes.

## Immediate isolated fix candidates

Q1-FIX-1:
- Finding: HIGH-5 recover_position silently defaults missing payload fields.
- Validated severity: High.
- Impact: paper-runtime data integrity bug.
- Recommended next handling: isolated Q-fix.
- Future allowed files:
  - apps/position_manager/application/recover_position.py
  - apps/position_manager/tests/test_recover_position.py
- Minimal tests:
  - missing symbol returns EXECUTION_PAYLOAD_INVALID and does not create position
  - missing quantity returns EXECUTION_PAYLOAD_INVALID and does not create position
  - missing entry_price returns EXECUTION_PAYLOAD_INVALID and does not create position

Q1-FIX-2:
- Finding: HIGH-8 freshness naive datetime can raise TypeError.
- Validated severity: Medium.
- Impact: paper-runtime crash on affected input.
- Recommended next handling: isolated Q-fix.
- Future allowed files:
  - apps/market_data/domain/freshness.py
  - apps/market_data/tests/test_freshness.py
- Minimal tests:
  - naive datetime input does not raise uncontrolled TypeError
  - stale/fresh behavior remains correct for timezone-aware timestamps

Q1-FIX-3:
- Finding: HIGH-1 EMA calculated as SMA.
- Validated severity: High.
- Impact: strategy correctness issue in paper signal quality.
- Recommended next handling: isolated Q-fix.
- Future allowed files:
  - apps/market_data/domain/snapshot_builder.py
  - apps/market_data/tests/test_snapshot_builder.py
- Minimal tests:
  - ema_20 is exponentially weighted
  - ema_50 is exponentially weighted
  - insufficient-data behavior remains unchanged

## Backlog findings not safe to fix immediately

Q1-BACKLOG-1:
- Finding: CRIT-3 approve_candidate commits approval before execution HTTP call.
- Validated severity: High.
- Status: real.
- Impact: paper stuck-state risk and pre-live blocker.
- Handling: architecture decision required before code changes.
- Notes: do not patch in isolation; likely needs outbox or approval/execution state-machine decision.

Q1-BACKLOG-2:
- Finding: HIGH-3 deterministic approve journal event_id can collide under concurrent approval.
- Validated severity: Medium.
- Status: real.
- Impact: concurrent paper edge case and pre-live concern.
- Handling: backlog, likely tied to Q1-BACKLOG-1.

Q1-BACKLOG-3:
- Finding: HIGH-4 DbJournalClient commits internally.
- Validated severity: Medium.
- Status: real.
- Impact: data integrity risk depending on caller transaction boundaries.
- Handling: backlog; requires call-site audit before changing commit to flush.

Q1-BACKLOG-4:
- Finding: CRIT-1 advisory lock/open-position admission concern.
- Validated severity: Low.
- Status: partial/latent.
- Impact: pre-live when DB-backed execution store is introduced.
- Handling: defer until DB-backed execution store / Stage 53-C+ planning.

Q1-BACKLOG-5:
- Finding: CRIT-2 sync orphan detector calls async methods without await.
- Validated severity: Low.
- Status: real dead-code bug.
- Impact: zero current production impact.
- Handling: backlog; remove sync variant or mark not for async detectors.

Q1-BACKLOG-6:
- Finding: CRIT-4 paper execution recorded filled without submitted state.
- Validated severity: Medium.
- Status: partial/by design for paper.
- Impact: pre-live blocker for live order lifecycle.
- Handling: defer to Stage 53-C live execution state machine.

Q1-BACKLOG-7:
- Finding: HIGH-2 advisory lock acquisition lacks structured error handling.
- Validated severity: Medium.
- Status: real.
- Impact: operational robustness.
- Handling: backlog.

Q1-BACKLOG-8:
- Finding: HIGH-6 paper runner bid=ask=last_price makes spread zero.
- Validated severity: Medium.
- Status: real/documented.
- Impact: paper-only strategy limitation; pre-live blocker B-12.
- Handling: track only; live runner must use real bid/ask.

Q1-BACKLOG-9:
- Finding: HIGH-7 reconcile_scheduler uses asyncio.run inside asyncio.to_thread.
- Validated severity: Medium.
- Status: real.
- Impact: shutdown/cancellation fragility.
- Handling: backlog; needs scheduler design review.

## False positives / no action

Q1-NOACT-1:
- Finding: CRIT-5 reconcile.py final list_open_positions stale identity-map concern.
- Validated severity: Not a bug.
- Status: false positive.
- Handling: no action.

## Recommended order

1. Q1-FIX-1 recover_position payload validation.
2. Q1-FIX-2 freshness naive datetime handling.
3. Q1-FIX-3 true EMA calculation.
4. Architecture decision for approve_candidate distributed transaction.
5. Backlog grooming for remaining items.
