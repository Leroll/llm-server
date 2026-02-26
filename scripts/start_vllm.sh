#!/bin/bash
# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ------------
# 配置项
# ------------
MODEL_PATH="/root/autodl-tmp/models/Qwen/Qwen3-8B"
MODEL_NAME="qwen3-8b"
PORT=8845
MAX_MODEL_LEN=16384
GPU_MEMORY_UTILIZATION=0.9
LOG_DIR="$PROJECT_ROOT/logs"


# ------------
# 启动 vLLM 服务器
# ------------
mkdir -p "$LOG_DIR"

echo "Starting vLLM server..."
echo "Model: $MODEL_PATH on port $PORT"
echo "Logs will be written to $LOG_DIR/vllm.log"

cd "$PROJECT_ROOT" && nohup uv run vllm serve \
    $MODEL_PATH \
    --served-model-name $MODEL_NAME \
    --port $PORT \
    --trust-remote-code \
    --max-model-len $MAX_MODEL_LEN \
    --gpu-memory-utilization $GPU_MEMORY_UTILIZATION > "$LOG_DIR/vllm.log" 2>&1 &

echo $! > "$LOG_DIR/vllm.pid"
echo "vLLM server started with PID $(cat $LOG_DIR/vllm.pid)"
