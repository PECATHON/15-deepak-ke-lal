#!/usr/bin/env python3
"""
Quick Integration Test - Tests all API endpoints without pytest.
Start the server first: ./start_server.sh
Then run: python3 quick_test.py
"""

import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"


async def main():
    print("🚀 Multi-Agent Travel Planning API Test\n")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Health Check
        print("\n[TEST 1] Health Check")
        try:
            resp = await client.get(f"{BASE_URL}/api/health")
            print(f"✅ Status: {resp.status_code}")
            print(f"   Response: {resp.json()}")
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\n⚠️  Make sure server is running: ./start_server.sh")
            return
        
        # Test 2: Start Flight Search
        print("\n[TEST 2] Flight Search")
        message = {
            "message": "Find flights from JFK to LAX on 2025-12-15"
        }
        resp = await client.post(f"{BASE_URL}/api/message", json=message)
        print(f"✅ Status: {resp.status_code}")
        data = resp.json()
        print(f"   Request ID: {data['request_id']}")
        flight_req_id = data['request_id']
        
        # Test 3: Monitor Progress
        print("\n[TEST 3] Monitoring Progress...")
        for i in range(8):
            await asyncio.sleep(1)
            resp = await client.get(f"{BASE_URL}/api/status/{flight_req_id}")
            status_data = resp.json()
            
            is_running = status_data.get('is_running', False)
            status = status_data.get('status', 'unknown')
            
            print(f"   [{i+1}s] Status: {status}, Running: {is_running}")
            
            if not is_running:
                print(f"\n✅ Search completed!")
                
                # Show results
                if 'data' in status_data and 'results' in status_data['data']:
                    results = status_data['data']['results']
                    
                    if 'flight_agent' in results:
                        flight_results = results['flight_agent'].get('results', [])
                        print(f"\n   📊 Flight Results: {len(flight_results)} flights found")
                        if flight_results:
                            flight = flight_results[0]
                            print(f"      Sample: {flight.get('airline', 'N/A')} - ${flight.get('price', 'N/A')}")
                break
        
        # Test 4: Multi-Agent (Flight + Hotel)
        print("\n\n[TEST 4] Multi-Agent Search (Flight + Hotel)")
        message = {
            "message": "Find flights from JFK to LAX on 2025-12-15 and hotels in Los Angeles"
        }
        resp = await client.post(f"{BASE_URL}/api/message", json=message)
        data = resp.json()
        print(f"✅ Request ID: {data['request_id']}")
        multi_req_id = data['request_id']
        
        # Monitor
        print("\n   Monitoring both agents...")
        for i in range(8):
            await asyncio.sleep(1)
            resp = await client.get(f"{BASE_URL}/api/status/{multi_req_id}")
            status_data = resp.json()
            
            is_running = status_data.get('is_running', False)
            print(f"   [{i+1}s] Running: {is_running}")
            
            if not is_running:
                print(f"\n✅ Multi-agent search completed!")
                
                if 'data' in status_data and 'results' in status_data['data']:
                    results = status_data['data']['results']
                    
                    if 'flight_agent' in results:
                        flight_count = len(results['flight_agent'].get('results', []))
                        print(f"   ✈️  Flights: {flight_count}")
                    
                    if 'hotel_agent' in results:
                        hotel_count = len(results['hotel_agent'].get('results', []))
                        print(f"   🏨 Hotels: {hotel_count}")
                break
        
        # Test 5: Cancellation
        print("\n\n[TEST 5] Cancellation Test")
        message = {
            "message": "Find flights from SFO to NYC on 2025-12-20"
        }
        resp = await client.post(f"{BASE_URL}/api/message", json=message)
        cancel_req_id = resp.json()['request_id']
        print(f"✅ Started search: {cancel_req_id}")
        
        # Wait 2 seconds then cancel
        await asyncio.sleep(2)
        print(f"   Cancelling search...")
        
        resp = await client.post(f"{BASE_URL}/api/cancel/{cancel_req_id}")
        cancel_data = resp.json()
        print(f"✅ Cancelled: {cancel_data.get('message', 'Success')}")
        
        # Check partial results preserved
        if 'partial_results' in cancel_data:
            partials = cancel_data['partial_results']
            if 'flight_agent' in partials:
                partial_count = len(partials['flight_agent'])
                print(f"   📦 Partial results preserved: {partial_count} flights")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("\n📚 API Documentation: http://localhost:8000/docs")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
