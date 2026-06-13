# Hephaestus — Claude Code Startup Guide

## Quick Orientation

**Project:** Hephaestus — Python async microservice crypto trading system  
**Mode:** Paper trading only  
**Live trading:** NO-GO  
**VPS:** Beget, Ubuntu 24.04, 9 services healthy  
**Python:** 3.12.3 | **Alembic head:** 0008

## Source of Truth (read in this order)

1. `docs/CURRENT_STATE.md` — current gate, allowed work, recent commits
2. `docs/BOUNDARIES.md` — hard safety constraints (canonical)
3. Recent git commits — actual repo state
4. `research/signal_observation/RESEARCH_STATE.md` — research track status
5. `docs/archive/AGENT_PROMPTS.md` — role-specific startup prompts
6. Historical docs (`PROGRESS.md`, `STAGE_STATUS.md`) — **ARCHIVED**, use only if `CURRENT_STATE.md` is missing or conflicting

**Rule:** Code beats docs for actual behavior. GitHub merged docs beat project memory. Report conflicts before acting.

## Current Gate (as of last CURRENT_STATE.md update)

- **Exchange track:** Stage 54-BG / Bitget Demo planning (docs-only)
- **Research track:** Setup E / Post-Liquidation Exhaustion Reversal — source access blocked (Hyperliquid / The Graph free plan restriction)
- **Setup C:** Parked after DR1 Binance recent rerun LOW result
- **Bybit Stage 53-B2c.1c / B2d:** Blocked — usable testnet credentials unavailable

## Pipeline

```
signal_engine → risk_engine → review_gateway → orchestrator → execution_service → position_manager
```

Authority boundaries (must not change without explicit architectural decision):
- `risk_engine` decides admissibility
- `review_gateway` does not recompute risk
- `orchestrator` cannot bypass risk or kill switch
- `execution_service` makes no strategic decisions

## Tech Stack

- **Services:** 9 FastAPI services (paper mode)
- **DB:** PostgreSQL + SQLAlchemy v2 + Alembic (8 tables)
- **Auth:** 3-tier tokens — INTERNAL_SERVICE_TOKEN, OPERATOR_TOKEN, ADMIN_TOKEN
- **Exchange clients:** Bybit read-only skeleton (mocked tests only), Bitget public skeleton + signing helper (mocked tests only)
- **AI models:** GPT-5.4-thinking (orchestrator), Claude Sonnet (signal_reasoning, review, journal_review), Claude Haiku (alerts)
- **Config:** `config/system.yaml`, `config/models.yaml`, `config/risk.yaml`, `config/exchange.yaml`, `config/strategy.yaml`, `config/feature_flags.yaml`

## 8 Database Tables

`journal_events`, `system_state`, `trade_candidates`, `operator_actions`, `positions`, `position_events`, `incidents`, `executions`

## Operating Lanes

| Lane | When to use |
|---|---|
| **Fast Lane** | docs-only, report-only, typo/status cleanup — no code/test/config changes |
| **Standard Lane** | approved focused code/test/docs work not touching Protected criteria |
| **Protected Lane** | exchange clients, secrets, orders, live execution, migrations, runtime wiring, service startup, safety authority — requires explicit Owner authorization |

## Forbidden Without Explicit Owner Approval

- Private exchange API calls (any exchange)
- Secrets, API keys, account IDs, signed payloads in repo/docs/logs
- Orders, cancels, set_leverage, withdraw, transfer
- Live execution, live reconcile, probe readiness
- Runtime/service wiring changes
- Real smoke scripts execution
- Generic exchange adapter creation
- Readiness promotion by inference

## Environment (Windows PowerShell)

```powershell
# Command separator: ; not &&
# Always use module invocation:
python -m pytest
python -m alembic
python -m uvicorn

# Project path: E:\trading-system
# Env vars: Process scope only, never Machine scope
```

## Verify After Every Change

```powershell
# After file edit:
Get-Content <file>
Select-String <file> '<key>'

# After service start:
Invoke-RestMethod http://127.0.0.1:<port>/health

# After migration:
python -m alembic current

# After tests:
# Show full: N passed, N warnings
```

## Test Baseline (last known good)

```powershell
python -m pytest tests\libs\config -q         # 19 passed
python -m pytest tests\libs\exchange -q       # 122+ passed
python -m pytest apps -q                      # 163+ passed
python -m pytest -q --ignore=./research       # 408 passed, 5 warnings
```

## Agent Report Format (required)

Every agent report must include:
1. Agent
2. Task Type
3. Scope
4. Lane
5. Changed Files
6. Commands Run
7. Readiness Claims (separate docs/code/test/runtime)
8. Not Verified
9. Decision Needed (use `None` only when no owner decision is needed)

## Key Docs Map

| Topic | File |
|---|---|
| Current state | `docs/CURRENT_STATE.md` |
| Safety boundaries | `docs/BOUNDARIES.md` |
| Working protocol | `docs/HOW_WE_WORK.md` |
| Agent prompts | `docs/archive/AGENT_PROMPTS.md` |
| Stage 53 design lock | `docs/archive/STAGE_53_DESIGN_LOCK.md` |
| Bitget BG2 design lock | `docs/archive/STAGE_54_BG2_DESIGN_LOCK.md` |
| Operator runbook | `docs/OPERATOR_RUNBOOK.md` |
| Research state | `research/signal_observation/RESEARCH_STATE.md` |

## What Must Not Change (invariants)

- Authority rules
- Pipeline order (signal_engine → … → position_manager)
- `RiskDecision.entry_price` = midpoint of entry_zone
- Advisory vs authoritative separation (LLM outputs are advisory only)
- Redis must never be source of truth for execution/candidate/kill switch state

## Source of Truth by Domain

| Domain | Source | Service |
|---|---|---|
| entry_price | RiskDecision | risk_engine |
| kill switch | system_state table | kill_switch |
| execution state | executions table | execution_service |
| position state | positions table | position_manager |
| operator approvals | operator_actions table | orchestrator |
| market freshness | market_data | market_data |
