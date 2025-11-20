"""
Integration Test - End-to-end workflow testing.

Tests:
1. Message processing → Coordinator → Multi-agent execution
2. Partial result streaming
3. Cancellation during execution
4. Final result aggregation
"""

import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000"


async def test_end_to_end():
    """Test complete workflow with FastAPI endpoints."""
    
    print("🧪 Integration Test - Multi-Agent Travel Planning\n")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("\n[1] Testing health endpoint...")
        response = await client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print(f"✅ Health check passed: {response.json()['status']}")
        
        # Test 2: Start search (flight + hotel)
        print("\n[2] Starting multi-agent search...")
        message_data = {
            "message": "Find flights from JFK to LAX on 2025-12-15 and hotels in Los Angeles"
        }
        response = await client.post(f"{BASE_URL}/api/message", json=message_data)
        assert response.status_code == 200
        
        result = response.json()
        request_id = result["request_id"]
        print(f"✅ Search started: {request_id}")
        print(f"   Status: {result['status']}")
        
        # Test 3: Poll for status (check partial results)
        print("\n[3] Monitoring progress...")
        for i in range(10):
            await asyncio.sleep(1)
            
            response = await client.get(f"{BASE_URL}/api/status/{request_id}")
            assert response.status_code == 200
            
            status = response.json()
            is_running = status["is_running"]
            
            print(f"   [{i+1}] Running: {is_running}, Status: {status['status']}")
            
            # Show partial results if available
            if "partials" in status["data"]:
                partials = status["data"]["partials"]
                for agent, agent_partials in partials.items():
                    print(f"      {agent}: {len(agent_partials)} partial batches")
            
            if not is_running:
                print(f"   ✅ Search completed!")
                break
        
        # Test 4: Get final results
        print("\n[4] Final results:")
        response = await client.get(f"{BASE_URL}/api/status/{request_id}")
        final_status = response.json()
        
        if "results" in final_status["data"]:
            results = final_status["data"]["results"]
            
            if "flight_agent" in results:
                flight_count = results["flight_agent"]["metadata"]["total_results"]
                print(f"   ✅ Flights: {flight_count}")
            
            if "hotel_agent" in results:
                hotel_count = results["hotel_agent"]["metadata"]["total_results"]
                print(f"   ✅ Hotels: {hotel_count}")
        
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")


async def test_cancellation():
    """Test cancellation during search."""
    
    print("\n\n🧪 Cancellation Test\n")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Start search
        print("\n[1] Starting search...")
        message_data = {
            "message": "Find flights from NYC to Miami tomorrow and hotels"
        }
        response = await client.post(f"{BASE_URL}/api/message", json=message_data)
        request_id = response.json()["request_id"]
        print(f"✅ Search started: {request_id}")
        
        # Wait a bit
        print("\n[2] Waiting 2 seconds...")
        await asyncio.sleep(2)
        
        # Cancel
        print("\n[3] Cancelling search...")
        response = await client.post(f"{BASE_URL}/api/cancel/{request_id}")
        assert response.status_code == 200
        
        cancel_result = response.json()
        print(f"✅ Cancellation successful")
        print(f"   Status: {cancel_result['status']}")
        
        if "partial_results" in cancel_result:
            print(f"   Partial results preserved:")
            for agent, partials in cancel_result["partial_results"].items():
                print(f"      {agent}: {len(partials)} batches")
        
        print("\n" + "=" * 60)
        print("✅ Cancellation test passed!")


if __name__ == "__main__":
    print("\n🚀 Starting Integration Tests")
    print("Make sure FastAPI server is running on http://localhost:8000\n")
    
    try:
        asyncio.run(test_end_to_end())
        asyncio.run(test_cancellation())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
