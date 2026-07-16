# How We Work

Status: ACTIVE / PROCESS

This file defines the working protocol. Hard safety law lives in
`docs/BOUNDARIES.md`. Research law lives in `docs/RESEARCH_CONSTITUTION.md`.
Project-memory law lives in `docs/MEMORY_POLICY.md`.

## Objective Discipline

The project objective is repeatable net trading profit after costs and risk.
Engineering and research work must either reduce a real blocker to that goal or
be deferred.

Current owner constraints are read from `docs/CURRENT_STATE.md`. Do not replace
the economic objective with infrastructure completion, test count, or research
activity.

## Session Startup

Read in this order:

1. `docs/CURRENT_STATE.md`
2. `docs/BOUNDARIES.md`
3. recent Git commits and current working tree
4. `research/signal_observation/RESEARCH_STATE.md` for research work
5. the task-specific design/decision file
6. history only if current sources are missing, stale, or conflicting

Report conflicts before edits. Chat memory is orientation only.

## Pre-Edit Sync Gate

Run:

```powershell
git status --short --branch
git rev-parse HEAD
git log -1 --oneline
git diff --name-only
```

Classify dirty paths as current-task, pre-existing, generated, local-only, or
unknown. Unknown overlapping changes block edits. Unrelated owner files are
preserved.

## Operating Lanes

### Fast Lane

Docs/report-only work with no code, test, config, dependency, runtime, schema,
exchange, or trading-behavior change.

Minimum verification: status, changed files, diff check, and targeted readback.

### Standard Lane

Approved focused code, tests, CI, or behavior-preserving refactors outside
Protected criteria.

Required verification: narrow relevant tests/static checks plus scope review.

### Protected Lane

Anything involving capital, authority, runtime, private exchange access,
secrets, orders/cancels, account state, risk, kill switch, orchestrator,
execution, position state, migrations, deployment, or readiness promotion.

Explicit Human Owner authorization and risk-matched QA are required. Runtime or
trading readiness also requires independent review and runtime evidence.

## Implementation Rules

- Keep authority boundaries and pipeline order unchanged unless an accepted
  architecture decision explicitly changes them.
- Use-cases own transaction boundaries. Repository commits require an explicit
  documented exception.
- Enforce safety at the last authoritative boundary.
- No blocking network calls or sleeps in async paths.
- External actions must be idempotent.
- Partial side effects require durable observation and a repair path.
- Production `apps/*` must not import another `apps/*` without an explicit
  exception.
- Production services must not import `research/*`.
- Correlation IDs must survive success and failure paths.
- LLM output remains advisory.
- Redis remains non-authoritative.

## Research Work

Use the process in `docs/RESEARCH_CONSTITUTION.md`. The compact sequence is:

`Idea -> intake -> triage -> mechanism hypothesis -> preregistration/design lock
-> bounded run -> independent review -> owner decision`

Before inspecting candidate data, preserve a non-overlapping held-out path.
After observing results, do not change source, timeframe, universe, thresholds,
or segmentation without a new gate. A PASS is evidence, not readiness.

No paid source or infrastructure work is allowed under the current owner
constraint recorded in `docs/CURRENT_STATE.md`.

## Memory Update Rule

A change that alters owner constraints, gate, mode, readiness, migration head,
active family, verdict, or next action must update the relevant STATE file in
the same accepted change set.

Do not append chronology to state files. Put detail in a decision/result record
or `docs/archive/`. Run:

```powershell
python -m pytest tests\test_project_memory.py -q
```

## Verification

- File edit: targeted readback and search.
- Tests: report exact pass/fail/warning counts.
- Migration metadata: `python -m alembic heads`.
- Runtime: health/readiness endpoint tied to the environment and time.
- Remote claim: fetch/remote ref or GitHub evidence.
- Commit: report hash and subject.
- Push: confirm remote visibility.

A successful local check does not prove runtime or trading readiness.

## Interrupted Work

On resume:

1. Re-run the sync gate.
2. Inspect changed paths without reverting them.
3. Identify completed, partial, and untouched work.
4. Continue only inside the prior authorized scope.
5. Do not stage, commit, push, download data, or start runtime by implication.

## Roles And Approval

- Human Owner: objective, budget, authorization, risk acceptance, and final
  project decisions.
- Implementer: scoped edits and verification; no self-approval.
- Independent reviewer: challenges correctness, architecture, and evidence.
- Auditor: read-only structural and safety review.

One agent must not implement and independently approve the same readiness
decision.

## Required Report

Every completed task reports:

1. Agent
2. Task Type
3. Scope
4. Lane
5. Changed Files
6. Commands Run and exact results
7. Readiness Claims separated into docs/code/test/runtime
8. Not Verified
9. Decision Needed

Use `None` only when no owner decision remains.
