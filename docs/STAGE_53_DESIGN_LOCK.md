# Stage 53-0 Design Lock

System: Hephaestus trading system
Date: 2026-04-25
Status: DRAFT — Sasha review applied 2026-04-25; pending owner input on marked items

## Purpose

This document locks all architectural decisions required before any Stage 53
implementation begins. Each decision is marked either:

- **LOCKED** — decided, rationale included, no further input required
- **OWNER-INPUT-NEEDED** — decision cannot be made without owner runtime/account
  information; implementation of affected stages is blocked until resolved

No production code is changed by this document.

---

## Context

Live Path Existence Audit (2026-04-25) confirmed:

- Paper pipeline is complete and validated (Stage 52B.41)
- Live exchange layer does not exist — 0 exchange API calls in any money-path service
- Switching `EXECUTION_MODE=live` crashes at startup (`RuntimeError` in
  `execution_service/main.py:41-42`) before any order could be attempted
- Exchange decision: moving from OKX to Bybit
- Revised live blocker count: 14 (7 critical, 5 high, 2 medium)
- `account_state.equity_usdt` is a CLI argument (default 1000.0) — position sizing
  uses unverified caller-supplied equity in paper mode (`paper_pipeline_runner.py:77`)

---

## Authority Rules (Invariants — Must Not Change)

These rules govern all Stage 53 design decisions. Any implementation that would
violate them requires a separate explicit architectural decision before proceeding.

| Rule | Authority | Notes |
|---|---|---|
| Kill-switch is top authority | `system_state` / `kill_switch` service | Fail-closed for all 4 error classes; checked before every execution boundary |
| Risk engine is source of truth for admissibility | `risk_engine` | No downstream service may recompute or override a risk decision |
| `execution_service` owns execution outcome | `executions` table | Only execution_service writes execution status; no other service may |
| `position_manager` owns position state | `positions` table | Only position_manager writes position state; no other service may |
| Journal is audit, not authority | `journal_events` | Journal failure must not roll back authoritative DB state |
| Confidence is not authoritative | Signal engine | Signal confidence cannot block or approve a trade on its own |
| Manual approval only | orchestrator `/v1/pipeline/approve` | No auto-approve path; operator must be in the loop for every live trade |
| One trade at a time (first controlled live) | config `max_open_positions: 1` | Enforced by DB cap gate at execution admission |
| No withdrawal permissions | Exchange account | Exchange API keys must not have withdrawal permission |
| Pipeline order must not change | signal → risk → review → orchestrator → execution_service → position_manager | Adding live exchange calls must not alter this order |

---

## Decision 1 — First Live Market Type

**Status: LOCKED**

**Decision: Bybit linear perpetual (USDT-margined, `category=linear`)**

Rationale:
- System already implements `TradeDirection.LONG` and `TradeDirection.SHORT` for
  both directions — natural fit for perpetual futures
- PnL formula `(close_price - entry_price) * quantity` is correct for USDT-linear
  contracts; it would require a different formula for inverse (coin-margined) contracts
- Stop-loss and take-profit fields already exist with correct directional validation
- Spot requires margin borrowing for SHORT trades — incompatible with current position
  model which treats SHORT symmetrically with LONG
- No contract expiry to manage; no roll risk
- USDT-settled; all margin, PnL, and balance in the same currency as the risk model

All live API calls must include `category=linear` in every request to Bybit V5 API.

---

## Decision 2 — Bybit Account Assumptions

### 2a — Account Type

**Status: OWNER-INPUT-NEEDED**

Bybit has two account types:
- **Unified Trading Account (UTA)**: single wallet, shared margin across products,
  balance endpoint `GET /v5/account/wallet-balance?accountType=UNIFIED`
- **Classic account**: separate sub-wallets per product, balance endpoint uses
  `accountType=CONTRACT` for derivatives

Impact: the `get_balance()` method in `BybitExchangeClient` (Stage 53-B) must use
the correct `accountType` parameter. Using the wrong type returns an empty or
misleading balance, which propagates to risk sizing.

**Owner must confirm:** Is the live trading account a Unified Trading Account or a
Classic account?

### 2b — Position Mode

**Status: OWNER-INPUT-NEEDED**

Bybit supports two position modes for linear perpetuals:
- **One-way mode**: one position per symbol; open and close orders are net against
  the same position. All `place_order` calls use `positionIdx=0`.
- **Hedge mode**: long and short positions coexist per symbol. Each order must
  specify `positionIdx=1` (long) or `positionIdx=2` (short).

Impact: if the account is in Hedge mode and the implementation uses `positionIdx=0`,
orders are rejected by the exchange. The system currently does not track
`positionIdx` anywhere in the execution schema.

