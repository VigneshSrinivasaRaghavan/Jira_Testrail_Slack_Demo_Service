#!/bin/bash
# Quick start script for Jira Mock Service (local development)

set -e

echo "🚀 Starting Jira Mock Service..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the jira-mock directory"
    echo "   cd mock-services/jira-mock && ./start.sh"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip and install dependencies
echo "📥 Installing dependencies..."
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Start the server
echo "✅ Starting Jira Mock on http://localhost:4001"
echo "   - UI: http://localhost:4001/ui"
echo "   - API Docs: http://localhost:4001/docs"
echo "   - Health: http://localhost:4001/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn app:app --host 0.0.0.0 --port 4001 --reload
