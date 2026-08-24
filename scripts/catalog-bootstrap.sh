#!/bin/sh
set -eu

cd /workspace

STATE_DIR="${AGENT_CATALOG_STATE_DIR:-/workspace/agentc-state}"

if [ ! -d .git ]; then
  git init -q
  git config user.email "demo@couchbase.com"
  git config user.name "Agent Catalog Demo"
fi

git add catalog/
if git diff --cached --quiet; then
  git commit -q --allow-empty -m "Agent Catalog demo assets"
else
  git commit -q -m "Agent Catalog demo assets"
fi

export AGENT_CATALOG_INTERACTIVE="${AGENT_CATALOG_INTERACTIVE:-False}"
export AGENT_CATALOG_CONN_STRING="${AGENT_CATALOG_CONN_STRING:-couchbase://couchbase-demo}"
export AGENT_CATALOG_USERNAME="${AGENT_CATALOG_USERNAME:-Administrator}"
export AGENT_CATALOG_PASSWORD="${AGENT_CATALOG_PASSWORD:-password}"
export AGENT_CATALOG_BUCKET="${AGENT_CATALOG_BUCKET:-ams}"
# Let agentc create the default .agent-catalog / .agent-activity under /workspace.
unset AGENT_CATALOG_CATALOG_PATH AGENT_CATALOG_ACTIVITY_PATH AGENT_CATALOG_PROJECT_PATH || true
export CB_CONN_STRING="${CB_CONN_STRING:-couchbase://couchbase-demo}"
export CB_USERNAME="${CB_USERNAME:-Administrator}"
export CB_PASSWORD="${CB_PASSWORD:-password}"

mkdir -p "$STATE_DIR"

echo "Initializing Agent Catalog (local + Couchbase)..."
uv run agentc --no-interactive init --local --db --bucket "$AGENT_CATALOG_BUCKET"

echo "Indexing catalog tools and prompts..."
uv run agentc --no-interactive index catalog --tools --prompts

echo "Publishing catalog to Couchbase bucket ${AGENT_CATALOG_BUCKET}..."
uv run agentc --no-interactive publish --bucket "$AGENT_CATALOG_BUCKET"

# Share the indexed local catalog with the grpc service via the compose volume.
echo "Syncing local catalog state to ${STATE_DIR}..."
rm -rf "${STATE_DIR}/.agent-catalog" "${STATE_DIR}/.agent-activity"
cp -a .agent-catalog "${STATE_DIR}/.agent-catalog"
if [ -d .agent-activity ]; then
  cp -a .agent-activity "${STATE_DIR}/.agent-activity"
else
  mkdir -p "${STATE_DIR}/.agent-activity"
fi

echo "Agent Catalog bootstrap complete."
