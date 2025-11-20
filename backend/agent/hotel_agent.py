try:
    from .base_agent import BaseAgent
except ImportError:
    from base_agent import BaseAgent

import asyncio
from typing import Any, Callable

try:
    from ..tools.hotel_api import search_hotels
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from tools.hotel_api import search_hotels


class HotelAgent(BaseAgent):
    name = "hotel"

    async def run(self, user_id: str, input_data: dict, progress_callback: Callable[[dict], Any], cancel_event: asyncio.Event) -> dict:
        # input_data expected keys: location, checkin, checkout
        await progress_callback({"status": "started", "agent": self.name})

        async def _simulate():
            # Get the async generator for partial results
            partials_gen = await search_hotels(input_data, final=False)
            
            # Stream partial results
            async for partial in partials_gen:
                if cancel_event.is_set():
                    await progress_callback({"status": "cancelled", "agent": self.name, "partial": partial})
                    return {"status": "cancelled", "partial": partial}
                await progress_callback({"status": "partial", "agent": self.name, "partial": partial})
            
            # Get final results
            results = await search_hotels(input_data, final=True)
            return {"status": "completed", "results": results}

        return await _simulate()
