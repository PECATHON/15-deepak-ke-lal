# AI-Powered Travel Planning Assistant (Multi-Agent)

A full-stack travel planning assistant built with **LangGraph** multi-agent orchestration, supporting real-time interruptions, partial result preservation, and context-aware agent coordination.

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  - Chat UI                                                   │
│  - Real-time status updates                                  │
│  - Interruption controls                                     │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/REST
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           AgentManager (runner.py)                   │   │
│  │  - Manages workflow execution                        │   │
│  │  - Handles interruptions                             │   │
│  │  - Tracks conversation state                         │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │       LangGraph Workflow (graph_workflow.py)        │   │
│  │                                                      │   │
│  │  ┌──────────┐    ┌────────────┐   ┌─────────────┐ │   │
│  │  │  Router  │───▶│Flight Agent│   │ Hotel Agent │ │   │
│  │  │   Node   │    └─────┬──────┘   └──────┬──────┘ │   │
│  │  └──────────┘          │                 │        │   │
│  │                        └────────┬────────┘        │   │
│  │                                 ▼                 │   │
│  │                      ┌──────────────────┐        │   │
│  │                      │Response Assembler│        │   │
│  │                      └──────────────────┘        │   │
│  └──────────────────────────────────────────────────┘   │
│                     │                                     │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │              State Store                         │   │
│  │  - Conversation history                          │   │
│  │  - Partial results                               │   │
│  │  - Agent state tracking                          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    External APIs                             │
│  - Flight Search APIs (stubbed/configurable)                 │
│  - Hotel Search APIs (stubbed/configurable)                  │
│  - OpenAI LLM (optional, for intent parsing)                 │
└─────────────────────────────────────────────────────────────┘
```

### Agent Definitions

#### 1. **Router Node**
- **Responsibility**: Analyze incoming user queries and determine intent
- **Inputs**: `user_query` (string)
- **Outputs**: 
  - `intent`: "flight", "hotel", "both", or "unknown"
  - `flight_input`: Parsed flight parameters (source, destination, date)
  - `hotel_input`: Parsed hotel parameters (location, checkin, checkout)
- **Capabilities**: 
  - Keyword-based intent detection
  - Optional LLM-based query parsing (when OpenAI key configured)
  - Context preservation from conversation history

#### 2. **Flight Agent** (`agent/flight_agent.py`)
- **Responsibility**: Search for flights between source and destination
- **Inputs**: `flight_input` dict with keys: `source`, `destination`, `date`, `raw`
- **Outputs**: 
  - Partial results during search (via progress callback)
  - Final results: List of flights with airline, price, route info
- **Capabilities**:
  - Async streaming of partial results
  - Cancellation support (checks `cancel_event`)
  - Integration with flight APIs (currently stubbed)

#### 3. **Hotel Agent** (`agent/hotel_agent.py`)
- **Responsibility**: Find hotels in specified locations
- **Inputs**: `hotel_input` dict with keys: `location`, `checkin`, `checkout`, `raw`
- **Outputs**: 
  - Partial results during search
  - Final results: List of hotels with name, rating, price, location
- **Capabilities**:
  - Async streaming of partial results
  - Cancellation support
  - Integration with hotel APIs (currently stubbed)

#### 4. **Response Assembler Node**
- **Responsibility**: Collate agent results and format final response
- **Inputs**: All agent results from workflow state
- **Outputs**: `final_response` (formatted string for user)
- **Capabilities**:
  - Handles both complete and partial results
  - Formats cancellation messages appropriately

### LangGraph Workflow Structure

The workflow is defined as a **StateGraph** with the following flow:

```
START 
  ↓
Router Node (intent detection)
  ↓
  ├─→ Flight Agent (if intent = "flight")
  ├─→ Hotel Agent (if intent = "hotel")
  └─→ Both (if intent = "both")
  ↓
Response Assembler
  ↓
END
```

**State Schema** (`AgentState` in `graph_workflow.py`):
```python
{
    "user_id": str,
    "messages": list[dict],
    "user_query": str,
    "intent": str,
    "flight_input": Optional[dict],
    "hotel_input": Optional[dict],
    "flight_results": Optional[dict],
    "hotel_results": Optional[dict],
    "final_response": Optional[str],
    "cancel_requested": bool,
    "status": str
}
```

### State Management

**StateStore** (`state_store.py`):
- In-memory conversation storage (per user_id)
- Async locks for thread-safe access
- Stores:
  - Full conversation history
  - Partial results from each agent
  - Current task status

**LangGraph Checkpointing**:
- Uses `MemorySaver` for workflow state persistence
- Enables workflow resumption after interruption
- Each user has a unique `thread_id` for state isolation

### Request Interruption Implementation

#### Detection
- New user queries trigger interruption of existing workflow
- Backend tracks active tasks per `user_id`
- Status endpoint shows current workflow state

#### Cancellation
- `AgentManager.interrupt(user_id)` cancels the running asyncio task
- Sets `cancel_requested` flag in workflow state
- Each agent node checks cancellation flag during execution

#### Partial Result Preservation
1. Agents call `progress_callback` with partial data during search
2. Partial results stored in `StateStore` and workflow state
3. On cancellation, agents return `{"status": "cancelled", "partial": {...}}`
4. Response assembler includes partial results in final message

#### Context Transfer
- Conversation history maintained across interruptions
- LangGraph checkpointer persists workflow state via `thread_id`
- New queries can reference previous partial results
- State includes full message history for context-aware responses

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 16+ (for frontend)
- pip and npm/yarn

### Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Create and activate virtual environment**:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
OPENAI_API_KEY=sk-...
FLIGHT_API_KEY=your_key_here
HOTEL_API_KEY=your_key_here
```

