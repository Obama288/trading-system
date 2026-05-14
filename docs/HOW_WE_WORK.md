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

## Context Restore Before New Work

Before starting any new stage or new chat continuation, restore context from the
source-of-truth docs and stage map:
1. `docs/PROGRESS.md`
2. `docs/AI_COMMANDS.md`
3. `docs/HOW_WE_WORK.md`
4. `docs/AI_HANDOFF.md`
5. `docs/STAGE_MAP.md`
6. `docs/PROJECT_ORIGIN.md`
7. `docs/CONTEXT.md`
8. Current-stage docs as needed

Do not infer the current stage from memory alone.
If docs conflict, `docs/PROGRESS.md` wins.

## Task-Specific Context Discipline

- One session = one role = one task.
- Load only context required for the current task.
- Reviewer context should be the reviewed file/diff plus minimal known context.
- Implementer context should be the governing design lock, target scope, and
  verification expectation.
- Auditor context should include the explicit audit scope.
- Do not load full history docs unless compact state is stale, conflicting, or
  insufficient.

## Design Locks, Decisions, And Scope Smells

- Implementation without an approved design lock is scope drift for any
  non-trivial research, runtime, or governance change.
- Small pointer edits and trivial post-review wording fixes do not require a
  new design lock.
- Preferred decision-record pattern: Decision, Why, Alternatives considered,
  Why alternatives were not chosen, and What this does not authorize. This is a
  compact preferred pattern, not a mandatory long template.
- Large diffs should trigger a scope check. If a diff is unusually large for
  the task, Codex or Tower Control should explain why it is still one logical
  change. Treat this as a scope-smell heuristic, not a rigid numeric blocker.

## Candidate Intake And Triage Before Hypothesis Notes

### Candidate Intake

- Raw research ideas should first enter a lightweight candidate backlog before
  becoming formal setup work.
- Intake does not create an active project stage or obligation to execute.
- Suggested backlog entry fields:
  - Candidate
  - Signal family
  - One-line mechanism
  - Potential payer / counterparty
  - Likely data
  - Why it may matter
  - Status: watchlist / triage-ready / rejected / advanced-to-hypothesis

### Signal Family Tag

- Every candidate must declare a signal family.
- Family tags distinguish genuinely new research directions from repeated
  attempts in an exhausted family.
- This supports the project rule that repeated failures within one family
  trigger structural review before another same-family setup attempt.
- Brief examples: Trend / continuation, Carry / funding, Forced deleveraging /
  liquidation, Calendar / seasonality, Cross-asset, Microstructure, Regime
  meta-layer.

### Candidate Triage

Before creating a full mechanism-first hypothesis note, Tower Control should
triage a candidate using six questions:

1. Mechanism clarity:
   Can we explain who creates the imbalance and why?
2. Counterparty clarity:
   Can we name who may plausibly be paying the edge?
3. Data feasibility:
   Does a plausible data path appear to exist?
4. Cheap falsifiability:
   Is there a simple pre-backtest statistic or observation that can
   weaken/support the idea?
5. Distinctness:
   Is this genuinely a new signal family or just another variation of an
   exhausted one?
6. Expected edge above cost floor:
   Is there a plausible reason the effect could survive realistic costs?

### Triage Result

- Triage result should be exactly one of: Advance to hypothesis note, Keep on
  watchlist, Reject for now.
- If a candidate cannot clear triage, it should not move into a full hypothesis
  note yet.

Preferred sequence for new setup-family work:
Idea -> Candidate Intake -> Candidate Triage -> Hypothesis Note -> Pre-Cn
Decision Gate -> Design Lock -> Data / Implementation -> Reviewed Result ->
Decision Record.

## Research Throughput Discipline

A current strategic risk is not only weak validation, but low discovery
throughput: too few candidates, too slow movement from idea to cheap
falsification, and too much heavy setup work before early rejection.

Preserve research rigor while increasing the speed of Candidate Backlog ->
Triage -> Hypothesis Note -> cheap falsification. Prefer early, low-cost
falsification before expensive setup design, data work, or implementation when
the question can be weakened cheaply.

This does not authorize skipping gates, weakening evidence standards, or
treating research PASS as paper, runtime, trading, probe, or live readiness.

After each security or infrastructure milestone, Tower Control must explicitly
check whether research throughput has been harmed. If the active research lane
is parked or stalled, security/infrastructure work may continue only when the
next step directly blocks the nearest active research gate. Otherwise, Tower
Control should recommend PARK for the side lane, record the next known
follow-up step, and return the project to the active research priority.

## Exploratory Discovery Lane

EXPLORE exists to quickly inspect whether a candidate area may contain
something worth formal research.

EXPLORE is not validation, not evidence, not a PASS/FAIL research verdict, and
not a readiness claim. EXPLORE may use quick one-off local notebooks/scripts
and public data only unless a future explicit owner-approved task authorizes
otherwise.

EXPLORE outputs do not become formal evidence by themselves. If an EXPLORE
result appears interesting, any later formal research must use a separately
specified validation path on data not used in exploration. A discovered effect
must not be "validated" on the same data used to find it.

EXPLORE should reduce wasted formal process on empty ideas, not replace the
formal process when an idea advances.

## Hypothesis-First Protocol For New Setup Families

Before any new setup family receives a Pre-Cn Decision Gate, design lock, data
acquisition work, or implementation code, it must first have a short
mechanism-first hypothesis note.

The hypothesis note must define:
1. Mechanism: who creates the imbalance and why.
2. Forced or predictable behavior: what market participants are structurally or
   behaviorally pushed to do.
3. Counterparty: who may be paying for the edge.
4. Data: what evidence would be needed and whether the data path is plausibly
   available.
5. Prior support: literature, known market microstructure, or explicit
   statement that support is weak/absent.
6. Failure mode: why the idea may not work or may be untradeable.
7. First cheap falsification: the simplest pre-backtest statistic that can
   weaken or support the hypothesis.
8. Decision unlocked: what first test would allow or disallow next.

Within that sequence, a hypothesis note precedes a Pre-Cn Decision Gate if a
concrete first test is justified, then design lock, data / implementation,
reviewed result, and decision record.

"Indicator first, explanation later" is discouraged. A known strategy family
may still be considered, but it must be translated into an explicit market
mechanism before coding. If the hypothesis note cannot state who plausibly pays
the edge or why the mechanism should persist, the idea should not move to
design lock yet.

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
