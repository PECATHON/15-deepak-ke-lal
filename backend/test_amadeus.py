"""Test Amadeus API credentials."""

import asyncio
import httpx
from datetime import datetime, timedelta
from config import config


async def test_amadeus_auth():
    """Test Amadeus authentication."""
    print("\n" + "="*60)
    print("TESTING AMADEUS AUTHENTICATION")
    print("="*60)
    
    print(f"API Key: {config.AMADEUS_API_KEY[:10]}...{config.AMADEUS_API_KEY[-4:]}")
    print(f"API Secret: {config.AMADEUS_API_SECRET[:10]}...{config.AMADEUS_API_SECRET[-4:]}")
    print(f"Hostname: {config.AMADEUS_HOSTNAME}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://{config.AMADEUS_HOSTNAME}/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": config.AMADEUS_API_KEY,
                    "client_secret": config.AMADEUS_API_SECRET
                }
            )
            
            print(f"\nStatus Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Authentication successful!")
                print(f"Access Token: {data['access_token'][:20]}...")
                print(f"Token Type: {data['token_type']}")
                print(f"Expires In: {data['expires_in']} seconds")
                return data['access_token']
            else:
                print(f"❌ Authentication failed: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None


async def test_amadeus_flights(token):
    """Test Amadeus flight search."""
    print("\n" + "="*60)
    print("TESTING AMADEUS FLIGHT SEARCH")
    print("="*60)
    
    if not token:
        print("❌ Skipping - no valid token")
        return False
    
    try:
        date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://{config.AMADEUS_HOSTNAME}/v2/shopping/flight-offers",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "originLocationCode": "JFK",
                    "destinationLocationCode": "LAX",
                    "departureDate": date,
                    "adults": 1,
                    "max": 5
                }
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                flights = data.get("data", [])
                print(f"✅ Found {len(flights)} flights")
                
                for i, offer in enumerate(flights[:3], 1):
                    itinerary = offer["itineraries"][0]
                    segment = itinerary["segments"][0]
                    
                    print(f"\n--- Flight {i} ---")
                    print(f"  Airline: {segment['carrierCode']}")
                    print(f"  Flight #: {segment['carrierCode']}{segment['number']}")
                    print(f"  Price: {offer['price']['total']} {offer['price']['currency']}")
                    print(f"  From: {segment['departure']['iataCode']} at {segment['departure']['at']}")
                    print(f"  To: {segment['arrival']['iataCode']} at {segment['arrival']['at']}")
                    print(f"  Duration: {itinerary['duration']}")
                    print(f"  Stops: {len(itinerary['segments']) - 1}")
                
                return True
            else:
                print(f"❌ Flight search failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_integrated_flight_search():
    """Test the integrated flight search function."""
    print("\n" + "="*60)
    print("TESTING INTEGRATED FLIGHT SEARCH")
    print("="*60)
    
    from tools.flight_api import search_flights
    
    try:
        flight_data = {
            "source": "JFK",
            "destination": "LAX",
            "date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "raw": "Find flights from JFK to LAX"
        }
        
        print("Searching for flights...")
        flights = await search_flights(flight_data, final=True)
        print(f"✅ Flight search returned {len(flights)} results")
        
        for i, flight in enumerate(flights[:3], 1):
            print(f"\n  Flight {i}:")
            print(f"    Airline: {flight.get('airline', 'N/A')}")
            print(f"    Flight #: {flight.get('flight_number', 'N/A')}")
            print(f"    From: {flight.get('from', 'N/A')}")
            print(f"    To: {flight.get('to', 'N/A')}")
            print(f"    Price: {flight.get('price', 'N/A')} {flight.get('currency', 'USD')}")
            print(f"    Departure: {flight.get('departure', 'N/A')}")
            print(f"    Duration: {flight.get('duration', 'N/A')}")
        
        return len(flights) > 0
    except Exception as e:
        print(f"❌ Flight search failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Amadeus tests."""
    print("\n" + "="*60)
    print("AMADEUS API TEST SUITE")
    print("="*60)
    
    # Test authentication
    token = await test_amadeus_auth()
    
    # Test flight search with token
    flight_result = await test_amadeus_flights(token)
    
    # Test integrated search
    integrated_result = await test_integrated_flight_search()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Amadeus Authentication: {'✅ PASS' if token else '❌ FAIL'}")
    print(f"Amadeus Flight Search: {'✅ PASS' if flight_result else '❌ FAIL'}")
    print(f"Integrated Flight Search: {'✅ PASS' if integrated_result else '❌ FAIL'}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
