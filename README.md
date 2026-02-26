# 基于 vLLM 和 Dashboard 的 LLM 服务端

本项目提供了一个本地的、兼容 OpenAI 接口的 vLLM 服务端，以及一个用于监控指标的 Streamlit 仪表盘。项目使用 `uv` 进行包管理。

## 前置要求

- Python 3.10+
- `uv` 包管理器
- 支持 CUDA 的 NVIDIA GPU

## 安装设置

1. 使用 `uv` 安装依赖：
   ```bash
   uv sync
   ```

## 运行服务

脚本位于 `scripts/` 目录中，将使用 `nohup` 在后台运行服务。日志和 PID 文件存储在 `logs/` 目录中。

1. 启动兼容 OpenAI 接口的 vLLM 服务端：
   ```bash
   ./scripts/start_vllm.sh
   ```
   这将在 `http://localhost:8845` 启动服务。模型需要自行配置。

2. 启动监控仪表盘：
   ```bash
   ./scripts/start_dashboard.sh
   ```
   这将在 `http://localhost:7857` 启动一个 Streamlit 应用。您可以查看实时指标，如运行中的请求、等待中的请求以及 GPU/CPU 缓存使用情况。

3. 停止所有服务：
   ```bash
   ./scripts/stop_all.sh
   ```

## 测试服务

您可以使用提供的测试脚本来测试兼容 OpenAI 的 API：
```bash
./scripts/client.sh
```

## 接口端点

- **OpenAI API 基础 URL**: `http://localhost:8845/v1`
- **Metrics 指标端点**: `http://localhost:8845/metrics`
- **Dashboard 仪表盘**: `http://localhost:7857`
