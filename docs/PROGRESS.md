# Progress Log

## Current Gate Status

Date: 2026-04-29

Stage:
Stage 54-BG2-C private read-only preflight runbook active; Stage 54-BG2-B remains remote-visible; Stage 54-BG2-A remains remote-visible; Stage 54-BG2 design lock remains recorded; Stage 54-BG1 remains closed as a config-only slice; Bybit Stage 53-B2c.1c/B2d private real testnet path remains blocked due unavailable usable Bybit testnet API access.

Target:
Docs-only design/runbook update for a future Stage 54-BG2-C Bitget Demo
private read-only preflight.

Not target:
- Stage 54-BG implementation
- Stage 54-BG2 implementation
- Bitget client implementation
- Bitget private client implementation
- Bitget private preflight implementation
- Bitget smoke scripts
- Generic exchange adapter creation
- Alpaca integration into a crypto-CEX abstraction
- Stage 53-B runtime implementation
- Order status implementation
- Service startup wiring
- Bitget private smoke
- Bitget real wallet/balance/positions smoke
- Real wallet_balance smoke execution
- Real query-api retry
- Mainnet read-only smoke
- Credentials use for B2c implementation
- Open positions smoke
- Real live exchange execution
- Unsupervised production live
- Signal quality work as part of the BG2-C Bitget/private-preflight lane; Stage 54-SQ is now a separate parallel research-only track
- Media/AI advisory work
- LH-2 accumulation/stats work

Readiness levels:
- Docs-ready: GO - planning trail reflects Stage 54-BG Bitget candidate and Stage 54-AP fallback boundary
- Docs-ready: GO - Stage 54-BG1 config-only checkpoint recorded with final QA PASS and P2 env-isolation finding closed
- Docs-ready: GO - Stage 54-BG2 design lock recorded for Bitget Demo API planning only
- Docs-ready: GO - Stage 54-BG2-A public-only skeleton evidence recorded at HEAD `ad8df47`
- Docs-ready: GO - Stage 54-BG2-B signing helper evidence recorded at HEAD `07cea3b`
- Docs-ready: GO - Stage 54-BG2-C private read-only preflight runbook recorded for planning only
- Docs-ready: GO - status reflects B2c wallet_balance smoke harness checkpoint at HEAD c9b1337
- Docs-ready: GO - status reflects B2c.1a authenticated readiness hardening checkpoint at HEAD 189cb0a
- Code-ready: code-ready candidate / accepted implementation checkpoint for Stage 53-B2c.1a mocked/local authenticated-readiness hardening only
- Test-ready: mocked/local B2c.1a hardening behavior only; server_time no-flag latch LASTEXITCODE=3; wallet_balance no-flag latch LASTEXITCODE=3; tests/scripts 40 passed; tests/libs/exchange 86 passed; tests/libs/config 19 passed
- Runtime-ready: not runtime-ready; B2b confirmed server_time connectivity only and B2c.1a is mocked/local hardening behavior only

