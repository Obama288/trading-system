# Project Memory Policy

Status: ACTIVE / LAW

Purpose: keep Hephaestus recoverable across people, agents, machines, and
sessions without turning stale narrative into authority.

## Economic Objective

The project exists to build a system capable of producing repeatable net
trading profit after fees, slippage, funding, operational failures, and risk.
Infrastructure and research process serve that objective; they are not the
objective themselves.

The current absence of a proven edge is an evidence statement, not a change of
goal. Profit may be claimed only after the relevant evidence gate is met.

## Current Owner Constraints

- No new project spending: no paid data, paid API plans, new subscriptions, or
  infrastructure upgrades unless the Human Owner explicitly reverses this.
- Correctness and reproducibility take priority over speed.
- Paper-only remains in force. Live trading remains NO-GO.
- The next phase is preparation: truthful state, reproducible tests, safe paper
  behavior, and disciplined research.

Current owner instructions in the active session override older planning notes.
Material owner constraints must then be recorded in `docs/CURRENT_STATE.md` in
the same accepted change set.

## Memory Layers And Precedence

Use the first applicable layer. Report conflicts; do not silently reconcile
them.

1. **Current owner instruction** - intent, budget, and explicit authorization.
2. **LAW** - `docs/BOUNDARIES.md`, `docs/RESEARCH_CONSTITUTION.md`, and this
   policy.
3. **STATE** - `docs/CURRENT_STATE.md` and, for research work,
   `research/signal_observation/RESEARCH_STATE.md`.
4. **IMPLEMENTATION FACT** - current Git history, code, migrations, tests, CI,
   and runtime evidence tied to a commit or environment.
5. **DECISION / DESIGN** - accepted decision records and design locks.
6. **REFERENCE** - maps, runbooks, working practices, and surveys.
7. **HISTORY** - `docs/archive/` and closed research artifacts.
8. **SESSION MEMORY / INFERENCE** - orientation only; never project fact.

Code beats docs for implemented behavior. Runtime evidence beats assumptions
about deployment. STATE beats HISTORY for the current gate. LAW beats every
other repo document for constraints.

## Compact State Contract

`docs/CURRENT_STATE.md` must contain only:

- objective and current owner constraints;
- mode, gate, active lane, and readiness claims;
- current blockers and allowed next work;
- a short research snapshot;
- the latest decision needed.

`research/signal_observation/RESEARCH_STATE.md` must contain only:

- active family and current research gate;
- compact verdicts for parked/retired families;
- current candidate and its prerequisites;
- allowed next research decision;
- pointers to detailed evidence.

Neither state file is a progression log. Detailed chronology belongs in Git,
decision records, result reports, or `docs/archive/`. Target limits:

- `CURRENT_STATE.md`: at most 150 lines;
- `RESEARCH_STATE.md`: at most 180 lines.

## Update Transaction

A change that alters a gate, verdict, owner constraint, mode, readiness claim,
migration head, active family, or allowed next action must update the relevant
STATE file in the same accepted change set.

Before reporting completion:

1. Read current STATE and LAW.
2. Verify Git HEAD and dirty files.
3. Verify changed facts from code/tests/runtime rather than memory.
4. Update only the affected state fields.
5. Run the project-memory integrity test.
6. Report docs/code/test/runtime readiness separately.

Do not copy recent commit lists, test counts, service-health claims, or model
names into multiple startup files. Volatile facts have one canonical home.

## Fact Labels

- **Verified**: supported by an observable check tied to a commit/environment.
- **Recorded**: accepted owner decision or repo decision record.
- **Unverified**: plausible but not checked in the current environment.
- **Blocked**: required check cannot currently be performed.
- **Inference**: reasoned conclusion, explicitly labeled.

Never write "healthy", "ready", "working", or "green" without stating what was
checked and whether the claim applies to docs, code, tests, or runtime.

## Durable State Ownership

PostgreSQL is authoritative for durable operational state, including:

- kill-switch/system state;
- trade candidates and operator actions;
- executions;
- positions and position events;
- paper account authority;
- incidents and journal events.

Redis is ephemeral only: cache, session, transport, and deduplication support.
It must not become the source of truth for candidate, execution, position,
account authority, or kill-switch state.

LLM output and research output are advisory. They become project decisions only
through an explicit owner decision and the appropriate repo record.

## Document Lifecycle

Every active or reference document must declare one status near the top:
`ACTIVE`, `DRAFT`, `PARKED`, `RETIRED`, `SUPERSEDED`, `HISTORICAL`, or
`ARCHIVED`.

There is one archive path: `docs/archive/` (lowercase). Archived content is not
loaded during normal startup.

## Local-Only State

The following are not project memory and must not be used as evidence:

- chat/session memory;
- editor or agent local settings;
- untracked reports, scripts, fixtures, or review packets;
- local `.env` contents;
- local runtime state not tied to an explicit verification report.

Useful local artifacts must be classified and accepted before becoming repo
fact.

## Secrets

Never store or echo secrets, account identifiers, balances, signed payloads,
private-endpoint output, secret prefixes/suffixes/hashes, or derived secret
values in docs, prompts, logs, commits, issues, or chat. An exposed secret is
treated as compromised and rotated.
