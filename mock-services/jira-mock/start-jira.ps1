# PowerShell script for Jira Mock Service (Windows alternative)
# Usage: .\start-jira.ps1

Write-Host "🚀 Starting Jira Mock Service with Docker/Podman..." -ForegroundColor Green

# Navigate to repo root (two levels up from jira-mock folder)
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
Write-Host "🔧 Building and starting Jira Mock..." -ForegroundColor Yellow
& $containerCmd compose up -d --build jira-mock

# Wait a moment for startup
Start-Sleep -Seconds 3

# Check if service is running
$status = & $containerCmd compose ps jira-mock 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Jira Mock Service started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
    Write-Host "   - UI: http://localhost:4001/ui"
    Write-Host "   - API Docs: http://localhost:4001/docs"
    Write-Host "   - Health: http://localhost:4001/health"
    Write-Host ""
    Write-Host "📋 Useful commands:" -ForegroundColor Cyan
    Write-Host "   - View logs: $containerCmd compose logs -f jira-mock"
    Write-Host "   - Stop service: $containerCmd compose down"
    Write-Host "   - Restart: $containerCmd compose restart jira-mock"
    Write-Host ""
} else {
    Write-Host "❌ Failed to start Jira Mock Service" -ForegroundColor Red
    Write-Host "📋 Check logs: $containerCmd compose logs jira-mock" -ForegroundColor Yellow
    exit 1
}
