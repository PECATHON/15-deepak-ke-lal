"""
Hotel API Tool - Real-time hotel search using Booking.com Rapid API.

Integrates with RapidAPI's Booking.com endpoint for live hotel data.
Falls back to mock data if API key is not configured.
"""

import asyncio
import os
from typing import Dict, Any, AsyncGenerator, Optional
import logging
from datetime import datetime, timedelta
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# RapidAPI configuration for Booking.com
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "booking-com.p.rapidapi.com"
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_HOST}/v1"


async def search_hotels_iter(params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Search hotels using Booking.com API or fallback to mock data.
    
    Args:
        params: Search parameters containing:
            - location: City or airport code (e.g., "Los Angeles", "LAX")
            - checkin: Check-in date (YYYY-MM-DD)
            - checkout: Check-out date (YYYY-MM-DD)
            - adults: Number of adults (default: 2)
            - rooms: Number of rooms (default: 1)
            
    Yields:
        Dict containing a batch of hotel results
    """
    location = params.get("location", "Los Angeles")
    checkin = params.get("checkin", "2025-12-15")
    checkout = params.get("checkout", "2025-12-17")
    adults = params.get("adults", 2)
    rooms = params.get("rooms", 1)
    
    logger.info(f"[HotelAPI] Searching hotels: {location}, {checkin} to {checkout}")
    
    # Try real API first
    if RAPIDAPI_KEY:
        async for batch in _search_booking_api(location, checkin, checkout, adults, rooms):
            yield batch
    else:
        logger.warning("[HotelAPI] Using fallback mock data (RapidAPI key not configured)")
        async for batch in _search_mock_hotels(location, checkin, checkout, adults, rooms):
            yield batch


async def _search_booking_api(
    location: str,
    checkin: str,
    checkout: str,
    adults: int,
    rooms: int
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Search hotels using real Booking.com API via RapidAPI.
    
    API Documentation: https://rapidapi.com/apidojo/api/booking
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Get destination ID from location name
            dest_response = await client.get(
                f"{RAPIDAPI_BASE_URL}/hotels/locations",
                params={"name": location, "locale": "en-us"},
                headers={
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": RAPIDAPI_HOST
                }
            )
            
            if dest_response.status_code != 200:
                logger.error(f"[HotelAPI] Location lookup failed: {dest_response.status_code}")
                raise Exception(f"Failed to lookup location: {location}")
            
            destinations = dest_response.json()
            if not destinations:
                logger.warning(f"[HotelAPI] No destination found for: {location}")
                yield {
                    "page": 1,
                    "total_pages": 1,
                    "results": [],
                    "result_count": 0,
                    "source": "booking_api"
                }
                return
            
            dest_id = destinations[0].get("dest_id")
            dest_type = destinations[0].get("dest_type", "city")
            
            logger.info(f"[HotelAPI] Found destination ID: {dest_id}")
            
            # Step 2: Search hotels
            search_response = await client.get(
                f"{RAPIDAPI_BASE_URL}/hotels/search",
                params={
                    "dest_id": dest_id,
                    "dest_type": dest_type,
                    "checkin_date": checkin,
                    "checkout_date": checkout,
                    "adults_number": adults,
                    "room_number": rooms,
                    "units": "metric",
                    "locale": "en-us",
                    "currency": "USD",
                    "order_by": "popularity",
                    "page_number": 0
                },
                headers={
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": RAPIDAPI_HOST
                }
            )
            
            if search_response.status_code == 200:
                data = search_response.json()
                hotels = data.get("result", [])
                
                if not hotels:
                    logger.warning("[HotelAPI] No hotels found from Booking.com API")
                    yield {
                        "page": 1,
                        "total_pages": 1,
                        "results": [],
                        "result_count": 0,
                        "source": "booking_api"
                    }
                    return
                
                # Transform Booking.com data to our format
                transformed_hotels = []
                for hotel in hotels[:15]:  # Limit to 15 results
                    transformed_hotels.append({
                        "hotel_id": hotel.get("hotel_id", "N/A"),
                        "name": hotel.get("hotel_name", "N/A"),
                        "address": hotel.get("address", "N/A"),
                        "city": hotel.get("city", location),
                        "latitude": hotel.get("latitude"),
                        "longitude": hotel.get("longitude"),
                        "rating": float(hotel.get("review_score", 0)),
                        "review_count": hotel.get("review_nr", 0),
                        "price_per_night": float(hotel.get("min_total_price", 0)) / max(1, int((datetime.strptime(checkout, "%Y-%m-%d") - datetime.strptime(checkin, "%Y-%m-%d")).days)),
                        "currency": hotel.get("currency_code", "USD"),
                        "image_url": hotel.get("main_photo_url", ""),
                        "distance_km": hotel.get("distance", 0),
                        "amenities": hotel.get("hotel_facilities", "").split(",")[:5] if hotel.get("hotel_facilities") else []
                    })
                
                # Return as single page (API returns all results at once)
                yield {
                    "page": 1,
                    "total_pages": 1,
                    "results": transformed_hotels,
                    "result_count": len(transformed_hotels),
                    "source": "booking_api"
                }
                
                logger.info(f"[HotelAPI] Retrieved {len(transformed_hotels)} hotels from Booking.com")
                
            else:
                logger.error(f"[HotelAPI] Booking.com API error: {search_response.status_code}")
                logger.error(f"[HotelAPI] Response: {search_response.text}")
                raise Exception(f"Booking.com API returned {search_response.status_code}")
                    
    except Exception as e:
        logger.error(f"[HotelAPI] Booking.com API exception: {e}", exc_info=True)
        raise


async def _search_mock_hotels(
    location: str,
    checkin: str,
    checkout: str,
    adults: int,
    rooms: int
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Fallback mock hotel data generator.
    Used when RapidAPI key is not configured or unavailable.
    """
    import random
    
    total_pages = 2
    results_per_page = 8
    
    hotel_chains = ["Marriott", "Hilton", "Hyatt", "Best Western", "Holiday Inn", "Radisson"]
    amenities_list = ["WiFi", "Pool", "Gym", "Parking", "Restaurant", "Spa", "Bar", "Airport Shuttle"]
    
    for page in range(1, total_pages + 1):
        # Simulate API latency
        await asyncio.sleep(1.5)
        
        hotels = []
        for i in range(results_per_page):
            chain = random.choice(hotel_chains)
            hotel_type = random.choice(["Hotel", "Suites", "Inn", "Resort"])
            
            hotels.append({
                "hotel_id": f"hotel_{page}_{i}",
                "name": f"{chain} {hotel_type} {location}",
                "address": f"{random.randint(100, 9999)} Main St, {location}",
                "city": location,
                "latitude": 34.0522 + random.uniform(-0.1, 0.1),
                "longitude": -118.2437 + random.uniform(-0.1, 0.1),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "review_count": random.randint(50, 2000),
                "price_per_night": random.randint(80, 350),
                "currency": "USD",
                "image_url": f"https://example.com/hotel_{i}.jpg",
                "distance_km": round(random.uniform(0.5, 15.0), 1),
                "amenities": random.sample(amenities_list, random.randint(3, 6))
            })
        
        yield {
            "page": page,
            "total_pages": total_pages,
            "results": hotels,
            "result_count": len(hotels),
            "source": "mock"
        }
        
        logger.info(f"[HotelAPI] Yielding mock page {page}/{total_pages} with {len(hotels)} hotels")
    
    logger.info(f"[HotelAPI] Completed mock search for {location}")
