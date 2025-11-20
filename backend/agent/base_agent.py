"""
BaseAgent - Cancel-safe async base class for all agents.

Provides:
- Async execution with request tracking
- Cancellation via asyncio.Event
- Partial result publishing to state store
- Graceful CancelledError handling
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.
    
    Responsibilities:
    - Manage cancellation state via asyncio.Event
    - Publish partial results during execution
    - Handle graceful cancellation and cleanup
    """
    
    def __init__(self, state_store, agent_name: str):
        """
        Initialize the base agent.
        
        Args:
            state_store: Reference to the global state store
            agent_name: Unique identifier for this agent type
        """
        self.state_store = state_store
        self.agent_name = agent_name
        self._cancel_event: Optional[asyncio.Event] = None
        self._current_request_id: Optional[str] = None
    
    async def run(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with cancellation support.
        
        Args:
            request_id: Unique identifier for this request
            params: Parameters for the agent execution
            
        Returns:
            Dict containing status and results
        """
        # Initialize cancellation event for this request
        self._cancel_event = asyncio.Event()
        self._current_request_id = request_id
        
        try:
            logger.info(f"[{self.agent_name}] Starting request {request_id}")
            result = await self._execute(request_id, params)
            logger.info(f"[{self.agent_name}] Completed request {request_id}")
            return result
            
        except asyncio.CancelledError:
            logger.warning(f"[{self.agent_name}] Request {request_id} cancelled via CancelledError")
            await self.on_cancel(request_id)
            return {
                "status": "cancelled",
                "agent": self.agent_name,
                "request_id": request_id,
                "results": []
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Request {request_id} failed: {e}", exc_info=True)
            return {
                "status": "error",
                "agent": self.agent_name,
                "request_id": request_id,
                "error": str(e),
                "results": []
            }
            
        finally:
            self._cancel_event = None
            self._current_request_id = None
    
    @abstractmethod
    async def _execute(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement agent-specific logic here.
        
        Must:
        - Check self.is_cancelled() periodically
        - Call self.publish_partial() to save incremental results
        - Return {"status": "completed"|"cancelled", "results": [...]}
        """
        pass
    
    def cancel(self):
        """
        Request cancellation of the current operation.
        Sets the internal cancel event that _execute should check.
        """
        if self._cancel_event and not self._cancel_event.is_set():
            logger.info(f"[{self.agent_name}] Cancellation requested for {self._current_request_id}")
            self._cancel_event.set()
    
    def is_cancelled(self) -> bool:
        """
        Check if cancellation has been requested.
        
        Returns:
            True if cancel() was called, False otherwise
        """
        return self._cancel_event is not None and self._cancel_event.is_set()
    
    async def publish_partial(self, request_id: str, data: Any):
        """
        Publish partial results to the state store.
        
        Args:
            request_id: The request identifier
            data: Partial data to persist
        """
        try:
            self.state_store.save_partial(request_id, self.agent_name, data)
            logger.debug(f"[{self.agent_name}] Published partial for {request_id}")
        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed to publish partial: {e}")
    
    async def on_cancel(self, request_id: str):
        """
        Hook called when cancellation occurs.
        Override to add custom cleanup logic.
        
        Args:
            request_id: The request identifier
        """
        self.state_store.mark_cancelled(request_id, self.agent_name)
        logger.info(f"[{self.agent_name}] Marked {request_id} as cancelled in state store")