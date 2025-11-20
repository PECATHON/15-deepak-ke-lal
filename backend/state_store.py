"""
StateStore - In-memory state management for multi-agent system.

Responsibilities:
- Store partial results from agents
- Track cancellation metadata
- Provide thread-safe access to shared state
- Support request-level result aggregation
"""

import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StateStore:
    """
    Thread-safe in-memory state store for agent results and metadata.
    
    Structure:
    {
        "request_id": {
            "agent_name": {
                "partials": [partial_result_1, partial_result_2, ...],
                "cancelled": bool,
                "cancelled_at": timestamp,
                "metadata": {...}
            }
        }
    }
    """
    
    def __init__(self):
        """Initialize the state store with thread-safe data structures."""
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        logger.info("[StateStore] Initialized")
    
    def save_partial(self, request_id: str, agent: str, payload: Any):
        """
        Save partial result for a specific agent and request.
        
        Args:
            request_id: Unique request identifier
            agent: Agent name (e.g., "flight_agent")
            payload: Partial result data to store
        """
        with self._lock:
            # Initialize request structure if needed
            if request_id not in self._store:
                self._store[request_id] = {}
            
            # Initialize agent structure if needed
            if agent not in self._store[request_id]:
                self._store[request_id][agent] = {
                    "partials": [],
                    "cancelled": False,
                    "cancelled_at": None,
                    "metadata": {}
                }
            
            # Append partial result with timestamp
            partial_entry = {
                "data": payload,
                "timestamp": datetime.utcnow().isoformat(),
                "sequence": len(self._store[request_id][agent]["partials"])
            }
            
            self._store[request_id][agent]["partials"].append(partial_entry)
            
            logger.debug(
                f"[StateStore] Saved partial for {request_id}/{agent}, "
                f"total partials: {len(self._store[request_id][agent]['partials'])}"
            )
    
    def get_all_partials(self, request_id: str) -> Dict[str, List[Any]]:
        """
        Retrieve all partial results for a request across all agents.
        
        Args:
            request_id: Unique request identifier
            
        Returns:
            Dict mapping agent names to lists of their partial results
        """
        with self._lock:
            if request_id not in self._store:
                logger.warning(f"[StateStore] No data found for request {request_id}")
                return {}
            
            result = {}
            for agent, agent_data in self._store[request_id].items():
                result[agent] = agent_data["partials"]
            
            logger.info(
                f"[StateStore] Retrieved partials for {request_id}: "
                f"{sum(len(v) for v in result.values())} total entries across {len(result)} agents"
            )
            return result
    
    def mark_cancelled(self, request_id: str, agent: str):
        """
        Mark an agent's execution as cancelled for a specific request.
        
        Args:
            request_id: Unique request identifier
            agent: Agent name
        """
        with self._lock:
            if request_id not in self._store:
                self._store[request_id] = {}
            
            if agent not in self._store[request_id]:
                self._store[request_id][agent] = {
                    "partials": [],
                    "cancelled": False,
                    "cancelled_at": None,
                    "metadata": {}
                }
            
            self._store[request_id][agent]["cancelled"] = True
            self._store[request_id][agent]["cancelled_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"[StateStore] Marked {request_id}/{agent} as cancelled")
    
    def is_cancelled(self, request_id: str, agent: str) -> bool:
        """
        Check if an agent's execution was cancelled.
        
        Args:
            request_id: Unique request identifier
            agent: Agent name
            
        Returns:
            True if cancelled, False otherwise
        """
        with self._lock:
            if request_id not in self._store:
                return False
            if agent not in self._store[request_id]:
                return False
            return self._store[request_id][agent].get("cancelled", False)
    
    def get_request_state(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete state for a request.
        
        Args:
            request_id: Unique request identifier
            
        Returns:
            Complete state dict or None if not found
        """
        with self._lock:
            return self._store.get(request_id)
    
    def clear_request(self, request_id: str):
        """
        Clear all data for a specific request.
        
        Args:
            request_id: Unique request identifier
        """
        with self._lock:
            if request_id in self._store:
                del self._store[request_id]
                logger.info(f"[StateStore] Cleared data for request {request_id}")
    
    def get_all_requests(self) -> List[str]:
        """
        Get list of all request IDs currently in the store.
        
        Returns:
            List of request IDs
        """
        with self._lock:
            return list(self._store.keys())
    
    def get_partial_data_only(self, request_id: str, agent: str) -> List[Any]:
        """
        Retrieve only the data payloads (without metadata) for an agent.
        Useful for interruption continuation.
        
        Args:
            request_id: Unique request identifier
            agent: Agent name
            
        Returns:
            List of data payloads from partials
        """
        with self._lock:
            partials = self.get_all_partials(request_id)
            if agent in partials:
                return [p["data"] for p in partials[agent]]
            return []
    
    def get_agents_for_request(self, request_id: str) -> List[str]:
        """
        Get list of all agents that have data for a request.
        
        Args:
            request_id: Unique request identifier
            
        Returns:
            List of agent names
        """
        with self._lock:
            if request_id in self._store:
                return list(self._store[request_id].keys())
            return []
    
    def get_agent_state(self, request_id: str, agent: str) -> Optional[Dict[str, Any]]:
        """
        Get complete state for a specific agent in a request.
        
        Args:
            request_id: Unique request identifier
            agent: Agent name
            
        Returns:
            Agent state dict or None if not found
        """
        with self._lock:
            if request_id in self._store and agent in self._store[request_id]:
                return self._store[request_id][agent]
            return None
    
    def mark_completed(self, request_id: str, agent: str):
        """
        Mark an agent's execution as successfully completed.
        
        Args:
            request_id: Unique request identifier
            agent: Agent name
        """
        with self._lock:
            if request_id in self._store and agent in self._store[request_id]:
                self._store[request_id][agent]["metadata"]["status"] = "completed"
                self._store[request_id][agent]["metadata"]["completed_at"] = datetime.utcnow().isoformat()
                logger.info(f"[StateStore] Marked {request_id}/{agent} as completed")
    
    def mark_error(self, request_id: str, agent: str, error: str):
        """
        Mark an agent's execution as failed with error.
        
        Args:
            request_id: Unique request identifier
            agent: Agent name
            error: Error message
        """
        with self._lock:
            if request_id not in self._store:
                self._store[request_id] = {}
            
            if agent not in self._store[request_id]:
                self._store[request_id][agent] = {
                    "partials": [],
                    "cancelled": False,
                    "cancelled_at": None,
                    "metadata": {}
                }
            
            self._store[request_id][agent]["metadata"]["status"] = "error"
            self._store[request_id][agent]["metadata"]["error"] = error
            self._store[request_id][agent]["metadata"]["error_at"] = datetime.utcnow().isoformat()
            
            logger.error(f"[StateStore] Marked {request_id}/{agent} as error: {error}")