5. **Run the backend**:
```bash
python main.py
```

The API will be available at `http://127.0.0.1:8000`

**API Documentation**: Visit `http://127.0.0.1:8000/docs` for interactive Swagger UI

---

## 📡 API Endpoints

### POST `/chat`
Submit a new user query.

**Request**:
```json
{
  "user_id": "user123",
  "message": "Find flights from NYC to LAX"
}
```

**Response**:
```json
{
  "task_id": "uuid-here",
  "status": "processing"
}
```

### POST `/interrupt`
Cancel running workflow for a user.

**Request**:
```json
{
  "user_id": "user123"
}
```

**Response**:
```json
{
  "status": "interrupted",
  "user_id": "user123"
}
```

### GET `/status/{user_id}`
Get current workflow status.

**Response**:
```json
{
  "task_id": "uuid",
  "state": "completed",
  "response": "Found 2 flights: ..."
}
```

---

## 🧪 Demo & Testing

### Sample Queries

**Flight Search**:
```
"Find flights from New York to Los Angeles on Dec 25"
"Show me tickets from SFO to JFK"
```

**Hotel Search**:
```
"Find hotels in Paris"
"Show me accommodation in Tokyo for next week"
```

**Combined Search**:
```
"I need flights and hotels for Miami"
"Plan my trip from Boston to Seattle"
```

### Testing Interruption Flow

1. **Start a long-running search**:
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test1", "message": "Find flights and hotels for Hawaii"}'
```

2. **Immediately interrupt** (within a few seconds):
```bash
curl -X POST http://127.0.0.1:8000/interrupt \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test1"}'
```

3. **Check status**:
```bash
curl http://127.0.0.1:8000/status/test1
```

4. **Verify partial results are preserved** in the response

### Using Python Client

```python
import httpx
import asyncio

async def test_workflow():
    async with httpx.AsyncClient() as client:
        # Start search
        resp = await client.post(
            "http://127.0.0.1:8000/chat",
            json={"user_id": "demo", "message": "Find flights to Paris"}
        )
        print(f"Task started: {resp.json()}")
        
        # Wait a bit
        await asyncio.sleep(1)
        
        # Interrupt
        await client.post(
            "http://127.0.0.1:8000/interrupt",
            json={"user_id": "demo"}
        )
        print("Interrupted!")
        
        # Check status
        status = await client.get("http://127.0.0.1:8000/status/demo")
        print(f"Status: {status.json()}")

asyncio.run(test_workflow())
```

---

## 🔧 Configuration

### Using Real APIs

To integrate real flight/hotel APIs, modify:

1. **`backend/tools/flight_api.py`**: Replace `search_flights` with actual API calls
2. **`backend/tools/hotel_api.py`**: Replace `search_hotels` with actual API calls

Example with httpx:
```python
async def search_flights(input_data: dict, final: bool = False):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            config.FLIGHT_API_URL,
            params={"from": input_data["source"], "to": input_data["destination"]},
            headers={"Authorization": f"Bearer {config.FLIGHT_API_KEY}"}
        )
        return response.json()
```

### Enabling LLM-Based Intent Detection

Set `use_llm=True` in the Coordinator initialization to use OpenAI for query parsing:

```python
# In graph_workflow.py or where Coordinator is used
coordinator = Coordinator(use_llm=True)
```

---

## 📦 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── runner.py               # AgentManager orchestration
├── graph_workflow.py       # LangGraph workflow definition
├── state_store.py          # Conversation & state management
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── agent/
│   ├── base_agent.py       # Abstract agent interface
│   ├── coordinator.py      # Intent routing logic
│   ├── flight_agent.py     # Flight search agent
│   └── hotel_agent.py      # Hotel search agent
└── tools/
    ├── flight_api.py       # Flight API integration (stubbed)
    └── hotel_api.py        # Hotel API integration (stubbed)
```

---

## 🎯 Technical Highlights

### Multi-Agent Architecture
- **LangGraph StateGraph** for workflow orchestration
- **Modular agent design** with clear interfaces and responsibilities
- **Dynamic routing** based on user intent detection

### Interruption Handling
- **Graceful cancellation** using asyncio.Event and task.cancel()
- **Partial result preservation** via progress callbacks and state store
- **Context continuity** through LangGraph checkpointing

### Async & Performance
- **Fully async** implementation for non-blocking operations
- **Concurrent agent execution** when multiple agents needed
- **Streaming partial results** for responsive user experience

### Extensibility
- Easy to add new agents (just extend `BaseAgent`)
- Pluggable API integrations via tools module
- Optional LLM enhancement for intent detection

---

## 🚧 Future Enhancements (Bonus Features)

- [ ] Multi-leg flight itinerary support
- [ ] Price comparison across multiple providers
- [ ] Booking simulation flow
- [ ] Multi-modal responses (maps, images)
- [ ] User profile & preferences (seat class, hotel rating)
- [ ] WebSocket support for real-time updates
- [ ] Persistent storage (PostgreSQL/MongoDB)
- [ ] Frontend React application
- [ ] Docker containerization
- [ ] CI/CD pipeline

---

## 📝 License

MIT

---

## 👥 Contributors

PECATHON Team - Hackathon 2025
