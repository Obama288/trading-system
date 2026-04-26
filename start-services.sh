#!/bin/bash
cd /opt/trading-system
source venv/bin/activate

export $(cat .env | grep -v '^#' | grep '=' | xargs)

services=(
  "apps.kill_switch.main:app 8001"
  "apps.journal_ingest.main:app 8004"
  "apps.risk_engine.main:app 8002"
  "apps.review_gateway.main:app 8003"
  "apps.position_manager.main:app 8007"
  "apps.execution_service.main:app 8006"
  "apps.orchestrator.main:app 8005"
  "apps.incidents.main:app 8009"
  "apps.dashboard_service.main:app 8008"
)

for svc in "${services[@]}"; do
  module=$(echo $svc | cut -d' ' -f1)
  port=$(echo $svc | cut -d' ' -f2)
  echo "Starting $module on $port..."
  nohup python -m uvicorn $module --host 127.0.0.1 --port $port > /opt/trading-system/logs/${port}.log 2>&1 &
done

echo "All 9 services started"
