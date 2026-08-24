# couchbase-agent-memory-demo

This demo showcases Couchbase Agent Memory Server, Couchbase MCP Server, and Couchbase Agent Catalog together on the AI Data Plane.

## Running the Demo via Docker Compose

Follow these steps to run the demo locally using Docker Compose.

### Prerequisites

You will need two API keys to run this demo:

1. **OpenAI API Key**: Used for the LLM. You can get one at [platform.openai.com](https://platform.openai.com/).
2. **Tavily API Key**: Used for web search capabilities. You can get one at [tavily.com](https://tavily.com/).

### Setup

1. Create a file named `.env` in the root directory of this project.
2. Add your API keys to the `.env` file as follows:

   ```env
   OPENAI_API_KEY=your_openai_key_here
   TAVILY_API_KEY=your_tavily_key_here
   ```

3. Get and run Agent Memory Server container

   ```shell
   docker load -i agentmemory-server-arm64-v1.0.0.tar
   ```

### Run

Start the demo by running:

```bash
docker compose up --build -d
```

Once the containers are running, you can access the demo in your browser at `http://localhost:3000`.

### What starts up

Docker Compose brings up:

- **Couchbase Server** with demo flight data (`travel.data.flights`)
- **Agent Memory Server** for session and long-term memory
- **Couchbase MCP Server** for flight schedule lookup and SQL++ access
- **Agent Catalog bootstrap** (`catalog-bootstrap`) which indexes and publishes catalog prompts/tools to Couchbase using `agentc` (installed with `uv`)
- **gRPC chat service** which loads the catalog-managed system prompt, catalog SQL++ tools, memory tools, MCP tools, and Tavily web search
- **Web UI** with a chat pane and a live Agent Catalog tool audit pane

The catalog assets live under `catalog/`:

- `catalog/prompts/travel_assistant.yaml` — versioned system prompt
- `catalog/tools/flights_by_route.sqlpp` — SQL++ flight lookup tool (MCP remains the primary flight lookup path described in the prompt)

Agent Catalog docs: https://docs.couchbase.com/ai/build/integrate-agent-with-catalog.html
