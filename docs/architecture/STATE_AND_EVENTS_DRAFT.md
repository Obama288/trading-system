# State Ownership and Domain Events Draft

## Status

| Field | Value |
|---|---|
| Status | DRAFT |
| Applies to | Stage 54+ |
| Current implementation impact | NONE |
| Live trading impact | NONE |
| Event Bus implementation | NOT STARTED |
| Redis Pub/Sub implementation | NOT STARTED |

---

## Scope

This document is architectural planning only.

It does not change the current paper runtime.
It does not enable live trading.
It does not authorize any service to bypass risk, review, kill_switch, or execution ownership.
It does not modify the trading pipeline, service behavior, or any runtime code.

All decisions recorded here require a separate explicit implementation decision before any code changes begin.

---

## Core Principle

> One state type must have exactly one authoritative owner.
> Other services may read, subscribe, or derive, but must not directly mutate another service's owned state.

---

## Durable vs Ephemeral State

| Layer | Role | Authoritative? |
|---|---|---|
| PostgreSQL | Durable source of truth for all trading state | YES — all authoritative reads and writes |
| Redis | Optional cache / pub-sub / heartbeat / ephemeral runtime data | NO — never authoritative for trading decisions |
| In-memory state | Local optimization only (e.g. instrument rule cache, config) | NO — never authoritative |
| Exchange state | External source requiring reconciliation | NO — trusted only after reconcile logic confirms; internal DB state wins in any conflict |

Redis must never be used as the source of truth for:
- execution state
- candidate status
- kill-switch state
- position state
- operator decisions

Any mismatch between Redis and DB must default to the DB.

---

## State Ownership Table

| State type | Authoritative owner | Durable store | Allowed readers | Notes |
|---|---|---|---|---|
| Orders | `execution_service` | `executions` table | `position_manager`, `dashboard_service`, `journal_ingest` | Only `execution_service` writes order and execution status |
| Executions | `execution_service` | `executions` table | `position_manager`, `dashboard_service`, `journal_ingest` | `exchange_order_id`, fill price, filled qty written here after exchange confirmation |
| Positions | `position_manager` | `positions` table | `dashboard_service`, `risk_engine`, `journal_ingest` | Only `position_manager` writes position state; no other service may |
| Risk approvals | `risk_engine` | `trade_candidates` (risk fields) | `review_gateway`, `orchestrator` | `review_gateway` must not recompute risk; reads only |
| Exposure calculations | `risk_engine` | Computed from `positions` + `executions` + config | `orchestrator`, `dashboard_service` | Derived at evaluation time; not stored as a separate authoritative row |
| Kill-switch state | `kill_switch` | `system_state` table | All services on the money path | Checked before every execution boundary; fail-closed for all 4 error classes |
| Incidents | `incidents` | `incidents` table | `dashboard_service`, `journal_ingest` | Created on reconcile mismatch, orphan detection, or manual trigger |
| Journal events | `journal_ingest` | `journal_events` table | `dashboard_service`, operators, analytics | Append-only audit log; must not become authority for trading decisions |
| Operator decisions | `orchestrator` / `review_gateway` | `operator_actions` table | `journal_ingest`, `dashboard_service` | Every approve/reject must write to `operator_actions` atomically |
| Market snapshots | `market_data` / exchange adapter (when implemented) | Ephemeral (Redis cache or in-memory) | `risk_engine`, `position_manager` reconcile | Not durable; reconcile uses latest available snapshot |
| Instrument rules | Exchange adapter / market_data layer | In-memory cache with TTL | `execution_service` | Cached at startup; TTL 1 hour; stale rules acceptable, absent rules not |
| Signal decisions | `signal_engine` | Not persisted (advisory only) | `risk_engine` (as input) | Signal confidence is advisory; cannot directly approve or block a trade |
| Reconcile results | `position_manager` | `position_events` table + incidents | `dashboard_service`, `journal_ingest` | Mismatch must create an incident; position_manager owns reconcile outcome |
| Service health | Each service (self-reported) | Ephemeral (`/health`, `/ready` endpoints) | `dashboard_service` (aggregates) | Each service owns its own health; dashboard aggregates but does not mutate |
| Business metrics | `dashboard_service` (derived) | None (computed on read) | Operators, analytics | Derives from `positions` + `executions`; does not own trading state |

---

## Planned Domain Events

Events are immutable facts. They describe something that already happened. They are not commands.

### Signal

