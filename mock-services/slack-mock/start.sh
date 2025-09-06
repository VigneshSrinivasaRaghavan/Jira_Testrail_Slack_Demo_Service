#!/bin/bash

# Slack Mock Service Startup Script

set -e

echo "🚀 Starting Slack Mock Service..."

# Set default environment variables
export PORT=${PORT:-4003}
export HOST=${HOST:-0.0.0.0}
export MOCK_AUTH_REQUIRED=${MOCK_AUTH_REQUIRED:-true}
export DEFAULT_SLACK_CHANNEL=${DEFAULT_SLACK_CHANNEL:-qa-reports}

echo "📋 Configuration:"
echo "  Port: $PORT"
echo "  Host: $HOST"
echo "  Auth Required: $MOCK_AUTH_REQUIRED"
echo "  Default Channel: $DEFAULT_SLACK_CHANNEL"

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "🐳 Running in Docker container"
else
    echo "💻 Running locally"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

# Create data directory if it doesn't exist
mkdir -p data

echo "🎯 Starting FastAPI server..."
echo "📡 API will be available at: http://$HOST:$PORT"
echo "🌐 Web UI will be available at: http://$HOST:$PORT/ui"
echo "📚 API docs will be available at: http://$HOST:$PORT/docs"

# Initialize database first
echo "🔧 Initializing database..."
python3 -c "
try:
    from storage import init_db
    init_db()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    exit(1)
"

# Verify app can be imported
echo "🔍 Verifying application..."
python3 -c "
try:
    from app_simple import app
    print('✅ Application verified successfully')
except Exception as e:
    print(f'❌ Application verification failed: {e}')
    exit(1)
"

# Start the application using simplified startup
echo "🎯 Starting FastAPI server..."
exec uvicorn app_simple:app --host "$HOST" --port "$PORT" --log-level info --access-log
