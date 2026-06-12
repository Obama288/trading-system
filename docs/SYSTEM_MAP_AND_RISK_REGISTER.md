# System Map & Risk Register

Status: v1.0 — audit part 1, conducted 2026-06-13 on commit e4db1e8
Scope: whole-system architecture, order path, risk controls, secrets, docs.
Out of scope (deferred to part 2, a Stage 5 entry gate): line-by-line
correctness of execution code on the frozen pre-paper commit.
Location when adopted: `docs/SYSTEM_MAP_AND_RISK_REGISTER.md`

---

## 1. System map

Five planes. Arrows = primary data flow.

```
DATA        research CSV downloaders (Binance/Bitget/OKX) ──► research datasets
            libs/clients/okx_market_data_fetcher ──► live snapshots

RESEARCH    research/simcore (simulator, quality, time, costs)
            research/signal_observation (Stage 2-4 engine, governed by
              docs/RESEARCH_CONSTITUTION.md)
            research/hypothesis_agent (Stage 0 candidate generator → Telegram)

PAPER/LIVE  ops/paper_pipeline_runner ──► kill_switch check (fail-closed)
              ──► market_data (snapshot + freshness gate, 120 s stale cutoff)
              ──► signal_engine (EMA20/50 + RSI rules, 15 m)   ⚠ see R1
              ──► risk_engine (sizing: 1 %/trade, 2 % daily, 1 position, 3x)
              ──► review_gateway (anomaly/consistency checks)
              ──► orchestrator (approve/reject; ops/auto_approve_paper)
              ──► execution_service (validation, idempotency, dry-run,
                    orphan detection)
              ──► position_manager (open/close, stop/TP/TTL exit rules,
                    reconcile scheduler)

RECORD      journal_ingest ──► journal_review (LLM summaries) / incidents

CONTROL     kill_switch service (halt/resume/status), operator tokens,
            Telegram alerts
```

State lives in Postgres (positions, executions, candidates, incidents,
system_state, paper_account_authority) + Redis. Services authenticate to each
other with INTERNAL_SERVICE_TOKEN.

## 2. Order path trace (paper)

runner tick → kill switch status (errors = skip, fail-closed ✓) → build
snapshot from OKX → staleness gate ✓ → signal_engine decision → risk_engine
position size from equity × max_risk_fraction / stop distance; zero size on
non-positive equity ✓ → review_gateway checks → orchestrator approval
(auto-approve in paper) → execution_service validates candidate (stop on
correct side of entry ✓, positive qty/price ✓), idempotency key, paper fill →
position_manager persists; exit rules: stop-loss / take-profit / TTL;
reconcile scheduler for drift; orphan detector for unmatched orders →
journal.

Verified positives: kill switch is consulted FIRST and fails closed; risk
limits exist and are config-driven; execution candidate validation rejects
malformed stops; idempotency, reconciliation, and orphan detection exist;
incidents service exists. The execution skeleton is more mature than typical
at this stage.

## 3. Risk register (probability × damage, descending)

R1 — Research and execution are two disconnected brains. HIGH/HIGH.
signal_engine trades EMA20/50+RSI "breakout_retest"/"trend_continuation" on
15 m — rules the research pipeline has retired (Setup A/B families) or never
validated, with zero connection to simcore or the constitution gates.
Acceptable ONLY as an infrastructure harness. Dangers: (a) paper results get
read as strategy evidence; (b) at go-live the unvalidated engine is what is
wired in. Mitigation: relabel runner output/docs as "plumbing harness, not
strategy evidence"; constitution Stage 5 already requires paper to run a
frozen, gated detector — when Setup E (or successor) reaches Stage 5, the
signal source must be the frozen research detector, and signal_engine rules
must never be promoted to live without passing the pipeline.

R2 — Paper account state is caller-supplied, not authoritative. MED/HIGH.
PaperHarnessAccountState (equity, daily PnL, exposure) is provided by the
caller; the repo's own docstring flags this as open issue P0-A. drawdown_lock
is hardcoded False. Daily-loss and exposure limits computed from unverified
numbers protect nothing. Known and documented by the project — must be closed
(authoritative reconstruction from positions/executions) before live; ideally
before Stage 5 so paper exercises the real path.

R3 — No CI. MED/MED. "Suite green" depends on whose machine runs it (audit
reproduced 136 environment-dependent failures locally). One-time acceptance
greps (session_label, single-simulator) are not standing protections.
Mitigation: GitHub Actions running the research suite + grep-checks as tests;
required for the research scope at minimum.

R4 — float in the money path. MED/MED. position_manager rules and risk_engine
use float for prices/equity while research is Decimal end-to-end. Paper-safe;
for live, comparison/rounding at stop boundaries is a real failure mode. Add
to pre-live audit: Decimal (or integer ticks) through execution.

R5 — Locked windows are locked by date, not by content. MED/MED. Re-downloaded
datasets silently change "the same" window (the OKX pagination fix makes this
concrete: old and new OKX history differ). Mitigation: pre-registration
records SHA-256 of dataset files; quality reports bind to file hash.

R6 — Silent-channel ambiguity. MED/LOW-MED. Telegram alerts' normal state is
silence; a dead token/process is indistinguishable from "no signals" for
weeks. Mitigation: periodic heartbeat ("alive, scanned N symbols") on every
alert channel.

R7 — Memory sprawl and discoverability. MED/LOW. 15k+ lines in docs/;
RESEARCH_CONSTITUTION.md is not on the documented session startup path
(CURRENT_STATE → BOUNDARIES → role docs). Stale memory creates false
confidence. Mitigation: one-line links from CURRENT_STATE and HOW_WE_WORK;
archive pass for legacy docs; explicit precedence rule (state docs describe,
law docs govern, history docs never change).

R8 — Secrets. LOW/HIGH (currently clean). .env gitignored, never committed in
history; .env.example contains placeholders only. Keep: never log tokens,
enforce 32-char minimum (noted in .env.example), rotate if a session ever
echoes one.

R9 — Stage 5 freeze is declarative. LOW/MED today, HIGH at paper entry. The
constitution requires a frozen commit hash, but no runtime check verifies the
running code matches it. Mitigation (at Stage 5 implementation): runner logs
its git hash at startup and refuses to trade if it differs from the decision
record.

## 4. Standing guardrails to add now (cheap, rot-proof)

1. CI (GitHub Actions): research suite + simcore tests on every push.
2. Convert one-time acceptance greps into permanent tests:
   - no session_label(open_time) outside simcore;
   - no trade-exit computation outside simcore in research/.
3. Paper runner banner + docs line: "infrastructure harness; output is not
   strategy evidence" (closes the cheap half of R1).
4. CURRENT_STATE/HOW_WE_WORK one-line links to the constitution (R7).
5. Constitution amendment (single commit): Stage 5 entry additionally requires
   (a) execution audit passed on the frozen commit, (b) runtime hash check
   (R9), (c) pre-registration records dataset SHA-256 (R5).

## 5. Pre-paper execution audit checklist (part 2 scope, run on frozen commit)

- Position sizing math line-by-line, including rounding and min-notional.
- Decimal/tick handling through execution (R4).
- Authoritative account state in place; P0-A closed (R2).
- Kill switch under failure: service down, slow, flapping.
- Exchange failure modes mid-position: reconnect, reconcile, orphan paths.
- auto_approve must be provably impossible outside paper mode.
- Alert heartbeats live (R6).
- Frozen-hash runtime check active (R9).
- Signal source = frozen research detector, not signal_engine (R1).