Current verdict:
- Tower Control Architect role: DOCUMENTED / ACTIVE as the GPT project-control role; responsible for context recovery from `docs/PROGRESS.md`, stage-gate discipline, scope control, prompt architecture, and GO/HOLD/NO-GO recommendations only; no final readiness authority
- Historical stage groups: DOCUMENTED as compact pre-Stage-43 chronology only; not authoritative renumbering; official current stage/gate remains defined by `docs/PROGRESS.md`
- Beget API access: AVAILABLE / OPERATIONAL CAPABILITY ONLY; no secrets recorded; does not imply deployment readiness, runtime readiness, probe readiness, trading readiness, or live readiness; any Beget API operation that changes infra/runtime/server state requires separate explicit Human Owner authorization under Protected Lane
- Stage 54-BG planning: PRIMARY CANDIDATE selected at planning level only; Bitget Demo / Simulated Trading should start with docs-only architecture planning, then `BitgetBg1Settings` plus mocked tests only
- Stage 54-BG proposed env namespace: `BITGET_BG1_ENVIRONMENT`, `BITGET_BG1_API_KEY`, `BITGET_BG1_API_SECRET`, `BITGET_BG1_PASSPHRASE`
- Stage 54-BG alias boundary: no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback in the first implementation
- Stage 54-BG safety boundary: Bitget production/mainnet must fail closed by default; no private Bitget smoke before config, environment, and passphrase boundaries are locked
- Stage 54-BG1 checkpoint: COMPLETE as a config-only slice; `BitgetBg1Settings` and mocked/env-isolated config tests accepted; final QA PASS; previous P2 env-isolation finding closed; validation evidence `tests/libs/config/test_bitget_bg1_settings.py` 12 passed and `tests/libs/config` 36 passed
- Stage 54-BG2 design lock: DESIGNED / DOCS-ONLY; Bitget Demo API planning only; future demo private REST requests must account for `paptrading: 1`; auth shape uses API key, secret key, and passphrase; private requests require signing; public and private paths must remain split; WebSocket demo endpoints remain out of scope unless later authorized; see `docs/STAGE_54_BG2_DESIGN_LOCK.md`
- Stage 54-BG2 locked boundaries: no API/exchange/Beget/network operations; no private smoke; no orders/cancels/set_leverage/withdraw/transfer; no runtime/service wiring; no generic exchange adapter; no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback; no readiness beyond docs-ready for BG2
- Stage 54-BG2 locked implementation posture: keep Bitget exchange-specific; keep `BITGET_BG1_` naming unless later owner-approved; passphrase remains `SecretStr`; future signing helpers must redact all secret-bearing data; future private read-only path must fail closed without credentials
- Stage 54-BG2-A public-only skeleton: ACCEPTED / REMOTE-VISIBLE on `ad8df47`; public unsigned Bitget connectivity skeleton only; mocked tests only; no credentials, no `SecretStr`, no signing, no passphrase, no `paptrading` header, no private endpoints, no smoke script, no runtime/service wiring, no generic exchange adapter, and no real API/exchange/Beget/network operations
- Stage 54-BG2-A test evidence: `python -m pytest tests\libs\exchange\test_bitget_public.py -q --basetemp=.pytest-temp-run` -> 8 passed; `python -m pytest tests\libs\exchange -q --basetemp=.pytest-temp-run` -> 107 passed
- Stage 54-BG2-A readiness: code-ready/test-ready for public-only skeleton only; not runtime-ready, trading-ready, live-ready, or probe-ready
- Stage 54-BG2-B signing helper: ACCEPTED on `07cea3b`; Bitget-specific signing helper only; mocked tests only; deterministic payload uses timestamp + uppercased method + request path + optional query string + body; HMAC-SHA256 Base64 signature; required headers are `ACCESS-KEY`, `ACCESS-SIGN`, `ACCESS-TIMESTAMP`, `ACCESS-PASSPHRASE`, and `Content-Type: application/json`; no env reads; missing/empty credentials fail closed; redaction/safe repr prevents exposing api_key, api_secret, passphrase, or signature; no private client, no endpoint methods, no network calls, no `paptrading` header, no smoke script, no runtime/service wiring, and no generic exchange adapter
- Stage 54-BG2-B test evidence: `python -m pytest tests\libs\exchange\test_bitget_auth.py -q --basetemp=.pytest-temp-run` -> 15 passed; `python -m pytest tests\libs\exchange -q --basetemp=.pytest-temp-run` -> 122 passed
- Stage 54-BG2-B readiness: code-ready/test-ready for signing helper only; not runtime-ready, trading-ready, live-ready, or probe-ready
- Stage 54-BG2-C private read-only preflight runbook: DOCS-ONLY / PLANNING; candidate future endpoint is `GET /api/v3/account/info` for a private read-only preflight discussion only, not an approved call; future sanitized output must stay at high-level summaries only such as status, exchange, endpoint, read_only / permissions_safe summary, ip_whitelist_present summary, and elapsed_ms only if a future smoke is separately approved; raw uid, raw permissions, raw IPs, raw response body, raw error messages, API keys, secrets, passphrases, signatures, account IDs, balances, positions, and signed payloads remain forbidden in logs, docs, and output
- Stage 54-BG2-C required future guardrails: future demo private requests must include explicit `paptrading: 1` marker handling; no `paptrading` runtime behavior is implemented in BG2-C; safe env presence and hygiene checks are required; no generic `BITGET_API_KEY` / `BITGET_API_SECRET` fallback; `BITGET_BG1_` namespace only unless later owner-approved; fail closed if credentials are missing/empty, if environment is not demo/simulated, if permissions include trade/transfer/withdraw/write-like capability, if the response cannot prove safe read-only posture, or if result is rate-limited/inconclusive; no automatic retry after a real preflight failure; see `docs/STAGE_54_BG2C_PRIVATE_PREFLIGHT_RUNBOOK.md`
- Stage 54-BG2-C readiness: docs-ready only; not code-ready, test-ready, runtime-ready, trading-ready, live-ready, or probe-ready
- Stage 54-SQ: ACTIVE PARALLEL RESEARCH-ONLY SIGNAL-QUALITY OBSERVATION TRACK / APPROVED BY HUMAN OWNER
- Stage 54-SQ purpose: automated signal observations from public OHLCV for BTC/ETH/SOL, Setup A/B detection, BTC score tagging for ETH, simulated outcome in R, and statistics/reporting
- Stage 54-SQ-A models skeleton: ACCEPTED FOR COMMIT as research-layer implementation only
- Stage 54-BG2-C relationship: remains the current documented Bitget/private-preflight planning gate and is not replaced, advanced, or closed by Stage 54-SQ
- Stage 54-SQ not authorized: paper execution, live trading, private exchange API, exchange operations, orders, cancels, set_leverage, runtime wiring, or changes to risk_engine, execution_service, orchestrator, position_manager, or kill_switch
- Stage 54-SQ claim boundary: no signal edge, profitability, runtime readiness, trading readiness, live readiness, or probe readiness is claimed; Live trading remains NO-GO
- Stage 54-AP fallback: Alpaca Paper remains fallback-only and must stay a separate architecture track
- Generic adapter boundary: do not create a generic exchange adapter yet
- Real live execution: NO-GO
- Stage 53-B owner decisions: ANSWERED / APPROVED
- Stage 53-B1 architecture plan: ADDED in docs/STAGE_53B1_ARCHITECTURE.md
- Stage 53-B1 implementation owner inputs: ANSWERED / APPROVED
- B1-CONFIG config-only slice: CODE/TEST COMPLETE on HEAD c17c7d0
- Stage 53-B1 Slice 1 server-time skeleton: ACCEPTED / PUSHED on HEAD 828b64a
- Stage 53-B1 Slice 2 wallet_balance: ACCEPTED / PUSHED on HEAD 66a898d
- Stage 53-B1 Slice 3 open_positions: ACCEPTED / PUSHED on HEAD 0596afb
- Stage 53-B2a server_time smoke harness: ACCEPTED / PUSHED on HEAD a511e2f
- Stage 53-B2b real server_time smoke: SUCCESS; Human Owner executed exactly one real Bybit testnet server_time smoke locally after safe credential presence and hygiene checks; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only
- Stage 53-B2c wallet_balance smoke harness: ACCEPTED / PUSHED / REMOTE-VISIBLE on HEAD c9b1337; mocked tests only; direct no-flag latch exits 3; --allow-real-smoke required for real-capable path; not runtime-ready; no real wallet_balance smoke or credentials use for B2c implementation
- Stage 53-B2c.1a authenticated readiness hardening: ACCEPTED / PUSHED / REMOTE-VISIBLE on HEAD 189cb0a; server_time now uses unsigned public /v5/market/time; get_server_time no longer requires credentials; private reads still fail closed without credentials; signed private reads include X-BAPI-SIGN-TYPE: 2; signed GET query handling is deterministic and consistent with what is sent; wallet_balance signs/sends accountType=UNIFIED; safe retCode classifications added for 10002/10003/10004/10005/10006/10007/10010; 10006 remains exit code 2 / inconclusive; no raw retMsg or raw response body exposure; wallet smoke output remains sanitized; no query-api, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
- Stage 53-B2c.1b query-api read-only preflight harness: ACCEPTED / PUSHED / REMOTE-VISIBLE on HEAD 00d84d8; get_query_api_info() supports signed read-only GET /v5/user/query-api; sanitized ApiKeyInfo model; scripts/smoke_query_api.py exists; no-flag latch exits 3 with sanitized authorization_required JSON; success output exact approved field set; operation and endpoint_family absent from success output; unsafe readOnly/permissions/expiry metadata fail closed; stale and malformed expiredAt regression tests exist; rate limit remains exit 2 / inconclusive; no real query-api execution, credentials use, Bybit call, real wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring, or runtime readiness
- Stage 53-B2c.1c real query-api preflight: BLOCKED; attempted once and failed safely with retCode=10003, error_category=invalid_key_or_environment, LASTEXITCODE=1; likely ordinary/mainnet Bybit key used against testnet API endpoint, or no usable Bybit testnet API access; no further query-api retry is authorized
- Stage 53-B2d real wallet_balance testnet smoke: BLOCKED / NO-GO because usable Bybit testnet API credentials are unavailable; ordinary/mainnet Bybit key must not be substituted into the testnet flow; any mainnet read-only smoke requires a new separately authorized stage and guardrails, not continuation of B2d
- Stage 53-B2 testnet API access runbook: DOCUMENTED in docs/STAGE_53B2_SMOKE_PLAN.md; use `https://testnet.bybit.com` and `https://testnet.bybit.com/app/user/api-management`; keys from ordinary Bybit mainnet / `www.bybit.com` must not be used in the B2 testnet flow; key type must be API Transaction / Транзакция API, read-only only, with withdrawal/transfer/trade/order/write disabled; `BYBIT_B1_ENVIRONMENT=testnet`; `BYBIT_B1_API_KEY` and `BYBIT_B1_API_SECRET` must come from the same testnet key pair; generic `BYBIT_API_KEY` / `BYBIT_API_SECRET` should be missing during B2 flow; recovery requires safe env presence/hygiene check, no-flag latch LASTEXITCODE=3, explicit Human Owner authorization, exactly one query-api preflight, and no automatic retry
- Stage 53-B2c.1 authenticated readiness audit / query-api preflight decision: B2c.1a and B2c.1b implementation checkpoints are code/test ready for mocked/local behavior only; private real testnet path is blocked due unavailable usable Bybit testnet API access
- Stage 53-B2 permanent real-smoke preflight: safe credential presence check, safe credential hygiene check, and Human Owner external key active/not expired confirmation are REQUIRED before any real Bybit smoke gate; any missing required env var, hygiene warning, expired/uncertain key, or missing owner confirmation stops the smoke
- 7-day note is not treated as verified API key expiry; if secret availability is uncertain, recreate the testnet key rather than exposing or guessing it
- Bybit auth/signing helper, timestamp/recv_window handling, redaction helpers, minimal ServerTime model, read-only client skeleton, and get_server_time() only: PRESENT
- get_wallet_balance(), wallet balance read-only models, Decimal numeric values, redacted repr()/model_dump(), sanitized wallet errors, and mocked tests: PRESENT
- get_open_positions(), open-position read-only models, Decimal numeric values, redacted repr()/model_dump(), sanitized open-position errors, and mocked tests: PRESENT
- Mocked tests for auth and get_server_time skeleton behavior: PRESENT
- B2c wallet_balance smoke harness and mocked tests: PRESENT
- B2c.1a authenticated readiness hardening: PRESENT
- B2c.1b query-api read-only preflight harness and mocked tests: PRESENT
- Service startup wiring for B1 client: NOT PRESENT
- B2b real server_time smoke execution: SUCCESS for server_time only; LASTEXITCODE=0; elapsed_ms=1534; sanitized output only
- Credentials use for smoke: USED LOCALLY ONLY by Human Owner for B2b; credentials must not be stored or disclosed
- B2c.1c real query-api retry: NOT AUTHORIZED / BLOCKED
- B2d real wallet_balance smoke and open_positions smoke: NOT AUTHORIZED / NOT RUN; B2d testnet path is BLOCKED because usable Bybit testnet API credentials are unavailable
- Mainnet read-only smoke: NOT AUTHORIZED; would require a new separately authorized stage
- Query-api `/v5/user/query-api`: NOT IN CURRENT B1/B2 ENDPOINT SET; separate Human Owner decision required; if authorized, read-only preflight only and must not print raw permissions, IDs, raw response body, API key, or API secret
- Signing audit before B2d: B2c.1a implemented deterministic signed/sent GET query handling, `X-BAPI-SIGN-TYPE: 2`, and safe retCode classification; query-api remains a separate Human Owner decision and B2d remains unauthorized
- Order status, place_order, cancel_order, set_leverage, withdraw, transfer, live_reconcile, live_execution: NOT PRESENT
- Real Bybit server_time connectivity verification: PRESENT for B2b only; wallet_balance/open_positions connectivity and real credential permission verification remain NOT PRESENT
- Stage 53-B implementation beyond Slice 3 open_positions: BLOCKED; separate explicit approval required
- Unsupervised production live: NO-GO

