# 🛫 AI-Powered Travel Planning Assistant (Multi-Agent)

> A sophisticated multi-agent travel planning system with request interruption support, built with LangGraph and FastAPI.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Key Features](#key-features)
- [Setup Instructions](#setup-instructions)
- [Agent Design](#agent-design)
- [Request Interruption System](#request-interruption-system)
- [API Endpoints](#api-endpoints)
- [Demo Instructions](#demo-instructions)
- [Project Structure](#project-structure)
- [Technical Stack](#technical-stack)

---

## 🏗️ Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐   │
│  │   Chat UI    │────▶│  HTTP/REST   │────▶│  WebSocket Client    │   │
│  └──────────────┘     └──────────────┘     └──────────────────────┘   │
└───────────────────────────┬─────────────────────────┬───────────────────┘
                            │                         │
                            ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI + Python)                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    API Layer                                    │    │
│  │  • /chat         - Process user queries                        │    │
│  │  • /interrupt    - Cancel running tasks                        │    │
│  │  • /ws/{user_id} - WebSocket real-time updates                │    │
│  │  • /status       - Get task status                             │    │
│  │  • /partial      - Retrieve partial results                    │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │              INTERRUPTION MANAGER                               │    │
│  │  • Task lifecycle management (queued → running → completed)    │    │
│  │  • Cancellation tokens (asyncio.Event)                         │    │
│  │  • Partial result preservation                                 │    │
│  │  • Context transfer between tasks                              │    │
│  │  • Status callbacks for real-time updates                      │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │              LANGGRAPH ORCHESTRATION                            │    │
│  │                                                                 │    │
│  │   ┌──────────────┐                                             │    │
│  │   │   Router     │  (Intent Detection & Agent Selection)       │    │
│  │   │   Node       │                                             │    │
│  │   └───────┬──────┘                                             │    │
│  │           │                                                     │    │
│  │      ┌────┴────┐                                               │    │
│  │      │         │                                               │    │
│  │  ┌───▼───┐ ┌──▼─────┐                                         │    │
│  │  │Flight │ │ Hotel  │  (Specialized Agent Nodes)              │    │
│  │  │ Agent │ │ Agent  │                                          │    │
│  │  └───┬───┘ └──┬─────┘                                         │    │
│  │      │         │                                               │    │
│  │      └────┬────┘                                               │    │
│  │           │                                                     │    │
│  │   ┌───────▼──────┐                                             │    │
│  │   │  Response    │  (Result Assembly)                          │    │
│  │   │  Assembler   │                                             │    │
│  │   └──────────────┘                                             │    │
│  │                                                                 │    │
│  │  State: {messages, intent, previous_context, partial_results}  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    AGENT TOOLS                                  │    │
│  │  ┌──────────────┐         ┌──────────────┐                     │    │
│  │  │ Flight API   │         │  Hotel API   │                     │    │
│  │  │              │         │              │                     │    │
│  │  │ • Amadeus    │         │ • Amadeus    │                     │    │
│  │  │ • SerpAPI    │         │ • Booking    │                     │    │
│  │  │ • Mock Data  │         │ • Mock Data  │                     │    │
│  │  └──────────────┘         └──────────────┘                     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    LLM INTEGRATION                              │    │
│  │                    OpenAI GPT-4o                                │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Query** → Frontend sends to `/chat` endpoint
2. **Interruption Check** → InterruptionManager cancels any running task for this user
3. **Intent Detection** → Router node analyzes query and determines agent(s) needed
4. **Agent Execution** → Flight/Hotel agents fetch data via APIs with cancellation checkpoints
5. **Partial Results** → Saved incrementally during processing
6. **WebSocket Updates** → Real-time status broadcast to frontend
7. **Response Assembly** → Final response aggregated and returned

---

## ✨ Key Features

### 🎯 Multi-Agent System
- **Flight Agent**: Search flights by route, date, airline, price range
- **Hotel Agent**: Find hotels by location, dates, amenities, star rating
- **Coordinator (Router)**: Intelligent intent detection and agent orchestration
- **Context Transfer**: Seamless handoffs between agents

### 🔴 Request Interruption (Core Innovation)
- **Automatic Detection**: New query cancels in-flight requests
- **Graceful Cancellation**: AsyncIO-based task cancellation with cleanup
- **Partial Result Preservation**: Saves progress before interruption
- **Context Continuity**: Transfers conversation state to new task
- **Real-Time Updates**: WebSocket notifications for status changes

### 🔄 State Management
- **Conversation History**: Full context maintained across queries
- **Partial Results**: Incremental progress saved per agent
- **Task Metadata**: Status, timestamps, user info tracked
- **Interrupted Context**: Last 5 interrupted contexts preserved per user

### 🌐 Real-Time Communication
- **WebSocket Support**: Live status updates during processing
- **Connection Management**: Multi-user concurrent connections
- **Progress Tracking**: Agent-level progress reporting

---

## 🚀 Setup Instructions

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 16+ and npm (for frontend)
- **API Keys**: OpenAI (required), Amadeus/SerpAPI (optional)

### Backend Setup

#### 1. Navigate to Backend Directory

```bash
cd backend
```

#### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Required: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Amadeus API (for real flight/hotel data)
AMADEUS_API_KEY=your_amadeus_key
AMADEUS_API_SECRET=your_amadeus_secret
AMADEUS_HOSTNAME=test.api.amadeus.com

# Optional: SerpAPI (for Google search)
SERPAPI_KEY=your_serpapi_key

# Optional: RapidAPI (for Booking.com hotels)
RAPIDAPI_KEY=your_rapidapi_key
RAPIDAPI_HOTEL_HOST=booking-com.p.rapidapi.com

# Backend Configuration
DEBUG=True
HOST=127.0.0.1
PORT=8000
USE_REAL_APIS=False  # Set to True to use real APIs instead of mocks
```

**Getting API Keys:**
- **OpenAI**: https://platform.openai.com/api-keys
- **Amadeus**: https://developers.amadeus.com/ (free tier available)
- **SerpAPI**: https://serpapi.com/ (100 searches/month free)

#### 5. Run the Backend

```bash
# Option 1: Using the shell script
chmod +x start_server.sh
./start_server.sh

# Option 2: Direct uvicorn command
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Option 3: Using Python
python main.py
```

Backend will be available at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

### Frontend Setup

#### 1. Navigate to Frontend Directory

```bash
cd ../frontend
```

#### 2. Install Dependencies

```bash
npm install
```

#### 3. Configure Backend URL

Edit `src/Chat.js` if your backend runs on a different port:

```javascript
const BACKEND_URL = 'http://localhost:8000';
```

#### 4. Run the Frontend

```bash
npm start
```

Frontend will be available at: **http://localhost:3000**

---

## 🤖 Agent Design

### Architecture Pattern: LangGraph StateGraph

The system uses **LangGraph** for multi-agent orchestration with a shared state model and conditional routing.

### Agent Definitions

#### 1. **Router Node** (Coordinator)

**Responsibility**: Intent detection and agent selection

**Inputs:**
- `messages`: List of conversation messages
- `previous_context`: Context from interrupted tasks (optional)

**Outputs:**
- `intent`: Detected intent (`"flight"`, `"hotel"`, `"both"`, `"general"`)
- `routing_decision`: Next agent to invoke

**Logic:**
```python
def router_node(state: AgentState):
    """Analyzes user query and routes to appropriate agent(s)."""
    messages = state["messages"]
    last_message = messages[-1].content.lower()
    
    # Intent detection logic
    if "flight" in last_message or "fly" in last_message:
        intent = "flight"
    elif "hotel" in last_message or "stay" in last_message:
        intent = "hotel"
    elif ("flight" in last_message and "hotel" in last_message):
        intent = "both"
    else:
        intent = "general"
    
    return {"intent": intent}
```

**Capabilities:**
- Keyword-based intent classification
- Multi-intent handling (flight + hotel)
- Context awareness from previous queries

---

#### 2. **Flight Agent**

**Responsibility**: Search and provide flight information

**Inputs:**
- `messages`: User query with travel details
- `cancel_event`: Cancellation token (asyncio.Event)
- `partial_results`: Previously saved partial results

**Outputs:**
- `messages`: Flight search results
- `partial_results`: Incremental search progress

**Tools:**
- **Amadeus Flight API**: Real-time flight search
- **SerpAPI**: Google Flights web scraping
- **Mock Data**: Fallback for testing

**Capabilities:**
- Route search (source → destination)
- Date-based filtering
- Price range filtering
- Airline preferences
- Cancellation checkpoint checks

**Example Query Processing:**
```
User: "Find flights from NYC to London on Dec 15"
↓
Extract: origin="NYC", destination="LON", date="2025-12-15"
↓
Call Flight API → Return top 5 results with prices
```

**Interruption Handling:**
```python
async def flight_node(state: AgentState):
    cancel_event = state.get("cancel_event")
    
    for chunk in search_flights():
        # Check for cancellation
        if cancel_event and cancel_event.is_set():
            # Save partial results
            state["partial_results"]["FlightAgent"] = {
                "chunks_completed": current_chunk,
                "progress": f"{(current_chunk/total)*100}%"
            }
            raise CancellationError("Task interrupted")
        
        # Process chunk
        results.append(chunk)
    
    return {"messages": [AIMessage(content=format_results(results))]}
```

---

#### 3. **Hotel Agent**

**Responsibility**: Search and provide hotel information

**Inputs:**
- `messages`: User query with location and dates
- `cancel_event`: Cancellation token
- `partial_results`: Previously saved partial results

**Outputs:**
- `messages`: Hotel search results
- `partial_results`: Incremental search progress

**Tools:**
- **Amadeus Hotel API**: Real hotel data
- **Booking.com API** (via RapidAPI)
- **Mock Data**: Fallback for testing

**Capabilities:**
- Location-based search
- Date availability checking
- Price range filtering
- Star rating filtering
- Amenity filtering (pool, WiFi, parking)
- Cancellation checkpoint checks

**Example Query Processing:**
```
User: "Hotels in Paris for Dec 20-25"
↓
Extract: location="Paris", check_in="2025-12-20", check_out="2025-12-25"
↓
Call Hotel API → Return top 5 hotels with prices and ratings
```

---

#### 4. **Response Assembler Node**

**Responsibility**: Aggregate results and format final response

**Inputs:**
- `messages`: All agent messages
- `intent`: Original user intent
- `partial_results`: Any saved partial results

**Outputs:**
- `messages`: Final formatted response

**Logic:**
- Combines flight + hotel results if both requested
- Formats data into readable text
- Includes pricing summaries
- Adds booking links (if available)

---

### State Schema (AgentState)

```python
class AgentState(TypedDict):
    """Shared state across all agents."""
    
    messages: Annotated[list, add_messages]
    # Conversation history
    
    intent: str
    # Detected intent: "flight", "hotel", "both", "general"
    
    cancel_event: Optional[asyncio.Event]
    # Cancellation token for interruption
    
    previous_context: Optional[Dict[str, Any]]
    # Context from interrupted tasks
    
    partial_results: Dict[str, Any]
    # Incremental results from agents
```

---

### Workflow Graph

```
START
  │
  ▼
ROUTER ────┐
  │        │ (intent="flight")
  │        ├──▶ FLIGHT_AGENT ──┐
  │        │                   │
  │        │ (intent="hotel")  │
  │        ├──▶ HOTEL_AGENT ───┤
  │        │                   │
  │        │ (intent="both")   │
  │        └──▶ BOTH_AGENTS ───┤
  │                            │
  ▼                            ▼
RESPONSE_ASSEMBLER ◀───────────┘
  │
  ▼
END
```

**Conditional Edges:**
- Router → Flight Agent (if intent contains "flight")
- Router → Hotel Agent (if intent contains "hotel")
- Router → Both (if intent is "both")
- All agents → Response Assembler → END

---

## 🔴 Request Interruption System

### Technical Challenge: Handling Double-Texting

**Problem**: User sends a new query while the previous one is still processing.

**Solution**: Automatic interruption with graceful cancellation and context preservation.

### Architecture Components

#### 1. **InterruptionManager** (`interruption_manager.py`)

Core class managing task lifecycle and cancellation.

**Key Methods:**

```python
class InterruptionManager:
    def create_task_context(self, user_id: str, query: str, intent: str):
        """Creates new task and auto-interrupts existing task."""
        # If user has running task, interrupt it
        if user_id in self.active_tasks:
            await self.interrupt_task(user_id)
        
        # Create new task with cancellation event
        task_id = str(uuid.uuid4())
        cancel_event = asyncio.Event()
        
        context = TaskContext(
            task_id=task_id,
            user_id=user_id,
            query=query,
            intent=intent,
            cancel_event=cancel_event,
            status=TaskStatus.QUEUED
        )
        
        self.active_tasks[user_id] = context
        return context
    
    async def interrupt_task(self, user_id: str):
        """Gracefully cancels running task."""
        task = self.active_tasks.get(user_id)
        if task and task.status == TaskStatus.RUNNING:
            # Set cancellation flag
            task.cancel_event.set()
            
            # Save partial results
            await self.save_partial_results(user_id, task.partial_results)
            
            # Update status
            task.status = TaskStatus.INTERRUPTED
            
            # Preserve context for potential resume
            self.state_store.preserve_interrupted_context(
                user_id, task.query, task.intent, task.partial_results
            )
    
    def save_partial_results(self, task_id: str, results: Dict):
        """Preserves incremental progress."""
        self.partial_results[task_id] = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": results
        }
```

**Task States:**
- `QUEUED`: Task created, waiting to start
- `RUNNING`: Currently executing
- `COMPLETED`: Successfully finished
- `INTERRUPTED`: Cancelled by new query
- `FAILED`: Error occurred

---

#### 2. **Enhanced Runner** (`runner.py`)

AgentManager orchestrates LangGraph with interruption support.

**Interruption Flow:**

```python
class AgentManager:
    async def handle_user_message(self, user_id: str, message: str):
        """Processes query with auto-interruption."""
        
        # 1. Detect intent
        intent = self.detect_intent(message)
        
        # 2. Create task context (auto-interrupts existing)
        task_context = await self.interruption_manager.create_task_context(
            user_id, message, intent
        )
        
        # 3. Get previous interrupted context (if any)
        previous_context = self.state_store.get_latest_interrupted_context(user_id)
        
        # 4. Run workflow with cancellation support
        try:
            result = await self._run(
                task_context, 
                message, 
                previous_context
            )
            
            # Mark as completed
            task_context.status = TaskStatus.COMPLETED
            return result
            
        except CancellationError:
            # Task was interrupted - partial results already saved
            return {"status": "interrupted", "task_id": task_context.task_id}
    
    async def _run(self, task_context, message, previous_context):
        """Executes LangGraph with cancellation checks."""
        
        # Prepare state
        state = {
            "messages": [HumanMessage(content=message)],
            "cancel_event": task_context.cancel_event,
            "previous_context": previous_context,
            "partial_results": {}
        }
        
        # Run graph (agents check cancel_event at each node)
        result = await WORKFLOW.ainvoke(state)
        
        return result
```

---

#### 3. **State Store Enhancement** (`state_store.py`)

Thread-safe storage for interrupted contexts.

**Key Features:**

```python
class StateStore:
    def preserve_interrupted_context(
        self, 
        user_id: str, 
        query: str, 
        intent: str, 
        partial_results: Dict
    ):
        """Saves interrupted task context."""
        context = {
            "query": query,
            "intent": intent,
            "partial_results": partial_results,
            "interrupted_at": datetime.utcnow().isoformat()
        }
        
        # Keep last 5 interrupted contexts per user
        if user_id not in self.interrupted_contexts:
            self.interrupted_contexts[user_id] = []
        
        self.interrupted_contexts[user_id].append(context)
        
        # Limit to 5 most recent
        if len(self.interrupted_contexts[user_id]) > 5:
            self.interrupted_contexts[user_id].pop(0)
    
    def get_latest_interrupted_context(self, user_id: str):
        """Retrieves most recent interrupted context."""
        contexts = self.interrupted_contexts.get(user_id, [])
        return contexts[-1] if contexts else None
```

---

#### 4. **Graph Workflow Integration** (`graph_workflow.py`)

Each agent node checks for cancellation.

**Cancellation Checkpoints:**

```python
async def flight_node(state: AgentState):
    """Flight search with interruption support."""
    cancel_event = state.get("cancel_event")
    partial_results = state.get("partial_results", {})
    
    results = []
    total_chunks = 10
    
    for i in range(total_chunks):
        # ✅ CANCELLATION CHECKPOINT
        if cancel_event and cancel_event.is_set():
            # Save progress before exiting
            partial_results["FlightAgent"] = {
                "chunks_completed": i,
                "progress": f"{(i/total_chunks)*100:.1f}%",
                "results_so_far": results
            }
            raise CancellationError("Flight search interrupted")
        
        # Simulate API call
        await asyncio.sleep(0.3)
        chunk_data = fetch_flight_chunk(i)
        results.append(chunk_data)
        
        # Update partial results
        partial_results["FlightAgent"] = {
            "chunks_completed": i + 1,
            "progress": f"{((i+1)/total_chunks)*100:.1f}%"
        }
    
    return {
        "messages": [AIMessage(content=format_flights(results))],
        "partial_results": partial_results
    }
```

---

#### 5. **WebSocket Real-Time Updates** (`main.py`)

Real-time status broadcasting to frontend.

**Connection Manager:**

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    async def send_status(self, user_id: str, status: Dict):
        """Broadcasts status update to user's WebSocket."""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(status)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# Status callback in InterruptionManager
def broadcast_status(task_context):
    asyncio.create_task(
        manager.send_status(task_context.user_id, {
            "task_id": task_context.task_id,
            "status": task_context.status.value,
            "progress": task_context.partial_results
        })
    )
```

---

### Interruption Flow Example

**Scenario**: User asks for flights, then immediately asks for hotels

```
Timeline:

T=0s   User: "Find flights to Paris"
       ├─▶ Create Task A (intent=flight)
       ├─▶ Start FlightAgent
       └─▶ Status: RUNNING

T=1.5s FlightAgent: 50% complete (5/10 chunks processed)
       └─▶ Partial results: {chunks: 5, progress: "50%"}

T=2s   User: "Actually, show me hotels in Paris"
       ├─▶ Create Task B (intent=hotel)
       ├─▶ Auto-interrupt Task A:
       │   ├─ Set cancel_event
       │   ├─ FlightAgent detects cancellation at next checkpoint
       │   ├─ Save partial: {FlightAgent: {chunks: 5, progress: "50%"}}
       │   └─ Preserve context in StateStore
       ├─▶ Start HotelAgent with previous_context
       └─▶ Status: Task A=INTERRUPTED, Task B=RUNNING

T=4s   HotelAgent: Completes successfully
       └─▶ Response includes hotel results
       └─▶ Previous flight context available if user wants to resume
```

---

### Cancellation Libraries Used

- **asyncio.Event**: Cancellation tokens for async tasks
- **asyncio.CancelledError**: Exception handling for task cancellation
- **FastAPI BackgroundTasks**: Non-blocking task execution
- **WebSocket**: Real-time status updates

---

## 🌐 API Endpoints

### REST API

#### `POST /chat`
Process user query through multi-agent system.

**Request:**
```json
{
  "user_id": "user123",
  "message": "Find flights from NYC to Paris on Dec 15"
}
```

**Response:**
```json
{
  "response": "Here are flights from NYC to Paris on Dec 15:\n1. Air France...",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed"
}
```

---

#### `POST /interrupt`
Manually interrupt a running task.

**Request:**
```json
{
  "user_id": "user123"
}
```

**Response:**
```json
{
  "status": "interrupted",
  "message": "Task interrupted successfully",
  "partial_results": {"FlightAgent": {"progress": "30%"}}
}
```

---

#### `GET /status/{user_id}`
Get current task status for a user.

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "query": "Find flights to Paris",
  "intent": "flight",
  "created_at": "2025-11-21T04:26:15.123456"
}
```

---

#### `GET /partial-results/{user_id}`
Retrieve partial results from interrupted task.

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "partial_results": {
    "FlightAgent": {
      "chunks_completed": 7,
      "progress": "70%",
      "results_so_far": [...]
    }
  },
  "timestamp": "2025-11-21T04:26:18.500000"
}
```

---

### WebSocket API

#### `WS /ws/{user_id}`
Real-time status updates during query processing.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/user123');

ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  console.log('Status:', status.status);
  console.log('Progress:', status.progress);
};
```

**Status Updates:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": {
    "FlightAgent": {"chunks_completed": 3, "progress": "30%"}
  }
}
```

---

## 🎬 Demo Instructions

### Prerequisites

- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- OpenAI API key configured

---

### Test Scenario 1: Basic Flight Search

**Steps:**
1. Open frontend at `http://localhost:3000`
2. Enter: `"Find flights from New York to London on December 15"`
3. Wait for response (3-5 seconds with mock data)

**Expected:**
- Agent detects `intent=flight`
- FlightAgent executes search
- Response shows flight options with prices
- Status updates visible in console (if WebSocket connected)

**Sample Response:**
```
Here are the top flights from New York to London on December 15, 2025:

1. American Airlines AA100
   Departure: 08:00 AM → Arrival: 08:00 PM
   Price: $650
   Duration: 7h 0m

2. British Airways BA117
   Departure: 10:30 AM → Arrival: 10:30 PM
   Price: $720
   Duration: 7h 0m
```

---

### Test Scenario 2: Basic Hotel Search

**Steps:**
1. Enter: `"Show me hotels in Paris for December 20-25"`
2. Wait for response

**Expected:**
- Agent detects `intent=hotel`
- HotelAgent executes search
- Response shows hotel options with ratings

**Sample Response:**
```
Here are hotels in Paris for December 20-25:

1. Hotel Plaza Athénée ⭐⭐⭐⭐⭐
   Price: $450/night
   Amenities: Pool, WiFi, Spa

2. Le Bristol Paris ⭐⭐⭐⭐⭐
   Price: $420/night
   Amenities: WiFi, Restaurant, Gym
```

---

### Test Scenario 3: Request Interruption (Core Feature)

**Steps:**
1. Enter: `"Find flights from NYC to Tokyo"` (long-running query)
2. **IMMEDIATELY** (within 1-2 seconds) enter: `"Actually, show me hotels in Paris"`
3. Observe interruption behavior

**Expected Behavior:**

**Phase 1: Initial Query**
- FlightAgent starts processing
- Status: `RUNNING`
- Partial results accumulate (10%, 20%, 30%...)

**Phase 2: Interruption**
- New query detected
- InterruptionManager automatically interrupts Task 1
- FlightAgent detects cancellation at next checkpoint
- Partial results saved: `{FlightAgent: {progress: "30%", chunks: 3}}`
- Context preserved in StateStore

**Phase 3: New Query**
- HotelAgent starts processing
- Previous flight context available (not used in this case)
- Hotel results returned successfully

**Console Output:**
```
[09:30:15] Task A created: Find flights from NYC to Tokyo (intent=flight)
[09:30:15] FlightAgent: Starting search...
[09:30:15] FlightAgent: Progress 10%
[09:30:16] FlightAgent: Progress 20%
[09:30:16] FlightAgent: Progress 30%
[09:30:17] NEW QUERY DETECTED: Show me hotels in Paris
[09:30:17] Interrupting Task A...
[09:30:17] Partial results saved: {chunks: 3, progress: "30%"}
[09:30:17] Task B created: Show me hotels in Paris (intent=hotel)
[09:30:17] HotelAgent: Starting search...
[09:30:18] HotelAgent: Progress 50%
[09:30:19] HotelAgent: ✅ Completed
[09:30:19] Response: Here are hotels in Paris...
```

**Backend API Response:**
```json
{
  "response": "Here are hotels in Paris for your stay:\n1. Hotel Ritz...",
  "task_id": "new-task-id",
  "status": "completed",
  "previous_task": {
    "task_id": "old-task-id",
    "status": "interrupted",
    "partial_results": {
      "FlightAgent": {"progress": "30%", "chunks": 3}
    }
  }
}
```

---

### Test Scenario 4: Multiple Rapid Interruptions

**Steps:**
1. Quickly type and send these queries (1 second apart):
   - `"Flights to Paris"`
   - `"Hotels in London"`
   - `"Flights to Rome"`
   - `"Hotels in Barcelona"`

**Expected:**
- Only the LAST query (`"Hotels in Barcelona"`) completes
- All previous queries are interrupted
- Each interruption preserves partial results
- Final response shows Barcelona hotels

**StateStore Contents:**
```python
interrupted_contexts["user123"] = [
  {"query": "Flights to Paris", "progress": "10%", ...},
  {"query": "Hotels in London", "progress": "20%", ...},
  {"query": "Flights to Rome", "progress": "15%", ...}
]
# (Max 5 stored, oldest removed if exceeded)
```

---

### Test Scenario 5: Context Transfer

**Steps:**
1. Enter: `"Find flights from NYC to Paris on Dec 15"`
2. Wait 1 second, then enter: `"Make that Dec 20 instead"`

**Expected:**
- First query starts FlightAgent
- Second query interrupts with partial results
- Router detects this is a modification of previous query
- Previous context transferred to new task
- Response acknowledges the change: *"Updated your flight search to December 20..."*

---

### Test Scenario 6: Multi-Intent Query

**Steps:**
1. Enter: `"I need flights to Paris on Dec 15 and hotels for Dec 15-20"`

**Expected:**
- Router detects `intent=both`
- Both FlightAgent AND HotelAgent execute
- Response assembler combines results
- Single response with flights + hotels

**Sample Response:**
```
I found the following options for your Paris trip:

FLIGHTS (NYC → Paris, Dec 15):
1. Air France AF007 - $650 - 08:00 AM → 08:00 PM

HOTELS (Paris, Dec 15-20):
1. Hotel Plaza Athénée ⭐⭐⭐⭐⭐ - $450/night
```

---

### Test Scenario 7: Manual Interruption via API

**Steps:**
1. Start a long-running query: `"Find all flights to Tokyo"`
2. Open another terminal:
   ```bash
   curl -X POST http://localhost:8000/interrupt \
     -H "Content-Type: application/json" \
     -d '{"user_id": "user123"}'
   ```

**Expected:**
- Task is cancelled immediately
- Partial results returned in API response
- Frontend shows interruption notification

---

### Testing with Real APIs

**Enable Real APIs:**
1. Set environment variables in `.env`:
   ```env
   AMADEUS_API_KEY=your_key
   AMADEUS_API_SECRET=your_secret
   USE_REAL_APIS=True
   ```

2. Restart backend

**Real API Test Query:**
```
"Find flights from JFK to CDG on 2025-12-15"
```

**Expected:**
- Real flight data from Amadeus API
- Actual prices and availability
- Longer response time (5-10 seconds)

---

### Debugging Tips

**Enable Debug Logs:**
```bash
export DEBUG=True
python main.py
```

**Check Task Status:**
```bash
curl http://localhost:8000/status/user123
```

**Get Partial Results:**
```bash
curl http://localhost:8000/partial-results/user123
```

**WebSocket Testing (Browser Console):**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/user123');
ws.onmessage = (e) => console.log('Status:', JSON.parse(e.data));
ws.send('ping'); // Keep alive
```

---

## 📁 Project Structure

```
.
├── backend/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── base_agent.py          # Base agent interface
│   │   ├── flight_agent.py        # Flight search agent
│   │   ├── hotel_agent.py         # Hotel search agent
│   │   ├── coordinator.py         # Basic coordinator (legacy)
│   │   └── langgraph_coordinator.py  # LangGraph coordinator
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── flight_api.py          # Flight API integration
│   │   └── hotel_api.py           # Hotel API integration
│   │
│   ├── config.py                  # Configuration management
│   ├── main.py                    # FastAPI application
│   ├── runner.py                  # AgentManager with interruption
│   ├── state_store.py             # State management
│   ├── graph_workflow.py          # LangGraph workflow definition
│   ├── interruption_manager.py    # Core interruption logic
│   ├── intent_detector.py         # Intent classification
│   │
│   ├── test_interruption.py       # Interruption tests
│   ├── demo_interruption.py       # Interactive demo
│   ├── quick_test_interruption.py # Quick validation
│   ├── test_*.py                  # Other test files
│   │
│   ├── requirements.txt           # Python dependencies
│   ├── pyproject.toml            # Python project metadata
│   ├── Dockerfile                # Docker configuration
│   ├── start_server.sh           # Server startup script
│   └── README.md                 # This file
│
└── frontend/
    ├── public/
    │   ├── index.html
    │   └── ...
    │
    ├── src/
    │   ├── App.js                # Main app component
    │   ├── Chat.js               # Chat interface
    │   ├── Home.js               # Home page
    │   └── index.js              # Entry point
    │
    ├── package.json              # Node dependencies
    └── README.md                 # Frontend docs
```

---

## 🛠️ Technical Stack

### Backend
- **Python**: 3.10+
- **FastAPI**: Web framework with WebSocket support
- **LangGraph**: Multi-agent orchestration
- **LangChain**: LLM integration and tooling
- **OpenAI GPT-4**: Language model
- **AsyncIO**: Async task management and cancellation
- **Uvicorn**: ASGI server

### Frontend
- **React**: UI framework
- **JavaScript (ES6+)**
- **WebSocket API**: Real-time communication
- **Fetch API**: HTTP requests

### APIs & Tools
- **Amadeus Travel API**: Flight and hotel data
- **SerpAPI**: Google search results
- **RapidAPI**: Hotel booking data
- **Mock Data**: Testing fallback

### Infrastructure
- **Docker**: Containerization (optional)
- **python-dotenv**: Environment management
- **CORS**: Cross-origin resource sharing

---

## 📊 Testing

### Run Interruption Tests

```bash
cd backend

# Quick validation (30 seconds)
python quick_test_interruption.py

# Comprehensive tests (2 minutes)
python test_interruption.py

# Interactive demo
python demo_interruption.py
```

### Run Backend Tests

```bash
# All tests
pytest

# Specific test file
pytest test_backend.py

# With coverage
pytest --cov=. --cov-report=html
```

---

## 🚢 Deployment (Optional)

### Docker Deployment

```bash
# Build image
docker build -t travel-assistant-backend .

# Run container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  travel-assistant-backend
```

### Production Considerations

- Set `DEBUG=False` in production
- Use environment secrets management (AWS Secrets Manager, etc.)
- Enable HTTPS/TLS for WebSocket connections
- Implement rate limiting on API endpoints
- Add authentication/authorization
- Use production ASGI server (Gunicorn + Uvicorn workers)
- Set up logging and monitoring

---

## 🔮 Future Enhancements

### Bonus Features (Not Implemented)
- ✈️ Multi-leg flight itineraries
- 💰 Price alerts and comparison
- 🎫 Booking simulation flow
- 🗺️ Multi-modal responses (maps, images)
- 👤 User profiles with preferences

### Potential Improvements
- Persistent storage (PostgreSQL/MongoDB)
- Redis for caching and session management
- Kubernetes orchestration
- Advanced NLP for intent detection
- A/B testing framework
- Analytics dashboard

---

## 📝 License

This project is part of the PS-005 assignment for AI-Powered Travel Planning.

---

## 👥 Support

For issues or questions:
1. Check the [Demo Instructions](#demo-instructions)
2. Review logs: `tail -f backend/logs/app.log`
3. Test with `quick_test_interruption.py`
4. Enable debug mode: `DEBUG=True`

---

**Built with ❤️ using LangGraph, FastAPI, and React**
