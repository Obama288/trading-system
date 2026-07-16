# Signal Observation Research State

Status: ACTIVE / STATE

Governing law: `docs/RESEARCH_CONSTITUTION.md` and `docs/BOUNDARIES.md`.
Project objective and owner constraints: `docs/CURRENT_STATE.md`.

## Research Objective

Find a repeatable, cost-aware trading edge that can plausibly contribute to net
trading profit. Research is useful only when it reduces uncertainty about that economic
objective.

No current family has sufficient evidence for trading or paper-candidate
promotion. This does not remove the profit objective; it prevents unsupported
claims and wasted capital.

## Current Gate

- Active family: none.
- Current candidate: Setup I / Price-Flow Divergence Reversion.
- Setup I status: DRAFT / feasibility candidate only.
- Screening, analysis, validation, data acquisition, and paper progression:
  not authorized by this file.
- Paid data and paid source upgrades: not allowed under the current owner
  constraint.

## Setup I Preconditions

Before any Setup I data inspection or run:

1. Finalize a mechanism-first preregistration with a named counterparty and a
   plausible post-cost effect.
2. Confirm a free data path and a non-overlapping held-out path before looking
   at candidate-relevant history.
3. Lock universe, interval, event definition, cost model, baseline, seed,
   multiplicity budget, and STOP/PARK rule.
4. Independently review look-ahead and selection-contamination risk.
5. Obtain a separate owner authorization for the bounded run.

Current draft: `research/signal_observation/SETUP_I_PREREGISTRATION.md`.
Local untracked Setup I scripts are not repo evidence or authorization.

## Family Verdicts

| Family | Current verdict | Meaning |
|---|---|---|
| Setup A / breakout-retest | RETIRED | Price-action continuation attempt; do not reopen without a new family decision. |
| Setup B / pullback continuation | RETIRED | Cost/robustness evidence insufficient. |
| Setup C / TSMOM volatility-targeted | PARKED | Historical C7 evidence existed, but recent DR1 Binance rerun was LOW. No paper lane. |
| Setup D / funding carry-stress | HOLD | Historical acquisition exists; interval policy and a new analysis gate would be required. |
| Setup E / post-liquidation reversal | PARKED | Stage 2 expectancy failed the locked gate. |
| Setup F / basis | FEASIBILITY NOTE ONLY | No active research authorization. |
| Setup G / options | NEEDS PAID DATA | Ineligible under current no-spend constraint. |
| Setup H / regime-gated TSMOM | PARKED | Stage 2 gate failed; regime gate hurt the result. |
| Setup I / price-flow divergence | DRAFT | Candidate for a future bounded free-data feasibility decision. |

## Evidence Summary

- Setup C: cross-venue C7 results are historical research evidence only. The
  later recent-data DR1 result was LOW, so the family is parked.
- Setup E: locked Stage 2 result was negative and below its baseline gate; the
  family is parked.
- Setup H: gated expectancy and shuffled-percentile requirements failed; the
  family is parked.
- Funding normalization BTC/ETH: discovery screen was weak and validation was
  not opened. Broader-pair work is not active.
- E1 paid-plan/source-access work is not a next action under the current owner
  constraint.

## Research Integrity Constraints

- Preserve a held-out source/window before EXPLORE or feasibility inspection.
- No post-hoc split of an inspected window into discovery and validation.
- No timeframe, source, universe, or segmentation changes after seeing a
  result without a new preregistration and owner decision.
- Public studies and third-party statistics may support a mechanism but are not
  internal evidence.
- Manual chart review is qualitative pre-triage only.
- Use the canonical simulator in `research/simcore/` for formal trade outcomes.
- Track cumulative same-family attempts and comparison budget.
- A PASS is evidence, not proof and not readiness.

## Free-Path Policy

Research should use committed local data or genuinely free public paths while
respecting contamination and held-out constraints. "Free" must include the real
operational cost: download size, storage, rate limits, implementation time, and
realistic execution costs.

No paid API key, hosted plan, requester-pays dataset, VPS upgrade, or data
purchase is a current next action.

## Next Decision

After project-memory and repository-baseline cleanup, decide whether Setup I
has a valid free, contamination-safe feasibility path. If any prerequisite is
missing, PARK it without rescue variants. If all prerequisites are explicit,
prepare one bounded owner decision; do not run it by implication.

## Detailed Evidence Pointers

- Constitution: `docs/RESEARCH_CONSTITUTION.md`
- Candidate backlog: `research/signal_observation/RESEARCH_CANDIDATE_BACKLOG.md`
- Setup I draft: `research/signal_observation/SETUP_I_PREREGISTRATION.md`
- Setup C final recent decision:
  `research/signal_observation/SETUP_C_DR1_BINANCE_RECENT_RERUN_POST_RESULT_DECISION.md`
- Setup E decision: `research/signal_observation/SETUP_E_DECISION_RECORD.md`
- Setup H result: `research/signal_observation/SETUP_H_DISCOVERY_RESULT.md`
- Historical design locks and gates: `docs/archive/`

Detailed chronology belongs in Git and the linked decision/result artifacts,
not in this compact state file.
