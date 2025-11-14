# Quick Start: Dedalus Integration

Get up and running with the Property Management MCP server on Dedalus in 5 minutes.

## Prerequisites

- Python 3.13+
- UV package manager
- Dedalus account

## Step 1: Install Dependencies

```bash
cd /path/to/real_estate
uv sync
```

## Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your Calendly API credentials (optional - server works without it)
```

## Step 3: Start Milvus (Optional - for RAG features)

```bash
docker run -d --name milvus-standalone -p 19530:19530 milvusdb/milvus:latest
```

## Step 4: Verify Server

```bash
python verify_mcp.py
```

Expected output:
```
✅ All checks passed!
Server is ready for deployment to Dedalus.
```

## Step 5: Configure Dedalus

Edit your Dedalus MCP configuration to include:

```json
{
  "mcpServers": {
    "property-management": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "/absolute/path/to/real_estate"
    }
  }
}
```

**Important:** Use the absolute path to the `real_estate` directory.

## Step 6: Test from Dedalus

```python
from dedalus_labs import AsyncDedalus, DedalusRunner
import asyncio

async def test_property_server():
    client = AsyncDedalus()
    runner = DedalusRunner(client)

    # Test 1: Add a property document
    response = await runner.run(
        input="""Add a property document using the add_property_document tool:
        - Property ID: TEST-001
        - Document name: Amenities
        - Text: This property features a swimming pool, gym, and parking""",
        model="anthropic/claude-3.5-sonnet",
        mcp_servers=["property-management"],
    )
    print("Test 1:", response.final_output)

    # Test 2: Search the documents
    response = await runner.run(
        input="Does TEST-001 have a gym? Use search_property_documents.",
        model="anthropic/claude-3.5-sonnet",
        mcp_servers=["property-management"],
    )
    print("Test 2:", response.final_output)

asyncio.run(test_property_server())
```

## Available Tools

### Most Useful for Testing

1. **add_property_document** - Add test documents
   ```
   "Add property doc for PROP-001, name 'Features', text 'Modern kitchen, hardwood floors'"
   ```

2. **search_property_documents** - Search documents
   ```
   "Search property PROP-001 for kitchen features"
   ```

3. **submit_offer** - Create test offer
   ```
   "Submit offer for PROP-001: buyer John Doe, email john@test.com, price $500k, closing 2025-12-31"
   ```

4. **list_offers** - View offers
   ```
   "List all offers for PROP-001"
   ```

### Tour Scheduling (Requires Calendly)

Only works if `CALENDLY_API_KEY` is configured:

- **check_tour_availability** - Query available slots
- **book_property_tour** - Schedule tours
- **cancel_tour** - Cancel bookings

## Common Issues

### Server Not Found

**Error:** `MCP server "property-management" not found`

**Fix:** Check the `cwd` path in your Dedalus config is absolute:
```bash
pwd  # Get current directory
# Use this full path in cwd
```

### Tool Execution Errors

**Error:** `Milvus is not connected`

**Fix:** Either start Milvus or ignore (RAG features will be disabled but other tools work)

**Error:** `Calendly is not configured`

**Fix:** Set `CALENDLY_API_KEY` in `.env` or skip tour scheduling tools

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'X'`

**Fix:** Run `uv sync` in the project directory

## Next Steps

Once working:

1. **Add real property data** - Use `add_property_document` with actual property descriptions
2. **Configure Calendly** - Set up API access for tour scheduling
3. **Test workflows** - Try complex multi-step tasks
4. **Production deployment** - See [DEDALUS_DEPLOYMENT.md](./DEDALUS_DEPLOYMENT.md)

## Support

- **Server issues:** Check README.md and CLAUDE.md
- **Dedalus questions:** Contact Dedalus support
- **Bug reports:** Create an issue in the repository

## Example Workflows

### Complete Property Workflow

```python
async def property_workflow():
    client = AsyncDedalus()
    runner = DedalusRunner(client)

    # 1. Add property information
    await runner.run(
        input="""Add property documents for PROP-123:
        Document 1 - Description: Beautiful 2BR apartment, hardwood floors, modern kitchen
        Document 2 - Amenities: Pool, gym, parking, pet-friendly
        Document 3 - Location: Downtown, near transit, walkable""",
        model="anthropic/claude-3.5-sonnet",
        mcp_servers=["property-management"],
    )

    # 2. Answer questions
    response = await runner.run(
        input="What are the key features of PROP-123? Is it pet-friendly?",
        model="anthropic/claude-3.5-sonnet",
        mcp_servers=["property-management"],
    )
    print(response.final_output)

    # 3. Process an offer
    await runner.run(
        input="""Submit and accept an offer for PROP-123:
        Buyer: Alice Johnson, alice@example.com, 555-1234
        Price: $525,000, contingencies: inspection + financing
        Closing: 2025-12-31
        Then accept this offer.""",
        model="anthropic/claude-3.5-sonnet",
        mcp_servers=["property-management"],
    )

asyncio.run(property_workflow())
```

This demonstrates the complete agent workflow using the Property Management MCP server!
