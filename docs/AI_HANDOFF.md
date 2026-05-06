# AI Handoff - Hephaestus

## New chat restore protocol

Every new Tower Control, Codex, Claude, or reviewer chat must restore project
context from repo docs before relying on task text or memory.

Read in this order:
1. `docs/PROGRESS.md`
2. `docs/AI_COMMANDS.md`
3. `docs/HOW_WE_WORK.md`
4. `docs/AI_HANDOFF.md`
5. `docs/STAGE_MAP.md`
6. `docs/PROJECT_ORIGIN.md`
7. `docs/CONTEXT.md`
8. Current-stage docs as needed

Rules:
- Do not use chat memory as source of truth.
- Do not use `.codex/worktrees` as source of truth.
- Do not use detached worktrees as source of truth.
- If docs conflict, `docs/PROGRESS.md` wins.
- Live trading remains NO-GO unless `docs/PROGRESS.md` explicitly says otherwise.

## Current project status

Project:
Hephaestus - Python async microservice trading system.

Current mode:
paper trading only.

Live trading:
NO-GO.

Runtime status:
- Local paper runtime: GO
- VPS paper runtime: GO
- 9 services healthy
- Current test baseline: HEAD 189cb0a PASS for mocked/local B2c.1a authenticated-readiness hardening only; server_time no-flag latch LASTEXITCODE=3; wallet_balance no-flag latch LASTEXITCODE=3; tests/scripts 40 passed; tests/libs/exchange 86 passed; tests/libs/config 19 passed
- Alembic head: 0008
- execution-service confirmed ready in paper mode
- Live exchange layer: NOT IMPLEMENTED
- B1-CONFIG config-only slice: CODE/TEST COMPLETE, no runtime wiring
- Stage 53-B1 Slice 1 server-time skeleton: ACCEPTED / PUSHED at 828b64a; mocked tests only; not runtime-ready
- Stage 53-B1 Slice 2 wallet_balance: ACCEPTED / PUSHED at 66a898d; mocked tests only; not runtime-ready
- Stage 53-B1 Slice 3 open_positions: ACCEPTED / PUSHED / REMOTE-VISIBLE at 0596afb; mocked tests only; not runtime-ready
- Stage 53-B2a server_time smoke harness: ACCEPTED / PUSHED / REMOTE-VISIBLE at a511e2f; mocked tests only; direct no-flag latch exits 3; not runtime-ready; no real smoke or credentials use authorized
- Stage 53-B2b real server_time smoke: SUCCESS for server_time only; Human Owner executed exactly one real Bybit testnet server_time smoke locally after safe credential presence and hygiene checks; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only; not runtime-ready
- Stage 53-B2c wallet_balance smoke harness: ACCEPTED / PUSHED / REMOTE-VISIBLE at c9b1337; mocked tests only; direct no-flag latch exits 3; --allow-real-smoke required for real-capable path; not runtime-ready; no real wallet_balance smoke or credentials use for B2c implementation
- Stage 53-B2c.1a authenticated readiness hardening: ACCEPTED / PUSHED / REMOTE-VISIBLE at 189cb0a; server_time now uses unsigned public /v5/market/time; get_server_time no longer requires credentials; private reads fail closed without credentials; signed private reads include X-BAPI-SIGN-TYPE: 2; deterministic signed GET query handling is consistent with what is sent; wallet_balance signs/sends accountType=UNIFIED; safe retCode classifications added for 10002/10003/10004/10005/10006/10007/10010; 10006 remains exit code 2 / inconclusive; no query-api, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
- Stage 53-B2c.1b query-api read-only preflight harness: ACCEPTED / PUSHED / REMOTE-VISIBLE at 00d84d8; get_query_api_info() supports signed read-only GET /v5/user/query-api; sanitized ApiKeyInfo model; scripts/smoke_query_api.py exists; no-flag latch exits 3 with sanitized authorization_required JSON; success output exact approved field set with no operation or endpoint_family; unsafe readOnly/permissions/expiry metadata fail closed; stale/malformed expiredAt regression tests exist; rate limit remains exit 2 / inconclusive; no real query-api execution, credentials use, Bybit call, real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
- Stage 53-B2c.1c real query-api preflight: BLOCKED; attempted once and failed safely with retCode=10003, error_category=invalid_key_or_environment, LASTEXITCODE=1; likely ordinary/mainnet Bybit key used against testnet API endpoint, or no usable Bybit testnet API access; no further query-api retry is authorized
- Stage 53-B2d real wallet_balance testnet smoke: BLOCKED / NO-GO because usable Bybit testnet API credentials are unavailable; ordinary/mainnet Bybit key must not be substituted into the testnet flow; any mainnet read-only smoke requires a new separately authorized stage, not continuation of B2d
- Stage 54-BG planning: Bitget Demo / Simulated Trading is the primary candidate for the next exchange-specific read-only sandbox track; start with docs-only architecture planning, then `BitgetBg1Settings` plus mocked tests only
- Stage 54-BG proposed env namespace: `BITGET_BG1_ENVIRONMENT`, `BITGET_BG1_API_KEY`, `BITGET_BG1_API_SECRET`, `BITGET_BG1_PASSPHRASE`
- Stage 54-BG first-slice safety boundary: no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback, Bitget production/mainnet fail-closed by default, and no private Bitget smoke before config/environment/passphrase boundaries are locked
- Stage 54-BG1 config-only checkpoint: COMPLETE; `BitgetBg1Settings` plus mocked/env-isolated config tests accepted; final QA PASS; previous P2 env-isolation finding closed; validation evidence `tests/libs/config/test_bitget_bg1_settings.py` 12 passed and `tests/libs/config` 36 passed; no exchange tests, script tests, or broader repo regression were run
- Stage 54-BG2 design lock: DOCS-ONLY / DESIGN LOCK; Bitget Demo API planning only; future demo private REST requests must account for `paptrading: 1`; auth shape uses API key, secret key, and passphrase; private requests require signing; public endpoints stay separate from private/authenticated endpoints; WebSocket demo endpoints remain future/out of scope unless explicitly authorized
- Stage 54-BG2 safety boundary: no API/exchange/Beget/network operations; no private smoke; no orders/cancels/set_leverage/withdraw/transfer; no runtime/service wiring; no generic exchange adapter; no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback; `production` / `mainnet` / `live` / `testnet` remain fail-closed for the BG1/BG2 path
- Stage 54-BG2-A public-only skeleton: ACCEPTED / REMOTE-VISIBLE on `ad8df47`; public unsigned Bitget connectivity skeleton only; mocked tests only; no credentials, no `SecretStr`, no signing, no passphrase, no `paptrading` header, no private endpoints, no smoke script, no runtime/service wiring, no generic exchange adapter, and no real API/exchange/Beget/network operations
- Stage 54-BG2-A test evidence: `tests/libs/exchange/test_bitget_public.py` 8 passed and `tests/libs/exchange` 107 passed; readiness is code-ready/test-ready for public-only skeleton only; not runtime-ready, trading-ready, live-ready, or probe-ready
- Stage 54-BG2-B signing helper: ACCEPTED on `07cea3b`; Bitget-specific signing helper only; mocked tests only; deterministic payload uses timestamp + uppercased method + request path + optional query string + body; HMAC-SHA256 Base64 signature; required headers are `ACCESS-KEY`, `ACCESS-SIGN`, `ACCESS-TIMESTAMP`, `ACCESS-PASSPHRASE`, and `Content-Type: application/json`; no env reads; missing/empty credentials fail closed; redaction/safe repr prevents exposing api_key, api_secret, passphrase, or signature; no private client, no endpoint methods, no network calls, no `paptrading` header, no smoke script, no runtime/service wiring, and no generic exchange adapter
- Stage 54-BG2-B test evidence: `tests/libs/exchange/test_bitget_auth.py` 15 passed and `tests/libs/exchange` 122 passed; readiness is code-ready/test-ready for signing helper only; not runtime-ready, trading-ready, live-ready, or probe-ready
- Stage 54-BG2-C private read-only preflight runbook: DOCS-ONLY / PLANNING; candidate future endpoint is `GET /api/v3/account/info` for a private read-only preflight discussion only, not an approved call; future demo private requests must include explicit `paptrading: 1` marker handling; future private output must remain sanitized to high-level summaries only and must never expose raw uid, raw permissions, raw IPs, raw response body, raw error messages, API keys, secrets, passphrases, signatures, account IDs, balances, positions, or signed payloads
- Stage 54-BG2-C guardrails: safe env presence/hygiene checks required; no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback; `BITGET_BG1_` namespace only unless later owner-approved; fail closed if credentials are missing/empty, environment is not demo/simulated, permissions include trade/transfer/withdraw/write-like capability, response cannot prove safe read-only posture, or result is rate-limited/inconclusive; no automatic retry after a real preflight failure; no private client, no private smoke, no runtime wiring, and no real API/exchange/Beget/network operations are authorized
- Stage 54-AP fallback planning: Alpaca Paper remains fallback-only and must stay a separate architecture track; do not fold Alpaca into a crypto-CEX abstraction
- Generic adapter boundary: do not create a generic exchange adapter yet
- Beget API access: AVAILABLE / OPERATIONAL CAPABILITY ONLY; no secrets recorded; does not imply deployment readiness or runtime readiness; any Beget API operation that changes infrastructure, deployment, runtime, secrets, or server state is Protected Lane and requires explicit Human Owner authorization
- Stage 53-B2 testnet API access runbook: DOCUMENTED in docs/STAGE_53B2_SMOKE_PLAN.md; Human Owner must obtain testnet credentials from https://testnet.bybit.com / https://testnet.bybit.com/app/user/api-management; use API Transaction key type, read-only only, withdrawal/transfer/trade/order/write disabled; BYBIT_B1_ENVIRONMENT=testnet; BYBIT_B1_API_KEY and BYBIT_B1_API_SECRET must come from the same testnet key pair; BYBIT_API_KEY / BYBIT_API_SECRET should be missing during B2 flow; retCode 10003 troubleshooting covers mainnet/testnet mismatch, demo/testnet-demo mismatch, deleted/disabled/expired key, wrong key/secret pair, IP whitelist mismatch, and endpoint compatibility issue
- Stage 53-B2 Pit-stop audit: RECORDED as audit-only, not an implementation gate; repo was aligned at 8153c61; tracked diff was empty; full local regression passed with 408 passed and 5 warnings; targeted suites passed with tests/scripts 60, tests/libs/exchange 99, tests/libs/config 19; server_time, wallet_balance, and query_api no-flag latches all exited 3; checked BYBIT env names were missing; no runtime/trading/live/probe readiness is claimed
- Stage 53-B2c.1 authenticated readiness audit / query-api preflight decision: B2c.1a and B2c.1b are mocked/local implementation checkpoints only; private real testnet path is blocked due unavailable usable Bybit testnet API access
- Stage 53-B2 permanent real-smoke preflight: safe credential presence check, safe credential hygiene check, and Human Owner external key active/not expired confirmation are required before any real Bybit smoke gate; any missing required env var, hygiene warning, expired/uncertain key, or missing owner confirmation stops the smoke; 7-day note is not verified API key expiry

