"""
FlightAgent - Async agent for flight search with cancellation support.

Responsibilities:
- Search flights using async generator (flight_api)
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
from tools.flight_api import search_flights_iter

logger = logging.getLogger(__name__)


class FlightAgent(BaseAgent):
    """
    Agent responsible for flight search operations.
    
    Capabilities:
    - Paginated flight search via async generator
    - Partial result streaming
    - Cancellation at page boundaries
    - Result aggregation
    """
    
    def __init__(self, state_store):
        """
        Initialize the FlightAgent.
        
        Args:
            state_store: Reference to the global state store
        """
        super().__init__(state_store, agent_name="flight_agent")
        
    async def _execute(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute flight search with cancellation support.
        
        Args:
            request_id: Unique request identifier
            params: Flight search parameters
                - origin: Departure airport
                - destination: Arrival airport
                - date: Departure date
                - passengers: Number of passengers
                
        Returns:
            Dict with status and aggregated results
        """
        all_flights = []
        total_pages_processed = 0
        
        try:
            logger.info(f"[FlightAgent] Starting search for request {request_id}")
            logger.info(f"[FlightAgent] Params: {params}")
            
            # Stream results from flight API
            async for batch in search_flights_iter(params):
                # Check for cancellation before processing batch
                if self.is_cancelled():
                    logger.warning(f"[FlightAgent] Cancellation detected at page {batch['page']}")
                    break
                
                page_num = batch["page"]
                flights = batch["results"]
                total_pages_processed += 1
                
                # Add flights to aggregated results
                all_flights.extend(flights)
                
                logger.info(
                    f"[FlightAgent] Processed page {page_num}, "
                    f"got {len(flights)} flights, "
                    f"total so far: {len(all_flights)}"
                )
                
                # Publish partial results after each batch
                partial_payload = {
                    "page": page_num,
                    "flights_in_batch": len(flights),
                    "total_flights": len(all_flights),
                    "flights": all_flights.copy(),  # Copy to avoid mutation
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                await self.publish_partial(request_id, partial_payload)
                
                # Check cancellation again after I/O
                if self.is_cancelled():
                    logger.warning(f"[FlightAgent] Cancellation detected after page {page_num}")
                    break
            
            # Determine final status
            if self.is_cancelled():
                status = "cancelled"
                logger.info(
                    f"[FlightAgent] Request {request_id} cancelled. "
                    f"Processed {total_pages_processed} pages, found {len(all_flights)} flights"
                )
            else:
                status = "completed"
                logger.info(
                    f"[FlightAgent] Request {request_id} completed. "
                    f"Processed {total_pages_processed} pages, found {len(all_flights)} flights"
                )
            
            return {
                "status": status,
                "agent": self.agent_name,
                "request_id": request_id,
                "results": all_flights,
                "metadata": {
                    "total_results": len(all_flights),
                    "pages_processed": total_pages_processed,
                    "search_params": params
                }
            }
            
        except asyncio.CancelledError:
            # Task was cancelled externally (e.g., asyncio.Task.cancel())
            logger.warning(
                f"[FlightAgent] Task cancelled externally. "
                f"Processed {total_pages_processed} pages, found {len(all_flights)} flights"
            )
            # Re-raise to be caught by BaseAgent.run()
            raise
            
        except Exception as e:
            logger.error(f"[FlightAgent] Unexpected error during search: {e}", exc_info=True)
            raise