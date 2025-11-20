# Request Interruption System Documentation

## Overview

The Request Interruption System is a core component of the Travel Planning Assistant that enables graceful handling of user behavior where new queries arrive while agents are still processing previous requests. This is commonly known as "double-texting" or request cancellation.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Client (Frontend)                       │
│  - Sends queries                                             │
│  - Receives real-time updates via WebSocket                 │
│  - Can send new queries anytime                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  - POST /chat: Submit new queries                           │
│  - POST /interrupt: Explicit interruption                   │
│  - WS /ws/{user_id}: Real-time status streaming            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    AgentManager                              │
│  - Detects new queries during active processing             │
│  - Triggers automatic interruption                          │
│  - Coordinates workflow execution                           │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ InterruptionMgr  │    │   StateStore     │
│ - Task tracking  │    │ - Conversations  │
│ - Cancellation   │    │ - Partials       │
│ - Context mgmt   │    │ - Metadata       │
└────────┬─────────┘    └──────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                        │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐            │
│  │ Router   │ --> │  Flight  │ --> │Response  │            │
│  │          │     │  Agent   │     │Assembler │            │
│  └──────────┘     └──────────┘     └──────────┘            │
│                   ┌──────────┐                              │
│                   │  Hotel   │                              │
│                   │  Agent   │                              │
│                   └──────────┘                              │
│  Each node checks cancellation events                       │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Automatic Detection of New Queries

When a new message arrives for a user who already has an active task:

```python
# In runner.py - handle_user_message()
context = await self._interruption_manager.create_task_context(
    user_id=user_id,
    query=message,
    intent=""
)
# ↑ This automatically interrupts any existing task
```

**What happens:**
- InterruptionManager checks for existing tasks
- If found, sets cancellation event
- Cancels the asyncio.Task
- Preserves partial results in history
- Creates new task context

### 2. Graceful Cancellation

Agents check for cancellation at multiple points:

```python
# In graph_workflow.py - flight_node()
if state.get("cancel_requested"):
    return {
        **state,
        "flight_results": {"status": "cancelled", "partial": partial_data}
    }

# Agents also check during execution
cancel_event = asyncio.Event()
result = await agent.run(..., cancel_event)
```

**Cancellation points:**
- Before agent starts
- During API calls (via cancel_event)
- After each partial result
- In exception handlers (asyncio.CancelledError)

### 3. Partial Result Preservation

Multiple levels of preservation:

**Level 1: In-Memory (InterruptionManager)**
```python
await manager.save_partial_results(
    user_id="user123",
    agent_name="flight",
    results={"found": 10, "searching": True}
)
```

**Level 2: State Store**
```python
await store.save_partial(user_id, "flight", partial_data)
await store.preserve_interrupted_context(user_id, task_id, context)
```

**Level 3: Agent Return Values**
```python
return {
    "status": "cancelled",
    "partial": last_partial_result
}
```

### 4. Context Transfer

Previous task context is available to new tasks:

```python
# In runner.py
previous_context = await self._interruption_manager.get_previous_context(
    user_id, message
)

# Included in initial state
initial_state = {
    ...
    "previous_context": previous_context,
    "partial_results": partials
}
```

**Available context includes:**
- Previous query text
- Detected intent
- Partial results from all agents
- List of completed agents
- Timestamp of interruption

### 5. Real-time Updates via WebSocket

Clients receive streaming updates:

```javascript
// Frontend WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/user123');

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    // update.type === 'status_update'
    // update.status: running, interrupted, completed
    // update.current_agent: flight, hotel, etc.
    // update.partial_results: {...}
};
```

## Technical Implementation

### InterruptionManager Class

**Core Methods:**

| Method | Purpose |
|--------|---------|
| `create_task_context()` | Create new task, auto-interrupt existing |
| `interrupt_task()` | Explicitly interrupt a task |
| `save_partial_results()` | Save partial results from agents |
| `get_cancellation_event()` | Get asyncio.Event for cancellation checks |
| `get_previous_context()` | Retrieve context from interrupted tasks |
| `register_status_callback()` | Register WebSocket callbacks |

**TaskContext Data Structure:**

```python
@dataclass
class TaskContext:
    task_id: str                    # Unique identifier
    user_id: str                    # User identifier
    query: str                      # User's query
    intent: str                     # Detected intent
    status: TaskStatus              # Current status
    current_agent: str              # Currently executing agent
    agents_completed: list[str]     # Completed agents
    partial_results: Dict[str, Any] # Partial results by agent
    cancel_event: asyncio.Event     # Cancellation signal
    task: asyncio.Task              # Task reference for cancellation
```

### Agent Integration

Agents must support interruption by:

1. **Accepting cancel_event parameter:**
```python
async def run(self, user_id: str, input_data: dict, 
              progress_callback: Callable, 
              cancel_event: asyncio.Event):
```

2. **Checking cancellation periodically:**
```python
if cancel_event.is_set():
    await progress_callback({
        "status": "cancelled",
        "partial": current_partial_results
    })
    return {"status": "cancelled", "partial": current_partial_results}
```

3. **Handling CancelledError:**
```python
try:
    results = await search_api(...)
except asyncio.CancelledError:
    return {"status": "cancelled", "partial": last_partial}
```

## Usage Examples

### Example 1: Basic Interruption

```python
# User sends first query
task_id_1 = await manager.handle_user_message(
    "user123",
    "Find flights from NYC to London"
)

# While processing, user sends new query
task_id_2 = await manager.handle_user_message(
    "user123", 
    "Actually, find hotels in Paris instead"
)
# → First task is automatically interrupted
# → Partial flight results are preserved
```

