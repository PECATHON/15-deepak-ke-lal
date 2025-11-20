import asyncio
from state_store import StateStore  
from agent.hotel_agent import HotelAgent

async def main():
    print("Testing...")
    store = StateStore()
    agent = HotelAgent(store)
    result = await agent.run('test', {
        'location': 'New Delhi',
        'checkin': '2025-12-20',
        'checkout': '2025-12-22',
        'adults': 2,
        'rooms': 1
    })
    print(f"Status: {result['status']}")
    print(f"Hotels: {len(result['results'])}")
    for h in result['results'][:3]:
        print(f"- {h['name']}: ${h['price_per_night']:.2f}")

asyncio.run(main())
