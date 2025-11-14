# Property Management Agent - MCP Server

An MCP (Model Context Protocol) server that powers an agentic chatbot for property management, acting as a virtual real estate agent.

## Features

- **RAG-backed Property Q&A**: Semantic search across property documents using Milvus vector database and sentence-transformers
- **Tour Scheduling**: Fully integrated with Calendly API for booking, canceling, and rescheduling property tours
- **Document Generation**: Create rental applications, lease agreements, and offer documents
- **Offer Processing**: Submit, track, and process property offers

## Prerequisites

- Python 3.13+
- [UV package manager](https://github.com/astral-sh/uv)
- [Docker](https://www.docker.com/) (for Milvus vector database)
- Calendly account with API access (Professional plan or higher)

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Calendly API

#### Get Your Calendly API Credentials

1. Go to [Calendly Integrations](https://calendly.com/integrations/api_webhooks)
2. Generate a Personal Access Token
3. Copy your API token

#### Get Your User URI and Event Type URI

```bash
# Using your API token, get your user URI
curl -H "Authorization: Bearer YOUR_API_TOKEN" https://api.calendly.com/users/me

# List your event types to find the one for property tours
curl -H "Authorization: Bearer YOUR_API_TOKEN" https://api.calendly.com/event_types?user=YOUR_USER_URI
```

#### Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and add your Calendly credentials:

```env
CALENDLY_API_KEY=your_personal_access_token_here
CALENDLY_USER_URI=https://api.calendly.com/users/XXXXXX
CALENDLY_DEFAULT_EVENT_TYPE_URI=https://api.calendly.com/event_types/XXXXXX
```

### 3. Start Milvus Vector Database

```bash
# Start Milvus using Docker
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest

# Verify Milvus is running
docker ps | grep milvus
```

### 4. Run the Server

```bash
uv run python main.py
```

The server will:
- Load the embedding model (first run downloads ~80MB model)
- Connect to Milvus and create the collection if needed
- Connect to Calendly API (if configured)
- Initialize SQLite offer database
- Start the MCP server on stdio

**Expected Output:**
```
============================================================
Property Management MCP Server
============================================================
Server: Property Management Agent
Protocol: Model Context Protocol (MCP)
Communication: stdin/stdout

Component Status:
  Calendly: ✗ Not configured
  Milvus RAG: ✓ Connected
  Offer DB: ✓ Ready

Registered MCP Tools: 15
============================================================
Server ready. Waiting for MCP client connection...
============================================================
```

The server will then wait for MCP protocol commands on stdin. It runs until:
- Client sends shutdown request
- Process receives SIGINT (Ctrl+C) or SIGTERM
- Fatal error occurs

**Features of the main loop:**
- ✅ Graceful shutdown with resource cleanup
- ✅ Signal handling (SIGINT, SIGTERM)
- ✅ Proper logging to stderr (stdout reserved for MCP protocol)
- ✅ Database connection cleanup on exit
- ✅ Component status reporting

## Deployment Options

This project offers two deployment modes:

### 1. MCP Server (AI Agent Integration)

The MCP server (`main.py`) implements the Model Context Protocol and integrates with AI agent frameworks like Dedalus and Claude Desktop.

### 2. REST API Server (Frontend Integration)

The REST API server (`server.py`) exposes all MCP tools as HTTP/HTTPS endpoints for frontend applications, with WebSocket support for real-time updates.

**Quick Start:**
```bash
# Development (HTTP only)
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Production (HTTPS with SSL)
python server.py
```

**Features:**
- ✅ RESTful endpoints for all 15 tools
- ✅ CORS middleware for frontend access
- ✅ WebSocket support for real-time updates
- ✅ Automatic API documentation (Swagger/ReDoc)
- ✅ HTTPS/SSL support for production
- ✅ Pydantic validation for requests/responses

**Resources:**
- **Full Guide**: [FRONTEND_DEPLOYMENT.md](./FRONTEND_DEPLOYMENT.md) - Complete REST API documentation
- **API Docs**: http://localhost:8000/docs (when server is running)
- **Health Check**: http://localhost:8000/health

## Using with MCP Clients

The MCP server (`main.py`) implements the Model Context Protocol (MCP) and can be used with various AI agent clients:

### Dedalus Integration

This server is designed to work seamlessly with [Dedalus](https://dedalus.ai), an AI agent framework with MCP support.

**Quick Start:**

1. **Verify server is ready:**
   ```bash
   python verify_mcp.py
   ```

2. **Add to Dedalus configuration** (see `mcp_config.json`):
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

3. **Use from Dedalus:**
   ```python
   from dedalus_labs import AsyncDedalus, DedalusRunner
   import asyncio

   async def main():
       client = AsyncDedalus()
       runner = DedalusRunner(client)

       # Example: Search property documents
       response = await runner.run(
           input="What amenities does property PROP-001 have?",
           model="anthropic/claude-3.5-sonnet",
           mcp_servers=["property-management"],
       )

       print(response.final_output)

   asyncio.run(main())
   ```

4. **Run complete examples:**
   ```bash
   python dedalus_client_example.py
   ```

   This runs comprehensive examples showing:
   - Property Q&A with RAG
   - Offer submission and processing
   - Tour scheduling
   - Complete end-to-end workflows

**Resources:**
- **Quick Start:** [QUICKSTART_DEDALUS.md](./QUICKSTART_DEDALUS.md) - Get running in 5 minutes
- **Full Guide:** [DEDALUS_DEPLOYMENT.md](./DEDALUS_DEPLOYMENT.md) - Complete deployment instructions
- **Examples:** [dedalus_client_example.py](./dedalus_client_example.py) - Working code examples

### Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "property-management": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "/path/to/real_estate"
    }
  }
}
```

### Available MCP Tools

Once connected, the following tools are available to the client:

**Property Q&A:**
- `search_property_documents` - Semantic search across property documents
- `add_property_document` - Add documents to knowledge base
- `delete_property_documents` - Remove property documents
- `get_property_details` - Get property metadata

**Tour Scheduling:**
- `check_tour_availability` - Query available tour slots
- `book_property_tour` - Book a property tour
- `cancel_tour` - Cancel a scheduled tour
- `reschedule_tour` - Reschedule an existing tour

**Offer Processing:**
- `submit_offer` - Submit a property offer
- `get_offer_status` - Check offer status
- `process_offer_response` - Accept/reject/counter an offer
- `list_offers` - List offers with filtering
- `get_offer_statistics` - Get offer statistics

## RAG System Integration

The property Q&A system uses Retrieval-Augmented Generation (RAG) with Milvus vector database for semantic search.

### Available Tools

#### `add_property_document`
Ingest a document into the RAG knowledge base.

**Parameters:**
- `property_id`: Property identifier
- `document_name`: Document title (e.g., "Amenities List", "Floor Plan")
- `text`: Full document text content

**Example:**
```python
add_property_document(
    property_id="PROP-001",
    document_name="Property Description",
    text="This beautiful 2-bedroom apartment features..."
)
```

**Returns:**
```json
{
    "success": true,
    "property_id": "PROP-001",
    "document_name": "Property Description",
    "chunks_inserted": 3,
    "insert_count": 3
}
```

#### `search_property_documents`
Search property documents using semantic search.

**Parameters:**
- `query`: Search question or query
- `property_id`: Optional property filter
- `limit`: Max results (default: 5)

**Example:**
```python
search_property_documents(
    query="What amenities are included?",
    property_id="PROP-001"
)
```

**Returns:**
```json
{
    "query": "What amenities are included?",
    "property_id": "PROP-001",
    "num_results": 3,
    "results": [
        {
            "text": "...amenities include pool, gym, parking...",
            "document_name": "Amenities List",
            "chunk_index": 0,
            "score": 0.89
        }
    ],
    "context": "Aggregated text from all relevant chunks",
    "answer": "Found 3 relevant document sections..."
}
```

#### `delete_property_documents`
Remove all documents for a property.

**Parameters:**
- `property_id`: Property identifier

**Returns:**
```json
{
    "success": true,
    "property_id": "PROP-001",
    "deleted_count": 15
}
```

### How RAG Works

1. **Document Ingestion**:
   - Text is split into 512-character chunks with 50-character overlap
   - Chunks break at sentence boundaries when possible
   - Each chunk is embedded using sentence-transformers (384-dimensional vectors)
   - Embeddings are stored in Milvus with metadata (property_id, document_name, chunk_index)

2. **Search**:
   - Query is embedded using the same model
   - Milvus performs cosine similarity search
   - Results are ranked by similarity score
   - Optional filtering by property_id

3. **Configuration**:
   - Default model: `all-MiniLM-L6-v2` (fast, good quality)
   - Alternative: `all-mpnet-base-v2` (better quality, slower, 768-dim)
   - Configure in `.env`: `EMBEDDING_MODEL=all-mpnet-base-v2`

### Troubleshooting RAG

**"Milvus is not connected" Error:**
1. Ensure Milvus container is running: `docker ps | grep milvus`
2. Check Milvus logs: `docker logs milvus-standalone`
3. Verify port 19530 is accessible

**"No relevant documents found":**
1. Add documents first using `add_property_document`
2. Verify documents were added successfully
3. Try broader search queries

**Embedding model download slow:**
- First run downloads model from HuggingFace (~80MB)
- Subsequent runs use cached model
- Model location: `~/.cache/huggingface/`

## Calendly Integration

The tour scheduling tools are fully integrated with Calendly's API:

### Available Tools

#### `check_tour_availability`
Query available tour slots within a date range (max 7 days).

**Parameters:**
- `property_id`: Property identifier
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)

**Returns:** List of available time slots with ISO datetime strings

#### `book_property_tour`
Book a property tour by creating a Calendly event.

**Parameters:**
- `property_id`: Property identifier
- `iso_datetime`: Tour datetime (from check_tour_availability)
- `visitor_name`: Full name of visitor
- `visitor_email`: Email address
- `visitor_phone`: Phone number

**Returns:** Booking confirmation with Calendly event UUID

#### `cancel_tour`
Cancel a scheduled tour.

**Parameters:**
- `booking_id`: Calendly event UUID
- `reason`: Optional cancellation reason

**Returns:** Cancellation confirmation

#### `reschedule_tour`
Reschedule a tour (cancels old event and creates new one).

**Parameters:**
- `booking_id`: Original Calendly event UUID
- `property_id`: Property identifier
- `new_iso_datetime`: New tour datetime
- `visitor_name`: Full name
- `visitor_email`: Email address
- `visitor_phone`: Phone number
- `reschedule_reason`: Optional reason

**Returns:** New booking details with old and new booking IDs

### Important Notes

- Calendly automatically sends confirmation and cancellation emails to invitees
- The API requires a Professional plan or higher
- Date range queries are limited to 7 days maximum
- Rescheduling is implemented as cancel + rebook (Calendly API limitation)
- All tools return detailed error messages if Calendly is not configured

## Development

### Project Structure

```
real_estate/
   main.py              # MCP server with CalendlyClient and tools
   .env                 # Environment configuration (create from .env.example)
   .env.example         # Example environment file
   pyproject.toml       # Python dependencies
   CLAUDE.md           # Claude Code documentation
   README.md           # This file
```

### Architecture

- **CalendlyClient** (main.py:20-159): Async HTTP client for Calendly API
- **Tour Scheduling Tools** (main.py:217-489): MCP tools using CalendlyClient
- All tools use FastMCP decorators and return structured dictionaries

## Troubleshooting

### "Calendly is not configured" Error

Make sure you have:
1. Created a `.env` file from `.env.example`
2. Added your `CALENDLY_API_KEY`
3. Set both `CALENDLY_USER_URI` and `CALENDLY_DEFAULT_EVENT_TYPE_URI`

### API Authentication Errors

- Verify your Personal Access Token is valid
- Check that your Calendly account has a Professional plan or higher
- Ensure the token has not expired

### No Available Time Slots

- Check that your Calendly event type has availability set
- Verify the event type URI is correct
- Ensure you're querying within a 7-day window

## Offer Processing

The offer management system uses SQLite for storing and tracking property offers with full CRUD operations.

### Available Tools

#### `submit_offer`
Submit a new offer on a property.

**Parameters:**
- `property_id`: Property identifier
- `buyer_name`: Full name of the buyer
- `buyer_email`: Email address
- `buyer_phone`: Phone number
- `offer_price`: Offered purchase price (must be > 0)
- `contingencies`: List of contingencies (e.g., ["inspection", "financing", "appraisal"])
- `closing_date`: Proposed closing date (ISO format: YYYY-MM-DD)
- `additional_terms`: Optional dict with additional terms

**Example:**
```python
submit_offer(
    property_id="PROP-001",
    buyer_name="Jane Smith",
    buyer_email="jane@example.com",
    buyer_phone="555-9876",
    offer_price=525000.00,
    contingencies=["inspection", "financing"],
    closing_date="2025-12-31",
    additional_terms={"earnest_money": 10000}
)
```

**Returns:**
```json
{
    "success": true,
    "message": "Offer submitted successfully",
    "offer": {
        "offer_id": "OFFER-20251114-A1B2C3D4",
        "property_id": "PROP-001",
        "buyer_name": "Jane Smith",
        "offer_price": 525000.0,
        "status": "pending_review",
        "contingencies": ["inspection", "financing"],
        "submitted_at": "2025-11-14T15:30:00.123456"
    }
}
```

#### `get_offer_status`
Check the status of a submitted offer.

**Parameters:**
- `offer_id`: The offer ID to check

**Returns:** Full offer details including current status, all buyer info, pricing, and timestamps

#### `process_offer_response`
Accept, reject, or counter an offer.

**Parameters:**
- `offer_id`: The offer ID to respond to
- `response`: Response type ("accept", "reject", or "counter")
- `counter_offer_price`: Required if response is "counter"
- `notes`: Optional notes about the response

**Example:**
```python
process_offer_response(
    offer_id="OFFER-20251114-A1B2C3D4",
    response="counter",
    counter_offer_price=550000.00,
    notes="Counter at asking price"
)
```

**Returns:**
```json
{
    "success": true,
    "message": "Offer countered successfully",
    "offer": {
        "offer_id": "OFFER-20251114-A1B2C3D4",
        "status": "countered",
        "counter_offer_price": 550000.0,
        "response_notes": "Counter at asking price",
        "responded_at": "2025-11-14T16:00:00.123456"
    }
}
```

#### `list_offers`
List all offers for a property with optional status filtering.

**Parameters:**
- `property_id`: Property to list offers for
- `status`: Optional filter ("pending_review", "accepted", "rejected", "countered")

**Returns:** List of offers plus aggregate statistics

#### `get_offer_statistics`
Get aggregate statistics for offers on a property.

**Parameters:**
- `property_id`: Property identifier

**Returns:**
```json
{
    "success": true,
    "property_id": "PROP-001",
    "statistics": {
        "total_offers": 5,
        "pending": 2,
        "accepted": 1,
        "rejected": 1,
        "countered": 1,
        "highest_offer": 575000.0,
        "average_offer": 532000.0
    }
}
```

### Database Details

**Location:** `./data/offers.db` (SQLite)
**Configuration:** Set `OFFERS_DB_PATH` in `.env` to customize

**Offer Statuses:**
- `pending_review`: Initial status when offer is submitted
- `accepted`: Offer has been accepted
- `rejected`: Offer has been declined
- `countered`: Counter-offer has been made

**Offer ID Format:** `OFFER-YYYYMMDD-XXXXXXXX`
- Date stamp for easy chronological sorting
- 8-character UUID for uniqueness

### Workflow Example

```python
# 1. Submit offer
result = submit_offer(
    property_id="PROP-123",
    buyer_name="John Doe",
    buyer_email="john@example.com",
    buyer_phone="555-1234",
    offer_price=500000,
    contingencies=["inspection", "financing"],
    closing_date="2025-12-31"
)
offer_id = result["offer"]["offer_id"]

# 2. Property manager reviews offers
offers = list_offers(property_id="PROP-123", status="pending_review")

# 3. Respond to offer
process_offer_response(
    offer_id=offer_id,
    response="counter",
    counter_offer_price=525000,
    notes="Counter with higher price due to market conditions"
)

# 4. Check statistics
stats = get_offer_statistics(property_id="PROP-123")
print(f"Highest offer: ${stats['statistics']['highest_offer']:,.2f}")
```

## Next Steps

### Completed Features ✅

1. ✅ **RAG System**: Milvus vector database with semantic search
2. ✅ **Tour Scheduling**: Full Calendly API integration
3. ✅ **Offer Processing**: SQLite database with full CRUD operations
4. ✅ **REST API Server**: FastAPI server with HTTPS support for frontend integration
5. ✅ **WebSocket Support**: Real-time updates for property events

### Planned Features

1. **Document Generation**: Template engine and PDF generation for leases and offers
2. **Property Management**: Database for property details and availability
3. **LLM Integration**: Connect to Claude or OpenAI for natural language responses in RAG
4. **Email Notifications**: Automated emails for offer submissions and responses
5. **Authentication**: API key or OAuth authentication for REST API
6. **Rate Limiting**: Prevent API abuse in production

## License

[Your License Here]
