# Multi-Agent Travel Planning Assistant - Quick Start

## ✅ What's Implemented

### Backend (100% Complete)
- ✅ FlightAgent (Amadeus API integration)
- ✅ HotelAgent (Booking.com API via RapidAPI)
- ✅ StateStore (thread-safe partial result storage)
- ✅ IntentDetector (regex-based NLP)
- ✅ CoordinatorAgent (parallel agent orchestration)
- ✅ TaskRunner (async task management)
- ✅ FastAPI REST endpoints
- ✅ Integration tests

## 🚀 How to Run

### 1. Install Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### 2. Configure API Keys

Create `.env` file:

```bash
# Required for flight search
AMADEUS_API_KEY=your_amadeus_key
AMADEUS_API_SECRET=your_amadeus_secret

# Optional for hotel search (uses mock data if not provided)
RAPIDAPI_KEY=your_rapidapi_key
```

**Get API Keys:**
- Amadeus: https://developers.amadeus.com/register (free)
- RapidAPI: https://rapidapi.com/apidojo/api/booking (freemium)

### 3. Start the Server

```bash
python3 main.py
```

Server runs at `http://localhost:8000`

### 4. Test the API

**Option A: Using `curl`**

```bash
# Start search
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Find flights from JFK to LAX on 2025-12-15 and hotels"}'

# Response: {"request_id": "req_abc123", "status": "started"}

# Check status
curl http://localhost:8000/api/status/req_abc123

# Cancel search
curl -X POST http://localhost:8000/api/cancel/req_abc123
```

**Option B: Using Python Test Script**

```bash
# Run integration tests (server must be running)
python3 test_integration.py
```

**Option C: API Documentation**

Visit `http://localhost:8000/docs` for interactive Swagger UI

## 📡 API Endpoints

### POST /api/message
Start a new search

**Request:**
```json
{
  "message": "Find flights from JFK to LAX on 2025-12-15 and hotels in Los Angeles",
  "request_id": "optional_custom_id"
}
```

**Response:**
```json
{
  "request_id": "req_abc123",
  "status": "started",
  "message": "Search started..."
}
```

### GET /api/status/{request_id}
Get current status and partial/final results

**Response (while running):**
```json
{
  "request_id": "req_abc123",
  "is_running": true,
  "status": "running",
  "data": {
    "agents": {
      "flight_agent": {"status": "running", "partial_count": 2},
      "hotel_agent": {"status": "running", "partial_count": 1}
    },
    "partials": {
      "flight_agent": [...],
      "hotel_agent": [...]
    }
  }
}
```

**Response (completed):**
```json
{
  "request_id": "req_abc123",
  "is_running": false,
  "status": "completed",
  "data": {
    "results": {
      "flight_agent": {
        "status": "completed",
        "results": [15 flights],
        "metadata": {"total_results": 15}
      },
      "hotel_agent": {
        "status": "completed",
        "results": [16 hotels],
        "metadata": {"total_results": 16}
      }
    }
  }
}
```

### POST /api/cancel/{request_id}
Cancel a running search

**Response:**
```json
{
  "request_id": "req_abc123",
  "status": "cancelled",
  "message": "Search cancelled successfully",
  "partial_results": {
    "flight_agent": [{...}, {...}],
    "hotel_agent": [{...}]
  }
}
```

## 🧪 Run Tests

```bash
# Test individual agents
python3 test_flight_agent.py

# Test hotel agent
python3 -c "
import asyncio
from state_store import StateStore
from agent.hotel_agent import HotelAgent

async def test():
    store = StateStore()
    agent = HotelAgent(store)
    result = await agent.run('test', {'location': 'Los Angeles', 'checkin': '2025-12-15', 'checkout': '2025-12-17'})
    print(f'Hotels found: {result[\"metadata\"][\"total_results\"]}')

asyncio.run(test())
"

# Test coordinator
python3 -c "
import asyncio
from state_store import StateStore
from agent.coordinator import CoordinatorAgent

async def test():
    store = StateStore()
    coord = CoordinatorAgent(store)
    result = await coord.process_message('Find flights from JFK to LAX on 2025-12-15 and hotels')
    print(f'Status: {result[\"status\"]}')
    print(f'Intents: {result[\"intents\"]}')

asyncio.run(test())
"

# Integration tests (requires server running)
python3 test_integration.py
```

## 🏗️ Architecture

```
User Request (HTTP)
    ↓
FastAPI (/api/message)
    ↓
TaskRunner (background async task)
    ↓
CoordinatorAgent
    ↓
IntentDetector → ["flight", "hotel"]
    ↓
┌─────────────────┬─────────────────┐
│  FlightAgent    │   HotelAgent    │
│  (parallel)     │   (parallel)    │
└────────┬────────┴────────┬────────┘
         │                 │
         ↓                 ↓
    Amadeus API      Booking.com API
         │                 │
         ↓                 ↓
    StateStore (partial results)
         │
         ↓
GET /api/status (polling)
         │
         ↓
    Final Response
```

## 🎯 Features

- ✅ **Async execution** - Non-blocking parallel agent processing
- ✅ **Real-time progress** - Partial results streaming
- ✅ **Graceful cancellation** - Preserve partial results on cancel
- ✅ **Multi-agent** - Flight + Hotel search simultaneously
- ✅ **Intent detection** - NLP parameter extraction
- ✅ **Production APIs** - Amadeus + Booking.com integration
- ✅ **Thread-safe** - Concurrent request handling
- ✅ **CORS enabled** - Frontend-ready

## 📂 Project Structure

```
backend/
├── main.py                 # FastAPI app
├── runner.py               # Task manager
├── state_store.py          # State management
├── intent_detector.py      # NLP intent detection
├── requirements.txt        # Dependencies
├── .env                    # API keys (create this)
├── agent/
│   ├── base_agent.py       # Base class
│   ├── flight_agent.py     # Flight search
│   ├── hotel_agent.py      # Hotel search
│   └── coordinator.py      # Orchestration
├── tools/
│   ├── flight_api.py       # Amadeus integration
│   └── hotel_api.py        # Booking.com integration
└── tests/
    ├── test_flight_agent.py
    └── test_integration.py
```

## 🔧 Troubleshooting

**Server won't start:**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

**Import errors:**
```bash
# Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall
```

**API key issues:**
- Check `.env` file exists in `backend/` directory
- Verify keys are valid on provider websites
- System works with mock data if keys not configured

## 📝 Example Usage

**Simple flight search:**
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Find flights from NYC to LA tomorrow"}'
```

**Multi-intent search:**
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Book flights JFK to LAX Dec 15 for 2 passengers and hotels near LAX"}'
```

**Check progress:**
```bash
# Poll every second
watch -n 1 curl http://localhost:8000/api/status/req_abc123
```

## 🎉 You're Ready!

The backend is fully functional. To add a frontend, see the React integration guide in `frontend/README.md` (not yet implemented - optional Step 7).
