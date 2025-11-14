#!/usr/bin/env python3
"""
FastAPI REST API Server for Property Management + AI Chat (MCP-backed)

Features:
- RAG-based property Q&A via Milvus
- Calendly-based tour scheduling
- Offer intake & processing backed by OfferDatabase
- WebSocket broadcast for live updates
- Unified AI chat endpoint that uses all of the above as tools
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

import logging
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from dotenv import load_dotenv
from openai import OpenAI

# Import MCP server components (your existing code)
from main import (
    CalendlyClient,
    MilvusRAGClient,
    OfferDatabase,
    calendly_client,
    rag_client,
    offer_db,
)

# ---------------------------------------------------------------------------
# ENV & LOGGING
# ---------------------------------------------------------------------------

load_dotenv()

logger = logging.getLogger("property-api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    stream=sys.stderr,
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set. /api/chat will not work without it.")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# OpenAI client (new style)
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# ---------------------------------------------------------------------------
# SHARED / CHAT MODELS
# ---------------------------------------------------------------------------


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    property_id: str = Field(..., description="Property identifier")
    messages: List[ChatTurn] = Field(
        ..., description="Conversation history (incl. latest user message)"
    )


# ---------------------------------------------------------------------------
# PROPERTY Q&A MODELS
# ---------------------------------------------------------------------------


class AddDocumentRequest(BaseModel):
    property_id: str = Field(..., description="Property identifier")
    document_name: str = Field(..., description="Document title")
    text: str = Field(..., description="Full document text content")


class SearchDocumentsRequest(BaseModel):
    query: str = Field(..., description="Search query")
    property_id: Optional[str] = Field(None, description="Filter by property ID")
    limit: int = Field(5, ge=1, le=50, description="Maximum results to return")


class DeleteDocumentsRequest(BaseModel):
    property_id: str = Field(..., description="Property ID to delete documents for")


class PropertyDetailsRequest(BaseModel):
    property_id: str = Field(..., description="Property identifier")


# ---------------------------------------------------------------------------
# TOUR SCHEDULING MODELS
# ---------------------------------------------------------------------------


class CheckAvailabilityRequest(BaseModel):
    property_id: str = Field(..., description="Property identifier")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")


class BookTourRequest(BaseModel):
    property_id: str = Field(..., description="Property identifier")
    iso_datetime: str = Field(..., description="Tour datetime in ISO format")
    visitor_name: str = Field(..., description="Full name of visitor")
    visitor_email: EmailStr = Field(..., description="Email address")
    visitor_phone: str = Field(..., description="Phone number")


class CancelTourRequest(BaseModel):
    booking_id: str = Field(..., description="Calendly event UUID")
    reason: Optional[str] = Field(None, description="Cancellation reason")


class RescheduleTourRequest(BaseModel):
    booking_id: str = Field(..., description="Original Calendly event UUID")
    property_id: str = Field(..., description="Property identifier")
    new_iso_datetime: str = Field(..., description="New tour datetime in ISO format")
    visitor_name: str = Field(..., description="Full name")
    visitor_email: EmailStr = Field(..., description="Email address")
    visitor_phone: str = Field(..., description="Phone number")
    reschedule_reason: Optional[str] = Field(
        None, description="Reason for rescheduling"
    )


# ---------------------------------------------------------------------------
# OFFER PROCESSING MODELS
# ---------------------------------------------------------------------------


class SubmitOfferRequest(BaseModel):
    property_id: str = Field(..., description="Property identifier")
    buyer_name: str = Field(..., description="Full name of buyer")
    buyer_email: EmailStr = Field(..., description="Email address")
    buyer_phone: str = Field(..., description="Phone number")
    offer_price: float = Field(..., gt=0, description="Offered purchase price")
    contingencies: List[str] = Field(..., description="List of contingencies")
    closing_date: str = Field(..., description="Proposed closing date (YYYY-MM-DD)")
    additional_terms: Optional[Dict[str, Any]] = Field(
        None, description="Additional terms"
    )


class GetOfferStatusRequest(BaseModel):
    offer_id: str = Field(..., description="Offer ID to check")


class ProcessOfferResponseRequest(BaseModel):
    offer_id: str = Field(..., description="Offer ID to respond to")
    response: str = Field(..., description="Response type: accept, reject, or counter")
    counter_offer_price: Optional[float] = Field(
        None, description="Required if response is counter"
    )
    notes: Optional[str] = Field(None, description="Notes about the response")


class ListOffersRequest(BaseModel):
    property_id: str = Field(..., description="Property to list offers for")
    status: Optional[str] = Field(None, description="Filter by status")


class GetOfferStatisticsRequest(BaseModel):
    property_id: str = Field(..., description="Property identifier")


# ---------------------------------------------------------------------------
# DOCUMENT GENERATION MODELS
# ---------------------------------------------------------------------------


class GenerateRentalApplicationRequest(BaseModel):
    property_id: str = Field(..., description="Property identifier")
    applicant_name: str = Field(..., description="Applicant's full name")
    applicant_email: EmailStr = Field(..., description="Email address")


class GenerateLeaseAgreementRequest(BaseModel):
    property_id: str = Field(..., description="Property identifier")
    tenant_name: str = Field(..., description="Tenant's full name")
    lease_start_date: str = Field(..., description="Lease start date (YYYY-MM-DD)")
    lease_term_months: int = Field(..., gt=0, description="Lease term in months")
    monthly_rent: float = Field(..., gt=0, description="Monthly rent amount")


# ---------------------------------------------------------------------------
# WEBSOCKET CONNECTION MANAGER
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket client connected. Total: %d", len(self.active_connections)
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            "WebSocket client disconnected. Total: %d", len(self.active_connections)
        )

    async def broadcast(self, message: dict):
        dead: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("Error broadcasting to client: %s", e)
                dead.append(connection)
        # Clean up dead connections
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# FASTAPI APPLICATION SETUP
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# TEMP MOCK CALENDLY CLIENT (for local testing without real Calendly)
# ---------------------------------------------------------------------------


class MockCalendlyClient:
    """
    Lightweight fake Calendly client.
    It simulates availability, booking, cancel, and rescheduling.
    This mock is async-compatible and matches the methods used by the API.
    """

    def __init__(self):
        self.default_event_type_uri = "mock-event-type/12345"
        self._events = {}  # event_uuid -> event dict

    async def get_event_type_available_times(
        self, event_type_uri, start_time, end_time
    ):
        # Generate fake availability every hour between 9am–5pm
        import datetime

        start = datetime.datetime.fromisoformat(start_time.replace("Z", ""))
        end = datetime.datetime.fromisoformat(end_time.replace("Z", ""))

        slots = []
        current = start.replace(hour=9, minute=0, second=0)
        while current < end:
            slot = {
                "start_time": current.isoformat() + "Z",
                "status": "available",
                "invitees_remaining": 1,
            }
            slots.append(slot)
            current += datetime.timedelta(hours=1)

        return slots

    async def create_scheduled_event(
        self,
        event_type_uri,
        start_time,
        invitee_email,
        invitee_name,
        invitee_phone,
        additional_notes=None,
    ):
        # Pretend we created an event with a UUID
        import uuid

        event_uuid = uuid.uuid4().hex
        event_uri = f"https://mock.calendly.com/events/{event_uuid}"

        self._events[event_uuid] = {
            "event_uuid": event_uuid,
            "uri": event_uri,
            "start_time": start_time,
            "invitee_email": invitee_email,
            "invitee_name": invitee_name,
            "invitee_phone": invitee_phone,
            "notes": additional_notes,
        }

        return self._events[event_uuid]

    async def cancel_scheduled_event(self, event_uuid, reason=None):
        # Mark event canceled (if exists)
        event = self._events.get(event_uuid)
        if event:
            event["canceled"] = True
            event["cancellation_reason"] = reason
        return {"success": True}


# If the real Calendly client failed to load, replace it with mock
if not calendly_client:
    logger.warning("Calendly client not found — using mock Calendly client")
    calendly_client = MockCalendlyClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    logger.info("=" * 60)
    logger.info("Property Management REST API Server")
    logger.info("=" * 60)

    calendly_status = "connected" if calendly_client else "NOT CONFIGURED"
    milvus_status = "connected" if rag_client else "NOT CONFIGURED"
    offer_db_status = "ready" if offer_db else "NOT CONFIGURED"

    logger.info("Component Status:")
    logger.info("  Calendly: %s", calendly_status)
    logger.info("  Milvus RAG: %s", milvus_status)
    logger.info("  Offer DB: %s", offer_db_status)
    logger.info("=" * 60)

    yield

    # Shutdown
    if offer_db and hasattr(offer_db, "conn"):
        offer_db.conn.close()
        logger.info("Closed Offer DB connections")
    logger.info("Server stopped")


app = FastAPI(
    title="Property Management API",
    description="REST API for property management with RAG Q&A, tours, offers, docs, and AI chat",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS – tighten this in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------------


async def generate_llm_reply(system_prompt: str, history: List[ChatTurn]) -> str:
    """Call OpenAI chat completion with given system prompt and history."""
    if not openai_client:
        logger.error("OpenAI client not initialized (missing OPENAI_API_KEY)")
        raise HTTPException(status_code=500, detail="LLM not configured on server")

    def _call():
        return openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *[{"role": m.role, "content": m.content} for m in history],
            ],
        )

    try:
        completion = await asyncio.to_thread(_call)
        return completion.choices[0].message.content
    except Exception as e:
        logger.exception("Error calling OpenAI: %s", e)
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")


def detect_tool_intent(user_msg: str) -> Optional[str]:
    """Very simple heuristic tool router based on user text."""
    lower = user_msg.lower()

    if "tour" in lower and any(
        w in lower for w in ["book", "schedule", "visit", "see"]
    ):
        return "tour"

    if "offer" in lower and any(w in lower for w in ["submit", "make", "buy", "bid"]):
        return "offer"

    if any(w in lower for w in ["valuation", "value", "price estimate"]):
        return "valuation"

    return None


async def fetch_rag_context(
    query: str, property_id: Optional[str], limit: int = 5
) -> str:
    """Get concatenated context from Milvus RAG for a query, if configured."""
    if not rag_client:
        return ""

    try:
        results = rag_client.search(
            query=query,
            property_id=property_id,
            limit=limit,
        )
        if not results:
            return ""
        return "\n\n".join([r.get("text", "") for r in results])
    except Exception as e:
        logger.warning("RAG search failed: %s", e)
        return ""


# ---------------------------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------------------------


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "calendly": calendly_client is not None,
            "milvus_rag": rag_client is not None,
            "offer_db": offer_db is not None,
            "openai": openai_client is not None,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# AI CHAT ENDPOINT (NEW, UNIFIED)
# ---------------------------------------------------------------------------


@app.post("/api/chat")
async def chat_with_property_ai(request: ChatRequest):
    """
    Unified AI assistant endpoint.

    - Uses Milvus RAG for property-specific context.
    - Detects simple tool intents (tours, offers, valuations).
    - Calls OpenAI (or configured LLM) to generate final reply.
    - Returns { reply: str, tool: Optional[str] }.

    The frontend can decide how to act on `tool`:
    - "tour"    → prompt the user and hit /api/tours/*
    - "offer"   → open offer form and hit /api/offers/*
    - "valuation" → maybe call /api/property/search or just show RAG-based answer
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    last_msg = request.messages[-1]
    if last_msg.role != "user":
        raise HTTPException(
            status_code=400, detail="Last message must be from the user"
        )

    user_msg = last_msg.content
    tool = detect_tool_intent(user_msg)

    # Pull RAG context for the latest user query
    rag_context = await fetch_rag_context(
        query=user_msg,
        property_id=request.property_id,
        limit=5,
    )

    system_prompt = f"""
You are Jayjay, a friendly AI real-estate assistant for property {request.property_id}.
Use the RAG context when answering, but you can also rely on general real-estate knowledge.

If user intent is clearly about:
- booking/scheduling a tour
- submitting an offer
- asking for valuation

mention what you *can* do, but let the frontend handle actual bookings/offers
via its tools. Do NOT invent confirmations or bookings.

If you lack information, say so and suggest what data is needed.

=== RAG CONTEXT (may be empty) ===
{rag_context}
"""

    reply = await generate_llm_reply(system_prompt, request.messages)

    return {
        "reply": reply,
        "tool": tool,
    }


# ---------------------------------------------------------------------------
# PROPERTY Q&A ENDPOINTS
# ---------------------------------------------------------------------------


@app.post("/api/property/search")
async def search_property_documents(request: SearchDocumentsRequest):
    """Search property documents using semantic search via Milvus."""
    if not rag_client:
        raise HTTPException(status_code=503, detail="Milvus RAG is not configured")

    try:
        results = rag_client.search(
            query=request.query,
            property_id=request.property_id,
            limit=request.limit,
        )

        if not results:
            return {
                "query": request.query,
                "property_id": request.property_id,
                "num_results": 0,
                "results": [],
                "answer": "No relevant documents found for this query.",
            }

        context = "\n\n".join([r.get("text", "") for r in results])

        return {
            "query": request.query,
            "property_id": request.property_id,
            "num_results": len(results),
            "results": results,
            "context": context,
            "answer": f"Found {len(results)} relevant document sections.",
        }

    except Exception as e:
        logger.exception("Search failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@app.post("/api/property/add-document")
async def add_property_document(request: AddDocumentRequest):
    """Add a document to the property knowledge base."""
    if not rag_client:
        raise HTTPException(status_code=503, detail="Milvus RAG is not configured")

    try:
        result = rag_client.add_document(
            property_id=request.property_id,
            document_name=request.document_name,
            text=request.text,
        )

        await manager.broadcast(
            {
                "event": "document_added",
                "property_id": request.property_id,
                "document_name": request.document_name,
                "chunks_inserted": result.get("insert_count", 0),
            }
        )

        return result

    except Exception as e:
        logger.exception("Failed to add document: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to add document: {e}")


@app.post("/api/property/delete-documents")
async def delete_property_documents(request: DeleteDocumentsRequest):
    """Delete all documents for a property."""
    if not rag_client:
        raise HTTPException(status_code=503, detail="Milvus RAG is not configured")

    try:
        result = rag_client.delete_documents(property_id=request.property_id)

        await manager.broadcast(
            {
                "event": "documents_deleted",
                "property_id": request.property_id,
                "deleted_count": result.get("deleted_count", 0),
            }
        )

        return result

    except Exception as e:
        logger.exception("Failed to delete documents: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to delete documents: {e}")


@app.post("/api/property/details")
async def get_property_details(request: PropertyDetailsRequest):
    """Get property metadata and document count."""
    if not rag_client:
        raise HTTPException(status_code=503, detail="Milvus RAG is not configured")

    try:
        all_docs = rag_client.search(
            query="", property_id=request.property_id, limit=1000
        )
        unique_docs = {
            doc.get("document_name") for doc in all_docs if doc.get("document_name")
        }

        return {
            "property_id": request.property_id,
            "total_chunks": len(all_docs),
            "unique_documents": len(unique_docs),
            "document_names": sorted(list(unique_docs)),
        }

    except Exception as e:
        logger.exception("Failed to get property details: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get details: {e}")


# ---------------------------------------------------------------------------
# TOUR SCHEDULING ENDPOINTS
# ---------------------------------------------------------------------------


@app.post("/api/tours/check-availability")
async def check_tour_availability(request: CheckAvailabilityRequest):
    """Check available tour slots for a property via Calendly."""
    if not calendly_client:
        raise HTTPException(status_code=503, detail="Calendly is not configured")

    try:
        start_datetime = f"{request.start_date}T00:00:00Z"
        end_datetime = f"{request.end_date}T23:59:59Z"

        available_times = await calendly_client.get_event_type_available_times(
            event_type_uri=calendly_client.default_event_type_uri,
            start_time=start_datetime,
            end_time=end_datetime,
        )

        slots = [
            {
                "start_time": slot.get("start_time"),
                "status": slot.get("status"),
                "invitees_remaining": slot.get("invitees_remaining", 1),
            }
            for slot in available_times
        ]

        return {
            "property_id": request.property_id,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "available_slots": slots,
            "total_slots": len(slots),
        }

    except Exception as e:
        logger.exception("Failed to check availability: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to check availability: {e}"
        )


@app.post("/api/tours/book")
async def book_property_tour(request: BookTourRequest):
    """Book a property tour via Calendly."""
    if not calendly_client:
        raise HTTPException(status_code=503, detail="Calendly is not configured")

    try:
        event = await calendly_client.create_scheduled_event(
            event_type_uri=calendly_client.default_event_type_uri,
            start_time=request.iso_datetime,
            invitee_email=request.visitor_email,
            invitee_name=request.visitor_name,
            invitee_phone=request.visitor_phone,
            additional_notes=f"Property tour for {request.property_id}",
        )

        booking_id = event.get("uri", "").split("/")[-1] if event.get("uri") else None

        result = {
            "success": True,
            "property_id": request.property_id,
            "booking_id": booking_id,
            "scheduled_time": request.iso_datetime,
            "visitor_name": request.visitor_name,
            "visitor_email": request.visitor_email,
            "confirmation": "Tour booked successfully. Confirmation email sent to visitor.",
        }

        await manager.broadcast(
            {
                "event": "tour_booked",
                "property_id": request.property_id,
                "booking_id": booking_id,
                "scheduled_time": request.iso_datetime,
                "visitor_name": request.visitor_name,
            }
        )

        return result

    except Exception as e:
        logger.exception("Failed to book tour: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to book tour: {e}")


@app.post("/api/tours/cancel")
async def cancel_tour(request: CancelTourRequest):
    """Cancel a scheduled tour."""
    if not calendly_client:
        raise HTTPException(status_code=503, detail="Calendly is not configured")

    try:
        await calendly_client.cancel_scheduled_event(
            event_uuid=request.booking_id,
            reason=request.reason,
        )

        result = {
            "success": True,
            "booking_id": request.booking_id,
            "cancellation_reason": request.reason,
            "message": "Tour cancelled successfully. Cancellation email sent to visitor.",
        }

        await manager.broadcast(
            {
                "event": "tour_cancelled",
                "booking_id": request.booking_id,
                "reason": request.reason,
            }
        )

        return result

    except Exception as e:
        logger.exception("Failed to cancel tour: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to cancel tour: {e}")


@app.post("/api/tours/reschedule")
async def reschedule_tour(request: RescheduleTourRequest):
    """Reschedule a tour (cancel old and create new)."""
    if not calendly_client:
        raise HTTPException(status_code=503, detail="Calendly is not configured")

    try:
        # Cancel old booking
        await calendly_client.cancel_scheduled_event(
            event_uuid=request.booking_id,
            reason=request.reschedule_reason or "Rescheduled by request",
        )

        # Create new booking
        new_event = await calendly_client.create_scheduled_event(
            event_type_uri=calendly_client.default_event_type_uri,
            start_time=request.new_iso_datetime,
            invitee_email=request.visitor_email,
            invitee_name=request.visitor_name,
            invitee_phone=request.visitor_phone,
            additional_notes=f"Rescheduled tour for {request.property_id}. Reason: {request.reschedule_reason}",
        )

        new_booking_id = (
            new_event.get("uri", "").split("/")[-1] if new_event.get("uri") else None
        )

        result = {
            "success": True,
            "old_booking_id": request.booking_id,
            "new_booking_id": new_booking_id,
            "new_scheduled_time": request.new_iso_datetime,
            "property_id": request.property_id,
            "visitor_name": request.visitor_name,
            "message": "Tour rescheduled successfully. Confirmation email sent with new time.",
        }

        await manager.broadcast(
            {
                "event": "tour_rescheduled",
                "old_booking_id": request.booking_id,
                "new_booking_id": new_booking_id,
                "new_scheduled_time": request.new_iso_datetime,
                "property_id": request.property_id,
            }
        )

        return result

    except Exception as e:
        logger.exception("Failed to reschedule tour: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to reschedule tour: {e}")


# ---------------------------------------------------------------------------
# OFFER PROCESSING ENDPOINTS
# ---------------------------------------------------------------------------


@app.post("/api/offers/submit")
async def submit_offer(request: SubmitOfferRequest):
    """Submit a new offer on a property."""
    if not offer_db:
        raise HTTPException(status_code=503, detail="Offer database is not configured")

    try:
        offer = offer_db.create_offer(
            property_id=request.property_id,
            buyer_name=request.buyer_name,
            buyer_email=request.buyer_email,
            buyer_phone=request.buyer_phone,
            offer_price=request.offer_price,
            contingencies=request.contingencies,
            closing_date=request.closing_date,
            additional_terms=request.additional_terms,
        )

        result = {
            "success": True,
            "message": "Offer submitted successfully",
            "offer": offer,
        }

        await manager.broadcast(
            {
                "event": "offer_submitted",
                "offer_id": offer["offer_id"],
                "property_id": request.property_id,
                "buyer_name": request.buyer_name,
                "offer_price": request.offer_price,
            }
        )

        return result

    except Exception as e:
        logger.exception("Failed to submit offer: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to submit offer: {e}")


@app.post("/api/offers/status")
async def get_offer_status(request: GetOfferStatusRequest):
    """Get the status of a submitted offer."""
    if not offer_db:
        raise HTTPException(status_code=503, detail="Offer database is not configured")

    try:
        offer = offer_db.get_offer(request.offer_id)

        if not offer:
            raise HTTPException(
                status_code=404, detail=f"Offer {request.offer_id} not found"
            )

        return {
            "success": True,
            "offer": offer,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get offer status: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get offer status: {e}")


@app.post("/api/offers/respond")
async def process_offer_response(request: ProcessOfferResponseRequest):
    """Process a response to an offer (accept/reject/counter)."""
    if not offer_db:
        raise HTTPException(status_code=503, detail="Offer database is not configured")

    try:
        if request.response not in {"accept", "reject", "counter"}:
            raise HTTPException(
                status_code=400,
                detail="Response must be 'accept', 'reject', or 'counter'",
            )

        if request.response == "counter" and request.counter_offer_price is None:
            raise HTTPException(
                status_code=400,
                detail="counter_offer_price is required when response is 'counter'",
            )

        offer = offer_db.update_offer_status(
            offer_id=request.offer_id,
            response=request.response,
            counter_offer_price=request.counter_offer_price,
            notes=request.notes,
        )

        if not offer:
            raise HTTPException(
                status_code=404, detail=f"Offer {request.offer_id} not found"
            )

        result = {
            "success": True,
            "message": f"Offer {request.response}ed successfully",
            "offer": offer,
        }

        await manager.broadcast(
            {
                "event": "offer_response_processed",
                "offer_id": request.offer_id,
                "response": request.response,
                "counter_offer_price": request.counter_offer_price,
            }
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to process offer response: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to process offer response: {e}"
        )


@app.post("/api/offers/list")
async def list_offers(request: ListOffersRequest):
    """List all offers for a property with optional status filter."""
    if not offer_db:
        raise HTTPException(status_code=503, detail="Offer database is not configured")

    try:
        offers = offer_db.list_offers(
            property_id=request.property_id,
            status=request.status,
        )

        stats = offer_db.get_offer_stats(request.property_id)

        return {
            "success": True,
            "property_id": request.property_id,
            "status_filter": request.status,
            "offers": offers,
            "total_offers": len(offers),
            "statistics": stats,
        }

    except Exception as e:
        logger.exception("Failed to list offers: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to list offers: {e}")


@app.post("/api/offers/statistics")
async def get_offer_statistics(request: GetOfferStatisticsRequest):
    """Get aggregate statistics for offers on a property."""
    if not offer_db:
        raise HTTPException(status_code=503, detail="Offer database is not configured")

    try:
        stats = offer_db.get_offer_stats(request.property_id)

        return {
            "success": True,
            "property_id": request.property_id,
            "statistics": stats,
        }

    except Exception as e:
        logger.exception("Failed to get statistics: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {e}")


# ---------------------------------------------------------------------------
# DOCUMENT GENERATION ENDPOINTS (STUBS)
# ---------------------------------------------------------------------------


@app.post("/api/documents/rental-application")
async def generate_rental_application(request: GenerateRentalApplicationRequest):
    """Generate a rental application (stub)."""
    return {
        "success": False,
        "message": "Document generation not yet implemented",
        "property_id": request.property_id,
        "applicant_name": request.applicant_name,
    }


@app.post("/api/documents/lease-agreement")
async def generate_lease_agreement(request: GenerateLeaseAgreementRequest):
    """Generate a lease agreement (stub)."""
    return {
        "success": False,
        "message": "Document generation not yet implemented",
        "property_id": request.property_id,
        "tenant_name": request.tenant_name,
    }


# ---------------------------------------------------------------------------
# WEBSOCKET ENDPOINT
# ---------------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        await websocket.send_json(
            {
                "event": "connected",
                "message": "Connected to Property Management API",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        while True:
            data = await websocket.receive_text()
            await websocket.send_json(
                {
                    "event": "echo",
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    ssl_keyfile = os.getenv("SSL_KEYFILE")
    ssl_certfile = os.getenv("SSL_CERTFILE")

    ssl_config: Dict[str, Any] = {}
    if ssl_keyfile and ssl_certfile:
        ssl_config = {
            "ssl_keyfile": ssl_keyfile,
            "ssl_certfile": ssl_certfile,
        }
        logger.info("Starting server with HTTPS on %s:%d", host, port)
    else:
        logger.warning(
            "Starting server with HTTP on %s:%d (no SSL configured)", host, port
        )

    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        **ssl_config,
    )