**Recommendation**: One-way mode is simpler, safer for first controlled live, and
matches the system's one-direction-per-symbol assumption.

**Owner must confirm:** Is the live trading account in One-way mode or Hedge mode?
If Hedge mode, it must be switched to One-way before 53-C implementation begins.

### 2c — Leverage Setting

**Status: OWNER-INPUT-NEEDED**

`config/risk.yaml` contains `max_leverage` which is used in position sizing output
(`evaluate_risk.py:125`) but is **never sent to the exchange**. If the account
leverage on Bybit differs from this config value, the actual margin required will
differ from what the risk engine computed.

**Owner must confirm:**
- What leverage is currently set on the Bybit account for BTC/ETH linear perpetuals?
- Should Stage 53-B set leverage via API (`POST /v5/position/set-leverage`) at
  execution time, or is the account leverage pre-configured manually?

---

## Decision 3 — Canonical Symbol Format

**Status: LOCKED**

**Decision: Keep `BTC-USDT` as internal canonical format; translate to `BTCUSDT` at adapter boundary only**

Rule:
```
internal symbol: BTC-USDT   (hyphenated — used everywhere in DB, config, services)
exchange symbol: BTCUSDT    (no hyphen — used only inside BybitMarketDataFetcher
                             and BybitExchangeClient)
translation:     exchange_symbol = internal_symbol.replace("-", "")
```

Where translation lives:
- Inside `libs/exchange/bybit_public.py` for the Stage 53-A public adapter
- Inside the authenticated Bybit client boundary for Stage 53-B+ private calls
- Nowhere else in the codebase

Where translation must NOT occur:
- `config/strategy.yaml` — symbols stay `BTC-USDT`
- `executions` table — symbol stored as `BTC-USDT`
- `positions` table — symbol stored as `BTC-USDT`
- `trade_candidates` table — symbol stored as `BTC-USDT`
- Any service other than the two adapter files above

Rationale: zero churn to existing DB rows, queries, signal/risk/review/orchestrator
logic, and statistics. Single translation point is auditable and reversible.

---

## Decision 4 — Live Account Equity Source

**Status: LOCKED (with confirmation requirement — see below)**

**Decision: Exchange wallet balance via `GET /v5/account/wallet-balance`**

Current paper behavior: `equity_usdt` is a CLI argument (default `1000.0`) passed to
`paper_pipeline_runner.py`. The risk engine comment at `evaluate_risk.py:30` explicitly
states: "caller-supplied in MVP pass; migrate to trusted source before live."

Live requirement: equity must come from the exchange balance endpoint at the start of
each pipeline cycle, not from a static config value. Using a stale or hardcoded equity
value in live mode produces wrong position sizes, wrong max loss, and wrong daily loss
limit calculation.

Implementation location: `BybitExchangeClient.get_balance()` (Stage 53-B), called at
the start of each live pipeline cycle in the live runner (see Decision 14).

Balance field mapping:
- `equity_usdt` ← `walletBalance` (UTA) or `equity` (Classic) for USDT coin
- `available_balance` ← `availableToWithdraw` or `availableBalance`

**Confirmation required**: owner must confirm account type (Decision 2a) before the
correct field names can be finalized.

---

## Decision 5 — daily_pnl_usdt Source

**Status: LOCKED**

**Decision: DB closed positions — sum of PnL from `positions` table for current calendar day**

Formula:
```
LONG PnL:  (close_price - entry_price) * quantity
SHORT PnL: (entry_price - close_price) * quantity
Filter:    positions.status = 'closed' AND positions.closed_at >= today 00:00 UTC
```

Rationale:
- `positions` table is the authoritative source for position state (authority rule)
- Exchange P&L endpoint is exchange-owned, not authoritative by the system's own rules
- DB query is synchronous and does not require an extra exchange API call per cycle
- Consistent with `stats truth -> positions + executions` documented in AI_COMMANDS.md

Risk: if `close_price` is null (reconcile-close path can write null — known issue
from Stage 52B.41), the PnL computation returns 0 for that trade. This must be
resolved before live (close_price nullable is an existing tracked issue).

Implementation: `PositionRepository.get_daily_pnl_usdt(since_utc: datetime) -> float`
called in the live runner before constructing `AccountState`.

---

## Decision 6 — Instrument Rules Validation

**Status: LOCKED**

**Decision: Validate computed position size against exchange instrument rules before placing any order**

