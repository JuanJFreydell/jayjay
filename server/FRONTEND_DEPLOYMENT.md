# Frontend Deployment Guide - REST API Server

This guide explains how to deploy and use the Property Management REST API server for frontend applications.

## Overview

The `server.py` file provides a FastAPI REST API wrapper around the MCP server tools, making them accessible to frontend applications via HTTP/HTTPS. This allows you to build web, mobile, or desktop frontends that interact with the property management system.

## Architecture

```
Frontend (React/Vue/Angular/etc)
    ↓ HTTP/HTTPS + WebSocket
REST API Server (server.py) - Port 8000
    ↓ Direct function calls
MCP Server Components (main.py)
    ↓
External Services (Calendly, Milvus, SQLite)
```

## Quick Start

### 1. Prerequisites

- Python 3.13+
- UV package manager installed
- Dependencies installed: `uv sync`
- Milvus running (for RAG features): `docker run -d -p 19530:19530 milvusdb/milvus:latest`
- Optional: Calendly API configured (for tour scheduling)

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Calendly (optional)
CALENDLY_API_KEY=your_personal_access_token_here
CALENDLY_USER_URI=https://api.calendly.com/users/XXXXXX
CALENDLY_DEFAULT_EVENT_TYPE_URI=https://api.calendly.com/event_types/XXXXXX

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# SSL (for HTTPS)
SSL_KEYFILE=path/to/key.pem
SSL_CERTFILE=path/to/cert.pem
```

### 3. Generate SSL Certificates (for HTTPS)

For production deployment with HTTPS:

```bash
# Self-signed certificate (development/testing)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# For production, use certificates from a CA like Let's Encrypt
```

### 4. Start the Server

**Development (HTTP only):**
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Production (HTTPS with SSL):**
```bash
# Set SSL paths in .env, then run:
python server.py
```

**Using uvicorn directly with SSL:**
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### 5. Verify Server is Running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "calendly": true,
    "milvus_rag": true,
    "offer_db": true
  },
  "timestamp": "2025-11-14T12:00:00.000000"
}
```

## API Endpoints

All endpoints return JSON responses. Base URL: `http://localhost:8000` (or `https://` if SSL configured)

### Health Check

**GET** `/health`

