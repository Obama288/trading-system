# Project Origin

## Source Status

This file is historical navigation only.
It is not the project source of truth.
For current project state, read `docs/PROGRESS.md` first.
If this file conflicts with `docs/PROGRESS.md`, `docs/PROGRESS.md` wins.

Early-stage details are partially reconstructed from repo docs and git history.
Where exact early stage details are missing, they are not invented here.

## Original Goal

Hephaestus began as a trading-system project intended to turn market signals into
a controlled paper-trading pipeline before any live trading path could be
considered.

The original system intent was not "an AI trader." The core intent was a
deterministic trading system with explicit service ownership, audit trails,
manual approval gates, and safety controls around every money-path action.

## Initial Trading-System Direction

The documented money path is:

`signal_engine -> risk_engine -> review_gateway -> orchestrator -> execution_service -> position_manager`

The early architecture separated these responsibilities:
- signal generation proposes candidates;
- risk decides admissibility;
- review does not recompute authoritative risk;
- orchestrator coordinates operator approval and downstream calls;
- execution_service owns execution state;
- position_manager owns internal position state;
- journal/operator records preserve audit memory;
- kill_switch can stop the path.

This direction appears throughout the architecture and source-of-truth docs.
Details for exact stages before Stage 43 are not fully reconstructed from repo
docs, so this file uses stage groups rather than invented early stage numbers.

## Why Deterministic Money-Path Matters

The project repeatedly documents that execution-relevant state must come from
authoritative systems, not advisory memory or downstream inference.

Important examples:
- risk admissibility belongs to risk_engine;
- kill state belongs to system_state / kill_switch;
- execution state belongs to executions;
- position state belongs to positions;
- audit belongs to operator_actions and journal_events;
- statistics truth comes from positions and executions.

This deterministic boundary exists because a trading system can fail dangerously
when state is inferred twice, recomputed in the wrong service, silently cached, or
allowed to drift between DB, journal, exchange, and runtime services.

## Why The Main Boundaries Exist

Kill Switch:
The kill switch is the top safety authority. It must fail closed for known error
classes and can halt execution before capital is put at risk.

Risk Engine:
Risk is the source of truth for trade admissibility. Downstream services are not
allowed to override risk decisions or recompute core risk values.

Review:
Review is a gate and enrichment layer. It does not become risk authority and does
not silently approve trades.

Orchestrator:
The orchestrator coordinates the workflow and operator actions, but it must not
bypass risk, review, or kill switch boundaries.

Execution Service:
Execution service owns execution lifecycle state. Any future live path must keep
exchange interaction and execution state ownership explicit.

Position Manager:
Position manager owns internal position state. It should not become an exchange
order sender unless a future source-of-truth decision explicitly changes the
architecture.

Journal and Operator Actions:
Journal is audit memory, not trading authority. Operator actions preserve human
approval/rejection evidence.

## Why Live Trading Remains Gated

Repo docs record a validated paper contour and paper runtime proof, but also
record that live trading remains gated.

The live-path audit found that the paper pipeline existed while the live exchange
layer did not exist. Later Stage 53 design documents expanded this into a live
blocker taxonomy and exchange-readiness plan.

Live trading is gated because the system must prove, before any live action:
- authenticated exchange behavior is correct;
- orders, cancels, status polling, fills, and partial fills are handled safely;
- account equity and instrument rules are authoritative;
- reconcile uses real exchange state safely;
- kill switch, risk, execution, position, and journal boundaries hold under
  failure;
- human approval and final GO/NO-GO authority remain intact.

Nothing in this historical document changes that gate.

## Major Early Corrections

The repo history and progress docs record several important corrections:
- journal gaps were tightened so candidate creation and audit memory could be
  atomic where required;
- retry/idempotency behavior was hardened around signal_id and execution flow;
- blocking HTTP calls in async money-path contexts were removed or tracked;
- DB startup health checks were added to services;
- max_open_positions enforcement moved toward an authoritative DB-backed cap;
- paper runtime market-data coupling was corrected by moving runtime fetcher code
  out of research;
- paper contour validation exposed non-blocking issues around close_price and
  position close contracts;
- Q1 cleanup addressed recovered-position payload validation, freshness datetime
  handling, and true EMA behavior;
- exchange readiness was separated from signal-quality work.

These corrections shaped the current rule: evidence before status, and no status
promotion from unaccepted or unverified work.

## Evolution Into The Current Process

Hephaestus evolved from a paper-trading pipeline into a stage-gated engineering
process with explicit lanes:
- Fast Lane for docs and report-only work;
- Standard Lane for focused implementation and compact QA;
- Protected Lane for live/probe readiness, private exchange work, secrets,
  runtime wiring, infra, schema, dependencies, and safety boundaries.

Current process rules also formalize agent roles:
- Human Owner has final authority;
- Tower Control Architect coordinates context and gate discipline;
- Codex executes scoped repo work;
- Claude reviews architecture and source-of-truth drift.

The project now keeps exchange-readiness work, Bitget/Bybit private-preflight
planning, and signal-quality research as separate tracks. That separation is an
important historical outcome of the early corrections: advisory research and
execution authority must not collapse into one path.

