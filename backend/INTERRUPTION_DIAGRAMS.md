# Request Interruption System - Visual Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React/Vue/etc)                       │
│                                                                          │
│  ┌──────────────┐         ┌──────────────┐         ┌─────────────┐     │
│  │ Chat Input   │────────▶│ HTTP Client  │────────▶│  WebSocket  │     │
│  │              │         │              │         │  Connection │     │
│  └──────────────┘         └──────────────┘         └─────────────┘     │
│        │                        │                         │             │
│        │ User types             │ POST /chat              │ Receives    │
│        │ new message            │                         │ updates     │
│        ▼                        ▼                         ▼             │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │              Display: Messages, Status, Partials              │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/WebSocket
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI + Python)                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                         main.py                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │    │
│  │  │ POST /chat   │  │POST /interrupt│  │ WS /ws/{user_id}    │ │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────────────┘ │    │
│  └─────────┼─────────────────┼──────────────────┼──────────────────┘    │
│            │                 │                  │                       │
│            ▼                 ▼                  │                       │
│  ┌─────────────────────────────────────────────┼──────────────────┐    │
│  │              AgentManager (runner.py)       │                  │    │
│  │                                              │                  │    │
│  │  handle_user_message()                      │                  │    │
│  │       │                                      │                  │    │
│  │       ├──▶ 1. Check for existing task       │                  │    │
│  │       │                                      │                  │    │
│  │       ├──▶ 2. Auto-interrupt if found       │                  │    │
│  │       │         │                            │                  │    │
│  │       │         ▼                            │                  │    │
│  │       │    ┌─────────────────────────────────┴────────────┐    │    │
│  │       │    │   InterruptionManager                        │    │    │
│  │       │    │   (interruption_manager.py)                  │    │    │
│  │       │    │                                              │    │    │
│  │       │    │  • create_task_context()                    │    │    │
│  │       │    │    ↓ Detects existing task                  │    │    │
│  │       │    │    ↓ Sets cancel_event                      │    │    │
│  │       │    │    ↓ Calls task.cancel()                    │    │    │
│  │       │    │                                              │    │    │
│  │       │    │  • save_partial_results()                   │    │    │
│  │       │    │    ↓ Stores agent progress                  │    │    │
│  │       │    │                                              │    │    │
│  │       │    │  • get_previous_context()                   │    │    │
│  │       │    │    ↓ Retrieves interrupted history          │    │    │
│  │       │    │                                              │    │    │
│  │       │    │  • register_status_callback()               │    │    │
│  │       │    │    ↓ WebSocket streaming ─────────────────┐ │    │    │
│  │       │    └───────────────────────────────────────────┼─┘    │    │
│  │       │                                                 │      │    │
│  │       ├──▶ 3. Create workflow task                     │      │    │
│  │       │                                                 │      │    │
│  │       ├──▶ 4. Execute LangGraph workflow               │      │    │
│  │       │         │                                       │      │    │
│  │       │         ▼                                       │      │    │
│  │       │    ┌────────────────────────────────────┐      │      │    │
│  │       │    │   StateStore (state_store.py)      │      │      │    │
│  │       │    │                                     │      │      │    │
│  │       │    │  • Conversations                    │      │      │    │
│  │       │    │  • Partial results                  │      │      │    │
│  │       │    │  • Task metadata                    │      │      │    │
│  │       │    │  • Interrupted context history      │      │      │    │
│  │       │    └────────────────────────────────────┘      │      │    │
│  │       │                                                 │      │    │
│  │       └──▶ 5. Stream status via callbacks ─────────────┘      │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              LangGraph Workflow (graph_workflow.py)             │   │
│  │                                                                 │   │
│  │         ┌──────────┐                                           │   │
│  │    ┌───▶│  Router  │──────┐                                    │   │
│  │    │    │  Node    │      │ Detect intent                      │   │
│  │    │    └──────────┘      │ (flight/hotel/both)                │   │
│  │    │                      │                                     │   │
│  │  START                    ▼                                     │   │
│  │                   ┌──────────────┐                              │   │
│  │                   │   Decision   │                              │   │
│  │                   └───┬──────┬───┘                              │   │
│  │                       │      │                                  │   │
│  │               flight  │      │  hotel                           │   │
│  │                       ▼      ▼                                  │   │
│  │              ┌──────────┐  ┌──────────┐                        │   │
│  │              │ Flight   │  │  Hotel   │                        │   │
│  │              │ Agent    │  │  Agent   │                        │   │
│  │              │ Node     │  │  Node    │                        │   │
│  │              │          │  │          │                        │   │
│  │              │ Checks:  │  │ Checks:  │                        │   │
│  │              │ • cancel │  │ • cancel │                        │   │
│  │              │   event  │  │   event  │                        │   │
│  │              │ • Saves  │  │ • Saves  │                        │   │
│  │              │   partial│  │   partial│                        │   │
│  │              │ • Handles│  │ • Handles│                        │   │
│  │              │   errors │  │   errors │                        │   │
│  │              └─────┬────┘  └────┬─────┘                        │   │
│  │                    │            │                              │   │
│  │                    └────┬───────┘                              │   │
│  │                         ▼                                      │   │
│  │                  ┌──────────────┐                              │   │
│  │                  │  Response    │                              │   │
│  │                  │  Assembler   │                              │   │
│  │                  │              │                              │   │
│  │                  │ Combines:    │                              │   │
│  │                  │ • Completed  │                              │   │
│  │                  │ • Partial    │                              │   │
│  │                  │ • Cancelled  │                              │   │
│  │                  └──────┬───────┘                              │   │
│  │                         │                                      │   │
│  │                         ▼                                      │   │
│  │                       END                                      │   │
│  └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Interruption Flow Diagram