Latest known commits:
- 189cb0a feat: harden Stage 53-B2 authenticated smoke readiness
- 00d84d8 feat: add Stage 53-B2 query-api preflight harness
- c9b1337 feat: add Stage 53-B2 wallet-balance smoke harness
- a511e2f feat: add Stage 53-B2 server-time smoke harness
- 0596afb feat: add Bybit B1 read-only open positions
- 66a898d feat: add Bybit B1 read-only wallet balance
- 828b64a feat: add Bybit B1 read-only server-time skeleton
- d6045ad docs: add three-lane operating model
- 43940c8 docs: sync Stage 53-B1 B1-CONFIG status
- c17c7d0 feat: add Bybit B1 read-only config settings
- 67c37f6 Merge pull request #10 from Obama288/docs/stage-53b1-owner-inputs
- 93e7767 docs: record Stage 53-B1 implementation owner inputs
- 63d14f0 docs: add Stage 53-B1 architecture plan
- 19e00a8 docs: record Stage 53-B owner decisions
- 1bd8e2a fix: implement true EMA in snapshot builder
- 5e5eb48 docs: add stage 53-B design lock
- 3b3b06f feat: add Bybit public market data adapter

---

## Closed work

- Q1-FIX-1 recover_position payload validation: MERGED
- Q1-FIX-2 freshness naive datetime handling: MERGED
- Q1-FIX-3 true EMA in snapshot builder: MERGED, regression-validated on main 1bd8e2a
- Stage 53-A: CLOSED, commit 3b3b06f
- Stage 53-B design lock: CLOSED, commit 5e5eb48
- Status docs after 53-B design lock: CLOSED, commit 69176ed
- Stage 53-B owner decision tracker: ADDED, commit e814031
- Stage 53-B1 architecture plan: ADDED in docs/STAGE_53B1_ARCHITECTURE.md
- Stage 53-B1 owner inputs: ADDED, commit 93e7767
- B1-CONFIG config-only settings: ADDED, commit c17c7d0
- Stage 53-B1 Slice 1 server-time skeleton: ACCEPTED / PUSHED, commit 828b64a
- Stage 53-B1 Slice 2 wallet_balance: ACCEPTED / PUSHED, commit 66a898d
- Stage 53-B1 Slice 3 open_positions: ACCEPTED / PUSHED / REMOTE-VISIBLE, commit 0596afb
- Stage 53-B2a server_time smoke harness: ACCEPTED / PUSHED / REMOTE-VISIBLE, commit a511e2f
- Stage 53-B2b real server_time smoke: SUCCESS, local owner-run; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only; no wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
- Stage 53-B2c wallet_balance smoke harness: ACCEPTED / PUSHED / REMOTE-VISIBLE, commit c9b1337; mocked tests only; no real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
- Stage 53-B2c.1a authenticated readiness hardening: ACCEPTED / PUSHED / REMOTE-VISIBLE, commit 189cb0a; mocked/local hardening only; no query-api, real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
- Stage 53-B2c.1b query-api read-only preflight harness: ACCEPTED / PUSHED / REMOTE-VISIBLE, commit 00d84d8; mocked tests only; no real query-api execution, credentials use, Bybit call, real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
- Stage 53-B2c.1c real query-api preflight: BLOCKED, local owner-run; retCode=10003 invalid_key_or_environment; LASTEXITCODE=1; likely mainnet/testnet key-environment mismatch or no usable testnet API access; no retry authorized
- Stage 53-B2d real wallet_balance testnet smoke: BLOCKED / NO-GO; usable Bybit testnet API credentials unavailable; mainnet key must not be substituted into testnet flow
- Stage 53-B2 testnet API access runbook: DOCUMENTED; safe restart path is safe env presence/hygiene check, no-flag latch LASTEXITCODE=3, explicit Human Owner authorization, exactly one real query-api preflight, and no automatic retry
- Stage 53-B2 Pit-stop audit: RECORDED; cleanup removed generated `.pytest-temp-run/`; backlog includes async mock warning cleanup, env-isolation guard tests, B2 generic alias static guard, transaction ownership audit, handler-level log redaction audit, future authority map / reconciliation / TradingState / OMS planning, dependency and secret-scan review, and periodic docs source-of-truth audit
- Live Path Audit completed
- Legacy 11-item live blocker audit completed; canonical current taxonomy is 14 live blockers.

