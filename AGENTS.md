# Hephaestus Agent Startup Guide

Status: ACTIVE / STARTUP POINTER

This file intentionally contains no dated project snapshot. Volatile facts have
one canonical home.

## Required Startup Order

1. Read `docs/CURRENT_STATE.md` for objective, owner constraints, current gate,
   readiness, blockers, and allowed next work.
2. Read `docs/BOUNDARIES.md` for hard safety constraints.
3. Run the Git sync gate from `docs/HOW_WE_WORK.md`.
4. For research tasks, read
   `research/signal_observation/RESEARCH_STATE.md` and
   `docs/RESEARCH_CONSTITUTION.md`.
5. Read only the design/decision files required by the task.

If docs, code, Git, tests, or owner instruction conflict, report the conflict
before editing. Code is authoritative for implemented behavior; STATE is
authoritative for the current gate; LAW is authoritative for constraints.

## Non-Negotiable Rules

- Paper-only and live NO-GO remain in force until the Human Owner explicitly
  changes them in project state.
- Do not call private exchange endpoints or place/cancel orders.
- Do not expose secrets, account identifiers, balances, signed payloads, or
  secret-derived values.
- Do not change runtime wiring, deployment, migrations, authority boundaries,
  risk, kill switch, execution, or position behavior without Protected Lane
  authorization.
- Do not promote docs/code/test/runtime/trading readiness by inference.
- Preserve unrelated dirty and untracked owner files.
- Use `python -m pytest`, `python -m alembic`, and `python -m uvicorn`.
- Use process-scoped environment variables only.

## Project Memory

Follow `docs/MEMORY_POLICY.md`. Chat memory and local untracked files are not
project facts. Significant state changes update the relevant compact STATE file
and pass:

```powershell
python -m pytest tests\test_project_memory.py -q
```

## Required Report

Every report includes: Agent, Task Type, Scope, Lane, Changed Files, Commands
Run with exact results, Readiness Claims separated by docs/code/test/runtime,
Not Verified, and Decision Needed.