| Event | Description |
|---|---|
| `SignalCreated` | Signal engine produced a new signal |
| `SignalRejected` | Signal failed pre-risk filter or freshness check |
| `SignalExpired` | Signal TTL elapsed before a candidate was created |

### Risk

| Event | Description |
|---|---|
| `RiskApproved` | Risk engine approved a candidate for review |
| `RiskRejected` | Risk engine rejected the candidate |
| `ExposureChanged` | Aggregate exposure updated after position open/close |

### Review

| Event | Description |
|---|---|
| `ReviewApproved` | Operator approved the candidate via review gateway |
| `ReviewRejected` | Operator rejected the candidate |
| `OperatorOverrideRequested` | Operator requested a manual override outside normal flow |

### Execution

| Event | Description |
|---|---|
| `OrderSubmitRequested` | Execution service received a request to place an order |
| `OrderSubmitted` | Order request sent to exchange |
| `OrderAccepted` | Exchange acknowledged the order (`New` status) |
| `OrderRejected` | Exchange rejected the order |
| `OrderCancelled` | Order cancelled — by system or operator |
| `OrderCancelFailed` | Cancel request sent but exchange did not confirm |
| `OrderPartiallyFilled` | Exchange returned partial fill — triggers halt in first live phase |
| `OrderFilled` | Order fully filled; position open may proceed |
| `OrderStatusUnknown` | Poll timed out; status could not be determined — triggers halt |

### Position

| Event | Description |
|---|---|
| `PositionOpened` | Position row created after fill confirmed |
| `PositionUpdated` | Position fields updated (e.g. stop-loss, take-profit adjustment) |
| `PositionCloseRequested` | Close intent recorded (by reconcile, operator, or TTL) |
| `PositionCloseFailed` | Close order sent but not confirmed |
| `PositionClosed` | Position row marked closed after fill confirmed |

### Reconcile

| Event | Description |
|---|---|
| `ReconcileStarted` | Reconcile cycle began |
| `ReconcileMatched` | Internal position matches exchange snapshot |
| `ReconcileMismatch` | Internal position does not match exchange snapshot — incident created |
| `ReconcileFailed` | Reconcile could not complete (exchange unreachable, DB error) |

### Kill Switch / Safety

| Event | Description |
|---|---|
| `KillSwitchActivated` | Kill switch set to active; trading blocked |
| `KillSwitchDeactivated` | Kill switch cleared; trading re-enabled |
| `SafeModeEntered` | Service entered safe mode due to kill_switch unreachability |
| `SafeModeExited` | Safe mode cleared after kill_switch confirmed reachable |
| `CircuitBreakerOpened` | Circuit breaker triggered (rate limit, error threshold) |
| `CircuitBreakerClosed` | Circuit breaker reset |

### Incident

| Event | Description |
|---|---|
| `IncidentCreated` | New incident opened (orphan, mismatch, auth failure, etc.) |
| `IncidentResolved` | Incident closed by operator |

### Journal

| Event | Description |
|---|---|
| `JournalEventRecorded` | A journal event was durably written to `journal_events` |

---

## Event Rules

1. Events are immutable. Once written, an event must not be modified or deleted.
2. Events describe facts that already happened. They are not commands or intentions.
3. Commands are not events. `PlaceOrder` is a command; `OrderSubmitted` is an event.
4. Every event must include `correlation_id` — propagated from the originating request.
5. Every event must include `event_id` — globally unique identifier for deduplication.
6. Every event must include `timestamp_utc` — time the fact occurred, not time of publish.
7. Every event must include `source_service` — which service produced the event.
8. Every event must include `schema_version` — for forward-compatible consumers.
9. Events must not contain secrets, tokens, credentials, or raw API keys.
10. Events should be idempotent or safely deduplicated. Consumers must tolerate receiving the same event more than once.
11. Consumers must not assume total global ordering unless the transport explicitly guarantees it.
12. Publishing an event must not replace durable DB writes by the owning service. The DB write comes first; the event is derived from the committed fact.

---

## Feedback Loop Boundaries

- **Execution → Signal:** Execution feedback (fill quality, slippage, win/loss) may influence future signals via derived metrics, cooldowns, and quality gates. This path is advisory only.
- **Signal engine** must not own orders, executions, or positions. Signal outputs are inputs to the risk engine, nothing more.
- **Risk engine** may read `positions` and `executions` to compute current exposure. It must not write to those tables.
- **Position manager** owns all position state. No other service may write to the `positions` table. Reconcile is a position_manager responsibility.
- **Dashboard** may aggregate trading state for display. It must not mutate trading state or be used as a source of truth for any trading decision.
- **Journal** records facts. It must not become an authority for trading decisions. Journal failure must not roll back an authoritative DB write.