---

## Current gate

Current gate:
Stage 54-BG2-C private read-only preflight runbook active; Stage 54-BG2-B remains remote-visible; Stage 54-BG2-A remains remote-visible; Stage 54-BG2 design lock remains recorded; Stage 54-BG1 config-only checkpoint remains closed; Bybit Stage 53-B2c.1c/B2d private real testnet path remains blocked due unavailable usable Bybit testnet API access.

Stage 53-B implementation:
BLOCKED beyond accepted Slice 3 open_positions.

Stage 53-B1 implementation state:
B1-CONFIG config-only slice is complete on c17c7d0. Slice 1 server-time skeleton is accepted and pushed on 828b64a. Slice 2 wallet_balance is accepted and pushed on 66a898d. Slice 3 open_positions is accepted, pushed, and remote-visible on 0596afb. It includes get_open_positions(), open-position read-only models, Decimal numeric values, redacted repr() / model_dump(), sanitized open-position errors, and mocked tests.

Stage 53-B2a implementation state:
B2a server_time smoke harness is accepted, pushed, and remote-visible on a511e2f. It includes a server_time smoke harness, mocked tests, and a direct CLI no-flag safety latch that exits 3 with authorization_required JSON.

Stage 53-B2b smoke state:
B2b real server_time smoke succeeded for server_time only. Human Owner executed exactly one real Bybit testnet server_time smoke locally after safe credential presence and hygiene checks. Result: LASTEXITCODE=0; elapsed_ms=1534; sanitized output only. Credentials were used locally only and must not be stored or disclosed. No wallet_balance smoke, open_positions smoke, order_status, write/live methods, or service wiring was run or authorized. Runtime readiness is not confirmed.

