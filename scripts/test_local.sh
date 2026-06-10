#!/usr/bin/env bash
# Run local health check and a sample interview invocation.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
SESSION_ID="${SESSION_ID:-test-session-1}"
USER_ID="${USER_ID:-candidate-1}"

echo "==> Health check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
if [ "$HTTP_CODE" != "200" ]; then
  echo "FAIL: GET /health returned ${HTTP_CODE}" >&2
  exit 1
fi
echo "PASS: GET /health -> 200"

echo "==> Interview start..."
curl -s -X POST "${BASE_URL}/invocations" \
  -H "Content-Type: application/json" \
  -H "X-GreenNode-AgentBase-Session-Id: ${SESSION_ID}" \
  -H "X-GreenNode-AgentBase-User-Id: ${USER_ID}" \
  -d '{"message": "Tôi muốn phỏng vấn React, level mid"}' | jq .

echo "==> Sample answer..."
curl -s -X POST "${BASE_URL}/invocations" \
  -H "Content-Type: application/json" \
  -H "X-GreenNode-AgentBase-Session-Id: ${SESSION_ID}" \
  -H "X-GreenNode-AgentBase-User-Id: ${USER_ID}" \
  -d '{"message": "React re-render khi state hoặc props thay đổi. Virtual DOM so sánh diff rồi cập nhật DOM thật."}' | jq .
