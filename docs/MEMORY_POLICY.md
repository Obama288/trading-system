# Memory Policy
PostgreSQL: authoritative
  - kill switch, candidates, executions, positions, operator_actions
Redis: ephemeral only (cache, session, dedup)
LLM output: advisory only
Research output: advisory only
docs/: project memory for AI continuity

## Agent and Process Memory

These rules govern how project agents (Tower Control, Codex Implementation
Agent, Claude Independent Reviewer, Auditor) and the Human Owner maintain
shared project memory across sessions. Role definitions live in
`docs/AGENT_PROMPTS.md`.

### 1. Human memory vs project control memory
- Human Owner memory is private and authoritative for owner intent.
- Project control memory lives in repo docs, code, tests, runtime evidence,
  commits, and PR / review threads. It is shared, auditable, and the basis
  for any agent claim about project state.
- Agent session / chat memory is not project control memory.

### 2. Memory is orientation, not authority
- Project memory orients agents to context. It does not authorize action.
- Stage transitions, GO / NO-GO, scope grants, and risk acceptance are owner
  decisions. Memory cannot substitute for them.

### 3. Source of facts
- Important claims must come from one of: repo docs, code, tests, runtime
  evidence, commits, or explicit current-session owner instruction.
- A claim that cannot be traced to one of those sources is inference or
  unknown and must be labeled as such.

### 4. Self-contained role prompts
- Every role prompt must be self-contained. No "as above", "see previous",
  "continue from yesterday", or cross-session assumptions.
- Bounds, symbols, gates, lookback, timeframe, mode, and authorization scope
  must be restated in each prompt that depends on them.

### 5. Project roles
- Tower Control coordinates, scopes, challenges assumptions, and drafts
  proposals; does not implement.
- Codex Implementation Agent implements only owner-approved tasks and
  reports exact commands, files, and verification.
- Claude Independent Reviewer reviews diffs, scope, and safety independently.
- Auditor performs structural / periodic review of repo state and safety
  boundaries.
- Roles do not collapse. The same agent must not play more than one role in
  a single decision.

### 6. No unnecessary fragmentation
- Default: one goal -> one self-contained prompt -> one report -> one
  decision.
- Split only when risk requires it (Protected Lane, multi-stage approval,
  large blast radius, or owner-requested staging).
- Do not split a single approved task into many micro-prompts that each
  require fresh approval; do not bundle unrelated changes either.

### 7. Source labeling for important claims
- Important claims about project state, gate, readiness, safety, scope,
  architecture, role, existence, or absence must be labeled or clearly
  separated as one of: fact, memory, inference, unknown, blocked.
- "Verified" requires an observable check (commit SHA, test output, runtime
  response, GitHub ref). Without that, label memory or inference, not fact.

### 8. Compact state maintenance
- After significant remote-visible project changes, update the compact state
  docs (`docs/CURRENT_STATE.md`, `research/signal_observation/RESEARCH_STATE.md`,
  and `docs/BOUNDARIES.md` where relevant) when status meaningfully changes.
- A change is significant if it alters the gate, mode, lane, escalation
  state, or recorded research verdict.
- Wording fixes and typo passes do not require compact-state updates.

### 9. Secrets policy
- Never store, log, paste, or echo secrets, tokens, passwords, API keys,
  account IDs, private exchange-endpoint output, signed payloads, or values
  derived from secrets (key prefixes / suffixes, hashes, partial keys, or
  signed request samples) in repo files, docs, prompts, comments, commit
  messages, PRs, issue text, or chat.
- If a secret is exposed by mistake, treat the secret as compromised and
  rotate it; do not merely delete the message.

### 10. Research evidence is not readiness
- C7_PASS or any other research verdict is research evidence only.
- It does not promote paper trading, runtime wiring, trading readiness,
  probe readiness, or live readiness.
- Promotion to any of those lanes requires a separate explicit Human Owner
  decision, recorded in repo docs and supported by additional gates.