Last accepted evidence:
- Stage 53-B2 Pit-stop audit record:
  - Classification: Pit-stop audit only, not an implementation gate.
  - Repo state during audit: HEAD and origin/main aligned at 8153c61 docs: add Stage 53-B2 testnet API runbook; tracked diff was empty.
  - Cleanup follow-up: generated `.pytest-temp-run/` artifact from requested pytest `--basetemp` run was removed in the follow-up cleanup.
  - Control state preserved: B2d real wallet_balance testnet smoke remains blocked / NO-GO because usable Bybit testnet API access is unavailable; B2c.1c real query-api failed safely with retCode=10003 invalid_key_or_environment due no usable testnet API access / environment mismatch.
  - Authorization state preserved: no mainnet smoke, no real query-api retry, no real wallet_balance smoke, no open_positions smoke, no order_status, no write/live methods, and no service wiring are authorized.
  - Readiness boundary preserved: no runtime readiness, trading readiness, live readiness, or probe readiness is claimed.
  - Full local regression evidence: `python -m pytest -q --ignore=research --basetemp=.pytest-temp-run` passed with 408 passed, 5 warnings.
  - Targeted suite evidence: `tests/scripts` 60 passed; `tests/libs/exchange` 99 passed; `tests/libs/config` 19 passed.
  - No-flag latch evidence: `smoke_server_time`, `smoke_wallet_balance`, and `smoke_query_api` all returned sanitized authorization_required JSON with LASTEXITCODE=3.
  - Env hygiene evidence: checked BYBIT_B1_ENVIRONMENT, BYBIT_B1_API_KEY, BYBIT_B1_API_SECRET, BYBIT_API_KEY, and BYBIT_API_SECRET by name only; all were missing; no values, lengths, prefixes, suffixes, hashes, masks, or derived values were printed.
  - Issues found: 5 async mock warnings remain; Engineering Rules v2 transaction ownership is partial; handler-level secret redaction is not evident; future risks remain around authority map, reconciliation, TradingState, OMS, dependency drift, docs drift, and runtime observability.
  - Pit-stop backlog: clean async mock warnings; add env-isolation guard tests; add static guard for generic BYBIT_API_KEY/BYBIT_API_SECRET in B2 flow; follow-up audit on transaction ownership; follow-up audit on handler-level log redaction; future authority map / reconciliation / TradingState / OMS planning; dependency and secret-scan review; periodic docs source-of-truth audit.
- Stage 53-B2c.1c/B2d blocked-state evidence:
  - Real query-api preflight was attempted once and failed safely: retCode=10003, error_category=invalid_key_or_environment, LASTEXITCODE=1.
  - Likely cause: ordinary/mainnet Bybit key used against testnet API endpoint, or no usable Bybit testnet API access.
  - Human Owner confirmed Bybit testnet API key cannot be used / is unavailable and the ordinary Bybit key must not be used for the existing testnet flow.
  - B2c.1c query-api retry is not authorized.
  - B2d real wallet_balance testnet smoke is blocked / NO-GO because usable Bybit testnet API credentials are unavailable.
  - Any mainnet read-only smoke would require a new separately authorized stage, not continuation of B2d.
  - Testnet API access runbook now documents the testnet URL, API Management URL, correct API Transaction / Транзакция API key type, read-only permission requirements, environment variable shape, generic alias avoidance, retCode 10003 troubleshooting tree, and safe restart path.
  - B2d remains blocked until query-api preflight succeeds or the Human Owner explicitly accepts a documented alternative.
  - Preserved evidence: B2b public server_time success; B2c/B2c.1a/B2c.1b mocked/local/code readiness.
  - Not verified: runtime readiness, trading readiness, live readiness, probe readiness, real wallet_balance smoke, open_positions smoke, order_status, service startup wiring.
