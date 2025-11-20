import asyncio
import os
from state_store import StateStore  
from agent.hotel_agent import HotelAgent

# Load env manually
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

async def main():
    print("=" * 60)
    print("🏨 Hotel Search: Delhi (Real Booking.com API)")
    print("=" * 60)
    
    store = StateStore()
    agent = HotelAgent(store)
    
    result = await agent.run('delhi_hotels', {
        'location': 'New Delhi',
        'checkin': '2025-12-20',
        'checkout': '2025-12-22',
        'adults': 2,
        'rooms': 1
    })
    
    print(f"\n✅ Status: {result['status']}")
    print(f"📊 Total Hotels: {len(result['results'])}")
    
    if result['results']:
        print(f"\n🏆 Top 5 Hotels:\n")
        for i, h in enumerate(result['results'][:5], 1):
            print(f"{i}. {h['name']}")
            print(f"   💰 ${h['price_per_night']:.2f}/night")
            print(f"   ⭐ Rating: {h['rating']}/10 ({h['review_count']} reviews)")
            print(f"   📍 {h.get('address', 'N/A')}")
            print()
    else:
        print("No hotels found")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
