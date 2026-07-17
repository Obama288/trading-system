# Hephaestus Current State

Status: ACTIVE / STATE

Evidence baseline: local and remote verification on 2026-07-17 through
`5b3907060a93ce98a8b3a3a2e14262dbc4591c5c`. Local `main` matched
`origin/main`; GitHub `Project Test Suite` run `29536915514` succeeded.

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
- Runtime and VPS readiness: not verified in this work.
- In-process paper lifecycle: verified as infrastructure plumbing.
- Paper-economic readiness: not established.
- Trading profitability: not established.

No document, test pass, research verdict, or infrastructure harness may promote
paper, runtime, trading, probe, or live readiness by inference.

## Current Gates

- Project-control lane: memory and reproducible test baseline completed.
- Research lane: no active family.
- H1 / Cross-Venue Perpetual Funding Dispersion: PARKED / DATA FEASIBILITY /
  NO OUTCOME INSPECTION.
- H1 Phase A historical coverage: Binance and Bybit PASS; Binance is ineligible
  because prior Setup D/F work inspected its funding outcomes. Bitget and OKX
  have insufficient coverage, so the required clean `Bitget + Bybit` pair is
  unavailable. Phase B is forbidden.
- H3 / Beta-Neutral Cross-Sectional Residual Reversion has a planning-only
  draft preregistration:
  `research/signal_observation/H3_BETA_NEUTRAL_RESIDUAL_REVERSION_PREREGISTRATION.md`.
  Active family remains none; H3 acquisition and analysis are not authorized.
- Setup I / Price-Flow Divergence Reversion: DRAFT / feasibility candidate only.
- Setup C, Setup E, and Setup H: parked from active progression.
- Exchange lane: Stage 54-BG / Bitget Demo remains planning only.

H1 Phase B, outcome inspection, pair substitution, and rescue acquisition are
forbidden. H3 is not authorized beyond preregistration work. No paper
progression or private exchange work is authorized.

## Verified Repository Facts

- Local and remote `main` matched at `5b39070` on 2026-07-17.
- GitHub `Project Test Suite` passed on Python 3.12: 1103 passed with one
  third-party FastAPI/Starlette deprecation warning.
- The test suite is self-contained; tracked tests do not require a root
  `conftest.py`.
- Protected risk-route tests configure their own token for each test.
- Deterministic in-process lifecycle covers fixed market input, signal, risk,
  review, candidate, approval, paper fill, position open, close, journaling,
  and persistence across a new SQLAlchemy session.
- The lifecycle does not account for fees, funding, slippage, or net realized
  PnL. It is plumbing evidence, not economic evidence.
- Ruff: 145 findings. Mypy for `apps libs ops`: 50 errors in 19 files.
- Local interpreter observed: Python 3.14.4. Canonical project/CI target remains
  Python 3.12 until deliberately changed.
- Alembic head in code: `0009_create_paper_account_authority`.
- Dependency consistency check: `python -m pip check` passed.

Detailed commands, counts, and limitations are in
`docs/VERIFICATION_BASELINE.md`.

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

1. Design authoritative paper accounting for fees, funding, slippage, gross/net
   realized PnL, and equity movement. Schema work requires explicit Protected
   Lane authorization.
2. Fix high-risk mypy findings in orphan detection, risk input typing, recovery,
   nullable execution payloads, and auth headers.
3. Fix duplicate approval for `submitted` candidates and transaction ownership.
4. Require safe recovery data, preserve `signal_id`, and make reconcile absence
   fail closed without creating false closes.
5. Clarify multi-target take-profit behavior.
6. Remove cross-app production imports and reduce float use in money state.
7. Reduce Ruff findings by mechanical category without behavior changes.

## Allowed Next Work

- Compare and preregister trading hypotheses using only existing knowledge and
  free-data feasibility criteria.
- Docs-only paper-accounting authority design.
- H3 preregistration review/lock planning without acquisition or analysis.
- Focused test, type, lint, and paper-safety work that does not cross Protected
  Lane boundaries.
- Classification of existing untracked files without deleting owner work.

## Not Authorized

- Paid data or paid-plan upgrades.
- Private exchange calls, orders, cancels, leverage, transfers, or withdrawals.
- Migrations, service/runtime wiring, deployments, real smoke tests, or VPS
  changes without explicit Protected Lane approval.
- Paper/live readiness promotion.
- Data screening or rescue variants of parked research families without a new
  decision gate.
- H1 Phase B, outcome inspection, or source/window rescue under the parked
  attempt.

## Current Decision

The H1 free-data feasibility attempt is parked before outcome inspection because
the locked clean venue pair is unavailable. H3 / Beta-Neutral Cross-Sectional
Residual Reversion is the recommended next preregistration candidate, but the
active family remains none and no H3 acquisition or analysis is authorized.

Authoritative paper accounting remains required before any claim about economic
paper performance. Neither research planning nor the green CI authorizes
trading.

Detailed history remains in Git, accepted decision records, research result
artifacts, and `docs/archive/`.
