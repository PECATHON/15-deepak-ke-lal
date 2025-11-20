from __future__ import annotations
import asyncio
from typing import Any, Callable


class BaseAgent:
	"""Abstract base class for agents.

	Agents should implement `run` which accepts: `user_id`, `input_data`, a
	`progress_callback` coroutine function to report partial results, and an
	`asyncio.Event` used for cancellation.
	"""

	name: str = "base"

	async def run(
		self,
		user_id: str,
		input_data: dict,
		progress_callback: Callable[[dict], Any],
		cancel_event: asyncio.Event,
	) -> dict:
		raise NotImplementedError()

