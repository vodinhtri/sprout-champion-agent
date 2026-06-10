#!/usr/bin/env bash
# Setup GreenNode AgentBase platform resources for the interview agent.
# Prerequisites: IAM credentials in .greennode.json or GREENNODE_CLIENT_ID/SECRET env vars.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SCRIPTS=".cursor/skills/agentbase/scripts"

echo "==> Checking IAM credentials..."
bash "$SCRIPTS/check_credentials.sh" iam

if bash "$SCRIPTS/check_credentials.sh" llm 2>/dev/null; then
  echo "==> LLM API key already configured."
else
  echo "==> Creating LLM API key..."
  bash "$SCRIPTS/aip.sh" api-keys create --name interview-agent-key
  bash "$SCRIPTS/save_env_var.sh" --key LLM_BASE_URL \
    --value "https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1"
fi

if grep -qE '^MEMORY_ID=.+' .env 2>/dev/null; then
  echo "==> MEMORY_ID already configured in .env."
else
  echo "==> Creating AgentBase Memory store..."
  RESPONSE=$(bash "$SCRIPTS/memory.sh" create \
    --name interview-agent-memory \
    --description "Interview Q&A agent conversation memory" \
    --expiry-days 30 \
    --strategy-name semantic-facts \
    --strategy-type SEMANTIC \
    --namespace-template "/strategies/{memoryStrategyId}/actors/{actorId}" \
    --auto-generate)
  MEMORY_ID=$(echo "$RESPONSE" | jq -r '.id // .data.id // empty')
  if [ -z "$MEMORY_ID" ]; then
    echo "ERROR: Could not extract memory ID from response." >&2
    echo "$RESPONSE" >&2
    exit 1
  fi
  bash "$SCRIPTS/save_env_var.sh" --key MEMORY_ID --value "$MEMORY_ID"
  bash "$SCRIPTS/save_env_var.sh" --key MEMORY_STRATEGY_ID --value "semantic-facts"
fi

if ! grep -qE '^LLM_MODEL=.+' .env 2>/dev/null; then
  echo "==> Setting default LLM model (gpt-4o-mini if available)..."
  MODELS=$(bash "$SCRIPTS/aip.sh" models list --size 50 2>/dev/null || true)
  MODEL=$(echo "$MODELS" | jq -r '
    [.listData[]? | select(.modelStatus == "ENABLED" and (.enabledTypes | index("chat")))]
    | (map(select(.path | test("gpt-4o-mini"; "i"))) + .)
    | .[0].path // empty
  ')
  if [ -z "$MODEL" ]; then
    MODEL=$(echo "$MODELS" | jq -r '
      [.listData[]? | select(.modelStatus == "ENABLED" and (.enabledTypes | index("chat")))]
      | .[0].path // empty
    ')
  fi
  if [ -n "$MODEL" ]; then
    bash "$SCRIPTS/save_env_var.sh" --key LLM_MODEL --value "$MODEL"
    echo "    LLM_MODEL=$MODEL"
  else
    echo "WARN: No ENABLED model found. Set LLM_MODEL manually in .env" >&2
  fi
fi

echo ""
echo "Platform setup complete. Verify with:"
echo "  bash $SCRIPTS/check_env.sh ."
echo "  source venv/bin/activate && python main.py"
