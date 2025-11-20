"""Quick test to debug the NYC to London query."""

import asyncio
from tools.flight_api import search_flights

async def test_nyc_london():
    print("Testing: Chandigarh to Delhi")
    
    # Test with different variations
    test_cases = [
        {"source": "Chandigarh", "destination": "Delhi", "raw": "flights from Chandigarh to Delhi"},
        {"source": "CHD", "destination": "DEL", "raw": "flights from CHD to DEL"},
        {"source": "IXC", "destination": "DEL", "raw": "flights from IXC to DEL"},
    ]
    
    for i, data in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Source: {data['source']}, Dest: {data['destination']}")
        
        try:
            flights = await search_flights(data, final=True)
            print(f"Result: {len(flights)} flights found")
            
            if flights:
                for j, flight in enumerate(flights[:3], 1):
                    print(f"\nFlight {j}:")
                    print(f"  {flight.get('airline')} {flight.get('flight_number')}")
                    print(f"  {flight.get('from')} -> {flight.get('to')}")
                    print(f"  Price: {flight.get('price')} {flight.get('currency')}")
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_nyc_london())