- Stage 53-B2c.1b query-api read-only preflight harness ACCEPTED / PUSHED / REMOTE-VISIBLE: 00d84d8 feat: add Stage 53-B2 query-api preflight harness
  - Classification: code-ready candidate / accepted implementation checkpoint; test-ready for mocked query-api preflight behavior only; not runtime-ready.
  - Exists: get_query_api_info() signed read-only GET /v5/user/query-api support; sanitized ApiKeyInfo model with boolean/status summary fields; scripts/smoke_query_api.py; tests/scripts/test_smoke_query_api.py; direct no-flag latch exits 3 with sanitized authorization_required JSON.
  - Success output exact approved field set: endpoint, status, exchange, read_only, permissions_safe, key_active, deadline_days_present, expired_at_present, elapsed_ms. Operation and endpoint_family are absent from success output.
  - Safety behavior: unsafe readOnly, unsafe permissions, expired/non-positive/missing/stale/malformed expiry metadata fail closed; stale and malformed expiredAt regression tests exist; rate limit remains exit code 2 / inconclusive.
  - Does not exist / is not authorized: real query-api execution; credentials use; Bybit call; real wallet_balance smoke; open_positions smoke; order_status; write/live methods; service wiring.
  - Not verified: runtime readiness, trading readiness, live readiness, probe readiness, real query-api execution, real wallet_balance smoke, open_positions smoke, order_status, service startup wiring.
  - B2d wallet_balance real smoke remains unauthorized until separate Human Owner decision. No automatic progression and no automatic retry are allowed.
- Stage 53-B2c.1a authenticated readiness hardening ACCEPTED / PUSHED / REMOTE-VISIBLE: 189cb0a feat: harden Stage 53-B2 authenticated smoke readiness
  - Classification: code-ready candidate / accepted implementation checkpoint; test-ready for mocked/local authenticated-readiness hardening only; not runtime-ready.
  - Exists: unsigned public `/v5/market/time` methodology for server_time; get_server_time no longer requires credentials; private reads still fail closed without credentials; private signed reads include `X-BAPI-SIGN-TYPE: 2`; deterministic signed GET query handling consistent with what is sent; wallet_balance signs/sends `accountType=UNIFIED`; safe retCode classifications for 10002 timestamp_or_recv_window_error, 10003 invalid_key_or_environment, 10004 invalid_signature, 10005 permission_denied, 10006 rate_limited, 10007 authentication_failed, and 10010 ip_mismatch; 10006 remains exit code 2 / inconclusive in smoke harnesses.
  - Output safety: no raw retMsg or raw response body exposure; wallet smoke output remains sanitized.
  - Does not exist / is not authorized: query-api support; real wallet_balance smoke; open_positions smoke; order_status; write/live methods; service wiring.
  - Test evidence: server_time no-flag latch LASTEXITCODE=3; wallet_balance no-flag latch LASTEXITCODE=3; tests/scripts: 40 passed; tests/libs/exchange: 86 passed; tests/libs/config: 19 passed.
  - Not verified: runtime readiness, trading readiness, live readiness, probe readiness, real wallet_balance smoke, open_positions smoke, order_status, service startup wiring.
  - B2d wallet_balance real smoke remains unauthorized until separate Human Owner decision. No automatic progression and no automatic retry are allowed.
- Stage 53-B2c wallet_balance smoke harness ACCEPTED / PUSHED / REMOTE-VISIBLE: c9b1337 feat: add Stage 53-B2 wallet-balance smoke harness
  - Classification: code-ready candidate / accepted implementation checkpoint; test-ready for mocked wallet_balance smoke harness behavior only; not runtime-ready.
  - Exists: scripts/smoke_wallet_balance.py; tests/scripts/test_smoke_wallet_balance.py; wallet_balance smoke harness; mocked tests; direct no-flag latch exits 3 with authorization_required JSON; --allow-real-smoke required for real-capable path.
  - Mocked success output is sanitized and includes only endpoint/status/exchange/account_type/coins_count/elapsed_ms.
  - Does not exist / is not authorized: real wallet_balance smoke; credentials use for B2c implementation; open_positions smoke; order_status; write/live methods; service wiring.
  - Test evidence: tests/scripts/test_smoke_wallet_balance.py: 14 passed; tests/scripts: 28 passed; tests/libs/exchange: 78 passed; tests/libs/config: 19 passed after clearing BYBIT_B1 env vars.
  - Operational hygiene lesson: config suite initially failed because real BYBIT_B1 env vars from B2b smoke were still present; after clearing env vars it passed. This is not classified as a B2c code failure.
  - Not verified: runtime readiness, trading readiness, live readiness, probe readiness, real wallet_balance smoke, open_positions smoke, order_status, service startup wiring.
  - B2d wallet_balance real smoke remains unauthorized until separate Human Owner decision.
- Stage 53-B2c.1 authenticated readiness audit / query-api preflight decision:
  - Required before B2d real wallet_balance smoke.
  - Not real wallet smoke; must not call wallet_balance or open_positions.
  - Does not authorize order_status or write/live methods.
  - Must audit signing/query-string behavior, signed vs unsigned server_time behavior, `X-BAPI-SIGN-TYPE: 2`, whether to add `/v5/user/query-api`, and key active/not expired wording.
  - `/v5/market/time` is public and should be treated as unsigned connectivity/time; B2b remains valid as a real testnet connectivity checkpoint, but signed server_time usage should be tracked as an audit/backlog issue if present.
  - Query-api is a scope expansion requiring explicit Human Owner decision; if authorized, it is read-only preflight only.
  - Current authorized state: READ_ONLY_TESTNET_SMOKE.
  - Future READ_ONLY_ACTIVE / READ_ONLY_DEGRADED / READ_ONLY_HALTED, OMS, reconciliation, kill switch, risk controls, runbook, write client, ExchangePort refactor, dependency changes, CI secret scanning, and service wiring remain future-gate/backlog concepts only.
- Stage 53-B2b real server_time smoke SUCCESS:
  - Command: python scripts\smoke_server_time.py --allow-real-smoke
  - LASTEXITCODE=0; elapsed_ms=1534; output was sanitized.
  - Sanitized output fields included endpoint server_time, endpoint_family server_time, exchange bybit, operation bybit_b1_server_time_smoke, status success, timestamp_second, and timestamp_nano.
  - Credentials were used locally only and must not be stored, disclosed, logged, committed, or pasted into chat.
  - Not run / not authorized: wallet_balance smoke, open_positions smoke, order_status, write/live methods, service wiring.
  - Not verified: runtime readiness, trading readiness, live readiness, probe readiness, wallet_balance connectivity, open_positions connectivity, order_status, service startup wiring.
  - B2d wallet_balance real smoke remains unauthorized until separate Human Owner decision.
