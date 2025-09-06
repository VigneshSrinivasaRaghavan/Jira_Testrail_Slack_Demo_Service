#!/bin/bash
# Quick start script for TestRail Mock Service (from repo root)

set -e

echo "🚀 Starting TestRail Mock Service with Docker/Podman..."

# Navigate to repo root (two levels up from testrail-mock folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

# Check if we're in the repo root
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Could not find docker-compose.yml in repo root"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Check if podman is available, fallback to docker
if command -v podman >/dev/null 2>&1; then
    CONTAINER_CMD="podman"
elif command -v docker >/dev/null 2>&1; then
    CONTAINER_CMD="docker"
else
    echo "❌ Error: Neither podman nor docker found. Please install one of them."
    exit 1
fi

echo "📦 Using $CONTAINER_CMD to start services..."

# Start the service
echo "🔧 Building and starting TestRail Mock..."
$CONTAINER_CMD compose up -d --build testrail-mock

# Wait a moment for startup
sleep 3

# Check if service is running
if $CONTAINER_CMD compose ps testrail-mock | grep -q "Up"; then
    echo "✅ TestRail Mock Service started successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   - UI Dashboard: http://localhost:4002/ui"
    echo "   - Test Cases: http://localhost:4002/ui/cases"
    echo "   - API Docs: http://localhost:4002/docs"
    echo "   - Health: http://localhost:4002/health"
    echo ""
    echo "📋 Useful commands:"
    echo "   - View logs: $CONTAINER_CMD compose logs -f testrail-mock"
    echo "   - Stop service: $CONTAINER_CMD compose down"
    echo "   - Restart: $CONTAINER_CMD compose restart testrail-mock"
    echo ""
    echo "🧪 Sample API calls:"
    echo "   - Get test cases: curl -H \"Authorization: Bearer test-token\" http://localhost:4002/api/v2/cases/1"
    echo "   - Add test result: curl -X POST -H \"Authorization: Bearer test-token\" -H \"Content-Type: application/json\" -d '{\"status_id\":1,\"comment\":\"Test passed\"}' http://localhost:4002/api/v2/results/1"
    echo ""
else
    echo "❌ Failed to start TestRail Mock Service"
    echo "📋 Check logs: $CONTAINER_CMD compose logs testrail-mock"
    exit 1
fi
