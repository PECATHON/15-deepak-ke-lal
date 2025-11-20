"""Configuration management for the backend."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Amadeus API (recommended for flights & hotels)
    AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY", "")
    AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET", "")
    AMADEUS_HOSTNAME = os.getenv("AMADEUS_HOSTNAME", "test.api.amadeus.com")
    
    # SerpAPI (Google search for flights/hotels)
    SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
    
    # RapidAPI
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
    RAPIDAPI_HOTEL_HOST = os.getenv("RAPIDAPI_HOTEL_HOST", "booking-com.p.rapidapi.com")
    
    # AviationStack Flight API
    AVIATIONSTACK_KEY = os.getenv("AVIATIONSTACK_KEY", "")
    
    # Backend
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))
    USE_REAL_APIS = os.getenv("USE_REAL_APIS", "False").lower() == "true"


config = Config()
