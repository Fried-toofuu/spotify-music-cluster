#!/bin/sh
set -eu

: "${HF_TOKEN:?HF_TOKEN Space secret is required}"
: "${ARTIFACT_DATASET:?ARTIFACT_DATASET Space variable is required}"

python - <<'PY'
import os
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id=os.environ["ARTIFACT_DATASET"],
    repo_type="dataset",
    local_dir="/tmp/artifacts",
    token=os.environ["HF_TOKEN"],
)
PY

export SPOTIFY_MODEL_DIR=/tmp/artifacts/deployment-v1
export SPOTIFY_VISUALIZATION_DIR=/tmp/artifacts/visualization
export SPOTIFY_RESEARCH_DIR=/tmp/artifacts/research-v1
export SPOTIFY_PUBLIC_MODE="${PUBLIC_MODE:-1}"
export SPOTIFY_API_BASE_URL=http://127.0.0.1:8000
export SPOTIFY_WEB_HOST=0.0.0.0
export SPOTIFY_WEB_PORT="${PORT:-7860}"
export GRADIO_ANALYTICS_ENABLED=False
export HF_HOME=/tmp/hf
export GRADIO_TEMP_DIR=/tmp/gradio

uvicorn spotify_cluster.api.app:app --host 127.0.0.1 --port 8000 &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' INT TERM EXIT

ready=0
for _ in $(seq 1 90); do
    if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=2)" 2>/dev/null; then
        ready=1
        break
    fi
    sleep 1
done

if [ "$ready" -ne 1 ]; then
    echo "API did not become ready" >&2
    exit 1
fi

python -m spotify_cluster.web.app
