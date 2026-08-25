#!/bin/sh
set -eu

WORKSPACE="${WORKSPACE:-/workspace}"
STATE_DIR="${AGENT_CATALOG_STATE_DIR:-${WORKSPACE}/agentc-state}"
REPO_DIR="${CATALOG_REPO_DIR:-${WORKSPACE}/source}"

CATALOG_GIT_URL="${CATALOG_GIT_URL:-https://github.com/mminichino/couchbase-agent-memory-demo.git}"
CATALOG_GIT_REF="${CATALOG_GIT_REF:-main}"

# Optional token for private repos (GitHub HTTPS).
if [ -n "${CATALOG_GIT_TOKEN:-}" ]; then
  # Rewrite https://github.com/org/repo.git -> https://x-access-token:TOKEN@github.com/org/repo.git
  CATALOG_GIT_URL="$(
    printf '%s' "$CATALOG_GIT_URL" | sed -E "s#https://([^/]+)/#https://x-access-token:${CATALOG_GIT_TOKEN}@\\1/#"
  )"
fi

export AGENT_CATALOG_INTERACTIVE="${AGENT_CATALOG_INTERACTIVE:-False}"
export AGENT_CATALOG_CONN_STRING="${AGENT_CATALOG_CONN_STRING:-couchbase://couchbase-demo}"
export AGENT_CATALOG_USERNAME="${AGENT_CATALOG_USERNAME:-Administrator}"
export AGENT_CATALOG_PASSWORD="${AGENT_CATALOG_PASSWORD:-password}"
export AGENT_CATALOG_BUCKET="${AGENT_CATALOG_BUCKET:-ams}"
unset AGENT_CATALOG_CATALOG_PATH AGENT_CATALOG_ACTIVITY_PATH AGENT_CATALOG_PROJECT_PATH || true
export CB_CONN_STRING="${CB_CONN_STRING:-couchbase://couchbase-demo}"
export CB_USERNAME="${CB_USERNAME:-Administrator}"
export CB_PASSWORD="${CB_PASSWORD:-password}"

mkdir -p "$STATE_DIR"

echo "Cloning Agent Catalog source from GitHub..."
if [ -n "${CATALOG_GIT_TOKEN:-}" ]; then
  echo "  url=<redacted; token auth enabled>"
else
  echo "  url=${CATALOG_GIT_URL}"
fi
echo "  ref=${CATALOG_GIT_REF}"
rm -rf "$REPO_DIR"
git clone --depth 1 --branch "$CATALOG_GIT_REF" "$CATALOG_GIT_URL" "$REPO_DIR"

cd "$REPO_DIR"

if [ ! -d catalog ]; then
  echo "ERROR: cloned repository has no catalog/ directory at ref ${CATALOG_GIT_REF}." >&2
  echo "Push catalog assets to GitHub or set CATALOG_GIT_REF to a branch that contains them." >&2
  exit 1
fi

# Use the uv project / venv baked into the image at /workspace.
run_agentc() {
  uv --project "$WORKSPACE" run agentc --no-interactive "$@"
}

echo "Initializing Agent Catalog (local + Couchbase)..."
run_agentc init --local --db --bucket "$AGENT_CATALOG_BUCKET"

echo "Indexing catalog tools and prompts..."
run_agentc index catalog --tools --prompts

echo "Publishing catalog to Couchbase bucket ${AGENT_CATALOG_BUCKET}..."
run_agentc publish --bucket "$AGENT_CATALOG_BUCKET"

# Share the indexed local catalog with the grpc service via the compose volume.
echo "Syncing local catalog state to ${STATE_DIR}..."
rm -rf "${STATE_DIR}/.agent-catalog" "${STATE_DIR}/.agent-activity"
cp -a .agent-catalog "${STATE_DIR}/.agent-catalog"
if [ -d .agent-activity ]; then
  cp -a .agent-activity "${STATE_DIR}/.agent-activity"
else
  mkdir -p "${STATE_DIR}/.agent-activity"
fi

echo "Agent Catalog bootstrap complete (source=$(git rev-parse --short HEAD) from ${CATALOG_GIT_REF})."
