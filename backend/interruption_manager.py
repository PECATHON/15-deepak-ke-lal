"""Interruption Manager for handling request cancellation and context preservation.

This module provides the core infrastructure for:
1. Detecting new queries during active processing
2. Gracefully cancelling running agent operations
3. Preserving partial results from interrupted agents
4. Transferring context between agents
5. Supporting resume/continuation logic
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Status states for agent tasks."""
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskContext:
    """Context information for a running or completed task."""
    task_id: str
    user_id: str
    query: str
    intent: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    
    # Agent execution state
    current_agent: Optional[str] = None
    agents_completed: list[str] = field(default_factory=list)
    
    # Partial results from agents
    partial_results: Dict[str, Any] = field(default_factory=dict)
    
    # Final results
    final_results: Optional[Dict[str, Any]] = None
    
    # Cancellation support
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    
    # Error tracking
    error: Optional[str] = None
    
    # Asyncio task reference
    task: Optional[asyncio.Task] = None


class InterruptionManager:
    """Manages task interruption, cancellation, and context preservation.
    
    Key responsibilities:
    - Track active tasks per user
    - Provide cancellation tokens (Events) for agents to check
    - Preserve partial results when tasks are interrupted
    - Enable context transfer when switching between queries
    - Support task resumption with preserved context
    """
    
    def __init__(self):
        # Track active task context per user
        self._user_tasks: Dict[str, TaskContext] = {}
        
        # History of interrupted tasks (for context transfer)
        self._interrupted_history: Dict[str, list[TaskContext]] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Callbacks for status updates (can be used for WebSocket streaming)
        self._status_callbacks: Dict[str, list[Callable]] = {}
    
    async def create_task_context(
        self, 
        user_id: str, 
        query: str, 
        intent: str = ""
    ) -> TaskContext:
        """Create a new task context for a user query.
        
        If there's an active task for this user, it will be interrupted.
        
        Args:
            user_id: User identifier
            query: User's query text
            intent: Detected intent (flight, hotel, both, etc.)
            
        Returns:
            TaskContext for the new task
        """
        async with self._lock:
            # Interrupt existing task if present
            if user_id in self._user_tasks:
                await self._interrupt_task_internal(user_id, preserve_context=True)
            
            # Create new context
            task_id = str(uuid.uuid4())
            context = TaskContext(
                task_id=task_id,
                user_id=user_id,
                query=query,
                intent=intent,
                status=TaskStatus.QUEUED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self._user_tasks[user_id] = context
            
            # Notify callbacks
            await self._notify_status_change(user_id, context)
            
            return context
    
    async def update_task_status(
        self,
        user_id: str,
        status: TaskStatus,
        current_agent: Optional[str] = None,
        partial_results: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Update the status of a running task.
        
        Args:
            user_id: User identifier
            status: New status
            current_agent: Currently executing agent name
            partial_results: Partial results to preserve
            error: Error message if failed
        """
        async with self._lock:
            if user_id not in self._user_tasks:
                return
            
            context = self._user_tasks[user_id]
            context.status = status
            context.updated_at = datetime.now()
            
            if current_agent:
                context.current_agent = current_agent
                if current_agent not in context.agents_completed:
                    # Mark previous agents as completed when moving to new one
                    if context.current_agent and context.current_agent != current_agent:
                        context.agents_completed.append(context.current_agent)
            
            if partial_results:
                # Merge partial results
                for agent_name, results in partial_results.items():
                    context.partial_results[agent_name] = results
            
            if error:
                context.error = error
            
            # Notify callbacks
            await self._notify_status_change(user_id, context)
    
    async def save_partial_results(
        self,
        user_id: str,
        agent_name: str,
        results: Any
    ):
        """Save partial results from an agent.
        
        These results are preserved even if the task is interrupted.
        
        Args:
            user_id: User identifier
            agent_name: Name of the agent producing results
            results: Partial results data
        """
        async with self._lock:
            if user_id not in self._user_tasks:
                return
            
            context = self._user_tasks[user_id]
            context.partial_results[agent_name] = results
            context.updated_at = datetime.now()
            
            # Notify callbacks
            await self._notify_status_change(user_id, context)
    
    async def get_task_context(self, user_id: str) -> Optional[TaskContext]:
        """Get the current task context for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            TaskContext if exists, None otherwise
        """
        async with self._lock:
            return self._user_tasks.get(user_id)
    
    async def get_cancellation_event(self, user_id: str) -> Optional[asyncio.Event]:
        """Get the cancellation event for a user's task.
        
        Agents should check this event periodically and exit gracefully if set.
        
        Args:
            user_id: User identifier
            
        Returns:
            asyncio.Event that will be set when cancellation is requested
        """
        context = await self.get_task_context(user_id)
        return context.cancel_event if context else None
    
    async def interrupt_task(self, user_id: str, preserve_context: bool = True):
        """Interrupt the currently running task for a user.
        
        This is the main entry point for request interruption.
        
        Args:
            user_id: User identifier
            preserve_context: Whether to preserve partial results and context
        """
        async with self._lock:
            await self._interrupt_task_internal(user_id, preserve_context)
    
    async def _interrupt_task_internal(self, user_id: str, preserve_context: bool):
        """Internal interrupt implementation (assumes lock is held).
        
        Args:
            user_id: User identifier
            preserve_context: Whether to preserve partial results and context
        """
        if user_id not in self._user_tasks:
            return
        
        context = self._user_tasks[user_id]
        
        # Set cancellation event (agents will detect this)
        context.cancel_event.set()
        
        # Cancel the asyncio task if it exists
        if context.task and not context.task.done():
            context.task.cancel()
        
        # Update status
        context.status = TaskStatus.INTERRUPTED
        context.updated_at = datetime.now()
        
        # Preserve in history if requested
        if preserve_context:
            if user_id not in self._interrupted_history:
                self._interrupted_history[user_id] = []
            self._interrupted_history[user_id].append(context)
            
            # Keep only last 5 interrupted tasks per user
            if len(self._interrupted_history[user_id]) > 5:
                self._interrupted_history[user_id].pop(0)
        
        # Notify callbacks
        await self._notify_status_change(user_id, context)
    
    async def complete_task(
        self,
        user_id: str,
        final_results: Dict[str, Any],
        status: TaskStatus = TaskStatus.COMPLETED
    ):
        """Mark a task as completed with final results.
        
        Args:
            user_id: User identifier
            final_results: Final assembled results
            status: Final status (COMPLETED or FAILED)
        """
        async with self._lock:
            if user_id not in self._user_tasks:
                return
            
            context = self._user_tasks[user_id]
            context.status = status
            context.final_results = final_results
            context.updated_at = datetime.now()
            
            # Mark current agent as completed
            if context.current_agent and context.current_agent not in context.agents_completed:
                context.agents_completed.append(context.current_agent)
            
            # Notify callbacks
            await self._notify_status_change(user_id, context)
    
    async def get_previous_context(
        self,
        user_id: str,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """Get relevant context from previous interrupted tasks.
        
        This enables context transfer - if a new query is related to an
        interrupted query, we can use the partial results.
        
        Args:
            user_id: User identifier
            query: New query to check for relevance
            
        Returns:
            Dictionary with relevant context from previous tasks
        """
        async with self._lock:
            if user_id not in self._interrupted_history:
                return None
            
            # Get most recent interrupted task
            history = self._interrupted_history[user_id]
            if not history:
                return None
            
            # For now, return the most recent interrupted task's context
            # In production, you'd use LLM to determine relevance
            last_interrupted = history[-1]
            
            return {
                "previous_query": last_interrupted.query,
                "previous_intent": last_interrupted.intent,
                "partial_results": last_interrupted.partial_results,
                "agents_completed": last_interrupted.agents_completed,
                "interrupted_at": last_interrupted.updated_at.isoformat()
            }
    
    async def register_status_callback(
        self,
        user_id: str,
        callback: Callable[[TaskContext], Any]
    ):
        """Register a callback to be notified of status changes.
        
        Useful for WebSocket streaming of agent progress.
        
        Args:
            user_id: User identifier
            callback: Async function to call with TaskContext on updates
        """
        async with self._lock:
            if user_id not in self._status_callbacks:
                self._status_callbacks[user_id] = []
            self._status_callbacks[user_id].append(callback)
    
    async def unregister_status_callback(
        self,
        user_id: str,
        callback: Callable[[TaskContext], Any]
    ):
        """Unregister a status callback.
        
        Args:
            user_id: User identifier
            callback: Callback function to remove
        """
        async with self._lock:
            if user_id in self._status_callbacks:
                try:
                    self._status_callbacks[user_id].remove(callback)
                except ValueError:
                    pass
    
    async def _notify_status_change(self, user_id: str, context: TaskContext):
        """Notify all registered callbacks of a status change.
        
        Args:
            user_id: User identifier
            context: Updated task context
        """
        if user_id not in self._status_callbacks:
            return
        
        for callback in self._status_callbacks[user_id]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(context)
                else:
                    callback(context)
            except Exception as e:
                # Log error but don't fail the notification
                print(f"Error in status callback: {e}")
    
    async def set_task_reference(self, user_id: str, task: asyncio.Task):
        """Set the asyncio Task reference for cancellation support.
        
        Args:
            user_id: User identifier
            task: The asyncio Task running the workflow
        """
        async with self._lock:
            if user_id in self._user_tasks:
                self._user_tasks[user_id].task = task
    
    def get_status_dict(self, user_id: str) -> Dict[str, Any]:
        """Get status as a serializable dictionary.
        
        Args:
            user_id: User identifier
            
        Returns:
            Status dictionary for API responses
        """
        if user_id not in self._user_tasks:
            return {"status": "idle"}
        
        context = self._user_tasks[user_id]
        
        return {
            "task_id": context.task_id,
            "status": context.status.value,
            "query": context.query,
            "intent": context.intent,
            "current_agent": context.current_agent,
            "agents_completed": context.agents_completed,
            "partial_results": context.partial_results,
            "final_results": context.final_results,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "error": context.error
        }