Stage 53-B2c implementation state:
B2c wallet_balance smoke harness is accepted, pushed, and remote-visible on c9b1337. It adds scripts/smoke_wallet_balance.py and tests/scripts/test_smoke_wallet_balance.py. It includes a wallet_balance smoke harness, mocked tests only, and a direct CLI no-flag safety latch that exits 3 with authorization_required JSON. The real-capable path requires --allow-real-smoke. Mocked success output is sanitized and includes only endpoint/status/exchange/account_type/coins_count/elapsed_ms. No real wallet_balance smoke was run. No credentials were used for B2c implementation. No open_positions smoke, order_status, write/live methods, or service wiring was added. Runtime readiness is not confirmed.

Stage 53-B2c.1a implementation state:
B2c.1a authenticated readiness hardening is accepted, pushed, and remote-visible on 189cb0a. It changes server_time to unsigned public /v5/market/time methodology, allows get_server_time without credentials, keeps private reads fail-closed without credentials, adds X-BAPI-SIGN-TYPE: 2 to private signed reads, ensures signed GET query handling is deterministic and consistent with what is sent, keeps wallet_balance signing/sending accountType=UNIFIED, and adds safe retCode classifications for 10002/10003/10004/10005/10006/10007/10010. 10006 remains exit code 2 / inconclusive in smoke harnesses. It did not add query-api, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness.

