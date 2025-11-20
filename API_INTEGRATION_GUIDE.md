# Real API Integration Guide

This guide will help you integrate real flight and hotel APIs into your travel assistant.

## 🔑 API Options

### Option 1: Amadeus API (Recommended) ⭐

**Best for**: Production-grade flight and hotel data  
**Cost**: Free tier available (2,000 calls/month)  
**Data Quality**: Excellent - real airline pricing and availability

#### Getting Started with Amadeus

1. **Register for API Access**
   - Go to: https://developers.amadeus.com/register
   - Create a free account
   - Verify your email

2. **Create an App**
   - Login to: https://developers.amadeus.com/my-apps
   - Click "Create New App"
   - Choose "Self-Service" plan (free tier)
   - Note your **API Key** and **API Secret**

3. **Configure Your Backend**
   ```bash
   # Edit backend/.env
   AMADEUS_API_KEY=your_api_key_here
   AMADEUS_API_SECRET=your_api_secret_here
   AMADEUS_HOSTNAME=test.api.amadeus.com
   USE_REAL_APIS=True
   ```

4. **Test Your Setup**
   ```bash
   cd backend
   .venv\Scripts\activate
   python -c "from tools.flight_api import AmadeusFlightAPI; import asyncio; api = AmadeusFlightAPI(); print(asyncio.run(api.search_flights('NYC', 'LAX')))"
   ```

#### Amadeus API Endpoints We Use

- **Flight Search**: `/v2/shopping/flight-offers`
  - Real-time flight prices from 400+ airlines
  - Multiple booking classes
  - Direct and connecting flights

- **Hotel Search**: `/v3/shopping/hotel-offers`
  - 150,000+ hotels worldwide
  - Real-time availability
  - Multiple room types

---

### Option 2: SerpAPI (Alternative)

**Best for**: Quick setup, Google search results  
**Cost**: Free tier (100 searches/month)  
**Data Quality**: Good - Google Flights/Hotels data

#### Getting Started with SerpAPI

1. **Register**
   - Go to: https://serpapi.com/users/sign_up
   - Create account
   - Get your API key from dashboard

2. **Configure**
   ```bash
   # Edit backend/.env
   SERPAPI_KEY=your_serpapi_key
   USE_REAL_APIS=True
   ```

3. **Test**
   ```bash
   python -c "from tools.flight_api import SerpAPIFlightSearch; import asyncio; api = SerpAPIFlightSearch(); print(asyncio.run(api.search_flights('NYC', 'LAX')))"
   ```

---

### Option 3: RapidAPI (Multiple Providers)

**Best for**: Access to multiple travel APIs  
**Cost**: Varies by provider (many free tiers)

Popular APIs on RapidAPI:
- **Skyscanner Flight Search**
- **Booking.com Hotels**
- **Priceline**

1. **Sign Up**: https://rapidapi.com/auth/sign-up
2. **Subscribe to APIs** (free tiers available)
3. **Get API Key** from dashboard
4. **Update config** with `RAPIDAPI_KEY`

---

## 🚀 Installation & Setup

### Step 1: Install New Dependencies

```bash
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
```

New packages added:
- `amadeus>=9.0.0` - Amadeus SDK
- `google-search-results>=2.4.2` - SerpAPI SDK

### Step 2: Update Environment File

```bash
# Copy example to .env if you haven't already
copy .env.example .env

# Edit .env with your API keys
notepad .env
```

Required settings:
```env
# For Amadeus
AMADEUS_API_KEY=your_key
AMADEUS_API_SECRET=your_secret
USE_REAL_APIS=True

# OR for SerpAPI
SERPAPI_KEY=your_key
USE_REAL_APIS=True
```

### Step 3: Test the Integration

Run the test script:
```bash
python test_backend.py
```

Or test specific API:
```bash
# Test Amadeus flights
python -c "from tools.flight_api import search_flights; import asyncio; print(asyncio.run(search_flights({'source': 'NYC', 'destination': 'LAX'}, final=True)))"

# Test Amadeus hotels
python -c "from tools.hotel_api import search_hotels; import asyncio; print(asyncio.run(search_hotels({'location': 'PAR'}, final=True)))"
```

### Step 4: Start the Server

```bash
python main.py
```

Visit http://127.0.0.1:8000/docs to test via Swagger UI

---

## 📊 API Comparison