- Stage 53-B2a server_time smoke harness ACCEPTED / PUSHED / REMOTE-VISIBLE: a511e2f feat: add Stage 53-B2 server-time smoke harness
  - Classification: code-ready candidate / accepted implementation checkpoint; test-ready for mocked B2a behavior only; not runtime-ready.
  - Exists: server_time smoke harness; mocked tests; direct no-flag latch exits 3 with authorization_required JSON.
  - Does not exist / is not authorized: real smoke execution; credentials use; wallet_balance smoke; open_positions smoke; order_status; write/live methods; service wiring.
  - Test evidence: python scripts\smoke_server_time.py: LASTEXITCODE=3 with sanitized authorization_required JSON; python -m pytest tests\scripts\test_smoke_server_time.py -q --basetemp=.pytest-temp-run: 14 passed; python -m pytest tests\libs\exchange -q: 78 passed; python -m pytest tests\libs\config -q: 19 passed.
  - Not verified: runtime readiness, real Bybit connectivity, real credentials, B2b real server_time smoke, wallet_balance smoke, open_positions smoke, order_status, service startup wiring, live/probe/trading readiness.
- Stage 53-B1 Slice 3 open_positions ACCEPTED / PUSHED / REMOTE-VISIBLE: 0596afb feat: add Bybit B1 read-only open positions
  - Classification: code-ready candidate / accepted implementation checkpoint; test-ready for mocked open_positions behavior only; not runtime-ready.
  - Exists: get_open_positions(); open-position read-only models; Decimal numeric values; redacted repr() / model_dump(); sanitized open-position errors; mocked tests.
  - Does not exist: order_status; place_order; cancel_order; set_leverage; withdraw; transfer; live_reconcile; live_execution; service startup wiring; real Bybit connectivity verification; real credential verification.
  - Test evidence: python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 39 passed; python -m pytest tests\libs\exchange -q: 78 passed; python -m pytest tests\libs\config -q: 19 passed.
  - Not verified: runtime readiness, real Bybit connectivity, real credentials, order_status, service startup wiring, live/probe/trading readiness.
- Stage 53-B1 Slice 2 wallet_balance ACCEPTED / PUSHED: 66a898d feat: add Bybit B1 read-only wallet balance
  - Exists: get_wallet_balance(); wallet balance read-only models; Decimal numeric values; redacted repr() / model_dump(); sanitized wallet errors; mocked tests.
  - Test evidence: python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 33 passed; python -m pytest tests\libs\exchange -q: 72 passed; python -m pytest tests\libs\config -q: 19 passed.
  - Not verified: runtime readiness, real Bybit connectivity, real credentials, open_positions, order_status, service startup wiring, live/probe/trading readiness.
- Stage 53-B1 Slice 1 server-time skeleton ACCEPTED / PUSHED: 828b64a feat: add Bybit B1 read-only server-time skeleton
  - Exists: Bybit auth/signing helper; timestamp / recv_window handling; redaction helpers; minimal ServerTime model; read-only client skeleton; get_server_time() only; mocked tests.
  - Test evidence: python -m pytest tests\libs\exchange\test_bybit_auth.py tests\libs\exchange\test_bybit_read_only.py -q --basetemp=.pytest-temp-run: 28 passed; python -m pytest tests\libs\exchange -q: 67 passed.
  - Not verified: runtime readiness, real Bybit connectivity, real credentials, wallet balance, open positions, order status, service startup wiring, live/probe/trading readiness.
- Stage 53-A CLOSED: 3b3b06f
- Stage 53-B design lock CLOSED: 5e5eb48
- Status docs after 53-B design lock CLOSED: 69176ed
- Stage 53-B owner decision tracker ADDED: e814031
- Stage 53-B gate/status handoff cleanup ADDED: 3d72ba8
- Stage 53 design lock decisions cleanup ADDED: ff2f30c
- Q1-FIX-1 recover_position payload validation MERGED
- Q1-FIX-2 freshness naive datetime handling MERGED
- Q1-FIX-3 true EMA in snapshot builder MERGED: 1bd8e2a
- Q1 regression gate PASS on main HEAD 1bd8e2a
- B1-CONFIG config-only slice ADDED: c17c7d0
- B1-CONFIG regression on HEAD c17c7d0:
  - python -m pytest tests\libs\config -q: 19 passed
  - python -m pytest tests\libs\exchange -q: 39 passed
  - python -m pytest apps\market_data\tests -q: 8 passed
  - python -m pytest apps -q: 163 passed
  - python -m pytest -q --ignore=./research --basetemp=.pytest_tmp: 288 passed, 5 warnings
- Owner decisions OI-1..OI-9 ANSWERED / APPROVED
- Stage 53-B1 architecture plan ADDED: docs/STAGE_53B1_ARCHITECTURE.md
- B1-OI-1..B1-OI-6 ANSWERED / APPROVED for future Stage 53-B1 implementation planning
- First implementation allowed endpoints: server time/connectivity, wallet balance read-only, open positions read-only
- First implementation excluded: order status, place_order, cancel_order, set_leverage, withdraw, transfer, live reconcile, live execution, production private endpoint access
- Approved Stage 53-B1 maximum scope: Bybit only; testnet/demo only; authenticated client; read-only balances and positions; optional order status read-only; no place order; no cancel order; no live reconcile
- Withdrawal permission forbidden.
- No secrets belong in repo, prompts, docs, or logs.
- Q1 regression results:
  - python -m pytest apps/market_data/tests -q: 8 passed
  - python -m pytest apps/position_manager/tests -q: 36 passed
  - python -m pytest apps -q: 163 passed
  - python -m pytest -q --ignore=research with project-local temp isolation: 269 passed, 5 warnings
- No secrets observed during Q1 regression.
- No live/exchange/private endpoints/orders/cancels/balances/live execution/live reconcile were enabled or observed.
- Final Gate Diff Review completed
- pytest current baseline: HEAD c17c7d0 PASS; non-research suite 288 passed, 5 warnings
- alembic head: 0008_unique_tc_signal_id (local and VPS)
- docker-compose binds postgres/redis to 127.0.0.1
- .env.example uses postgresql+psycopg
- EXECUTION_MODE guard raises RuntimeError at startup if not paper/dry_run (code-verified)
- validate_startup_auth enforces ≥32 char tokens + denylist at startup (code-verified)
- secrets.compare_digest used for all token comparisons (code-verified)
- kill-switch fail-closed for all 4 error classes (AUTH_FAILURE / TIMEOUT / UNAVAILABLE / ERROR) — test-proven
- open_position and close_position journal/alert failures are fail-soft after authoritative DB commit
- halt/resume state + operator_action + journal use one DB commit
- halt/resume failure-injection tests added
- execution-boundary kill-switch typed errors preserved and journaled
- stop-loss / take-profit direction validation enforced at execution boundary
- recover_position journal/alert failures are fail-soft after authoritative DB commit
- no active production call-sites remain for old commit-based position repo methods
- VPS runtime proof complete: Python 3.12.3, Docker 29.4.1, all 9 services healthy, execution-service mode=paper (2026-04-26)