Stage 53-B2c.1b implementation state:
B2c.1b query-api read-only preflight harness is accepted, pushed, and remote-visible on 00d84d8. It adds get_query_api_info() signed read-only GET /v5/user/query-api support, sanitized ApiKeyInfo boolean/status summary output, scripts/smoke_query_api.py, and mocked tests. The direct no-flag latch exits 3 with sanitized authorization_required JSON and does not load settings/client/credentials or call Bybit. Success output includes exactly endpoint/status/exchange/read_only/permissions_safe/key_active/deadline_days_present/expired_at_present/elapsed_ms; operation and endpoint_family are absent. Unsafe readOnly, unsafe permissions, and expired/non-positive/missing/stale/malformed expiry metadata fail closed. No real query-api execution, credentials use, Bybit call, real wallet_balance smoke, open_positions smoke, order_status, write/live methods, or service wiring was added. Runtime readiness is not confirmed.

Stage 53-B2c.1c / B2d blocked state:
B2c.1c real query-api preflight was attempted once and failed safely with retCode=10003, error_category=invalid_key_or_environment, and LASTEXITCODE=1. The likely cause is an ordinary/mainnet Bybit API key used against the testnet API endpoint, or no usable Bybit testnet API access. No further query-api retry is authorized. B2d real wallet_balance testnet smoke is blocked / NO-GO because usable Bybit testnet API credentials are unavailable. The ordinary/mainnet Bybit key must not be substituted into the testnet flow. Any mainnet read-only smoke would require a new separately authorized stage and guardrails; it is not a continuation of B2d.

