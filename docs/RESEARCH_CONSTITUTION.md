# Research Constitution — Edge Discovery Pipeline

Status: v1.3 — ADOPTED 2026-06-13 (default baseline seed 69). v1.2 explicit baseline seed at lock; cumulative comparison budget. v1.1 Stage 5 hardening; v1.0 base.
Scope: governs all edge research in this repository. Supersedes per-family ad-hoc
process. Existing decision records (Setup A/B/C) remain valid history.
Location when adopted: `docs/RESEARCH_CONSTITUTION.md`

Rule zero: if a section of this document does not change a promote/kill decision,
it must be deleted. This document stays under ~3 pages or it has failed.

---

## 1. Pipeline stages and gates

Every idea moves through these stages in order. No stage may be skipped.
Failing a gate parks or retires the family; restart requires a NEW pre-registration.

### Stage 0 — Idea generation
- Sources: hypothesis_agent output, manual observation, literature, post-mortems.
- Output: an entry in `RESEARCH_CANDIDATE_BACKLOG.md` with a one-paragraph
  mechanism statement (see 2.1).
- HARD RULE: Stage 0 produces candidates, never evidence. No win rates,
  no confidence labels, no "edge found" language in alerts or docs.

### Stage 1 — Pre-registration
- A pre-registration document (template in section 2) is written and committed
  BEFORE any analysis run on the discovery window.
- Feasibility-only data inspection is allowed (does the data exist, coverage,
  quality) — outcome metrics are not.
- Gate to Stage 2: pre-registration committed; data quality report (section 5)
  passes for all required datasets.

### Stage 2 — Discovery
- Run on the locked discovery window only.
- Gate to Stage 3: primary metric (post-cost, moderate scenario) exceeds the
  pre-registered threshold AND exceeds the random baseline by the pre-registered
  margin, at N ≥ the pre-registered minimum.

### Stage 3 — Validation
- Run once on the locked validation window. The validation window is touched
  exactly once per pre-registration. A second look = new pre-registration.
- Gate to Stage 4: post-cost expectancy non-negative, effect direction
  consistent with discovery, N ≥ pre-registered minimum.

### Stage 4 — Recent-data rerun
- Mandatory. Window: most recent data available at run time, length fixed at
  pre-registration (default: last 12 months).
- Rationale: Setup C passed locked 2022–2023 windows and failed recent data
  (DR1 LOW). This filter is permanent.
- Gate to Stage 5: post-cost expectancy non-negative on recent window; no
  pre-registered red flag triggered.

### Stage 5 — Paper
- Entry requires: owner sign-off + frozen detector code (tag/commit hash in the
  decision record) + execution audit passed on the frozen commit
  (docs/SYSTEM_MAP_AND_RISK_REGISTER.md §5 checklist) + runner logs its commit
  hash at startup and refuses to trade if it differs from the decision record
  (runtime hash check).
- Kill criteria fixed at entry, defaults:
  - expectancy after 30 paper trades below −0.15R → kill;
  - peak-to-trough drawdown ≥ 10R → kill;
  - 90 calendar days without reaching 30 trades → review (likely kill: signal
    too rare to matter).
- Paper results cannot "improve" a hypothesis. Any parameter change → back to
  Stage 1.

### Stage 6 — Live
- Owner decision. Out of scope for this document beyond: live is never entered
  from any stage other than a completed Stage 5.

---

## 2. Pre-registration template

Each item is mandatory. Copy into `<FAMILY>_PREREGISTRATION.md`.

### 2.1 Hypothesis and mechanism
- One sentence: what is predicted to happen and when.
- Mechanism: WHO is on the other side of this trade and why do they
  systematically lose to us (forced flows, liquidations, funding pressure,
  rebalancing, attention constraints)? "The pattern worked historically" is not
  a mechanism. No credible mechanism → idea stays in Stage 0.

### 2.2 Primary metric and gate
- Exactly one primary metric (default: post-cost expectancy in R, moderate
  cost scenario).
- Numeric pass threshold, written before any run.
- Everything else (sessions, hours, regimes, MFE/MAE, sensitivity lookbacks)
  is diagnostic-only and cannot promote a hypothesis.

### 2.3 Windows
- Discovery window: [start, end], locked.
- Validation window: [start, end], locked, non-overlapping with discovery.
- Recent-rerun length (default 12 months).
- Pre-registration records the SHA-256 of each dataset file in the locked
  windows; quality reports bind to that file hash.

### 2.4 Random baseline
- Specification of the baseline (e.g., same entry timestamps with shuffled
  direction; or random entries matched on symbol/regime), the exact integer
  random seed value (fixed and written here at lock, not at first run), number
  of resamples, and the required margin over baseline. Default seed value is 69
  unless a family records a different integer at lock; this keeps baselines
  reproducible without requiring a per-family choice.

### 2.5 Multiple-testing budget
- List every variant that will be examined: symbols × timeframes × parameter
  values × regime splits × session splits. Compute V = total variant count.
- The primary gate threshold applies to ONE pre-named primary variant.
- Any non-primary variant may be promoted only via a new pre-registration in
  which it is the primary — and its discovery evidence is treated as Stage 0
  material (it was selected post-hoc out of V looks).
- The comparison budget is cumulative across a research campaign, not
  per-document: each additional locked pre-registration on the same data class
  adds to the total independent looks. A candidate that clears its gate after
  many prior families failed must be read in light of that cumulative count,
  not in isolation.

### 2.6 Sample size minimums
- Defaults: discovery N ≥ 80, validation N ≥ 40, counted as non-overlapping
  observations (section 4.6). Families may pre-register different minimums
  with written justification, but only before any run.

### 2.7 Kill criteria
- Conditions under which the family is retired at each stage, including the
  Stage 5 defaults above (overridable, in writing, before entry).