Owner decisions:
- OI-1 through OI-9 are ANSWERED / APPROVED in docs/STAGE_53B_OWNER_DECISIONS.md.
- This does not authorize Stage 53-B implementation.
- This does not authorize live trading.

Allowed work:
- Stage 53-B1 docs/status cleanup and static safety checks
- Further B1 implementation slices only after separate explicit approval

Blocked work:
- Stage 53-B implementation beyond accepted Slice 3 unless separately approved
- Service startup wiring for any Bybit private/read-only client
- B2b real server_time smoke unless separately approved
- Credentials use unless separately approved
- Wallet_balance smoke and open_positions smoke unless separately approved
- Order status implementation
- Order placement, order cancellation, live execution, and live reconcile
- LH-2 paper accumulation
- Real live execution

Next gate:
Stage 54-BG2-C runbook complete; next possible slice is BG2-D mocked private
read-only preflight parser/client skeleton, if separately authorized by the
Human Owner.

Stage 53-B1 maximum scope:
- Bybit only
- Testnet/demo only
- Authenticated client
- Read-only balances and positions
- Order status read-only deferred to a later slice
- No place order
- No cancel order
- No set_leverage
- No live reconcile

Next allowed lane:
Stage 53-B2 docs/status maintenance and Stage 54-BG2/BG2-D follow-up planning; any
Bitget private client, any Bitget private smoke, B2c.1c
query-api retry, B2d real wallet_balance smoke, mainnet read-only smoke,
open_positions smoke, order_status, and any write/live methods require
separate Human Owner authorization.

Constraints:
- Do not claim live-ready.
- Do not start Stage 53-B implementation from the owner-decision sync.
- Keep docs consistent with source-of-truth rules.
- Stage 53-A is CLOSED.
- Live trading remains NO-GO.
- Canonical live blocker taxonomy is the 14 live blockers in docs/STAGE_53_DESIGN_LOCK.md.
- Any 11-blocker list below is historical/legacy/summarized, not the current authoritative count.
- Historical Stage 53-B design-lock generic env vars were BYBIT_API_KEY and BYBIT_API_SECRET; Stage 53-B2 testnet smoke flow uses BYBIT_B1_ENVIRONMENT, BYBIT_B1_API_KEY, and BYBIT_B1_API_SECRET, and generic BYBIT_API_KEY / BYBIT_API_SECRET should be missing during B2 flow.
- Canonical Stage 53-B idempotency rule is client_order_id = execution_id.
- 0009_execution_exchange_fields is deferred beyond Stage 53-B.
- Canonical Bybit public adapter path is libs/exchange/bybit_public.py.

---

## Session: 2026-04-25 (updated — VPS Runtime Proof partial)
pytest: 215 passed, 5 warnings — H-1 closed (recover_position fail-soft fix + 2 regression tests)

### VPS Runtime Proof — Static Proof Complete / Runtime Checks Pending

**Scope limitation:** Docker and Linux system commands are not available in the current Windows dev environment.
Static/code-level proof is complete. VPS-level runtime checks require direct VPS access.

---

#### SECTION 1 — Repo Proof (VERIFIED)

| Check | Result |
|-------|--------|
| `git status` | 19 expected session files modified/untracked. No unwanted changes. |
| `git diff --check` | CLEAN. LF warning on .env.example only (not a blocker). |
| `git diff --stat` | 644 insertions, 81 deletions — matches session scope. |
| `uv run pytest` | **215 passed, 5 warnings, 0 failed** |
| `uv run alembic heads` | **0008_unique_tc_signal_id** |

---

#### SECTION 2 — Network / Container Topology (PARTIALLY VERIFIED)

| Check | Result |
|-------|--------|
| docker-compose.yml postgres binding | `127.0.0.1:5432:5432` — loopback only ✅ |
| docker-compose.yml redis binding | `127.0.0.1:6379:6379` — loopback only ✅ |
| `docker compose ps` (running containers) | **PENDING — requires VPS** |
| `docker ps` (port runtime verification) | **PENDING — requires VPS** |
| `ss -lntup` (actual listening ports) | **PENDING — requires VPS (Linux only)** |
| `sudo ufw status` (firewall rules) | **PENDING — requires VPS (Linux only)** |

---

#### SECTION 3 — Env Safety (STATICALLY VERIFIED)

| Check | Result |
|-------|--------|
| POSTGRES_DSN driver | `.env.example` uses `postgresql+psycopg` (psycopg3 correct) ✅ |
| PAPER_MODE | `.env.example` has `PAPER_MODE=true` ✅ |
| EXECUTION_MODE guard | Startup `lifespan` raises `RuntimeError` if not `paper` or `dry_run` ✅ |
| Token min length | `validate_startup_auth()` enforces ≥ 32 chars + denylist, raises at startup ✅ |
| Token comparison | `secrets.compare_digest` used for all three token types ✅ |
| Service base URLs | Internal container names in .env.example (no public exposure) ✅ |
| EXECUTION_MODE at runtime | Actual VPS env vars **PENDING — requires VPS** |
| Token values at runtime | **PENDING — requires VPS** |

---

#### SECTION 4 — Kill-Switch Safety (STATICALLY VERIFIED)

| Check | Result |
|-------|--------|
| AUTH_FAILURE blocks execution | ✅ confirmed by test |
| KILL_SWITCH_TIMEOUT blocks execution | ✅ confirmed by test |
| KILL_SWITCH_UNAVAILABLE blocks execution | ✅ confirmed by test |
| KILL_SWITCH_ERROR blocks execution | ✅ confirmed by test |
| All 4 error paths write `kill_switch_check_failed` journal event | ✅ confirmed by test |
| halt route writes `kill_switch_halted` in one DB commit | ✅ confirmed by test |
| resume route writes `kill_switch_resumed` in one DB commit | ✅ confirmed by test |
| kill-switch HTTP smoke test (halt→verify→resume) | **PENDING — requires VPS** |

---

#### SECTION 5 — DB Consistency (PENDING)

- Orphan executions (filled, no position) count: **PENDING — requires VPS**
- Open positions with closed executions: **PENDING — requires VPS**
- Candidate stuck in approved/submitted: **PENDING — requires VPS**
- DB accessible and alembic current at runtime: **PENDING — requires VPS**

---

#### SECTION 6 — Service Health (PENDING)

- `systemctl list-units` for uvicorn services: **PENDING — requires VPS**
- `/ready` endpoint for each service: **PENDING — requires VPS**
- `/health` and `/version` responses: **PENDING — requires VPS**

