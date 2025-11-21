import asyncio
import uuid
from typing import Dict, Any
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage

try:
    from .state_store import StateStore
    from .langgraph_react_agent import create_react_agent
    from .interruption_manager import InterruptionManager, TaskStatus
except ImportError:
    from state_store import StateStore
    from langgraph_react_agent import create_react_agent
    from interruption_manager import InterruptionManager, TaskStatus


class AgentManager:
    """Orchestrates LangGraph workflow with interruption support.
    
    Key features:
    - Automatic interruption of existing tasks when new queries arrive
    - Preservation of partial results from interrupted agents
    - Context transfer between queries
    - Real-time status updates
    """

    def __init__(self, ws_manager=None):
        self._store = StateStore()
        self._interruption_manager = InterruptionManager()
        self._thread_ids: Dict[str, str] = {}
        self._agent = create_react_agent()
        self._ws_manager = ws_manager

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
                print(f"🚀 Starting workflow for user {user_id}, message: {message}")
                
                # Send initial status via WebSocket
                if self._ws_manager:
                    await self._ws_manager.send_message(user_id, {
                        "type": "status_update",
                        "task_id": task_id,
                        "status": "processing",
                        "current_agent": "ReAct Agent",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Update status to running
                await self._interruption_manager.update_task_status(
                    user_id, TaskStatus.RUNNING
                )
                print(f"✅ Task status updated to RUNNING")
                
                # Get previous context for potential continuation
                previous_context = await self._interruption_manager.get_previous_context(
                    user_id, message
                )
                print(f"📝 Previous context: {previous_context}")
                
                # Get cancellation event from interruption manager
                cancel_event = await self._interruption_manager.get_cancellation_event(user_id)
                print(f"🔔 Cancellation event obtained")
                
                # Prepare initial state for ReAct agent
                conversation = await self._store.get_conversation(user_id)
                print(f"💬 Conversation history: {len(conversation)} messages")
                
                # Convert conversation to LangChain messages
                messages = []
                for msg in conversation:
                    if msg["sender"] == "user":
                        messages.append(HumanMessage(content=msg["message"]))
                    elif msg["sender"] == "assistant":
                        messages.append(AIMessage(content=msg["message"]))
                
                # Add current message (already saved to conversation history)
                # messages.append(HumanMessage(content=message))
                
                initial_state = {
                    "messages": messages
                }
                
                config = {
                    "configurable": {
                        "thread_id": thread_id
                    },
                    "recursion_limit": 10  # Limit recursion to prevent infinite loops
                }
                
                print(f"🤖 Invoking ReAct agent...")
                print(f"   Agent object: {self._agent}")
                print(f"   Initial state: {initial_state}")
                print(f"   Config: {config}")
                
                # Send agent execution status
                if self._ws_manager:
                    await self._ws_manager.send_message(user_id, {
                        "type": "status_update",
                        "task_id": task_id,
                        "status": "thinking",
                        "current_agent": "Travel Assistant AI",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Run the ReAct agent
                result = await asyncio.to_thread(
                    self._agent.invoke,
                    initial_state,
                    config
                )
                print(f"✅ Agent completed! Result: {result}")
                
                # Check if cancelled during execution
                if cancel_event and cancel_event.is_set():
                    raise asyncio.CancelledError("Task cancelled by user")
                
                # Extract final response from agent
                final_messages = result.get("messages", [])
                response = final_messages[-1].content if final_messages else "No response generated"
                
                # Analyze messages to detect tool usage and send appropriate status updates
                if self._ws_manager:
                    current_agent = "Travel Assistant AI"
                    
                    for msg in final_messages:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                tool_name = tool_call.get('name', '')
                                if 'flight' in tool_name.lower():
                                    current_agent = "Flight Search Agent"
                                    await self._ws_manager.send_message(user_id, {
                                        "type": "status_update",
                                        "task_id": task_id,
                                        "status": "searching",
                                        "current_agent": current_agent,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                elif 'hotel' in tool_name.lower():
                                    current_agent = "Hotel Search Agent"
                                    await self._ws_manager.send_message(user_id, {
                                        "type": "status_update",
                                        "task_id": task_id,
                                        "status": "searching",
                                        "current_agent": current_agent,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                elif 'booking' in tool_name.lower():
                                    current_agent = "Booking Agent"
                                    await self._ws_manager.send_message(user_id, {
                                        "type": "status_update",
                                        "task_id": task_id,
                                        "status": "processing",
                                        "current_agent": current_agent,
                                        "timestamp": datetime.now().isoformat()
                                    })
                
                # Save to conversation history
                await self._store.append_message(user_id, "assistant", response)
                
                # Analyze response content to determine final agent status
                final_agent = "Travel Assistant AI"
                if self._ws_manager:
                    response_lower = response.lower()
                    if any(word in response_lower for word in ['flight', 'airline', 'departure', 'arrival']):
                        if any(word in response_lower for word in ['hotel', 'accommodation', 'stay', 'room']):
                            final_agent = "Multi-Service Agent"
                        else:
                            final_agent = "Flight Search Agent"
                    elif any(word in response_lower for word in ['hotel', 'accommodation', 'stay', 'room']):
                        final_agent = "Hotel Search Agent"
                    elif any(word in response_lower for word in ['book', 'reservation', 'confirm']):
                        final_agent = "Booking Agent"
                
                # Mark task as completed
                await self._interruption_manager.complete_task(
                    user_id=user_id,
                    final_results={"response": response},
                    status=TaskStatus.COMPLETED
                )
                
                # Send response via WebSocket if available
                if self._ws_manager:
                    print(f"📡 Sending WebSocket message to {user_id}")
                    await self._ws_manager.send_message(user_id, {
                        "type": "response",
                        "task_id": task_id,
                        "status": "completed",
                        "current_agent": final_agent,
                        "response": response,
                        "timestamp": datetime.now().isoformat()
                    })
                    print(f"✅ WebSocket message sent!")
                else:
                    print(f"⚠️ No WebSocket manager available!")
                
                return {"task_id": task_id, "response": response}
                
            except asyncio.CancelledError:
                print(f"⚠️ Task cancelled for user {user_id}")
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
                print(f"❌ ERROR in workflow: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                error_msg = str(e)
                
                await self._interruption_manager.update_task_status(
                    user_id, TaskStatus.FAILED, error=error_msg
                )
                
                return {"status": "error", "task_id": task_id, "error": error_msg}

        # Create and track the task
        task = asyncio.create_task(_run())
        
        # Add done callback to catch any exceptions
        def task_done_callback(t):
            try:
                exc = t.exception()
                if exc:
                    print(f"❌ TASK EXCEPTION for {user_id}: {type(exc).__name__}: {str(exc)}")
                    import traceback
                    traceback.print_exception(type(exc), exc, exc.__traceback__)
            except asyncio.CancelledError:
                print(f"✅ Task cancelled for {user_id}")
            except Exception as e:
                print(f"❌ Error in task callback: {e}")
        
        task.add_done_callback(task_done_callback)
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