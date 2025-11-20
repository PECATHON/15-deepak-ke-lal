"""
FastAPI Backend - REST API for Multi-Agent Travel Planning Assistant.

Endpoints:
- POST /api/message - Start a new search
- POST /api/cancel/{request_id} - Cancel a running search
- GET /api/status/{request_id} - Get status and partial results
- GET /api/health - Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import uuid

from state_store import StateStore
from agent.coordinator import CoordinatorAgent
from runner import TaskRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Travel Planning API",
    description="Async travel search with cancellation support",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global components
state_store = StateStore()
coordinator = CoordinatorAgent(state_store)
task_runner = TaskRunner(coordinator)

logger.info("[FastAPI] Application initialized")


# Request/Response models
class MessageRequest(BaseModel):
    message: str
    request_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Find flights from JFK to LAX on 2025-12-15 and hotels in Los Angeles",
                "request_id": "optional_custom_id"
            }
        }


class MessageResponse(BaseModel):
    request_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    request_id: str
    is_running: bool
    status: str
    data: dict


# Endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Multi-Agent Travel Planning API",
        "version": "1.0.0"
    }


@app.post("/api/message", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    """
    Process user message and start agent search.
    
    Returns immediately with request_id.
    Use /api/status/{request_id} to check progress.
    """
    try:
        # Generate request ID if not provided
        request_id = request.request_id or f"req_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"[API] Received message for {request_id}: {request.message}")
        
        # Start background task
        task_runner.start_task(request_id, request.message)
        
        return {
            "request_id": request_id,
            "status": "started",
            "message": "Search started. Use /api/status/{request_id} to check progress."
        }
        
    except Exception as e:
        logger.error(f"[API] Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cancel/{request_id}")
async def cancel_request(request_id: str):
    """
    Cancel a running search request.
    
    Returns partial results collected before cancellation.
    """
    try:
        logger.info(f"[API] Cancellation requested for {request_id}")
        
        success = task_runner.cancel_task(request_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Request {request_id} not found or already completed"
            )
        
        # Get partial results
        status = task_runner.get_status(request_id)
        
        return {
            "request_id": request_id,
            "status": "cancelled",
            "message": "Search cancelled successfully",
            "partial_results": status.get("partials", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error cancelling request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{request_id}", response_model=StatusResponse)
async def get_status(request_id: str):
    """
    Get current status of a search request.
    
    Returns:
    - is_running: Whether search is still in progress
    - status: Current status (running, completed, cancelled, error)
    - data: Partial or final results
    """
    try:
        status = task_runner.get_status(request_id)
        
        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
        
        return {
            "request_id": request_id,
            "is_running": status.get("is_running", False),
            "status": status.get("status", "unknown"),
            "data": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error getting status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("[FastAPI] Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("[FastAPI] Application shutting down")


if __name__ == "__main__":
    import uvicorn
    
    logger.info("[FastAPI] Starting server on http://localhost:8000")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
