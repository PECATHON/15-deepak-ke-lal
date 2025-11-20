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
    """Execute flight search agent."""
    from agent.flight_agent import FlightAgent
    
    if state.get("cancel_requested"):
        return {**state, "status": "cancelled"}
    
    agent = FlightAgent()
    
    # Prepare progress callback that updates state
    partial_results = []
    
    async def progress_cb(data):
        partial_results.append(data)
    
    # Create cancel event
    cancel_event = asyncio.Event()
    if state.get("cancel_requested"):
        cancel_event.set()
    
    # Run agent
    result = await agent.run(
        state["user_id"],
        state.get("flight_input", {}),
        progress_cb,
        cancel_event
    )
    
    return {
        **state,
        "flight_results": result,
        "status": "flight_completed" if result.get("status") == "completed" else "flight_partial"
    }


async def hotel_node(state: AgentState) -> AgentState:
    """Execute hotel search agent."""
    from agent.hotel_agent import HotelAgent
    
    if state.get("cancel_requested"):
        return {**state, "status": "cancelled"}
    
    agent = HotelAgent()
    partial_results = []
    
    async def progress_cb(data):
        partial_results.append(data)
    
    cancel_event = asyncio.Event()
    if state.get("cancel_requested"):
        cancel_event.set()
    
    result = await agent.run(
        state["user_id"],
        state.get("hotel_input", {}),
        progress_cb,
        cancel_event
    )
    
    return {
        **state,
        "hotel_results": result,
        "status": "hotel_completed" if result.get("status") == "completed" else "hotel_partial"
    }


def response_assembler_node(state: AgentState) -> AgentState:
    """Assemble final response from agent results."""
    parts = []
    
    if state.get("flight_results"):
        flight_data = state["flight_results"]
        if flight_data.get("status") == "completed":
            results = flight_data.get("results", [])
            parts.append(f"Found {len(results)} flights: {results}")
        elif flight_data.get("status") == "cancelled":
            parts.append(f"Flight search cancelled (partial: {flight_data.get('partial', {})})")
    
    if state.get("hotel_results"):
        hotel_data = state["hotel_results"]
        if hotel_data.get("status") == "completed":
            results = hotel_data.get("results", [])
            parts.append(f"Found {len(results)} hotels: {results}")
        elif hotel_data.get("status") == "cancelled":
            parts.append(f"Hotel search cancelled (partial: {hotel_data.get('partial', {})})")
    
    final_response = " | ".join(parts) if parts else "No results available."
    
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