Check server health and component status.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "calendly": true,
    "milvus_rag": true,
    "offer_db": true
  },
  "timestamp": "2025-11-14T12:00:00.000000"
}
```

### Property Q&A

#### Search Documents
**POST** `/api/property/search`

Search property documents using semantic search.

**Request:**
```json
{
  "query": "Does it have a backyard?",
  "property_id": "PROP-001",
  "limit": 5
}
```

**Response:**
```json
{
  "query": "Does it have a backyard?",
  "property_id": "PROP-001",
  "num_results": 3,
  "results": [
    {
      "text": "Large fenced backyard with deck...",
      "document_name": "Property Features",
      "chunk_index": 0,
      "score": 0.89
    }
  ],
  "context": "Aggregated text from all results...",
  "answer": "Found 3 relevant document sections."
}
```

#### Add Document
**POST** `/api/property/add-document`

Add a document to the property knowledge base.

**Request:**
```json
{
  "property_id": "PROP-001",
  "document_name": "Property Description",
  "text": "Beautiful 2-bedroom apartment with modern kitchen..."
}
```

**Response:**
```json
{
  "success": true,
  "property_id": "PROP-001",
  "document_name": "Property Description",
  "chunks_inserted": 3,
  "insert_count": 3
}
```

#### Delete Documents
**POST** `/api/property/delete-documents`

Delete all documents for a property.

**Request:**
```json
{
  "property_id": "PROP-001"
}
```

**Response:**
```json
{
  "success": true,
  "property_id": "PROP-001",
  "deleted_count": 15
}
```

#### Get Property Details
**POST** `/api/property/details`

Get property metadata and document count.

**Request:**
```json
{
  "property_id": "PROP-001"
}
```

**Response:**
```json
{
  "property_id": "PROP-001",
  "total_chunks": 15,
  "unique_documents": 3,
  "document_names": ["Property Description", "Amenities", "Location"]
}
```

### Tour Scheduling

#### Check Availability
**POST** `/api/tours/check-availability`

Check available tour slots for a date range.

**Request:**
```json
{
  "property_id": "PROP-001",
  "start_date": "2025-12-01",
  "end_date": "2025-12-07"
}
```

**Response:**
```json
{
  "property_id": "PROP-001",
  "start_date": "2025-12-01",
  "end_date": "2025-12-07",
  "available_slots": [
    {
      "start_time": "2025-12-01T10:00:00Z",
      "status": "available",
      "invitees_remaining": 1
    }
  ],
  "total_slots": 5
}
```

#### Book Tour
**POST** `/api/tours/book`

Book a property tour.

**Request:**
```json
{
  "property_id": "PROP-001",
  "iso_datetime": "2025-12-01T10:00:00Z",
  "visitor_name": "John Doe",
  "visitor_email": "john@example.com",
  "visitor_phone": "555-1234"
}
```

**Response:**
```json
{
  "success": true,
  "property_id": "PROP-001",
  "booking_id": "abc123...",
  "scheduled_time": "2025-12-01T10:00:00Z",
  "visitor_name": "John Doe",
  "visitor_email": "john@example.com",
  "confirmation": "Tour booked successfully. Confirmation email sent to visitor."
}
```

#### Cancel Tour
**POST** `/api/tours/cancel`

Cancel a scheduled tour.

**Request:**
```json
{
  "booking_id": "abc123...",
  "reason": "Visitor is no longer interested"
}
```

**Response:**
```json
{
  "success": true,
  "booking_id": "abc123...",
  "cancellation_reason": "Visitor is no longer interested",
  "message": "Tour cancelled successfully. Cancellation email sent to visitor."
}
```

#### Reschedule Tour
**POST** `/api/tours/reschedule`

Reschedule a tour to a new time.

**Request:**
```json
{
  "booking_id": "abc123...",
  "property_id": "PROP-001",
  "new_iso_datetime": "2025-12-02T14:00:00Z",
  "visitor_name": "John Doe",
  "visitor_email": "john@example.com",
  "visitor_phone": "555-1234",
  "reschedule_reason": "Visitor requested different time"
}
```

**Response:**
```json
{
  "success": true,
  "old_booking_id": "abc123...",
  "new_booking_id": "def456...",
  "new_scheduled_time": "2025-12-02T14:00:00Z",
  "property_id": "PROP-001",
  "visitor_name": "John Doe",
  "message": "Tour rescheduled successfully. Confirmation email sent with new time."
}
```

### Offer Processing

#### Submit Offer
**POST** `/api/offers/submit`

Submit a new offer on a property.

**Request:**
```json
{
  "property_id": "PROP-001",
  "buyer_name": "Jane Smith",
  "buyer_email": "jane@example.com",
  "buyer_phone": "555-9876",
  "offer_price": 525000.00,
  "contingencies": ["inspection", "financing"],
  "closing_date": "2025-12-31",
  "additional_terms": {
    "earnest_money": 10000
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Offer submitted successfully",
  "offer": {
    "offer_id": "OFFER-20251114-A1B2C3D4",
    "property_id": "PROP-001",
    "buyer_name": "Jane Smith",
    "buyer_email": "jane@example.com",
    "buyer_phone": "555-9876",
    "offer_price": 525000.0,
    "status": "pending_review",
    "contingencies": ["inspection", "financing"],
    "closing_date": "2025-12-31",
    "submitted_at": "2025-11-14T15:30:00.123456"
  }
}
```

#### Get Offer Status
**POST** `/api/offers/status`

Check the status of a submitted offer.

**Request:**
```json
{
  "offer_id": "OFFER-20251114-A1B2C3D4"
}
```

**Response:**
```json
{
  "success": true,
  "offer": {
    "offer_id": "OFFER-20251114-A1B2C3D4",
    "property_id": "PROP-001",
    "status": "pending_review",
    "offer_price": 525000.0,
    ...
  }
}
```

#### Process Offer Response
**POST** `/api/offers/respond`

Accept, reject, or counter an offer.

**Request (Counter):**
```json
{
  "offer_id": "OFFER-20251114-A1B2C3D4",
  "response": "counter",
  "counter_offer_price": 550000.00,
  "notes": "Counter at asking price"
}
```

**Request (Accept):**
```json
{
  "offer_id": "OFFER-20251114-A1B2C3D4",
  "response": "accept",
  "notes": "Offer accepted as submitted"
}
```

**Response:**
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

#### List Offers
**POST** `/api/offers/list`

List all offers for a property with optional status filter.

**Request:**
```json
{
  "property_id": "PROP-001",
  "status": "pending_review"
}
```

**Response:**
```json
{
  "success": true,
  "property_id": "PROP-001",
  "status_filter": "pending_review",
  "offers": [
    {
      "offer_id": "OFFER-20251114-A1B2C3D4",
      "buyer_name": "Jane Smith",
      "offer_price": 525000.0,
      "status": "pending_review",
      ...
    }
  ],
  "total_offers": 1,
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

#### Get Offer Statistics
**POST** `/api/offers/statistics`

Get aggregate statistics for offers on a property.

**Request:**
```json
{
  "property_id": "PROP-001"
}
```

**Response:**
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

### Document Generation (Stubs)

#### Generate Rental Application
**POST** `/api/documents/rental-application`

Generate a rental application (not yet implemented).

**Request:**
```json
{
  "property_id": "PROP-001",
  "applicant_name": "John Doe",
  "applicant_email": "john@example.com"
}
```

#### Generate Lease Agreement
**POST** `/api/documents/lease-agreement`

Generate a lease agreement (not yet implemented).

**Request:**
```json
{
  "property_id": "PROP-001",
  "tenant_name": "Jane Smith",
  "lease_start_date": "2026-01-01",
  "lease_term_months": 12,
  "monthly_rent": 2500.00
}
```

## WebSocket Endpoint

**WebSocket** `ws://localhost:8000/ws` (or `wss://` for HTTPS)

Real-time updates for property management events.

### Connecting

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to Property Management API');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received event:', data);

  // Handle different event types
  switch(data.event) {
    case 'connected':
      console.log('WebSocket connected:', data.message);
      break;
    case 'document_added':
      console.log(`Document added to ${data.property_id}`);
      break;
    case 'tour_booked':
      console.log(`Tour booked for ${data.property_id} at ${data.scheduled_time}`);
      break;
    case 'offer_submitted':
      console.log(`New offer ${data.offer_id} submitted`);
      break;
    // ... handle other events
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

### Event Types

The server broadcasts these events to all connected clients:

- `connected` - Initial connection confirmation
- `document_added` - New document added to property
- `documents_deleted` - Documents removed from property
- `tour_booked` - New tour scheduled
- `tour_cancelled` - Tour cancelled
- `tour_rescheduled` - Tour rescheduled to new time
- `offer_submitted` - New offer submitted
- `offer_response_processed` - Offer accepted/rejected/countered

## Frontend Integration Examples

### React Example

```javascript
import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

function PropertySearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const searchProperty = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/property/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          property_id: 'PROP-001',
          limit: 5,
        }),
      });

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask about the property..."
      />
      <button onClick={searchProperty} disabled={loading}>
        {loading ? 'Searching...' : 'Search'}
      </button>

      {results && (
        <div>
          <h3>Results: {results.num_results}</h3>
          {results.results.map((r, i) => (
            <div key={i}>
              <p>{r.text}</p>
              <small>Score: {r.score}</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// WebSocket Hook
function usePropertyUpdates() {
  const [updates, setUpdates] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setUpdates(prev => [...prev, data]);
    };

    return () => ws.close();
  }, []);

  return updates;
}
```

### Vue.js Example

```javascript
<template>
  <div>
    <input v-model="query" placeholder="Ask about the property..." />
    <button @click="searchProperty" :disabled="loading">
      {{ loading ? 'Searching...' : 'Search' }}
    </button>

    <div v-if="results">
      <h3>Results: {{ results.num_results }}</h3>
      <div v-for="(result, i) in results.results" :key="i">
        <p>{{ result.text }}</p>
        <small>Score: {{ result.score }}</small>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      query: '',
      results: null,
      loading: false,
    };
  },
  methods: {
    async searchProperty() {
      this.loading = true;
      try {
        const response = await fetch('http://localhost:8000/api/property/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: this.query,
            property_id: 'PROP-001',
            limit: 5,
          }),
        });

        this.results = await response.json();
      } catch (error) {
        console.error('Search failed:', error);
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
```

### Vanilla JavaScript/Fetch

```javascript
// Search property documents
async function searchProperty(query, propertyId = 'PROP-001') {
  const response = await fetch('http://localhost:8000/api/property/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      property_id: propertyId,
      limit: 5,
    }),
  });

  return await response.json();
}

// Submit an offer
async function submitOffer(offerData) {
  const response = await fetch('http://localhost:8000/api/offers/submit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(offerData),
  });

  return await response.json();
}

// Book a tour
async function bookTour(tourData) {
  const response = await fetch('http://localhost:8000/api/tours/book', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(tourData),
  });

  return await response.json();
}

// Usage
const results = await searchProperty('Does it have a pool?');
console.log('Search results:', results);

const offer = await submitOffer({
  property_id: 'PROP-001',
  buyer_name: 'John Doe',
  buyer_email: 'john@example.com',
  buyer_phone: '555-1234',
  offer_price: 500000,
  contingencies: ['inspection', 'financing'],
  closing_date: '2025-12-31',
});
console.log('Offer submitted:', offer);
```

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad request (validation error)
- `404` - Not found (offer/booking not found)
- `500` - Internal server error
- `503` - Service unavailable (component not configured)

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example Error Handling:**
```javascript
try {
  const response = await fetch(`${API_BASE}/api/property/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(searchData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }

  const data = await response.json();
  return data;
} catch (error) {
  console.error('API error:', error.message);
  // Show error to user
}
```

## CORS Configuration

The server is configured to allow all origins by default:

```python
allow_origins=["*"]
```

**For production**, update `server.py` to restrict to specific origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Production Deployment

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy project files
COPY . .

# Install dependencies
RUN uv sync

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "server.py"]
```

Build and run:
```bash
docker build -t property-management-api .
docker run -p 8000:8000 --env-file .env property-management-api
```

### Using Nginx Reverse Proxy

Configure Nginx to proxy requests to the FastAPI server:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Using systemd (Linux)

Create `/etc/systemd/system/property-api.service`:

```ini
[Unit]
Description=Property Management API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/real_estate
Environment="PATH=/usr/local/bin"
ExecStart=/usr/local/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable property-api
sudo systemctl start property-api
sudo systemctl status property-api
```

## Monitoring and Logging

### Server Logs

The server logs to stderr by default. Redirect to a file:

```bash
python server.py 2>> server.log &
```

### Health Monitoring

Set up a cron job or monitoring service to check `/health`:

```bash
# Check every 5 minutes
*/5 * * * * curl -f http://localhost:8000/health || echo "API is down"
```

### Performance Monitoring

Use tools like:
- **Prometheus** + **Grafana** for metrics
- **Sentry** for error tracking
- **DataDog** or **New Relic** for APM

## Security Considerations

1. **HTTPS in Production**: Always use SSL/TLS certificates
2. **CORS**: Restrict origins to your specific domains
3. **Rate Limiting**: Add rate limiting middleware (e.g., `slowapi`)
4. **Authentication**: Add API key or OAuth authentication for production
5. **Input Validation**: Already handled by Pydantic models
6. **Environment Variables**: Never commit `.env` file to version control

### Adding Authentication (Example)

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Use in endpoints
@app.post("/api/property/search")
async def search_property_documents(
    request: SearchDocumentsRequest,
    api_key: str = Security(verify_api_key)
):
    # ... endpoint code
```

## Troubleshooting

### Server won't start

1. Check if port 8000 is already in use: `lsof -i :8000`
2. Verify dependencies are installed: `uv sync`
3. Check environment variables in `.env`
4. Review server logs for errors

### CORS errors in browser

1. Verify CORS middleware is configured
2. Check browser console for specific error
3. For production, ensure frontend origin is in `allow_origins` list

### WebSocket connection fails

1. Ensure `/ws` endpoint is accessible
2. For HTTPS, use `wss://` protocol
3. Check firewall rules allow WebSocket connections
4. Verify nginx/reverse proxy WebSocket configuration

### Component not available (503 errors)

1. Check Milvus is running: `docker ps | grep milvus`
2. Verify Calendly credentials in `.env`
3. Check SQLite database path exists and is writable
4. Review startup logs for component status

## API Documentation

Once the server is running, FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API testing and complete endpoint documentation.

## Next Steps

1. Build your frontend application using the examples above
2. Set up SSL certificates for HTTPS
3. Configure CORS for your specific frontend domain
4. Add authentication/authorization as needed
5. Deploy to production server
6. Set up monitoring and logging
7. Implement rate limiting
8. Add comprehensive error handling in frontend

## Support

For issues or questions:
- Check server logs: `tail -f server.log`
- Review API documentation: http://localhost:8000/docs
- Test with curl or Postman before integrating frontend
- Verify environment configuration in `.env`