---

#### Static Proof Verdict

**Code-level / static runtime proof: COMPLETE**

All code-derivable safety controls verified:
- EXECUTION_MODE guard enforced at startup
- Token strength enforced at startup (not request-time)
- Kill-switch fail-closed for all 4 error classes
- postgres/redis bound to loopback in compose config
- alembic at correct head
- 215 tests passing

**Runtime-ready: STILL PENDING**

VPS-specific items that must be verified on the actual deployed environment before Runtime-ready can be claimed:
1. `docker compose ps` — containers actually up
2. `ss -lntup` — no unintended external port exposure
3. `sudo ufw status` — firewall active and configured
4. EXECUTION_MODE and token values in actual deployed `.env`
5. Kill-switch HTTP smoke test (halt → verify `kill_switch_active=true` → resume)
6. DB consistency queries (no orphan executions, no stuck candidates)
7. Service `/ready` endpoints returning 200

**Owner decision required:** The human operator must run these 7 checks directly on the VPS before making the START / HOLD decision for the controlled paper probe.

## Session: 2026-04-24 (updated end-of-session)
pytest: 213 passed, 5 warnings (updated from 181 after final session fixes)
alembic head: 0008_unique_tc_signal_id
Shadow trading: COMPLETE
Paper trading: VALIDATED CONTOUR (Stage 52B.41)
Live trading: NOT READY — P1 items pending

## Local runtime setup (2026-04-25)
- All 9 services running: kill_switch, risk_engine, review_gateway, journal_ingest, orchestrator, execution_service, position_manager, dashboard_service, incidents
- execution_service: status=ready, mode=paper
- Postgres + Redis running via Docker on E drive
- Alembic migrations: head 0008
- start-local-runtime.ps1 created for repeatable startup
- Working Protocol documented in AI_COMMANDS.md

## VPS Runtime Proof (2026-04-26)

### VPS details
- Provider: Beget
- IP: 45.145.5.254
- OS: Ubuntu 24.04.4 LTS
- Path: /opt/trading-system

### Confirmed
- Python 3.12.3
- Git 2.43.0
- Docker 29.4.1 + Compose v5.1.3
- 211 tests passing
- Alembic head: 0008
- Postgres + Redis running (hephaestus-system containers)
- All 9 services healthy
- execution-service: status=ready, mode=paper

### LH-1 status
COMPLETE — paper runtime proven on both local (E drive) and VPS.

## Live Path Audit (2026-04-25 historical/legacy summary)

### Key finding
Paper trading pipeline is complete and tested.
Live exchange layer does not exist.
Switching EXECUTION_MODE=live crashes at startup (RuntimeError in execution_service/main.py).

### Live blockers (legacy/summarized 11-item list, not current authoritative taxonomy)

Current authoritative taxonomy: 14 canonical live blockers in docs/STAGE_53_DESIGN_LOCK.md.
1. No authenticated exchange client (no place_order, cancel_order, get_order_status, get_balance)
2. place_order.py hard-rejects non-paper mode (ValueError)
3. No order status polling loop — instant DB fill is not valid for live
4. entry_price from signal, not from exchange fill confirmation
5. position close sends no exchange order — DB only
6. No balance/margin check before order placement
7. No rate limit handling on exchange calls
8. No partial fill handling
9. Live reconcile scheduler blocked — paper-only guard
10. Symbol format OKX-only (BTC-USDT) — Bybit needs BTCUSDT
11. cancel_order sends no exchange request — DB only

### What exists
- Complete paper trading pipeline (paper mode only)
- All auth/security/kill-switch hardening (S-1..S-9)
- Local runtime: 9 services running, 211 tests passing

### Roadmap to controlled live
Stage 53-A: Bybit market data adapter
Stage 53-B: Authenticated exchange client (place/cancel/status/balance)
Stage 53-C: Live execution path (replace paper stub)
Stage 53-D: Live reconcile scheduler
Stage 53-E: Tests + exchange smoke tests
Stage 53-F: Controlled live — 1 trade, manual approval

## Completed stages
23-42, 38c, 38d, 43, 44, 45, 46, 47, 48, 49, 50, 51
52A, 52C, 52B.3, 52B.4, 52B.23, 52B.27
53A.1, 53A.3
Research: B1, B4, B4.1, B4.2

## Active
Stage LH-1 live-hardening — P1 items remaining before full live-readiness audit

## Security fixes (2026-04-24)

Security audit completed — 9 fixes implemented (S-1 through S-9). `docs/SECURITY.md` created.

S-1: Duplicate-execution path now emits `position_open_failed` journal event (was silent)
S-2: `validate_startup_auth()` enforces token minimum length (32 chars) and denylist at startup
S-3: `OrphanDetector` now runs on 60 s schedule via `orphan_scheduler` (was on-demand only)
S-4: `/halt` endpoint now writes `kill_switch_halted` journal event atomically with state change
S-5: E2E auth money-path proof — 8 test scenarios passing (`tests/test_auth_money_path.py`)
S-6: Network boundary and inter-service topology documented in `docs/SECURITY.md`
S-7: Token rotation runbook (generate → update → rolling restart → verify) in `docs/SECURITY.md`
S-8: Kill-switch error taxonomy — `AUTH_FAILURE` / `KILL_SWITCH_TIMEOUT` / `KILL_SWITCH_UNAVAILABLE` / `KILL_SWITCH_ERROR`
S-9: Kill-switch block and error paths now write `kill_switch_blocked` / `kill_switch_check_failed` journal events

## Today's fixes (2026-04-24)

TD-14 CLOSED — sync httpx converted to async across money-path:
- `libs/messaging/journal_client.py` and `apps/position_manager/infrastructure/journal_client.py` converted
- 23 additional files updated

TD-16 CLOSED — DB startup health check added to 8 services via `libs/db/startup_health.py`

TD-18 CLOSED — `OkxMarketDataFetcher` moved from `research/` to `libs/clients/okx_market_data_fetcher.py`

TD-19 (53A.12) CLOSED — DB-backed `max_open_positions` cap gate with advisory lock (closed last session, confirmed)

TD-20 CLOSED — approve/reject journaling now DB-atomic (Option A: same-transaction pattern as TD-12)

Additional fixes:
- `approve_candidate.py` HTTPError early-commit bug fixed
- `execution_service` direct import of `position_manager` replaced with `HttpPositionManagerClient`
- Execution persisted without position open: added `position_open_failed` status + journal event

