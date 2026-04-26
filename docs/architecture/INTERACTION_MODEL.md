# Interaction Model

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

## Three Types of Interaction

### Commands
A request to do something. Can be rejected.
Examples: ApproveTrade, SubmitOrder, CancelOrder, ClosePosition, EnterSafeMode

### Queries
Read-only state access. Must not change state.
Examples: GetOpenPositions, GetExposure, GetKillSwitchState, GetOrderStatus

### Events
A fact that already happened. Cannot be rejected.
Examples: RiskApproved, OrderSubmitted, OrderFilled, PositionOpened, KillSwitchActivated

---

## Rules

- Never mix commands and events.
- Queries must have no side effects.
- Events are immutable facts — write to journal.
- Commands route through authority owners only.
- Commands are not events. `SubmitOrder` is a command; `OrderSubmitted` is an event.
- Events must not replace durable DB writes by the owning service. The DB write comes first; the event is derived from the committed fact.
- Consumers must tolerate duplicate events.
- Consumers must not assume total global ordering unless explicitly guaranteed by the transport.

---

## Current Pipeline (Stage 53 — must not change)

```
signal -> risk_engine -> review_gateway -> orchestrator -> execution_service -> position_manager
```

This order is an invariant. No Stage 53 work may alter it.

Stage 53-A scope: Bybit public market data only. No pipeline changes. No execution path changes. No schema migrations.

---

## Non-Goals

- No Event Bus implementation in this stage.
- No Redis Pub/Sub implementation in this stage.
- No schema migration in this stage.
- No service behavior change in this stage.
- No live execution.
- No exchange authentication.
- No automatic order placement.

---

## Event Bus Prerequisites

Event Bus must not be implemented until all of the following are satisfied:

1. State ownership table accepted (see SERVICE_OWNERSHIP.md).
2. Event envelope schema accepted: event_id, correlation_id, timestamp_utc, source_service, schema_version, payload.
3. Idempotency strategy accepted (event_id deduplication at consumer or DB unique constraint).
4. Retry and dead-letter policy accepted (max retries, backoff, DLQ destination, alert on DLQ depth).
5. Failure behavior defined per consumer (fail-closed vs fail-soft; which failures trigger incidents).
6. Tests exist for all event consumers: normal path, duplicate event, out-of-order event, malformed payload.
7. No event consumer can bypass risk_engine, review_gateway, kill_switch, or execution_service ownership.

---

## Stage 54+ Plan

Stage 54-A: Formalize interaction model in code
Stage 54-B: Event envelope with correlation_id/causation_id
Stage 54-C: Event store mapping to journal
Stage 54-D: Event bus MVP
