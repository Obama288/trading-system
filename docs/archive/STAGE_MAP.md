# Stage Map

> **Status: ARCHIVED** — Retained for historical context only. Not authoritative for current state, gates, readiness, or next actions. Current state entry point: `docs/CURRENT_STATE.md`.

## Source Status

This file is navigation only.
It is not the current project source of truth.
For current project state and gate decisions, read `docs/PROGRESS.md` first.
If this file conflicts with `docs/PROGRESS.md`, `docs/PROGRESS.md` wins.

Early-stage details before the documented Stage 43+ map are partially
reconstructed from repo docs and git history. Details are not fully
reconstructed from repo docs, so early work is grouped rather than assigned
invented stage numbers.

## Current Source-Of-Truth Snapshot

Current gate per `docs/PROGRESS.md`:
- Stage 54-BG2-C private read-only preflight runbook active.
- Stage 54-SQ is a separate active parallel research-only signal-quality
  observation track.
- Bybit Stage 53-B2c.1c/B2d private real testnet path remains blocked because
  usable Bybit testnet API access is unavailable.
- Live trading remains NO-GO.

This file does not change readiness, stage status, or authorization.

## Historical Stage Groups

Stage Group A - Architecture foundation:
Money-path design, authority rules, service boundaries, deterministic control,
and advisory-only LLM/research boundaries.

Stage Group B - Paper trading core:
Signal, risk, review, orchestrator, paper execution, position manager, and
journal/audit flow.

Stage Group C - Safety and authority hardening:
Kill-switch authority, DB source-of-truth rules, operator actions, idempotency,
max_open_positions guard, fail-closed behavior, token discipline, and journal
integrity.

Stage Group D - Paper runtime validation:
Local paper runtime, VPS paper runtime, 9 services healthy, execution-service
paper mode, and paper contour validation.

Stage Group E - Quality and regression cleanup:
Q1 audit backlog, recover_position payload validation, freshness datetime
handling, true EMA, regression baselines, and docs/status cleanup.

Stage Group F - Exchange-readiness preparation:
Stage 53 design lock, Bybit public adapter, authenticated read-only planning,
testnet smoke harnesses, and the blocked Bybit private real testnet path.

## Official Stage 43+ Map

The following Stage 43+ labels are documented in repo docs:

- Stage 43 - Dashboards MVP
- Stage 44 - Operator audit hardening
- Stage 45 - Approve -> execution rollback (MVP)
- Stage 46 - Kill switch enforcement in orchestrator
- Stage 47 - Execution store DB migration
- Stage 48 - End-to-end pipeline tests
- Stage 49 - Observability
- Stage 50 - Statistics MVP
- Stage 51 - Statistics breakdown
- Stage 52 - Paper trading validation
- Stage 53 - Real exchange integration
- Stage 54 - Reconciliation layer / later Bitget and signal-quality tracks
- Stage 55 - Advanced observability / later portfolio-control concepts

Exact internal details for every stage in this list are not fully reconstructed
in this navigation file. Use the named stage docs and `docs/PROGRESS.md` for
accepted evidence.

## Architecture Hardening And Runtime Proof

Closed or recorded areas:
- security fixes S-1 through S-9;
- TD-12 journal atomicity;
- TD-13 retry-safe candidate creation;
- TD-14 async HTTP money-path cleanup;
- TD-16 DB startup health checks;
- TD-18 market-data fetcher coupling cleanup;
- TD-19 max_open_positions authority hardening;
- TD-20 approve/reject DB-atomic journaling;
- LH-1 local and VPS paper runtime proof.

Boundaries preserved:
- kill switch remains top safety authority;
- risk remains admissibility authority;
- execution_service owns execution state;
- position_manager owns internal position state;
- journal is audit, not trading authority;
- research and LLM outputs are advisory only.

## Exchange And Preflight Track

Closed / accepted:
- Stage 53-A Bybit public market data adapter.
- Stage 53-B design lock.
- Stage 53-B owner decisions.
- Stage 53-B1 config-only Bybit settings.
- Stage 53-B1 Slice 1 server-time skeleton.
- Stage 53-B1 Slice 2 wallet_balance read-only skeleton.
- Stage 53-B1 Slice 3 open_positions read-only skeleton.
- Stage 53-B2a server_time smoke harness.
- Stage 53-B2b real server_time smoke, owner-run, server_time only.
- Stage 53-B2c wallet_balance smoke harness, mocked tests only.
- Stage 53-B2c.1a authenticated-readiness hardening.
- Stage 53-B2c.1b query-api read-only preflight harness.

Blocked:
- Stage 53-B2c.1c real query-api retry.
- Stage 53-B2d real wallet_balance testnet smoke.
- Bybit private real testnet path while usable testnet API access is unavailable.

Planned / active docs:
- Stage 54-BG1 config-only Bitget settings closed.
- Stage 54-BG2 design lock recorded.
- Stage 54-BG2-A public-only skeleton accepted.
- Stage 54-BG2-B signing helper accepted.
- Stage 54-BG2-C private read-only preflight runbook active as planning only.

Not authorized by this map:
- private smoke;
- real wallet/balance/positions smoke;
- order_status;
- place_order;
- cancel_order;
- set_leverage;
- withdraw;
- transfer;
- service/runtime wiring;
- live execution.

## Signal-Quality Research Track

Stage 54-SQ is documented as a separate parallel research-only observation track.
It does not replace, advance, or close the Stage 54-BG2-C gate.

Documents and implemented research slices visible in repo history:
- Stage 54-SQ proposal and observation-driven sprint document.
- Stage 54-SQ-A automated observation collector design.
- Stage 54-SQ-A models skeleton.
- CSV candle loader.
- indicator utilities.
- Setup A detector.
- outcome tracker.
- local fixture summary runner.
- local historical CSV summary runner.
- OKX public candle downloader for optional comparison.
- Bitget public OHLCV downloader for venue-aligned local CSV input.

Research boundaries:
- public/local data only unless separately authorized;
- no private API;
- no account data;
- no orders or cancels;
- no paper execution;
- no live trading;
- no runtime wiring;
- no claimed signal edge or profitability from this navigation map.

## Current Active, Closed, And Blocked Areas

Active:
- Stage 54-BG2-C docs-only/private-preflight planning.
- Stage 54-SQ parallel research-only signal observation track.

Closed / remote-visible:
- Paper contour validation.
- LH-1 paper runtime proof.
- Stage 53-A public Bybit adapter.
- Stage 53-B1/B2 mocked read-only slices listed above.
- Stage 54-BG1/BG2-A/BG2-B accepted checkpoints.
- Stage 54-SQ-A research implementation slices visible in git history.

Blocked / NO-GO:
- Bybit B2 private real testnet path without usable testnet API access.
- Mainnet read-only smoke unless separately authorized.
- Any private Bitget smoke unless separately authorized.
- Runtime/service wiring for exchange clients.
- Controlled live trading.

## How To Use This Map

Use this file to find the right document or stage family.
Use `docs/PROGRESS.md` to decide what is current, accepted, active, blocked, or
authorized.
Use git history only as supporting evidence when docs do not contain the exact
stage detail.

