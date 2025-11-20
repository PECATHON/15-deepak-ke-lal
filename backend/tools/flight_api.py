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


# City name to IATA code mapping
CITY_TO_IATA = {
    # US Cities
    "nyc": "JFK", "new york": "JFK", "newyork": "JFK",
    "los angeles": "LAX", "la": "LAX", "losangeles": "LAX",
    "chicago": "ORD",
    "san francisco": "SFO", "sf": "SFO", "sanfrancisco": "SFO",
    "miami": "MIA",
    "boston": "BOS",
    "seattle": "SEA",
    "las vegas": "LAS", "vegas": "LAS", "lasvegas": "LAS",
    "washington": "DCA", "dc": "DCA",
    
    # International
    "london": "LHR",
    "paris": "CDG",
    "tokyo": "NRT",
    "dubai": "DXB",
    "singapore": "SIN",
    "hong kong": "HKG", "hongkong": "HKG",
    "sydney": "SYD",
    
    # Indian Cities
    "mumbai": "BOM",
    "delhi": "DEL", "newdelhi": "DEL", "new delhi": "DEL",
    "bangalore": "BLR", "bengaluru": "BLR",
    "chandigarh": "IXC", "chd": "IXC",
    "hyderabad": "HYD",
    "chennai": "MAA",
    "kolkata": "CCU",
    "pune": "PNQ",
    "ahmedabad": "AMD",
    "goa": "GOI",
    "jaipur": "JAI",
    "kochi": "COK", "cochin": "COK",
    "lucknow": "LKO",
    "indore": "IDR",
    "bhopal": "BHO",
}


def normalize_airport_code(location: str) -> str:
    """Convert city name to IATA code or return as-is if already valid."""
    if not location:
        return ""
    
    location_lower = location.lower().strip()
    
    # Check if it's already a 3-letter IATA code
    if len(location) == 3 and location.isalpha():
        return location.upper()
    
    # Try to find in mapping
    if location_lower in CITY_TO_IATA:
        return CITY_TO_IATA[location_lower]
    
    # Default: take first 3 letters and uppercase
    return location[:3].upper()


class AmadeusFlightAPI:
    """Amadeus Flight API integration."""
    
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
            # Token expires in 1799 seconds, refresh 5 min before
            self.token_expiry = datetime.now() + timedelta(seconds=data.get("expires_in", 1799) - 300)
            return self.access_token
    
    async def search_flights(self, origin: str, destination: str, date: str = None, adults: int = 1):
        """Search flights using Amadeus API."""
        token = await self.get_access_token()
        
        # Normalize airport codes
        origin_code = normalize_airport_code(origin)
        dest_code = normalize_airport_code(destination)
        
        # Default to 7 days from now if no date provided
        if not date:
            date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://{self.hostname}/v2/shopping/flight-offers",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "originLocationCode": origin_code,
                    "destinationLocationCode": dest_code,
                    "departureDate": date,
                    "adults": adults,
                    "max": 5  # Limit results
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Amadeus API error ({response.status_code}): {response.text}")
            
            data = response.json()
            flights = []
            
            for offer in data.get("data", [])[:5]:
                itinerary = offer["itineraries"][0]
                segment = itinerary["segments"][0]
                
                flights.append({
                    "airline": segment["carrierCode"],
                    "flight_number": f"{segment['carrierCode']}{segment['number']}",
                    "price": float(offer["price"]["total"]),
                    "currency": offer["price"]["currency"],
                    "from": segment["departure"]["iataCode"],
                    "to": segment["arrival"]["iataCode"],
                    "departure": segment["departure"]["at"],
                    "arrival": segment["arrival"]["at"],
                    "duration": itinerary["duration"],
                    "stops": len(itinerary["segments"]) - 1
                })
            
            return flights


class AviationStackFlightAPI:
    """AviationStack Flight API integration."""
    
    def __init__(self):
        self.api_key = config.AVIATIONSTACK_KEY
    
    async def search_flights(self, origin: str, destination: str, date: str = None):
        """Search flights using AviationStack API."""
        if not date:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://api.aviationstack.com/v1/flights",
                params={
                    "access_key": self.api_key,
                    "dep_iata": origin.upper()[:3],
                    "arr_iata": destination.upper()[:3],
                    "flight_date": date,
                    "limit": 5
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"AviationStack API error: {response.text}")
            
            data = response.json()
            flights = []
            
            for flight in data.get("data", [])[:5]:
                departure = flight.get("departure", {})
                arrival = flight.get("arrival", {})
                airline = flight.get("airline", {})
                
                flights.append({
                    "airline": airline.get("name", "Unknown"),
                    "flight_number": flight.get("flight", {}).get("iata", "N/A"),
                    "price": 199.99,  # AviationStack doesn't provide pricing
                    "currency": "USD",
                    "from": departure.get("iata", origin.upper()[:3]),
                    "to": arrival.get("iata", destination.upper()[:3]),
                    "departure": departure.get("scheduled", ""),
                    "arrival": arrival.get("scheduled", ""),
                    "duration": "N/A",
                    "stops": 0
                })
            
            return flights


