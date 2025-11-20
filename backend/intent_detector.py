"""
Intent Detection - Extract user intent and parameters from natural language queries.

Capabilities:
- Regex-based pattern matching for flights, hotels
- Parameter extraction (locations, dates, passengers, rooms)
- Multi-intent detection (flight + hotel in same message)
- Date parsing with relative expressions ("tomorrow", "next week")
- Optional LLM fallback for complex queries
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Detects user intent and extracts parameters from natural language.
    
    Supported Intents:
    - flight: Flight search queries
    - hotel: Hotel search queries
    - Both: Multi-agent requests
    """
    
    # Airport/City code patterns
    AIRPORT_PATTERN = r'\b[A-Z]{3}\b'  # 3-letter IATA codes
    
    # Date patterns
    DATE_PATTERNS = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',  # Month DD
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}',  # Abbreviated month
    ]
    
    # Relative date expressions
    RELATIVE_DATES = {
        'today': 0,
        'tomorrow': 1,
        'next week': 7,
        'next month': 30,
    }
    
    def __init__(self, llm_fallback: bool = False):
        """
        Initialize the intent detector.
        
        Args:
            llm_fallback: Whether to use LLM for complex queries (not implemented yet)
        """
        self.llm_fallback = llm_fallback
        logger.info("[IntentDetector] Initialized")
    
    def detect(self, message: str) -> Dict[str, Any]:
        """
        Detect intent and extract parameters from user message.
        
        Args:
            message: User's natural language query
            
        Returns:
            Dict with:
                - intents: List of detected intents ["flight", "hotel"]
                - params: Extracted parameters {origin, destination, date, etc.}
                - confidence: Confidence score 0-1
        """
        message_lower = message.lower()
        
        intents = []
        params = {}
        
        # Detect flight intent
        if self._has_flight_intent(message_lower):
            intents.append("flight")
            flight_params = self._extract_flight_params(message)
            params.update(flight_params)
        
        # Detect hotel intent
        if self._has_hotel_intent(message_lower):
            intents.append("hotel")
            hotel_params = self._extract_hotel_params(message)
            params.update(hotel_params)
        
        # Calculate confidence
        confidence = self._calculate_confidence(message_lower, intents, params)
        
        result = {
            "intents": intents,
            "params": params,
            "confidence": confidence,
            "original_message": message
        }
        
        logger.info(f"[IntentDetector] Detected: {intents} (confidence: {confidence:.2f})")
        logger.debug(f"[IntentDetector] Parameters: {params}")
        
        return result
    
    def _has_flight_intent(self, message: str) -> bool:
        """Check if message contains flight-related keywords."""
        flight_keywords = [
            r'\bflight[s]?\b',
            r'\bfly\b',
            r'\bflying\b',
            r'\bairline[s]?\b',
            r'\bairfare\b',
            r'\bticket[s]?\b',
            r'\bairport\b',
        ]
        return any(re.search(pattern, message) for pattern in flight_keywords)
    
    def _has_hotel_intent(self, message: str) -> bool:
        """Check if message contains hotel-related keywords."""
        hotel_keywords = [
            r'\bhotel[s]?\b',
            r'\bstay\b',
            r'\bstaying\b',
            r'\baccommodation[s]?\b',
            r'\broom[s]?\b',
            r'\bresort[s]?\b',
            r'\blodging\b',
        ]
        return any(re.search(pattern, message) for pattern in hotel_keywords)
    
    def _extract_flight_params(self, message: str) -> Dict[str, Any]:
        """Extract flight-specific parameters."""
        params = {}
        
        # Extract origin and destination
        airports = re.findall(self.AIRPORT_PATTERN, message)
        if len(airports) >= 2:
            params["origin"] = airports[0]
            params["destination"] = airports[1]
        elif len(airports) == 1:
            # Try to find city names
            cities = self._extract_city_names(message)
            if cities:
                params["origin"] = airports[0]
                params["destination"] = cities[0] if cities[0] != airports[0] else cities[1] if len(cities) > 1 else None
        
        # Extract passengers
        passenger_match = re.search(r'(\d+)\s+(passenger[s]?|adult[s]?|people|person[s]?)', message.lower())
        if passenger_match:
            params["passengers"] = int(passenger_match.group(1))
        else:
            params["passengers"] = 1  # Default
        
        # Extract date
        date = self._extract_date(message)
        if date:
            params["date"] = date
        
        return params
    
    def _extract_hotel_params(self, message: str) -> Dict[str, Any]:
        """Extract hotel-specific parameters."""
        params = {}
        
        # Extract location (city or airport code)
        airports = re.findall(self.AIRPORT_PATTERN, message)
        cities = self._extract_city_names(message)
        
        if cities:
            params["location"] = cities[-1]  # Use last mentioned city for hotels
        elif airports:
            params["location"] = airports[-1]  # Use last airport code
        
        # Extract check-in/check-out dates
        dates = self._extract_all_dates(message)
        if len(dates) >= 2:
            params["checkin"] = dates[0]
            params["checkout"] = dates[1]
        elif len(dates) == 1:
            params["checkin"] = dates[0]
            # Default checkout: 2 days after checkin
            checkin_date = datetime.strptime(dates[0], "%Y-%m-%d")
            params["checkout"] = (checkin_date + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Extract adults
        adult_match = re.search(r'(\d+)\s+(adult[s]?|guest[s]?|people)', message.lower())
        if adult_match:
            params["adults"] = int(adult_match.group(1))
        else:
            params["adults"] = 2  # Default
        
        # Extract rooms
        room_match = re.search(r'(\d+)\s+room[s]?', message.lower())
        if room_match:
            params["rooms"] = int(room_match.group(1))
        else:
            params["rooms"] = 1  # Default
        
        return params
    
    def _extract_city_names(self, message: str) -> List[str]:
        """Extract city names from message (simple heuristic)."""
        # Common cities (expandable)
        common_cities = [
            "new york", "nyc", "los angeles", "la", "chicago", "houston", "phoenix",
            "philadelphia", "san antonio", "san diego", "dallas", "san jose",
            "austin", "jacksonville", "fort worth", "columbus", "charlotte",
            "san francisco", "indianapolis", "seattle", "denver", "boston",
            "miami", "las vegas", "detroit", "nashville", "portland", "orlando",
            "london", "paris", "tokyo", "dubai", "singapore", "hong kong", "mumbai"
        ]
        
        found_cities = []
        message_lower = message.lower()
        
        for city in common_cities:
            if re.search(r'\b' + city + r'\b', message_lower):
                found_cities.append(city.title())
        
        return found_cities
    
    def _extract_date(self, message: str) -> Optional[str]:
        """Extract first date from message."""
        dates = self._extract_all_dates(message)
        return dates[0] if dates else None
    
    def _extract_all_dates(self, message: str) -> List[str]:
        """Extract all dates from message in YYYY-MM-DD format."""
        dates = []
        message_lower = message.lower()
        
        # Check relative dates first
        for phrase, days_offset in self.RELATIVE_DATES.items():
            if phrase in message_lower:
                target_date = datetime.now() + timedelta(days=days_offset)
                dates.append(target_date.strftime("%Y-%m-%d"))
        
        # Check explicit date patterns
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse and normalize to YYYY-MM-DD
                    if re.match(r'\d{4}-\d{2}-\d{2}', match):
                        dates.append(match)
                    elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', match):
                        parsed = datetime.strptime(match, "%m/%d/%Y")
                        dates.append(parsed.strftime("%Y-%m-%d"))
                    else:
                        # Month name format
                        current_year = datetime.now().year
                        parsed = datetime.strptime(f"{match} {current_year}", "%B %d %Y" if len(match.split()[0]) > 3 else "%b %d %Y")
                        dates.append(parsed.strftime("%Y-%m-%d"))
                except:
                    continue
        
        return dates
    
    def _calculate_confidence(self, message: str, intents: List[str], params: Dict[str, Any]) -> float:
        """Calculate confidence score based on detected intents and parameters."""
        if not intents:
            return 0.0
        
        confidence = 0.5  # Base confidence for having any intent
        
        # Bonus for having parameters
        if "flight" in intents:
            if "origin" in params and "destination" in params:
                confidence += 0.2
            if "date" in params:
                confidence += 0.1
            if "passengers" in params:
                confidence += 0.05
        
        if "hotel" in intents:
            if "location" in params:
                confidence += 0.15
            if "checkin" in params:
                confidence += 0.1
            if "checkout" in params:
                confidence += 0.05
        
        return min(confidence, 1.0)
