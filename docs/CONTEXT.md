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
- Runtime/client implementation: B2a server_time smoke harness accepted/pushed/remote-visible at a511e2f; B2b real server_time smoke succeeded locally with LASTEXITCODE=0 and elapsed_ms=1534; B2c wallet_balance smoke harness accepted/pushed/remote-visible at c9b1337 with mocked tests only; B2c.1a authenticated readiness hardening accepted/pushed/remote-visible at 189cb0a with mocked/local tests only; B2c.1b query-api read-only preflight harness accepted/pushed/remote-visible at 00d84d8 with mocked tests only; B2c.1c query-api real preflight attempted once and blocked with retCode=10003 invalid_key_or_environment; B2d real wallet_balance testnet smoke blocked due unavailable usable Bybit testnet API access; testnet API access runbook documented in docs/STAGE_53B2_SMOKE_PLAN.md; no runtime/service wiring; no open_positions smoke; no order_status or write/live methods
- Stage 54-BG planning: Bitget Demo / Simulated Trading is the primary candidate replacement track after the blocked Bybit private testnet path; begin with docs-only architecture planning, then `BitgetBg1Settings` plus mocked tests only
- Stage 54-BG proposed env namespace: `BITGET_BG1_ENVIRONMENT`, `BITGET_BG1_API_KEY`, `BITGET_BG1_API_SECRET`, `BITGET_BG1_PASSPHRASE`
- Stage 54-BG safety boundary: no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback in the first implementation; production/mainnet must fail closed by default; no private Bitget smoke before config, environment, and passphrase boundaries are locked
- Stage 54-BG2 design lock: DOCS-ONLY / DESIGN LOCK; Bitget Demo API planning only; future demo private REST requests must account for `paptrading: 1`; auth shape uses API key, secret key, and passphrase; private requests require signing; public endpoints stay separate from private/authenticated endpoints; WebSocket demo endpoints remain future/out of scope unless explicitly authorized
- Stage 54-BG2 safety boundary: no API/exchange/Beget/network operations; no private smoke; no orders/cancels/set_leverage/withdraw/transfer; no runtime/service wiring; no generic exchange adapter; no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback; `production` / `mainnet` / `live` / `testnet` remain fail-closed for the BG1/BG2 path
- Stage 54-BG2-A public-only skeleton: ACCEPTED / REMOTE-VISIBLE on `ad8df47`; public unsigned Bitget connectivity skeleton only; mocked tests only; no credentials, no `SecretStr`, no signing, no passphrase, no `paptrading` header, no private endpoints, no smoke script, no runtime/service wiring, no generic exchange adapter, and no real API/exchange/Beget/network operations
- Stage 54-BG2-A test evidence: `tests/libs/exchange/test_bitget_public.py` 8 passed and `tests/libs/exchange` 107 passed; readiness is code-ready/test-ready for public-only skeleton only; not runtime-ready, trading-ready, live-ready, or probe-ready
- Stage 54-BG2-B signing helper: ACCEPTED on `07cea3b`; Bitget-specific signing helper only; mocked tests only; deterministic payload uses timestamp + uppercased method + request path + optional query string + body; HMAC-SHA256 Base64 signature; required headers are `ACCESS-KEY`, `ACCESS-SIGN`, `ACCESS-TIMESTAMP`, `ACCESS-PASSPHRASE`, and `Content-Type: application/json`; no env reads; missing/empty credentials fail closed; redaction/safe repr prevents exposing api_key, api_secret, passphrase, or signature; no private client, no endpoint methods, no network calls, no `paptrading` header, no smoke script, no runtime/service wiring, and no generic exchange adapter
- Stage 54-BG2-B test evidence: `tests/libs/exchange/test_bitget_auth.py` 15 passed and `tests/libs/exchange` 122 passed; readiness is code-ready/test-ready for signing helper only; not runtime-ready, trading-ready, live-ready, or probe-ready
- Stage 54-BG2-C private read-only preflight runbook: DOCS-ONLY / PLANNING; candidate future endpoint is `GET /api/v3/account/info` for a private read-only preflight discussion only, not an approved call; future demo private requests must include explicit `paptrading: 1` marker handling; future private output must remain sanitized to high-level summaries only and must never expose raw uid, raw permissions, raw IPs, raw response body, raw error messages, API keys, secrets, passphrases, signatures, account IDs, balances, positions, or signed payloads
- Stage 54-BG2-C guardrails: safe env presence/hygiene checks required; no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback; `BITGET_BG1_` namespace only unless later owner-approved; fail closed if credentials are missing/empty, environment is not demo/simulated, permissions include trade/transfer/withdraw/write-like capability, response cannot prove safe read-only posture, or result is rate-limited/inconclusive; no automatic retry after a real preflight failure; no private client, no private smoke, no runtime wiring, and no real API/exchange/Beget/network operations are authorized
- Beget API access: AVAILABLE / OPERATIONAL CAPABILITY ONLY; no secrets recorded; does not imply deployment readiness or runtime readiness; any Beget API operation that changes infrastructure, deployment, runtime, secrets, or server state is Protected Lane and requires explicit Human Owner authorization
- Stage 54-AP fallback planning: Alpaca Paper remains fallback-only and must stay a separate architecture track; do not fold Alpaca into a crypto-CEX abstraction
- Generic adapter boundary: do not create a generic exchange adapter yet
- Pit-stop audit: audit-only checkpoint recorded; repo aligned at 8153c61; `.pytest-temp-run/` generated artifact removed; full local regression 408 passed / 5 warnings; targeted suites passed; no-flag server_time, wallet_balance, and query_api latches all exited 3; checked BYBIT env names were missing; no runtime/trading/live/probe readiness is claimed

