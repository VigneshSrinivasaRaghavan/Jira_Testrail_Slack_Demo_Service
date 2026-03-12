#!/bin/bash
# Clear Local Data Script for Mock Services
# This script clears all local data from Jira, Slack, and TestRail mock services

echo "🧹 Clearing local data from all mock services..."

# Remove database files
echo "📂 Removing database files..."
rm -f ./mock-services/jira-mock/jira.db
rm -f ./mock-services/slack-mock/slack_mock.db  
rm -f ./mock-services/testrail-mock/testrail.db

# Remove Python cache files
echo "🐍 Removing Python cache directories..."
rm -rf ./mock-services/jira-mock/__pycache__
rm -rf ./mock-services/slack-mock/__pycache__
rm -rf ./mock-services/testrail-mock/__pycache__

# Clear data directory (if it has files)
echo "📁 Clearing Slack data directory..."
rm -f ./mock-services/slack-mock/data/*

# Remove log files and PID files
echo "📝 Removing log files..."
rm -f ./logs/*.log
rm -f ./logs/*.pid
rm -f ./logs/archive/*.log

echo "✅ All local data cleared successfully!"
echo ""
echo "Note: When you restart the services, they will:"
echo "- Recreate empty databases"
echo "- Load fresh seed/sample data"
echo "- Start with clean logs"
echo ""
echo "To restart all services, run:"
echo "  ./start-all.sh"