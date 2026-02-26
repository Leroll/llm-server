#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Start Streamlit dashboard
HOST=127.0.0.1
PORT=6006
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"

echo "Starting Streamlit dashboard on port $PORT"
echo "Logs will be written to $LOG_DIR/dashboard.log"

cd "$PROJECT_ROOT" && nohup uv run streamlit run src/llm_server/dashboard.py --server.port $PORT --server.address $HOST > "$LOG_DIR/dashboard.log" 2>&1 &
echo $! > "$LOG_DIR/dashboard.pid"
echo "Dashboard started with PID $(cat $LOG_DIR/dashboard.pid)"

# 显式打印 URL 以便 VS Code 自动感知并转发端口
echo "Dashboard is running at: http://$HOST:$PORT"
