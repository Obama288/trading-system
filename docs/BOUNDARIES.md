# Hephaestus - Boundaries

Purpose: compact safety boundary entry point. This file does not replace
`docs/PROGRESS.md`; it summarizes current hard limits for routine agent startup.

## Source Rules

- GitHub merged docs, latest commits, actual code, tests, and relevant PR
  metadata are primary project sources.
- Project memory is orientation only.
- Code beats docs for actual implemented behavior.
- `docs/PROGRESS.md` wins if status docs conflict.
- Report conflicts before implementation.

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
