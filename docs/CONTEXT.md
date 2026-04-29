# Hephaestus Context

## Project

- Name: Hephaestus
- Type: Python async microservice trading system
- Current mode: paper trading only
- Live trading: forbidden until Stage 53 live blockers are closed

## Current runtime status

- Local paper runtime: GO
- VPS paper runtime: GO
- VPS provider: Beget
- VPS OS: Ubuntu 24.04
- VPS IP: 45.145.5.254
- Python: 3.12.3
- Docker: 29.4.1
- Services: 9 healthy
- Tests: HEAD 189cb0a PASS for mocked/local B2c.1a authenticated-readiness hardening only; server_time no-flag latch LASTEXITCODE=3; wallet_balance no-flag latch LASTEXITCODE=3; tests/scripts 40 passed; tests/libs/exchange 86 passed; tests/libs/config 19 passed
- Alembic head: 0008
- execution-service: ready, mode=paper

## Stage 53-A result

- Stage 53-A: CLOSED
- Commit: 3b3b06f feat: add Bybit public market data adapter
- Tests added: 39 (Stage 53-A mocked unit tests)
- Total tests: 250 passed, 5 warnings
- Public read-only smoke: PASS (live Bybit API, BTC-USDT/linear)

## Stage 53-B design lock result

- Stage 53-B design lock: CLOSED
- Commit: 5e5eb48 docs: add stage 53-B design lock
- Owner decisions: ANSWERED / APPROVED
- Runtime/client implementation: B2a server_time smoke harness accepted/pushed/remote-visible at a511e2f; B2b real server_time smoke succeeded locally with LASTEXITCODE=0 and elapsed_ms=1534; B2c wallet_balance smoke harness accepted/pushed/remote-visible at c9b1337 with mocked tests only; B2c.1a authenticated readiness hardening accepted/pushed/remote-visible at 189cb0a with mocked/local tests only; no runtime/service wiring; no real wallet_balance/open_positions smoke; no order_status or write/live methods

## Q1 fix and regression status

- Q1-FIX-1 recover_position payload validation: MERGED
- Q1-FIX-2 freshness naive datetime handling: MERGED
- Q1-FIX-3 true EMA in snapshot builder: MERGED
- Regression gate: PASS on main 1bd8e2a; B1-CONFIG green at c17c7d0; Slice 1 mocked server-time skeleton tests green at 828b64a; Slice 2 mocked wallet_balance tests green at 66a898d; Slice 3 mocked open_positions tests green at 0596afb; B2a mocked server_time smoke harness tests green at a511e2f
- Results:
  - python -m pytest tests\libs\config -q: 19 passed
  - python -m pytest tests\libs\exchange -q: 39 passed
  - python -m pytest apps/market_data/tests -q: 8 passed
  - python -m pytest apps -q: 163 passed
  - python -m pytest -q --ignore=./research --basetemp=.pytest_tmp: 288 passed, 5 warnings
- No secrets observed.
- No live/exchange/private endpoints/orders/cancels/balances/live execution/live reconcile were enabled or observed.
- Slice 1 evidence:
  - python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 28 passed
  - python -m pytest tests\libs\exchange -q: 67 passed
- Slice 2 evidence:
  - python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 33 passed
  - python -m pytest tests\libs\exchange -q: 72 passed
  - python -m pytest tests\libs\config -q: 19 passed
- Slice 3 evidence:
  - python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 39 passed
  - python -m pytest tests\libs\exchange -q: 78 passed
  - python -m pytest tests\libs\config -q: 19 passed
- B2a evidence:
  - python scripts\smoke_server_time.py: LASTEXITCODE=3 with sanitized authorization_required JSON
  - python -m pytest tests\scripts\test_smoke_server_time.py -q --basetemp=.pytest-temp-run: 14 passed
  - python -m pytest tests\libs\exchange -q: 78 passed
  - python -m pytest tests\libs\config -q: 19 passed
- B2b evidence:
  - Human Owner executed exactly one real Bybit testnet server_time smoke locally after safe credential presence and hygiene checks
  - python scripts\smoke_server_time.py --allow-real-smoke: LASTEXITCODE=0; elapsed_ms=1534; sanitized output only
  - No wallet_balance smoke, open_positions smoke, order_status, write/live methods, or service wiring was run
