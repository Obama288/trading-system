# Service Ownership Map

## Status

| Field | Value |
|---|---|
| Status | DRAFT |
| Applies to | Stage 54+ |
| Current implementation impact | NONE |
| Live trading impact | NONE |

---

## Core Principle

> One state type must have exactly one authoritative owner.
> Other services may read, subscribe, or derive, but must not directly mutate another service's owned state.

---

## Durable vs Ephemeral State

| Layer | Role | Authoritative? |
|---|---|---|
| PostgreSQL | Durable source of truth for all trading state | YES |
| Redis | Optional cache / pub-sub / heartbeat / ephemeral runtime data | NO |
| In-memory state | Local optimization only (config cache, instrument rules TTL) | NO |
| Exchange state | External source — trusted only after reconcile confirms; internal DB wins in any conflict | NO |

Redis must never be used as the source of truth for execution state, candidate status, kill-switch state, position state, or operator decisions. Any mismatch between Redis and DB must default to DB.

In-memory state is never authoritative. It resets on restart and must not be relied on for trading decisions.

Exchange state requires reconciliation logic before it can influence internal state. The internal DB state is the system of record.

---

## Ownership Table

| State type | Authoritative owner | Durable store | Allowed readers | Notes |
|---|---|---|---|---|
| Orders | execution_service | executions table | position_manager, dashboard_service, journal_ingest | Only execution_service writes order and execution status |
| Executions | execution_service | executions table | position_manager, dashboard_service, journal_ingest | exchange_order_id, fill price, filled qty written here after exchange confirmation |
| Positions | position_manager | positions table | risk_engine, dashboard_service, journal_ingest | Only position_manager writes position state |
| Risk approvals | risk_engine | trade_candidates (risk fields) | review_gateway, orchestrator | review_gateway must not recompute risk |
| Exposure calculations | risk_engine | Computed from positions + executions + config | orchestrator, dashboard_service | Derived at evaluation time; not stored as a separate authoritative row |
| Kill-switch state | kill_switch | system_state table | All money-path services | Fail-closed for all 4 error classes; checked before every execution boundary |
| Incidents | incidents | incidents table | dashboard_service, operators | Created on reconcile mismatch, orphan detection, or manual trigger |
| Journal events | journal_ingest | journal_events table | dashboard_service, journal_review, operators | Append-only audit log; must not become authority for trading decisions |
| Operator decisions | review_gateway / orchestrator | operator_actions table | journal_ingest, dashboard_service | Every approve/reject must write to operator_actions atomically |
| Market snapshots | market_data / exchange adapter | Ephemeral (cache or in-memory) | risk_engine, position_manager reconcile | Not durable; reconcile uses latest available snapshot |
| Instrument rules | Exchange adapter / market_data layer | In-memory cache with TTL | execution_service | Cached at startup; TTL 1 hour; stale rules acceptable, absent rules not |
| Signal decisions | signal_engine | Not persisted (advisory only) | risk_engine (as input) | Signal confidence is advisory; cannot directly approve or block a trade |
| Reconcile results | position_manager | position_events table + incidents | dashboard_service, journal_ingest | Mismatch must create an incident; position_manager owns reconcile outcome |
| Service health | Each service (self-reported) | Ephemeral (/health, /ready endpoints) | dashboard_service (aggregates) | Each service owns its own health state |
| Business metrics | dashboard_service (derived) | None (computed on read) | Operators, analytics | Derived from positions + executions; does not own trading state |

---

## Rules

1. execution_service owns exchange intent and order lifecycle.
2. position_manager owns internal position lifecycle and DB state.
3. risk_engine owns admission decisions — not orchestrator.
4. orchestrator coordinates workflow but must not bypass risk, review, kill_switch, or execution_service ownership.
5. kill_switch has top authority over all trading operations.
6. Dashboard aggregates and must not mutate trading state.
7. Journal records facts and must not become trading authority.
8. Publishing an event must not replace durable DB writes by the owning service. The DB write comes first.
