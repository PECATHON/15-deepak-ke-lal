"""
Enhanced Travel Tools with Bonus Features
=========================================

Implements all PS-005 bonus features:
1. Multi-leg flight itinerary support
2. Price alerts / comparison across multiple providers
3. Booking simulation flow
4. Multi-modal responses (maps, images, links)
5. User profile with preferences
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from langchain_core.tools import tool


# ============================================================================
# USER PROFILE MANAGEMENT
# ============================================================================

# In-memory user profiles (in production, use database)
USER_PROFILES: Dict[str, Dict[str, Any]] = {}


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get or create user profile with preferences."""
    if user_id not in USER_PROFILES:
        USER_PROFILES[user_id] = {
            "user_id": user_id,
            "preferences": {
                "seat_class": "Economy",  # Economy, Premium Economy, Business, First
                "hotel_star_rating": 3,  # 1-5 stars
                "budget_per_night": 5000,  # INR
                "max_layovers": 1,
                "airline_preference": [],  # Preferred airlines
                "dietary_requirements": [],  # Veg, Non-veg, Vegan
                "price_alert_enabled": True,
                "price_alert_threshold": 10  # % price change
            },
            "booking_history": [],
            "price_alerts": []
        }
    return USER_PROFILES[user_id]


def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
    """Update user preferences."""
    profile = get_user_profile(user_id)
    profile["preferences"].update(preferences)
    return profile


# ============================================================================
# MULTI-LEG FLIGHT TOOL
# ============================================================================

