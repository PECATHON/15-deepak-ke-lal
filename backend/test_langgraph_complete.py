"""
Comprehensive Test Suite for Multi-Agent Travel Planning System

This script demonstrates:
1. LangGraph-based coordination
2. Real API integration (Amadeus + Booking.com)
3. Request interruption handling
4. Partial result preservation
5. Context transfer between agents
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from state_store import StateStore
from agent.langgraph_coordinator import LangGraphCoordinator
from agent.flight_agent import FlightAgent
from agent.hotel_agent import HotelAgent


async def test_1_flight_search():
    """Test 1: Basic flight search with LangGraph"""
    print("\n" + "="*80)
    print("TEST 1: Flight Search (LangGraph Coordinator)")
    print("="*80)
    
    store = StateStore()
    coordinator = LangGraphCoordinator(store)
    
    result = await coordinator.process_query(
        request_id="test_flight_001",
        user_query="Find flights from Chandigarh to Delhi on December 20, 2025"
    )
    
    print(f"\n✅ Status: {result['status']}")
    print(f"📊 Intents Detected: {result['intents']}")
    print(f"🎯 Confidence: {result['confidence']}")
    
    if result.get('flight_results'):
        flights = result['flight_results'].get('results', [])
        print(f"\n✈️  Found {len(flights)} flights")
        if flights:
            cheapest = min(flights, key=lambda x: x.get('price_usd', float('inf')))
            print(f"💰 Cheapest: ${cheapest['price_usd']} on {cheapest['airline']}")
    
    print(f"\n💬 Final Response:\n{result.get('final_response', 'N/A')}")
    print("\n" + "="*80)
    
    return result


async def test_2_hotel_search():
    """Test 2: Hotel search"""
    print("\n" + "="*80)
    print("TEST 2: Hotel Search")
    print("="*80)
    
    store = StateStore()
    coordinator = LangGraphCoordinator(store)
    
    result = await coordinator.process_query(
        request_id="test_hotel_001",
        user_query="Find hotels in Delhi for December 20-22"
    )
    
    print(f"\n✅ Status: {result['status']}")
    print(f"📊 Intents Detected: {result['intents']}")
    
    if result.get('hotel_results'):
        hotels = result['hotel_results'].get('results', [])
        print(f"\n🏨 Found {len(hotels)} hotels")
        if hotels:
            best = max(hotels, key=lambda x: x.get('rating', 0))
            print(f"⭐ Top Rated: {best['name']} ({best['rating']}/10)")
    
    print(f"\n💬 Final Response:\n{result.get('final_response', 'N/A')}")
    print("\n" + "="*80)
    
    return result


async def test_3_multi_agent():
    """Test 3: Multi-agent (both flight and hotel)"""
    print("\n" + "="*80)
    print("TEST 3: Multi-Agent Search (Flight + Hotel)")
    print("="*80)
    
    store = StateStore()
    coordinator = LangGraphCoordinator(store)
    
    result = await coordinator.process_query(
        request_id="test_both_001",
        user_query="Find flights from Chandigarh to Delhi on Dec 20 and hotels in Delhi for Dec 20-22"
    )
    
    print(f"\n✅ Status: {result['status']}")
    print(f"📊 Intents Detected: {result['intents']}")
    
    # Flight results
    if result.get('flight_results'):
        flights = result['flight_results'].get('results', [])
        print(f"\n✈️  Flights: {len(flights)}")
    
    # Hotel results
    if result.get('hotel_results'):
        hotels = result['hotel_results'].get('results', [])
        print(f"🏨 Hotels: {len(hotels)}")
    
    print(f"\n💬 Final Response:\n{result.get('final_response', 'N/A')}")
    print("\n" + "="*80)
    
    return result


async def test_4_interruption():
    """Test 4: Request interruption with partial result preservation"""
    print("\n" + "="*80)
    print("TEST 4: Request Interruption & Partial Result Preservation")
    print("="*80)
    
    store = StateStore()
    coordinator = LangGraphCoordinator(store)
    
    # Start a long-running search
    print("\n1️⃣  Starting flight search...")
    task = asyncio.create_task(
        coordinator.process_query(
            request_id="test_interrupt_001",
            user_query="Find flights from New York to Los Angeles"
        )
    )
    
    # Wait a bit, then cancel
    await asyncio.sleep(2)
    print("2️⃣  Cancelling request after 2 seconds...")
    
    cancel_result = await coordinator.cancel_request("test_interrupt_001")
    
    print(f"\n✅ Cancellation Status: {cancel_result['status']}")
    print(f"📦 Partial Results Preserved: {cancel_result.get('message')}")
    
    # Check partial results
    partials = cancel_result.get('partial_results', {})
    if partials.get('flight_agent'):
        partial_count = len(partials['flight_agent'])
        print(f"💾 Partial Flight Results: {partial_count} batches preserved")
    
    # Cancel the task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("✅ Task cancelled successfully")
    
    print("\n" + "="*80)
    
    return cancel_result


async def test_5_context_transfer():
    """Test 5: Context transfer between agents"""
    print("\n" + "="*80)
    print("TEST 5: Context Transfer Between Agents")
    print("="*80)
    
    store = StateStore()
    coordinator = LangGraphCoordinator(store)
    
    # First query: Flight search
    print("\n1️⃣  Query 1: Flight search")
    result1 = await coordinator.process_query(
        request_id="test_context_001",
        user_query="Find flights from Delhi to Mumbai on Dec 20"
    )
    
    print(f"   Detected: {result1['intents']}")
    print(f"   Extracted: {result1['extracted_params']}")
    
    # Second query: Hotel search (should transfer context)
    print("\n2️⃣  Query 2: Hotel search (context transfer)")
    result2 = await coordinator.process_query(
        request_id="test_context_002",
        user_query="What about hotels in Mumbai?"
    )
    
    print(f"   Detected: {result2['intents']}")
    print(f"   Extracted: {result2['extracted_params']}")
    
    # Verify context transfer
    if result2['extracted_params'].get('destination') == 'Mumbai':
        print("\n✅ Context transferred successfully!")
    
    print("\n" + "="*80)
    
    return result1, result2


async def run_all_tests():
    """Run all tests sequentially"""
    print("\n" + "🚀"*40)
    print("MULTI-AGENT TRAVEL PLANNING SYSTEM - TEST SUITE")
    print("🚀"*40)
    
    try:
        # Test 1: Flight search
        await test_1_flight_search()
        await asyncio.sleep(1)
        
        # Test 2: Hotel search
        await test_2_hotel_search()
        await asyncio.sleep(1)
        
        # Test 3: Multi-agent
        await test_3_multi_agent()
        await asyncio.sleep(1)
        
        # Test 4: Interruption
        await test_4_interruption()
        await asyncio.sleep(1)
        
        # Test 5: Context transfer
        await test_5_context_transfer()
        
        print("\n" + "✅"*40)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✅"*40 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Load environment variables manually
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    print("\n📋 Environment Configuration:")
    print(f"   AMADEUS_API_KEY: {'✅ Set' if os.getenv('AMADEUS_API_KEY') else '❌ Missing'}")
    print(f"   RAPIDAPI_KEY: {'✅ Set' if os.getenv('RAPIDAPI_KEY') else '❌ Missing'}")
    print(f"   OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    
    # Run tests
    asyncio.run(run_all_tests())
