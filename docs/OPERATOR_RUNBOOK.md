# Operator Runbook

Status: ACTIVE / REFERENCE - runtime procedures unverified in the 2026-07-16 local audit.

System: trading-system
Mode: paper (live path defined below)
Last updated: 2026-04-25

## Service Port Map

| Service | Port | Auth required |
|---|---|---|
| kill_switch | 8001 | INTERNAL_SERVICE_TOKEN (status), ADMIN_TOKEN (halt/resume) |
| risk_engine | 8002 | INTERNAL_SERVICE_TOKEN |
| review_gateway | 8003 | INTERNAL_SERVICE_TOKEN |
| journal_ingest | 8004 | INTERNAL_SERVICE_TOKEN |
| orchestrator | 8005 | INTERNAL_SERVICE_TOKEN (evaluate), OPERATOR_TOKEN (approve/reject/pending) |
| execution_service | 8006 | INTERNAL_SERVICE_TOKEN |
| position_manager | 8007 | INTERNAL_SERVICE_TOKEN (open/close/reconcile), OPERATOR_TOKEN (list open) |
| dashboard_service | 8008 | (public read) |
| incidents | 8009 | INTERNAL_SERVICE_TOKEN |
| journal_review | 8010 | INTERNAL_SERVICE_TOKEN |

---

## Halt Conditions

Trigger an immediate kill-switch halt for any of the following. When in doubt, halt first, assess second.

### Exchange state
- Open position exists on exchange but is not in internal `positions` table
- Internal position is `open` but exchange shows it as closed, cancelled, or liquidated
- Order submitted to exchange but no fill confirmation received within 60 seconds
- Exchange rejects order with insufficient margin or balance error
- Exchange API returns unexpected 5xx or authentication failure on any money-path call
- Position size on exchange does not match `quantity` in `positions` table

### DB state
- Alembic migration head is not `0009_create_paper_account_authority` (schema mismatch)
- Orphan executions detected: execution status `filled` with no corresponding position row
- Candidate stuck in `approved` status for more than 5 minutes without execution_id attached
- Candidate stuck in `submitted` status for more than 2 minutes
- DB connection failure or timeout from any service
- `max_open_positions` cap exceeded (more open positions in DB than config allows)

### Journal gaps
- Execution `filled` event missing from `journal_events` for a completed execution
- `position_opened` event missing after `paper_execution_filled`
- `candidate_approved` event missing after operator approval action
- Any `kill_switch_check_failed` journal event appearing — indicates auth or connectivity failure on the kill-switch path
- Any `position_open_failed` journal event — indicates execution committed but position not opened

### Auth failures
- Any `401 Unauthorized` on a money-path endpoint (evaluate, approve, place, open, close)
- `kill_switch_check_failed` journal event with `error_code: AUTH_FAILURE`
- Service fails to start due to token validation failure (`validate_startup_auth` raises at lifespan)
- Token value is shorter than 32 characters or on the denylist

### Service crashes
- Any service `/health` endpoint returns non-200 or connection refused
- `execution_service` /ready returns `mode` != expected execution mode
- Any service process exits (PowerShell window closes unexpectedly)
- Orphan scheduler stops emitting log lines (indicates task crash without restart)
- Reconcile scheduler stops emitting log lines in paper mode

### Market conditions (live only)
- Sustained price movement > 15% in under 5 minutes on any active symbol
- Exchange websocket feed drops or lags > 30 seconds
- Spread on active symbol exceeds 3x normal
- Any forced liquidation notification from exchange

---

## Day-1 Monitoring Checklist

Run every 15 minutes during the first 24 hours of controlled live. Use the exact commands below.

### 0. Set token variables once per session

```powershell
$internal = $env:INTERNAL_SERVICE_TOKEN
$operator = $env:OPERATOR_TOKEN
$admin    = $env:ADMIN_TOKEN
```

### 1. All 9 services healthy

```powershell
@(8001,8002,8003,8004,8005,8006,8007,8008,8009) | ForEach-Object {
    try {
        $r = Invoke-RestMethod "http://127.0.0.1:$_/health"
        Write-Host "[$_] $($r.status)" -ForegroundColor Green
    } catch {
        Write-Host "[$_] UNREACHABLE" -ForegroundColor Red
    }
}
```

