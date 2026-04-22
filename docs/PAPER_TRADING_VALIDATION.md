# Paper Trading Validation

## Purpose

This runbook defines how to run and validate the system in paper-trading mode before any move toward live exchange integration.

Paper trading must exercise the real internal pipeline on real market data while preventing any real exchange order placement.

## Required Env And Config

Minimum required runtime settings:

- `EXECUTION_MODE=paper`
- valid database connection settings
- valid Redis settings if used by surrounding infrastructure
- service base URLs configured so internal services can reach each other
- kill switch service available
- orchestrator, execution_service, position_manager, journal_ingest, dashboard_service available

Recommended checks before startup:

- DB migrations are up to date
- `EXECUTION_MODE` is explicitly set to `paper`
- kill switch status is known before starting observation
- dashboards are reachable

## How To Run In Paper Mode

1. Set `EXECUTION_MODE=paper`.
2. Start the required services.
3. Confirm `execution_service` reports paper mode on readiness/version endpoints.
4. Confirm kill switch status is healthy and controllable.
5. Allow the normal pipeline to process real market data.
6. Observe candidate -> execution -> position flow without any real exchange order placement.

## Daily Monitoring

Review these items every day during validation:

- count of paper executions
- count of opened positions
- count of closed positions
- journal events for `paper_execution_filled`
- journal events for execution failures
- kill switch block events
- dashboard stats consistency
- any orphaned states between `trade_candidates`, `executions`, and `positions`

## Validation Checklist

- `EXECUTION_MODE=paper`
- kill switch works
- candidate -> execution -> position flow works
- journal events exist
- dashboard stats visible

## Required Validation Metrics

Track these metrics throughout the validation window:

- total paper trades
- win rate
- pnl
- avg rr
- failures count
- kill switch blocks
- orphaned states count

Authoritative sources for validation metrics:

- `positions`
- `executions`
- `journal_events`

Research output is advisory only and must not be used for validation scoring.

## Minimum Sample Size

Minimum required sample size before evaluation:

- `30+ trades`

Do not treat early results from a smaller sample as sufficient validation.

## Stop Conditions For Validation Failure

Stop paper-trading validation and investigate if any of the following occurs:

- kill switch fails to block execution when activated
- candidate -> execution -> position flow breaks
- repeated orphaned execution or position states appear
- journal events are missing for execution or position activity
- dashboard stats are missing or materially inconsistent with DB truth
- execution failures rise above normal operational noise
- repeated duplicate or inconsistent state transitions appear

## Success Criteria Before Moving Toward Live Integration

All of the following should be true before advancing toward live integration:

- paper mode remains enforced throughout validation
- kill switch behavior is verified repeatedly
- candidate -> execution -> position flow is stable
- journal and audit coverage are present and consistent
- dashboard stats are visible and match authoritative DB state
- at least `30+ trades` have been observed
- no unresolved orphaned state pattern remains
- failure rate is operationally acceptable

## Notes

- This runbook does not change authority rules.
- This runbook does not change APIs.
- This runbook does not authorize live trading.
- Live trading remains not ready until paper-trading validation is completed successfully.
