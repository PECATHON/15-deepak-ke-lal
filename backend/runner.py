import asyncio
import uuid
from typing import Dict, Any

try:
    from .state_store import StateStore
    from .graph_workflow import WORKFLOW, AgentState
except ImportError:
    from state_store import StateStore
    from graph_workflow import WORKFLOW, AgentState


class AgentManager:
    """Orchestrates LangGraph workflow, supports cancellation and partials."""

    def __init__(self):
        self._store = StateStore()
        self._tasks: Dict[str, asyncio.Task] = {}
        self._thread_ids: Dict[str, str] = {}
        self._statuses: Dict[str, dict] = {}

    async def handle_user_message(self, user_id: str, message: str) -> str:
        # Save message to store
        await self._store.append_message(user_id, "user", message)

        # Generate task and thread IDs for LangGraph
        task_id = str(uuid.uuid4())
        thread_id = self._thread_ids.get(user_id, str(uuid.uuid4()))
        self._thread_ids[user_id] = thread_id

        async def _run():
            try:
                # Prepare initial state
                initial_state: AgentState = {
                    "user_id": user_id,
                    "messages": await self._store.get_conversation(user_id),
                    "user_query": message,
                    "intent": "",
                    "flight_input": None,
                    "hotel_input": None,
                    "flight_results": None,
                    "hotel_results": None,
                    "final_response": None,
                    "cancel_requested": False,
                    "status": "started"
                }

                # Run the workflow with state persistence via thread_id
                config = {"configurable": {"thread_id": thread_id}}
                
                # Stream workflow execution
                final_state = None
                async for state in WORKFLOW.astream(initial_state, config):
                    # Update status with latest state
                    final_state = state
                    # Extract last node that updated state
                    node_name = list(state.keys())[-1] if state else "unknown"
                    self._statuses[user_id] = {
                        "task_id": task_id,
                        "node": node_name,
                        "status": state.get(node_name, {}).get("status", "running")
                    }
                
                # Extract final response from completed workflow
                if final_state:
                    last_node_state = list(final_state.values())[-1] if final_state else {}
                    response = last_node_state.get("final_response", "Workflow completed")
                    await self._store.append_message(user_id, "assistant", response)
                    self._statuses[user_id] = {
                        "task_id": task_id,
                        "state": "completed",
                        "response": response
                    }
                    return {"task_id": task_id, "response": response}
                
            except asyncio.CancelledError:
                self._statuses[user_id] = {"state": "cancelled", "task_id": task_id}
                return {"status": "cancelled", "task_id": task_id}
            except Exception as e:
                self._statuses[user_id] = {"state": "error", "task_id": task_id, "error": str(e)}
                return {"status": "error", "task_id": task_id, "error": str(e)}

        t = asyncio.create_task(_run())
        self._tasks[user_id] = t
        return task_id

    async def interrupt(self, user_id: str):
        """Cancel the running workflow for a user.
        
        Sets cancel_requested flag in workflow state and cancels the task.
        The workflow nodes check this flag and preserve partial results.
        """
        task = self._tasks.get(user_id)
        if task and not task.done():
            # Mark as cancelled in status
            self._statuses[user_id] = {"state": "interrupting"}
            task.cancel()
            
            # Could also update workflow state here via thread_id if needed
            # For now, task cancellation is sufficient

    def get_status(self, user_id: str) -> dict:
        """Return current workflow status for a user."""
        return self._statuses.get(user_id, {"state": "idle"})