- B2c evidence:
  - c9b1337 feat: add Stage 53-B2 wallet-balance smoke harness
  - Added scripts/smoke_wallet_balance.py and tests/scripts/test_smoke_wallet_balance.py
  - wallet_balance smoke harness exists with mocked tests only
  - direct no-flag latch exits 3 with authorization_required JSON
  - --allow-real-smoke is required for the real-capable path
  - mocked success output is sanitized and includes only endpoint/status/exchange/account_type/coins_count/elapsed_ms
  - tests/scripts/test_smoke_wallet_balance.py: 14 passed; tests/scripts: 28 passed; tests/libs/exchange: 78 passed; tests/libs/config: 19 passed after clearing BYBIT_B1 env vars
  - Operational hygiene lesson: config suite initially failed because real BYBIT_B1 env vars from B2b smoke were still present; after clearing env vars it passed, not a B2c code failure
- B2c.1a evidence:
  - 189cb0a feat: harden Stage 53-B2 authenticated smoke readiness
  - server_time now uses unsigned public /v5/market/time methodology
  - get_server_time no longer requires credentials
  - private reads still fail closed without credentials
  - private signed reads include X-BAPI-SIGN-TYPE: 2
  - signed GET query handling is deterministic and consistent with what is sent
  - wallet_balance signs/sends accountType=UNIFIED
  - safe retCode classifications added for 10002 timestamp_or_recv_window_error, 10003 invalid_key_or_environment, 10004 invalid_signature, 10005 permission_denied, 10006 rate_limited, 10007 authentication_failed, and 10010 ip_mismatch
  - 10006 remains exit code 2 / inconclusive in smoke harnesses
  - no raw retMsg or raw response body exposure
  - wallet smoke output remains sanitized
  - server_time no-flag latch LASTEXITCODE=3; wallet_balance no-flag latch LASTEXITCODE=3
  - tests/scripts: 40 passed; tests/libs/exchange: 86 passed; tests/libs/config: 19 passed
  - no query-api support, open_positions smoke, order_status, write/live methods, service wiring, runtime readiness, trading readiness, live readiness, or probe readiness was added
- B2c.1 required next gate:
  - authenticated readiness audit / query-api preflight decision before B2d
  - not real wallet smoke; must not call wallet_balance or open_positions
  - does not authorize order_status or write/live methods
  - must audit signing/query-string behavior, signed vs unsigned server_time, X-BAPI-SIGN-TYPE: 2, safe retCode classification, key active/not expired wording, and whether to add /v5/user/query-api
  - query-api is not currently in B1/B2 endpoint set and requires explicit Human Owner decision; if authorized, it is read-only preflight only
  - /v5/market/time is public and should be treated as unsigned connectivity/time; B2b remains valid, but signed server_time usage should be tracked as audit/backlog issue if present

## Current stage

