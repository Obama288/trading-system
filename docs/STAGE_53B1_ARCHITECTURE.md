# Stage 53-B1 Architecture Plan

## 1. Objective

Define the architecture plan for a future Stage 53-B1 implementation slice.

Stage 53-B1 is planning / architecture only in this PR. Stage 53-B1 implementation has not started.

The planned implementation, if separately approved later, is a Bybit testnet/demo authenticated read-only client for balances and positions, with optional read-only order status. It must not enable live trading, production private endpoint access, order placement, order cancellation, live execution, or live reconcile.

OI-1..OI-9 are already answered/approved and merged in PR #8. Future implementation questions in this document are not blockers for this docs-only architecture PR.

## 2. Non-goals

- No runtime code changes.
- No tests changed.
- No infra/config/dependency changes.
- No API keys or secrets.
- No account UID, email, balances, or signed payloads in repo, prompts, docs, or logs.
- No Bybit client implementation in this PR.
- No private endpoint implementation in this PR.
- No place_order.
- No cancel_order.
- No live reconcile.
- No live execution.
- No production private endpoint access.
- No claim that live trading is ready.
- No change to the authority model.
- No change to the pipeline: signal -> risk -> review -> orchestrator -> execution_service -> position_manager.

## 3. Allowed Scope

The maximum future Stage 53-B1 implementation scope is:

- Bybit only.
- Testnet/demo only.
- Authenticated client.
- Read-only wallet balance.
- Read-only open positions.
- Optional read-only order status.
- Server time / connectivity check if needed.
- Explicit startup/runtime guards to prevent production/live use.
- Logging redaction and secret-safety controls.
- Unit tests and mocked HTTP tests only unless separately approved.

## 4. Forbidden Scope

Stage 53-B1 must not include:

- place_order.
- cancel_order.
- withdraw.
- transfer.
- set_leverage unless a future owner-approved stage allows it.
- Live reconcile.
- Live execution.
- Production private endpoint access.
- Service startup wiring into execution_service, position_manager, orchestrator, risk_engine, review_gateway, dashboard, or kill_switch.
- Any order routing, order creation, order cancellation, fill processing, or position mutation.
- Any change to risk authority, kill-switch authority, review authority, execution_service authority, position_manager authority, dashboard read-only behavior, or journal audit-only behavior.

## 5. Proposed Module/File Boundaries

Future implementation may introduce or modify only narrowly scoped exchange-library and exchange-test files after separate approval.

Recommended future files:

- `libs/exchange/bybit_read_only.py`
- `libs/exchange/bybit_auth.py`
- `libs/exchange/bybit_models.py`
- `libs/exchange/errors.py`
- `tests/libs/exchange/test_bybit_read_only.py`
- `tests/libs/exchange/test_bybit_auth.py`

The client should remain a library component. It must not be imported by application startup paths in Stage 53-B1.

The client should expose read-only query methods and typed response models. It should not expose command methods that mutate exchange state.

## 6. Secret Handling Model

- Local testnet credentials may be read from process environment variables only.
- Secret manager or GitHub secrets may be used later for CI or deployment, if separately approved.
- No secrets belong in repo, prompts, docs, logs, screenshots, test fixtures, cassettes, or error messages.
- No account UID, email, balances, or signed payloads may be committed.
- Logs must redact:
  - API key.
  - API secret.
  - signatures.
  - signed payloads.
  - auth headers.
  - account identifiers.
  - balances.
- Any missing credential must fail closed for the explicit client call, not fall back to production or public defaults.

## 7. Read-Only Bybit Testnet/Demo Client Interface

Future client shape, subject to separate implementation approval:

```python
class BybitReadOnlyClient:
    async def get_server_time(self) -> ServerTime: ...
    async def get_wallet_balance(self) -> WalletBalance: ...
    async def get_open_positions(self) -> list[OpenPosition]: ...
    async def get_order_status(self, order_id: str | None = None, order_link_id: str | None = None) -> OrderStatus: ...
```

`get_order_status` is optional for the first implementation slice. If included, it must be read-only and must not poll newly placed orders because Stage 53-B1 cannot place orders.

All methods are queries. They must not create, cancel, amend, transfer, withdraw, set leverage, or reconcile anything.

## 8. Allowed Methods

- Server time / connectivity check if needed.
- Read-only wallet balance.
- Read-only open positions.
- Optional read-only order status.

## 9. Explicitly Forbidden Methods

- `place_order`.
- `cancel_order`.
- `withdraw`.
- `transfer`.
- `set_leverage` unless future owner-approved stage allows it.
- `live_reconcile`.

No method with exchange-side mutation is allowed in Stage 53-B1.

## 10. Startup/Runtime Guards

Future implementation should include fail-closed guards:

- Environment must identify testnet/demo only.
- Production/private live base URLs must be rejected in Stage 53-B1.
- Missing or malformed credentials must fail closed.
- Read-only API key expectation must be documented and validated where Bybit exposes enough metadata.
- Withdrawal permission must be forbidden.
- The client must not start automatically with any service.
- The client must not run from application startup.
- The client must not be wired into execution_service, position_manager, orchestrator, risk_engine, or live reconcile.
- Any accidental call to a forbidden method should be impossible because the method should not exist in B1.

