"""
LangGraph-based Multi-Agent Coordinator for Travel Planning.

This module implements a LangGraph workflow that orchestrates between
FlightAgent and HotelAgent, with support for:
- Intent detection and routing
- Parallel agent execution
- Request interruption and cancellation
- Partial result preservation
- Context transfer between agents
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
try:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
except ImportError:
    from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .flight_agent import FlightAgent
from .hotel_agent import HotelAgent
from ..state_store import StateStore
from ..intent_detector import IntentDetector

logger = logging.getLogger(__name__)


class TravelPlanningState(TypedDict):
    """
    State schema for the LangGraph travel planning workflow.
    
    This state is passed between nodes in the graph and maintains
    all context needed for multi-agent coordination.
    """
    # User input
    messages: Annotated[List[Any], operator.add]
    user_query: str
    request_id: str
    
    # Intent detection
    detected_intents: List[str]
    confidence: float
    extracted_params: Dict[str, Any]
    
    # Agent execution
    flight_results: Optional[Dict[str, Any]]
    hotel_results: Optional[Dict[str, Any]]
    
    # Interruption handling
    is_cancelled: bool
    partial_results: Dict[str, Any]
    
    # Context preservation
    conversation_history: List[Dict[str, Any]]
    current_step: str
    
    # Final response
    final_response: Optional[str]
    status: str


class LangGraphCoordinator:
    """
    LangGraph-based coordinator for multi-agent travel planning.
    
    Implements a state machine that:
    1. Receives user queries
    2. Detects intent (flight/hotel/both)
    3. Routes to appropriate agents
    4. Handles interruptions gracefully
    5. Preserves partial results
    6. Generates final response
    """
    
    def __init__(self, state_store: StateStore, llm_model: str = "gpt-4"):
        self.state_store = state_store
        self.flight_agent = FlightAgent(state_store)
        self.hotel_agent = HotelAgent(state_store)
        self.intent_detector = IntentDetector()
        
        # LLM for intent parsing and response generation
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        
        logger.info("[LangGraphCoordinator] Initialized with LLM-based workflow")
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph state machine workflow.
        
        Workflow:
        START → intent_detection → route_to_agents → execute_agents → generate_response → END
                                                   ↓
                                            check_interruption (can cancel and preserve)
        """
        workflow = StateGraph(TravelPlanningState)
        
        # Add nodes
        workflow.add_node("intent_detection", self._intent_detection_node)
        workflow.add_node("route_to_agents", self._route_to_agents_node)
        workflow.add_node("execute_flight_agent", self._execute_flight_node)
        workflow.add_node("execute_hotel_agent", self._execute_hotel_node)
        workflow.add_node("execute_both_agents", self._execute_both_nodes)
        workflow.add_node("check_interruption", self._check_interruption_node)
        workflow.add_node("generate_response", self._generate_response_node)
        
        # Set entry point
        workflow.set_entry_point("intent_detection")
        
        # Add edges
        workflow.add_edge("intent_detection", "route_to_agents")
        
        # Conditional routing based on detected intent
        workflow.add_conditional_edges(
            "route_to_agents",
            self._should_execute_which_agents,
            {
                "flight_only": "execute_flight_agent",
                "hotel_only": "execute_hotel_agent",
                "both": "execute_both_agents",
                "unknown": "generate_response"
            }
        )
        
        # After agent execution, check for interruptions
        workflow.add_edge("execute_flight_agent", "check_interruption")
        workflow.add_edge("execute_hotel_agent", "check_interruption")
        workflow.add_edge("execute_both_agents", "check_interruption")
        
        # After interruption check, generate response
        workflow.add_edge("check_interruption", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow
    
    async def _intent_detection_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Node 1: Detect user intent using IntentDetector.
        
        Determines if user wants:
        - Flight search only
        - Hotel search only
        - Both flight and hotel
        - Unknown (needs clarification)
        """
        logger.info(f"[IntentNode] Processing query: {state['user_query']}")
        
        # Use existing intent detector
        intent_result = self.intent_detector.detect(state['user_query'])
        
        state['detected_intents'] = intent_result['intents']
        state['confidence'] = intent_result['confidence']
        state['extracted_params'] = intent_result['params']
        state['current_step'] = 'intent_detected'
        
        # Add to conversation history
        state['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'step': 'intent_detection',
            'intents': intent_result['intents'],
            'confidence': intent_result['confidence']
        })
        
        logger.info(f"[IntentNode] Detected: {intent_result['intents']} (confidence: {intent_result['confidence']})")
        
        return state
    
    async def _route_to_agents_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Node 2: Determine routing based on detected intents.
        """
        logger.info(f"[RoutingNode] Routing based on intents: {state['detected_intents']}")
        
        state['current_step'] = 'routing_complete'
        
        return state
    
    def _should_execute_which_agents(self, state: TravelPlanningState) -> str:
        """
        Conditional edge function: determine which agents to execute.
        """
        intents = state['detected_intents']
        
        if 'flight' in intents and 'hotel' in intents:
            return "both"
        elif 'flight' in intents:
            return "flight_only"
        elif 'hotel' in intents:
            return "hotel_only"
        else:
            return "unknown"
    
    async def _execute_flight_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Node 3a: Execute FlightAgent.
        """
        logger.info("[FlightNode] Executing FlightAgent")
        
        try:
            # Extract flight parameters
            params = state['extracted_params']
            
            # Run flight agent
            result = await self.flight_agent.run(
                state['request_id'],
                {
                    'origin': params.get('origin', 'JFK'),
                    'destination': params.get('destination', 'LAX'),
                    'date': params.get('departure_date', '2025-12-20'),
                    'passengers': params.get('passengers', 1)
                }
            )
            
            state['flight_results'] = result
            state['current_step'] = 'flight_complete'
            
            # Update conversation history
            state['conversation_history'].append({
                'timestamp': datetime.now().isoformat(),
                'step': 'flight_execution',
                'status': result['status'],
                'results_count': len(result.get('results', []))
            })
            
            logger.info(f"[FlightNode] Found {len(result.get('results', []))} flights")
            
        except Exception as e:
            logger.error(f"[FlightNode] Error: {e}")
            state['flight_results'] = {'status': 'error', 'error': str(e), 'results': []}
        
        return state
    
    async def _execute_hotel_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Node 3b: Execute HotelAgent.
        """
        logger.info("[HotelNode] Executing HotelAgent")
        
        try:
            params = state['extracted_params']
            
            result = await self.hotel_agent.run(
                state['request_id'],
                {
                    'location': params.get('destination', 'Los Angeles'),
                    'checkin': params.get('departure_date', '2025-12-20'),
                    'checkout': params.get('return_date', '2025-12-22'),
                    'adults': params.get('passengers', 2),
                    'rooms': params.get('rooms', 1)
                }
            )
            
            state['hotel_results'] = result
            state['current_step'] = 'hotel_complete'
            
            state['conversation_history'].append({
                'timestamp': datetime.now().isoformat(),
                'step': 'hotel_execution',
                'status': result['status'],
                'results_count': len(result.get('results', []))
            })
            
            logger.info(f"[HotelNode] Found {len(result.get('results', []))} hotels")
            
        except Exception as e:
            logger.error(f"[HotelNode] Error: {e}")
            state['hotel_results'] = {'status': 'error', 'error': str(e), 'results': []}
        
        return state
    
    async def _execute_both_nodes(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Node 3c: Execute both FlightAgent and HotelAgent in parallel.
        """
        logger.info("[BothNode] Executing both agents in parallel")
        
        # Execute both agents concurrently
        flight_task = self._execute_flight_node(state.copy())
        hotel_task = self._execute_hotel_node(state.copy())
        
        flight_state, hotel_state = await asyncio.gather(flight_task, hotel_task)
        
        # Merge results
        state['flight_results'] = flight_state['flight_results']
        state['hotel_results'] = hotel_state['hotel_results']
        state['current_step'] = 'both_complete'
        state['conversation_history'].extend(flight_state['conversation_history'])
        state['conversation_history'].extend(hotel_state['conversation_history'])
        
        logger.info("[BothNode] Both agents completed")
        
        return state
    
    async def _check_interruption_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Node 4: Check if request was interrupted/cancelled.
        
        If cancelled:
        - Mark as cancelled
        - Preserve partial results
        - Update status
        """
        request_id = state['request_id']
        
        # Check if request was cancelled via state store
        agent_state = self.state_store.get_agent_state(request_id, 'flight_agent')
        is_cancelled = agent_state.get('status') == 'cancelled' if agent_state else False
        
        if is_cancelled:
            logger.info(f"[InterruptionNode] Request {request_id} was cancelled")
            
            # Preserve partial results
            partials = self.state_store.get_all_partials(request_id)
            state['is_cancelled'] = True
            state['partial_results'] = partials
            state['status'] = 'cancelled'
            
            state['conversation_history'].append({
                'timestamp': datetime.now().isoformat(),
                'step': 'interruption_detected',
                'partial_results_preserved': True
            })
        else:
            state['is_cancelled'] = False
            state['status'] = 'completed'
        
        return state
    
    async def _generate_response_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Node 5: Generate final response using LLM.
        
        Creates a natural language response summarizing:
        - What was found
        - Recommendations
        - Next steps
        """
        logger.info("[ResponseNode] Generating final response")
        
        # Build context for LLM
        context_parts = []
        
        if state.get('flight_results'):
            flights = state['flight_results'].get('results', [])
            context_parts.append(f"Found {len(flights)} flights.")
            if flights:
                cheapest = min(flights, key=lambda x: x.get('price_usd', float('inf')))
                context_parts.append(f"Cheapest: ${cheapest.get('price_usd', 'N/A')} on {cheapest.get('airline', 'N/A')}")
        
        if state.get('hotel_results'):
            hotels = state['hotel_results'].get('results', [])
            context_parts.append(f"Found {len(hotels)} hotels.")
            if hotels:
                best = max(hotels, key=lambda x: x.get('rating', 0))
                context_parts.append(f"Top rated: {best.get('name', 'N/A')} ({best.get('rating', 'N/A')}/10)")
        
        if state.get('is_cancelled'):
            context_parts.append("Request was cancelled, but partial results are preserved.")
        
        # Generate response
        prompt = f"""
        You are a travel planning assistant. Summarize the search results naturally:
        
        User Query: {state['user_query']}
        Results: {' '.join(context_parts)}
        Status: {state['status']}
        
        Provide a brief, friendly summary with recommendations.
        """
        
        try:
            response = await self.llm.ainvoke([SystemMessage(content=prompt)])
            state['final_response'] = response.content
        except Exception as e:
            logger.error(f"[ResponseNode] LLM error: {e}")
            state['final_response'] = ' '.join(context_parts)
        
        logger.info("[ResponseNode] Response generated")
        
        return state
    
    async def process_query(self, request_id: str, user_query: str) -> Dict[str, Any]:
        """
        Main entry point: process a user query through the LangGraph workflow.
        
        Args:
            request_id: Unique identifier for this request
            user_query: User's natural language query
            
        Returns:
            Dict containing final response and all results
        """
        logger.info(f"[LangGraphCoordinator] Processing query {request_id}: {user_query}")
        
        # Initialize state
        initial_state: TravelPlanningState = {
            'messages': [HumanMessage(content=user_query)],
            'user_query': user_query,
            'request_id': request_id,
            'detected_intents': [],
            'confidence': 0.0,
            'extracted_params': {},
            'flight_results': None,
            'hotel_results': None,
            'is_cancelled': False,
            'partial_results': {},
            'conversation_history': [],
            'current_step': 'initialized',
            'final_response': None,
            'status': 'running'
        }
        
        try:
            # Run the workflow
            final_state = await self.app.ainvoke(initial_state)
            
            # Build response
            response = {
                'request_id': request_id,
                'status': final_state['status'],
                'intents': final_state['detected_intents'],
                'confidence': final_state['confidence'],
                'flight_results': final_state.get('flight_results'),
                'hotel_results': final_state.get('hotel_results'),
                'partial_results': final_state.get('partial_results', {}),
                'final_response': final_state.get('final_response'),
                'conversation_history': final_state.get('conversation_history', [])
            }
            
            logger.info(f"[LangGraphCoordinator] Completed query {request_id}")
            
            return response
            
        except Exception as e:
            logger.error(f"[LangGraphCoordinator] Error processing query: {e}", exc_info=True)
            return {
                'request_id': request_id,
                'status': 'error',
                'error': str(e),
                'flight_results': None,
                'hotel_results': None
            }
    
    async def cancel_request(self, request_id: str) -> Dict[str, Any]:
        """
        Cancel an in-flight request and preserve partial results.
        
        This implements the interruption handling required by the assignment.
        """
        logger.info(f"[LangGraphCoordinator] Cancelling request {request_id}")
        
        # Cancel agents
        self.flight_agent.cancel()
        self.hotel_agent.cancel()
        
        # Mark as cancelled in state store
        self.state_store.mark_cancelled(request_id)
        
        # Get partial results
        partials = self.state_store.get_all_partials(request_id)
        
        return {
            'request_id': request_id,
            'status': 'cancelled',
            'message': 'Request cancelled successfully',
            'partial_results': partials
        }
