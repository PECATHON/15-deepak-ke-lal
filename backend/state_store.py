from typing import Dict, Any
import asyncio


class StateStore:
	"""In-memory conversation and partial-result store.

	This is intentionally simple: it stores per-user conversation history,
	partial results from agents, and the current running task id.
	"""

	def __init__(self):
		self._conversations: Dict[str, list] = {}
		self._partials: Dict[str, dict] = {}
		self._locks: Dict[str, asyncio.Lock] = {}

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

