#!/bin/bash
# Clears all test cases, results, and run entries from the TestRail mock DB
# then restarts the service so the changes take effect immediately.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$SCRIPT_DIR/testrail.db"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$REPO_ROOT/logs/testrail-mock.log"

echo "Clearing TestRail test cases..."

# Wipe cases, results, and run entries
sqlite3 "$DB_PATH" "DELETE FROM results; DELETE FROM run_entries; DELETE FROM cases;"

REMAINING=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM cases;")
echo "Done. Cases remaining: $REMAINING"

# Restart the local service process to flush SQLAlchemy connection pool
TESTRAIL_PID=$(lsof -ti :4002 2>/dev/null || true)
if [ -n "$TESTRAIL_PID" ]; then
    echo "Restarting TestRail service (PID $TESTRAIL_PID)..."
    kill "$TESTRAIL_PID"
    sleep 2
    cd "$SCRIPT_DIR"
    nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 4002 >> "$LOG_FILE" 2>&1 &
    sleep 3
    echo "TestRail service restarted on http://localhost:4002"
else
    echo "TestRail service not running — start it manually if needed."
fi
