This file is the canonical startup handoff. Do not use docs/AI_HANDOFF_LEGACY.md for current state; it is archive-only.

# AI Handoff — Hephaestus

## 1. Startup order

1. `docs/CURRENT_STATE.md` — current gate, mode, Recent Commits anchor,
   Research Track, Next Allowed Work.
2. `docs/BOUNDARIES.md` — compact safety boundaries.
3. `docs/MEMORY_POLICY.md` — data-store + agent / process memory rules.
4. `research/signal_observation/RESEARCH_STATE.md` — only when the task is
   research-track.
5. `git status` / `git log --oneline -N` — only when the task needs it.
6. `docs/AGENT_PROMPTS.md` — role-specific startup prompt for your role.

Long historical docs (`docs/PROGRESS.md`, `docs/STAGE_STATUS.md`,
`docs/AI_HANDOFF_LEGACY.md`, deep stage docs) are read only when the compact
state is missing, stale, or conflicting.

## 2. Source-of-truth rule

Chat memory is orientation only. Facts come from repo docs, code, tests,
runtime evidence, commits, and PR / review threads, or from explicit current
-session owner instruction. Anything else is inference, memory, or unknown
and must be labeled as such. Never present project memory or inference as
verified fact.

## 3. Token-saving rule

Do not paste long reports, full diffs, full test logs, or large JSON dumps
into chat. Summarize:

- decision: PASS / HOLD / FAIL (or n/a)
- changed files (paths only)
- exact commands run + one-line results
- readiness claims, separated as docs / code / test / runtime
- not verified
- decision needed

Persist long content as repo artifacts (under `research/.../output/`,
`docs/`, or a Protected-Lane data path), not as chat text.

## 4. Role discipline

- Tower Control coordinates, scopes, challenges assumptions, drafts
  proposals. Does not implement.
- Codex Implementation Agent implements only owner-approved tasks and
  reports exact commands, files, and verification.
- Claude Independent Reviewer reviews diffs, scope, and safety
  independently.
- Auditor performs structural / periodic review.
- Human Owner is final authority for GO / NO-GO, stage transitions, risk
  acceptance, and readiness approval.
- Roles do not collapse in a single decision.

## 5. Self-contained prompt rule

Every role prompt must be self-contained. No "as above", "see previous",
"continue from yesterday", or cross-session assumptions. Bounds, symbols,
gates, lookback, timeframe, mode, and authorization scope must be restated
in each prompt that depends on them.

## 6. Current C7 status

- Setup C **C7_PASS** accepted on the locked backward expanded window
  `2022-01-01T00:00:00Z → 2023-12-17T12:00:00Z`, public Bitget 4H OHLCV
  only, frozen 3-symbol set BTCUSDT / ETHUSDT / SOLUSDT.
- All five C7 gate conditions pass.
- Independent post-C7 review verdict: PASS (see
  `research/signal_observation/SETUP_C_C7_POST_REVIEW_DECISION.md`).
- Setup C remains research-only **PASS_CANDIDATE**. Escalation **HOLD**.
- Mode: paper trading only. **LIVE NO-GO**.

## 7. Next likely research gate

OKX cross-venue validation planning. Same frozen detector, same symbol set,
same locked dev and expanded windows reused from C7. Public OKX
history-candles endpoint only; no credentials; no private endpoints.

Active blockers:

1. The existing `research/signal_observation/okx_public_downloader.py` is
   single-page only and needs a bounded-pagination fix analogous to
   `c3d15d0` (Bitget bounded-pagination fix) before any cross-venue
   download.
2. SOL-USDT-SWAP earliest-available date on OKX is not yet empirically
   probed; verify before locking the download bounds.

No paper, runtime, trading, probe, or live readiness is authorized by the
cross-venue plan.

## 8. Explicit no-readiness rule

`C7_PASS` is research evidence only. It does not authorize paper trading,
runtime wiring, trading readiness, probe readiness, or live readiness. Per
the design lock §"What C7 Does Not Authorize", promotion to any paper /
runtime / probe / trading / live lane requires a separate explicit Human
Owner decision recorded in repo docs and supported by additional gates.
LIVE remains **NO-GO** until that explicit decision exists.