Expected: all return `healthy`. Any `UNREACHABLE` = halt immediately.

### 2. Kill-switch state

```powershell
Invoke-RestMethod http://127.0.0.1:8001/v1/kill-switch/status `
    -Headers @{ Authorization = "Bearer $internal"; "X-Correlation-Id" = "ops-check" }
```

Expected: `trading_enabled: true`, `kill_switch_active: false`.

### 3. Execution mode

```powershell
Invoke-RestMethod http://127.0.0.1:8006/ready
```

Expected: `mode: paper` (or `live` when intentionally switched). Never `dry_run` in production.

### 4. Open positions

```powershell
Invoke-RestMethod http://127.0.0.1:8007/v1/positions/open `
    -Headers @{ Authorization = "Bearer $operator" }
```

Check:
- Count matches expectation
- No position `opened_at` older than TTL config without triggering a close
- `stop_loss` and `take_profit` present on every live position
- No position with `close_price: null` that is already closed

### 5. Orphan executions

```powershell
Invoke-RestMethod "http://127.0.0.1:8006/v1/execution/orphans?emit_events=false" `
    -Headers @{ Authorization = "Bearer $internal" }
```

Expected: `data.orphan_count: 0`. Any orphan = halt, then investigate.

### 6. Pending candidates

```powershell
Invoke-RestMethod http://127.0.0.1:8005/v1/pipeline/pending `
    -Headers @{ Authorization = "Bearer $operator" }
```

Check: no candidate stuck in `approved` for more than 5 minutes.

### 7. Dashboard stats

```powershell
Invoke-RestMethod http://127.0.0.1:8008/v1/stats
```

Spot-check: `total_trades`, `win_rate`, `pnl` move in expected direction. If `total_trades` is 0 after confirmed fills, investigate stats source.

### 8. Journal recent events (requires direct DB access or dashboard)

Verify latest journal events for expected event types in order:
`candidate_created` → `risk_decision` → `review_result` → `candidate_approved` → `paper_execution_filled` → `position_opened`

Any gap in this chain for a completed trade = halt and investigate.

### 9. Exchange position cross-check (live only)

Compare open positions from step 4 against exchange account:
- Position count matches
- Symbol and side match for each position
- Quantity within 1% of internal value (rounding tolerance)
- Any discrepancy = halt immediately

---

## Incident Response

### Phase 1: Detect

Signs that an incident is in progress:
- Service health check fails (step 1 above returns UNREACHABLE)
- Orphan execution detected (step 5 returns count > 0)
- Journal event gap observed
- Exchange position mismatch
- Any `kill_switch_check_failed`, `position_open_failed`, or `execution_failed_after_approval` in journal
- Operator receives alert from `alert_client`

### Phase 2: Halt

**Always halt first. Do not attempt recovery on a running system.**

```powershell
$body = @{
    operator_user_id = 1
    reason           = "incident response — <describe reason>"
    actor            = "operator"
    correlation_id   = "inc_$(Get-Date -Format 'yyyyMMddHHmmss')"
} | ConvertTo-Json

Invoke-RestMethod http://127.0.0.1:8001/v1/kill-switch/halt `
    -Method POST `
    -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $admin" } `
    -Body $body
```

Verify halt was accepted:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/v1/kill-switch/status `
    -Headers @{ Authorization = "Bearer $internal"; "X-Correlation-Id" = "ops-verify-halt" }
```

Expected: `kill_switch_active: true`, `trading_enabled: false`.

### Phase 3: Assess

Run all checks from the Day-1 Monitoring Checklist. Then perform these targeted queries.

**Check for orphan executions:**
```powershell
Invoke-RestMethod "http://127.0.0.1:8006/v1/execution/orphans?emit_events=true" `
    -Headers @{ Authorization = "Bearer $internal" }
```

**Check all open positions:**
```powershell
Invoke-RestMethod http://127.0.0.1:8007/v1/positions/open `
    -Headers @{ Authorization = "Bearer $operator" }
