"""
Flight API Tool - Real-time flight search using Amadeus API.

Integrates with Amadeus Flight Offers Search API for live flight data.
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

# Amadeus API configuration
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
AMADEUS_BASE_URL = "https://test.api.amadeus.com"


class AmadeusAuth:
    """Handle Amadeus API authentication and token management."""
    
    def __init__(self):
        self.api_key = AMADEUS_API_KEY
        self.api_secret = AMADEUS_API_SECRET
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    async def get_access_token(self) -> Optional[str]:
        """Get or refresh the Amadeus access token."""
        if not self.api_key or not self.api_secret:
            logger.warning("[AmadeusAuth] API credentials not configured")
            return None
        
        # Return cached token if still valid
        if self.access_token and self.token_expires_at:
            if datetime.utcnow() < self.token_expires_at:
                return self.access_token
        
        # Request new token
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{AMADEUS_BASE_URL}/v1/security/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.api_key,
                        "client_secret": self.api_secret
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data["access_token"]
                    expires_in = data.get("expires_in", 1800)
                    self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                    logger.info("[AmadeusAuth] Access token obtained successfully")
                    return self.access_token
                else:
                    logger.error(f"[AmadeusAuth] Failed to get token: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"[AmadeusAuth] Token request error: {e}")
            return None


# Global auth instance
_auth = AmadeusAuth()


async def search_flights_iter(params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Search flights using Amadeus API or fallback to mock data.
    
    Args:
        params: Search parameters containing:
            - origin: IATA airport code (e.g., "JFK")
            - destination: IATA airport code (e.g., "LAX")
            - date: Departure date (YYYY-MM-DD)
            - passengers: Number of passengers (adults)
            
    Yields:
        Dict containing a batch of flight results
    """
    origin = params.get("origin", "NYC")
    destination = params.get("destination", "LAX")
    date = params.get("date", "2025-12-01")
    passengers = params.get("passengers", 1)
    
    logger.info(f"[FlightAPI] Searching flights: {origin} -> {destination} on {date}")
    
    # Try real API first
    token = await _auth.get_access_token()
    
    if token:
        async for batch in _search_amadeus_api(origin, destination, date, passengers, token):
            yield batch
    else:
        logger.warning("[FlightAPI] Using fallback mock data (Amadeus API not configured)")
        async for batch in _search_mock_data(origin, destination, date, passengers):
            yield batch


async def _search_amadeus_api(
    origin: str,
    destination: str,
    date: str,
    passengers: int,
    token: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Search flights using real Amadeus API.
    
    API Documentation: https://developers.amadeus.com/self-service/category/flights
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Amadeus Flight Offers Search API
            response = await client.get(
                f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers",
                params={
                    "originLocationCode": origin,
                    "destinationLocationCode": destination,
                    "departureDate": date,
                    "adults": passengers,
                    "max": 15,  # Max results per request
                    "currencyCode": "USD"
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                flight_offers = data.get("data", [])
                
                if not flight_offers:
                    logger.warning("[FlightAPI] No flights found from Amadeus API")
                    yield {
                        "page": 1,
                        "total_pages": 1,
                        "results": [],
                        "result_count": 0,
                        "source": "amadeus"
                    }
                    return
                
                # Transform Amadeus data to our format
                transformed_flights = []
                for offer in flight_offers:
                    # Extract first itinerary and segment
                    itinerary = offer.get("itineraries", [{}])[0]
                    segment = itinerary.get("segments", [{}])[0]
                    
                    transformed_flights.append({
                        "flight_number": segment.get("number", "N/A"),
                        "airline": segment.get("carrierCode", "N/A"),
                        "origin": segment.get("departure", {}).get("iataCode", origin),
                        "destination": segment.get("arrival", {}).get("iataCode", destination),
                        "departure_time": segment.get("departure", {}).get("at", "N/A"),
                        "arrival_time": segment.get("arrival", {}).get("at", "N/A"),
                        "duration_minutes": _parse_duration(itinerary.get("duration", "PT0M")),
                        "price_usd": float(offer.get("price", {}).get("total", 0)),
                        "seats_available": offer.get("numberOfBookableSeats", 0),
                        "stops": len(itinerary.get("segments", [])) - 1,
                        "offer_id": offer.get("id", "")
                    })
                
                # Return as single page (Amadeus returns all results at once)
                yield {
                    "page": 1,
                    "total_pages": 1,
                    "results": transformed_flights,
                    "result_count": len(transformed_flights),
                    "source": "amadeus"
                }
                
                logger.info(f"[FlightAPI] Retrieved {len(transformed_flights)} flights from Amadeus")
                
            else:
                logger.error(f"[FlightAPI] Amadeus API error: {response.status_code}")
                logger.error(f"[FlightAPI] Response: {response.text}")
                # Fallback to mock
                async for batch in _search_mock_data(origin, destination, date, passengers):
                    yield batch
                    
    except Exception as e:
        logger.error(f"[FlightAPI] Amadeus API exception: {e}", exc_info=True)
        # Fallback to mock
        async for batch in _search_mock_data(origin, destination, date, passengers):
            yield batch


async def _search_mock_data(
    origin: str,
    destination: str,
    date: str,
    passengers: int
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Fallback mock flight data generator.
    Used when Amadeus API is not configured or unavailable.
    """
    import random
    
    total_pages = 3
    results_per_page = 5
    airlines = ["Delta", "United", "American", "Southwest", "JetBlue"]
    
    for page in range(1, total_pages + 1):
        # Simulate API latency
        await asyncio.sleep(1.5)
        
        flights = []
        for i in range(results_per_page):
            airline = random.choice(airlines)
            flight_num = f"{airline[:2].upper()}{random.randint(100, 999)}"
            price = random.randint(150, 800)
            duration_hours = random.randint(2, 8)
            
            flights.append({
                "flight_number": flight_num,
                "airline": airline,
                "origin": origin,
                "destination": destination,
                "departure_time": f"{date}T{random.randint(6, 20):02d}:{random.choice(['00', '30'])}:00",
                "arrival_time": f"{date}T{random.randint(6, 20):02d}:{random.choice(['00', '30'])}:00",
                "duration_minutes": duration_hours * 60,
                "price_usd": price,
                "seats_available": random.randint(1, 50),
                "stops": random.choice([0, 1, 2])
            })
        
        yield {
            "page": page,
            "total_pages": total_pages,
            "results": flights,
            "result_count": len(flights),
            "source": "mock"
        }
        
        logger.info(f"[FlightAPI] Yielding mock page {page}/{total_pages} with {len(flights)} flights")
    
    logger.info(f"[FlightAPI] Completed mock search for {origin} -> {destination}")


def _parse_duration(duration_str: str) -> int:
    """
    Parse ISO 8601 duration to minutes.
    Example: "PT2H30M" -> 150 minutes
    """
    try:
        hours = 0
        minutes = 0
        
        if "H" in duration_str:
            hours = int(duration_str.split("PT")[1].split("H")[0])
        if "M" in duration_str:
            minutes = int(duration_str.split("M")[0].split("H")[-1] if "H" in duration_str else duration_str.split("PT")[1].split("M")[0])
        
        return hours * 60 + minutes
    except:
        return 0
