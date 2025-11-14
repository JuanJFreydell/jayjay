#!/usr/bin/env python3
"""
Dedalus Client Example for Property Management MCP Server

This script demonstrates how to use the Property Management MCP server
from Dedalus. It shows various workflows including:
- Property document management
- Property search
- Offer submission and processing
- Tour scheduling (if Calendly is configured)

Prerequisites:
1. Dedalus installed: pip install dedalus-labs
2. MCP server configured in Dedalus (see mcp_config.json)
3. Server dependencies installed: uv sync
4. Optional: Milvus running for RAG features
5. Optional: Calendly configured for tour scheduling
"""

import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner


async def example_property_qa_workflow():
    """
    Example: Property Q&A with RAG

    Demonstrates:
    - Adding property documents to the knowledge base
    - Searching documents with semantic search
    - Getting property details
    """
    print("\n" + "=" * 60)
    print("Example 1: Property Q&A Workflow")
    print("=" * 60)

    client = AsyncDedalus()
    runner = DedalusRunner(client)

    # Step 1: Add property documents
    print("\n[Step 1] Adding property documents...")
    response = await runner.run(
        input="""Add property documents for property DEMO-001:

        Document 1 - Property Description:
        Beautiful 2-bedroom, 2-bathroom apartment in downtown.
        Modern kitchen with stainless steel appliances, granite countertops.
        Hardwood floors throughout. Large windows with city views.
        1,200 sq ft of living space.

        Document 2 - Amenities:
        - Rooftop swimming pool
        - 24/7 fitness center
        - Secure parking garage (2 spaces included)
        - Pet-friendly (dogs and cats welcome)
        - 24-hour concierge service
        - Package receiving room

        Document 3 - Location:
        Located at 123 Main Street, downtown district.
        Walking distance to subway (2 blocks).
        Near restaurants, shopping, and entertainment.
        Park and green space within 5-minute walk.

        Use the add_property_document tool for each document.""",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")

    # Step 2: Search the documents
    print("\n[Step 2] Searching property documents...")
    response = await runner.run(
        input="""Using search_property_documents, answer these questions about DEMO-001:
        1. How many bedrooms does it have?
        2. Is it pet-friendly?
        3. What parking options are available?
        4. How close is public transit?""",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")

    # Step 3: Get property statistics
    print("\n[Step 3] Getting property details...")
    response = await runner.run(
        input="Get details for property DEMO-001 using get_property_details.",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")


async def example_offer_workflow():
    """
    Example: Complete offer processing workflow

    Demonstrates:
    - Submitting offers
    - Listing offers
    - Processing offer responses (counter-offer)
    - Getting offer statistics
    """
    print("\n" + "=" * 60)
    print("Example 2: Offer Processing Workflow")
    print("=" * 60)

    client = AsyncDedalus()
    runner = DedalusRunner(client)

    # Step 1: Submit an offer
    print("\n[Step 1] Submitting property offer...")
    response = await runner.run(
        input="""Submit an offer on property DEMO-001 using submit_offer:
        - Buyer name: Alice Johnson
        - Email: alice.johnson@example.com
        - Phone: 555-0101
        - Offer price: $475,000
        - Contingencies: inspection, financing
        - Closing date: 2025-12-31

        After submitting, tell me the offer ID.""",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")

    # Step 2: Submit a second offer
    print("\n[Step 2] Submitting second offer...")
    response = await runner.run(
        input="""Submit another offer on property DEMO-001:
        - Buyer name: Bob Williams
        - Email: bob.williams@example.com
        - Phone: 555-0202
        - Offer price: $490,000
        - Contingencies: inspection only
        - Closing date: 2025-12-15""",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")

    # Step 3: List all offers
    print("\n[Step 3] Listing all offers...")
    response = await runner.run(
        input="List all offers for property DEMO-001 using list_offers. Show me the statistics too.",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")

    # Step 4: Counter the first offer
    print("\n[Step 4] Countering an offer...")
    response = await runner.run(
        input="""Find Alice Johnson's offer from the list above and counter it using process_offer_response:
        - Response type: counter
        - Counter price: $485,000
        - Notes: Counter offer - split the difference with asking price

        Then check the updated status.""",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")

    # Step 5: Get final statistics
    print("\n[Step 5] Getting offer statistics...")
    response = await runner.run(
        input="Get offer statistics for DEMO-001 using get_offer_statistics.",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")


async def example_tour_scheduling_workflow():
    """
    Example: Tour scheduling workflow (requires Calendly)

    Demonstrates:
    - Checking tour availability
    - Booking a tour
    - Note: Requires CALENDLY_API_KEY to be configured
    """
    print("\n" + "=" * 60)
    print("Example 3: Tour Scheduling Workflow")
    print("=" * 60)
    print("Note: This requires Calendly API to be configured")

    client = AsyncDedalus()
    runner = DedalusRunner(client)

    # Step 1: Check availability
    print("\n[Step 1] Checking tour availability...")
    response = await runner.run(
        input="""Check tour availability for property DEMO-001
        from 2025-12-01 to 2025-12-07 using check_tour_availability.

        Show me what time slots are available.""",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")

    # Step 2: Book a tour
    print("\n[Step 2] Booking a tour...")
    response = await runner.run(
        input="""If there are available slots, book a tour using book_property_tour:
        - Property: DEMO-001
        - Visitor: Charlie Davis
        - Email: charlie@example.com
        - Phone: 555-0303
        - Use the first available slot from the previous check

        If Calendly is not configured, that's okay - just let me know.""",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")


async def example_complete_workflow():
    """
    Example: Complete end-to-end workflow

    Simulates a complete property management scenario from
    listing to offer acceptance.
    """
    print("\n" + "=" * 60)
    print("Example 4: Complete End-to-End Workflow")
    print("=" * 60)

    client = AsyncDedalus()
    runner = DedalusRunner(client)

    response = await runner.run(
        input="""Help me manage property COMPLETE-001. Here's the scenario:

1. First, add this property information:
   - Type: 3BR/2BA house
   - Features: Updated kitchen, backyard, garage
   - Amenities: Near schools, shopping
   - Price: $550,000

2. A buyer asks: "Does it have a backyard? How many bedrooms?"
   Search the documents to answer.

3. The buyer makes an offer:
   - Name: Dana Martinez
   - Email: dana@example.com
   - Phone: 555-0404
   - Offer: $525,000
   - Contingencies: inspection, financing, appraisal
   - Closing: 2026-01-15

4. Counter the offer at $540,000 with note "Counter - closer to asking"

5. Show me final statistics for all offers on this property.

Use the appropriate MCP tools for each step and guide me through the process.""",
        model="anthropic/claude-3-5-sonnet",
        mcp_servers=["property-management"],
    )
    print(f"Response: {response.final_output}")


async def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("Property Management MCP Server - Dedalus Client Examples")
    print("=" * 70)
    print("\nThis demonstrates using the Property Management MCP server from Dedalus.")
    print("The AI agent will use the MCP tools to complete each workflow.")
    print("\nMake sure:")
    print("  1. The MCP server is configured in your Dedalus setup")
    print("  2. Server dependencies are installed (uv sync)")
    print("  3. Optional: Milvus is running for RAG features")
    print("  4. Optional: Calendly is configured for tour scheduling")

    try:
        # Run examples
        await example_property_qa_workflow()

        await example_offer_workflow()

        # Tour scheduling may fail if Calendly not configured - that's okay
        try:
            await example_tour_scheduling_workflow()
        except Exception as e:
            print(f"\nTour scheduling example skipped: {e}")
            print("(This is expected if Calendly is not configured)")

        await example_complete_workflow()

        print("\n" + "=" * 70)
        print("All examples completed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nTroubleshooting:")
        print("  1. Is the MCP server configured correctly?")
        print("  2. Check mcp_config.json has the correct path")
        print("  3. Run 'python verify_mcp.py' to test server setup")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
