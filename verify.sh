#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="registry-multistage-check"
PORT=8001

python - <<'PYEOF'
import json

with open("size_report.json") as f:
    report = json.load(f)

assert report["fits_target"] is True
assert report["savings_pct"] >= 20

print("size target: PASS")
print("minimum savings: PASS")
PYEOF

docker rm -f "$CONTAINER_NAME" > /dev/null 2>&1 || true

docker run -d \
  --name "$CONTAINER_NAME" \
  -p "$PORT":8000 \
  registry:multistage > /dev/null

cleanup() {
  docker rm -f "$CONTAINER_NAME" > /dev/null 2>&1 || true
}

trap cleanup EXIT

echo "waiting for service..."

for i in {1..30}; do
  if curl -fsS "http://localhost:$PORT/health" > /dev/null; then
    break
  fi
  sleep 1
done

curl -fsS "http://localhost:$PORT/health"
echo

curl -fsS "http://localhost:$PORT/registry" |
  grep -q "Qwen2.5-0.5B-Instruct"

curl -fsS \
  "http://localhost:$PORT/registry/Qwen2.5-0.5B-Instruct" |
  grep -q "approved"

STATUS=$(
  curl -s \
    -o /dev/null \
    -w "%{http_code}" \
    "http://localhost:$PORT/registry/unknown-model"
)

test "$STATUS" = "404"

echo "health check: PASS"
echo "registry list: PASS"
echo "model lookup: PASS"
echo "unknown model 404: PASS"
echo "GREEN CHECK: PASS"
