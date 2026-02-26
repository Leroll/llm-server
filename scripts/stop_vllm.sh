#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

echo "Stopping vLLM service..."

if [ -f "$LOG_DIR/vllm.pid" ]; then
    PID=$(cat "$LOG_DIR/vllm.pid")
    if ps -p $PID > /dev/null; then
        echo "Stopping vLLM server (PID: $PID)..."
        kill $PID
        pkill -f "vllm serve" > /dev/null 2>&1
        rm "$LOG_DIR/vllm.pid"
    else
        echo "vLLM server is not running (PID $PID not found)."
        pkill -f "vllm serve" > /dev/null 2>&1
        rm "$LOG_DIR/vllm.pid"
    fi
else
    echo "vLLM PID file not found."
    pkill -f "vllm serve" > /dev/null 2>&1
fi

echo "Done."
