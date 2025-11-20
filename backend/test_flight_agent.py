"""
Test runner for FlightAgent - demonstrates usage and cancellation.

Run with:
    python test_flight_agent.py
"""

import asyncio
import logging
from state_store import StateStore
from agent.flight_agent import FlightAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_complete_search():
    """Test 1: Complete flight search without cancellation."""
    logger.info("=" * 60)
    logger.info("TEST 1: Complete Flight Search")
    logger.info("=" * 60)
    
    state_store = StateStore()
    agent = FlightAgent(state_store)
    
    params = {
        "origin": "JFK",
        "destination": "LAX",
        "date": "2025-12-15",
        "passengers": 2
    }
    
    result = await agent.run("request_001", params)
    
    logger.info(f"Final Result: {result['status']}")
    logger.info(f"Total Flights Found: {result['metadata']['total_results']}")
    logger.info(f"Pages Processed: {result['metadata']['pages_processed']}")
    
    # Check partial results in state store
    partials = state_store.get_all_partials("request_001")
    logger.info(f"Partial results saved: {len(partials.get('flight_agent', []))} batches")
    
    return result


async def test_cancelled_search():
    """Test 2: Flight search with mid-execution cancellation."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Cancelled Flight Search")
    logger.info("=" * 60)
    
    state_store = StateStore()
    agent = FlightAgent(state_store)
    
    params = {
        "origin": "SFO",
        "destination": "MIA",
        "date": "2025-12-20",
        "passengers": 1
    }
    
    # Run agent in background task
    task = asyncio.create_task(agent.run("request_002", params))
    
    # Cancel after 2 seconds (should be mid-search)
    await asyncio.sleep(2)
    logger.info("🛑 Requesting cancellation...")
    agent.cancel()
    
    # Wait for completion
    result = await task
    
    logger.info(f"Final Result: {result['status']}")
    logger.info(f"Flights Found Before Cancel: {result['metadata']['total_results']}")
    logger.info(f"Pages Processed Before Cancel: {result['metadata']['pages_processed']}")
    
    # Check if marked as cancelled in state store
    is_cancelled = state_store.is_cancelled("request_002", "flight_agent")
    logger.info(f"Marked as cancelled in state store: {is_cancelled}")
    
    # Check partial results
    partials = state_store.get_all_partials("request_002")
    logger.info(f"Partial results preserved: {len(partials.get('flight_agent', []))} batches")
    
    return result


async def test_task_cancellation():
    """Test 3: External task cancellation (asyncio.CancelledError)."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: External Task Cancellation")
    logger.info("=" * 60)
    
    state_store = StateStore()
    agent = FlightAgent(state_store)
    
    params = {
        "origin": "ORD",
        "destination": "SEA",
        "date": "2025-12-25",
        "passengers": 3
    }
    
    # Run agent in background task
    task = asyncio.create_task(agent.run("request_003", params))
    
    # Cancel task externally after 2.5 seconds
    await asyncio.sleep(2.5)
    logger.info("🛑 Cancelling asyncio task externally...")
    task.cancel()
    
    # Wait for completion (will raise CancelledError internally, caught by BaseAgent)
    try:
        result = await task
        logger.info(f"Final Result: {result['status']}")
        if 'metadata' in result:
            logger.info(f"Flights Preserved: {result.get('metadata', {}).get('total_results', 0)}")
        else:
            logger.info(f"Flights Preserved: {len(result.get('results', []))}")
    except asyncio.CancelledError:
        logger.error("Task was cancelled (should not reach here - BaseAgent catches it)")
    
    # Check state store
    is_cancelled = state_store.is_cancelled("request_003", "flight_agent")
    logger.info(f"Marked as cancelled: {is_cancelled}")
    
    return None


async def main():
    """Run all tests sequentially."""
    logger.info("🚀 Starting FlightAgent Tests\n")
    
    # Test 1: Normal completion
    await test_complete_search()
    
    # Test 2: Agent-level cancellation
    await test_cancelled_search()
    
    # Test 3: Task-level cancellation
    await test_task_cancellation()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ All tests completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
