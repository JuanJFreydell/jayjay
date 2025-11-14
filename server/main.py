import os
import httpx
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Property Management Agent")


# ============================================================================
# CALENDLY API CLIENT
# ============================================================================


class CalendlyClient:
    """Client for interacting with Calendly API"""

    def __init__(self):
        self.api_key = os.getenv("CALENDLY_API_KEY")
        self.base_url = os.getenv("CALENDLY_API_BASE_URL", "https://api.calendly.com")
        self.user_uri = os.getenv("CALENDLY_USER_URI")
        self.default_event_type_uri = os.getenv("CALENDLY_DEFAULT_EVENT_TYPE_URI")

        if not self.api_key:
            raise ValueError(
                "CALENDLY_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )

    def _get_headers(self) -> dict:
        """Get standard headers for Calendly API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def get_event_type_available_times(
        self, event_type_uri: str, start_time: str, end_time: str
    ) -> list[dict]:
        """
        Get available time slots for an event type.

        Args:
            event_type_uri: URI of the Calendly event type
            start_time: Start of the range (ISO 8601 format)
            end_time: End of the range (ISO 8601 format, max 7 days from start)

        Returns:
            List of available time slots
        """
        url = f"{self.base_url}/event_type_available_times"
        params = {
            "event_type": event_type_uri,
            "start_time": start_time,
            "end_time": end_time,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("collection", [])

    async def create_scheduled_event(
        self,
        event_type_uri: str,
        start_time: str,
        invitee_email: str,
        invitee_name: str,
        invitee_phone: Optional[str] = None,
        additional_notes: Optional[str] = None,
    ) -> dict:
        """
        Create a scheduled event (book an appointment).

        Args:
            event_type_uri: URI of the Calendly event type
            start_time: Start time in ISO 8601 format
            invitee_email: Invitee's email address
            invitee_name: Invitee's full name
            invitee_phone: Optional phone number
            additional_notes: Optional notes about the booking

        Returns:
            Created scheduled event details
        """
        url = f"{self.base_url}/scheduled_events/invitees"

        # Split name into first and last
        name_parts = invitee_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        payload = {
            "event_type": event_type_uri,
            "start_time": start_time,
            "email": invitee_email,
            "first_name": first_name,
            "last_name": last_name,
        }

        if invitee_phone:
            payload["phone_number"] = invitee_phone

        if additional_notes:
            payload["notes"] = additional_notes

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            return response.json()

    async def cancel_scheduled_event(
        self, event_uuid: str, reason: Optional[str] = None
    ) -> dict:
        """
        Cancel a scheduled event.

        Args:
            event_uuid: UUID of the scheduled event to cancel
            reason: Optional cancellation reason

        Returns:
            Cancellation confirmation
        """
        url = f"{self.base_url}/scheduled_events/{event_uuid}/cancellation"

        payload = {}
        if reason:
            payload["reason"] = reason

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            return response.json()

    async def get_scheduled_event(self, event_uuid: str) -> dict:
        """
        Get details of a scheduled event.

        Args:
            event_uuid: UUID of the scheduled event

        Returns:
            Event details
        """
        url = f"{self.base_url}/scheduled_events/{event_uuid}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()


# Initialize Calendly client
try:
    calendly_client = CalendlyClient()
except ValueError as e:
    # If Calendly is not configured, set to None and log warning
    print(f"Warning: Calendly not configured - {e}")
    calendly_client = None


# ============================================================================
# MILVUS RAG CLIENT
# ============================================================================


class MilvusRAGClient:
    """Client for RAG operations using Milvus vector database"""

    def __init__(self):
        from pymilvus import MilvusClient, DataType
        from sentence_transformers import SentenceTransformer

        self.host = os.getenv("MILVUS_HOST", "localhost")
        self.port = int(os.getenv("MILVUS_PORT", "19530"))
        self.collection_name = os.getenv("MILVUS_COLLECTION_NAME", "property_documents")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

        # Initialize embedding model
        print(f"Loading embedding model: {self.embedding_model_name}...")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        print(f"Embedding model loaded. Dimension: {self.embedding_dim}")

        # Initialize Milvus client
        try:
            self.client = MilvusClient(uri=f"http://{self.host}:{self.port}")
            self._ensure_collection_exists()
            print(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            print(f"Warning: Could not connect to Milvus - {e}")
            print(
                "RAG features will be disabled. Start Milvus with: docker run -d -p 19530:19530 milvusdb/milvus:latest"
            )
            self.client = None

    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        from pymilvus import MilvusClient

        if not self.client:
            return

        # Check if collection exists
        collections = self.client.list_collections()
        if self.collection_name in collections:
            print(f"Collection '{self.collection_name}' already exists")
            return

        # Create collection with schema
        schema = MilvusClient.create_schema(
            auto_id=True,
            enable_dynamic_field=True,
        )

        # Add fields
        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
        schema.add_field(
            field_name="embedding",
            datatype=DataType.FLOAT_VECTOR,
            dim=self.embedding_dim,
        )
        schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
        schema.add_field(
            field_name="property_id", datatype=DataType.VARCHAR, max_length=255
        )
        schema.add_field(
            field_name="document_name", datatype=DataType.VARCHAR, max_length=512
        )
        schema.add_field(field_name="chunk_index", datatype=DataType.INT64)

        # Create index parameters
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )

        # Create collection
        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params,
        )
        print(f"Created collection '{self.collection_name}'")

    def chunk_text(
        self, text: str, chunk_size: int = 512, overlap: int = 50
    ) -> list[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(".")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > chunk_size // 2:  # Only break if we're past halfway
                    chunk = chunk[: break_point + 1]
                    end = start + len(chunk)

            chunks.append(chunk.strip())
            start = end - overlap

        return [c for c in chunks if c]  # Filter empty chunks

    def add_document(self, property_id: str, document_name: str, text: str) -> dict:
        """
        Add a document to the vector database.

        Args:
            property_id: Property identifier
            document_name: Name of the document
            text: Document text content

        Returns:
            Result with number of chunks inserted
        """
        if not self.client:
            return {"error": "Milvus is not connected"}

        try:
            # Chunk the text
            chunks = self.chunk_text(text)

            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)

            # Prepare data for insertion
            data = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                data.append(
                    {
                        "embedding": embedding.tolist(),
                        "text": chunk,
                        "property_id": property_id,
                        "document_name": document_name,
                        "chunk_index": idx,
                    }
                )

            # Insert into Milvus
            result = self.client.insert(collection_name=self.collection_name, data=data)

            return {
                "success": True,
                "property_id": property_id,
                "document_name": document_name,
                "chunks_inserted": len(chunks),
                "insert_count": result.get("insert_count", 0),
            }

        except Exception as e:
            return {"error": f"Failed to add document: {str(e)}"}

    def search(
        self, query: str, property_id: Optional[str] = None, limit: int = 5
    ) -> list[dict]:
        """
        Search for relevant document chunks.

        Args:
            query: Search query
            property_id: Optional property ID filter
            limit: Maximum number of results

        Returns:
            List of relevant chunks with metadata
        """
        if not self.client:
            return []

        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(
                [query], show_progress_bar=False
            )[0]

            # Build filter expression
            filter_expr = None
            if property_id:
                filter_expr = f'property_id == "{property_id}"'

            # Search in Milvus
            results = self.client.search(
                collection_name=self.collection_name,
                data=[query_embedding.tolist()],
                filter=filter_expr,
                limit=limit,
                output_fields=["text", "property_id", "document_name", "chunk_index"],
            )

            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append(
                        {
                            "text": hit.get("entity", {}).get("text", ""),
                            "property_id": hit.get("entity", {}).get("property_id", ""),
                            "document_name": hit.get("entity", {}).get(
                                "document_name", ""
                            ),
                            "chunk_index": hit.get("entity", {}).get("chunk_index", 0),
                            "distance": hit.get("distance", 0.0),
                            "score": 1
                            - hit.get(
                                "distance", 1.0
                            ),  # Convert distance to similarity score
                        }
                    )

            return formatted_results

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def delete_property_documents(self, property_id: str) -> dict:
        """
        Delete all documents for a property.

        Args:
            property_id: Property identifier

        Returns:
            Deletion result
        """
        if not self.client:
            return {"error": "Milvus is not connected"}

        try:
            result = self.client.delete(
                collection_name=self.collection_name,
                filter=f'property_id == "{property_id}"',
            )

            return {
                "success": True,
                "property_id": property_id,
                "deleted_count": result.get("delete_count", 0),
            }

        except Exception as e:
            return {"error": f"Failed to delete documents: {str(e)}"}


# Initialize RAG client
try:
    rag_client = MilvusRAGClient()
except Exception as e:
    print(f"Warning: RAG client initialization failed - {e}")
    rag_client = None


# ============================================================================
# OFFER DATABASE CLIENT
# ============================================================================


class OfferDatabase:
    """SQLite database client for managing property offers"""

    def __init__(self, db_path: str = None):
        import sqlite3
        from pathlib import Path

        self.db_path = db_path or os.getenv("OFFERS_DB_PATH", "./data/offers.db")

        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access

        # Create tables
        self._create_tables()
        print(f"Offer database initialized at {self.db_path}")

    def _create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()

        # Offers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                offer_id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                buyer_name TEXT NOT NULL,
                buyer_email TEXT NOT NULL,
                buyer_phone TEXT NOT NULL,
                offer_price REAL NOT NULL,
                contingencies TEXT NOT NULL,
                closing_date TEXT NOT NULL,
                additional_terms TEXT,
                status TEXT NOT NULL DEFAULT 'pending_review',
                counter_offer_price REAL,
                response_notes TEXT,
                submitted_at TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                responded_at TEXT
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_id
            ON offers(property_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON offers(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_submitted_at
            ON offers(submitted_at DESC)
        """)

        self.conn.commit()

    def generate_offer_id(self) -> str:
        """Generate a unique offer ID"""
        import uuid

        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"OFFER-{timestamp}-{unique_id}"

    def create_offer(
        self,
        property_id: str,
        buyer_name: str,
        buyer_email: str,
        buyer_phone: str,
        offer_price: float,
        contingencies: list[str],
        closing_date: str,
        additional_terms: Optional[dict] = None,
    ) -> dict:
        """Create a new offer"""
        import json

        offer_id = self.generate_offer_id()
        now = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO offers (
                offer_id, property_id, buyer_name, buyer_email, buyer_phone,
                offer_price, contingencies, closing_date, additional_terms,
                status, submitted_at, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                offer_id,
                property_id,
                buyer_name,
                buyer_email,
                buyer_phone,
                offer_price,
                json.dumps(contingencies),
                closing_date,
                json.dumps(additional_terms) if additional_terms else None,
                "pending_review",
                now,
                now,
            ),
        )

        self.conn.commit()

        return self.get_offer(offer_id)

    def get_offer(self, offer_id: str) -> Optional[dict]:
        """Get offer by ID"""
        import json

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM offers WHERE offer_id = ?", (offer_id,))
        row = cursor.fetchone()

        if not row:
            return None

        offer = dict(row)

        # Parse JSON fields
        if offer.get("contingencies"):
            offer["contingencies"] = json.loads(offer["contingencies"])
        if offer.get("additional_terms"):
            offer["additional_terms"] = json.loads(offer["additional_terms"])

        return offer

    def update_offer_status(
        self,
        offer_id: str,
        response: str,
        counter_offer_price: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Optional[dict]:
        """Update offer status with response"""
        # Validate response type
        valid_responses = ["accept", "reject", "counter"]
        if response not in valid_responses:
            raise ValueError(f"Invalid response. Must be one of: {valid_responses}")

        # Validate counter offer
        if response == "counter" and not counter_offer_price:
            raise ValueError(
                "counter_offer_price is required when response is 'counter'"
            )

        now = datetime.now().isoformat()
        status_map = {
            "accept": "accepted",
            "reject": "rejected",
            "counter": "countered",
        }
        new_status = status_map[response]

        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE offers
            SET status = ?,
                counter_offer_price = ?,
                response_notes = ?,
                responded_at = ?,
                last_updated = ?
            WHERE offer_id = ?
        """,
            (new_status, counter_offer_price, notes, now, now, offer_id),
        )

        self.conn.commit()

        if cursor.rowcount == 0:
            return None

        return self.get_offer(offer_id)

    def list_offers(self, property_id: str = None, status: str = None) -> list[dict]:
        """List offers with optional filters"""
        import json

        cursor = self.conn.cursor()

        query = "SELECT * FROM offers WHERE 1=1"
        params = []

        if property_id:
            query += " AND property_id = ?"
            params.append(property_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY submitted_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        offers = []
        for row in rows:
            offer = dict(row)
            # Parse JSON fields
            if offer.get("contingencies"):
                offer["contingencies"] = json.loads(offer["contingencies"])
            if offer.get("additional_terms"):
                offer["additional_terms"] = json.loads(offer["additional_terms"])
            offers.append(offer)

        return offers

    def delete_offer(self, offer_id: str) -> bool:
        """Delete an offer"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM offers WHERE offer_id = ?", (offer_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_offer_stats(self, property_id: str) -> dict:
        """Get statistics for offers on a property"""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) as total_offers,
                COUNT(CASE WHEN status = 'pending_review' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'accepted' THEN 1 END) as accepted,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                COUNT(CASE WHEN status = 'countered' THEN 1 END) as countered,
                MAX(offer_price) as highest_offer,
                AVG(offer_price) as average_offer
            FROM offers
            WHERE property_id = ?
        """,
            (property_id,),
        )

        row = cursor.fetchone()
        return dict(row) if row else {}


# Initialize offer database
try:
    offer_db = OfferDatabase()
except Exception as e:
    print(f"Warning: Offer database initialization failed - {e}")
    offer_db = None


# ============================================================================
# 1. RAG-BACKED PROPERTY Q&A TOOLS
# ============================================================================


@mcp.tool()
def search_property_documents(
    query: str, property_id: Optional[str] = None, limit: int = 5
) -> dict:
    """
    Search property documents using RAG to answer questions about properties.

    Args:
        query: The question or search query about the property
        property_id: Optional specific property ID to search within
        limit: Maximum number of relevant chunks to return (default: 5)

    Returns:
        Search results with relevant document chunks and metadata
    """
    if not rag_client or not rag_client.client:
        return {
            "error": "RAG system is not available. Please ensure Milvus is running.",
            "query": query,
            "results": [],
        }

    try:
        # Search for relevant chunks
        results = rag_client.search(query=query, property_id=property_id, limit=limit)

        if not results:
            return {
                "query": query,
                "property_id": property_id,
                "results": [],
                "message": "No relevant documents found. Try adding documents first using add_property_document.",
            }

        # Format response with aggregated context
        context_text = "\n\n".join(
            [
                f"[{r['document_name']} - Chunk {r['chunk_index']}] (Score: {r['score']:.2f})\n{r['text']}"
                for r in results
            ]
        )

        return {
            "query": query,
            "property_id": property_id,
            "num_results": len(results),
            "results": results,
            "context": context_text,
            "answer": f"Found {len(results)} relevant document sections. "
            f"Use the context above to answer questions about the property.",
        }

    except Exception as e:
        return {"error": f"Search failed: {str(e)}", "query": query, "results": []}


@mcp.tool()
def add_property_document(property_id: str, document_name: str, text: str) -> dict:
    """
    Add a document to the property knowledge base for RAG search.

    Args:
        property_id: Unique identifier for the property
        document_name: Name/title of the document (e.g., "Floor Plan", "Amenities List")
        text: The full text content of the document

    Returns:
        Result indicating success and number of chunks created
    """
    if not rag_client or not rag_client.client:
        return {
            "error": "RAG system is not available. Please ensure Milvus is running."
        }

    try:
        result = rag_client.add_document(
            property_id=property_id, document_name=document_name, text=text
        )
        return result

    except Exception as e:
        return {"error": f"Failed to add document: {str(e)}"}


@mcp.tool()
def delete_property_documents(property_id: str) -> dict:
    """
    Delete all documents for a specific property.

    Args:
        property_id: Property identifier

    Returns:
        Deletion result with count of deleted documents
    """
    if not rag_client or not rag_client.client:
        return {
            "error": "RAG system is not available. Please ensure Milvus is running."
        }

    try:
        result = rag_client.delete_property_documents(property_id=property_id)
        return result

    except Exception as e:
        return {"error": f"Failed to delete documents: {str(e)}"}


@mcp.tool()
def get_property_details(property_id: str) -> dict:
    """
    Get detailed information about a specific property.

    Args:
        property_id: The unique identifier for the property

    Returns:
        Property details including address, specs, amenities, pricing
    """
    # TODO: Implement database query for property details
    # For now, this is a placeholder that could integrate with a property database
    return {
        "property_id": property_id,
        "status": "available",
        "details": "Property details would be retrieved from database",
        "note": "Use search_property_documents() to search through property documentation in the RAG system",
    }


# ============================================================================
# 2. TOUR SCHEDULING TOOLS
# ============================================================================


@mcp.tool()
async def check_tour_availability(
    property_id: str, start_date: str, end_date: str
) -> list[dict]:
    """
    Check available tour slots for a property within a date range.

    Args:
        property_id: The property to check availability for
        start_date: Start of date range (ISO format: YYYY-MM-DD)
        end_date: End of date range (ISO format: YYYY-MM-DD)

    Returns:
        List of available time slots with invitee_start_time and status
    """
    if not calendly:
        return [
            {
                "error": "Calendly is not configured. Please set CALENDLY_API_KEY in .env file."
            }
        ]

    try:
        # Convert dates to ISO 8601 datetime format for Calendly
        start_datetime = f"{start_date}T00:00:00Z"
        end_datetime = f"{end_date}T23:59:59Z"

        # Validate date range (Calendly max is 7 days)
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        if (end_dt - start_dt).days > 7:
            end_dt = start_dt + timedelta(days=7)
            end_datetime = f"{end_dt.date()}T23:59:59Z"

        # Get event type URI (you could map property_id to specific event types)
        event_type_uri = calendly.default_event_type_uri

        if not event_type_uri:
            return [
                {
                    "error": "CALENDLY_DEFAULT_EVENT_TYPE_URI not configured in .env file."
                }
            ]

        # Fetch available times from Calendly
        available_times = await calendly.get_event_type_available_times(
            event_type_uri, start_datetime, end_datetime
        )

        # Transform Calendly response to our format
        formatted_times = []
        for slot in available_times:
            if slot.get("status") == "available":
                start_time_str = slot.get("invitee_start_time", "")
                if start_time_str:
                    # Parse ISO datetime to extract date and time
                    slot_dt = datetime.fromisoformat(
                        start_time_str.replace("Z", "+00:00")
                    )
                    formatted_times.append(
                        {
                            "property_id": property_id,
                            "date": slot_dt.date().isoformat(),
                            "time": slot_dt.strftime("%I:%M %p"),
                            "iso_datetime": start_time_str,
                            "status": "available",
                        }
                    )

        return formatted_times

    except httpx.HTTPStatusError as e:
        return [
            {
                "error": f"Calendly API error: {e.response.status_code} - {e.response.text}"
            }
        ]
    except Exception as e:
        return [{"error": f"Error checking availability: {str(e)}"}]


@mcp.tool()
async def book_property_tour(
    property_id: str,
    iso_datetime: str,
    visitor_name: str,
    visitor_email: str,
    visitor_phone: str,
) -> dict:
    """
    Book a property tour for a prospective tenant/buyer.

    Args:
        property_id: The property to tour
        iso_datetime: Tour datetime in ISO format (from check_tour_availability)
        visitor_name: Full name of the visitor
        visitor_email: Email of the visitor
        visitor_phone: Phone number of the visitor

    Returns:
        Booking confirmation details including Calendly event URI
    """
    if not calendly:
        return {
            "error": "Calendly is not configured. Please set CALENDLY_API_KEY in .env file."
        }

    try:
        # Get event type URI
        event_type_uri = calendly.default_event_type_uri

        if not event_type_uri:
            return {
                "error": "CALENDLY_DEFAULT_EVENT_TYPE_URI not configured in .env file."
            }

        # Create the scheduled event via Calendly
        result = await calendly.create_scheduled_event(
            event_type_uri=event_type_uri,
            start_time=iso_datetime,
            invitee_email=visitor_email,
            invitee_name=visitor_name,
            invitee_phone=visitor_phone,
            additional_notes=f"Property tour for property ID: {property_id}",
        )

        # Extract event details from Calendly response
        resource = result.get("resource", {})
        event_uri = resource.get("uri", "")

        # Extract UUID from URI for cancellation/rescheduling
        event_uuid = event_uri.split("/")[-1] if event_uri else None

        # Parse datetime for readable format
        slot_dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))

        return {
            "booking_id": event_uuid,
            "calendly_event_uri": event_uri,
            "property_id": property_id,
            "date": slot_dt.date().isoformat(),
            "time": slot_dt.strftime("%I:%M %p"),
            "visitor_name": visitor_name,
            "visitor_email": visitor_email,
            "visitor_phone": visitor_phone,
            "status": "confirmed",
            "created_at": resource.get("created_at", ""),
        }

    except httpx.HTTPStatusError as e:
        return {
            "error": f"Calendly API error: {e.response.status_code} - {e.response.text}"
        }
    except Exception as e:
        return {"error": f"Error booking tour: {str(e)}"}


@mcp.tool()
async def cancel_tour(booking_id: str, reason: Optional[str] = None) -> dict:
    """
    Cancel a scheduled property tour.

    Args:
        booking_id: The Calendly event UUID (from booking confirmation)
        reason: Optional reason for cancellation

    Returns:
        Cancellation confirmation
    """
    if not calendly:
        return {
            "error": "Calendly is not configured. Please set CALENDLY_API_KEY in .env file."
        }

    try:
        # Cancel the event via Calendly API
        result = await calendly.cancel_scheduled_event(
            event_uuid=booking_id, reason=reason
        )

        return {
            "booking_id": booking_id,
            "status": "cancelled",
            "reason": reason,
            "cancelled_at": datetime.now().isoformat(),
            "calendly_response": result,
        }

    except httpx.HTTPStatusError as e:
        return {
            "error": f"Calendly API error: {e.response.status_code} - {e.response.text}"
        }
    except Exception as e:
        return {"error": f"Error cancelling tour: {str(e)}"}


@mcp.tool()
async def reschedule_tour(
    booking_id: str,
    property_id: str,
    new_iso_datetime: str,
    visitor_name: str,
    visitor_email: str,
    visitor_phone: str,
    reschedule_reason: Optional[str] = None,
) -> dict:
    """
    Reschedule an existing property tour.

    Note: Calendly doesn't have a direct reschedule API. This cancels the old event
    and creates a new one. The invitee will receive cancellation and new booking emails.

    Args:
        booking_id: The original Calendly event UUID to cancel
        property_id: The property ID
        new_iso_datetime: New tour datetime in ISO format
        visitor_name: Full name of the visitor
        visitor_email: Email of the visitor
        visitor_phone: Phone number of the visitor
        reschedule_reason: Optional reason for rescheduling

    Returns:
        New booking details with old and new booking IDs
    """
    if not calendly:
        return {
            "error": "Calendly is not configured. Please set CALENDLY_API_KEY in .env file."
        }

    try:
        # Step 1: Cancel the old event
        cancel_reason = reschedule_reason or "Rescheduling tour to a new time"
        cancel_result = await calendly.cancel_scheduled_event(
            event_uuid=booking_id, reason=cancel_reason
        )

        # Step 2: Create a new booking
        event_type_uri = calendly.default_event_type_uri
        if not event_type_uri:
            return {
                "error": "CALENDLY_DEFAULT_EVENT_TYPE_URI not configured in .env file.",
                "cancelled_booking_id": booking_id,
            }

        book_result = await calendly.create_scheduled_event(
            event_type_uri=event_type_uri,
            start_time=new_iso_datetime,
            invitee_email=visitor_email,
            invitee_name=visitor_name,
            invitee_phone=visitor_phone,
            additional_notes=f"Rescheduled property tour for property ID: {property_id}. Original booking: {booking_id}",
        )

        # Extract new event details
        resource = book_result.get("resource", {})
        new_event_uri = resource.get("uri", "")
        new_event_uuid = new_event_uri.split("/")[-1] if new_event_uri else None

        # Parse datetime for readable format
        slot_dt = datetime.fromisoformat(new_iso_datetime.replace("Z", "+00:00"))

        return {
            "status": "rescheduled",
            "old_booking_id": booking_id,
            "new_booking_id": new_event_uuid,
            "new_calendly_event_uri": new_event_uri,
            "property_id": property_id,
            "new_date": slot_dt.date().isoformat(),
            "new_time": slot_dt.strftime("%I:%M %p"),
            "visitor_name": visitor_name,
            "visitor_email": visitor_email,
            "reschedule_reason": reschedule_reason,
            "rescheduled_at": datetime.now().isoformat(),
        }

    except httpx.HTTPStatusError as e:
        return {
            "error": f"Calendly API error: {e.response.status_code} - {e.response.text}"
        }
    except Exception as e:
        return {"error": f"Error rescheduling tour: {str(e)}"}


# ============================================================================
# 3. FAIR MARKET VALUATION TOOLS
# ============================================================================

# TODO IMPLEMENT THIS


@mcp.tool()
def property_research():
    pass


def market_estimate():
    pass


# ============================================================================
# 4. OFFER PROCESSING TOOLS
# ============================================================================


@mcp.tool()
def submit_offer(
    property_id: str,
    buyer_name: str,
    buyer_email: str,
    buyer_phone: str,
    offer_price: float,
    contingencies: list[str],
    closing_date: str,
    additional_terms: Optional[dict] = None,
) -> dict:
    """
    Submit an offer on a property.

    Args:
        property_id: The property being offered on
        buyer_name: Name of the buyer
        buyer_email: Email of the buyer
        buyer_phone: Phone number of the buyer
        offer_price: Offered purchase price
        contingencies: List of contingencies (e.g., ["inspection", "financing"])
        closing_date: Proposed closing date (ISO format: YYYY-MM-DD)
        additional_terms: Optional additional terms and conditions

    Returns:
        Offer submission confirmation and tracking details
    """
    if not offer_db:
        return {
            "error": "Offer database is not available. Please check database configuration."
        }

    try:
        # Validate inputs
        if offer_price <= 0:
            return {"error": "Offer price must be greater than 0"}

        # Validate email format
        if "@" not in buyer_email:
            return {"error": "Invalid email address"}

        # Validate closing date format
        try:
            datetime.fromisoformat(closing_date)
        except ValueError:
            return {"error": "Invalid closing_date format. Use YYYY-MM-DD"}

        # Create offer in database
        offer = offer_db.create_offer(
            property_id=property_id,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            buyer_phone=buyer_phone,
            offer_price=offer_price,
            contingencies=contingencies,
            closing_date=closing_date,
            additional_terms=additional_terms,
        )

        return {
            "success": True,
            "message": "Offer submitted successfully",
            "offer": offer,
        }

    except Exception as e:
        return {"error": f"Failed to submit offer: {str(e)}"}


@mcp.tool()
def get_offer_status(offer_id: str) -> dict:
    """
    Check the status of a submitted offer.

    Args:
        offer_id: The offer ID to check

    Returns:
        Current offer status and details
    """
    if not offer_db:
        return {
            "error": "Offer database is not available. Please check database configuration."
        }

    try:
        offer = offer_db.get_offer(offer_id)

        if not offer:
            return {"error": f"Offer {offer_id} not found"}

        return {"success": True, "offer": offer}

    except Exception as e:
        return {"error": f"Failed to get offer status: {str(e)}"}


@mcp.tool()
def process_offer_response(
    offer_id: str,
    response: str,
    counter_offer_price: Optional[float] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    Process a response to an offer (accept, reject, or counter).

    Args:
        offer_id: The offer ID being responded to
        response: Response type ("accept", "reject", "counter")
        counter_offer_price: If countering, the counter offer price
        notes: Optional notes or conditions

    Returns:
        Updated offer status
    """
    if not offer_db:
        return {
            "error": "Offer database is not available. Please check database configuration."
        }

    try:
        # Validate response type
        valid_responses = ["accept", "reject", "counter"]
        if response not in valid_responses:
            return {
                "error": f"Invalid response type. Must be one of: {', '.join(valid_responses)}"
            }

        # Validate counter offer if needed
        if response == "counter" and not counter_offer_price:
            return {
                "error": "counter_offer_price is required when response is 'counter'"
            }

        if counter_offer_price and counter_offer_price <= 0:
            return {"error": "Counter offer price must be greater than 0"}

        # Update offer status
        updated_offer = offer_db.update_offer_status(
            offer_id=offer_id,
            response=response,
            counter_offer_price=counter_offer_price,
            notes=notes,
        )

        if not updated_offer:
            return {"error": f"Offer {offer_id} not found"}

        return {
            "success": True,
            "message": f"Offer {response}ed successfully",
            "offer": updated_offer,
        }

    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to process offer response: {str(e)}"}


@mcp.tool()
def list_offers(property_id: str, status: Optional[str] = None) -> dict:
    """
    List all offers for a property, optionally filtered by status.

    Args:
        property_id: The property to list offers for
        status: Optional status filter ("pending_review", "accepted", "rejected", "countered")

    Returns:
        List of offers and summary statistics
    """
    if not offer_db:
        return {
            "error": "Offer database is not available. Please check database configuration."
        }

    try:
        # Validate status if provided
        if status:
            valid_statuses = ["pending_review", "accepted", "rejected", "countered"]
            if status not in valid_statuses:
                return {
                    "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                }

        # Get offers
        offers = offer_db.list_offers(property_id=property_id, status=status)

        # Get statistics
        stats = offer_db.get_offer_stats(property_id=property_id)

        return {
            "success": True,
            "property_id": property_id,
            "filter_status": status,
            "count": len(offers),
            "offers": offers,
            "statistics": stats,
        }

    except Exception as e:
        return {"error": f"Failed to list offers: {str(e)}"}


@mcp.tool()
def get_offer_statistics(property_id: str) -> dict:
    """
    Get statistics about offers for a property.

    Args:
        property_id: The property to get statistics for

    Returns:
        Offer statistics including counts by status and price information
    """
    if not offer_db:
        return {
            "error": "Offer database is not available. Please check database configuration."
        }

    try:
        stats = offer_db.get_offer_stats(property_id=property_id)

        return {
            "success": True,
            "property_id": property_id,
            "statistics": stats,
        }

    except Exception as e:
        return {"error": f"Failed to get statistics: {str(e)}"}


def main():
    """Run the MCP server

    This server can be used by MCP clients like Dedalus, Claude Desktop,
    or any other MCP-compatible application.

    The server communicates via stdin/stdout using the Model Context Protocol.
    It will run until the client disconnects or sends a shutdown request.

    Environment Setup:
    - Loads configuration from .env file
    - Initializes Calendly client (if configured)
    - Connects to Milvus vector database (if available)
    - Initializes SQLite offer database

    For Dedalus deployment, add this server to your MCP configuration:
    {
      "mcpServers": {
        "property-management": {
          "command": "uv",
          "args": ["run", "python", "main.py"],
          "cwd": "/absolute/path/to/real_estate"
        }
      }
    }
    """
    import sys
    import signal
    import atexit

    # Track if we're shutting down
    shutdown_flag = False

    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully"""
        nonlocal shutdown_flag
        if not shutdown_flag:
            shutdown_flag = True
            print("Shutting down MCP server...", file=sys.stderr)
            # Close database connections
            if offer_db and hasattr(offer_db, "conn"):
                try:
                    offer_db.conn.close()
                    print("Closed offer database connection", file=sys.stderr)
                except Exception as e:
                    print(f"Error closing database: {e}", file=sys.stderr)
            sys.exit(0)

    def cleanup():
        """Cleanup resources on exit"""
        if not shutdown_flag and offer_db and hasattr(offer_db, "conn"):
            try:
                offer_db.conn.close()
            except:
                pass

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)

    # Print startup info to stderr (stdout is reserved for MCP protocol)
    print("=" * 60, file=sys.stderr)
    print("Property Management MCP Server", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Server: {mcp.name}", file=sys.stderr)
    print(f"Protocol: Model Context Protocol (MCP)", file=sys.stderr)
    print(f"Communication: stdin/stdout", file=sys.stderr)
    print(f"", file=sys.stderr)

    # Component status
    print("Component Status:", file=sys.stderr)
    print(
        f"  Calendly: {'✓ Connected' if calendly else '✗ Not configured'}",
        file=sys.stderr,
    )
    print(
        f"  Milvus RAG: {'✓ Connected' if rag_client and rag_client.client else '✗ Not available'}",
        file=sys.stderr,
    )
    print(
        f"  Offer DB: {'✓ Ready' if offer_db else '✗ Not available'}", file=sys.stderr
    )

    # Count registered tools
    tool_count = sum(
        1
        for attr in dir(mcp)
        if not attr.startswith("_") and callable(getattr(mcp, attr, None))
    )
    print(f"", file=sys.stderr)
    print(f"Registered MCP Tools: {tool_count}", file=sys.stderr)

    print("=" * 60, file=sys.stderr)
    print("Server ready. Waiting for MCP client connection...", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("", file=sys.stderr)

    try:
        # Run the FastMCP server
        # This blocks and handles MCP protocol communication via stdin/stdout
        mcp.run()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        print("Server stopped", file=sys.stderr)


if __name__ == "__main__":
    main()