Required fields (from `GET /v5/market/instruments-info?category=linear&symbol=BTCUSDT`):
- `minOrderQty` — minimum order quantity; reject if `position_size < minOrderQty`
- `qtyStep` — quantity step; round `position_size` down to nearest multiple
- `tickSize` — minimum price increment; round `entry_price` to nearest tick
- `minNotionalValue` — minimum order value in USDT; reject if
  `entry_price * position_size < minNotionalValue`

Validation location: `execution_service` at execution admission, after kill-switch
check and before calling `BybitExchangeClient.place_order()`.

Instrument rules must be cached per symbol at startup (fetched once, not per order)
with a TTL of 1 hour. Using stale instrument rules is acceptable; using no instrument
rules is not.

If validation fails:
- Write `instrument_rule_rejected` journal event
- Return `error.code = INSTRUMENT_RULE_REJECTED` from execution_service
- Do not halt; this is a risk sizing issue, not a system failure

---

## Decision 7 — Exchange Adapter Interface

**Status: LOCKED**

### 7a — Public Market Data (Stage 53-A)

```python
# libs/exchange/bybit_public.py
# Must satisfy the existing MarketFetcher Protocol in reconcile_scheduler.py:19-21

class BybitMarketDataFetcher:
    """
    Public Bybit market data. No auth. Used for reconcile mark price only.
    Satisfies MarketFetcher Protocol — same output shape as OkxMarketDataFetcher.
    """
    BASE_URL = "https://api.bybit.com"
    CATEGORY = "linear"

    def fetch_candles(
        self,
        symbol: str,        # internal format BTC-USDT; translated internally to BTCUSDT
        timeframe: str,     # internal format "1m"; translated to Bybit interval "1"
        *,
        limit: int = 100,
    ) -> list[dict]:
        # endpoint: GET /v5/market/kline
        # params: category=linear, symbol=BTCUSDT, interval=1, limit=100
        # response: retCode=0, result.list[0]=newest → sort ascending after parse
        # columns: [ts_ms, open, high, low, close, volume, turnover]
        # output keys: timestamp(datetime), open, high, low, close, volume, session="unknown"
        ...
```

Timeframe mapping (internal → Bybit interval):

| Internal | Bybit interval |
|---|---|
| `1m` | `1` |
| `5m` | `5` |
| `15m` | `15` |
| `30m` | `30` |
| `1h` | `60` |
| `4h` | `240` |
| `1d` | `D` |

### 7b — Authenticated Exchange Client (Stage 53-B)

```python
# libs/clients/bybit_exchange_client.py
# All methods are async. Auth via HMAC-SHA256.

@dataclass
class PlaceOrderResult:
    client_order_id: str      # echo of orderLinkId sent
    exchange_order_id: str    # Bybit orderId
    status: str               # mapped internal status (see Decision 9)
    submitted_at: datetime

@dataclass
class OrderStatusResult:
    client_order_id: str
    exchange_order_id: str
    status: str               # mapped internal status
    filled_qty: float         # cumExecQty
    avg_fill_price: float | None  # avgPrice; None if not yet filled
    updated_at: datetime

@dataclass
class CancelOrderResult:
    client_order_id: str
    cancelled: bool
    exchange_order_id: str | None

@dataclass
class ExchangePosition:
    symbol: str               # Bybit format BTCUSDT — translated to BTC-USDT before use
    side: str                 # "Buy" or "Sell"
    size: float               # positionAmt / size
    entry_price: float        # avgPrice
    mark_price: float         # markPrice
    unrealised_pnl: float

@dataclass
class InstrumentRules:
    symbol: str               # internal format BTC-USDT
    min_order_qty: float
    qty_step: float
    tick_size: float
    min_notional_value: float

@dataclass
class BalanceResult:
    equity_usdt: float        # total wallet equity
    available_balance: float  # available for new orders
    used_margin: float

class BybitExchangeClient:
    async def place_order(
        self,
        *,
        symbol: str,           # internal BTC-USDT → translated to BTCUSDT internally
        side: str,             # "Buy" or "Sell" (Bybit capitalised form)
        order_type: str,       # "Limit" or "Market"
        qty: float,            # after instrument rule rounding
        price: float | None,   # None for market orders; tick-rounded for limit
        client_order_id: str,  # = execution_id (see Decision 8)
        time_in_force: str = "GTC",
    ) -> PlaceOrderResult: ...

    async def cancel_order(
        self,
        *,
        symbol: str,
        client_order_id: str,
    ) -> CancelOrderResult: ...

    async def get_order_status(
        self,
        *,
        symbol: str,
        client_order_id: str,
    ) -> OrderStatusResult: ...

    async def get_open_positions(self) -> list[ExchangePosition]: ...

    async def get_balance(self) -> BalanceResult: ...

    async def get_instrument_rules(
        self, symbol: str
    ) -> InstrumentRules: ...
```