## Shared Rules (Project-wide Code Discipline)
1. Expand Critical Findings
- After any critical bug, inspect adjacent paths for the same failure class.
2. Enforce on Authoritative Boundaries
- Money-relevant controls must be enforced at authoritative boundaries, not only pre-checks.
3. Fix Root Cause, Not Only Symptom
- Do not treat symptom removal as full resolution.
4. Require Code + Tests + Runtime Proof
- Runtime-critical acceptance requires code, tests, and runtime confirmation.
5. Keep Shared Project Memory
- Confirmed bottlenecks, acceptance facts, and operational lessons must be written to shared docs.
6. Change One Variable at a Time
- Runtime experiments should change only one variable per test.
7. Prefer Safety Over Throughput
- Integrity/safety wins over throughput tuning.
8. Advisory Must Not Become Authority
- AI/research/advisory context must not silently become execution authority.
9. Use Minimal Safe Fixes First
- First close risk with minimal safe changes, then refactor if needed.
10. Mandatory Review After Integrity Gaps
- After critical integrity findings, review both the fix and adjacent same-class paths.
11. Docs Must Reflect Confirmed Reality
- Explicitly separate planned / implemented / runtime-validated.
12. Separate Active Issues from Residue
- Distinguish active problems from historical residue and harmless noise.

## Long-range roadmap (post current paper validation)

### Deferred option: Transactional Outbox (Journal Reliability)

- Problem addressed: cross-service journal reliability when an HTTP write can fail after an authoritative DB write.
- Pattern: in one DB transaction persist `trade_candidates` plus an `outbox_events` row; a separate deliverer loop/job
  publishes outbox → `journal_events` (via HTTP or direct DB) with retries and idempotency.
- Why deferred: higher implementation surface area (schema + deliverer + operational lifecycle).
- When to revisit: after current P1 live blockers are closed, or if we move journal storage behind a true service boundary
  (no shared DB) and need guaranteed delivery semantics.
Planning stages below are not immediate execution steps. They are sequenced after current Stage 52B / 53A history and preserve authority boundaries.

Execution order principle:
- first hardening
- then accumulation/stats
- then offline/advisory intelligence
- then shadow portfolio control
- then authoritative portfolio control

LH-1 - live-hardening baseline
- Purpose: close live-risk TDs and stabilize runtime/response/idempotency/HTTP/health discipline before new AI roles.

LH-2 - paper history + stats truth accumulation
- Purpose: accumulate enough paper trades and stable statistics to support later analyst layers.

53A - extension points for future intelligence
- Purpose: add placeholders/config hooks/feature flags without changing authority behavior.

53B - post-trade analyst MVP
- Purpose: offline/batch analytics over journal, executions, positions, closes.

53C - ops copilot / incident analyst MVP
- Purpose: advisory ops summaries, incident grouping, operator briefing.

54A - regime analyst advisory
- Purpose: advisory-only regime context generation.

54B - review enrichment by regime
- Purpose: optional advisory regime context in review, no hard reject from AI alone.

55A - portfolio manager shadow mode
- Purpose: compute heat/concentration/correlation limits in shadow only.

55B - portfolio manager authoritative mode
- Purpose: real portfolio gating only after shadow validation.

## Accepted result
Stage 52B.27 accepted:
- orchestrator no longer hangs on unreachable journal host
- journal failure is fail-fast and surfaced explicitly

Stage 52B.39 checkpoint:
- Validated paper contour end-to-end:
  - candidate created
  - candidate approved
  - execution created (paper filled)
  - position opened
  - manual close
  - reconcile close on missing exchange snapshot
- Remaining unvalidated close-trigger branches (require exchange snapshot scenarios):
  - stop-loss trigger close
  - take-profit trigger close
  - ttl expiry trigger close
  - cancel/external exchange status branches (`cancelled` / `expired`)
- Known non-blocking issues from review:
  - close_price can be null on reconcile close -> downstream stats may compute PnL as 0
  - `PositionCloseRequest` contract/comment should be tightened before live (non-manual closes)

Stage 52B.41 final checkpoint:
- Validated paper contour:
  - candidate creation
  - approve
  - execution
  - position open
  - manual close
  - reconcile close on missing snapshot
  - stop-loss close
  - take-profit close
  - ttl expiry close
  - external cancelled close
  - external expired close
- Known non-blocking issues (paper):
  - `position_repo.to_dict` missing `@staticmethod`
  - `HttpAlertClient` uses sync `httpx.post()` (TD-14 applies; not a paper blocker with `NoopAlertClient`)
  - `close_price` nullable in some close paths can skew stats/PnL interpretation
  - `PositionCloseRequest` contract/comment should be tightened before live
- Live-only risk focus (see `docs/AI_COMMANDS.md` TD table):
  - TD-14 through TD-16 remain open before live-oriented confidence
- Status:
  - paper contour validated
  - live not ready

Stage 53A.12 confirmed risk:
- `max_open_positions` enforcement gap confirmed under paper runtime burst.
- Mechanism:
  - stale runner-side open-position snapshot (TOCTOU window)
  - max-open check applied only in pre-risk runner path
  - no authoritative re-check in approve / execution / position-open stages
- Observed result:
  - 6 open paper positions were created while config cap remained `max_open_positions: 1`
- Classification:
  - live-risk issue
  - requires explicit TD tracking before live-oriented confidence

TD-11 closed:
- `DbJournalClient` now lives in `libs/messaging/journal_client.py`.
- Service layers use the shared client directly or thin re-export wrappers only.

TD-12 closed (LH-1.2):
- Candidate creation + `candidate_created` journaling are now atomic in DB.
- If the journal event cannot be written, the candidate is not persisted.

TD-13 closed (LH-1.3):
- `/v1/pipeline/evaluate` is retry-safe and idempotent on `signal_id`.
- `trade_candidates.signal_id` is now unique; retries return `CANDIDATE_EXISTS` instead of creating duplicates.

## Open P1 items (next session — required before live-readiness audit)

| ID | Problem | Priority |
|----|---------|----------|
| P1-1 | Dashboard hardcoded paper mode | ✅ closed |
| P1-2 | `correlation_id` lost in error responses | ✅ closed |
| P1-3 | `reconcile_scheduler` swallows exceptions silently | ✅ closed |
| P1-4 | `journal_client` dead parameter + incorrect wiring in `main.py` | ✅ closed (fixed pre-LH-1.6) |
| P1-5 | FastAPI `on_event` deprecation — migrate to `lifespan` | ✅ closed (all services use lifespan) |

## Pre-live checklist

- [x] All P0 TDs closed
- [x] P1 items resolved (see table above)
- [ ] Full audit (Claude + Codex + GPT-4)
- [x] Security audit
- [ ] Live

## TD history

TD-12: journal gap after candidate persistence ✅ closed (LH-1.2)
TD-13: response consistency / duplicate candidate ✅ closed (LH-1.3)
TD-14: sync httpx audit across money-path ✅ closed (2026-04-24)
TD-16: DB startup health check absent ✅ closed (2026-04-24)
TD-18: paper runtime fetcher coupling ✅ closed (2026-04-24)
TD-19 (53A.12): max_open_positions enforcement gap ✅ closed (2026-04-24)
TD-20: approve/reject journaling not DB-atomic ✅ closed (2026-04-24)