```

**Check pending candidates:**
```powershell
Invoke-RestMethod http://127.0.0.1:8005/v1/pipeline/pending `
    -Headers @{ Authorization = "Bearer $operator" }
```

**Check service logs** (each service runs in its own PowerShell window — scroll up for stack traces).

**Check Alembic head:**
```powershell
cd E:\trading-system
python -m alembic current
```

Expected: `0009_create_paper_account_authority (head)`. Any other value = schema mismatch, do not resume until fixed.

### Phase 4: Recover

Choose the recovery action based on the assessment finding.

**A: Orphan execution (filled, no position)**
```powershell
# Trigger position recovery by execution_id
$body = @{
    execution_id   = "<execution_id_from_orphan_check>"
    correlation_id = "recover_$(Get-Date -Format 'yyyyMMddHHmmss')"
} | ConvertTo-Json

Invoke-RestMethod http://127.0.0.1:8007/v1/positions/recover `
    -Method POST `
    -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $internal" } `
    -Body $body
```

**B: Position open on exchange but not in DB**
- Do NOT use reconcile to auto-close — this would close a real exchange position without a close order.
- Manually reconcile by posting a `ReconcileRequest` with the correct `ExchangePositionSnapshot`.
- Or: manually close the position on the exchange first, then run reconcile.

**C: Service crash (process exited)**
```powershell
cd E:\trading-system
# Reload .env then restart the specific service
. .\start-local-runtime.ps1   # restarts all 9
# Or restart individual service:
python -m uvicorn apps.<service>.main:app --host 127.0.0.1 --port <port>
```

**D: DB connection failure**
```powershell
# Verify Docker is running
docker ps
# Verify postgres is up
docker compose ps
# If container is stopped:
docker compose up -d postgres redis
# Then restart all services
. .\start-local-runtime.ps1
```

**E: Alembic head mismatch**
```powershell
cd E:\trading-system
python -m alembic upgrade head
python -m alembic current
```

Do not resume trading until `alembic current` confirms `(head)`.

**F: Auth token failure**
- Verify `.env` tokens are ≥ 32 characters and not on the denylist.
- Restart affected service after correcting `.env`.
- Do not commit real token values to git.

**G: Candidate stuck in approved**
```powershell
# Reject the stuck candidate to unblock the pipeline
$body = @{
    candidate_id   = "<candidate_id>"
    telegram_user_id = 1
    correlation_id = "reject_stuck_$(Get-Date -Format 'yyyyMMddHHmmss')"
} | ConvertTo-Json

Invoke-RestMethod http://127.0.0.1:8005/v1/pipeline/reject `
    -Method POST `
    -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $operator" } `
    -Body $body
```

### Phase 5: Resume

Only resume after:
- Root cause identified and documented
- All orphan executions resolved
- All service `/health` endpoints return 200
- Kill-switch status shows `trading_enabled: false` (still halted — resume will flip this)
- Alembic at correct head
- No pending candidates in ambiguous state

```powershell
$body = @{
    operator_user_id = 1
    actor            = "operator"
    correlation_id   = "resume_$(Get-Date -Format 'yyyyMMddHHmmss')"
} | ConvertTo-Json

Invoke-RestMethod http://127.0.0.1:8001/v1/kill-switch/resume `
    -Method POST `
    -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $admin" } `
    -Body $body
```

Verify resume was accepted:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/v1/kill-switch/status `
    -Headers @{ Authorization = "Bearer $internal"; "X-Correlation-Id" = "ops-verify-resume" }
```

Expected: `trading_enabled: true`, `kill_switch_active: false`.

Run the full Day-1 Monitoring Checklist before declaring incident resolved.

---

## Quick Reference

```
HALT:   POST 8001/v1/kill-switch/halt    Authorization: Bearer $admin
RESUME: POST 8001/v1/kill-switch/resume  Authorization: Bearer $admin
STATUS: GET  8001/v1/kill-switch/status  Authorization: Bearer $internal
OPEN:   GET  8007/v1/positions/open      Authorization: Bearer $operator
ORPHAN: GET  8006/v1/execution/orphans   Authorization: Bearer $internal
PENDING:GET  8005/v1/pipeline/pending    Authorization: Bearer $operator
```
