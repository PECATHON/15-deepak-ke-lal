"""Test script to verify real API integrations."""

import asyncio
import httpx
from datetime import datetime, timedelta
from config import config


async def test_aviationstack_api():
    """Test AviationStack Flight API."""
    print("\n" + "="*60)
    print("TESTING AVIATIONSTACK FLIGHT API")
    print("="*60)
    
    api_key = config.AVIATIONSTACK_KEY
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test with real airport codes
            params = {
                "access_key": api_key,
                "dep_iata": "JFK",
                "arr_iata": "LAX",
                "limit": 3
            }
            
            print(f"\nRequest URL: http://api.aviationstack.com/v1/flights")
            print(f"Parameters: {params}")
            
            response = await client.get(
                "http://api.aviationstack.com/v1/flights",
                params=params
            )
            
            print(f"\nStatus Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check pagination info
                if "pagination" in data:
                    print(f"\nPagination Info:")
                    print(f"  Limit: {data['pagination'].get('limit')}")
                    print(f"  Offset: {data['pagination'].get('offset')}")
                    print(f"  Count: {data['pagination'].get('count')}")
                    print(f"  Total: {data['pagination'].get('total')}")
                
                # Display flight results
                flights = data.get("data", [])
                print(f"\n✅ Found {len(flights)} flights")
                
                for i, flight in enumerate(flights[:3], 1):
                    print(f"\n--- Flight {i} ---")
                    print(f"  Flight Number: {flight.get('flight', {}).get('iata', 'N/A')}")
                    print(f"  Airline: {flight.get('airline', {}).get('name', 'Unknown')}")
                    print(f"  From: {flight.get('departure', {}).get('iata', 'N/A')} - {flight.get('departure', {}).get('airport', 'N/A')}")
                    print(f"  To: {flight.get('arrival', {}).get('iata', 'N/A')} - {flight.get('arrival', {}).get('airport', 'N/A')}")
                    print(f"  Departure: {flight.get('departure', {}).get('scheduled', 'N/A')}")
                    print(f"  Arrival: {flight.get('arrival', {}).get('scheduled', 'N/A')}")
                    print(f"  Status: {flight.get('flight_status', 'N/A')}")
                
                return True
            else:
                print(f"❌ Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False


async def test_rapidapi_booking():
    """Test RapidAPI Booking.com Hotel API."""
    print("\n" + "="*60)
    print("TESTING RAPIDAPI BOOKING.COM HOTEL API")
    print("="*60)
    
    api_key = config.RAPIDAPI_KEY
    host = config.RAPIDAPI_HOTEL_HOST
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"Host: {host}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First, test getting locations (simpler endpoint)
            print("\n--- Testing Location Search ---")
            
            location_response = await client.get(
                f"https://{host}/v1/hotels/locations",
                headers={
                    "x-rapidapi-key": api_key,
                    "x-rapidapi-host": host
                },
                params={
                    "locale": "en-gb",
                    "name": "London"
                }
            )
            
            print(f"Status Code: {location_response.status_code}")
            
            if location_response.status_code == 200:
                locations = location_response.json()
                print(f"✅ Found {len(locations)} locations")
                
                if locations:
                    # Show first few locations
                    for i, loc in enumerate(locations[:3], 1):
                        print(f"\n  Location {i}:")
                        print(f"    Name: {loc.get('name', 'N/A')}")
                        print(f"    Dest ID: {loc.get('dest_id', 'N/A')}")
                        print(f"    Dest Type: {loc.get('dest_type', 'N/A')}")
                        print(f"    Country: {loc.get('country', 'N/A')}")
                    
                    # Now test hotel search with first location
                    if locations:
                        dest_id = locations[0].get('dest_id', '-2601889')  # London default
                        
                        print(f"\n--- Testing Hotel Search for Dest ID: {dest_id} ---")
                        
                        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                        checkout = (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d")
                        
                        hotel_response = await client.get(
                            f"https://{host}/v1/hotels/search",
                            headers={
                                "x-rapidapi-key": api_key,
                                "x-rapidapi-host": host
                            },
                            params={
                                "locale": "en-gb",
                                "checkout_date": checkout,
                                "checkin_date": checkin,
                                "filter_by_currency": "USD",
                                "dest_id": dest_id,
                                "dest_type": "city",
                                "adults_number": 1,
                                "order_by": "popularity",
                                "units": "metric",
                                "room_number": 1,
                                "page_number": 0
                            }
                        )
                        
                        print(f"Status Code: {hotel_response.status_code}")
                        
                        if hotel_response.status_code == 200:
                            hotel_data = hotel_response.json()
                            hotels = hotel_data.get("result", [])
                            print(f"✅ Found {len(hotels)} hotels")
                            
                            for i, hotel in enumerate(hotels[:3], 1):
                                print(f"\n--- Hotel {i} ---")
                                print(f"  Name: {hotel.get('hotel_name', 'N/A')}")
                                print(f"  Address: {hotel.get('address', 'N/A')}")
                                print(f"  Rating: {hotel.get('review_score', 'N/A')}/10")
                                print(f"  Price: {hotel.get('min_total_price', 'N/A')} {hotel.get('currency_code', 'USD')}")
                                print(f"  Checkin: {hotel.get('checkin', {}).get('from', 'N/A')}")
                                print(f"  Checkout: {hotel.get('checkout', {}).get('until', 'N/A')}")
                            
                            return True
                        else:
                            print(f"❌ Hotel Search Error: {hotel_response.text}")
                            return False
                
                return True
            else:
                print(f"❌ Location Search Error: {location_response.text}")
                
                # Show response headers for debugging
                print("\nResponse Headers:")
                for key, value in location_response.headers.items():
                    print(f"  {key}: {value}")
                
                return False
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_integrated_search():
    """Test the integrated search functions from our modules."""
    print("\n" + "="*60)
    print("TESTING INTEGRATED SEARCH FUNCTIONS")
    print("="*60)
    
    from tools.flight_api import search_flights
    from tools.hotel_api import search_hotels
    
    # Test flight search
    print("\n--- Testing Flight Search Integration ---")
    try:
        flight_data = {
            "source": "JFK",
            "destination": "LAX",
            "date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "raw": "Find flights from JFK to LAX"
        }
        
        flights = await search_flights(flight_data, final=True)
        print(f"✅ Flight search returned {len(flights)} results")
        
        for i, flight in enumerate(flights[:2], 1):
            print(f"\n  Flight {i}:")
            print(f"    Airline: {flight.get('airline', 'N/A')}")
            print(f"    Flight #: {flight.get('flight_number', 'N/A')}")
            print(f"    From: {flight.get('from', 'N/A')}")
            print(f"    To: {flight.get('to', 'N/A')}")
            print(f"    Price: {flight.get('price', 'N/A')} {flight.get('currency', 'USD')}")
    except Exception as e:
        print(f"❌ Flight search failed: {str(e)}")
    
    # Test hotel search
    print("\n--- Testing Hotel Search Integration ---")
    try:
        hotel_data = {
            "location": "London",
            "checkin": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "checkout": (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d"),
            "raw": "Find hotels in London"
        }
        
        hotels = await search_hotels(hotel_data, final=True)
        print(f"✅ Hotel search returned {len(hotels)} results")
        
        for i, hotel in enumerate(hotels[:2], 1):
            print(f"\n  Hotel {i}:")
            print(f"    Name: {hotel.get('name', 'N/A')}")
            print(f"    Location: {hotel.get('location', 'N/A')}")
            print(f"    Rating: {hotel.get('rating', 'N/A')}")
            print(f"    Price: {hotel.get('price', 'N/A')} {hotel.get('currency', 'USD')}")
    except Exception as e:
        print(f"❌ Hotel search failed: {str(e)}")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("REAL API INTEGRATION TEST SUITE")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  USE_REAL_APIS: {config.USE_REAL_APIS}")
    print(f"  AVIATIONSTACK_KEY: {'✅ Set' if config.AVIATIONSTACK_KEY else '❌ Missing'}")
    print(f"  RAPIDAPI_KEY: {'✅ Set' if config.RAPIDAPI_KEY else '❌ Missing'}")
    
    results = {
        "aviationstack": False,
        "rapidapi": False
    }
    
    # Test AviationStack
    results["aviationstack"] = await test_aviationstack_api()
    
    # Test RapidAPI Booking.com
    results["rapidapi"] = await test_rapidapi_booking()
    
    # Test integrated functions
    await test_integrated_search()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"AviationStack Flight API: {'✅ PASS' if results['aviationstack'] else '❌ FAIL'}")
    print(f"RapidAPI Booking.com API: {'✅ PASS' if results['rapidapi'] else '❌ FAIL'}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
