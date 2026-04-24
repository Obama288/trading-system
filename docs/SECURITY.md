# Security Runbook

## S-6: Network Boundary

### Principle

All inter-service communication must occur over a private network only.
No internal service port should be reachable from the public internet.
TLS is required for any endpoint that accepts connections from outside the private network.

### Service Communication Map

```
Signal Engine
    └─► Risk Engine
            └─► Review Gateway
                    └─► Orchestrator ──────────► Kill Switch
                                └─► Execution Service ─► Kill Switch
                                            └─► Position Manager ─► Journal Ingest
                                                                 └─► Alerts Service
Incidents ──────────────────────────────────────────────────────► Journal Ingest

Operator/Telegram ──► Orchestrator  (X-Operator-Token)
Admin              ──► Kill Switch  (X-Admin-Token)
Operator           ──► Dashboard / Journal Review / Position Manager / Incidents
```

All arrows inside the box use `X-Internal-Token`. No service in this map should be
reachable on a public IP.

### Deployment Checklist

- [ ] All services are attached to an isolated Docker/container network; no service
      exposes a port to `0.0.0.0` on the host except the single operator-facing gateway.
- [ ] `docker-compose.yml` (or equivalent): postgres and redis ports are bound to
      `127.0.0.1` only (`"127.0.0.1:5432:5432"`) — not `0.0.0.0`.
- [ ] Firewall/security-group audit: run `ss -tlnp` or `netstat -tlnp` on each host and
      confirm no internal service port (8000-range) is reachable externally.
- [ ] Any external-facing endpoint (operator bot webhook, admin UI) is behind a TLS
      terminating proxy (nginx/caddy/traefik) with a valid certificate.
- [ ] Health endpoints (`/health`, `/ready`) are not routed to the public internet.
- [ ] Inter-service calls use Docker DNS names (`http://kill-switch:8000`) and never
      use the host's public IP.

---

## S-7: Token Rotation Runbook

### Token Tiers

| Variable | Used by | Protects |
|---|---|---|
| `INTERNAL_SERVICE_TOKEN` | orchestrator, execution_service, kill_switch (status), position_manager, review_gateway, risk_engine, journal_ingest, incidents, alerts_service | Machine-to-machine calls on the money-path |
| `OPERATOR_TOKEN` | orchestrator, dashboard_service, position_manager, incidents, journal_ingest, journal_review | Human operator actions (approve, reject, view) |
| `ADMIN_TOKEN` | kill_switch | Halt / resume trading system |

Minimum token length: **32 characters**. Tokens on the denylist (`test`, `admin`,
`secret`, `changeme`, etc.) are rejected at startup by `validate_startup_auth`.

### Rotation Procedure

#### Step 1 — Generate a new token

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

Run once. Copy the output — this is the new token value.

#### Step 2 — Update the secret in all affected services

Update the environment variable (`.env` file, secrets manager, or Docker secret) for
every service listed in the tier row above. Do **not** restart any service yet.

For `INTERNAL_SERVICE_TOKEN` update all services simultaneously — a partial update
creates an auth-failure window (old caller → new callee = 403). Stage all env changes
before the restart step.

#### Step 3 — Rolling restart (leaf services first)

Restart services in this order to minimise the auth-failure window.
Services listed first have no outbound internal calls and will start accepting the new
token immediately.

**INTERNAL_SERVICE_TOKEN rotation order:**
1. `kill_switch`
2. `review_gateway`
3. `risk_engine`
4. `journal_ingest`
5. `alerts_service`
6. `position_manager`
7. `execution_service`
8. `incidents`
9. `orchestrator`

**OPERATOR_TOKEN rotation order:**
1. `dashboard_service`
2. `journal_review`
3. `journal_ingest`
4. `incidents`
5. `position_manager`
6. `orchestrator`

**ADMIN_TOKEN rotation order:**
1. `kill_switch` (only consumer)

If a simultaneous/blue-green restart is available, prefer that over rolling to eliminate
the auth-failure window entirely.

#### Step 4 — Verify health after restart

```bash
# For each restarted service:
curl -sf http://<service-host>:<port>/health
curl -sf http://<service-host>:<port>/ready   # execution_service only
```

All services must return `200`. A `500` at startup means the token failed
`validate_startup_auth` — check the log for the specific error.

#### Step 5 — Confirm old token is rejected

```bash
curl -sf -X POST http://<orchestrator>/v1/pipeline/approve \
  -H "X-Operator-Token: <OLD_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"candidate_id":"probe","telegram_user_id":0,"correlation_id":"rot-probe"}'
# Expected: HTTP 403
```

Replace `<OLD_TOKEN>` with the previous value. A `403` confirms the old token is no
longer accepted. A `401` means the header was missing (wrong header name). Any `2xx`
means the rotation did not take effect — recheck env vars and restart.

---

### Suspected Token Leak — Immediate Halt Procedure

If a token is suspected compromised, halt trading immediately before rotating.

#### 1. Halt the kill switch (stops all approvals and execution)

```bash
curl -X POST http://<kill-switch>/v1/kill-switch/halt \
  -H "X-Admin-Token: <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "operator_user_id": 0,
    "reason": "suspected_token_leak",
    "actor": "ops",
    "correlation_id": "leak-halt-001"
  }'
# Expected: {"ok": true, "data": {"kill_switch_active": true}}
```

#### 2. Rotate the compromised token immediately (follow steps 1–5 above)

Rotate the specific tier that was leaked. If uncertain which tier, rotate all three.

#### 3. Verify the kill switch is still active after rotation

```bash
curl -sf "http://<kill-switch>/v1/kill-switch/status?correlation_id=post-rotate-check" \
  -H "X-Internal-Token: <NEW_INTERNAL_TOKEN>"
# Expected: {"data": {"kill_switch_active": true}}
```

#### 4. Review audit trail

Check `operator_actions` and `journal_events` tables for any actions taken with the
suspected token during the exposure window.

```sql
SELECT * FROM operator_actions
WHERE created_at > '<exposure_start>'
ORDER BY created_at DESC;

SELECT * FROM journal_events
WHERE event_type IN ('candidate_approved','kill_switch_halted','kill_switch_resumed')
  AND created_at > '<exposure_start>'
ORDER BY created_at DESC;
```

#### 5. Resume trading only after confirmation

```bash
curl -X POST http://<kill-switch>/v1/kill-switch/resume \
  -H "X-Admin-Token: <NEW_ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "operator_user_id": 0,
    "actor": "ops",
    "correlation_id": "leak-resume-001"
  }'
```

Only resume after: (a) token rotation is complete and verified, (b) audit review shows
no unauthorised approvals or position changes, (c) explicit sign-off from the operator.