@tool
def search_multi_leg_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    trip_type: str = "one-way",
    passengers: int = 1,
    user_id: str = "default"
) -> str:
    """
    Search for flights with multi-leg itinerary support.
    
    Supports:
    - One-way flights
    - Round-trip flights
    - Multi-city flights with multiple stops
    - Layover information
    - Price comparison across providers
    
    Args:
        origin: Departure city/airport
        destination: Arrival city/airport
        departure_date: Date of departure (YYYY-MM-DD)
        return_date: Return date for round-trip (optional)
        trip_type: "one-way", "round-trip", or "multi-city"
        passengers: Number of passengers
        user_id: User ID for personalized results
        
    Returns:
        JSON with multi-leg flight options, prices, layovers, and booking links
    """
    try:
        print(f"🛫 Searching multi-leg flights: {origin} → {destination}")
        
        # Get user preferences
        profile = get_user_profile(user_id)
        prefs = profile["preferences"]
        seat_class = prefs["seat_class"]
        max_layovers = prefs["max_layovers"]
        
        # Generate realistic multi-leg flight data
        flights = []
        
        # Direct flight option
        base_price = 8500
        flights.append({
            "flight_id": "FL001",
            "type": "direct",
            "legs": [
                {
                    "leg_number": 1,
                    "airline": "Air India",
                    "flight_number": "AI501",
                    "origin": origin,
                    "destination": destination,
                    "departure_time": f"{departure_date} 06:00",
                    "arrival_time": f"{departure_date} 09:30",
                    "duration": "3h 30m",
                    "aircraft": "Boeing 787"
                }
            ],
            "total_duration": "3h 30m",
            "layovers": 0,
            "prices": {
                "Economy": base_price,
                "Premium Economy": base_price * 1.5,
                "Business": base_price * 2.5,
                "First": base_price * 4
            },
            "providers": [
                {"name": "MakeMyTrip", "price": base_price, "link": f"https://makemytrip.com/flight/FL001"},
                {"name": "Goibibo", "price": base_price - 200, "link": f"https://goibibo.com/flight/FL001"},
                {"name": "Cleartrip", "price": base_price + 100, "link": f"https://cleartrip.com/flight/FL001"}
            ],
            "amenities": ["WiFi", "Meals", "Entertainment"],
            "baggage": "2 x 23kg",
            "refundable": True,
            "image": f"https://images.example.com/ai501.jpg",
            "seat_map": f"https://seatmaps.example.com/ai501",
            "booking_link": f"https://book.example.com/FL001"
        })
        
        # 1-stop flight option
        if max_layovers >= 1:
            flights.append({
                "flight_id": "FL002",
                "type": "1-stop",
                "legs": [
                    {
                        "leg_number": 1,
                        "airline": "IndiGo",
                        "flight_number": "6E234",
                        "origin": origin,
                        "destination": "Mumbai",
                        "departure_time": f"{departure_date} 08:00",
                        "arrival_time": f"{departure_date} 10:30",
                        "duration": "2h 30m",
                        "aircraft": "Airbus A320"
                    },
                    {
                        "leg_number": 2,
                        "airline": "IndiGo",
                        "flight_number": "6E456",
                        "origin": "Mumbai",
                        "destination": destination,
                        "departure_time": f"{departure_date} 12:00",
                        "arrival_time": f"{departure_date} 14:30",
                        "duration": "2h 30m",
                        "aircraft": "Airbus A320"
                    }
                ],
                "layover_info": [
                    {
                        "airport": "Mumbai (BOM)",
                        "duration": "1h 30m",
                        "facilities": ["Lounges", "Restaurants", "Shops"]
                    }
                ],
                "total_duration": "6h 30m",
                "layovers": 1,
                "prices": {
                    "Economy": base_price - 1500,
                    "Premium Economy": (base_price - 1500) * 1.5,
                    "Business": (base_price - 1500) * 2.5,
                    "First": (base_price - 1500) * 4
                },
                "providers": [
                    {"name": "MakeMyTrip", "price": base_price - 1500, "link": f"https://makemytrip.com/flight/FL002"},
                    {"name": "Goibibo", "price": base_price - 1700, "link": f"https://goibibo.com/flight/FL002"},
                    {"name": "Cleartrip", "price": base_price - 1400, "link": f"https://cleartrip.com/flight/FL002"}
                ],
                "amenities": ["Meals", "Entertainment"],
                "baggage": "1 x 20kg",
                "refundable": False,
                "image": f"https://images.example.com/6e234.jpg",
                "booking_link": f"https://book.example.com/FL002"
            })
        
        # Round-trip option
        if return_date and trip_type == "round-trip":
            return_flight = {
                "flight_id": "FL003-RT",
                "type": "round-trip",
                "outbound": flights[0],
                "inbound": {
                    "flight_id": "FL003-IN",
                    "type": "direct",
                    "legs": [
                        {
                            "leg_number": 1,
                            "airline": "Vistara",
                            "flight_number": "UK985",
                            "origin": destination,
                            "destination": origin,
                            "departure_time": f"{return_date} 16:00",
                            "arrival_time": f"{return_date} 19:30",
                            "duration": "3h 30m",
                            "aircraft": "Boeing 737"
                        }
                    ],
                    "total_duration": "3h 30m",
                    "layovers": 0
                },
                "total_price": {
                    "Economy": base_price * 2 * 0.85,  # Round-trip discount
                    "Premium Economy": base_price * 2 * 0.85 * 1.5,
                    "Business": base_price * 2 * 0.85 * 2.5,
                    "First": base_price * 2 * 0.85 * 4
                },
                "savings": f"₹{int(base_price * 2 * 0.15)}",
                "providers": [
                    {"name": "MakeMyTrip", "price": base_price * 2 * 0.85, "link": f"https://makemytrip.com/flight/FL003-RT"},
                    {"name": "Goibibo", "price": base_price * 2 * 0.85 - 400, "link": f"https://goibibo.com/flight/FL003-RT"}
                ],
                "booking_link": f"https://book.example.com/FL003-RT"
            }
            flights.append(return_flight)
        
        # Price alerts
        price_alerts = []
        if prefs["price_alert_enabled"]:
            best_price = min(f["prices"][seat_class] for f in flights if "prices" in f)
            price_alerts.append({
                "alert_id": f"PA_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "route": f"{origin} → {destination}",
                "current_price": best_price,
                "alert_threshold": prefs["price_alert_threshold"],
                "message": f"We'll notify you if prices drop by {prefs['price_alert_threshold']}% or more!"
            })
        
        result = {
            "success": True,
            "query": f"{origin} to {destination}",
            "trip_type": trip_type,
            "departure_date": departure_date,
            "return_date": return_date,
            "passengers": passengers,
            "class": seat_class,
            "flights": flights,
            "total_results": len(flights),
            "user_preferences": prefs,
            "price_alerts": price_alerts,
            "comparison": {
                "cheapest": min((f for f in flights if "prices" in f), key=lambda x: x["prices"][seat_class]),
                "fastest": min(flights, key=lambda x: parse_duration(x.get("total_duration", "24h")))
            },
            "map_link": f"https://maps.google.com/?q={origin}+to+{destination}",
            "timestamp": datetime.now().isoformat(),
            "source": "Enhanced Multi-Leg Flight Search"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


def parse_duration(duration_str: str) -> int:
    """Parse duration string to minutes."""
    try:
        if 'h' in duration_str:
            parts = duration_str.replace('m', '').split('h')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
        return 999
    except:
        return 999


# ============================================================================
# DYNAMIC HOTEL IMAGE GENERATION (No hard-coded photo arrays)
# ==========================================================================

def generate_hotel_images(hotel_name: str, location: str, count: int = 3) -> List[str]:
    """Generate dynamic (non hard-coded) image URLs for a hotel.

    Uses Unsplash source endpoints (no API key required) to fetch themed images.
    If an UNSPLASH_ACCESS_KEY is provided, this can be upgraded later to real API calls.
    The returned URLs are randomized by Unsplash on load, avoiding static photo lists.
    """
    base_tags = ["exterior", "room", "lobby", "amenities", "suite"]
    tags = base_tags[:count]
    images = []
    # Sanitize query components
    name_clean = hotel_name.replace(" ", "+")
    loc_clean = location.replace(" ", "+")
    for tag in tags:
        query = f"{name_clean}+{loc_clean}+hotel+{tag}"
        # Unsplash dynamic featured image endpoint
        images.append(f"https://source.unsplash.com/featured/?{query}")
    return images


# ============================================================================
# ENHANCED HOTEL TOOL WITH PRICE COMPARISON
# ============================================================================

@tool
def search_hotels_enhanced(
    location: str,
    checkin_date: str,
    checkout_date: str,
    guests: int = 1,
    user_id: str = "default"
) -> str:
    """
    Search for hotels with price comparison and user preferences.
    
    Features:
    - Price comparison across booking platforms
    - Filter by star rating preference
    - Multi-modal responses (images, maps, links)
    - Price alerts
    
    Args:
        location: City or area name
        checkin_date: Check-in date (YYYY-MM-DD)
        checkout_date: Check-out date (YYYY-MM-DD)
        guests: Number of guests
        user_id: User ID for personalized results
        
    Returns:
        JSON with hotel options, prices across platforms, images, and maps
    """
    try:
        print(f"🏨 Searching hotels in: {location}")
        
        # Get user preferences
        profile = get_user_profile(user_id)
        prefs = profile["preferences"]
        preferred_stars = prefs["hotel_star_rating"]
        budget = prefs["budget_per_night"]
        
        location_lower = location.lower()
        
        hotels = []
        
        # Generate location-specific hotel data
        if "paris" in location_lower:
            hotels = []
            paris_hotels_seed = [
                ("H001", "The Ritz Paris", 5, 4.8, "15 Place Vendôme, Paris", ["Pool", "Spa", "WiFi", "Restaurant", "Bar", "Gym", "Concierge"], 44500, 45000, 45200, 44800, "Hotels.com", "Absolutely stunning! The service is impeccable."),
                ("H002", "Ibis Paris Montmartre", 3, 4.2, "5 Rue Caulaincourt, Paris", ["WiFi", "Restaurant", "Bar"], 8200, 8500, 8600, 8300, "Hotels.com", "Great value for money, clean rooms."),
            ]
            for hid, name, stars, rating, addr, amenities, p_hotels, p_booking, p_expedia, p_mmt, cheapest_provider, snippet in paris_hotels_seed:
                prices = {
                    "Booking.com": p_booking,
                    "Hotels.com": p_hotels,
                    "Expedia": p_expedia,
                    "MakeMyTrip": p_mmt
                }
                hotels.append({
                    "hotel_id": hid,
                    "name": name,
                    "stars": stars,
                    "rating": rating,
                    "location": addr,
                    "coordinates": {"lat": 48.8682, "lon": 2.3288},  # Simplified; could be unique per hotel
                    "prices_per_night": prices,
                    "cheapest_provider": cheapest_provider,
                    "amenities": amenities,
                    "images": generate_hotel_images(name, location),
                    "reviews": int(rating * 1000 + 1000),
                    "review_snippet": snippet,
                    "availability": "Available",
                    "cancellation": "Free cancellation until 24h before" if stars > 3 else "Non-refundable",
                    "map_link": f"https://maps.google.com/?q={name.replace(' ', '+')}",
                    "booking_links": {prov: f"https://{prov.lower().replace('.com','')}.com/hotel/{name.lower().replace(' ', '-')[:25]}" for prov in prices.keys()},
                    "virtual_tour": f"https://tour.example.com/{name.lower().replace(' ', '-')[:25]}"
                })
        elif "chandigarh" in location_lower:
            hotels = []
            chandigarh_seed = [
                ("HC01", "JW Marriott Hotel Chandigarh", 5, 4.6, "Sector 35B, Chandigarh", ["Pool", "Spa", "WiFi", "Restaurant", "Gym"], 8400, 8500, 8600, 8300, "MakeMyTrip", "Premium stay with excellent amenities."),
                ("HC02", "Taj Chandigarh", 5, 4.5, "Sector 17A, Chandigarh", ["WiFi", "Restaurant", "Gym", "Business Center"], 7100, 7200, 7300, 7000, "Hotels.com", "Elegant property in central location."),
                ("HC03", "Hotel Sunbeam", 4, 4.2, "Sector 22, Chandigarh", ["WiFi", "Restaurant", "Room Service"], 3400, 3500, 3600, 3300, "Hotels.com", "Good mid-range option for families."),
                ("HC04", "Treebo Trend Amber", 3, 3.9, "Sector 9, Chandigarh", ["WiFi", "AC", "TV"], 2150, 2200, 2250, 2100, "Agoda", "Budget friendly with clean rooms."),
            ]
            for hid, name, stars, rating, addr, amenities, p_hotels, p_booking, p_expedia, p_mmt, cheapest_provider, snippet in chandigarh_seed:
                prices = {
                    "Booking.com": p_booking,
                    "Hotels.com": p_hotels,
                    "Expedia": p_expedia,
                    "MakeMyTrip": p_mmt
                }
                hotels.append({
                    "hotel_id": hid,
                    "name": name,
                    "stars": stars,
                    "rating": rating,
                    "location": addr,
                    "coordinates": {"lat": 30.7333, "lon": 76.7794},
                    "prices_per_night": prices,
                    "cheapest_provider": cheapest_provider,
                    "amenities": amenities,
                    "images": generate_hotel_images(name, location),
                    "reviews": int(rating * 1000 + 500),
                    "review_snippet": snippet,
                    "availability": "Available",
                    "cancellation": "Free cancellation" if stars >= 4 else "Non-refundable",
                    "map_link": f"https://maps.google.com/?q={name.replace(' ', '+')}",
                    "booking_links": {prov: f"https://{prov.lower().replace('.com','')}.com/hotel/{name.lower().replace(' ', '-')[:28]}" for prov in prices.keys()},
                    "virtual_tour": f"https://tour.example.com/{name.lower().replace(' ', '-')[:28]}"
                })
        else:
            # Generic hotels for other locations
            base_names = ["Central Plaza", "Grand Residency", "Cityscape Inn", "Skyline Suites"]
            hotels = []
            for idx, base in enumerate(base_names, start=1):
                stars = 5 - (idx % 3)  # vary stars
                rating = 4.0 + (idx * 0.1)
                prices = {
                    "Booking.com": 6000 + idx * 250,
                    "Hotels.com": 5800 + idx * 200,
                    "Expedia": 6100 + idx * 300,
                    "Agoda": 5700 + idx * 150
                }
                cheapest_provider = min(prices, key=prices.get)
                name = f"{base} {location}".strip()
                hotels.append({
                    "hotel_id": f"H{100+idx}",
                    "name": name,
                    "stars": stars,
                    "rating": round(rating, 1),
                    "location": f"Downtown, {location}",
                    "coordinates": {"lat": 28.6139 + idx * 0.01, "lon": 77.2090 + idx * 0.01},
                    "prices_per_night": prices,
                    "cheapest_provider": cheapest_provider,
                    "amenities": ["WiFi", "Restaurant", "Gym"] + (["Pool"] if stars >= 4 else []),
                    "images": generate_hotel_images(name, location),
                    "reviews": 1000 + idx * 123,
                    "review_snippet": "Dynamic listing generated on demand.",
                    "availability": "Available",
                    "cancellation": "Free cancellation" if stars >= 4 else "Non-refundable",
                    "map_link": f"https://maps.google.com/?q={name.replace(' ', '+')}",
                    "booking_links": {prov: f"https://{prov.lower().replace('.com','')}.com/hotel/{base.lower().replace(' ', '-')}-{idx}" for prov in prices.keys()},
                    "virtual_tour": f"https://tour.example.com/{base.lower().replace(' ', '-')}-{idx}"
                })
        
        # Filter by star rating preference
        filtered_hotels = [h for h in hotels if h["stars"] >= preferred_stars]
        if not filtered_hotels:
            filtered_hotels = hotels  # Show all if no match
        
        # Calculate stay duration
        try:
            checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
            checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
            nights = (checkout - checkin).days
        except:
            nights = 1
        
        # Price alerts
        price_alerts = []
        if prefs["price_alert_enabled"]:
            for hotel in filtered_hotels:
                cheapest = min(hotel["prices_per_night"].values())
                price_alerts.append({
                    "hotel": hotel["name"],
                    "current_price": cheapest,
                    "provider": hotel["cheapest_provider"],
                    "alert_message": f"Best price: ₹{cheapest}/night on {hotel['cheapest_provider']}"
                })
        
        result = {
            "success": True,
            "location": location,
            "checkin_date": checkin_date,
            "checkout_date": checkout_date,
            "nights": nights,
            "guests": guests,
            "hotels": filtered_hotels,
            "total_results": len(filtered_hotels),
            "user_preferences": prefs,
            "price_alerts": price_alerts,
            "comparison": {
                "cheapest": min(filtered_hotels, key=lambda x: min(x["prices_per_night"].values())),
                "highest_rated": max(filtered_hotels, key=lambda x: x["rating"])
            },
            "area_map": f"https://maps.google.com/?q=hotels+in+{location}",
            "timestamp": datetime.now().isoformat(),
            "source": "Enhanced Hotel Search with Price Comparison"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ============================================================================
# BOOKING SIMULATION TOOL
# ============================================================================

@tool
def simulate_booking(
    booking_type: str,
    item_id: str,
    passenger_details: Optional[Dict] = None,
    user_id: str = "default"
) -> str:
    """
    Simulate a booking flow (non-functional demo).
    
    Supports:
    - Flight booking with seat selection
    - Hotel booking with room preferences
    - Passenger details capture
    - Payment simulation
    
    Args:
        booking_type: "flight" or "hotel"
        item_id: Flight ID or Hotel ID
        passenger_details: Dict with passenger info (optional)
        user_id: User ID
        
    Returns:
        JSON with booking confirmation details
    """
    try:
        print(f"📋 Simulating {booking_type} booking for {item_id}")
        
        profile = get_user_profile(user_id)
        
        if not passenger_details:
            passenger_details = {
                "passengers": [
                    {
                        "title": "Mr",
                        "first_name": "John",
                        "last_name": "Doe",
                        "age": 30,
                        "gender": "Male",
                        "seat_preference": "Window"
                    }
                ]
            }
        
        booking_id = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if booking_type == "flight":
            booking = {
                "booking_id": booking_id,
                "type": "flight",
                "status": "CONFIRMED",
                "flight_id": item_id,
                "passengers": passenger_details["passengers"],
                "seat_selection": [
                    {
                        "passenger": "John Doe",
                        "seat": "12A",
                        "type": "Window"
                    }
                ],
                "meal_preferences": profile["preferences"].get("dietary_requirements", []),
                "payment": {
                    "method": "Credit Card (DEMO)",
                    "amount": 8500,
                    "currency": "INR",
                    "status": "Processed",
                    "transaction_id": f"TXN{booking_id}"
                },
                "extras": {
                    "baggage": "20kg checked, 7kg cabin",
                    "insurance": "Travel insurance included",
                    "priority_boarding": False
                },
                "confirmation_email": "john.doe@example.com",
                "boarding_pass": f"https://boardingpass.example.com/{booking_id}",
                "manage_booking": f"https://manage.example.com/{booking_id}"
            }
        else:  # hotel
            booking = {
                "booking_id": booking_id,
                "type": "hotel",
                "status": "CONFIRMED",
                "hotel_id": item_id,
                "guest_details": passenger_details["passengers"][0],
                "room_type": "Deluxe Room",
                "room_preferences": {
                    "bed_type": "King",
                    "floor": "High floor",
                    "smoking": "Non-smoking",
                    "view": "City view"
                },
                "special_requests": "Late check-in",
                "payment": {
                    "method": "Credit Card (DEMO)",
                    "amount": 6500,
                    "currency": "INR",
                    "status": "Processed",
                    "transaction_id": f"TXN{booking_id}"
                },
                "extras": {
                    "breakfast": "Included",
                    "wifi": "Free",
                    "parking": "Valet parking available"
                },
                "confirmation_email": "john.doe@example.com",
                "voucher": f"https://voucher.example.com/{booking_id}",
                "manage_booking": f"https://manage.example.com/{booking_id}"
            }
        
        # Add to booking history
        profile["booking_history"].append(booking)
        
        result = {
            "success": True,
            "message": "🎉 Booking simulation completed! (This is a demo, no real booking was made)",
            "booking": booking,
            "next_steps": [
                "Download your confirmation",
                "Add to calendar",
                "Check-in online (24h before departure)" if booking_type == "flight" else "Contact hotel for special requests"
            ],
            "support": {
                "phone": "+91-1800-XXX-XXXX",
                "email": "support@travelassistant.com",
                "chat": "https://chat.example.com"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ============================================================================
# USER PREFERENCES TOOL
# ============================================================================

@tool
def manage_user_preferences(
    user_id: str,
    action: str = "get",
    preferences: Optional[Dict] = None
) -> str:
    """
    Manage user travel preferences.
    
    Args:
        user_id: User ID
        action: "get" or "update"
        preferences: Dict of preferences to update (if action="update")
        
    Returns:
        JSON with current user preferences
    """
    try:
        if action == "update" and preferences:
            update_user_preferences(user_id, preferences)
            message = "Preferences updated successfully!"
        else:
            message = "Current user preferences"
        
        profile = get_user_profile(user_id)
        
        result = {
            "success": True,
            "message": message,
            "user_profile": profile,
            "available_preferences": {
                "seat_class": ["Economy", "Premium Economy", "Business", "First"],
                "hotel_star_rating": [1, 2, 3, 4, 5],
                "dietary_requirements": ["Vegetarian", "Non-Vegetarian", "Vegan", "Halal", "Kosher"],
                "max_layovers": [0, 1, 2, 3]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)