### Example 2: Explicit Interruption

```python
# Start a query
task_id = await manager.handle_user_message("user123", "Find hotels in Tokyo")

# User clicks "Cancel" button
await manager.interrupt("user123")

# Check preserved results
status = manager.get_status("user123")
partial = status.get("partial_results", {})
```

### Example 3: Context Continuation

```python
# First query (interrupted)
await manager.handle_user_message("user123", "Flights to Rome on Dec 25")
# ... gets interrupted ...

# Second query (can use previous context)
await manager.handle_user_message("user123", "Also find hotels in Rome")
# → Router can detect relationship to previous query
# → Can reuse partial flight results if relevant
```

## WebSocket Protocol

### Client Connection
```
WS /ws/{user_id}
```

### Message Types

**Status Update (Server → Client):**
```json
{
  "type": "status_update",
  "task_id": "abc-123",
  "status": "running",
  "current_agent": "flight",
  "partial_results": {
    "flight": {"found": 5, "searching": true}
  },
  "timestamp": "2025-11-21T10:30:00"
}
```

**Ping (Client → Server):**
```json
{
  "type": "ping"
}
```

**Pong (Server → Client):**
```json
{
  "type": "pong"
}
```

## Testing

### Test Scenarios

Run the test suite:
```bash
cd backend
python test_interruption.py
```

**Tests included:**
1. ✅ Basic Interruption - Cancel running task
2. ✅ Partial Result Preservation - Verify partials saved
3. ✅ Context Transfer - Use previous results
4. ✅ Multiple Interruptions - Rapid successive queries
5. ✅ Multi-Agent Interruption - Cancel multi-agent task
6. ✅ Normal Completion - Verify non-interrupted flow
7. ✅ InterruptionManager Direct - Unit tests

### Manual Testing

**Using curl:**

```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload

# Terminal 2: Send queries
# First query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test1", "message": "Find flights to Paris"}'

# Interrupt with new query (within 2 seconds)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test1", "message": "Find hotels in London"}'

# Check status
curl http://localhost:8000/status/test1
```

**Using WebSocket client:**

```javascript
// test_websocket.html
const ws = new WebSocket('ws://localhost:8000/ws/test_user');

ws.onopen = () => {
    console.log('Connected');
    // Send ping every 30 seconds
    setInterval(() => {
        ws.send(JSON.stringify({type: 'ping'}));
    }, 30000);
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Update:', data);
    
    if (data.type === 'status_update') {
        console.log(`Agent: ${data.current_agent}`);
        console.log(`Status: ${data.status}`);
        console.log('Partials:', data.partial_results);
    }
};
```

## Performance Considerations

### Memory Management
- Interrupted task history limited to 5 per user
- Partial results cleared after successful completion
- WebSocket connections cleaned up on disconnect

### Latency
- Cancellation event check: ~1ms
- Task cancellation propagation: ~10-50ms
- Context retrieval: ~1ms (in-memory)

### Concurrency
- AsyncIO event loop handles multiple users
- Per-user locks prevent race conditions
- Task cancellation is non-blocking

## Error Handling

### Cancellation Errors
```python
try:
    result = await agent.run(...)
except asyncio.CancelledError:
    # Preserve partial results
    await store.preserve_interrupted_context(...)
    raise  # Re-raise to propagate cancellation
```

### WebSocket Errors
```python
try:
    await websocket.send_json(message)
except Exception as e:
    logger.error(f"WebSocket error: {e}")
    ws_manager.disconnect(user_id)
```

### Partial Result Errors
```python
# Graceful degradation
partial_results = status.get('partial_results', {})
# If empty, continue without previous context
```

## Future Enhancements

### Planned Features
- [ ] Priority-based interruption (urgent queries)
- [ ] Smart context merging (LLM-based relevance)
- [ ] Persistent storage for long-term history
- [ ] Rate limiting for rapid interruptions
- [ ] Metrics and analytics dashboard

### Optimization Opportunities
- Redis for distributed state management
- Message queue for task coordination
- Streaming partial results to frontend
- Incremental result updates (diff-based)

## Troubleshooting

### Issue: Tasks not cancelling
**Solution:** Ensure agents check `cancel_event` periodically
```python
# In long-running loops
for item in large_dataset:
    if cancel_event.is_set():
        return {"status": "cancelled", "partial": ...}
```

### Issue: Partial results not preserved
**Solution:** Verify progress callbacks are called
```python
await progress_callback({
    "status": "partial",
    "data": current_results
})
```

### Issue: WebSocket disconnects
**Solution:** Implement ping/pong heartbeat
```javascript
setInterval(() => {
    ws.send(JSON.stringify({type: 'ping'}));
}, 30000);
```

## API Reference

### REST Endpoints

#### POST /chat
Submit a new query (auto-interrupts existing)
```json
{
  "user_id": "string",
  "message": "string"
}
```

#### POST /interrupt
Explicitly interrupt current task
```json
{
  "user_id": "string"
}
```

#### GET /status/{user_id}
Get current status and partial results

#### GET /partial-results/{user_id}
Get only partial results (for polling)

#### WebSocket /ws/{user_id}
Real-time status updates

## Conclusion

The Request Interruption System provides robust handling of user behavior patterns where queries change mid-execution. By preserving partial results, transferring context, and providing real-time updates, it creates a responsive and intelligent user experience.
