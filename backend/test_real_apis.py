"""Test real API integrations."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import config
from tools.flight_api import AmadeusFlightAPI, SerpAPIFlightSearch, search_flights
from tools.hotel_api import AmadeusHotelAPI, SerpAPIHotelSearch, search_hotels


async def test_amadeus_auth():
    """Test Amadeus API authentication."""
    print("=" * 60)
    print("Testing Amadeus API Authentication")
    print("=" * 60)
    
    if not config.AMADEUS_API_KEY or not config.AMADEUS_API_SECRET:
        print("❌ Amadeus credentials not configured in .env")
        print("   Add AMADEUS_API_KEY and AMADEUS_API_SECRET to backend/.env")
        return False
    
    try:
        api = AmadeusFlightAPI()
        token = await api.get_access_token()
        print(f"✅ Authentication successful!")
        print(f"   Token: {token[:20]}...")
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False


async def test_amadeus_flights():
    """Test Amadeus flight search."""
    print("\n" + "=" * 60)
    print("Testing Amadeus Flight Search")
    print("=" * 60)
    
    if not config.AMADEUS_API_KEY:
        print("⏭️  Skipping - credentials not configured")
        return
    
    try:
        api = AmadeusFlightAPI()
        flights = await api.search_flights("NYC", "LAX", "2025-12-01")
        
        print(f"✅ Found {len(flights)} flights")
        for i, flight in enumerate(flights[:3], 1):
            print(f"\n   Flight {i}:")
            print(f"   - Airline: {flight['airline']} {flight.get('flight_number', '')}")
            print(f"   - Price: {flight['currency']} {flight['price']}")
            print(f"   - Route: {flight['from']} → {flight['to']}")
            print(f"   - Departure: {flight.get('departure', 'N/A')}")
    except Exception as e:
        print(f"❌ Search failed: {e}")


async def test_amadeus_hotels():
    """Test Amadeus hotel search."""
    print("\n" + "=" * 60)
    print("Testing Amadeus Hotel Search")
    print("=" * 60)
    
    if not config.AMADEUS_API_KEY:
        print("⏭️  Skipping - credentials not configured")
        return
    
    try:
        api = AmadeusHotelAPI()
        hotels = await api.search_hotels("PAR", "2025-12-01", "2025-12-03")
        
        print(f"✅ Found {len(hotels)} hotels")
        for i, hotel in enumerate(hotels[:3], 1):
            print(f"\n   Hotel {i}:")
            print(f"   - Name: {hotel['name']}")
            print(f"   - Rating: {hotel.get('rating', 'N/A')}")
            print(f"   - Price: {hotel['currency']} {hotel['price']}")
            print(f"   - Location: {hotel['location']}")
    except Exception as e:
        print(f"❌ Search failed: {e}")


async def test_serpapi_flights():
    """Test SerpAPI flight search."""
    print("\n" + "=" * 60)
    print("Testing SerpAPI Flight Search")
    print("=" * 60)
    
    if not config.SERPAPI_KEY:
        print("⏭️  Skipping - SERPAPI_KEY not configured")
        return
    
    try:
        api = SerpAPIFlightSearch()
        flights = await api.search_flights("NYC", "LAX", "2025-12-01")
        
        print(f"✅ Found {len(flights)} flights")
        for i, flight in enumerate(flights[:3], 1):
            print(f"\n   Flight {i}:")
            print(f"   - Airline: {flight['airline']}")
            print(f"   - Price: ${flight['price']}")
            print(f"   - Duration: {flight['duration']}")
    except Exception as e:
        print(f"❌ Search failed: {e}")


async def test_integrated_search():
    """Test the integrated search_flights function."""
    print("\n" + "=" * 60)
    print("Testing Integrated Search Function")
    print("=" * 60)
    print(f"USE_REAL_APIS = {config.USE_REAL_APIS}")
    
    input_data = {
        "source": "NYC",
        "destination": "LAX",
        "date": "2025-12-01",
        "raw": "Find flights from NYC to LAX on Dec 1"
    }
    
    print(f"\nSearching flights: {input_data['source']} → {input_data['destination']}")
    
    try:
        results = await search_flights(input_data, final=True)
        
        print(f"✅ Found {len(results)} results")
        for i, flight in enumerate(results[:2], 1):
            print(f"\n   Result {i}:")
            print(f"   - Airline: {flight.get('airline', 'N/A')}")
            print(f"   - Price: {flight.get('currency', '$')} {flight.get('price', 0)}")
            print(f"   - From: {flight.get('from', 'N/A')} To: {flight.get('to', 'N/A')}")
    except Exception as e:
        print(f"❌ Search failed: {e}")


async def test_integrated_hotels():
    """Test the integrated search_hotels function."""
    print("\n" + "=" * 60)
    print("Testing Integrated Hotel Search")
    print("=" * 60)
    
    input_data = {
        "location": "PAR",
        "checkin": "2025-12-01",
        "checkout": "2025-12-03",
        "raw": "Find hotels in Paris"
    }
    
    print(f"\nSearching hotels in: {input_data['location']}")
    
    try:
        results = await search_hotels(input_data, final=True)
        
        print(f"✅ Found {len(results)} results")
        for i, hotel in enumerate(results[:2], 1):
            print(f"\n   Result {i}:")
            print(f"   - Name: {hotel.get('name', 'N/A')}")
            print(f"   - Rating: {hotel.get('rating', 'N/A')}")
            print(f"   - Price: {hotel.get('currency', '$')} {hotel.get('price', 0)}")
    except Exception as e:
        print(f"❌ Search failed: {e}")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🔧 REAL API INTEGRATION TESTS")
    print("=" * 60)
    print()
    
    # Show configuration
    print("Configuration Status:")
    print(f"  - Amadeus API: {'✅ Configured' if config.AMADEUS_API_KEY else '❌ Not configured'}")
    print(f"  - SerpAPI: {'✅ Configured' if config.SERPAPI_KEY else '❌ Not configured'}")
    print(f"  - USE_REAL_APIS: {config.USE_REAL_APIS}")
    print()
    
    if not config.AMADEUS_API_KEY and not config.SERPAPI_KEY:
        print("⚠️  No API credentials configured!")
        print("    Tests will use mock data.")
        print()
        print("To test real APIs:")
        print("1. Get API keys from https://developers.amadeus.com/register")
        print("2. Add them to backend/.env:")
        print("   AMADEUS_API_KEY=your_key")
        print("   AMADEUS_API_SECRET=your_secret")
        print("   USE_REAL_APIS=True")
        print()
    
    # Run tests
    if config.AMADEUS_API_KEY:
        await test_amadeus_auth()
        await test_amadeus_flights()
        await test_amadeus_hotels()
    
    if config.SERPAPI_KEY:
        await test_serpapi_flights()
    
    # Always test integrated functions
    await test_integrated_search()
    await test_integrated_hotels()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
