import os
import sys
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json

# ensure backend package path is importable when running from workspace root
sys.path.append(os.path.dirname(__file__))

try:
    from runner import AgentManager
    from config import config
except ImportError:
    import runner
    import config as config_module
    AgentManager = runner.AgentManager
    config = config_module.config

app = FastAPI(
    title="Travel Planning Assistant - Backend",
    description="Multi-agent travel assistant with LangGraph orchestration",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = AgentManager()

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """Connect a WebSocket for a user."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        """Disconnect a WebSocket."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_message(self, user_id: str, message: dict):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)

ws_manager = ConnectionManager()


class ChatRequest(BaseModel):
    user_id: str
    message: str


class InterruptRequest(BaseModel):
    user_id: str


# Initialize manager after ws_manager is created
manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize the agent manager with WebSocket support."""
    global manager
    manager = AgentManager(ws_manager=ws_manager)


@app.get("/")
def root():
    return {
        "service": "Travel Planning Assistant",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    """Submit a new user query to the travel assistant.
    
    Returns a task_id that can be used to track status.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    task_id = await manager.handle_user_message(req.user_id, req.message)
    return {"task_id": task_id, "status": "processing"}


@app.post("/interrupt")
async def interrupt(req: InterruptRequest):
    """Interrupt the currently running workflow for a user.
    
    Cancels in-flight agent operations and preserves partial results.
    """
    await manager.interrupt(req.user_id)
    return {"status": "interrupted", "user_id": req.user_id}


@app.get("/status/{user_id}")
def status(user_id: str):
    """Get current workflow status for a user."""
    return manager.get_status(user_id)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time agent status updates.
    
    Clients connect to this endpoint to receive streaming updates about:
    - Agent execution progress
    - Partial results as they arrive
    - Task status changes
    - Interruption notifications
    """
    await ws_manager.connect(user_id, websocket)
    
    # Define callback for status updates
    async def status_callback(context):
        """Send status updates through WebSocket."""
        message = {
            "type": "status_update",
            "task_id": context.task_id,
            "status": context.status.value,
            "current_agent": context.current_agent,
            "partial_results": context.partial_results,
            "timestamp": context.updated_at.isoformat()
        }
        await ws_manager.send_message(user_id, message)
    
    # Register the callback
    await manager.register_status_callback(user_id, status_callback)
    
    try:
        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            
            # Handle client messages (e.g., ping/pong for keepalive)
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
        await manager.unregister_status_callback(user_id, status_callback)
    except Exception as e:
        print(f"WebSocket error for {user_id}: {e}")
        ws_manager.disconnect(user_id)
        await manager.unregister_status_callback(user_id, status_callback)


@app.get("/partial-results/{user_id}")
async def get_partial_results(user_id: str):
    """Get current partial results for a user.
    
    This is useful for clients that don't use WebSocket but still want
    to poll for partial results during long-running operations.
    """
    status = manager.get_status(user_id)
    return {
        "user_id": user_id,
        "partial_results": status.get("partial_results", {}),
        "status": status.get("status", "idle")
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )