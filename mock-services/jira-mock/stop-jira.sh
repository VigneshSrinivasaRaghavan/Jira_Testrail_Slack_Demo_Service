#!/bin/bash
# Stop script for Jira Mock Service

set -e

echo "🛑 Stopping Jira Mock Service..."

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
    echo "❌ Error: Neither podman nor docker found."
    exit 1
fi

# Stop the service
$CONTAINER_CMD compose down

echo "✅ Jira Mock Service stopped successfully!"