## Historical stage groups

These groups preserve pre-Stage-43 chronology without renumbering official
stages. `docs/PROGRESS.md` remains the authoritative source for the current
stage and gate.

- Stage Group A - Architecture foundation: money-path, authority rules, service boundaries, deterministic control, advisory-only LLM boundary.
- Stage Group B - Paper trading core: signal, risk, review, orchestrator, paper execution, position manager, journal/audit flow.
- Stage Group C - Safety and authority hardening: kill-switch authority, DB source-of-truth rules, operator actions, idempotency, max_open_positions guard, fail-closed behavior.
- Stage Group D - Paper runtime validation: local paper runtime, VPS paper runtime, 9 services healthy, execution-service paper mode.
- Stage Group E - Quality and regression cleanup: Q1 audit backlog, recover_position payload validation, freshness datetime handling, true EMA, regression baseline.
- Stage Group F - Exchange-readiness preparation: Stage 53 design lock, Bybit public adapter, Bybit read-only/private-testnet planning, smoke harnesses, blocked Bybit B2 real private testnet path.

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
- B2c.1b evidence:
  - 00d84d8 feat: add Stage 53-B2 query-api preflight harness
  - get_query_api_info() supports signed read-only GET /v5/user/query-api
  - sanitized ApiKeyInfo model with boolean/status summary fields
  - scripts/smoke_query_api.py exists
  - no-flag latch exits 3 with sanitized authorization_required JSON
  - success output exact approved field set: endpoint, status, exchange, read_only, permissions_safe, key_active, deadline_days_present, expired_at_present, elapsed_ms
  - operation and endpoint_family are absent from success output
  - unsafe readOnly/permissions/expiry metadata fail closed
  - stale and malformed expiredAt regression tests exist
  - rate limit remains exit 2 / inconclusive
  - no real query-api execution, credentials use, Bybit call, real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, runtime readiness, trading readiness, live readiness, or probe readiness was added