Stage 53-B2 testnet API access runbook:
The practical runbook is in docs/STAGE_53B2_SMOKE_PLAN.md. Human Owner should use https://testnet.bybit.com and https://testnet.bybit.com/app/user/api-management, create an API Transaction key rather than third-party application binding, keep permissions read-only with withdrawal/transfer/trade/order/write disabled, set BYBIT_B1_ENVIRONMENT=testnet, and ensure BYBIT_B1_API_KEY and BYBIT_B1_API_SECRET come from the same testnet key pair. BYBIT_API_KEY / BYBIT_API_SECRET should be missing during B2 flow. B2d remains blocked until query-api preflight succeeds or the Human Owner explicitly accepts a documented alternative.

Stage 53-B2 Pit-stop audit record:
The Pit-stop was an audit-only checkpoint, not an implementation gate. Repo HEAD/origin main were aligned at 8153c61 and the tracked diff was empty. No-flag latches for server_time, wallet_balance, and query_api all returned sanitized authorization_required JSON with LASTEXITCODE=3. Tests passed: tests/scripts 60, tests/libs/exchange 99, tests/libs/config 19, and full local regression 408 passed with 5 warnings. All checked BYBIT env names were missing and no values were printed. B2d remains blocked / NO-GO; B2c.1c query-api failed safely with retCode=10003 invalid_key_or_environment due no usable testnet API access / environment mismatch. No mainnet smoke, real query-api retry, real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime/trading/live/probe readiness is authorized. Follow-up backlog: clean async mock warnings; add env-isolation guard tests; add static guard for generic BYBIT_API_KEY/BYBIT_API_SECRET in B2 flow; audit transaction ownership and handler-level log redaction; plan future authority map / reconciliation / TradingState / OMS work; review dependencies and secret scanning; repeat docs source-of-truth audits.

Stage 53-B2c.1 required gate:
B2c.1 is an authenticated readiness audit / query-api preflight decision before B2d. It is not real wallet smoke, must not call wallet_balance or open_positions, and does not authorize order_status or write/live methods. It must audit signing/query-string behavior, whether server_time is signed or unsigned, whether X-BAPI-SIGN-TYPE: 2 is present or intentionally omitted, whether to add /v5/user/query-api as a new read-only preflight endpoint, and docs wording around key active/not expired checks. Query-api is not currently in the B1/B2 endpoint set and requires explicit Human Owner decision. /v5/market/time is public and should be treated as unsigned connectivity/time; B2b remains valid as a real testnet connectivity checkpoint, but signed server_time usage should be tracked as an audit/backlog issue if present.

Slice 3 classification:
- Code-ready candidate / accepted implementation checkpoint for open_positions only.
- Test-ready for mocked open_positions behavior only.
- Not runtime-ready.

Still not implemented:
- B2d real wallet_balance smoke
- open_positions smoke
- order_status
- place_order
- cancel_order
- set_leverage
- withdraw
- transfer
- live_reconcile
- live_execution
- service startup wiring
- wallet_balance/open_positions real Bybit connectivity verification
- real credential verification

Block reason:
B2c.1c/B2d private real testnet smokes are blocked because usable Bybit testnet API credentials are unavailable. The ordinary/mainnet Bybit key must not be substituted into the testnet flow. Any mainnet read-only smoke would require a new separately authorized stage. Open_positions smoke, order_status, and all write/live methods require separate Human Owner authorization.

Owner decisions OI-1..OI-9 are ANSWERED / APPROVED in docs/STAGE_53B_OWNER_DECISIONS.md.
No runtime implementation is authorized by the decision-sync PR, B1-CONFIG, Slice 1, Slice 2, or Slice 3.
No live trading enablement is allowed.

Next safe work:
Stage 53-B2 docs/status cleanup and Stage 54-BG2/BG2-D follow-up planning. Only the Human Owner may authorize the next Bitget slice. The next possible implementation candidate, if separately approved, is BG2-D mocked private read-only preflight parser/client skeleton only. No private smoke or runtime wiring is authorized.

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

