# couchbase-agent-memory-demo

This demo showcases Couchbase Agent Memory Server, Couchbase MCP Server, and Couchbase Agent Catalog together on the AI Data Plane.

## Running the Demo via Docker Compose

Follow these steps to run the demo locally using Docker Compose.

### Prerequisites

You will need API keys to run this demo:

1. **LLM** — choose OpenAI **or** Claude via Agent Memory env vars:
   - **OpenAI**: set `OPENAI_API_KEY` (chat + AMS use `gpt-5.4` by default). Get a key at [platform.openai.com](https://platform.openai.com/).
   - **Claude**: leave `OPENAI_API_KEY` unset and set `AGENTMEMORY_LLM_API_KEY` to your Anthropic key, plus `AGENTMEMORY_LLM_URL` / `AGENTMEMORY_LLM_MODEL`. Get a key at [console.anthropic.com](https://console.anthropic.com/).
2. **Embeddings** (required for Agent Memory; separate from the chat LLM when using Claude):
   - With OpenAI: `OPENAI_API_KEY` also covers embeddings (`text-embedding-3-small` by default).
   - With Claude: set an OpenAI-compatible embedding endpoint via `AGENTMEMORY_EMBEDDING_URL`, `AGENTMEMORY_EMBEDDING_MODEL`, and `AGENTMEMORY_EMBEDDING_API_KEY` (for example Capella Model Service).
3. **Tavily API Key**: Used for web search capabilities. You can get one at [tavily.com](https://tavily.com/).

### Setup

1. Create a file named `.env` in the root directory of this project.
2. Add your API keys. Claude LLM and custom embeddings:

   ```env
   AGENTMEMORY_LLM_MODEL=claude-sonnet-5
   AGENTMEMORY_LLM_API_KEY=your_anthropic_key_here
   AGENTMEMORY_LLM_URL=https://api.anthropic.com/v1/
   AGENTMEMORY_EMBEDDING_URL=https://your_endpoint.ai.cloud.couchbase.com
   AGENTMEMORY_EMBEDDING_MODEL=nvidia/llama-3.2-nv-embedqa-1b-v2
   AGENTMEMORY_EMBEDDING_API_KEY=your_embedding_api_key
   TAVILY_API_KEY=your_tavily_key_here
   ```

   OpenAI for LLM and embeddings:

   ```env
   OPENAI_API_KEY=your_openai_key_here
   TAVILY_API_KEY=your_tavily_key_here
   ```

   See [Agent Memory env reference](https://docs.couchbase.com/ai/build/agent-memory/config-agent-mem-env.html) for `AGENTMEMORY_LLM_*` and `AGENTMEMORY_EMBEDDING_*`.

3. Get and run Agent Memory Server container

   ```shell
   docker load -i agentmemory-server-arm64-v1.0.0.tar
   ```

4. Ensure catalog assets are available on GitHub. The `catalog-bootstrap` service clones this repository at startup and publishes `catalog/` into Couchbase. By default, it uses:

   ```env
   CATALOG_GIT_URL=https://github.com/mminichino/couchbase-agent-memory-demo.git
   CATALOG_GIT_REF=main
   ```

   Override these in `.env` if you need another fork/branch. For a private repo, also set `CATALOG_GIT_TOKEN`.

### Run

Start the demo by running:

```shell
docker compose up --build -d
```

Or, using `make`:

```shell
make container-build
```
```shell
make run
```

Once the containers are running, you can access the demo in your browser at `http://localhost:3000`.

### What starts up

Docker Compose brings up:

- **Couchbase Server** with demo flight data (`travel.data.flights`)
- **Agent Memory Server** for session and long-term memory
- **Couchbase MCP Server** for flight schedule lookup and SQL++ access
- **Agent Catalog bootstrap** (`catalog-bootstrap`) which clones a catalog source from GitHub, then indexes, and publishes prompts/tools to Couchbase using `agentc` (installed with `uv`)
- **gRPC chat service** which loads the catalog-managed system prompt, catalog SQL++ tools, memory tools, MCP tools, and Tavily web search
- **Web UI** with a chat pane and a live Agent Catalog tool audit pane

The catalog assets live under `catalog/` in this repository:

- `catalog/prompts/travel_assistant.yaml` — versioned system prompt
- `catalog/tools/flights_by_route.sqlpp` — SQL++ flight lookup tool (MCP remains the primary flight lookup path described in the prompt)

Agent Catalog docs: https://docs.couchbase.com/ai/build/integrate-agent-with-catalog.html
