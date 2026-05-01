# How We Work

## Core Principle

No AI agent has authority to approve trading readiness.
AI agents may inspect, implement, review, summarize, and recommend.
Only the human owner can make final project decisions:
- accept / reject a diff
- move to the next stage
- start or stop a probe
- declare GO / NO-GO
- accept or reject known risk

## Pre-change Sync Gate

Before edits, branches, commits, or PRs, run the compact sync gate:
- `git status --short --branch`
- `git rev-parse HEAD`
- `git log -1 --oneline`
- `git diff --name-only`

Rules:
- Dirty files must be classified before editing: accepted current-task / pre-existing pending / generated / unknown.
- Unknown dirty files block new edits.
- Docs must not promote status based on unaccepted dirty code/test files.
- No branch may be created to bypass unclassified dirty files.
- After a clean or accepted sync gate, work in one bounded pass, not fragmented micro-steps.

## Evidence Before Status

- No evidence -> no status promotion.
- Uncommitted code is not project reality until accepted by the Human Owner and recorded in source-of-truth docs.
- Avoid duplicating `docs/PROGRESS.md` current status across multiple docs; summarize only what the target doc needs.

## 3-Lane Operating Model

The lanes reduce unnecessary handoff loops while preserving Human Owner authority and docs/code/test/runtime separation.
Use the strictest lane that matches the work. The Human Owner may always move work to a stricter lane.

### Fast Lane

Use for bounded, low-risk work:
- docs-only syncs that record already accepted reality
- typo, formatting, link, checklist, and status cleanup
- report-only inspection with no repo changes
- static documentation safety checks

Rules:
- No code, tests, config, infra, dependency, runtime, secret, service startup, or trading-behavior change.
- No new readiness claim unless it cites already existing evidence.
- QA is optional. If skipped, the report must say it was skipped and why.
- Minimum verification is scope verification: `git status --short --branch`, changed-file list, `git diff --check`, and targeted readback/search when relevant.
- Extra handoff is not required unless the Human Owner asks for it or the docs change alters an authority, readiness, or safety decision.

### Standard Lane

Use for normal approved project work:
- focused code or test changes inside an accepted scope
- non-runtime refactors that preserve behavior
- docs changes that coordinate with code/test changes
- bug fixes with local, targeted verification

Rules:
- Human Owner authority remains unchanged; agents may recommend, not approve readiness.
- The implementer may plan, patch, and run targeted verification without creating a separate handoff loop for every small step.
- QA is compact and required: run the narrowest relevant tests/static checks plus scope checks.
- Independent review is optional unless the change touches Protected Lane criteria or the Human Owner requests it.
- Readiness claims must stay separated as docs-ready, code-ready, test-ready, and runtime-ready.

### Protected Lane

Use when work touches safety, capital, runtime, or irreversible project gates:
- live trading, probe readiness, START/HOLD, GO/NO-GO, or readiness promotion
- authenticated/private exchange clients, API keys, secrets, balances, positions, orders, cancels, withdrawals, transfers, leverage, live reconcile, or live execution
- risk, kill switch, orchestrator, execution_service, position_manager, authority boundaries, or source-of-truth rules
- service startup wiring, deployments, VPS/runtime operations, infra, config that changes runtime behavior, dependency changes, migrations, or schema changes
- cross-service contracts, event bus/pub-sub, durable state ownership, or production data handling

Rules:
- Explicit Human Owner authorization is required before implementation.
- QA is mandatory and must match the risk: relevant tests, static checks, diff review, and runtime/deployment checks if any runtime readiness is claimed.
- Independent review is mandatory before readiness promotion, live/probe authorization, or acceptance of known Protected Lane risk.
- The writing agent cannot self-approve readiness.
- A Protected Lane report must clearly state what remains unverified and what decision is required from the Human Owner.

### QA Levels

- Optional QA: allowed only in Fast Lane docs/report-only work. Skips must be explicit.
- Compact QA: required in Standard Lane. Use targeted tests/checks that directly cover the change and confirm file scope.
- Mandatory QA: required in Protected Lane. Include relevant tests/checks, independent review when required, and runtime evidence for runtime claims.

## Roles

**Human Owner:**
Owns final GO/NO-GO, START/HOLD, stage transitions, risk acceptance, accepting/rejecting diffs.

