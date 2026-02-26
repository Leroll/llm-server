#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

echo "Stopping Dashboard service..."

if [ -f "$LOG_DIR/dashboard.pid" ]; then
    PID=$(cat "$LOG_DIR/dashboard.pid")
    if ps -p $PID > /dev/null; then
        echo "Stopping Dashboard (PID: $PID)..."
        kill $PID
        pkill -f "src/llm_server/dashboard.py" > /dev/null 2>&1
        rm "$LOG_DIR/dashboard.pid"
    else
        echo "Dashboard is not running (PID $PID not found)."
        pkill -f "src/llm_server/dashboard.py" > /dev/null 2>&1
        rm "$LOG_DIR/dashboard.pid"
    fi
else
    echo "Dashboard PID file not found."
    pkill -f "src/llm_server/dashboard.py" > /dev/null 2>&1
fi

echo "Done."