Auth headers for every private request:
```
X-BAPI-API-KEY:      <api_key>
X-BAPI-TIMESTAMP:    <timestamp_ms>
X-BAPI-SIGN:         HMAC-SHA256(timestamp + api_key + recv_window + body)
X-BAPI-RECV-WINDOW:  5000
```

Stage 53-B Bybit API key env vars: `BYBIT_API_KEY`, `BYBIT_API_SECRET`.
No passphrase required for Bybit. Do not document compatibility aliases unless
code support is verified elsewhere.

---

## Decision 8 — client_order_id / orderLinkId Rule

**Status: LOCKED**

**Decision: `client_order_id = execution_id` (verbatim)**

`execution_id` format: `exe_<32 hex chars>` = 36 characters total.
Bybit `orderLinkId` maximum length: 36 characters. Exact fit.

Rule:
```
orderLinkId (sent to Bybit) = execution_id (stored in executions table)
```

Why this is safe:
- `execution_id` is generated once at DB write time before any exchange call
- If a timeout occurs and the order is re-submitted, the same `execution_id` is used
  as `orderLinkId` — Bybit deduplicates and returns the existing order
- A new `execution_id` must never be generated for a retry of the same trade
- Recovery path: if `get_order_status(client_order_id=execution_id)` returns `Filled`,
  call `recover_position` (already implemented) to open the position from the
  existing filled execution

Schema change deferred beyond Stage 53-B:
- `0009_execution_exchange_fields` is not part of Stage 53-B implementation scope.
- Stage 53-B remains authenticated client foundation only.
- The following execution schema fields are deferred to Stage 53-C+ or a separately
  approved schema-prep stage:
