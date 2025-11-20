# Request Interruption System - Quick Reference

## Overview

The interruption system handles "double-texting" - when users send new queries while agents are processing.

## ✅ Features Implemented

1. **Automatic Detection** - New queries interrupt running tasks
2. **Graceful Cancellation** - Agents stop cleanly via asyncio events
3. **Partial Results** - All progress is preserved before interruption
4. **Context Transfer** - New queries can access previous partial results
5. **Real-time Updates** - WebSocket streaming of agent status

## Quick Test

```bash
# Run test suite
cd backend
python test_interruption.py

# Run interactive demo
python demo_interruption.py
```

## API Examples

### REST API
```bash
# Send first query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "message": "Find flights to Tokyo"}'

# Interrupt with new query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "message": "Find hotels in Paris"}'

# Check status
curl http://localhost:8000/status/user1
```

### WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/user123');

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    console.log(`Status: ${update.status}`);
    console.log(`Agent: ${update.current_agent}`);
    console.log('Partials:', update.partial_results);
};
```

## Key Files

- `interruption_manager.py` - Core interruption logic
- `runner.py` - Integration with workflow
- `state_store.py` - Partial result storage
- `graph_workflow.py` - Cancellation checkpoints
- `main.py` - WebSocket endpoints
- `INTERRUPTION_SYSTEM.md` - Full documentation

## How It Works

```
New Query → Auto-interrupt → Cancel Event → Agents Stop → Preserve Partials
```

See `INTERRUPTION_SYSTEM.md` for complete details.
