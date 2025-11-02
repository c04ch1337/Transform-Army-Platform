"""
Simplified FastAPI application for testing basic API endpoints.
"""

from fastapi import FastAPI
from datetime import datetime

# Create a simple FastAPI app
app = FastAPI(
    title="Transform Army AI Adapter Service",
    description="Simple API for testing",
    version="1.0.0"
)

# Basic health endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "environment": "development"
    }

@app.get("/health/providers")
async def provider_registry_status():
    """Get current provider registry status."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_registered": 3,
        "total_configured": 3,
        "registry": {
            "crm": {"count": 1, "providers": ["HubSpot"], "classes": ["HubSpotProvider"]},
            "helpdesk": {"count": 1, "providers": ["Zendesk"], "classes": ["ZendeskProvider"]},
            "calendar": {"count": 1, "providers": ["Google Calendar"], "classes": ["GoogleCalendarProvider"]}
        },
        "configured": {
            "hubspot": True,
            "zendesk": True,
            "google_calendar": True
        }
    }

@app.get("/api/v1/logs/stats")
async def get_action_stats():
    """Get action log statistics."""
    return {
        "total_actions": 0,
        "successful_actions": 0,
        "failed_actions": 0,
        "average_execution_time_ms": 0.0,
        "actions_by_type": {},
        "actions_by_provider": {}
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "service": "Transform Army AI Adapter Service",
        "version": "1.0.0",
        "environment": "development",
        "status": "operational",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_simple:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