| Feature | Amadeus | SerpAPI | RapidAPI |
|---------|---------|---------|----------|
| **Free Tier** | 2,000 calls/mo | 100 calls/mo | Varies |
| **Data Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Setup Difficulty** | Easy | Very Easy | Medium |
| **Coverage** | Global | Global | Global |
| **Real-time Prices** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Best For** | Production | Quick demos | Flexibility |

---

## 🧪 Testing Real APIs

### Test Flight Search

**Endpoint**: `POST /chat`

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/chat" `
  -ContentType "application/json" `
  -Body '{"user_id":"demo","message":"Find flights from NYC to LAX on 2025-12-01"}'
```

Expected response (with real API):
```json
{
  "task_id": "...",
  "status": "processing"
}
```

Then check status:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/status/demo"
```

You should see real flight data:
```json
{
  "response": "Found 5 flights: [{'airline': 'AA', 'price': 299.99, ...}]"
}
```

### Test Hotel Search

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/chat" `
  -ContentType "application/json" `
  -Body '{"user_id":"demo","message":"Find hotels in Paris for Dec 1-3"}'
```

---

## 🔧 Troubleshooting

### "Authentication failed" Error

**Problem**: Invalid API credentials

**Solution**:
1. Double-check your API key/secret in `.env`
2. Ensure no extra spaces in credentials
3. For Amadeus, verify you're using the correct hostname:
   - Test: `test.api.amadeus.com`
   - Production: `production.api.amadeus.com`

### "Rate limit exceeded"

**Problem**: Too many API calls

**Solution**:
1. Check your API usage in provider dashboard
2. Upgrade to paid tier if needed
3. Set `USE_REAL_APIS=False` to use mock data temporarily

### "Invalid location code"

**Problem**: API requires IATA codes (3-letter airport/city codes)

**Solution**:
- Use proper codes: NYC → JFK, Los Angeles → LAX, Paris → PAR
- The coordinator tries to extract codes automatically
- For better results, use OpenAI for query parsing (see below)

---

## 🤖 Enhanced Query Parsing with OpenAI (Optional)

For better parameter extraction from natural language, enable LLM parsing:

### Step 1: Get OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Create API key
3. Add to `.env`:
   ```env
   OPENAI_API_KEY=sk-...
   ```

### Step 2: Enable LLM Parsing

The coordinator already supports LLM mode. To enhance it further, update `agent/coordinator.py`:

```python
def __init__(self, use_llm: bool = True):  # Change to True
    ...
```

This will use OpenAI to:
- Extract source/destination from natural language
- Parse dates in various formats
- Understand complex queries like "I need to fly from New York to LA next Friday and stay for 3 nights"

---

## 📈 Production Considerations

### 1. Caching

Add Redis caching for API responses:
```python
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

# Cache flight results for 1 hour
cache.setex(f"flights:{origin}:{dest}:{date}", 3600, json.dumps(results))
```

### 2. Error Handling

Already implemented fallbacks:
- Amadeus fails → Try SerpAPI
- All APIs fail → Use mock data
- Preserves user experience

### 3. Rate Limiting

Add request throttling:
```python
from slowapi import Limiter
limiter = Limiter(key_func=lambda: request.client.host)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(req: ChatRequest):
    ...
```

### 4. Monitoring

Track API usage:
```python
import logging
logging.info(f"Amadeus API call: {origin}->{dest}, Cost: 1 credit")
```

---

## 🎯 Quick Start Checklist

- [ ] Sign up for Amadeus or SerpAPI
- [ ] Get API credentials
- [ ] Update `backend/.env` with keys
- [ ] Set `USE_REAL_APIS=True`
- [ ] Install new dependencies: `pip install -r requirements.txt`
- [ ] Test API: Run `test_backend.py`
- [ ] Start server: `python main.py`
- [ ] Test endpoint: Send chat request via `/docs` or curl
- [ ] Verify real data in response

---

## 💡 Tips for Demo

1. **Use real data**: Shows production readiness
2. **Show fallbacks**: Demonstrate error handling
3. **Cache responses**: Avoid hitting rate limits during demo
4. **Prepare test queries**: 
   - "Find flights from New York to San Francisco"
   - "Show me hotels in Tokyo"
   - "I need flights and hotels for London next week"

---

## 📚 Additional Resources

- **Amadeus Docs**: https://developers.amadeus.com/self-service
- **SerpAPI Docs**: https://serpapi.com/google-flights-api
- **RapidAPI Hub**: https://rapidapi.com/hub
- **OpenAI API**: https://platform.openai.com/docs

---

**Need Help?** Check the error logs in terminal or raise an issue!
