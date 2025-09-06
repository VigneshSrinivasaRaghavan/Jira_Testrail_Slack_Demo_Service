# PowerShell script for TestRail Mock Service (Windows alternative)
# Usage: .\start-testrail.ps1

Write-Host "🚀 Starting TestRail Mock Service with Docker/Podman..." -ForegroundColor Green

# Navigate to repo root (two levels up from testrail-mock folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "../..")
Set-Location $repoRoot

# Check if we're in the repo root
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ Error: Could not find docker-compose.yml in repo root" -ForegroundColor Red
    Write-Host "   Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Check if docker or podman is available
$containerCmd = $null
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $containerCmd = "docker"
} elseif (Get-Command podman -ErrorAction SilentlyContinue) {
    $containerCmd = "podman"
} else {
    Write-Host "❌ Error: Neither docker nor podman found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Using $containerCmd to start services..." -ForegroundColor Cyan

# Start the service
Write-Host "🔧 Building and starting TestRail Mock..." -ForegroundColor Yellow
& $containerCmd compose up -d --build testrail-mock

# Wait a moment for startup
Start-Sleep -Seconds 3

# Check if service is running
$status = & $containerCmd compose ps testrail-mock 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ TestRail Mock Service started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
    Write-Host "   - UI Dashboard: http://localhost:4002/ui"
    Write-Host "   - Test Cases: http://localhost:4002/ui/cases"
    Write-Host "   - API Docs: http://localhost:4002/docs"
    Write-Host "   - Health: http://localhost:4002/health"
    Write-Host ""
    Write-Host "📋 Useful commands:" -ForegroundColor Cyan
    Write-Host "   - View logs: $containerCmd compose logs -f testrail-mock"
    Write-Host "   - Stop service: $containerCmd compose down"
    Write-Host "   - Restart: $containerCmd compose restart testrail-mock"
    Write-Host ""
    Write-Host "🧪 Sample API calls:" -ForegroundColor Magenta
    Write-Host "   - Get test cases: curl -H `"Authorization: Bearer test-token`" http://localhost:4002/api/v2/cases/1"
    Write-Host "   - Add test result: curl -X POST -H `"Authorization: Bearer test-token`" -H `"Content-Type: application/json`" -d `"{`\`"status_id`\`":1,`\`"comment`\`":`\`"Test passed`\`"}`" http://localhost:4002/api/v2/results/1"
    Write-Host ""
} else {
    Write-Host "❌ Failed to start TestRail Mock Service" -ForegroundColor Red
    Write-Host "📋 Check logs: $containerCmd compose logs testrail-mock" -ForegroundColor Yellow
    exit 1
}
