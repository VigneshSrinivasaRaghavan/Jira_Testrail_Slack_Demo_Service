#!/bin/bash
# TestRail Mock Service Monitor Script
# Usage: ./monitor.sh

PORT=4002
SERVICE_NAME="TestRail Mock"

echo "=== $SERVICE_NAME Monitor ==="
echo "Checking service on port $PORT..."

# Check if service is running
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "✓ Service is running on port $PORT"
    
    # Health check
    if curl -s http://localhost:$PORT/health | grep -q "healthy"; then
        echo "✓ Health check passed"
    else
        echo "✗ Health check failed"
        exit 1
    fi
    
    # UI check
    if curl -s http://localhost:$PORT/ui | grep -q "TestRail Mock"; then
        echo "✓ UI is accessible"
    else
        echo "✗ UI is not accessible"
        exit 1
    fi
    
    # API check
    if curl -s -H "Authorization: Bearer test-token" "http://localhost:$PORT/api/v2/projects" | grep -q "Demo Project"; then
        echo "✓ API is working"
    else
        echo "✗ API is not working"
        exit 1
    fi
    
    echo "✓ All checks passed - Service is healthy!"
    
else
    echo "✗ Service is not running on port $PORT"
    echo "To start the service, run: python3 app.py"
    exit 1
fi