## 11. Logging Redaction Rules

Logs may include:

- operation name.
- sanitized endpoint category.
- request correlation ID.
- Bybit retCode and retMsg when safe.
- elapsed time.
- typed error class.

Logs must not include:

- API keys.
- API secrets.
- signatures.
- signed payloads.
- account UID.
- email.
- balances.
- raw wallet payloads.
- raw position payloads.
- auth headers.
- full URLs containing signed query strings.

Error messages returned to callers should be sanitized and typed.

## 12. Test Strategy

Future implementation tests should be mocked by default:

- HMAC signing input construction without exposing real secrets.
- Timestamp and recv_window validation.
- Testnet/demo guard rejects production/live configuration.
- Missing credentials fail closed.
- Read-only wallet balance maps to typed model.
- Read-only open positions maps to typed model.
- Optional order status maps to typed model.
- Forbidden methods do not exist.
- Logs redact secrets, signatures, account identifiers, balances, and raw payloads.
- Bybit error codes map to typed errors.

Current Q1 regression PASS remains the latest baseline:

- `python -m pytest apps/market_data/tests -q`: 8 passed.
- `python -m pytest apps/position_manager/tests -q`: 36 passed.
- `python -m pytest apps -q`: 163 passed.
- `python -m pytest -q --ignore=research` with project-local temp isolation: 269 passed, 5 warnings.

## 13. QA Checklist

- Docs-only architecture PR changes only approved docs.
- Stage 53-B1 implementation has not started.
- OI-1..OI-9 are referenced as answered/approved and merged in PR #8.
- Paper trading only is preserved.
- Live trading remains NO-GO.
- No production private endpoint access is authorized.
- Maximum scope is Bybit testnet/demo authenticated read-only balances and positions, with optional read-only order status.
- No place_order.
- No cancel_order.
- No withdraw.
- No transfer.
- No set_leverage.
- No live reconcile.
- No live execution.
- No secrets or sensitive account data appear in docs.
- Authority model is unchanged.
- Pipeline order is unchanged.
- Future implementation questions are marked NEEDS_OWNER_INPUT before implementation, not blockers for this docs-only PR.

## 14. Future Implementation Slices

- B1-DOC: maintain this architecture plan and status docs.
- B1-CONFIG: define testnet/demo-only configuration contract after separate approval.
- B1-CLIENT-SKELETON: create read-only client shell and typed errors after separate approval.
- B1-BALANCE-READ: implement mocked read-only wallet balance call after separate approval.
- B1-POSITIONS-READ: implement mocked read-only open positions call after separate approval.
- B1-ORDER-STATUS-READ-OPTIONAL: implement mocked read-only order status only if included in first implementation slice.
- B1-QA-HARDENING: complete mocked tests, redaction tests, guard tests, and regression gate after separate approval.

Each implementation slice requires the protocol from OI-9: architect -> plan -> implement -> QA -> external review if needed -> PR -> merge.

## 15. Risks and Future Implementation Questions

These are NEEDS_OWNER_INPUT before implementation. They are not blockers for this docs-only architecture PR.

- NEEDS_OWNER_INPUT: account type: Unified or Classic.
- NEEDS_OWNER_INPUT: position mode: One-way or Hedge.
- NEEDS_OWNER_INPUT: leverage policy: manual pre-config or API-managed.
- NEEDS_OWNER_INPUT: exact testnet/demo environment name.
- NEEDS_OWNER_INPUT: final allowed endpoint list.
- NEEDS_OWNER_INPUT: whether optional order-status read is included in first implementation slice.

Known risks:

- Accidentally using production endpoints instead of testnet/demo.
- Logging raw private payloads or sensitive account fields.
- Scope creep from read-only queries into commands.
- Mistaking exchange state for internal authority.
- Introducing service startup wiring before the client is reviewed.
- Treating optional order-status read as order lifecycle support.

## 16. Files Future Codex May Touch

Only after separate implementation approval, future Codex may touch:

- `libs/exchange/bybit_read_only.py`
- `libs/exchange/bybit_auth.py`
- `libs/exchange/bybit_models.py`
- `libs/exchange/errors.py`
- `tests/libs/exchange/test_bybit_read_only.py`
- `tests/libs/exchange/test_bybit_auth.py`
- Stage 53-B1 docs listed in the approved implementation task

Any additional file requires explicit scope approval.

## 17. Files Future Codex Must Not Touch

Future Stage 53-B1 work must not touch:

- `apps/execution_service/**`
- `apps/position_manager/**`
- `apps/orchestrator/**`
- `apps/risk_engine/**`
- `apps/review_gateway/**`
- `apps/kill_switch/**`
- `apps/dashboard_service/**`
- `config/**`
- `infra/**`
- `alembic/**`
- `scripts/**`
- `.env`
- `.env.*`
- `pyproject.toml`
- `requirements*.txt`

Future Stage 53-B1 work must also not add files containing API keys, secrets, account UID, email, balances, signed payloads, or raw private exchange responses.
