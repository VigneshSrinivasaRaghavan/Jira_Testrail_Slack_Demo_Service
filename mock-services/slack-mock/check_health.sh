#!/bin/bash

# Health check script for Slack Mock Service

echo "🔍 Checking Slack Mock Service health..."

# Check if service is running on port 4003
if curl -s -f http://localhost:4003/health > /dev/null 2>&1; then
    echo "✅ Service is healthy and responding"
    
    # Get health details
    echo "📊 Health details:"
    curl -s http://localhost:4003/health | python3 -m json.tool
    
    echo ""
    echo "🌐 Available endpoints:"
    echo "  - Web UI: http://localhost:4003/ui"
    echo "  - API Docs: http://localhost:4003/docs"
    echo "  - Health: http://localhost:4003/health"
    echo "  - Post Message: POST http://localhost:4003/api/chat.postMessage"
    echo "  - Get History: GET http://localhost:4003/api/conversations.history"
    
else
    echo "❌ Service is not responding on port 4003"
    echo "💡 Try running: ./start.sh"
    exit 1
fi
