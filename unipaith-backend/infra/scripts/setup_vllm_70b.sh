#!/bin/bash
# User-data script for g5.12xlarge: serves Llama 3.1 70B
set -euo pipefail

S3_BUCKET="${s3_bucket}"
MODEL_DIR="/opt/models"
LOG_DIR="/var/log/vllm"
mkdir -p "$MODEL_DIR" "$LOG_DIR"

# Install vLLM
pip install vllm>=0.6.0

# Download model weights from S3 cache (faster) or HuggingFace (fallback)
if aws s3 ls "s3://$S3_BUCKET/meta-llama/Llama-3.1-70B-Instruct/" 2>/dev/null; then
    aws s3 sync "s3://$S3_BUCKET/meta-llama/Llama-3.1-70B-Instruct/" "$MODEL_DIR/Llama-3.1-70B-Instruct/"
else
    huggingface-cli download meta-llama/Llama-3.1-70B-Instruct --local-dir "$MODEL_DIR/Llama-3.1-70B-Instruct"
    aws s3 sync "$MODEL_DIR/Llama-3.1-70B-Instruct/" "s3://$S3_BUCKET/meta-llama/Llama-3.1-70B-Instruct/"
fi

# Start vLLM for Llama 3.1 70B (port 8002)
# g5.12xlarge has 4x A10G (96GB total) — tensor parallel across all 4
nohup python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_DIR/Llama-3.1-70B-Instruct" \
    --host 0.0.0.0 \
    --port 8002 \
    --tensor-parallel-size 4 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.90 \
    > "$LOG_DIR/vllm-70b.log" 2>&1 &

echo "vLLM 70B server started"
