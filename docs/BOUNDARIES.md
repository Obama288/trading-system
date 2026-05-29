# Hephaestus - Boundaries

Purpose: compact safety boundary entry point. Canonical for hard constraints.
`docs/CURRENT_STATE.md` is the current state entry point.
`docs/PROGRESS.md` is ARCHIVED historical context; it does not override current state.

## Source Rules

- GitHub merged docs, latest commits, actual code, tests, and relevant PR
  metadata are primary project sources.
- Project memory is orientation only.
- Code beats docs for actual implemented behavior.
- `docs/CURRENT_STATE.md` is the current state entry point for all agents.
  `docs/BOUNDARIES.md` is canonical for hard constraints.
  If they conflict, report to Owner before acting.
- `docs/PROGRESS.md` is ARCHIVED and does not override `docs/CURRENT_STATE.md`.
- Report conflicts before implementation.

## Document Lifecycle Taxonomy

Every project document carries one of the following statuses. Documents without
an explicit status must not be assumed current if contradicted by
`docs/CURRENT_STATE.md`.

- **ACTIVE** — current, authoritative, and in use for the gate it governs.
- **PARKED** — deliberately deferred; may be reopened by explicit Owner decision.
- **RETIRED** — approach abandoned; do not reopen without a new design lock.
- **SUPERSEDED** — replaced by a later decision or track; historical record only.
- **HISTORICAL** — part of a completed or closed stage; not active next work.
- **ARCHIVED** — retained for orientation only; not authoritative for current
  state, gates, readiness, or next actions.

## Current Safety State

- Mode: paper trading only.
- Live trading: NO-GO.
- Runtime, trading, probe, paper-execution, and live readiness must not be
  promoted by inference.
- Human Owner has final authority for stage transitions, GO/NO-GO, risk
  acceptance, and readiness approval.

## Forbidden Without Explicit Owner Approval

- Private exchange endpoint calls.
- API keys, secrets, account IDs, balances, signed payloads, private endpoint
  data, key prefixes/suffixes/hashes, or secret-derived values in repo/docs/logs.
- Orders, cancels, `set_leverage`, withdraw, transfer, live reconcile, or live
  execution.
- Runtime/service wiring, Event Bus, Redis Pub/Sub, generic exchange adapters,
  strategy filters, or broad rewrites.
- Real smoke/API access.
- Paper execution, live trading, probe readiness, runtime readiness, or trading
  readiness claims.

## Protected Areas

- `apps/**`
- `libs/**`
- `config/**`
- `infra/**`
- `alembic/**`
- `scripts/**`
- `pyproject.toml`
- `requirements*`
- `.env` and `.env.*`

## Serious Change Verification

Escalate verification for:

- runtime behavior;
- exchange/private endpoint/auth/signing behavior;
- config/env/secrets;
- service wiring;
- risk, execution, position, or kill-switch authority;
- schema or migrations;
- readiness claims;
- real smoke/API access;
- broad research logic or generated decision reports.

For serious changes, do not skip owner approval, scope review, targeted tests,
and docs/status alignment.

## Action Discipline

Before proposing work, classify it as:

- Required for current gate.
- Quality-critical.
- Useful but optional.
- Noise / defer.

Default: propose only Required or Quality-critical actions. Do not propose
Useful/Optional work unless it prevents a real near-term risk. Never propose
Noise.

## Hard Research Boundaries

These rules are hard constraints and apply to all agents and lanes.

- No EXPLORE may begin on a triage-cleared candidate unless a non-overlapping
  held-out source or path has been confirmed upfront before any data inspection
  begins. Stating that a held-out path "should exist" or "is plausible" is not
  sufficient; it must be identified and named.
- EXPLORE must not consume the only available contiguous window needed for later
  formal validation. If consuming the full window is unavoidable, Tower Control
  must present this tradeoff explicitly to the Human Owner and obtain approval
  before authorizing the EXPLORE.
- Post-hoc splitting of an EXPLORE-consumed window into discovery and validation
  segments is rejected.
- Existing public statistics, published signals, or third-party benchmark results
  may support or inform a hypothesis; they do not confirm edge for this project.
- Manual visual review of charts, signals, or output data is qualitative
  pre-triage only. It is non-evidence and non-validation. If manual review may
  influence candidate specification, threshold selection, or signal framing,
  explicit Owner authorization is required before it proceeds.
- After results are observed, changing the timeframe, source, coin universe, or
  segmentation criteria is goalpost movement and is not authorized. Any such
  change after observing results requires a new design lock, independent review,
  and explicit Owner approval before the new specification may be analyzed.
  Results from a changed specification must not be compared to or merged with
  results from the original specification to claim a combined finding.