---

## 3. Simulator contract (single source of truth)

One outcome simulator serves all families. setup_a/setup_b/hypothesis_agent
implementations are migrated to it; per-family simulators are deleted.
Decisions below are binding; changing one requires a constitution amendment
and a rerun of any evidence that depended on it.

### 3.1 Time convention
- `Candle.timestamp` = bar OPEN time (matches Binance/OKX/Bitget raw data).
- `decision_time` = bar CLOSE time = open time + bar duration.
- All session labels, signal-hour fields, and weekday fields are computed from
  `decision_time`, never from open time.

### 3.2 Entry
- Default entry: OPEN of the bar following the signal bar
  (`entry_time = decision_time` of the signal bar; `entry_price = next bar open`).
- Rationale: filling at the signal bar's close assumes execution at the exact
  price that defines the signal — systematically optimistic. Next-bar-open is
  reproducible live.
- Signal-close fill may be recorded as a diagnostic column, never as the
  primary metric.

### 3.3 Outcome window
- Starts at the entry bar (the bar whose open is the entry price); its full
  high/low range counts. Window length in bars is pre-registered per family.

### 3.4 Intrabar ambiguity
- If stop and target are both reachable within one bar: stop is assumed hit
  first (conservative). Unchanged from current practice.

### 3.5 Gaps
- If a bar opens beyond the stop, the exit price is that bar's OPEN, and the
  realized loss is computed from it (may be worse than −1R). The −1R floor is
  abolished.

### 3.6 Costs
- Costs are specified in basis points of notional per side and converted to R
  per trade using that trade's actual initial_r distance.
- Rationale: a flat cost in R (e.g., 0.08R) understates costs for tight-stop
  setups — exactly the regime created by `min(percent_buffer, atr_buffer)`
  stops. Cost in R must grow as stops tighten.
- Default scenarios (per side, taker + slippage):
  optimistic 5 bps, moderate 8 bps, conservative 15 bps.
  Funding costs added where holding periods make them material (pre-registered).
- A zero-cost run is allowed only as an explicitly labeled diagnostic.

### 3.7 Flats and metrics
- `win_rate` = wins / resolved (stop-or-target) — diagnostic only.
- `expectancy_R` = mean final R over ALL observations, flats marked-to-market
  at window close, post-cost — this is the default primary metric.
- Gates are evaluated on expectancy, never on win rate alone.

### 3.8 Overlap
- Headline metrics use non-overlapping observations only: per symbol per
  family, a new observation cannot open while a prior one is unresolved.
- If a family genuinely requires overlapping samples, confidence intervals
  must come from block bootstrap, pre-registered.

---

## 4. Statistical standards

- 4.1 Random baseline is mandatory for every Stage 2 and Stage 3 run.
- 4.2 Session/hour/regime breakdowns are descriptive unless pre-registered as
  the primary variant. Reporting "best session" from a post-hoc max is banned.
- 4.3 Every evidence artifact reports: N, variant budget V from the
  pre-registration, window hashes/date ranges, simulator version, cost
  scenario, and random-baseline summary.
- 4.4 Surprising positive results trigger a look-ahead audit before
  celebration: re-verify pivot/indicator confirmation indices and entry-bar
  handling for that family.
- 4.5 No metric from an unclosed (live) candle ever enters analysis.
- 4.6 "Non-overlapping" means: observation i+1 entry bar index ≥ observation i
  resolution bar index, per symbol.

---

## 5. Data layer standard

Required before any Stage 2+ run; produced as a committed artifact next to the
dataset.

- Single ingestion contract for all venues: timestamp = open time, UTC,
  deduplicated, sorted, unclosed candles excluded (OKX `confirm` flag; for
  venues without a flag, drop the last bar if its close time > now).
- Quality report per dataset: bar-gap list, zero-volume bar count, OHLC sanity
  violations, date coverage vs requested window. Any gap inside a locked
  window must be acknowledged in the pre-registration or the window is moved.
- Known defect to fix before next acquisition: OKX history pagination must use
  `after` (records earlier than ts), not `before`.

---

## 6. Component roles

- `research/hypothesis_agent` — Stage 0 only. Its statistics module, confidence
  labels, and "performs best in session X" statements are removed or relabeled
  as candidate descriptions. It may not publish numbers computed by its own
  simulator once the unified simulator exists.
- `research/signal_observation` — Stages 2–4 engine.
- `ops/paper_pipeline_runner` + paper services — Stage 5.
- Decision records and design locks — unchanged, now required at every gate.

---

## 7. Owner decision record — 2026-06-12

1. Entry convention (3.2): next-bar-open. ADOPTED as written.
2. Cost scenarios (3.6): moderate = 8 bps per side (standard taker);
   optimistic 5, conservative 15. ADOPTED as written.
3. Sample minimums (2.6): discovery ≥ 80, validation ≥ 40. ADOPTED as written.
4. Stage 5 kill-criteria defaults: −0.15R after 30 trades / 10R drawdown /
   90 days. ADOPTED as written. Rationale: ≈10–15% false-kill probability for
   a true +0.10R edge vs bounded time spent on dead strategies. Overridable
   per family at pre-registration only.
5. Stage 4 recent-rerun default length: 12 months. ADOPTED as written.
6. Stage 5 hardening (v1.1 amendment): execution audit (SYSTEM_MAP §5 checklist)
   + runtime hash check + dataset SHA-256 binding are required at Stage 5 entry.
   ADOPTED 2026-06-13.

## 7. Amendment v1.2 (2026-06-13): §2.4 integer seed at lock; §2.5 cumulative comparison budget.

## 7. Amendment v1.3 (2026-06-13): default baseline seed = 69 unless overridden at lock.
