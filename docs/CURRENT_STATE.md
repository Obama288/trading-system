# Hephaestus Current State

Status: ACTIVE / STATE

Evidence baseline: local audit on 2026-07-16 against
`402f342d95d6a9a4e39d629d0a22d620cd5cbd02`; `HEAD` matched `origin/main`
after `git fetch --prune origin`.

## Objective

Build a system capable of producing repeatable net trading profit after all
costs and operational risks. Research discipline, infrastructure, and paper
execution are means to that economic objective.

No strategy currently has sufficient current, held-out, cost-aware evidence to
claim a proven edge. This is the present evidence state, not a change of goal.

## Owner Constraints

- No new project spending: no paid data, paid APIs, subscriptions, or
  infrastructure upgrades without a new explicit owner decision.
- Correctness and reproducibility take priority over speed.
- Use free/local evidence paths while they remain methodologically valid.
- Do not trade real money to solve a short-term cash problem.

## Safety And Readiness

- Mode: paper only.
- Live trading: NO-GO.
- Exchange/private API readiness: not verified.
- Runtime readiness: not verified in this audit.
- Paper end-to-end readiness: not established.
- Trading profitability: not established.

No document, test pass, research verdict, or infrastructure harness may promote
paper, runtime, trading, probe, or live readiness by inference.

## Current Gates

- Project-control lane: memory and reproducibility cleanup.
- Exchange lane: Stage 54-BG / Bitget Demo remains planning only.
- Research lane: no active family.
- Setup I / Price-Flow Divergence Reversion: DRAFT / feasibility candidate
  only. No screening, analysis, validation, or paper progression is authorized.
- Setup C, Setup E, and Setup H: parked from active progression.

## Verified Repository Facts

- Local `main` and `origin/main` matched at `402f342` on 2026-07-16.
- GitHub CI succeeded at that commit, but the workflow runs only the research
  subset and is not a full project gate.
- The full tracked-tree test suite passes without the local root `conftest.py`.
- Protected risk-route tests now configure their own token for each test.
- Local CI configuration runs the full project suite on Python 3.12; remote CI
  confirmation is pending push.
- Deterministic in-process paper lifecycle passes through close and a new DB
  session; see `docs/VERIFICATION_BASELINE.md` for scope and accounting gaps.
- Ruff: 145 findings. Mypy for `apps libs ops`: 50 errors in 19 files.
- Local interpreter observed: Python 3.14.4. Canonical project/CI target remains
  Python 3.12 until deliberately changed.
- Alembic head in code: `0009_create_paper_account_authority`.
- Dependency consistency check: `python -m pip check` passed.

These are test/code facts only. They are not runtime or trading-readiness
claims.

## Architecture State

Nominal authority flow:

`signal_engine -> risk_engine -> review_gateway -> orchestrator -> execution_service -> position_manager`

The nine-service launcher does not provide autonomous signal/market-data/alert
services. `ops/paper_pipeline_runner.py` is an infrastructure harness and uses
caller-supplied paper account state; it is not the protected authoritative risk
path and not strategy evidence.

The protected risk HTTP route remains fail-closed because authoritative daily
PnL is not implemented. This is intentional safety behavior, not readiness.

## Quality-Critical Backlog

Before reliable paper progression:

1. Make the tracked repository test suite reproducible on Python 3.12 and make
   CI run the relevant core suites.
2. Resolve async-mock warnings and establish enforceable lint/type baselines.
3. Fix duplicate approval for `submitted` candidates and transaction ownership.
4. Require safe recovery data, preserve `signal_id`, and make reconcile absence
   fail closed without creating false closes.
5. Clarify multi-target take-profit behavior.
6. Remove cross-app production imports and reduce float use in money state.
7. Revisit protected risk/account authority only under explicit Protected Lane
   authorization.

## Allowed Next Work

- Docs/test-only project-memory normalization and integrity checks.
- Clean test/CI baseline work that does not alter runtime behavior.
- Classification of existing dirty and untracked files without deleting them.
- Focused paper-safety fixes only after separate scope approval.
- Setup I preregistration/feasibility planning only; no data inspection or
  screening until its research prerequisites and owner gate are explicit.

## Not Authorized

- Paid data or paid-plan upgrades.
- Private exchange calls, orders, cancels, leverage, transfers, or withdrawals.
- Service/runtime wiring, deployments, real smoke tests, or VPS changes.
- Paper/live readiness promotion.
- Rescue variants of parked research families without a new decision gate.

## Current Decision

First restore truthful project memory and a reproducible repository baseline.
Then decide between focused paper-safety hardening and one bounded, free-data
Setup I feasibility gate. Neither choice authorizes trading.

Detailed history remains in Git, accepted decision records, research result
artifacts, and `docs/archive/`.