---

## Kill-Switch and Safe Mode

- Loss of connection to `kill_switch` must result in safe mode for any service capable of initiating or forwarding trading actions.
- `execution_service` must reject new live orders when `kill_switch` is unreachable (fail-closed; current behavior confirmed for all 4 error classes: `AUTH_FAILURE`, `KILL_SWITCH_TIMEOUT`, `KILL_SWITCH_UNAVAILABLE`, `KILL_SWITCH_ERROR`).
- `orchestrator` must stop forwarding trade requests when risk, review, or kill_switch availability is unknown.
- `risk_engine` must reject approvals when exposure state is stale or unavailable.
- `position_manager` must create an incident on any reconcile mismatch between internal state and exchange snapshot.
- Partial fills in the first live phase must result in HALT + manual operator review. Automatic partial fill recovery is not permitted until Stage 53-G or later.

---

## Event Bus Prerequisites

Event Bus must not be implemented until all of the following are satisfied:

1. State ownership table has been accepted by the owner (this document or a successor).
2. Event envelope schema is defined and accepted (fields: `event_id`, `correlation_id`, `timestamp_utc`, `source_service`, `schema_version`, `payload`).
3. Event naming convention is accepted (past-tense noun phrases, e.g. `OrderFilled`, not `order.filled` or `fill_event`).
4. Idempotency strategy is defined (event_id deduplication at consumer, or DB unique constraint on event_id).
5. Retry and dead-letter policy is defined (max retries, backoff, DLQ destination, alert on DLQ depth).
6. Failure behavior is defined for each consumer (fail-closed vs fail-soft; which failures trigger incidents).
7. Tests exist for all event consumers covering: normal path, duplicate event, out-of-order event, malformed payload.
8. No event consumer can bypass `risk_engine`, `review_gateway`, `kill_switch`, or `execution_service` ownership. Event-driven paths must enforce the same authority rules as HTTP paths.

---

## Business Observability Prerequisites

Business observability must be derived from:
- DB state (`positions`, `executions`, `trade_candidates`, `operator_actions`, `journal_events`)
- Immutable domain events (when Event Bus is implemented)
- Exchange reconcile results (after Stage 53-D)

It must not be derived from:
- In-memory counters that reset on restart
- Redis values without a DB fallback
- Signal engine output or research hypotheses

### Planned metrics

| Metric | Source |
|---|---|
| `signal_to_review_latency_ms` | `journal_events` timestamps: `candidate_created` → `review_result` |
| `review_to_execution_latency_ms` | `journal_events`: `candidate_approved` → `execution_started` |
| `execution_slippage_bps` | `executions.exchange_avg_fill_price` vs `executions.entry_price` |
| `order_reject_rate` | `executions` status counts: `failed` / total |
| `order_status_unknown_count` | `executions` with status `placement_timeout` or `poll_failure` |
| `partial_fill_count` | `executions` with status `partially_filled` |
| `reconcile_mismatch_count` | `incidents` with type `reconcile_mismatch` |
| `exposure_by_symbol` | `positions` open rows: sum of `entry_price * quantity` per symbol |
| `open_positions_count` | `positions` where `status = 'open'` |
| `daily_realized_pnl` | `positions` closed today: LONG `(close_price - entry_price) * quantity`; SHORT `(entry_price - close_price) * quantity` |
| `win_rate_by_strategy` | `positions` closed: winning trades / total per strategy tag |
| `loss_streak_by_symbol` | `positions` closed: consecutive losing trades per symbol |
| `trades_blocked_by_risk` | `trade_candidates` with `status = 'rejected'` and risk_rejection reason |
| `trades_blocked_by_kill_switch` | `journal_events` with type `kill_switch_blocked` or `kill_switch_check_failed` |
| `safe_mode_entries` | `journal_events` with type `safe_mode_entered` (once implemented) |

---

## Non-Goals

The following are explicitly out of scope for this document and for any stage it applies to:

- No Event Bus implementation.
- No Redis Pub/Sub implementation.
- No schema migration.
- No service behavior change.
- No live execution.
- No exchange authentication.
- No automatic order placement.
- No modification of the trading pipeline or authority rules.

---

## Verification

After creating this file, verify:

```bash
git status --short
cat docs/architecture/STATE_AND_EVENTS_DRAFT.md
```

Expected:
- File appears as untracked (`??`) in git status.
- Document contains no secrets, tokens, or credentials.
- No runtime files changed.