- B2c.1c/B2d blocked-state evidence:
  - B2c.1c real query-api preflight was attempted once and failed safely with retCode=10003, error_category=invalid_key_or_environment, and LASTEXITCODE=1
  - likely cause is ordinary/mainnet Bybit key used against testnet API endpoint, or no usable Bybit testnet API access
  - no further query-api retry is authorized
  - B2d real wallet_balance testnet smoke is blocked / NO-GO because usable Bybit testnet API credentials are unavailable
  - ordinary/mainnet Bybit key must not be substituted into the testnet flow
  - any mainnet read-only smoke would require a new separately authorized stage, not continuation of B2d
  - runbook uses `https://testnet.bybit.com` and `https://testnet.bybit.com/app/user/api-management`; keys from ordinary Bybit mainnet / `www.bybit.com` must not be used in the B2 testnet flow
  - runbook requires API Transaction / Транзакция API, not third-party application binding; read-only only; withdrawal, transfer, trade/order/write disabled
  - environment shape is `BYBIT_B1_ENVIRONMENT=testnet`; `BYBIT_B1_API_KEY` and `BYBIT_B1_API_SECRET` from the same testnet key pair; generic `BYBIT_API_KEY` / `BYBIT_API_SECRET` should be missing during B2 flow
  - retCode 10003 troubleshooting tree includes mainnet/testnet mismatch, demo/testnet-demo mismatch, deleted/disabled/expired key, wrong key/secret pair, IP whitelist mismatch, and endpoint compatibility issue
  - safe restart path requires safe env presence/hygiene check, no-flag latch LASTEXITCODE=3, explicit Human Owner authorization, exactly one real query-api preflight, and no automatic retry
  - B2d remains blocked until query-api preflight succeeds or Human Owner explicitly accepts a documented alternative
- Pit-stop audit evidence:
  - this was a Pit-stop audit, not an implementation gate
  - repo HEAD/origin main aligned at 8153c61 and tracked diff was empty
  - full local regression passed with 408 passed and 5 warnings
  - targeted suites passed: tests/scripts 60, tests/libs/exchange 99, tests/libs/config 19
  - no-flag latches for server_time, wallet_balance, and query_api returned sanitized authorization_required JSON with LASTEXITCODE=3
  - checked BYBIT_B1_ENVIRONMENT, BYBIT_B1_API_KEY, BYBIT_B1_API_SECRET, BYBIT_API_KEY, and BYBIT_API_SECRET by name only; all were missing and no values were printed
  - cleanup removed only the generated `.pytest-temp-run/` artifact
  - backlog: clean async mock warnings; add env-isolation guard tests; add B2 generic alias static guard; audit transaction ownership and handler-level log redaction; plan future authority map / reconciliation / TradingState / OMS; review dependencies and secret scanning; run periodic docs source-of-truth audits
- B2c.1 required next gate:
  - authenticated readiness audit / query-api preflight decision before B2d
  - not real wallet smoke; must not call wallet_balance or open_positions
  - does not authorize order_status or write/live methods
  - must audit signing/query-string behavior, signed vs unsigned server_time, X-BAPI-SIGN-TYPE: 2, safe retCode classification, key active/not expired wording, and whether to add /v5/user/query-api
  - query-api is not currently in B1/B2 endpoint set and requires explicit Human Owner decision; if authorized, it is read-only preflight only
  - /v5/market/time is public and should be treated as unsigned connectivity/time; B2b remains valid, but signed server_time usage should be tracked as audit/backlog issue if present

## Current stage

