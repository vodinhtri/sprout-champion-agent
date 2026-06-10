#!/usr/bin/env bash
# Build, push, and deploy the interview agent to AgentBase Runtime.
# Prerequisites: IAM credentials, .env configured, Docker running.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SCRIPTS=".cursor/skills/agentbase/scripts"
RUNTIME_NAME="${1:-sprout-interview-agent}"
IMAGE_NAME="${2:-sprout-interview-agent}"
IMAGE_TAG="${3:-latest}"
FLAVOR="${4:-runtime-s2-general-2x4}"

echo "==> Checking prerequisites..."
bash "$SCRIPTS/check_credentials.sh" iam
test -f .env || { echo "ERROR: .env not found. Run scripts/setup_platform.sh first." >&2; exit 1; }

echo "==> Fetching Container Registry info..."
REPO_JSON=$(bash "$SCRIPTS/cr.sh" repo get)
REGISTRY_URL=$(echo "$REPO_JSON" | jq -r '.registryUrl')
REPO_NAME=$(echo "$REPO_JSON" | jq -r '.name')
FULL_IMAGE="${REGISTRY_URL}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "    Image: ${FULL_IMAGE}"

echo "==> Building Docker image..."
docker build --platform linux/amd64 -t "${FULL_IMAGE}" .

echo "==> Logging in to Container Registry..."
bash "$SCRIPTS/cr.sh" credentials docker-login

echo "==> Pushing image..."
docker push "${FULL_IMAGE}"

EXISTING=$(bash "$SCRIPTS/runtime.sh" list --size 100 | jq -r --arg n "$RUNTIME_NAME" '
  [.listData[]? | select(.name == $n)] | .[0].id // empty
')

if [ -n "$EXISTING" ]; then
  echo "==> Updating existing runtime: ${EXISTING}"
  bash "$SCRIPTS/runtime.sh" update "$EXISTING" \
    --image "$FULL_IMAGE" \
    --flavor "$FLAVOR" \
    --env-file .env \
    --from-cr
  RUNTIME_ID="$EXISTING"
else
  echo "==> Creating runtime: ${RUNTIME_NAME}"
  CREATE_RESP=$(bash "$SCRIPTS/runtime.sh" create \
    --name "$RUNTIME_NAME" \
    --description "Technical Interview Q&A Agent" \
    --image "$FULL_IMAGE" \
    --flavor "$FLAVOR" \
    --env-file .env \
    --from-cr)
  RUNTIME_ID=$(echo "$CREATE_RESP" | jq -r '.id // empty')
fi

echo ""
echo "Deploy complete."
echo "  Runtime ID: ${RUNTIME_ID}"
echo "  Image:      ${FULL_IMAGE}"
echo ""
echo "Verify:"
echo "  bash $SCRIPTS/runtime.sh get ${RUNTIME_ID}"
echo "  bash $SCRIPTS/runtime.sh endpoints list ${RUNTIME_ID}"
