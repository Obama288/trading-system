# Verification Baseline

Status: ACTIVE / REFERENCE

Evidence date: 2026-07-16. This file records local verification facts; it does
not promote runtime, paper-economic, exchange, or live readiness.

## Environment

- Canonical Python target and GitHub Actions: Python 3.12.
- Local interpreter used for this baseline: Python 3.14.4.
- Alembic graph head: `0009_create_paper_account_authority`.
- No private exchange calls, paid services, or external runtime were used.

## Test Gate

- The tracked-tree suite is self-contained; no tracked root `conftest.py` is
  required.
- Full local tracked-tree result: `1111 passed` with no warnings.
- GitHub Actions is configured to install `.[dev,research]` and run the full
  project suite.
- Remote CI confirmation remains pending push.
- Deterministic lifecycle command:

```powershell
python -m pytest tests\integration\test_pipeline_e2e.py -q
```

The lifecycle test covers fixed market input, signal, risk, review, candidate
creation, operator approval, paper fill, position opening, take-profit closing,
journaling, and persistence across a new SQLAlchemy session. It makes no
network or exchange call.

## Static Baseline

`python -m ruff check . --statistics` reports 145 findings:

- 76 unused imports
- 32 f-strings without placeholders
- 19 unused variables
- 12 imports outside the module top level
- 4 ambiguous variable names
- 1 multiple import
- 1 undefined name

`python -m mypy apps libs ops` reports 50 errors in 19 files. Highest-risk
groups are orphan detection typing/await usage, risk input typing, nullable
execution and recovery payloads, and HTTP auth header types.

These findings are debt, not evidence that all affected paths are broken.
They prevent treating lint/type checks as release gates until reduced
deliberately.

## Economic Accounting Gap

The paper lifecycle stores entry price, close price, quantity, and close reason.
It does not persist authoritative:

- entry and exit fees
- funding payments
- modeled slippage
- gross realized PnL
- net realized PnL
- paper equity movement derived from closed trades

Therefore the lifecycle verifies state plumbing only. It cannot validate
strategy profitability or paper-economic correctness.

Adding authoritative accounting fields or tables requires a separate Protected
Lane decision covering schema, migration, ownership, reconciliation, and
backfill behavior.

## Next Engineering Order

1. Keep the full pytest suite green on Python 3.12.
2. Fix high-risk mypy findings in execution, recovery, risk, and auth clients.
3. Reduce Ruff findings by mechanical category without behavior changes.
4. Design paper accounting authority before any schema or migration work.