```
Timeline: User sends multiple queries
──────────────────────────────────────────────────────────────────▶

t=0s      User: "Find flights to Paris"
          │
          ▼
          [Task 1 STARTS]
          │
          ├─ Router: Detect "flight" intent
          │
          ├─ Flight Agent: Start API search
          │
t=1.5s    │  ├─ Partial: 3 flights found
          │  │
          │  ├─ Save partial results
          │  │
          │  ├─ Continue searching...
          │
          │  User: "Actually, hotels in London"
          │       │
          │       ▼
          │  [INTERRUPTION DETECTED]
          │       │
          │       ├─ Set cancel_event
          │       │
          │       ├─ Call task.cancel()
          │       │
          │  [Task 1 CANCELLED]
          │       │
          │       ├─ Flight Agent detects cancel_event
          │       │
          │       ├─ Returns {"status": "cancelled", "partial": {...}}
          │       │
          │       ├─ Preserve partial results (3 flights)
          │       │
          │       ├─ Save to interrupted history
          │       │
          │  [Task 2 STARTS]
          │       │
          │       ├─ Router: Detect "hotel" intent
          │       │
          │       ├─ Previous context available:
          │       │   • Previous query: "flights to Paris"
          │       │   • Partial results: 3 flights
          │       │
t=2.0s    │       ├─ Hotel Agent: Start API search
          │       │
          │       ├─ Partial: 2 hotels found
          │       │
t=3.5s    │       ├─ Partial: 5 hotels found
          │       │
t=4.5s    │  [Task 2 COMPLETES]
          │       │
          │       ├─ Final results: 8 hotels
          │       │
          │       ├─ Response includes status of previous task
          │       │
          │       ▼
          └─ Return to user: Hotels + info about interrupted flight search
```

## WebSocket Update Flow

```
┌────────────┐                                    ┌────────────┐
│  Frontend  │                                    │  Backend   │
└─────┬──────┘                                    └──────┬─────┘
      │                                                  │
      │  1. Connect WebSocket                           │
      ├─────────────────────────────────────────────────▶
      │  ws://localhost:8000/ws/user123                 │
      │                                                  │
      │  2. Connection Accepted                         │
      ◀─────────────────────────────────────────────────┤
      │                                                  │
      │  [User sends chat query via HTTP]               │
      │                                                  │
      │  3. Status Update: Task Started                 │
      ◀─────────────────────────────────────────────────┤
      │  {                                               │
      │    "type": "status_update",                     │
      │    "status": "running",                          │
      │    "current_agent": "flight"                     │
      │  }                                               │
      │                                                  │
      │  4. Status Update: Partial Results              │
      ◀─────────────────────────────────────────────────┤
      │  {                                               │
      │    "type": "status_update",                     │
      │    "partial_results": {                          │
      │      "flight": {"found": 3, "searching": true}   │
      │    }                                             │
      │  }                                               │
      │                                                  │
      │  [User sends NEW query - interruption!]         │
      │                                                  │
      │  5. Status Update: Interrupted                  │
      ◀─────────────────────────────────────────────────┤
      │  {                                               │
      │    "type": "status_update",                     │
      │    "status": "interrupted"                       │
      │  }                                               │
      │                                                  │
      │  6. Status Update: New Task Started             │
      ◀─────────────────────────────────────────────────┤
      │  {                                               │
      │    "type": "status_update",                     │
      │    "status": "running",                          │
      │    "current_agent": "hotel"                      │
      │  }                                               │
      │                                                  │
      │  7. Status Update: Completed                    │
      ◀─────────────────────────────────────────────────┤
      │  {                                               │
      │    "type": "status_update",                     │
      │    "status": "completed",                        │
      │    "final_results": {...}                        │
      │  }                                               │
      │                                                  │
      │  8. Ping (heartbeat every 30s)                  │
      ├─────────────────────────────────────────────────▶
      │  {"type": "ping"}                               │
      │                                                  │
      │  9. Pong                                         │
      ◀─────────────────────────────────────────────────┤
      │  {"type": "pong"}                               │
      │                                                  │
```

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEW QUERY ARRIVES                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │   AgentManager         │
            │   handle_user_message()│
            └────────┬───────────────┘
                     │
                     │ 1. Create task context
                     ▼
            ┌──────────────────────────────┐
            │  InterruptionManager         │
            │  create_task_context()       │
            │                              │
            │  Checks: existing task?      │
            └────────┬─────────────────────┘
                     │
          ┌──────────┴──────────┐
          │ YES                 │ NO
          ▼                     ▼
