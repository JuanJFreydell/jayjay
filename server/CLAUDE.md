# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based MCP (Model Context Protocol) server that powers an agentic chatbot for property management. The chatbot acts as a virtual real estate agent, handling tenant/buyer interactions on behalf of a property management company.

### Core Capabilities

The MCP server provides four main groups of tools:

1. **Property Q&A (RAG)**: Retrieval-augmented generation backed by a document database to answer questions about properties
2. **Tour Scheduling**: Calendar integration to schedule and book property tours
3. **Document Generation**: Create required documents for the application review and offer process
4. **Offer Processing**: Receive and process offers on properties

## Development Environment

- **Python Version**: 3.13+
- **Package Manager**: uv (UV package manager is configured via uv.lock)
- **Dependencies**: httpx, mcp[cli], milvus, python-dotenv

## Essential Commands

### Setup and Installation
```bash
uv sync                    # Install dependencies
cp .env.example .env       # Create environment file
# Edit .env and add your Calendly API credentials
```

### Running the Application
```bash
python main.py             # Run the main application
uv run main.py            # Run via uv
```

### Configuration
The application requires environment variables to be set in a `.env` file:

**Calendly API:**
- `CALENDLY_API_KEY`: Personal access token from Calendly
- `CALENDLY_USER_URI`: Your Calendly user URI (format: https://api.calendly.com/users/XXXXXX)
- `CALENDLY_DEFAULT_EVENT_TYPE_URI`: Default event type URI for property tours

**Milvus Vector Database:**
- `MILVUS_HOST`: Milvus server host (default: localhost)
- `MILVUS_PORT`: Milvus server port (default: 19530)
- `MILVUS_COLLECTION_NAME`: Collection name (default: property_documents)

**Embedding Model:**
- `EMBEDDING_MODEL`: Sentence transformer model name (default: all-MiniLM-L6-v2)

### MCP Server
The project uses FastMCP from the `mcp.server.fastmcp` module. The server is initialized as:

```python
mcp = FastMCP("Property Management Agent")
```

**Running the Server:**
```bash
uv run python main.py  # Starts MCP server on stdio
```

**Main Loop Features (main.py:1382-1484):**
- Signal handling for graceful shutdown (SIGINT, SIGTERM)
- Resource cleanup on exit (database connections)
- Component status reporting on startup
- Logging to stderr (stdout reserved for MCP protocol)
- Error handling and recovery
- Automatic database connection management

**Server Lifecycle:**
1. Load environment variables from `.env`
2. Initialize components (Calendly, Milvus, SQLite)
3. Register signal handlers for cleanup
4. Print startup banner with component status
5. Run FastMCP server (blocks, handles MCP protocol on stdin/stdout)
6. On shutdown: close database connections, cleanup resources

The server implements the Model Context Protocol and can be used with:
- **Dedalus**: AI agent framework with MCP support
- **Claude Desktop**: Anthropic's desktop app
- **Other MCP Clients**: Any application supporting the MCP protocol

**Configuration Example (mcp_config.json):**
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

**Testing the Server:**
```bash
# Verify server setup
python verify_mcp.py

# Run Dedalus client examples
python dedalus_client_example.py
```

### REST API Server (server.py)

In addition to the MCP server, the project includes a FastAPI REST API server that exposes all MCP tools as HTTP/HTTPS endpoints for frontend integration.

**Running the REST API Server:**
```bash
# Development (HTTP only)
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Production (HTTPS with SSL)
python server.py
```

**Key Features:**
- All 15 MCP tools exposed as REST endpoints
- CORS middleware for cross-origin requests
- WebSocket endpoint (`/ws`) for real-time updates
- Automatic API documentation (Swagger UI at `/docs`, ReDoc at `/redoc`)
- Pydantic models for request/response validation
- HTTPS/SSL support via environment configuration
- Health check endpoint (`/health`)

**Server Structure:**
- **Startup/Shutdown**: Lifespan context manager for resource management
- **Endpoints**: Organized by category (property, tours, offers, documents)
- **WebSocket Manager**: Broadcasts events to all connected clients
- **Error Handling**: Standard HTTP status codes with detailed error messages

**Configuration (via .env):**
- `SERVER_HOST`: Host to bind to (default: 0.0.0.0)
- `SERVER_PORT`: Port to listen on (default: 8000)
- `SSL_KEYFILE`: Path to SSL private key for HTTPS (optional)
- `SSL_CERTFILE`: Path to SSL certificate for HTTPS (optional)

**API Endpoints:**
- Property Q&A: `/api/property/search`, `/api/property/add-document`, `/api/property/delete-documents`, `/api/property/details`
- Tours: `/api/tours/check-availability`, `/api/tours/book`, `/api/tours/cancel`, `/api/tours/reschedule`
- Offers: `/api/offers/submit`, `/api/offers/status`, `/api/offers/respond`, `/api/offers/list`, `/api/offers/statistics`
- Documents: `/api/documents/rental-application`, `/api/documents/lease-agreement` (stubs)
- WebSocket: `ws://localhost:8000/ws` (or `wss://` for HTTPS)
- Health: `GET /health`

**WebSocket Events:**
The server broadcasts these events to all connected WebSocket clients:
- `connected` - Client connected successfully
- `document_added` - New document added to property
- `documents_deleted` - Documents removed from property
- `tour_booked` - New tour scheduled
- `tour_cancelled` - Tour cancelled
- `tour_rescheduled` - Tour rescheduled to new time
- `offer_submitted` - New offer submitted
- `offer_response_processed` - Offer accepted/rejected/countered

**Documentation:**
- Full deployment guide: `FRONTEND_DEPLOYMENT.md`
- Interactive API docs: http://localhost:8000/docs (when server is running)
- ReDoc documentation: http://localhost:8000/redoc

## Architecture

The MCP server is implemented in `main.py` and organized into four main functional groups:

### 1. RAG-Backed Property Q&A (Lines 174-568) - ✅ Milvus Integration Complete
Fully integrated vector database RAG system for property document search:

- **MilvusRAGClient class (Lines 174-426)**: Complete RAG implementation
  - `chunk_text()`: Intelligent text chunking with sentence boundary detection (512 chars, 50 char overlap)
  - `add_document()`: Embeds and stores documents in Milvus vector database
  - `search()`: Semantic search using cosine similarity
  - `delete_property_documents()`: Remove all docs for a property
  - **Embedding Model**: sentence-transformers (default: all-MiniLM-L6-v2, 384 dimensions)
  - **Vector DB**: Milvus with AUTOINDEX and COSINE similarity

- **MCP Tools**:
  - `search_property_documents(query, property_id?, limit)`: Semantic search across property docs
  - `add_property_document(property_id, document_name, text)`: Ingest documents into RAG system
  - `delete_property_documents(property_id)`: Remove property documentation
  - `get_property_details(property_id)`: Get property metadata (placeholder for future DB integration)

**Implementation Details**:
- Text chunking: 512 characters with 50 character overlap, breaks at sentence boundaries
- Embeddings: sentence-transformers with configurable model (all-MiniLM-L6-v2 or all-mpnet-base-v2)
- Vector storage: Milvus collection with fields: id, embedding, text, property_id, document_name, chunk_index
- Search: Cosine similarity with optional property_id filtering
- Returns: Ranked results with similarity scores and aggregated context

**Setup Requirements**:
- Milvus running on localhost:19530 (or configured host/port)
- Start Milvus: `docker run -d -p 19530:19530 milvusdb/milvus:latest`
- Embedding model auto-downloads on first run (~80MB for all-MiniLM-L6-v2)

### 2. Tour Scheduling (Lines 217-489) - ✅ Calendly Integration Complete
Fully integrated with Calendly API for tour scheduling:

- **CalendlyClient class (Lines 20-159)**: Async client for Calendly API interactions
  - `get_event_type_available_times()`: Fetch available time slots from Calendly
  - `create_scheduled_event()`: Create new bookings via Calendly
  - `cancel_scheduled_event()`: Cancel existing events
  - `get_scheduled_event()`: Retrieve event details

- **MCP Tools**:
  - `check_tour_availability()`: Queries Calendly for available slots (max 7-day range)
  - `book_property_tour()`: Creates Calendly event with invitee details
  - `cancel_tour()`: Cancels event via Calendly API
  - `reschedule_tour()`: Cancels old event and creates new one (Calendly has no native reschedule)

**Implementation Notes**:
- All tour tools are async and use the CalendlyClient
- Requires valid Calendly API credentials in `.env` file
- Returns detailed error messages if Calendly is not configured
- Date/time handling uses ISO 8601 format for API calls
- Calendly automatically sends confirmation/cancellation emails to invitees
- Reschedule is implemented as cancel + rebook (Calendly API limitation)

### 3. Document Generation (Lines 166-250)
- `generate_rental_application()`: Create rental application documents
- `generate_lease_agreement()`: Generate lease agreements with terms
- `generate_offer_document()`: Create purchase offer documents

**TODO**: Implement document templates, PDF generation, document storage

### 4. Offer Processing (Lines 442-690, 1144-1374) - ✅ SQLite Implementation Complete
Complete offer management system with SQLite database:

- **OfferDatabase class (Lines 442-690)**: Full CRUD operations for offers
  - `create_offer()`: Store new offers with buyer details, price, contingencies
  - `get_offer()`: Retrieve offer by ID
  - `update_offer_status()`: Process responses (accept/reject/counter)
  - `list_offers()`: Query offers with property_id and status filters
  - `get_offer_stats()`: Calculate statistics (total, by status, price ranges)
  - `delete_offer()`: Remove offers from database
  - **Database**: SQLite with indexed schema (property_id, status, submitted_at)

- **MCP Tools**:
  - `submit_offer(property_id, buyer_name, buyer_email, buyer_phone, offer_price, contingencies, closing_date, additional_terms?)`: Submit new offer
  - `get_offer_status(offer_id)`: Get current offer details and status
  - `process_offer_response(offer_id, response, counter_offer_price?, notes?)`: Accept, reject, or counter
  - `list_offers(property_id, status?)`: List all offers with statistics
  - `get_offer_statistics(property_id)`: Get aggregate statistics for a property

**Database Schema**:
- Fields: offer_id (PK), property_id, buyer details, pricing, contingencies, status, timestamps
- Statuses: pending_review, accepted, rejected, countered
- Indexes on property_id, status, submitted_at for fast queries
- JSON storage for contingencies and additional_terms
- Offer IDs: Format OFFER-YYYYMMDD-XXXXXXXX (date + UUID)

**Implementation Details**:
- Input validation: email format, positive prices, valid dates
- Automatic timestamps: submitted_at, last_updated, responded_at
- Counter-offer tracking with pricing and notes
- Statistics: total offers, by status, highest/average prices
- SQLite storage in ./data/offers.db (configurable via OFFERS_DB_PATH)
- Thread-safe with check_same_thread=False for MCP server usage

### Design Patterns
- All tools use the `@mcp.tool()` decorator from FastMCP
- Date formats follow ISO 8601 (YYYY-MM-DD)
- All tools return structured dictionaries or lists for consistent response handling
- TODOs mark integration points for external services (databases, calendars, document generation)
