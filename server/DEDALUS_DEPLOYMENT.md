# Deploying to Dedalus

This guide explains how to deploy the Property Management Agent MCP server to the Dedalus platform.

## Overview

This MCP server implements the Model Context Protocol and can be consumed by Dedalus for AI agent workflows. The server provides property management tools including:

- RAG-backed property document search (Milvus vector database)
- Tour scheduling (Calendly API integration)
- Offer processing (SQLite database)
- Document management

## Prerequisites

1. **Dedalus Account**: Sign up at [dedalus.ai](https://dedalus.ai)
2. **Python 3.13+**: Ensure Python is installed
3. **UV Package Manager**: Install from [astral.sh/uv](https://astral.sh/uv)
4. **Dependencies**: Run `uv sync` to install all requirements

## Quick Start

### 1. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required for tour scheduling
CALENDLY_API_KEY=your_calendly_token
CALENDLY_USER_URI=https://api.calendly.com/users/YOUR_USER_ID
CALENDLY_DEFAULT_EVENT_TYPE_URI=https://api.calendly.com/event_types/YOUR_EVENT_TYPE

# Optional - use defaults if running locally
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=property_documents
EMBEDDING_MODEL=all-MiniLM-L6-v2
OFFERS_DB_PATH=./data/offers.db
```

### 2. Start Required Services

**Start Milvus (for RAG features):**
```bash
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest
```

**Verify services:**
```bash
docker ps | grep milvus  # Should show running container
```

### 3. Test the MCP Server Locally

```bash
# Test server starts correctly
uv run python main.py
```

The server should start and wait for MCP commands on stdin. Press Ctrl+C to stop.

### 4. Add to Dedalus Configuration

**Option A: Using Dedalus CLI**

If Dedalus provides a CLI for adding MCP servers:

```bash
dedalus mcp add property-management \
  --command "uv" \
  --args "run,python,main.py" \
  --cwd "/path/to/real_estate"
```

**Option B: Manual Configuration**

Add to your Dedalus MCP servers configuration (location depends on Dedalus setup):

```json
{
  "mcpServers": {
    "property-management": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "/absolute/path/to/real_estate",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

See `mcp_config.json` for a complete example.

### 5. Use from Dedalus

```python
from dedalus_labs import AsyncDedalus, DedalusRunner
import asyncio

async def main():
    client = AsyncDedalus()
    runner = DedalusRunner(client)

    # Example: Search property documents
    response = await runner.run(
        input="What amenities does the property at 123 Main St have? Check the property documents.",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )

    print(response.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Available Tools

Once deployed, the following MCP tools are available:

### Property Q&A (RAG)
- `search_property_documents` - Semantic search across property docs
- `add_property_document` - Add documents to knowledge base
- `delete_property_documents` - Remove property docs
- `get_property_details` - Get property metadata

### Tour Scheduling (Calendly)
- `check_tour_availability` - Query available tour slots
- `book_property_tour` - Book a property tour
- `cancel_tour` - Cancel scheduled tour
- `reschedule_tour` - Reschedule existing tour

### Offer Processing (SQLite)
- `submit_offer` - Submit property offer
- `get_offer_status` - Check offer status
- `process_offer_response` - Accept/reject/counter offer
- `list_offers` - List offers with filtering
- `get_offer_statistics` - Get offer statistics

## Example Workflows

### 1. Property Question Answering

```python
# First, add property documents (run once)
response = await runner.run(
    input="""Add this property document:
    Property ID: PROP-001
    Document: Amenities List
    Content: This luxury apartment features a rooftop pool, 24/7 concierge,
    fitness center, parking garage, and pet-friendly policies.""",
    model="anthropic/claude-3-5-sonnet",
    mcp_servers=["property-management"],
)

# Then query the documents
response = await runner.run(
    input="Does property PROP-001 allow pets?",
    model="anthropic/claude-3-5-sonnet",
    mcp_servers=["property-management"],
)
```

### 2. Schedule Property Tour

```python
response = await runner.run(
    input="""Check tour availability for property PROP-001
    from 2025-12-01 to 2025-12-07, then book a tour for
    John Doe (john@example.com, 555-1234) at a convenient time.""",
    model="anthropic/claude-3-5-sonnet",
    mcp_servers=["property-management"],
)
```

### 3. Process Offer

```python
response = await runner.run(
    input="""Submit an offer for property PROP-001:
    - Buyer: Jane Smith
    - Email: jane@example.com
    - Phone: 555-9876
    - Offer: $525,000
    - Contingencies: inspection, financing
    - Closing: 2025-12-31""",
    model="anthropic/claude-3-5-sonnet",
    mcp_servers=["property-management"],
)
```

## Deployment Checklist

- [ ] Environment variables configured in `.env`
- [ ] Milvus running (if using RAG features)
- [ ] Calendly API credentials set (if using tour scheduling)
- [ ] Dependencies installed (`uv sync`)
- [ ] Server tested locally (`uv run python main.py`)
- [ ] MCP configuration added to Dedalus
- [ ] Server registered with correct absolute path
- [ ] Test tool invocation from Dedalus client

## Troubleshooting

### Server Not Starting

**Check logs:**
```bash
uv run python main.py 2>&1 | tee server.log
```

**Common issues:**
- Missing dependencies: Run `uv sync`
- Python version: Requires 3.13+
- Environment variables: Check `.env` file exists

### Tools Not Available

**Verify server registration:**
```bash
# Test the server responds to MCP protocol
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | uv run python main.py
```

Should return MCP initialization response.

### RAG Features Not Working

**Check Milvus:**
```bash
docker ps | grep milvus
docker logs milvus-standalone
```

**Fallback:** RAG features gracefully degrade if Milvus is unavailable. The server will still work for tour scheduling and offer processing.

### Calendly Integration Issues

**Verify credentials:**
- Check `CALENDLY_API_KEY` is set
- Verify `CALENDLY_USER_URI` format
- Confirm `CALENDLY_DEFAULT_EVENT_TYPE_URI` exists
- Test API token: `curl -H "Authorization: Bearer $CALENDLY_API_KEY" https://api.calendly.com/users/me`

## Production Deployment

For production deployment with Dedalus:

1. **Use absolute paths** in MCP configuration
2. **Set up proper logging** (server logs to stderr)
3. **Configure health checks** (server responds to MCP ping)
4. **Secure credentials** (use environment variables, not hardcoded)
5. **Monitor resource usage** (Milvus + SQLite + embedding model)
6. **Set up backups** for SQLite database (`./data/offers.db`)

## Security Considerations

- Store Calendly API key securely (environment variable or secrets manager)
- Validate all input in tool functions (already implemented)
- Use HTTPS for Calendly API calls (handled by httpx)
- Protect SQLite database file permissions
- Consider rate limiting for API calls
- Audit offer submissions and modifications

## Performance Notes

- **Cold start:** ~2-5 seconds (embedding model loading)
- **Warm requests:** <100ms per tool call
- **RAG search:** ~200-500ms (Milvus query + embedding)
- **Calendly API:** ~500-1000ms (external API)
- **SQLite operations:** <10ms (local database)

## Support

For issues related to:
- **This MCP server:** Check README.md and CLAUDE.md
- **Dedalus platform:** Contact Dedalus support
- **Calendly API:** See https://developer.calendly.com
- **Milvus:** See https://milvus.io/docs

## Version History

- **0.1.0** (2025-11-14): Initial release
  - RAG system with Milvus
  - Calendly tour scheduling
  - SQLite offer management
  - FastMCP implementation
