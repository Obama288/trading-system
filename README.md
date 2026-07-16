# Hephaestus

Status: ACTIVE / ENTRY POINT

Hephaestus is a paper-only crypto trading research and execution system. Its
economic objective is repeatable net trading profit after costs and risk.

The project does not currently claim a proven trading edge or runtime
readiness. Live trading is NO-GO.

## Start Here

Read in order:

1. [Current state](docs/CURRENT_STATE.md) - objective, owner constraints,
   current gate, blockers, readiness, and allowed next work.
2. [Boundaries](docs/BOUNDARIES.md) - hard safety constraints.
3. [How we work](docs/HOW_WE_WORK.md) - working protocol and verification.
4. [Research state](research/signal_observation/RESEARCH_STATE.md) - compact
   research gate and family verdicts.
5. [Documentation index](docs/README.md) - full documentation map.

Do not start from archived progress reports or chat memory.

## Current Operating Constraint

No new project spending is authorized: no paid data, paid APIs, subscriptions,
or infrastructure upgrades without a new explicit Human Owner decision.
Preparation prioritizes correctness and reproducibility over speed.

## Repository Checks

```powershell
git status --short --branch
python -m pytest tests\test_project_memory.py -q
python -m alembic heads
```

The full test suite and runtime have separate readiness states; consult the
current-state document before making claims.

## Safety

Without explicit Protected Lane authorization, do not:

- call private exchange endpoints;
- place or cancel orders;
- handle real balances or signed payloads;
- change risk, kill switch, execution, position, migration, deployment, or
  runtime authority;
- promote paper, runtime, trading, probe, or live readiness.

Project-memory rules: [memory policy](docs/MEMORY_POLICY.md).
