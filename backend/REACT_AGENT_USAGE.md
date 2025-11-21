# LangGraph ReAct Agent - Usage Guide

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Optional: Set Tavily API key for real search
export TAVILY_API_KEY="tvly-your-key-here"
```

Or create a `.env` file:
```env
OPENAI_API_KEY=sk-your-key-here
TAVILY_API_KEY=tvly-your-key-here  # Optional
```

### 2. Run Demo Mode

```bash
python langgraph_react_agent.py
```

**Output:**
```
🚀 LangGraph ReAct Travel Agent - Demo
✅ ReAct agent graph compiled successfully!

📝 Query 1: Find me flights from Delhi to Dubai on 15 Jan

🧠 REASON NODE: Analyzing query...
   → Decision: Tool call requested
   → Routing to ACT node (tool calls: 1)
🔍 Searching flights: Delhi to Dubai on 15 Jan

🧠 REASON NODE: Analyzing query...
   → Decision: Based on the search results...
   → Routing to RESPOND node (direct answer)

💬 RESPOND NODE: Generating final response...

✅ FINAL RESPONSE:
Here are the available flights from Delhi to Dubai on January 15:

1. **Air India AI501**
   - Departure: 06:00 AM → Arrival: 09:30 AM
   - Duration: 3h 30m
   - Price: ₹5,500
   - Non-stop, Economy class

2. **IndiGo 6E234**
   - Departure: 08:15 AM → Arrival: 11:50 AM
   - Duration: 3h 35m
   - Price: ₹4,800
   - Non-stop, Economy class

3. **Vistara UK985**
   - Departure: 02:30 PM → Arrival: 06:10 PM
   - Duration: 3h 40m
   - Price: ₹6,200
   - Non-stop, Premium Economy class

I recommend the IndiGo flight if you're looking for the best value!
```

### 3. Run Interactive Mode

```bash
python langgraph_react_agent.py --interactive
```

**Example Session:**
```
🚀 LangGraph ReAct Travel Agent - Interactive Mode
Commands:
  - Type your travel query
  - Type 'quit' or 'exit' to stop

💬 You: Show me hotels in Goa near the beach

🧠 REASON NODE: Analyzing query...
🔍 Searching hotels: Goa near the beach

🤖 Agent: I found some great beachfront hotels in Goa:

1. **The Taj Mahal Palace** (5⭐, Rating: 4.8)
   - Price: ₹12,000/night
   - Location: Colaba
   - Amenities: Pool, Spa, WiFi, Restaurant, Gym

2. **Hotel Marine Plaza** (4⭐, Rating: 4.2)
   - Price: ₹4,500/night
   - Location: Marine Drive
   - Amenities: WiFi, Restaurant, Room Service

Would you like more details about any of these?

💬 You: quit
👋 Goodbye!
```

---

## 🏗️ Architecture

### Graph Structure

```
    START
      │
      ▼
  ┌─────────┐
  │ REASON  │ ◀──────────┐
  │  Node   │            │
  └────┬────┘            │
       │                 │
   [Decision]            │
       │                 │
    ┌──┴───┐             │
    │      │             │
    ▼      ▼             │
  ACT   RESPOND          │
  Node   Node            │
    │      │             │
    └──────┘             │
       │                 │
       └─────────────────┘
       │
       ▼
      END
```

### ReAct Pattern

1. **REASON**: LLM decides what action to take
   - Analyzes user query
   - Decides if tools are needed
   - Returns tool calls or direct answer

2. **ACT**: Execute tools (if needed)
   - Calls `search_flights()` or `search_hotels()`
   - Returns results to the graph

3. **RESPOND**: Format final answer
   - LLM processes tool results
   - Generates user-friendly response

---

## 🛠️ Code Structure

### Tools

```python
@tool
def search_flights(query: str) -> str:
    """Search for flights based on natural language query."""
    # Returns JSON with flight results
    
@tool
def search_hotels(query: str) -> str:
    """Search for hotels based on natural language query."""
    # Returns JSON with hotel results
```

### State

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
```

### Nodes

- **reason_node**: LLM reasoning and decision-making
- **ToolNode**: Automatic tool execution (built-in)
- **respond_node**: Final response formatting

### Routing

```python
def should_continue(state) -> Literal["act", "respond"]:
    """Routes to tools or response based on LLM decision."""
```

---

## 🔧 Customization

### Add Real Search API

Replace mock data in tools with real API calls:

```python
@tool
def search_flights(query: str) -> str:
    from tavily import TavilyClient
    
    client = TavilyClient(api_key=TAVILY_API_KEY)
    results = client.search(
        query=f"flights {query}",
        search_depth="advanced"
    )
    
    return json.dumps(results)
```

### Change LLM Model

```python
# Use Anthropic Claude
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
```

### Add More Tools

```python
@tool
def search_car_rentals(query: str) -> str:
    """Search for car rentals."""
    # Implementation
    
# Add to graph
workflow.add_node("act", ToolNode([
    search_flights, 
    search_hotels, 
    search_car_rentals  # New tool
]))
```

### Add Memory/Checkpointing

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Use with thread_id for conversation memory
result = app.invoke(
    input_state,
    config={"configurable": {"thread_id": "user123"}}
)
```

---

## 📊 Example Queries

### Flights
- "Find me flights from Delhi to Dubai on 15 Jan"
- "Show me cheapest flights from Mumbai to London next week"
- "I need a direct flight from Bangalore to Singapore"

### Hotels
- "Hotels in Mumbai under 5,000 INR per night"
- "5-star hotels in Goa near the beach"
- "Budget hotels in Delhi with WiFi and breakfast"

### Multi-Intent
- "I need flights to Paris and hotels near Eiffel Tower"
- "Book me a flight to Dubai and find a 4-star hotel"

---

## 🐛 Troubleshooting

### API Key Error
```
Error code: 401 - You didn't provide an API key
```

**Solution:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### Import Error
```
ModuleNotFoundError: No module named 'langchain_openai'
```

**Solution:**
```bash
pip install langchain-openai langgraph
```

### Tool Not Called
If the LLM doesn't call tools, try:
- Make queries more specific
- Adjust LLM temperature (0.0 for deterministic)
- Add more context in the system message

---

## 🎯 Production Checklist

- [ ] Add authentication/authorization
- [ ] Implement rate limiting
- [ ] Add logging and monitoring
- [ ] Use real search APIs (Tavily, SerpAPI, Amadeus)
- [ ] Add error retry logic
- [ ] Implement conversation memory
- [ ] Add input validation
- [ ] Set up CI/CD pipeline
- [ ] Add unit tests
- [ ] Configure environment variables properly

---

## 📚 References

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **LangChain Tools**: https://python.langchain.com/docs/modules/tools/
- **Tavily API**: https://tavily.com/
- **ReAct Paper**: https://arxiv.org/abs/2210.03629

---

**Built with ❤️ using LangGraph and LangChain**
