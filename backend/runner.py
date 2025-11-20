"""
Task Runner - Manages async task execution and cancellation.

Responsibilities:
- Run coordinator tasks in background
- Track running tasks by request_id
- Support graceful cancellation
- Provide task status querying
- Handle task completion and cleanup
"""

import asyncio
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskRunner:
    """
    Background task manager for async agent execution.
    
    Capabilities:
    - Non-blocking task execution
    - Task lifecycle management
    - Cancellation support
    - Status tracking
    """
    
    def __init__(self, coordinator):
        """
        Initialize the task runner.
        
        Args:
            coordinator: CoordinatorAgent instance
        """
        self.coordinator = coordinator
        self.tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, Any] = {}
        self.start_times: Dict[str, datetime] = {}
        
        logger.info("[TaskRunner] Initialized")
    
    def start_task(self, request_id: str, message: str) -> str:
        """
        Start a new background task for message processing.
        
        Args:
            request_id: Unique request identifier
            message: User message to process
            
        Returns:
            request_id
        """
        if request_id in self.tasks and not self.tasks[request_id].done():
            logger.warning(f"[TaskRunner] Task {request_id} already running")
            return request_id
        
        logger.info(f"[TaskRunner] Starting task {request_id}")
        
        # Create background task
        task = asyncio.create_task(
            self._run_with_error_handling(request_id, message)
        )
        
        self.tasks[request_id] = task
        self.start_times[request_id] = datetime.utcnow()
        
        # Add completion callback
        task.add_done_callback(lambda t: self._on_task_complete(request_id, t))
        
        return request_id
    
    async def _run_with_error_handling(self, request_id: str, message: str):
        """
        Run coordinator with error handling.
        
        Args:
            request_id: Request identifier
            message: User message
        """
        try:
            result = await self.coordinator.process_message(message, request_id)
            self.results[request_id] = result
            logger.info(f"[TaskRunner] Task {request_id} completed successfully")
            
        except asyncio.CancelledError:
            logger.warning(f"[TaskRunner] Task {request_id} was cancelled")
            self.results[request_id] = {
                "request_id": request_id,
                "status": "cancelled",
                "message": "Task was cancelled"
            }
            raise
            
        except Exception as e:
            logger.error(f"[TaskRunner] Task {request_id} failed: {e}", exc_info=True)
            self.results[request_id] = {
                "request_id": request_id,
                "status": "error",
                "error": str(e)
            }
    
    def _on_task_complete(self, request_id: str, task: asyncio.Task):
        """
        Callback when task completes.
        
        Args:
            request_id: Request identifier
            task: Completed task
        """
        try:
            # Check if task raised exception
            if task.exception() and not isinstance(task.exception(), asyncio.CancelledError):
                logger.error(f"[TaskRunner] Task {request_id} exception: {task.exception()}")
        except asyncio.CancelledError:
            pass  # Already handled
        
        logger.info(f"[TaskRunner] Task {request_id} finished")
    
    def cancel_task(self, request_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            request_id: Request to cancel
            
        Returns:
            True if task was cancelled, False if not running
        """
        if request_id not in self.tasks:
            logger.warning(f"[TaskRunner] Task {request_id} not found")
            return False
        
        task = self.tasks[request_id]
        
        if task.done():
            logger.info(f"[TaskRunner] Task {request_id} already completed")
            return False
        
        logger.info(f"[TaskRunner] Cancelling task {request_id}")
        
        # Cancel via coordinator (propagates to agents)
        self.coordinator.cancel_request(request_id)
        
        # Cancel the task itself
        task.cancel()
        
        return True
    
    def get_status(self, request_id: str) -> Dict[str, Any]:
        """
        Get status of a task.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Dict with task status and results
        """
        if request_id not in self.tasks:
            return {
                "request_id": request_id,
                "status": "not_found",
                "message": "Task not found"
            }
        
        task = self.tasks[request_id]
        
        if task.done():
            # Task completed, return final result
            if request_id in self.results:
                result = self.results[request_id]
                result["is_running"] = False
                return result
            else:
                return {
                    "request_id": request_id,
                    "status": "completed",
                    "is_running": False
                }
        else:
            # Task still running, get partial results
            status = self.coordinator.get_status(request_id)
            status["is_running"] = True
            
            # Add elapsed time
            if request_id in self.start_times:
                elapsed = (datetime.utcnow() - self.start_times[request_id]).total_seconds()
                status["elapsed_seconds"] = round(elapsed, 2)
            
            return status
    
    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """
        Remove old completed tasks from memory.
        
        Args:
            max_age_seconds: Maximum age for completed tasks
        """
        now = datetime.utcnow()
        to_remove = []
        
        for request_id, start_time in self.start_times.items():
            age = (now - start_time).total_seconds()
            
            if age > max_age_seconds and request_id in self.tasks:
                if self.tasks[request_id].done():
                    to_remove.append(request_id)
        
        for request_id in to_remove:
            logger.info(f"[TaskRunner] Cleaning up old task {request_id}")
            del self.tasks[request_id]
            del self.start_times[request_id]
            if request_id in self.results:
                del self.results[request_id]
