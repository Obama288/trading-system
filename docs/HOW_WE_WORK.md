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

## Roles

**Human Owner:**
Owns final GO/NO-GO, START/HOLD, stage transitions, risk acceptance, accepting/rejecting diffs.

**GPT:**
Project control assistant and prompt architect.
Helps interpret roadmap from docs, drafts prompts, separates docs-ready/code-ready/test-ready/runtime-ready, summarizes findings into decision options.
Does not own roadmap, approve readiness, or make GO/NO-GO decisions.

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
Required flow:
1. Codex implements.
2. Independent review checks.
3. GPT structures decision options.
4. Human owner decides.
5. PROGRESS.md checkpoint records confirmed reality.

## Readiness Levels

- **Docs-ready:** documented, not necessarily implemented.
- **Code-ready:** code inspection confirms implementation.
- **Test-ready:** tests prove expected behavior.
- **Runtime-ready:** deployed environment proves expected behavior.

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
