import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


class ChatRequest(BaseModel):
    user_id: str
    message: str


class InterruptRequest(BaseModel):
    user_id: str


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )