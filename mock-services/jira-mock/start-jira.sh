#!/bin/bash
# Quick start script for Jira Mock Service (from repo root)

set -e

echo "🚀 Starting Jira Mock Service with Podman..."

# Navigate to repo root (two levels up from jira-mock folder)
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
echo "🔧 Building and starting Jira Mock..."
$CONTAINER_CMD compose up -d --build jira-mock

# Wait a moment for startup
sleep 2

# Check if service is running
if $CONTAINER_CMD compose ps jira-mock | grep -q "Up"; then
    echo "✅ Jira Mock Service started successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   - UI: http://localhost:4001/ui"
    echo "   - API Docs: http://localhost:4001/docs"
    echo "   - Health: http://localhost:4001/health"
    echo ""
    echo "📋 Useful commands:"
    echo "   - View logs: $CONTAINER_CMD compose logs -f jira-mock"
    echo "   - Stop service: $CONTAINER_CMD compose down"
    echo "   - Restart: $CONTAINER_CMD compose restart jira-mock"
    echo ""
else
    echo "❌ Failed to start Jira Mock Service"
    echo "📋 Check logs: $CONTAINER_CMD compose logs jira-mock"
    exit 1
fi
