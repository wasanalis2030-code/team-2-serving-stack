#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:?IMAGE is required}"
NAME="aidc-serving-green-check"

cleanup() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  rm -f health.json
}

trap cleanup EXIT

docker rm -f serving >/dev/null 2>&1 || true
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker rmi -f "$IMAGE" >/dev/null 2>&1 || true

echo "Pulling image from Docker Hub..."
docker pull "$IMAGE"

echo "Starting fresh container..."
docker run -d \
  --name "$NAME" \
  -p 8000:8000 \
  -v hf-cache:/home/app/.cache/huggingface \
  "$IMAGE" >/dev/null

echo "Waiting for health check..."

for i in $(seq 1 120); do
  if curl -fsS http://localhost:8000/health > health.json 2>/dev/null; then
    break
  fi

  if [ "$i" -eq 120 ]; then
    docker logs "$NAME"
    echo "GREEN CHECK: FAIL"
    exit 1
  fi

  sleep 5
done

grep -q '"status":"ok"' health.json

echo "Sending real completion..."

RESPONSE=$(curl -fsS \
  http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct",
    "messages": [
      {
        "role": "user",
        "content": "Say hi."
      }
    ],
    "max_tokens": 16
  }')

echo "$RESPONSE"
echo "$RESPONSE" | grep -q '"object":"chat.completion"'
echo "$RESPONSE" | grep -q '"content":'

echo "GREEN CHECK: PASS"
