import asyncio
import uuid
from typing import Dict, Any

try:
    from .state_store import StateStore
    from .graph_workflow import WORKFLOW, AgentState
    from .interruption_manager import InterruptionManager, TaskStatus
except ImportError:
    from state_store import StateStore
    from graph_workflow import WORKFLOW, AgentState
    from interruption_manager import InterruptionManager, TaskStatus


class AgentManager:
    """Orchestrates LangGraph workflow with interruption support.
    
    Key features:
    - Automatic interruption of existing tasks when new queries arrive
    - Preservation of partial results from interrupted agents
    - Context transfer between queries
    - Real-time status updates
    """

    def __init__(self):
        self._store = StateStore()
        self._interruption_manager = InterruptionManager()
        self._thread_ids: Dict[str, str] = {}

    async def handle_user_message(self, user_id: str, message: str) -> str:
        """Handle a new user message with automatic interruption support.
        
        If a task is already running for this user, it will be gracefully
        interrupted and its partial results preserved.
        
        Args:
            user_id: User identifier
            message: User's message/query
            
        Returns:
            task_id: Unique identifier for this task
        """
        # Save message to conversation history
        await self._store.append_message(user_id, "user", message)

        # Create task context (this automatically interrupts existing task)
        context = await self._interruption_manager.create_task_context(
            user_id=user_id,
            query=message,
            intent=""  # Will be determined by router
        )
        
        task_id = context.task_id

        # Get or create thread ID for LangGraph state persistence
        thread_id = self._thread_ids.get(user_id, str(uuid.uuid4()))
        self._thread_ids[user_id] = thread_id

        async def _run():
            """Execute the workflow with interruption support."""
            try:
                # Update status to running
                await self._interruption_manager.update_task_status(
                    user_id, TaskStatus.RUNNING
                )
                
                # Get previous context for potential continuation
                previous_context = await self._interruption_manager.get_previous_context(
                    user_id, message
                )
                
                # Prepare initial state
                conversation = await self._store.get_conversation(user_id)
                partials = await self._store.get_partials(user_id)
                
                initial_state: AgentState = {
                    "user_id": user_id,
                    "messages": conversation,
                    "user_query": message,
                    "intent": "",
                    "flight_input": None,
                    "hotel_input": None,
                    "flight_results": None,
                    "hotel_results": None,
                    "final_response": None,
                    "cancel_requested": False,
                    "status": "started",
                    # Include previous context if available
                    "previous_context": previous_context,
                    "partial_results": partials
                }

                # Get cancellation event from interruption manager
                cancel_event = await self._interruption_manager.get_cancellation_event(user_id)
                
                # Run the workflow with state persistence
                config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "user_id": user_id,
                        "cancel_event": cancel_event
                    }
                }
                
                final_state = None
                
                # Stream workflow execution and track progress
                async for state_update in WORKFLOW.astream(initial_state, config):
                    # Check if cancelled
                    if cancel_event and cancel_event.is_set():
                        raise asyncio.CancelledError("Task cancelled by user")
                    
                    final_state = state_update
                    
                    # Extract node name and state
                    node_name = list(state_update.keys())[-1] if state_update else "unknown"
                    node_state = state_update.get(node_name, {})
                    
                    # Update interruption manager with progress
                    current_agent = node_state.get("current_agent", node_name)
                    
                    await self._interruption_manager.update_task_status(
                        user_id=user_id,
                        status=TaskStatus.RUNNING,
                        current_agent=current_agent
                    )
                    
                    # Save partial results if available
                    if node_state.get("flight_results"):
                        await self._interruption_manager.save_partial_results(
                            user_id, "flight", node_state["flight_results"]
                        )
                        await self._store.save_partial(
                            user_id, "flight", node_state["flight_results"]
                        )
                    
                    if node_state.get("hotel_results"):
                        await self._interruption_manager.save_partial_results(
                            user_id, "hotel", node_state["hotel_results"]
                        )
                        await self._store.save_partial(
                            user_id, "hotel", node_state["hotel_results"]
                        )
                
                # Extract final response
                if final_state:
                    last_node_state = list(final_state.values())[-1] if final_state else {}
                    response = last_node_state.get("final_response", "Workflow completed")
                    
                    # Save to conversation history
                    await self._store.append_message(user_id, "assistant", response)
                    
                    # Mark task as completed
                    await self._interruption_manager.complete_task(
                        user_id=user_id,
                        final_results={
                            "response": response,
                            "flight_results": last_node_state.get("flight_results"),
                            "hotel_results": last_node_state.get("hotel_results")
                        },
                        status=TaskStatus.COMPLETED
                    )
                    
                    return {"task_id": task_id, "response": response}
                
            except asyncio.CancelledError:
                # Preserve partial results on cancellation
                partials = await self._store.get_partials(user_id)
                
                await self._store.preserve_interrupted_context(
                    user_id=user_id,
                    task_id=task_id,
                    context={
                        "query": message,
                        "partial_results": partials,
                        "status": "interrupted"
                    }
                )
                
                await self._interruption_manager.update_task_status(
                    user_id, TaskStatus.INTERRUPTED
                )
                
                return {"status": "interrupted", "task_id": task_id, "partial_results": partials}
                
            except Exception as e:
                error_msg = str(e)
                
                await self._interruption_manager.update_task_status(
                    user_id, TaskStatus.FAILED, error=error_msg
                )
                
                return {"status": "error", "task_id": task_id, "error": error_msg}

        # Create and track the task
        task = asyncio.create_task(_run())
        await self._interruption_manager.set_task_reference(user_id, task)
        
        return task_id

    async def interrupt(self, user_id: str):
        """Interrupt the currently running workflow for a user.
        
        Gracefully cancels the task and preserves partial results.
        
        Args:
            user_id: User identifier
        """
        await self._interruption_manager.interrupt_task(
            user_id=user_id,
            preserve_context=True
        )

    def get_status(self, user_id: str) -> dict:
        """Get current workflow status for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Status dictionary with task info and partial results
        """
        return self._interruption_manager.get_status_dict(user_id)
    
    async def register_status_callback(self, user_id: str, callback):
        """Register a callback for real-time status updates.
        
        Useful for WebSocket streaming.
        
        Args:
            user_id: User identifier
            callback: Async function to call on status updates
        """
        await self._interruption_manager.register_status_callback(user_id, callback)
    
    async def unregister_status_callback(self, user_id: str, callback):
        """Unregister a status callback.
        
        Args:
            user_id: User identifier
            callback: Callback to remove
        """
        await self._interruption_manager.unregister_status_callback(user_id, callback)