- Add `exchange_order_id` column to `executions` table (Bybit's `orderId`)
- Add `exchange_avg_fill_price` column (Bybit's `avgPrice`)
- Add `exchange_filled_qty` column (Bybit's `cumExecQty`)
- Deferred migration: `0009_execution_exchange_fields`

---

## Decision 9 — Order Status Mapping

**Status: LOCKED**

| Bybit status | Internal status | Action |
|---|---|---|
| `New` | `submitted` | Continue polling |
| `PartiallyFilled` | `partially_filled` | Trigger partial fill policy (Decision 10) |
| `Untriggered` | `submitted` | Continue polling |
| `Triggered` | `submitted` | Continue polling |
| `Active` | `submitted` | Continue polling (open limit order) |
| `Filled` | `filled` | Proceed to open_position |
| `Cancelled` | `cancelled` | Write journal; do not open position |
| `Rejected` | `failed` | Write journal; trigger halt |
| `Deactivated` | `cancelled` | Write journal; do not open position |

Terminal statuses (polling stops): `Filled`, `Cancelled`, `Rejected`, `Deactivated`.
Non-terminal statuses (polling continues): `New`, `PartiallyFilled`, `Untriggered`,
`Triggered`, `Active`.

Poll interval: 2 seconds.
Poll timeout: 60 seconds total.
On poll timeout: write `execution_placement_timeout`, trigger kill-switch halt.

---

## Decision 10 — Partial Fill Policy

**Status: LOCKED**

**Decision: HALT on any partial fill for first controlled live — manual review required**

Rationale:
- Partial fill means the position was entered with less quantity than the risk
  parameters assumed; stop-loss distance in absolute price terms is unchanged but
  the risk/reward ratio has shifted
- The reconcile scheduler and close_position_use_case use the stored `quantity`
  field — a partial fill would require updating this to `filled_qty` before those
  paths work correctly
- Implementing correct partial fill handling is Stage 53-G (deferred)
- For first controlled live with operator present, halt is the safest policy

Implementation:
1. `get_order_status` returns `partially_filled`
2. `execution_service` writes `execution_status = partially_filled`
3. Triggers kill-switch halt
4. Writes journal event `partial_fill_halt`
5. Operator resolves: wait for full fill, or cancel remainder manually on exchange
6. Resume trading only after operator confirms full fill or full cancellation

This policy must not be changed without an explicit owner decision.

---

## Decision 11 — Stop-Loss Policy for First Controlled Live

**Status: LOCKED**

**Decision: Application-managed stop-loss (reconcile scheduler detects SL hit, sends close order)**

Rationale:
- Matches existing reconcile architecture — `evaluate_exit_rules` in
  `apps/position_manager/domain/rules.py` already checks stop-loss trigger
- Exchange-native conditional/stop orders require a new order type in the execution
  path, a separate cancel path, and handling for order expiry on exchange restart
- For a single controlled trade with operator monitoring, scheduler-managed stop is
  acceptable
- Exchange-native stops are Stage 53-G (deferred)

Constraint: reconcile scheduler interval must be ≤ 30 seconds for live mode.
Current config default (`POSITION_RECONCILE_INTERVAL_SECONDS`) is 30 seconds.
The paper-only guard at `position_manager/main.py:45` must be replaced with a
live-safe guard in Stage 53-D.

Operator responsibility: monitor the position manually for rapid adverse moves during
the first controlled live; halt manually if price approaches stop-loss before the
scheduler fires.

---

## Decision 12 — Close-Position Responsibility

**Status: LOCKED**

**Decision: `execution_service` sends all exchange orders (open AND close); `position_manager` updates state only after fill confirmation**

Boundary rule:
```
position_manager   → triggers close intent (calls execution_service close endpoint)
execution_service  → sends exchange close order, polls for fill
execution_service  → reports fill result back to position_manager
position_manager   → updates position.status = 'closed' after fill confirmed
```

Why:
- `execution_service` is the single exchange interaction boundary — splitting exchange
  calls across two services creates dual API consumers, rate limit conflicts, and
  authority confusion
- Authority rule: `execution_service` owns execution outcome; position_manager owns
  position state; these remain cleanly separated under this design

New endpoint required (Stage 53-C): `POST /v1/execution/close`
- Request: `{ execution_id, symbol, side, qty, correlation_id }`
- Response: fill result or error with exact exchange status

`close_position_use_case` must be split:
- DB state update stays in `position_manager` (called after fill confirmed)
- Exchange close order is new code in `execution_service`

---

## Decision 13 — execution_started Journal Event

**Status: LOCKED**

**Decision: Emit `execution_started` immediately before calling `BybitExchangeClient.place_order()`**

Location: `execution_service/application/place_order.py`, after kill-switch check
passes and before the exchange API call.

Event structure:
```python
{
    "event_id": f"evt_execution_started_{execution_id}",
    "event_type": "execution_started",
    "severity": "info",
    "correlation_id": correlation_id,
    "payload": {
        "execution_id": execution_id,
        "candidate_id": candidate_id,
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "entry_price": entry_price,
        "quantity": quantity,
        "client_order_id": execution_id,
    }
}
```

This event closes the journal gap identified in the Live Path Audit:
`candidate_approved` → [gap] → `execution_filled`
becomes:
`candidate_approved` → `execution_started` → `execution_filled` / `execution_failed`

The event must be written to DB before the exchange call — if the exchange call
succeeds but the journal write fails, the failure must be logged (fail-soft after
the authoritative exchange submission), not rolled back.

---

## Decision 14 — Live Runner

**Status: LOCKED**

**Decision: Separate `ops/controlled_live_runner.py` — do not modify `paper_pipeline_runner.py`**

Rationale:
- `paper_pipeline_runner.py` has paper-specific assumptions that must not be changed:
  - `bid=last_price, ask=last_price` (fake spread — acceptable for paper, wrong for live)
  - `equity_usdt` from CLI argument (acceptable for paper, wrong for live)
  - `OkxMarketDataFetcher()` hardcoded at line 271
  - `daily_pnl_usdt` from CLI argument
- Modifying the paper runner risks breaking the validated paper pipeline
- A separate live runner makes the paper/live divergence explicit and auditable

`ops/controlled_live_runner.py` must:
1. Load equity from `BybitExchangeClient.get_balance()` at start of each cycle
2. Load `daily_pnl_usdt` from DB (`PositionRepository.get_daily_pnl_usdt()`)
3. Use `BybitMarketDataFetcher()` (Stage 53-A)
4. Use real bid/ask from exchange ticker (not last_price — requires 53-B)
5. Check kill-switch at top of each cycle (same as paper runner)
6. Support `--once` flag for single-cycle controlled live probe
7. Never auto-approve — candidates are created and wait for operator action

Until Stage 53-B (ticker endpoint), the live runner is blocked. Stage 53-A
(market data fetcher only) can be completed independently.

---

## Decision 15 — Timeout and Fail-Closed Policy

**Status: LOCKED**

**Decision: FAIL-CLOSED on any unresolved exchange timeout — halt, do not auto-retry**

On `place_order` timeout (> 60 seconds without terminal status):
1. Write `execution_status = placement_timeout` to `executions` table
2. Trigger kill-switch halt
3. Write journal event `execution_placement_timeout`
4. Return error to orchestrator
5. Operator must query Bybit using `client_order_id = execution_id` to determine
   if the order landed on the exchange
6. If `Filled` on exchange: use existing `recover_position` path
7. If not found or `Rejected`: cancel and resume normally

On `cancel_order` timeout:
1. Write journal event `cancel_timeout_halt`
2. Trigger kill-switch halt
3. Operator must verify cancellation on exchange before resuming

On `get_balance` timeout:
1. Do not proceed with the pipeline cycle
2. Log and skip; do not halt (this is pre-trade, not mid-trade)

On `get_order_status` poll failure (network error, not timeout):
1. Retry once after 2 seconds
2. If second attempt fails: write `poll_failure_halt`, trigger halt

Rationale: duplicate live orders are worse than missed orders for first controlled live.

---

## Decision 16 — Drawdown Lock

**Status: LOCKED (deferred)**

`evaluate_risk.py:48` has `drawdown_lock = False` hardcoded with comment "requires
historical drawdown state; not available in MVP."

**Decision: Drawdown lock remains deferred for Stage 53. Daily loss limit (`max_daily_loss_pct` from config) is the only active loss gate.**

This is acceptable for first controlled live with max_open_positions = 1 and operator
manual monitoring. Drawdown lock implementation is Stage 55A.

---

## Stage 53-A Scope

**Bybit public market data adapter only.**
This is the smallest safe increment. No execution path changes. No schema migrations.

### Files to add

| File | Purpose |
|---|---|
| `libs/exchange/bybit_public.py` | Stage 53-A public adapter satisfying existing `MarketFetcher` Protocol |
| `tests/libs/clients/test_bybit_market_data_fetcher.py` | Unit tests (all HTTP mocked) |

### Files to change

| File | Change |
|---|---|
| `apps/position_manager/main.py` | Line 25: swap `OkxMarketDataFetcher` import to `BybitMarketDataFetcher`; line 52: swap instantiation |
| `config/exchange.yaml` | `venue: bybit` |

### Files that must NOT change in 53-A

- `apps/position_manager/application/reconcile_scheduler.py` — Protocol already correct
- `config/strategy.yaml` — internal symbols stay `BTC-USDT`
- All execution path files
- All schema/migration files
- All auth/security files
- `ops/paper_pipeline_runner.py`

### 53-A acceptance criteria

1. `python -m pytest tests/libs/clients/test_bybit_market_data_fetcher.py` — all pass
2. Full test suite: `python -m pytest -q --ignore=research` — no regression (≥ 211 passed)
3. Verify `config/exchange.yaml` shows `venue: bybit`:
   `Get-Content config/exchange.yaml`
4. Verify import swap in position_manager:
   `Select-String -Path apps/position_manager/main.py -Pattern 'BybitMarketDataFetcher'`

### 53-A does NOT close any critical live blocker

53-A replaces the market data fetcher for reconcile mark price only. It is a
pre-condition for 53-D (live reconcile scheduler). The 7 critical live blockers
remain open after 53-A.

---

## Stage 53-B Through 53-F Implications

### Stage 53-B — Authenticated Exchange Client

Pre-conditions: owner input resolved (Decisions 2a, 2b, 2c), 53-A complete.

New file: `libs/clients/bybit_exchange_client.py` (interface defined in Decision 7b).
No schema migration in Stage 53-B. `0009_execution_exchange_fields` is deferred
to Stage 53-C+ or a separately approved schema-prep stage.

Closes live blockers: B-3 (no authenticated client), partial B-12 (position fetch).

### Stage 53-C — Live Execution Path

Pre-conditions: 53-B complete, owner inputs confirmed.

Changes:
- Remove `ValueError` guard in `place_order.py:51-52`
- Remove `RuntimeError` guard in `execution_service/main.py:41-42` for `live` mode
- Add live branch in `place_order_use_case`: call `BybitExchangeClient.place_order()`,
  poll for fill via `get_order_status()`, map status via Decision 9
- Add `POST /v1/execution/close` endpoint
- Emit `execution_started` journal event (Decision 13)
- Add instrument rule validation (Decision 6)
- Add partial fill halt (Decision 10)
- Add timeout/fail-closed policy (Decision 15)

Closes live blockers: B-1, B-2, B-4, B-5, B-6, B-7, B-8 (partial).

### Stage 53-D — Live Reconcile Scheduler

Pre-conditions: 53-B complete (needs `get_open_positions()`).

Changes:
- Replace paper-only guard in `position_manager/main.py:45` with mode-appropriate
  start condition
- For live mode: build reconcile snapshots from `BybitExchangeClient.get_open_positions()`
  instead of fabricated DB snapshots
- Reconcile interval ≤ 30 seconds for live

Closes live blockers: B-6 (reconcile scheduler), B-11 (real exchange position fetch).

### Stage 53-E — Tests and Exchange Smoke Tests

Pre-conditions: 53-C, 53-D complete.

Required tests:
- Mocked `BybitExchangeClient` — all order lifecycle paths (submit, poll, fill, cancel)
- Partial fill halt test
- Placement timeout halt test
- Instrument rule rejection test
- Live reconcile with mocked `get_open_positions()`
- Kill-switch before live `place_order` test

Exchange smoke test (non-production, testnet or minimal real account):
- Place 1 real minimum-size order → confirm `exchange_order_id` stored → cancel

### Stage 53-F — Controlled Live Probe

Pre-conditions: all of 53-A through 53-E complete, all owner inputs resolved, VPS
runtime proof complete.

Scope:
- 1 symbol only (BTC-USDT)
- 1 trade maximum (`max_open_positions: 1` enforced)
- Manual approval required for every trade
- Operator monitors every 15 minutes (Day-1 Monitoring Checklist in OPERATOR_RUNBOOK.md)
- Kill-switch tested manually before probe begins (halt → verify → resume)

Not in scope for first controlled live:
- Multiple symbols
- Auto-approve
- Exchange-native stop orders
- Partial fill recovery
- Drawdown lock

---

## Owner-Input-Needed Summary

Items that block Stage 53-B or later until resolved:

| # | Decision | What is needed | Blocking |
|---|---|---|---|
| OI-1 | Decision 2a | Confirm Bybit account type: Unified or Classic | 53-B balance endpoint |
| OI-2 | Decision 2b | Confirm position mode: One-way or Hedge | 53-B/C order parameters |
| OI-3 | Decision 2c | Confirm leverage setting; decide set-via-API vs manual pre-config | 53-C |
| OI-4 | Decision 14 | Confirm real bid/ask source for live runner (ticker endpoint) | 53-F |
| OI-5 | General | Bybit API key with: Futures read+write, NO withdrawal permission | 53-B integration test |
| OI-6 | General | Confirm VPS runtime proof (required before 53-F, per PROGRESS.md gate) | 53-F |

Items 53-A does not require any owner input. 53-A can begin immediately.

---

## Revised Live Blockers (14 total)

From Live Path Existence Audit 2026-04-25, with stage mapping:

| # | Blocker | Severity | Closes in |
|---|---|---|---|
| B-1 | `place_order.py` hard-rejects non-paper mode | CRITICAL | 53-C |
| B-2 | Startup `RuntimeError` for `EXECUTION_MODE=live` | CRITICAL | 53-C |
| B-3 | No authenticated exchange client | CRITICAL | 53-B |
| B-4 | No order status polling loop; instant DB fill | CRITICAL | 53-C |
| B-5 | Close position sends no exchange order | CRITICAL | 53-C |
| B-6 | Reconcile scheduler has paper-only guard | CRITICAL | 53-D |
| B-7 | Equity is CLI argument (default 1000.0), not from exchange | CRITICAL | 53-B |
| B-8 | No instrument rule validation | HIGH | 53-C |
| B-9 | No `client_order_id`/`exchange_order_id` in schema | HIGH | 53-C+ or approved schema-prep |
| B-10 | `close_price` nullable on reconcile close | HIGH | 53-C |
| B-11 | No real exchange position fetch for reconcile | HIGH | 53-D |
| B-12 | `bid=ask=last_price` in paper runner; spread always 0 | MEDIUM | 53-F runner |
| B-13 | `drawdown_lock` hardcoded False | MEDIUM | deferred (55A) |
| B-14 | `execution_started` journal event not emitted | MEDIUM | 53-C |

53-A closes: none of the above (it is a pre-condition for 53-D, not a blocker itself).

---

## What Must Not Change (Stage 53 Constraints)

Any implementation work in Stage 53 must not alter the following:

1. **Pipeline order**: `signal → risk → review → orchestrator → execution_service → position_manager`
2. **Kill-switch fail-closed**: all 4 error classes (`AUTH_FAILURE`, `KILL_SWITCH_TIMEOUT`, `KILL_SWITCH_UNAVAILABLE`, `KILL_SWITCH_ERROR`) must continue to block execution
3. **`RiskDecision.entry_price` midpoint rule**: `(entry_zone.min + entry_zone.max) / 2`
4. **`execution_idempotency_key` deduplication**: DB-level idempotency must remain for the paper path; live adds exchange-level idempotency on top
5. **Journal fail-soft after authoritative DB commit**: journal write failure must not roll back a committed position or execution
6. **operator_actions audit trail**: every approve/reject must continue to write to `operator_actions` table atomically
7. **`max_open_positions` DB cap gate with advisory lock**: must remain at execution admission boundary
8. **Token validation at startup**: `validate_startup_auth()` must not be weakened

---

## Safety-vs-Signal-Quality Staged Roadmap

**Owner decision (2026-04-25):** First controlled live is a technical money-path proof, not a performance optimisation attempt. Do not add strategy quality filters to Stage 53.

### Guiding principle

> Minimum filters for safety. Maximum observability. One honest trade with full logs is better than zero trades behind perfect filters.

The goal of Stage 53 is to verify that the execution path works end-to-end with real exchange interaction: order placed, filled, position opened, position closed, all events journaled, kill-switch enforced throughout. Signal quality, pair ranking, and regime detection are separate concerns that require trading data to calibrate. Adding them before the first trade produces uncalibrated filters that silently suppress trades and make it impossible to distinguish "filter rejected it" from "no valid signal."

### Stage 53 — Exchange Sanity Layer (live blockers)

These layers are required before any live execution attempt. All are live blockers.

| Layer | Purpose | Blocker |
|---|---|---|
| Exchange Sanity (EXECUTION_MODE guard removal) | Confirm execution path reaches exchange without crashing | B-1, B-2 |
| Instrument Rules validation | Reject orders that violate exchange minimums (minOrderQty, qtyStep, tickSize, minNotional) | B-8 |
| Liquidity / Spread Guard | Reject entry if bid-ask spread exceeds threshold at order time | B-12 |
| Position Exposure Guard | `max_open_positions` DB cap gate + account equity check before order | B-7 |
| Bybit public market data | `BybitMarketDataFetcher` for reconcile mark price | B-11 pre-condition |
| Authenticated Bybit client | `BybitExchangeClient` — place, cancel, poll, balance, positions | B-3 |
| Live execution path | `place_order_live_use_case` + `close` endpoint + partial fill halt | B-1..B-6, B-10, B-14 |
| Live reconcile scheduler | Real exchange positions from `get_open_positions()`, not fabricated snapshots | B-6, B-11 |

All Stage 53 layers are implemented as hard guards (fail-closed) that protect capital. They are not optional.

### Stage 54 — Signal Quality Layer (important, not live blockers)

These layers improve signal selection quality. They require real trading data to calibrate thresholds. None block the first controlled live.

| Layer | Purpose | Dependency |
|---|---|---|
| Pair Selection / Market Universe Selector | Filter symbol universe by volume, spread, volatility before signal generation | Trading data for threshold calibration |
| Market Regime Detector | Advisory regime context (trending / ranging / volatile) passed to review | Historical trade data |
| Signal Quality Gate | Filter signals by score, confidence, or historical hit-rate per symbol | Hit-rate data from live + paper history |

Stage 54 layers are advisory filters — they narrow inputs before the pipeline starts for a given cycle. They do not override risk decisions, do not interact with `execution_service` or `position_manager`, and do not hold approval authority.

### Stage 55+ — Advanced Execution Quality (deferred)

These layers require accumulated volume, order book data, and validated live behaviour before they can be calibrated.

| Layer | Purpose |
|---|---|
| News / Media Risk Filter | Suppress entries during high-impact news windows |
| Trade Cooldown / Anti-overtrading | Rate-limit candidate creation per symbol per window |
| Advanced slippage / adaptive execution | Adjust order type or size based on real-time order book depth |

None of these are in scope until Stage 53-F (controlled live probe) is complete and LH-2 (paper accumulation) has produced enough history.

### Separation rule

Stage 53 safety layers and Stage 54+ signal-quality layers must not be mixed in the same implementation increment.

| Verdict | Meaning |
|---|---|
| Stage 53 item missing | **Live blocker** — do not proceed to 53-F until it is closed |
| Stage 54 item missing | **Not a live blocker** — improves performance; absence does not make live trading unsafe |
| Stage 55+ item missing | **Fully deferred** — no implementation until post-53-F |

If a review or design discussion proposes adding a Stage 54 or Stage 55+ filter to Stage 53 scope, reject it. Recategorise it to its correct stage and track it there.

---

## Final Verdict

**DESIGN_LOCK_NEEDS_OWNER_INPUT**

Stage 53-A can begin immediately — no owner input is required for the Bybit public
market data adapter.

Stages 53-B through 53-F are blocked on owner inputs OI-1 through OI-3 (account
type, position mode, leverage setting). These are runtime/account facts that cannot
be determined from the codebase.

All architectural decisions that can be made from the codebase are LOCKED.
No decision has been left ambiguous where the codebase provides sufficient information.

Owner actions required before 53-B begins:
1. Confirm Bybit account type (Unified or Classic)
2. Confirm position mode is One-way (or switch it to One-way)
3. Confirm or set account leverage for linear perpetuals
4. Confirm Bybit API key has Futures read+write and NO withdrawal permission
