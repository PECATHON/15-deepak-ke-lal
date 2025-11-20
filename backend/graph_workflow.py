"""LangGraph workflow for multi-agent travel planning assistant.

This module defines the state schema, agent nodes, and routing logic for
coordinating between Flight and Hotel agents with interruption support.
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import asyncio
from typing import Any, Optional

try:
    from agent.flight_agent import FlightAgent
    from agent.hotel_agent import HotelAgent
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from agent.flight_agent import FlightAgent
    from agent.hotel_agent import HotelAgent


class AgentState(TypedDict):
    """State schema for the travel planning assistant workflow.
    
    Fields:
        user_id: User identifier for conversation tracking
        messages: Conversation history
        user_query: Current user input
        intent: Detected intent (flight, hotel, both, or unknown)
        flight_input: Parsed flight search parameters
        hotel_input: Parsed hotel search parameters
        flight_results: Results from flight agent (partial or final)
        hotel_results: Results from hotel agent (partial or final)
        final_response: Assembled response to user
        cancel_requested: Flag indicating if cancellation was requested
        status: Current workflow status
        previous_context: Context from previously interrupted tasks
        partial_results: Preserved partial results from agents
    """
    user_id: str
    messages: list[dict]
    user_query: str
    intent: str
    flight_input: Optional[dict]
    hotel_input: Optional[dict]
    flight_results: Optional[dict]
    hotel_results: Optional[dict]
    final_response: Optional[str]
    cancel_requested: bool
    status: str
    previous_context: Optional[dict]
    partial_results: Optional[dict]


def router_node(state: AgentState) -> AgentState:
    """Analyze user query and determine which agents to invoke.
    
    Simple keyword-based intent detection. In production, this would use
    an LLM to parse the query and extract structured parameters.
    """
    query = state["user_query"].lower()
    
    wants_flight = any(kw in query for kw in ["flight", "fly", "ticket", "plane"])
    wants_hotel = any(kw in query for kw in ["hotel", "stay", "room", "accommodation"])
    
    # Determine intent
    if wants_flight and wants_hotel:
        intent = "both"
    elif wants_flight:
        intent = "flight"
    elif wants_hotel:
        intent = "hotel"
    else:
        intent = "unknown"
    
    # Parse basic parameters (stub - would use LLM in production)
    flight_input = {"raw": state["user_query"]} if wants_flight else None
    hotel_input = {"raw": state["user_query"]} if wants_hotel else None
    
    return {
        **state,
        "intent": intent,
        "flight_input": flight_input,
        "hotel_input": hotel_input,
        "status": "routed"
    }


async def flight_node(state: AgentState) -> AgentState:
    """Execute flight search agent with cancellation support.
    
    Checks for cancellation requests at multiple points and preserves
    partial results if interrupted.
    """
    from agent.flight_agent import FlightAgent
    
    # Early cancellation check
    if state.get("cancel_requested"):
        return {
            **state,
            "status": "cancelled",
            "flight_results": {"status": "cancelled", "partial": state.get("partial_results", {}).get("flight")}
        }
    
    agent = FlightAgent()
    
    # Track partial results as they arrive
    partial_results = []
    
    async def progress_cb(data):
        """Callback to track progress and partial results."""
        partial_results.append(data)
        # Could also emit to websocket here
    
    # Create cancel event from configuration
    cancel_event = asyncio.Event()
    
    # Check if cancellation is already requested
    if state.get("cancel_requested"):
        cancel_event.set()
    
    try:
        # Run agent with cancellation support
        result = await agent.run(
            state["user_id"],
            state.get("flight_input", {}),
            progress_cb,
            cancel_event
        )
        
        # Check for cancellation after agent completes
        if state.get("cancel_requested") or result.get("status") == "cancelled":
            return {
                **state,
                "flight_results": result,
                "status": "flight_cancelled",
                "current_agent": "flight"
            }
        
        return {
            **state,
            "flight_results": result,
            "status": "flight_completed" if result.get("status") == "completed" else "flight_partial",
            "current_agent": "flight"
        }
        
    except asyncio.CancelledError:
        # Preserve partial results on cancellation
        last_partial = partial_results[-1] if partial_results else {}
        return {
            **state,
            "flight_results": {"status": "cancelled", "partial": last_partial},
            "status": "flight_cancelled",
            "current_agent": "flight"
        }


async def hotel_node(state: AgentState) -> AgentState:
    """Execute hotel search agent with cancellation support.
    
    Checks for cancellation requests at multiple points and preserves
    partial results if interrupted.
    """
    from agent.hotel_agent import HotelAgent
    
    # Early cancellation check
    if state.get("cancel_requested"):
        return {
            **state,
            "status": "cancelled",
            "hotel_results": {"status": "cancelled", "partial": state.get("partial_results", {}).get("hotel")}
        }
    
    agent = HotelAgent()
    partial_results = []
    
    async def progress_cb(data):
        """Callback to track progress and partial results."""
        partial_results.append(data)
    
    cancel_event = asyncio.Event()
    if state.get("cancel_requested"):
        cancel_event.set()
    
    try:
        result = await agent.run(
            state["user_id"],
            state.get("hotel_input", {}),
            progress_cb,
            cancel_event
        )
        
        # Check for cancellation after agent completes
        if state.get("cancel_requested") or result.get("status") == "cancelled":
            return {
                **state,
                "hotel_results": result,
                "status": "hotel_cancelled",
                "current_agent": "hotel"
            }
        
        return {
            **state,
            "hotel_results": result,
            "status": "hotel_completed" if result.get("status") == "completed" else "hotel_partial",
            "current_agent": "hotel"
        }
        
    except asyncio.CancelledError:
        # Preserve partial results on cancellation
        last_partial = partial_results[-1] if partial_results else {}
        return {
            **state,
            "hotel_results": {"status": "cancelled", "partial": last_partial},
            "status": "hotel_cancelled",
            "current_agent": "hotel"
        }


def response_assembler_node(state: AgentState) -> AgentState:
    """Assemble final response from agent results.
    
    Handles both completed and cancelled/partial results, providing
    meaningful feedback about what was accomplished before interruption.
    """
    import json
    
    response_data = {}
    status_messages = []
    
    # Check for previous context
    if state.get("previous_context"):
        prev_ctx = state["previous_context"]
        status_messages.append(
            f"Continuing from previous query: '{prev_ctx.get('previous_query', 'N/A')}'"
        )
    
    # Handle flight results
    if state.get("flight_results"):
        flight_data = state["flight_results"]
        if flight_data.get("status") == "completed":
            results = flight_data.get("results", [])
            response_data["flights"] = results
            status_messages.append(f"Found {len(results)} flight options")
        elif flight_data.get("status") == "cancelled":
            partial = flight_data.get("partial", {})
            response_data["flight_status"] = "interrupted"
            response_data["flight_partial"] = partial
            status_messages.append(
                f"Flight search interrupted (partial results available)"
            )
        else:
            # Partial or other status
            response_data["flight_status"] = flight_data.get("status", "unknown")
            response_data["flight_partial"] = flight_data.get("partial", {})
    
    # Handle hotel results
    if state.get("hotel_results"):
        hotel_data = state["hotel_results"]
        if hotel_data.get("status") == "completed":
            results = hotel_data.get("results", [])
            response_data["hotels"] = results
            status_messages.append(f"Found {len(results)} hotel options")
        elif hotel_data.get("status") == "cancelled":
            partial = hotel_data.get("partial", {})
            response_data["hotel_status"] = "interrupted"
            response_data["hotel_partial"] = partial
            status_messages.append(
                f"Hotel search interrupted (partial results available)"
            )
        else:
            response_data["hotel_status"] = hotel_data.get("status", "unknown")
            response_data["hotel_partial"] = hotel_data.get("partial", {})
    
    # Build final response
    if response_data:
        response_data["summary"] = " | ".join(status_messages) if status_messages else "Search completed"
        final_response = json.dumps(response_data, indent=2)
    else:
        final_response = json.dumps({
            "message": "No results available.",
            "status": state.get("status", "unknown")
        })
    
    return {
        **state,
        "final_response": final_response,
        "status": "completed"
    }


def route_after_router(state: AgentState) -> Literal["flight_node", "hotel_node", "both_parallel", "response_assembler", END]:
    """Conditional routing based on detected intent."""
    intent = state.get("intent", "unknown")
    
    if state.get("cancel_requested"):
        return "response_assembler"
    
    if intent == "flight":
        return "flight_node"
    elif intent == "hotel":
        return "hotel_node"
    elif intent == "both":
        return "both_parallel"
    else:
        # Unknown intent - go directly to response
        return "response_assembler"


def build_workflow() -> StateGraph:
    """Build the LangGraph workflow for travel planning assistant.
    
    Graph structure:
        START -> router_node -> (flight_node | hotel_node | both_parallel) -> response_assembler -> END
    
    Returns:
        Compiled StateGraph with memory checkpointer for state persistence
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("flight_node", flight_node)
    workflow.add_node("hotel_node", hotel_node)
    workflow.add_node("response_assembler", response_assembler_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional routing from router
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "flight_node": "flight_node",
            "hotel_node": "hotel_node",
            "both_parallel": "flight_node",  # Will handle both in sequence for now
            "response_assembler": "response_assembler",
            END: END
        }
    )
    
    # After flight node, check if we need hotel too
    workflow.add_conditional_edges(
        "flight_node",
        lambda state: "hotel_node" if state.get("intent") == "both" and not state.get("cancel_requested") else "response_assembler",
        {
            "hotel_node": "hotel_node",
            "response_assembler": "response_assembler"
        }
    )
    
    # After hotel node, go to response assembler
    workflow.add_edge("hotel_node", "response_assembler")
    
    # Response assembler ends the workflow
    workflow.add_edge("response_assembler", END)
    
    # Compile with memory checkpointer for state persistence and interruption support
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=[], interrupt_after=[])


# Global workflow instance
WORKFLOW = build_workflow()