- Current gate: Stage 54-BG2-C private read-only preflight runbook active; Stage 54-BG2-B remains remote-visible; Stage 54-BG2-A remains remote-visible; Stage 54-BG2 design lock remains recorded; Stage 54-BG1 remains closed as a config-only slice; Bybit Stage 53-B2c.1c/B2d private real testnet path remains blocked due unavailable usable Bybit testnet API access
- Status: owner decisions OI-1..OI-9 ANSWERED / APPROVED; B1-CONFIG config-only slice complete on c17c7d0; Slice 1 accepted/pushed at 828b64a; Slice 2 accepted/pushed at 66a898d; Slice 3 accepted/pushed/remote-visible at 0596afb; B2a accepted/pushed/remote-visible at a511e2f; B2b server_time smoke succeeded locally; B2c wallet_balance smoke harness accepted/pushed/remote-visible at c9b1337; B2c.1a authenticated readiness hardening accepted/pushed/remote-visible at 189cb0a; B2c.1b query-api preflight harness accepted/pushed/remote-visible at 00d84d8; B2c.1c real query-api preflight failed safely with retCode=10003 invalid_key_or_environment; B2d real wallet_balance smoke BLOCKED / NO-GO due unavailable usable Bybit testnet API access
- Stage 53-B1 architecture plan: docs/STAGE_53B1_ARCHITECTURE.md
- Stage 53-B1 implementation owner inputs B1-OI-1..B1-OI-6: ANSWERED / APPROVED
- Next allowed task: Stage 53-B2 docs/status cleanup and Stage 54-BG2/BG2-D follow-up planning; only the Human Owner may authorize the next Bitget slice; the next possible implementation candidate, if separately approved, is BG2-D mocked private read-only preflight parser/client skeleton only; no private smoke or runtime wiring is authorized
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
- B2c.1b scope already present: get_query_api_info() signed read-only GET /v5/user/query-api support; sanitized ApiKeyInfo model; scripts/smoke_query_api.py; mocked tests; direct no-flag latch exits 3; exact success output field set; unsafe readOnly/permissions/expiry metadata fail closed; stale/malformed expiredAt covered; no real query-api execution, credentials use, Bybit call, real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or readiness approval; not runtime-ready
- B2c.1c/B2d blocked state: query-api real preflight attempted once and failed safely with retCode=10003 invalid_key_or_environment and LASTEXITCODE=1; no further query-api retry is authorized; B2d real wallet_balance testnet smoke is blocked / NO-GO because usable Bybit testnet API credentials are unavailable; ordinary/mainnet Bybit key must not be substituted into the testnet flow; any mainnet read-only smoke requires a new separately authorized stage; safe restart path requires safe env presence/hygiene check, no-flag latch LASTEXITCODE=3, explicit Human Owner authorization, exactly one real query-api preflight, and no automatic retry
- Current authorized state: READ_ONLY_TESTNET_SMOKE. Future READ_ONLY_ACTIVE / READ_ONLY_DEGRADED / READ_ONLY_HALTED, OMS, reconciliation, kill switch, risk controls, runbook, write client, ExchangePort refactor, dependency changes, CI secret scanning, and service wiring remain future-gate/backlog concepts only
- Withdrawal permission: forbidden
- Secrets: no secrets in repo, prompts, docs, or logs

## Current forbidden scope

- No API keys in repo, prompts, docs, logs, or committed fixtures
- No further real Bybit connectivity or real credential use without separate Human Owner authorization
- No real query-api retry while B2c.1c is blocked
- No mainnet key substitution into the B2d testnet flow
- No mainnet read-only smoke without a new separately authorized stage
- No further real smoke execution without separate Human Owner authorization
- No orders
- No cancels
- No balance runtime verification or real account balance use
- No positions runtime verification or real account position use
- No real wallet_balance smoke or open_positions smoke without separate Human Owner authorization
- No B2d real wallet_balance testnet smoke while usable Bybit testnet API credentials are unavailable
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

- Human Owner: final authority for stage transitions, GO/NO-GO, risk acceptance, and readiness approval
- Tower Control Architect: project-control architect, prompt architect, stage-gate coordinator, and readiness-separation helper; no final readiness authority
- Codex: repo executor
- Claude: independent reviewer / architecture guardian
- All agents use the 3-lane operating model in docs/HOW_WE_WORK.md: Fast Lane, Standard Lane, Protected Lane
- Commit only after explicit Human Owner instruction
- Every agent report must identify Agent, Task Type, Scope, Lane, Changed Files, Commands Run, Readiness Claims, Not Verified, and Decision Needed
