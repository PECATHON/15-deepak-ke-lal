"""
HotelAgent - Async agent for hotel search with cancellation support.

Responsibilities:
- Search hotels using async generator (hotel_api)
- Stream partial results to state store
- Support graceful cancellation
- Aggregate final results
"""

import asyncio
from typing import Dict, Any
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.base_agent import BaseAgent
from tools.hotel_api import search_hotels_iter

logger = logging.getLogger(__name__)


class HotelAgent(BaseAgent):
    """
    Agent responsible for hotel search operations.
    
    Capabilities:
    - Paginated hotel search via async generator
    - Partial result streaming
    - Cancellation at page boundaries
    - Result aggregation
    """
    
    def __init__(self, state_store):
        """
        Initialize the HotelAgent.
        
        Args:
            state_store: Reference to the global state store
        """
        super().__init__(state_store, agent_name="hotel_agent")
        
    async def _execute(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute hotel search with cancellation support.
        
        Args:
            request_id: Unique request identifier
            params: Hotel search parameters
                - location: City or airport code
                - checkin: Check-in date (YYYY-MM-DD)
                - checkout: Check-out date (YYYY-MM-DD)
                - adults: Number of adults
                - rooms: Number of rooms
                
        Returns:
            Dict with status and aggregated results
        """
        all_hotels = []
        total_pages_processed = 0
        
        try:
            logger.info(f"[HotelAgent] Starting search for request {request_id}")
            logger.info(f"[HotelAgent] Params: {params}")
            
            # Stream results from hotel API
            async for batch in search_hotels_iter(params):
                # Check for cancellation before processing batch
                if self.is_cancelled():
                    logger.warning(f"[HotelAgent] Cancellation detected at page {batch['page']}")
                    break
                
                page_num = batch["page"]
                hotels = batch["results"]
                total_pages_processed += 1
                
                # Add hotels to aggregated results
                all_hotels.extend(hotels)
                
                logger.info(
                    f"[HotelAgent] Processed page {page_num}, "
                    f"got {len(hotels)} hotels, "
                    f"total so far: {len(all_hotels)}"
                )
                
                # Publish partial results after each batch
                partial_payload = {
                    "page": page_num,
                    "hotels_in_batch": len(hotels),
                    "total_hotels": len(all_hotels),
                    "hotels": all_hotels.copy(),  # Copy to avoid mutation
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                await self.publish_partial(request_id, partial_payload)
                
                # Check cancellation again after I/O
                if self.is_cancelled():
                    logger.warning(f"[HotelAgent] Cancellation detected after page {page_num}")
                    break
            
            # Determine final status
            if self.is_cancelled():
                status = "cancelled"
                logger.info(
                    f"[HotelAgent] Request {request_id} cancelled. "
                    f"Processed {total_pages_processed} pages, found {len(all_hotels)} hotels"
                )
            else:
                status = "completed"
                logger.info(
                    f"[HotelAgent] Request {request_id} completed. "
                    f"Processed {total_pages_processed} pages, found {len(all_hotels)} hotels"
                )
            
            return {
                "status": status,
                "agent": self.agent_name,
                "request_id": request_id,
                "results": all_hotels,
                "metadata": {
                    "total_results": len(all_hotels),
                    "pages_processed": total_pages_processed,
                    "search_params": params
                }
            }
            
        except asyncio.CancelledError:
            # Task was cancelled externally (e.g., asyncio.Task.cancel())
            logger.warning(
                f"[HotelAgent] Task cancelled externally. "
                f"Processed {total_pages_processed} pages, found {len(all_hotels)} hotels"
            )
            # Re-raise to be caught by BaseAgent.run()
            raise
            
        except Exception as e:
            logger.error(f"[HotelAgent] Unexpected error during search: {e}", exc_info=True)
            raise