Stage 53-B1 maximum scope:
- Bybit only
- Testnet/demo only; first target = testnet
- Authenticated client
- First implementation endpoints: server time/connectivity, wallet balance read-only, open positions read-only
- Order status read-only deferred to a later slice
- No place order
- No cancel order
- No set_leverage
- No live reconcile
- Withdrawal permission is forbidden
- No secrets in repo, prompts, docs, or logs

Architecture plan:
- docs/STAGE_53B1_ARCHITECTURE.md
- B1-CONFIG config-only slice exists.
- Slice 1 server-time skeleton exists at 828b64a; read-only client remains library-only and exposes get_server_time() only.
- Slice 2 wallet_balance exists at 66a898d; read-only client exposes get_wallet_balance() with mocked tests only.
- Slice 3 open_positions exists at 0596afb; read-only client exposes get_open_positions() with mocked tests only.
- B2a server_time smoke harness exists at a511e2f; direct no-flag latch exits 3 with authorization_required JSON; mocked tests only.
- B1-OI-1..B1-OI-6 are ANSWERED / APPROVED for future implementation planning.
- This does not authorize runtime implementation, live trading, production private endpoints, orders, cancels, leverage changes, live reconcile, or live execution.

Current regression evidence:
- python scripts\smoke_server_time.py: LASTEXITCODE=3 with sanitized authorization_required JSON
- python -m pytest tests\scripts\test_smoke_server_time.py -q --basetemp=.pytest-temp-run: 14 passed
- python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 39 passed
- python -m pytest tests\libs\exchange -q: 78 passed
- python -m pytest tests\libs\config -q: 19 passed
- python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 33 passed
- python -m pytest tests\libs\exchange -q: 72 passed
- python -m pytest tests\libs\config -q: 19 passed
- python -m pytest tests\libs\exchange -q: 39 passed
- python -m pytest apps/market_data/tests -q: 8 passed
- python -m pytest apps -q: 163 passed
- python -m pytest -q --ignore=./research --basetemp=.pytest_tmp: 288 passed, 5 warnings
- No secrets observed.
- No live/exchange/private endpoints/orders/cancels/balances/live execution/live reconcile were enabled or observed.

---

## Current forbidden scope

- API keys
- Private endpoints
- Orders
- Cancels
- Production balances
- Live positions
- Authenticated exchange client implementation beyond separately approved Slice 3 read-only library scope
- Service startup wiring for Bybit private/read-only client
- Live execution
- Live trading enablement
- Runtime implementation
- Risk pipeline rewrites
- Orchestrator rewrites
- Position manager rewrites
- Event Bus implementation
- Redis Pub/Sub implementation
- Strategy quality filters
- News filters
- Pair ranking
- Regime detector
- Signal quality gate

---

## Stage 53 constraints - must not change

1. Pipeline order: signal -> risk -> review -> orchestrator -> execution_service -> position_manager
2. Kill-switch fail-closed: all 4 error classes (AUTH_FAILURE, KILL_SWITCH_TIMEOUT, KILL_SWITCH_UNAVAILABLE, KILL_SWITCH_ERROR) must continue to block execution
3. RiskDecision.entry_price midpoint rule: (entry_zone.min + entry_zone.max) / 2
4. execution_idempotency_key deduplication: DB-level idempotency must remain for the paper path; live adds exchange-level idempotency on top
5. Journal fail-soft after authoritative DB commit: journal write failure must not roll back a committed position or execution
6. operator_actions audit trail: every approve/reject must continue to write to operator_actions table atomically
7. max_open_positions DB cap gate with advisory lock: must remain at execution admission boundary
8. Token validation at startup: validate_startup_auth() must not be weakened

---

## Live blockers

Legacy summarized list (11 items) - not the current authoritative blocker count.
Canonical current taxonomy: 14 canonical live blockers from docs/STAGE_53_DESIGN_LOCK.md.