- Current gate: Stage 53-B2c.1a authenticated readiness hardening checkpoint
- Status: owner decisions OI-1..OI-9 ANSWERED / APPROVED; B1-CONFIG config-only slice complete on c17c7d0; Slice 1 accepted/pushed at 828b64a; Slice 2 accepted/pushed at 66a898d; Slice 3 accepted/pushed/remote-visible at 0596afb; B2a accepted/pushed/remote-visible at a511e2f; B2b server_time smoke succeeded locally; B2c wallet_balance smoke harness accepted/pushed/remote-visible at c9b1337; B2c.1a authenticated readiness hardening accepted/pushed/remote-visible at 189cb0a; B2d real wallet_balance smoke NO-GO pending Human Owner decision
- Stage 53-B1 architecture plan: docs/STAGE_53B1_ARCHITECTURE.md
- Stage 53-B1 implementation owner inputs B1-OI-1..B1-OI-6: ANSWERED / APPROVED
- Next allowed task: Stage 53-B2 docs/status cleanup and static safety checks; B2c.1 authenticated readiness audit / query-api preflight decision. B2d real wallet_balance smoke, open_positions smoke, order_status, or any write/live implementation requires separate approval
- Live trading: NO-GO
- Stage 53-B1 first implementation scope: Bybit testnet authenticated read-only server time/connectivity, wallet balance, and open positions only; order status deferred; no place order; no cancel order; no set_leverage; no live reconcile
- B1-CONFIG scope already present: config-only settings; no client, no private API calls, no service startup wiring, no runtime behavior change
- Slice 1 scope already present: Bybit auth/signing helper; timestamp / recv_window handling; redaction helpers; minimal ServerTime model; read-only client skeleton; get_server_time() only; mocked tests; not runtime-ready
- Slice 2 scope already present: get_wallet_balance(); wallet balance read-only models; Decimal numeric values; redacted repr() / model_dump(); sanitized wallet errors; mocked tests; not runtime-ready
- Slice 3 scope already present: get_open_positions(); open-position read-only models; Decimal numeric values; redacted repr() / model_dump(); sanitized open-position errors; mocked tests; not runtime-ready
- B2a scope already present: server_time smoke harness; mocked tests; direct no-flag latch exits 3 with authorization_required JSON; not runtime-ready
- B2b scope already completed: real testnet server_time smoke succeeded locally; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only; credentials were used locally only and must not be stored or disclosed; not runtime-ready
- B2c scope already present: wallet_balance smoke harness; mocked tests only; direct no-flag latch exits 3 with authorization_required JSON; --allow-real-smoke required; sanitized mocked success output only; no real wallet_balance smoke or credentials use for B2c implementation; not runtime-ready
- B2c.1a scope already present: unsigned public server_time methodology; get_server_time no longer requires credentials; private reads fail closed without credentials; signed private reads include X-BAPI-SIGN-TYPE: 2; deterministic signed/sent GET query handling; wallet_balance signs/sends accountType=UNIFIED; safe retCode categories for 10002/10003/10004/10005/10006/10007/10010; no query-api, open_positions smoke, order_status, write/live methods, service wiring, or readiness approval; not runtime-ready
- Current authorized state: READ_ONLY_TESTNET_SMOKE. Future READ_ONLY_ACTIVE / READ_ONLY_DEGRADED / READ_ONLY_HALTED, OMS, reconciliation, kill switch, risk controls, runbook, write client, ExchangePort refactor, dependency changes, CI secret scanning, and service wiring remain future-gate/backlog concepts only
- Withdrawal permission: forbidden
- Secrets: no secrets in repo, prompts, docs, or logs

## Current forbidden scope

- No API keys in repo, prompts, docs, logs, or committed fixtures
- No further real Bybit connectivity or real credential use without separate Human Owner authorization
- No further real smoke execution without separate Human Owner authorization
- No orders
- No cancels
- No balance runtime verification or real account balance use
- No positions runtime verification or real account position use
- No real wallet_balance smoke or open_positions smoke without separate Human Owner authorization
- No B2d real wallet_balance smoke before B2c.1 authenticated readiness audit / query-api preflight decision
- No order_status
- No write/live methods without separate Human Owner authorization
- No live execution
- No service startup wiring
- No Event Bus implementation
- No Redis Pub/Sub implementation
- No strategy quality filters in Stage 53

## Current architecture docs

- docs/PROGRESS.md
- docs/HOW_WE_WORK.md
- docs/AI_COMMANDS.md
- docs/AI_HANDOFF.md
- docs/STAGE_53_DESIGN_LOCK.md
- docs/STAGE_53B_DESIGN_LOCK.md
- docs/STAGE_53B1_ARCHITECTURE.md
- docs/architecture/STATE_AND_EVENTS_DRAFT.md
- docs/architecture/SERVICE_OWNERSHIP.md
- docs/architecture/INTERACTION_MODEL.md

## Agent roles

- GPT: senior architect / final reviewer
- Claude: independent reviewer
- Claude Code / Codex: executor
- All agents use the 3-lane operating model in docs/HOW_WE_WORK.md: Fast Lane, Standard Lane, Protected Lane
- Human Owner keeps final authority for accept/reject, START/HOLD, GO/NO-GO, stage transitions, and risk acceptance
- Commit only after explicit Human Owner instruction
- Every agent report must identify Agent, Task Type, Scope, Lane, Changed Files, Commands Run, Readiness Claims, Not Verified, and Decision Needed
