# Commands Registry

Status: ACTIVE (reference layer). Extensible registry of `!`-shortcuts for
agent sessions. Replaces the command section of the archived AI_COMMANDS.md.
Proposed location: `docs/COMMANDS.md`

---

## The one rule that keeps this file alive

**Commands reference live state; they never store it.** A command definition
says *what to read and what to answer*, not the answer itself. The predecessor
(AI_COMMANDS.md) rotted because it embedded a dated project snapshot next to the
commands. Here, `!status` points at `CURRENT_STATE.md` — so it stays correct
forever, whatever the project does.

If you ever find yourself writing a concrete fact (a date, a gate name, a
commit) into a command *definition*, stop: that fact belongs in the file the
command reads, not here.

## How to add a command

Append an entry in this exact shape:

```
### !name
Reads:   <file(s) / git / source the command consults>
Returns: <what the agent should answer, described — never the answer itself>
Lane:    <read-only | requires-owner-approval>   (default read-only)
```

Keep it to those four lines. No state, no snapshots.

---

## Active commands

### !startup
Reads:   docs/CURRENT_STATE.md, docs/BOUNDARIES.md, recent git commits
Returns: repo, current gate, mode, live status (NO-GO until explicit owner GO),
         key blockers, allowed next lane, and the no-edit/no-branch/no-commit/
         no-probe/no-secrets reminder
Lane:    read-only

### !sync
Reads:   git branch/HEAD, working tree, current scope's allowed/blocked files
Returns: branch/HEAD, dirty files + classification, allowed vs blocked files
         for the current scope, GO/HOLD verdict before edits
Lane:    read-only

### !status
Reads:   docs/CURRENT_STATE.md, research/signal_observation/RESEARCH_STATE.md,
         latest commits, pytest count, alembic head
Returns: current gate/stage, last completed step, next allowed step, research
         track status, test count, migration head
Lane:    read-only

### !rules
Reads:   docs/BOUNDARIES.md (authority + source rules)
Returns: the hard authority and source-of-truth rules verbatim
Lane:    read-only

### !review
Reads:   the diff/files provided in-session
Returns: independent review — scope, safety, correctness, stale-wording, scope
         drift; does not make owner decisions
Lane:    read-only

### !checkpoint
Reads:   current session decisions and changed paths
Returns: a compact decision record (Decision · Why · Alternatives · Why
         rejected · What this does not authorize) ready to commit to the
         relevant decision-record doc
Lane:    requires-owner-approval (writes a doc)

---

## Retired commands

Removed because they were thin aliases for a normal request, or pointed at
content that is now stale. A natural-language ask does the same job:
`!stack`, `!stages`, `!hypothesis`, `!td`, `!context`. Re-add via the shape
above only if a real recurring need appears.