class SerpAPIFlightSearch:
    """Google Flight search via SerpAPI."""
    
    def __init__(self):
        self.api_key = config.SERPAPI_KEY
    
    async def search_flights(self, origin: str, destination: str, date: str = None):
        """Search flights using SerpAPI Google Flights."""
        if not date:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_flights",
                    "departure_id": origin.upper()[:3],
                    "arrival_id": destination.upper()[:3],
                    "outbound_date": date,
                    "type": "1",  # One way
                    "api_key": self.api_key
                }
            )
            
            data = response.json()
            flights = []
            
            for flight in data.get("best_flights", [])[:5]:
                flights.append({
                    "airline": flight["flights"][0]["airline"],
                    "flight_number": flight["flights"][0].get("flight_number", "N/A"),
                    "price": flight["price"],
                    "currency": "USD",
                    "from": origin.upper()[:3],
                    "to": destination.upper()[:3],
                    "departure": flight["flights"][0]["departure_airport"]["time"],
                    "arrival": flight["flights"][0]["arrival_airport"]["time"],
                    "duration": flight["total_duration"],
                    "stops": len(flight["flights"]) - 1
                })
            
            return flights


# Mock implementation for testing
async def _mock_partials(input_data: dict):
    """Yield a few partial updates to simulate streaming."""
    for i in range(2):
        await asyncio.sleep(0.8)
        yield {"step": i + 1, "note": f"Searching flights batch {i+1}..."}


async def _mock_flight_search(input_data: dict):
    """Stubbed flight search for testing - Enhanced with realistic data."""
    await asyncio.sleep(0.5)
    source = input_data.get("source", "NYC")
    dest = input_data.get("destination", "LAX")
    date = input_data.get("date", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
    
    # Generate more realistic mock data
    airlines = ["United Airlines", "Delta Air Lines", "American Airlines", "JetBlue Airways", "Southwest Airlines"]
    
    flights = []
    for i in range(5):
        base_price = 199.99 + (i * 50)
        dep_hour = 8 + (i * 2)
        duration_minutes = 210 + (i * 15)
        
        flights.append({
            "airline": airlines[i % len(airlines)],
            "flight_number": f"{airlines[i % len(airlines)][:2].upper()}{1230 + i}",
            "price": round(base_price, 2),
            "currency": "USD",
            "from": source[:3].upper(),
            "to": dest[:3].upper(),
            "departure": f"{date}T{dep_hour:02d}:00:00",
            "arrival": f"{date}T{dep_hour + duration_minutes//60:02d}:{duration_minutes%60:02d}:00",
            "duration": f"{duration_minutes//60}h {duration_minutes%60}m",
            "stops": i % 2
        })
    
    return flights


async def search_flights(input_data: dict, final: bool = False) -> List[Dict]:
    """Main flight search function with real API or mock fallback.
    
    Args:
        input_data: Dictionary with keys: source, destination, date, raw
        final: If False, returns async generator for partials. If True, returns final results.
    
    Returns:
        List of flight dictionaries or async generator for partials
    """
    if not final:
        # Return async generator for partial results
        return _mock_partials(input_data)
    
    # Check if real APIs should be used
    if config.USE_REAL_APIS:
        # Extract parameters
        source = input_data.get("source", "")
        destination = input_data.get("destination", "")
        date = input_data.get("date")
        
        # Validate we have required params
        if not source or not destination:
            # Try to parse from raw query if available
            raw = input_data.get("raw", "")
            if "from" in raw.lower() and "to" in raw.lower():
                # Simple extraction (in production, use LLM)
                parts = raw.lower().split()
                try:
                    from_idx = parts.index("from")
                    to_idx = parts.index("to")
                    if from_idx + 1 < len(parts):
                        source = parts[from_idx + 1]
                    if to_idx + 1 < len(parts):
                        destination = parts[to_idx + 1]
                except (ValueError, IndexError):
                    pass
        
        # Try AviationStack first
        if config.AVIATIONSTACK_KEY:
            try:
                aviation = AviationStackFlightAPI()
                return await aviation.search_flights(source, destination, date)
            except Exception as e:
                print(f"AviationStack API error: {e}, falling back to Amadeus")
        
        # Try Amadeus as fallback
        if config.AMADEUS_API_KEY and config.AMADEUS_API_SECRET:
            try:
                amadeus = AmadeusFlightAPI()
                return await amadeus.search_flights(source, destination, date)
            except Exception as e:
                print(f"Amadeus API error: {e}, falling back to SerpAPI")
        
        # Try SerpAPI as last fallback
        if config.SERPAPI_KEY:
            try:
                serp = SerpAPIFlightSearch()
                return await serp.search_flights(source, destination, date)
            except Exception as e:
                print(f"SerpAPI error: {e}, using mock data")
    
    # Fallback to mock data
    return await _mock_flight_search(input_data)
