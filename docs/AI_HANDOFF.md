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
  `2022-01-01T00:00:00Z → 2023-12-17T12:00:00Z`, frozen 3-symbol set
  BTCUSDT / ETHUSDT / SOLUSDT, 4H timeframe.
- Single-venue (Bitget) evidence: all five C7 gate conditions pass.
  Independent post-C7 review verdict: PASS (see
  `research/signal_observation/SETUP_C_C7_POST_REVIEW_DECISION.md`).
- Cross-venue replication on Binance USDT-M Futures: completed at
  `775d739` with decision **C7_PASS**, all five gate conditions
  independently satisfied. Cross-venue design lock written to reconcile
  governance:
  `docs/STAGE_54_SQ_C7_CROSS_VENUE_DESIGN_LOCK.md`.
- Cross-venue both-PASS math is supported (Bitget and Binance each
  independently pass the locked gate). Observational deltas: Binance
  dev-only vt-post-cost-moderate ≈ 25% of Bitget's; SOL concentration
  ~70% on Binance vs ~53% on Bitget. Not gate violations.
- Setup C remains research-only **PASS_CANDIDATE**. Escalation **HOLD**.
- Mode: paper trading only. **LIVE NO-GO**.

## 7. Next likely research gate

**Cross-venue decision record** (parallel to
`SETUP_C_C7_POST_REVIEW_DECISION.md`) covering Bitget + Binance
both-PASS, the Binance dev-magnitude divergence, the SOL concentration
delta, and the OKX-deferred status. Owner-only research decision; not
runtime, paper, trading, probe, or live readiness.

Recommended next research gate after the decision record:

- OKX C7 evidence if reachability is restored. OKX is authorized by the
  cross-venue design lock but currently **deferred / blocked**: every
  reachability probe from this host returned HTTP 403 Cloudflare error
  1010 (ASN-level block). The OKX bounded-pagination downloader exists at
  `research/signal_observation/okx_public_downloader.py` and tests pass,
  but no data can be fetched from this host. Lifting the block is a host
  / network change, not an in-repo code task.
- Otherwise: a **direction-call agreement diagnostic** comparing
  per-rebalance direction sign across Bitget and Binance over the locked
  expanded window. Observational only; no gate or readiness change.

No paper, runtime, trading, probe, or live readiness is authorized by
either branch of the next gate.

## 8. Explicit no-readiness rule

`C7_PASS` is research evidence only. It does not authorize paper trading,
runtime wiring, trading readiness, probe readiness, or live readiness. Per
the design lock §"What C7 Does Not Authorize", promotion to any paper /
runtime / probe / trading / live lane requires a separate explicit Human
Owner decision recorded in repo docs and supported by additional gates.
LIVE remains **NO-GO** until that explicit decision exists.
