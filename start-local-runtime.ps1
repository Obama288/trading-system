# start-local-runtime.ps1
# Starts all paper-mode services in separate PowerShell windows.
# Run from E:\trading-system after Docker is up and .env is populated.

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Load .env into the current process so child processes inherit it
Write-Host "Loading .env..." -ForegroundColor Cyan
foreach ($line in Get-Content "$root\.env") {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.+)$') {
        $name  = $Matches[1].Trim()
        $value = $Matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}
Write-Host ".env loaded." -ForegroundColor Cyan
Write-Host ""

function Start-Service {
    param([string]$Name, [int]$Port, [string]$Module)
    Write-Host "  Starting $Name on 127.0.0.1:$Port ..." -ForegroundColor Yellow
    Start-Process powershell `
        -WorkingDirectory $root `
        -ArgumentList '-NoExit', '-Command', "python -m uvicorn $Module --host 127.0.0.1 --port $Port"
    Start-Sleep -Milliseconds 400
}

Write-Host "=== Starting services (paper mode) ===" -ForegroundColor Cyan
Write-Host ""

# Leaf services first (no outbound service calls)
Start-Service "kill_switch"       8001 "apps.kill_switch.main:app"
Start-Service "journal_ingest"    8004 "apps.journal_ingest.main:app"
Start-Service "risk_engine"       8002 "apps.risk_engine.main:app"
Start-Service "review_gateway"    8003 "apps.review_gateway.main:app"

# Mid-tier (depend on leaf services)
Start-Service "position_manager"  8007 "apps.position_manager.main:app"
Start-Service "execution_service" 8006 "apps.execution_service.main:app"

# Top of pipeline
Start-Service "orchestrator"      8005 "apps.orchestrator.main:app"

# Observability / read services
Start-Service "incidents"         8009 "apps.incidents.main:app"
Start-Service "dashboard_service" 8008 "apps.dashboard_service.main:app"

Write-Host ""
Write-Host "=== All 9 services started ===" -ForegroundColor Green
Write-Host "Wait 15-20 seconds, then run health checks." -ForegroundColor Green