┌─────────────────────┐   ┌──────────────────┐
│ INTERRUPT EXISTING  │   │ CREATE NEW TASK  │
│                     │   │                  │
│ 1. cancel_event.set()│   │ 1. New context   │
│ 2. task.cancel()    │   │ 2. Start workflow│
│ 3. Save partials    │   └────────┬─────────┘
│ 4. Save to history  │            │
└─────────┬───────────┘            │
          │                        │
          └────────┬───────────────┘
                   │
                   │ 2. Execute workflow
                   ▼
         ┌─────────────────────┐
         │  LangGraph Workflow │
         │                     │
         │  ┌────────────┐    │
         │  │ Router Node│    │
         │  └─────┬──────┘    │
         │        │           │
         │        ▼           │
         │  ┌────────────┐   │
         │  │ Agent Node │   │
         │  │            │   │
         │  │ • Checks   │   │
         │  │   cancel   │◀──┼─── Cancel Event
         │  │   event    │   │
         │  │            │   │
         │  │ • Saves    │   │
         │  │   partial  │───┼──▶ InterruptionManager
         │  │   results  │   │    .save_partial_results()
         │  │            │   │
         │  └─────┬──────┘   │
         │        │           │
         │        ▼           │
         │  ┌────────────┐   │
         │  │ Response   │   │
         │  │ Assembler  │   │
         │  └─────┬──────┘   │
         └────────┼───────────┘
                  │
                  │ 3. Stream updates
                  ▼
         ┌────────────────────┐
         │ Status Callbacks   │
         │                    │
         │ • WebSocket send   │
         │ • Update UI        │
         └────────────────────┘
```

## State Lifecycle Diagram

```
┌─────────────┐
│    IDLE     │  No active tasks
└──────┬──────┘
       │
       │ New query arrives
       ▼
┌─────────────┐
│   QUEUED    │  Task created, not started
└──────┬──────┘
       │
       │ Workflow execution begins
       ▼
┌─────────────┐
│   RUNNING   │──────┐
│             │      │ New query? → INTERRUPT
└──────┬──────┘      │
       │             │
       │ Normal      │
       │ completion  │
       ▼             ▼
┌─────────────┐ ┌──────────────┐
│  COMPLETED  │ │ INTERRUPTED  │
│             │ │              │
│ • Final     │ │ • Partial    │
│   results   │ │   results    │
│             │ │ • Saved to   │
│             │ │   history    │
└─────────────┘ └──────────────┘
       │             │
       │             │ Context available
       │             │ for next query
       ▼             ▼
┌─────────────────────────┐
│  Context transferred to │
│  next task if relevant  │
└─────────────────────────┘
```

## Files & Responsibilities

```
backend/
├── interruption_manager.py     [Core Logic]
│   └─ TaskContext, TaskStatus, InterruptionManager
│
├── runner.py                    [Orchestration]
│   └─ AgentManager with interruption integration
│
├── state_store.py              [Storage]
│   └─ Conversations, partials, interrupted history
│
├── graph_workflow.py           [Workflow]
│   └─ Nodes with cancellation checkpoints
│
├── main.py                     [API]
│   └─ REST endpoints + WebSocket streaming
│
├── test_interruption.py        [Testing]
│   └─ 7 comprehensive test scenarios
│
├── demo_interruption.py        [Demo]
│   └─ 4 interactive demonstration scenarios
│
└── INTERRUPTION_SYSTEM.md      [Docs]
    └─ Complete technical documentation
```