**Tower Control Architect:**
GPT-based project-control architect.
Restores context from `docs/PROGRESS.md` first.
Keeps stage order and gate discipline.
Preserves architecture boundaries and source-of-truth rules.
Prepares scoped prompts for Codex and review prompts for Claude.
Checks scope drift, stale docs, and readiness overclaims.
Separates docs-ready, code-ready, test-ready, runtime-ready, trading-ready, live-ready, and probe-ready claims.
May recommend START/HOLD/GO/NO-GO options.
Does not own the roadmap, approve readiness, accept risk, or make final project decisions.

**Codex:**
Repo executor.
Reads code, makes minimal safe fixes, adds focused tests, runs repo commands, reports exact changed files and test results.
Does not self-approve readiness or expand scope.

**Claude:**
Independent reviewer / architecture guardian.
Challenges assumptions, finds stale docs vs code reality, reviews transaction/source-of-truth boundaries, finds adjacent same-class bugs.
Does not make final owner decision.

## No Self-Approval Rule

The agent that writes code cannot be the final approver of readiness.
Default flow by lane:
1. Fast Lane: agent scopes, edits or inspects, verifies scope, reports; Human Owner accepts/rejects if a decision is needed.
2. Standard Lane: agent plans or proceeds within accepted scope, implements, runs compact QA, reports; Human Owner accepts/rejects or asks for review.
3. Protected Lane: Human Owner authorizes, agent implements only inside that authorization, mandatory QA and independent review occur where required, Tower Control Architect may structure decision options, Human Owner decides.
4. PROGRESS.md checkpoint records confirmed project reality when the Human Owner requests a checkpoint or accepts a status change.

## Readiness Levels

- **Docs-ready:** documented, not necessarily implemented.
- **Code-ready:** code inspection confirms implementation.
- **Test-ready:** tests prove expected behavior.
- **Runtime-ready:** deployed environment proves expected behavior.

A docs-only change can make a docs-ready claim only. It must not imply code-ready, test-ready, runtime-ready, trading-ready, live-ready, or probe-ready unless it cites existing verified evidence and leaves the underlying readiness level unchanged.

## Required Agent Report

Every agent report must identify:
- Agent
- Task Type
- Scope
- Lane
- Changed Files
- Commands Run
- Readiness Claims
- Not Verified
- Decision Needed

Report rules:
- `Changed Files` must list every changed path, or `None`.
- `Commands Run` must include exact commands and results, or state that no commands were run.
- `Readiness Claims` must separate docs/code/test/runtime and must not promote readiness by implication.
- `Not Verified` must explicitly say when tests, runtime checks, deployment checks, external review, or QA were not run.
- `Decision Needed` belongs to the Human Owner. If no decision is needed, say `None`.

## Engineering Rules v2 (Keep The Codebase Stable)
These are project-wide rules that prevent the failure classes we already hit (TOCTOU, partial commits, event-loop hangs).
They are phrased as rules, not steps.

1. Commit Ownership Lives In Use-Cases
- Repositories may `add()` / mutate / `flush()`, but **must not** `commit()` inside business methods unless explicitly documented as safe.
- Use-cases own transaction boundaries so DB state + audit/journal state can be atomic.

2. Enforce At Authoritative Boundaries
- Any safety control that protects capital or integrity must be enforced at the last authoritative boundary (usually DB-backed) to avoid stale pre-checks.

3. No Blocking Calls In Async Contexts
- No sync `httpx.*` and no `time.sleep()` in async request handlers or code called by them.
- Prefer a single shared async HTTP client wrapper with timeouts and explicit retry policy.

4. Idempotency Is A Contract
- All externally-triggered actions must be safe to retry (idempotency keys, DB uniqueness where appropriate).
- Retries must not create duplicates or change meaning.

5. Side-Effects Must Have Compensation Or Repair
- If we persist execution but opening/closing a position can fail, we must emit a durable event and have a repair path (retry/compensate) that converges state.

6. Architecture Boundaries Are Enforced In Code
- `apps/*` must not import from other `apps/*` (except tests) without an explicit exception.
- `research/*` is advisory-only and must not be imported by production services.

7. Failure Must Be Observable
- `correlation_id` must be present in logs and error responses even on exceptions.
- Journal/audit failures must be explicit, never silent success.

## PR Checklist (Reviewer Uses This Every Change)
- pytest green
- authority rules preserved
- transaction boundaries make sense (no hidden commits in repos)
- no cross-service imports from `apps/*` to `apps/*` unless explicitly approved
- DB persistence where needed
- no sync httpx/time.sleep in async handlers
- alembic migration if new table
- correlation_id propagated (including error responses)
- idempotency covered for retries (DB unique constraints or keys)
