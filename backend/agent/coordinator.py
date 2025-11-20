import asyncio
from typing import Dict, Any, Optional

try:
    from .flight_agent import FlightAgent
    from .hotel_agent import HotelAgent
except ImportError:
    from flight_agent import FlightAgent
    from hotel_agent import HotelAgent


class Coordinator:
    """Coordinator that routes intents to Flight/Hotel agents.

    Intent detection uses keyword matching by default. When an OpenAI API key
    is configured, it can use LLM-based parsing for better accuracy.
    """

    def __init__(self, use_llm: bool = False):
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.use_llm = use_llm

    def detect_intent(self, message: str) -> Dict[str, Any]:
        """Detect user intent and extract parameters.
        
        Returns a dict mapping agent names to their input payloads.
        """
        if self.use_llm:
            return self._detect_intent_llm(message)
        return self._detect_intent_keywords(message)

    def _detect_intent_keywords(self, message: str) -> Dict[str, Any]:
        """Keyword-based intent detection (fast, no API calls)."""
        msg = message.lower()
        wants_flight = "flight" in msg or "fly" in msg or "ticket" in msg
        wants_hotel = "hotel" in msg or "stay" in msg or "room" in msg

        payloads = {}
        if wants_flight:
            # Simple extraction: look for common patterns
            # In production, use regex or NLP to extract source/dest/date
            payloads["flight"] = {
                "raw": message,
                "source": self._extract_location(msg, "from"),
                "destination": self._extract_location(msg, "to"),
                "date": None  # Would extract date patterns
            }
        if wants_hotel:
            payloads["hotel"] = {
                "raw": message,
                "location": self._extract_location(msg, "in"),
                "checkin": None,
                "checkout": None
            }
        if not payloads:
            # Default: try both agents if unclear
            payloads = {
                "flight": {"raw": message},
                "hotel": {"raw": message}
            }

        return payloads

    def _detect_intent_llm(self, message: str) -> Dict[str, Any]:
        """LLM-based intent detection using OpenAI.
        
        This method would call OpenAI to parse the user query and extract
        structured parameters. Stub implementation for now.
        """
        # TODO: Implement LLM-based parsing
        # Example prompt:
        # "Parse this travel query and extract: intent (flight/hotel/both),
        #  flight details (source, destination, date), hotel details (location, dates)"
        return self._detect_intent_keywords(message)

    def _extract_location(self, text: str, preposition: str) -> Optional[str]:
        """Simple location extraction helper."""
        # Very naive: find word after preposition
        words = text.split()
        try:
            idx = words.index(preposition)
            if idx + 1 < len(words):
                return words[idx + 1].strip(",.!?")
        except ValueError:
            pass
        return None