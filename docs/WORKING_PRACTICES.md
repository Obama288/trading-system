# Working Practices

Status: ACTIVE (reference layer). Distilled from the now-archived AI_HANDOFF,
AI_COMMANDS, AGENT_PROMPTS, AI_TEAM_BRIEF — deduplicated and updated to current
reality. Process LAW lives in BOUNDARIES.md and RESEARCH_CONSTITUTION.md; this
file holds working habits, not constraints. On conflict, LAW wins.
Proposed location: `docs/WORKING_PRACTICES.md`

---

## 1. Source of truth

Order, highest first:
1. Current explicit owner instruction in chat (unless unsafe).
2. GitHub merged docs for project status and gates.
3. Latest git commits for actual repo changes.
4. Actual code for implemented behavior (code beats docs).
5. Test/CI output tied to an exact commit SHA.
6. Runtime evidence for deployed state.
7. PR/review discussion for pending context.
8. Project memory / docs — orientation only.
9. Inference — only when explicitly labeled as such.

Chat memory is orientation, never verified fact. Never present memory or
inference as confirmed. If your understanding of state, gate, or allowed scope
changes, tell the owner before proposing work — never silently update the model.

## 2. Token discipline

Do not paste long reports, full diffs, full test logs, or large JSON into chat.
Persist long content as repo artifacts (under `research/.../output/`, `docs/`,
or a data path) and summarize in chat:
- decision: PASS / HOLD / FAIL (or n/a)
- changed files (paths only)
- exact commands run + one-line results
- readiness claims, separated as docs / code / test / runtime
- not verified
- decision needed

## 3. Self-contained prompts

Every task prompt is self-contained. No "as above", "see previous", "continue
from yesterday". Restate bounds, symbols, gates, lookback, timeframe, mode, and
authorization scope in each prompt that depends on them. (This is exactly how
the simcore/Setup-E work was driven: each Claude Code task carried its own full
spec.)

## 4. Environment defaults

- Windows PowerShell, not Bash. Use `;` not `&&` between commands.
- Always `python -m pytest`, `python -m alembic`, `python -m uvicorn`.
- Project path: `E:\trading-system`.
- Env vars: Process scope, never Machine. Secrets only in `.env` (gitignored).

## 5. Verify before proceeding

Never claim success from a write or run alone — verify with an independent
command.
- after a file edit: `Get-Content <file>` / `Select-String <file> '<key>'`
- after a service start: hit its `/health`
- after a migration: `python -m alembic current`
- after tests: show the full `N passed` line, do not paraphrase
- after a commit: `git push`, then confirm it is remote-visible

## 6. Definition of Done (every agent report)

Agent · Task type · Scope · Lane · Changed files · Commands run (exact +
results) · Readiness claims (docs/code/test/runtime separated) · Not verified
(skipped tests/runtime/review) · Decision needed (owner's; `None` if none).

## 7. Roles

Currently active: Human Owner + Claude (chat: strategy, architecture, risk,
review) + Claude Code (local repo executor/reviewer). Other roles are in
reserve and return as the project scales — kept here so the structure is ready.

- **Human Owner** — final authority for START/HOLD, GO/NO-GO, stage
  transitions, risk acceptance, readiness approval. ACTIVE.
- **Claude (chat)** — strategy, architecture, risk analysis, independent
  review of diffs and reasoning. Does not make owner decisions. ACTIVE.
- **Claude Code** — local repo executor and architecture guardian: scoped
  edits, focused fixes, reads files, runs checks, reviews diffs and stale
  wording. Does not self-approve readiness. ACTIVE.
- **Tower Control (GPT)** — project-control architect, stage-gate coordinator,
  context recovery, scoped-prompt preparation, scope-drift checks. Does not
  approve readiness. RESERVE.
- **Codex** — repo executor for scoped, authorized edits + tests. Does not
  expand scope or self-approve readiness. RESERVE.

Roles do not collapse in one decision. Docs-ready, code-ready, test-ready, and
runtime-ready are separate claims; a docs-only change never approves trading,
paper, probe, runtime, or live readiness.

## 8. Research-work rules (carried from AGENT_PROMPTS, aligned with constitution)

- New setup family path: idea → candidate backlog + triage (mechanism clarity,
  counterparty clarity, data feasibility, cheap falsifiability, distinctness,
  plausible edge above cost floor) → mechanism-first hypothesis note → only
  then a design lock / pre-registration. Never open a family from "interesting
  indicator" alone. Every candidate carries a signal-family tag.
- Mechanism-first hypothesis note must cover: mechanism, counterparty, data,
  prior support, failure mode, cheap falsification, decision unlocked.
- Decision-record shape: Decision · Why · Alternatives considered · Why
  alternatives rejected · What this does not authorize. Compact unless detail
  is needed.
- Large diffs are a scope smell — not a hard blocker, but explain why an
  unusually large diff is still one logical change.

## 9. Named procedures (replacing the old `!` hot-commands)

These read live state rather than storing it (the old AI_COMMANDS rotted
because it embedded a dated snapshot). See `docs/COMMANDS.md` for the
extensible command registry. Core two:

- **Session startup** — read `docs/CURRENT_STATE.md`, then `docs/BOUNDARIES.md`,
  then recent commits; read `RESEARCH_STATE.md` only for research tasks; read
  history docs only if compact state is missing/stale/conflicting. Report:
  repo, current gate, mode, live status (NO-GO until explicit owner GO), key
  blockers, allowed next lane.
- **Pre-edit sync check** — before any edit: branch/HEAD, dirty files and their
  classification, what files are allowed vs blocked for the current scope, and
  a GO/HOLD verdict. Halt if blocked files are touched.