1. No authenticated exchange client
2. place_order.py hard-rejects non-paper mode
3. No order status polling
4. entry_price from signal not exchange fill
5. Position close is DB-only
6. No balance/margin check
7. No rate limit handling
8. No partial fill handling
9. Live reconcile is paper-only
10. Symbol format is OKX-only
11. Cancel order is DB-only

---

## Owner decisions for Stage 53-B1

OI-1..OI-9 are ANSWERED / APPROVED in docs/STAGE_53B_OWNER_DECISIONS.md.

1. OI-1: Bybit only.
2. OI-2: Testnet/demo only.
3. OI-3: Read-only balances + positions; optional order status read-only; no place/cancel orders.
4. OI-4: Env vars for local testnet; secret manager/GitHub secrets later; no secrets in repo/prompts/docs.
5. OI-5: Read-only API key only; withdrawal permission forbidden.
6. OI-6: Live trading only after full implementation + QA + regression + external review + separate explicit owner approval.
7. OI-7: Keep current authority model exactly.
8. OI-8: Authenticated client + testnet read-only balances and positions only.
9. OI-9: Full protocol: architect -> plan -> implement -> QA -> external review if needed -> PR -> merge.

These decisions authorize planning only. Stage 53-B1 implementation, live trading, order placement, cancellation, live execution, and live reconcile all require separate explicit approval.

---

## Working protocol

- Windows PowerShell uses ; not &&
- Always use python -m pytest
- Always use python -m alembic
- Always use python -m uvicorn
- Verify file edits with Get-Content after writing
- Use the 3-lane operating model in docs/HOW_WE_WORK.md: Fast Lane, Standard Lane, Protected Lane
- Fast Lane: docs/report-only scope checks; QA optional when no readiness is promoted
- Standard Lane: focused approved work; compact QA required with targeted tests/checks
- Protected Lane: live/probe readiness, authenticated/private exchange work, secrets, safety authority, runtime wiring, infra/deploy, migrations/schema, dependencies, or runtime-behavior config; explicit Human Owner authorization and mandatory QA required
- Every report must identify Agent, Task Type, Scope, Lane, Changed Files, Commands Run, Readiness Claims, Not Verified, and Decision Needed
- Definition of Done: changed + verified + commands/results + readiness claims + not verified + git status
- Do not commit without explicit owner instruction

---

## Authority rules

- Kill switch is top safety authority
- Risk is source of truth for trade admissibility
- Orchestrator coordinates but must not bypass risk/review/kill_switch
- Review does not recompute authoritative risk values
- Execution service owns order lifecycle
- Position manager owns internal position state
- Dashboard aggregates and must not mutate trading state
- Journal records and must not become trading authority

---

## Agent roles

- Human Owner: final authority for stage transitions, GO/NO-GO, risk acceptance, and readiness approval
- Tower Control Architect: project-control architect, prompt architect, stage-gate coordinator, and readiness-separation helper; no final readiness authority
- Codex: repo executor
- Claude: independent reviewer / architecture guardian
- All agents use the 3-lane operating model in docs/HOW_WE_WORK.md: Fast Lane, Standard Lane, Protected Lane
- Commit only after explicit Human Owner instruction
- Every agent report must identify Agent, Task Type, Scope, Lane, Changed Files, Commands Run, Readiness Claims, Not Verified, and Decision Needed

---

## Stage 54+ reminder

- State ownership and domain events draft exists at docs/architecture/STATE_AND_EVENTS_DRAFT.md
- Do not implement Event Bus before state ownership, event envelope, idempotency, retry/dead-letter, and failure behavior are accepted
- Redis is optional cache/pub-sub/ephemeral state only, not durable source of truth

---

## Reviewer checklist before any code change

- Does this change touch runtime code?
- Does this change alter pipeline order?
- Does this change weaken kill-switch fail-closed behavior?
- Does this change introduce live execution?
- Does this change use API keys or private endpoints?
- Does this change add hidden defaults for market_type?
- Does this change use float for prices/qty?
- Does this change bypass service ownership?
- Does this change mix Stage 53 safety with Stage 54 signal-quality filters?
- Are tests updated or planned?
- Is git status clean except intended files?
