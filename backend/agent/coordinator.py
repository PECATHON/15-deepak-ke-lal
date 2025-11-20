"""
CoordinatorAgent - Orchestrates multiple agents based on detected intent.

Responsibilities:
- Route requests to appropriate agents (FlightAgent, HotelAgent)
- Execute agents in parallel for efficiency
- Merge results from multiple agents
- Handle cancellation across all running agents
- Aggregate partial results from StateStore
- Provide unified response format
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging
import uuid
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.flight_agent import FlightAgent
from agent.hotel_agent import HotelAgent
from intent_detector import IntentDetector

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """
    Master coordinator that orchestrates multi-agent workflows.
    
    Capabilities:
    - Intent-based routing
    - Parallel agent execution
    - Result merging
    - Cancellation propagation
    - Partial result aggregation
    """
    
    def __init__(self, state_store):
        """
        Initialize the coordinator.
        
        Args:
            state_store: Global state store instance
        """
        self.state_store = state_store
        self.intent_detector = IntentDetector()
        self.flight_agent = FlightAgent(state_store)
        self.hotel_agent = HotelAgent(state_store)
        self.running_tasks: Dict[str, List[asyncio.Task]] = {}
        
        logger.info("[CoordinatorAgent] Initialized")
    
    async def process_message(self, message: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user message through intent detection and agent routing.
        
        Args:
            message: User's natural language query
            request_id: Optional request ID (generated if not provided)
            
        Returns:
            Dict with:
                - request_id: Unique request identifier
                - intents: Detected intents
                - results: Agent results {flight_agent: {...}, hotel_agent: {...}}
                - status: Overall status
                - metadata: Additional info
        """
        # Generate request ID if not provided
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"[CoordinatorAgent] Processing message for {request_id}")
        logger.info(f"[CoordinatorAgent] Message: {message}")
        
        # Step 1: Detect intent
        intent_result = self.intent_detector.detect(message)
        intents = intent_result["intents"]
        params = intent_result["params"]
        confidence = intent_result["confidence"]
        
        if not intents:
            logger.warning(f"[CoordinatorAgent] No intent detected for: {message}")
            return {
                "request_id": request_id,
                "status": "error",
                "error": "Could not understand the request. Please specify flights or hotels.",
                "confidence": confidence
            }
        
        logger.info(f"[CoordinatorAgent] Detected intents: {intents} (confidence: {confidence:.2f})")
        
        # Step 2: Route to agents
        tasks = []
        agent_names = []
        
        if "flight" in intents:
            flight_params = {
                "origin": params.get("origin"),
                "destination": params.get("destination"),
                "date": params.get("date"),
                "passengers": params.get("passengers", 1)
            }
            
            # Validate required params
            if not flight_params["origin"] or not flight_params["destination"]:
                logger.warning("[CoordinatorAgent] Missing flight parameters")
            else:
                logger.info(f"[CoordinatorAgent] Launching FlightAgent with params: {flight_params}")
                task = asyncio.create_task(
                    self.flight_agent.run(request_id, flight_params)
                )
                tasks.append(task)
                agent_names.append("flight_agent")
        
        if "hotel" in intents:
            hotel_params = {
                "location": params.get("location"),
                "checkin": params.get("checkin"),
                "checkout": params.get("checkout"),
                "adults": params.get("adults", 2),
                "rooms": params.get("rooms", 1)
            }
            
            # Validate required params
            if not hotel_params["location"]:
                logger.warning("[CoordinatorAgent] Missing hotel parameters")
            else:
                logger.info(f"[CoordinatorAgent] Launching HotelAgent with params: {hotel_params}")
                task = asyncio.create_task(
                    self.hotel_agent.run(request_id, hotel_params)
                )
                tasks.append(task)
                agent_names.append("hotel_agent")
        
        if not tasks:
            return {
                "request_id": request_id,
                "status": "error",
                "error": "Missing required parameters for search",
                "intents": intents,
                "params": params
            }
        
        # Store running tasks for cancellation
        self.running_tasks[request_id] = tasks
        
        # Step 3: Execute agents in parallel
        logger.info(f"[CoordinatorAgent] Executing {len(tasks)} agents in parallel")
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Step 4: Merge results
            merged_results = {}
            overall_status = "completed"
            
            for agent_name, result in zip(agent_names, results):
                if isinstance(result, Exception):
                    logger.error(f"[CoordinatorAgent] {agent_name} failed: {result}")
                    merged_results[agent_name] = {
                        "status": "error",
                        "error": str(result)
                    }
                    overall_status = "partial"  # Some agents failed
                else:
                    merged_results[agent_name] = result
                    if result.get("status") == "cancelled":
                        overall_status = "cancelled"
            
            logger.info(f"[CoordinatorAgent] All agents completed with status: {overall_status}")
            
            return {
                "request_id": request_id,
                "status": overall_status,
                "intents": intents,
                "results": merged_results,
                "metadata": {
                    "agents_executed": agent_names,
                    "confidence": confidence,
                    "original_message": message
                }
            }
            
        except asyncio.CancelledError:
            logger.warning(f"[CoordinatorAgent] Request {request_id} cancelled")
            return {
                "request_id": request_id,
                "status": "cancelled",
                "intents": intents,
                "results": self._get_partial_results(request_id, agent_names),
                "metadata": {
                    "agents_executed": agent_names,
                    "message": "Request cancelled by user"
                }
            }
        
        finally:
            # Cleanup
            if request_id in self.running_tasks:
                del self.running_tasks[request_id]
    
    def cancel_request(self, request_id: str):
        """
        Cancel all running agents for a request.
        
        Args:
            request_id: Request to cancel
        """
        logger.info(f"[CoordinatorAgent] Cancelling request {request_id}")
        
        # Cancel agents via BaseAgent mechanism
        self.flight_agent.cancel()
        self.hotel_agent.cancel()
        
        # Cancel asyncio tasks
        if request_id in self.running_tasks:
            for task in self.running_tasks[request_id]:
                if not task.done():
                    task.cancel()
                    logger.info(f"[CoordinatorAgent] Cancelled task for {request_id}")
    
    def get_status(self, request_id: str) -> Dict[str, Any]:
        """
        Get current status of a request including partial results.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Dict with status and partial results from all agents
        """
        # Check if request is still running
        is_running = request_id in self.running_tasks
        
        # Get partial results from state store
        partials = self.state_store.get_all_partials(request_id)
        
        # Get agent states
        agents = self.state_store.get_agents_for_request(request_id)
        agent_statuses = {}
        
        for agent in agents:
            agent_state = self.state_store.get_agent_state(request_id, agent)
            if agent_state:
                agent_statuses[agent] = {
                    "status": agent_state.get("metadata", {}).get("status", "running"),
                    "partial_count": len(agent_state.get("partials", [])),
                    "cancelled": agent_state.get("cancelled", False)
                }
        
        return {
            "request_id": request_id,
            "is_running": is_running,
            "agents": agent_statuses,
            "partials": partials
        }
    
    def _get_partial_results(self, request_id: str, agent_names: List[str]) -> Dict[str, Any]:
        """
        Retrieve partial results from agents (used when cancelled).
        
        Args:
            request_id: Request identifier
            agent_names: List of agent names to retrieve from
            
        Returns:
            Dict mapping agent names to their partial results
        """
        partial_results = {}
        
        for agent in agent_names:
            partials = self.state_store.get_partial_data_only(request_id, agent)
            if partials:
                # Merge all partial data
                merged = []
                for partial in partials:
                    if isinstance(partial, dict):
                        if "flights" in partial:
                            merged.extend(partial.get("flights", []))
                        elif "hotels" in partial:
                            merged.extend(partial.get("hotels", []))
                
                partial_results[agent] = {
                    "status": "cancelled",
                    "results": merged,
                    "metadata": {
                        "partial_count": len(partials),
                        "total_results": len(merged)
                    }
                }
        
        return partial_results
