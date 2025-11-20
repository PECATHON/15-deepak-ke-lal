from typing import Dict, Any, Optional
import asyncio
from datetime import datetime


class StateStore:
	"""In-memory conversation and partial-result store with interruption support.

	This stores per-user conversation history, partial results from agents,
	and task metadata for context preservation during interruptions.
	"""

	def __init__(self):
		self._conversations: Dict[str, list] = {}
		self._partials: Dict[str, dict] = {}
		self._locks: Dict[str, asyncio.Lock] = {}
		
		# Enhanced tracking for interruption support
		self._task_metadata: Dict[str, dict] = {}  # Task execution metadata
		self._interruption_context: Dict[str, list] = {}  # History of interrupted tasks

	def _lock_for(self, user_id: str) -> asyncio.Lock:
		if user_id not in self._locks:
			self._locks[user_id] = asyncio.Lock()
		return self._locks[user_id]

	async def append_message(self, user_id: str, sender: str, message: str):
		async with self._lock_for(user_id):
			if user_id not in self._conversations:
				self._conversations[user_id] = []
			self._conversations[user_id].append({"sender": sender, "message": message})

	async def get_conversation(self, user_id: str):
		async with self._lock_for(user_id):
			return list(self._conversations.get(user_id, []))

	async def save_partial(self, user_id: str, agent_name: str, data: Any):
		async with self._lock_for(user_id):
			if user_id not in self._partials:
				self._partials[user_id] = {}
			self._partials[user_id][agent_name] = data

	async def get_partials(self, user_id: str):
		async with self._lock_for(user_id):
			return dict(self._partials.get(user_id, {}))

	async def clear_partials(self, user_id: str, agent_name: str | None = None):
		async with self._lock_for(user_id):
			if user_id not in self._partials:
				return
			if agent_name is None:
				self._partials[user_id] = {}
			else:
				self._partials[user_id].pop(agent_name, None)
	
	async def save_task_metadata(
		self,
		user_id: str,
		task_id: str,
		metadata: dict
	):
		"""Save task execution metadata for interruption tracking.
		
		Args:
			user_id: User identifier
			task_id: Task identifier
			metadata: Dictionary containing task state (status, current_agent, etc.)
		"""
		async with self._lock_for(user_id):
			if user_id not in self._task_metadata:
				self._task_metadata[user_id] = {}
			
			metadata["updated_at"] = datetime.now().isoformat()
			self._task_metadata[user_id][task_id] = metadata
	
	async def get_task_metadata(self, user_id: str, task_id: Optional[str] = None) -> Optional[dict]:
		"""Get task metadata for a user.
		
		Args:
			user_id: User identifier
			task_id: Specific task ID (if None, returns latest task)
			
		Returns:
			Task metadata dictionary or None
		"""
		async with self._lock_for(user_id):
			if user_id not in self._task_metadata:
				return None
			
			if task_id:
				return self._task_metadata[user_id].get(task_id)
			
			# Return most recent task metadata
			tasks = self._task_metadata[user_id]
			if not tasks:
				return None
			
			latest_task_id = max(tasks.keys(), key=lambda k: tasks[k].get("updated_at", ""))
			return tasks[latest_task_id]
	
	async def preserve_interrupted_context(
		self,
		user_id: str,
		task_id: str,
		context: dict
	):
		"""Preserve context from an interrupted task.
		
		This enables context transfer when a new query arrives during processing.
		
		Args:
			user_id: User identifier
			task_id: Task identifier that was interrupted
			context: Context to preserve (partial results, state, etc.)
		"""
		async with self._lock_for(user_id):
			if user_id not in self._interruption_context:
				self._interruption_context[user_id] = []
			
			context["task_id"] = task_id
			context["interrupted_at"] = datetime.now().isoformat()
			
			self._interruption_context[user_id].append(context)
			
			# Keep only last 5 interrupted contexts per user
			if len(self._interruption_context[user_id]) > 5:
				self._interruption_context[user_id].pop(0)
	
	async def get_interrupted_contexts(self, user_id: str) -> list:
		"""Get history of interrupted task contexts for a user.
		
		Args:
			user_id: User identifier
			
		Returns:
			List of interrupted contexts (most recent last)
		"""
		async with self._lock_for(user_id):
			return list(self._interruption_context.get(user_id, []))
	
	async def get_latest_interrupted_context(self, user_id: str) -> Optional[dict]:
		"""Get the most recent interrupted context for a user.
		
		Useful for context transfer to new queries.
		
		Args:
			user_id: User identifier
			
		Returns:
			Most recent interrupted context or None
		"""
		contexts = await self.get_interrupted_contexts(user_id)
		return contexts[-1] if contexts else None

