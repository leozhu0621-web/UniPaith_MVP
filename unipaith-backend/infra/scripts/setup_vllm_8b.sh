#!/bin/bash
# User-data script for g5.xlarge: serves Llama 3.1 8B + nomic-embed-text
set -euo pipefail

S3_BUCKET="${s3_bucket}"
MODEL_DIR="/opt/models"
LOG_DIR="/var/log/vllm"
mkdir -p "$MODEL_DIR" "$LOG_DIR"

# Install vLLM
pip install vllm>=0.6.0

# Download model weights from S3 cache (faster) or HuggingFace (fallback)
if aws s3 ls "s3://$S3_BUCKET/meta-llama/Llama-3.1-8B-Instruct/" 2>/dev/null; then
    aws s3 sync "s3://$S3_BUCKET/meta-llama/Llama-3.1-8B-Instruct/" "$MODEL_DIR/Llama-3.1-8B-Instruct/"
else
    huggingface-cli download meta-llama/Llama-3.1-8B-Instruct --local-dir "$MODEL_DIR/Llama-3.1-8B-Instruct"
    aws s3 sync "$MODEL_DIR/Llama-3.1-8B-Instruct/" "s3://$S3_BUCKET/meta-llama/Llama-3.1-8B-Instruct/"
fi

if aws s3 ls "s3://$S3_BUCKET/nomic-ai/nomic-embed-text-v1.5/" 2>/dev/null; then
    aws s3 sync "s3://$S3_BUCKET/nomic-ai/nomic-embed-text-v1.5/" "$MODEL_DIR/nomic-embed-text-v1.5/"
else
    huggingface-cli download nomic-ai/nomic-embed-text-v1.5 --local-dir "$MODEL_DIR/nomic-embed-text-v1.5"
    aws s3 sync "$MODEL_DIR/nomic-embed-text-v1.5/" "s3://$S3_BUCKET/nomic-ai/nomic-embed-text-v1.5/"
fi

# Start vLLM for Llama 3.1 8B (port 8001)
nohup python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_DIR/Llama-3.1-8B-Instruct" \
    --host 0.0.0.0 \
    --port 8001 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.7 \
    > "$LOG_DIR/vllm-8b.log" 2>&1 &

# Start vLLM for nomic-embed-text (port 8003, uses remaining GPU memory)
nohup python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_DIR/nomic-embed-text-v1.5" \
    --host 0.0.0.0 \
    --port 8003 \
    --task embedding \
    --gpu-memory-utilization 0.25 \
    > "$LOG_DIR/vllm-embed.log" 2>&1 &

echo "vLLM 8B + embedding server started"
