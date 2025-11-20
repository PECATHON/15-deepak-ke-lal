import asyncio
from typing import AsyncIterator, Dict, List
import httpx
from datetime import datetime, timedelta

try:
    from config import config
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config


class AmadeusHotelAPI:
    """Amadeus Hotel API integration."""
    
    def __init__(self):
        self.api_key = config.AMADEUS_API_KEY
        self.api_secret = config.AMADEUS_API_SECRET
        self.hostname = config.AMADEUS_HOSTNAME
        self.access_token = None
        self.token_expiry = None
    
    async def get_access_token(self):
        """Get OAuth2 access token from Amadeus."""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self.hostname}/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret
                }
            )
            data = response.json()
            self.access_token = data["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=data.get("expires_in", 1799) - 300)
            return self.access_token
    
    async def search_hotels(self, city_code: str, checkin: str = None, checkout: str = None):
        """Search hotels using Amadeus API."""
        token = await self.get_access_token()
        
        # Default dates if not provided
        if not checkin:
            checkin = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if not checkout:
            checkout = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            # First, get hotel list by city
            response = await client.get(
                f"https://{self.hostname}/v1/reference-data/locations/hotels/by-city",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "cityCode": city_code.upper()[:3],
                    "radius": 20,
                    "radiusUnit": "KM"
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Amadeus API error: {response.text}")
            
            hotel_data = response.json()
            hotel_ids = [h["hotelId"] for h in hotel_data.get("data", [])[:10]]
            
            if not hotel_ids:
                return []
            
            # Get hotel offers
            offers_response = await client.get(
                f"https://{self.hostname}/v3/shopping/hotel-offers",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "hotelIds": ",".join(hotel_ids[:5]),
                    "checkInDate": checkin,
                    "checkOutDate": checkout,
                    "adults": 1
                }
            )
            
            offers_data = offers_response.json()
            hotels = []
            
            for offer in offers_data.get("data", [])[:5]:
                hotel_info = offer.get("hotel", {})
                best_offer = offer.get("offers", [{}])[0]
                
                hotels.append({
                    "name": hotel_info.get("name", "Unknown Hotel"),
                    "rating": hotel_info.get("rating", "N/A"),
                    "price": float(best_offer.get("price", {}).get("total", 0)),
                    "currency": best_offer.get("price", {}).get("currency", "USD"),
                    "location": hotel_info.get("cityCode", city_code),
                    "address": hotel_info.get("address", {}).get("lines", [""])[0],
                    "checkin": checkin,
                    "checkout": checkout
                })
            
            return hotels


class SerpAPIHotelSearch:
    """Google Hotel search via SerpAPI."""
    
    def __init__(self):
        self.api_key = config.SERPAPI_KEY
    
    async def search_hotels(self, location: str, checkin: str = None, checkout: str = None):
        """Search hotels using SerpAPI Google Hotels."""
        if not checkin:
            checkin = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if not checkout:
            checkout = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_hotels",
                    "q": f"hotels in {location}",
                    "check_in_date": checkin,
                    "check_out_date": checkout,
                    "adults": "1",
                    "currency": "USD",
                    "api_key": self.api_key
                }
            )
            
            data = response.json()
            hotels = []
            
            for hotel in data.get("properties", [])[:5]:
                hotels.append({
                    "name": hotel.get("name", "Unknown Hotel"),
                    "rating": hotel.get("overall_rating", "N/A"),
                    "price": hotel.get("rate_per_night", {}).get("lowest", 0),
                    "currency": "USD",
                    "location": location,
                    "address": hotel.get("description", ""),
                    "checkin": checkin,
                    "checkout": checkout
                })
            
            return hotels


# Mock implementation for testing
async def _mock_partials(input_data: dict):
    """Yield a few partial updates to simulate streaming."""
    for i in range(2):
        await asyncio.sleep(0.7)
        yield {"step": i + 1, "note": f"Searching hotels batch {i+1}..."}


async def _mock_hotel_search(input_data: dict):
    """Stubbed hotel search for testing."""
    await asyncio.sleep(0.3)
    location = input_data.get("location", "Unknown City")
    
    return [
        {
            "name": "Demo Inn",
            "rating": 4.2,
            "price": 89.99,
            "currency": "USD",
            "location": location,
            "address": "123 Main St",
            "checkin": "2025-12-01",
            "checkout": "2025-12-03"
        },
        {
            "name": "Sample Suites",
            "rating": 4.6,
            "price": 129.99,
            "currency": "USD",
            "location": location,
            "address": "456 Park Ave",
            "checkin": "2025-12-01",
            "checkout": "2025-12-03"
        },
    ]


async def search_hotels(input_data: dict, final: bool = False) -> List[Dict]:
    """Main hotel search function with real API or mock fallback.
    
    Args:
        input_data: Dictionary with keys: location, checkin, checkout, raw
        final: If False, returns async generator for partials. If True, returns final results.
    
    Returns:
        List of hotel dictionaries or async generator for partials
    """
    if not final:
        # Return async generator for partial results
        return _mock_partials(input_data)
    
    # Check if real APIs should be used
    if config.USE_REAL_APIS:
        # Extract parameters
        location = input_data.get("location", "")
        checkin = input_data.get("checkin")
        checkout = input_data.get("checkout")
        
        # Validate we have required params
        if not location:
            # Try to parse from raw query if available
            raw = input_data.get("raw", "")
            if "in" in raw.lower() or "hotel" in raw.lower():
                # Simple extraction (in production, use LLM)
                parts = raw.lower().split()
                if "in" in parts:
                    try:
                        idx = parts.index("in")
                        if idx + 1 < len(parts):
                            location = parts[idx + 1]
                    except (ValueError, IndexError):
                        pass
        
        # Try Amadeus first
        if config.AMADEUS_API_KEY and config.AMADEUS_API_SECRET and location:
            try:
                amadeus = AmadeusHotelAPI()
                return await amadeus.search_hotels(location, checkin, checkout)
            except Exception as e:
                print(f"Amadeus API error: {e}, falling back to SerpAPI")
        
        # Try SerpAPI as fallback
        if config.SERPAPI_KEY and location:
            try:
                serp = SerpAPIHotelSearch()
                return await serp.search_hotels(location, checkin, checkout)
            except Exception as e:
                print(f"SerpAPI error: {e}, using mock data")
    
    # Fallback to mock data
    return await _mock_hotel_search(input_data)
