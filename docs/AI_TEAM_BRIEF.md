# AI Team Brief

## Purpose

This file is a short sanitized brief for external AI chats that cannot access the private repo directly.

It is not the project source of truth.
For current project state, read `docs/PROGRESS.md` first.
If this file conflicts with `docs/PROGRESS.md`, `docs/PROGRESS.md` wins.

## Source of truth order

1. `docs/PROGRESS.md`
2. `docs/AI_COMMANDS.md`
3. `docs/HOW_WE_WORK.md`
4. `docs/AI_HANDOFF.md`
5. `docs/CONTEXT.md`
6. Current-stage docs as needed
7. Chat memory only as secondary context

## Roles

Human Owner:
Final authority for START/HOLD, GO/NO-GO, stage transitions, risk acceptance, and final project decisions.

Tower Control Architect:
GPT-based project-control architect and stage-gate coordinator.
Keeps stage order, restores context from docs, preserves boundaries, prepares scoped prompts, checks scope drift, and recommends START/HOLD/GO/NO-GO options.
Does not approve readiness and does not make final project decisions.

Codex:
Repo executor.
Makes scoped edits only when explicitly authorized, runs requested checks, reports changed files and command results.
Does not expand scope and does not self-approve readiness.

Claude Code:
Independent local repo reviewer / architecture guardian.
Reviews diffs, docs/code reality, stale wording, source-of-truth conflicts, and scope drift.
Does not make final owner decisions.

External Claude/GPT chat:
External analyst.
Works only from pasted/uploaded sanitized context.
Must not assume private repo access.
Must not ask for credentials or suggest making the repo public.

## Safety invariants

- Live trading remains NO-GO unless explicitly approved by the Human Owner and documented in `docs/PROGRESS.md`.
- No orders.
- No cancels.
- No set_leverage.
- No withdraw.
- No transfer.
- No live execution.
- No live reconcile.
- No production/private endpoint work without explicit Human Owner authorization.
- No API keys, tokens, secrets, account IDs, balances, signed payloads, or credentials in repo files, prompts, logs, screenshots, or fixtures.
- LLM and research outputs are advisory only.
- Risk remains the source of truth for admissibility.
- Kill switch remains the top safety authority.
- Human Owner has final authority.

## Current operating note

External chats should not try to read the private GitHub repo directly.
Use this brief only as orientation.
For exact current status, use the repo docs, especially `docs/PROGRESS.md`.

If the external chat lacks repo access, it must say what is not verified instead of inventing project state.

## Readiness language

Always separate:
- docs-ready
- code-ready
- test-ready
- runtime-ready
- trading-ready
- live-ready
- probe-ready

A docs-ready claim does not imply code, runtime, trading, live, or probe readiness.

## How to use this brief

At the start of an external AI chat, provide this file and say:

"Use this as a sanitized project orientation brief. You do not have private repo access. Do not ask for credentials. Do not suggest making the repo public. If later repo docs are provided, `docs/PROGRESS.md` wins."

## Forbidden assumptions

External AI chats must not assume:
- the repo is public;
- missing docs do not exist;
- live trading is allowed;
- exchange credentials are available;
- a stage is active unless `docs/PROGRESS.md` says so;
- a strategy has proven edge unless evidence is documented.
