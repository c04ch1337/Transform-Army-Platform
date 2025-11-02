"""
Simplified FastAPI application for Transform Army AI Adapter Service.
This version runs without database dependencies for development.
"""

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Literal, Tuple
from pydantic import BaseModel, Field
import random
import hmac
import hashlib
import time
import json
from pathlib import Path
import copy

# ============================================================================
# AGENT CONFIGURATION STORAGE - Phase 2
# ============================================================================

# Agent configuration storage (in-memory for now)
agent_configs_storage: Dict[str, Dict[str, Any]] = {}  # {agent_id: config_dict}
config_history_storage: Dict[str, List[Dict[str, Any]]] = {}  # {agent_id: [list of versions]}

# Agent ID to filename mapping
AGENT_CONFIG_FILES = {
    "agent_bdr_concierge": "hunter-bdr.json",
    "agent_support_concierge": "medic-support.json",
    "agent_research_recon": "scout-research.json",
    "agent_ops_sapper": "engineer-ops.json",
    "agent_knowledge_librarian": "intel-knowledge.json",
    "agent_qa_auditor": "guardian-qa.json"
}


def load_default_agent_configs() -> None:
    """
    Load default agent configurations from vapi-config directory.
    This function loads all 6 JSON configuration files on startup.
    """
    config_dir = Path(__file__).parent.parent.parent.parent / "vapi-config" / "assistants"
    
    if not config_dir.exists():
        print(f"[WARNING] Config directory not found: {config_dir}")
        return
    
    loaded_count = 0
    for agent_id, filename in AGENT_CONFIG_FILES.items():
        config_file = config_dir / filename
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    agent_configs_storage[agent_id] = config
                    
                    # Initialize version history with default config
                    if agent_id not in config_history_storage:
                        config_history_storage[agent_id] = []
                    
                    save_config_version(
                        agent_id,
                        config,
                        "Initial configuration loaded from default"
                    )
                    
                    loaded_count += 1
                    print(f"[CONFIG] Loaded {agent_id} from {filename}")
            except Exception as e:
                print(f"[ERROR] Failed to load {filename}: {e}")
        else:
            print(f"[WARNING] Config file not found: {config_file}")
    
    print(f"[CONFIG] Loaded {loaded_count}/{len(AGENT_CONFIG_FILES)} agent configurations")


def validate_agent_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate agent configuration structure.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Required top-level fields
    required_fields = ["name", "model", "voice", "serverUrl", "functions"]
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Model validation
    if "model" in config:
        if not isinstance(config["model"], dict):
            errors.append("model must be an object")
        else:
            if "model" not in config["model"]:
                errors.append("model.model is required")
            
            if "temperature" in config["model"]:
                temp = config["model"]["temperature"]
                if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                    errors.append("model.temperature must be between 0 and 2")
            
            if "maxTokens" in config["model"]:
                max_tokens = config["model"]["maxTokens"]
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    errors.append("model.maxTokens must be a positive integer")
    
    # Voice validation
    if "voice" in config:
        if not isinstance(config["voice"], dict):
            errors.append("voice must be an object")
        else:
            if "provider" not in config["voice"]:
                errors.append("voice.provider is required")
            if "voiceId" not in config["voice"]:
                errors.append("voice.voiceId is required")
    
    # Functions validation
    if "functions" in config:
        if not isinstance(config["functions"], list):
            errors.append("functions must be an array")
        else:
            for idx, func in enumerate(config["functions"]):
                if not isinstance(func, dict):
                    errors.append(f"Function at index {idx} must be an object")
                    continue
                    
                if "name" not in func:
                    errors.append(f"Function at index {idx} missing name field")
                
                if "parameters" not in func:
                    func_name = func.get("name", f"index {idx}")
                    errors.append(f"Function '{func_name}' missing parameters field")
                elif not isinstance(func["parameters"], dict):
                    func_name = func.get("name", f"index {idx}")
                    errors.append(f"Function '{func_name}' parameters must be an object")
    
    # ServerUrl validation
    if "serverUrl" in config:
        if not isinstance(config["serverUrl"], str) or len(config["serverUrl"]) == 0:
            errors.append("serverUrl must be a non-empty string")
    
    return (len(errors) == 0, errors)


def save_config_version(agent_id: str, config: Dict[str, Any], change_summary: str = "") -> None:
    """
    Save config version to history.
    
    Args:
        agent_id: Agent identifier
        config: Configuration to save
        change_summary: Description of changes made
    """
    if agent_id not in config_history_storage:
        config_history_storage[agent_id] = []
    
    version_entry = {
        "version": len(config_history_storage[agent_id]) + 1,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "config": copy.deepcopy(config),
        "changes": change_summary or "Configuration updated"
    }
    
    config_history_storage[agent_id].append(version_entry)
    
    # Keep only last 20 versions
    if len(config_history_storage[agent_id]) > 20:
        config_history_storage[agent_id] = config_history_storage[agent_id][-20:]


# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

# Create FastAPI application
app = FastAPI(
    title="Transform Army AI Adapter",
    description="Simplified adapter service for development",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Load configurations on application startup."""
    print("=" * 60)
    print("Transform Army AI Adapter - Configuration Manager")
    print("=" * 60)
    load_default_agent_configs()
    print("=" * 60)


# Configure CORS - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================================
# VAPI WEBHOOK INFRASTRUCTURE - Phase 1
# ============================================================================

# Vapi webhook secret for signature verification
VAPI_WEBHOOK_SECRET = "vapi_webhook_secret_for_testing"

# In-memory storage for call logs (in production, use database)
call_logs_storage: List[Dict[str, Any]] = []


# Pydantic Models for Vapi Webhook Payloads
class VapiFunctionCallMessage(BaseModel):
    """Model for Vapi function call webhook message."""
    message: Dict[str, Any]
    call: Optional[Dict[str, Any]] = None
    
    @property
    def message_type(self) -> str:
        """Extract message type from message payload."""
        return self.message.get("type", "unknown")
    
    @property
    def function_name(self) -> str:
        """Extract function name from function call."""
        if self.message.get("type") == "function-call":
            function_call = self.message.get("functionCall", {})
            return function_call.get("name", "")
        return ""
    
    @property
    def function_parameters(self) -> Dict[str, Any]:
        """Extract function parameters from function call."""
        if self.message.get("type") == "function-call":
            function_call = self.message.get("functionCall", {})
            return function_call.get("parameters", {})
        return {}


class VapiCallLog(BaseModel):
    """Model for storing completed Vapi call data."""
    agent_id: str = Field(..., description="ID of the agent that handled the call")
    call_id: str = Field(..., description="Unique Vapi call identifier")
    duration_seconds: Optional[int] = Field(None, description="Call duration in seconds")
    transcript: Optional[str] = Field(None, description="Full call transcript")
    outcome: Optional[str] = Field(None, description="Call outcome (completed, failed, etc.)")
    cost: Optional[float] = Field(None, description="Cost of the call in USD")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional call metadata")


class VapiFunctionResult(BaseModel):
    """Response model for function call results."""
    result: Dict[str, Any] = Field(..., description="Function execution result")
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "execution_time_ms": 0,
            "success": True
        },
        description="Execution metadata"
    )


# HMAC-SHA256 Signature Verification
def verify_vapi_signature(body: bytes, signature: str, secret: str) -> bool:
    """
    Verify webhook came from Vapi using HMAC-SHA256.
    
    Args:
        body: Raw request body as bytes
        signature: Signature from x-vapi-signature header
        secret: Shared webhook secret
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        expected = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        print(f"[ERROR] Signature verification failed: {e}")
        return False


# Function Call Router - Maps Vapi function names to handlers
async def route_function_call(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route Vapi function calls to appropriate handlers.
    
    Args:
        function_name: Name of the function to execute
        parameters: Function parameters from Vapi
        
    Returns:
        Function execution result
        
    Raises:
        HTTPException: If function not found or execution fails
    """
    start_time = time.time()
    
    try:
        # BDR Agent (Hunter) Functions
        if function_name == "search_crm_contact":
            result = await handle_search_crm_contact(parameters)
        elif function_name == "create_crm_contact":
            result = await handle_create_crm_contact(parameters)
        elif function_name == "check_calendar_availability":
            result = await handle_check_calendar_availability(parameters)
        elif function_name == "book_meeting":
            result = await handle_book_meeting(parameters)
        
        # Support Agent (Medic) Functions
        elif function_name == "search_knowledge_base":
            result = await handle_search_knowledge_base(parameters)
        elif function_name == "create_support_ticket":
            result = await handle_create_support_ticket(parameters)
        elif function_name == "search_past_tickets":
            result = await handle_search_past_tickets(parameters)
        elif function_name == "escalate_to_human":
            result = await handle_escalate_to_human(parameters)
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown function: {function_name}"
            )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return {
            "result": result,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "execution_time_ms": execution_time,
                "success": True,
                "function_name": function_name
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        print(f"[ERROR] Function execution failed: {function_name} - {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Function execution error: {str(e)}"
        )


# BDR Agent Function Handlers
async def handle_search_crm_contact(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search for CRM contacts."""
    query = params.get("query", "")
    email = params.get("email", "")
    
    # Mock search logic - integrate with existing CRM search
    contacts = [
        {
            "id": "contact_001",
            "email": email or "john.doe@acme.example",
            "first_name": "John",
            "last_name": "Doe",
            "company": "Acme Corp",
            "title": "VP of Sales",
            "phone": "+1-555-0123",
            "bant_score": {
                "budget": 85,
                "authority": 90,
                "need": 75,
                "timeline": 80,
                "overall": 82.5
            },
            "last_contact": datetime.utcnow().isoformat() + "Z"
        }
    ]
    
    return {
        "contacts": contacts,
        "total_found": len(contacts),
        "search_query": query or email
    }


async def handle_create_crm_contact(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new CRM contact with BANT scores."""
    return {
        "contact_id": f"contact_{random.randint(1000, 9999)}",
        "email": params.get("email", ""),
        "first_name": params.get("first_name", ""),
        "last_name": params.get("last_name", ""),
        "company": params.get("company", ""),
        "bant_scores": {
            "budget": params.get("budget_score", 50),
            "authority": params.get("authority_score", 50),
            "need": params.get("need_score", 50),
            "timeline": params.get("timeline_score", 50)
        },
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "created"
    }


async def handle_check_calendar_availability(params: Dict[str, Any]) -> Dict[str, Any]:
    """Check calendar availability and return time slots."""
    date = params.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    duration = params.get("duration_minutes", 30)
    
    # Generate mock available slots
    base_date = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)
    slots = []
    
    for hour_offset in [0, 1, 3, 5]:
        slot_time = base_date + timedelta(hours=hour_offset)
        slots.append({
            "start": slot_time.isoformat() + "Z",
            "end": (slot_time + timedelta(minutes=duration)).isoformat() + "Z",
            "available": True
        })
    
    return {
        "date": date,
        "available_slots": slots,
        "timezone": "America/Chicago"
    }


async def handle_book_meeting(params: Dict[str, Any]) -> Dict[str, Any]:
    """Book a meeting on the calendar."""
    return {
        "meeting_id": f"meeting_{random.randint(1000, 9999)}",
        "title": params.get("title", "Sales Meeting"),
        "start_time": params.get("start_time", datetime.utcnow().isoformat() + "Z"),
        "duration_minutes": params.get("duration_minutes", 30),
        "attendees": params.get("attendees", []),
        "meeting_link": f"https://meet.example.com/meeting-{random.randint(1000, 9999)}",
        "status": "confirmed"
    }


# Support Agent Function Handlers
async def handle_search_knowledge_base(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search knowledge base articles."""
    query = params.get("query", "")
    
    # Mock KB articles
    articles = [
        {
            "id": "kb_001",
            "title": "Getting Started with API Integration",
            "summary": "Learn how to integrate with our REST API in minutes.",
            "category": "API",
            "relevance_score": 0.92,
            "url": "https://docs.example.com/kb/api-integration"
        },
        {
            "id": "kb_002",
            "title": "Troubleshooting Common Login Issues",
            "summary": "Solutions for common authentication problems.",
            "category": "Authentication",
            "relevance_score": 0.85,
            "url": "https://docs.example.com/kb/login-issues"
        }
    ]
    
    return {
        "articles": articles,
        "total_found": len(articles),
        "query": query
    }


async def handle_create_support_ticket(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a support ticket."""
    return {
        "ticket_id": f"ticket_{random.randint(10000, 99999)}",
        "subject": params.get("subject", "Support Request"),
        "description": params.get("description", ""),
        "priority": params.get("priority", "normal"),
        "status": "open",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "requester_email": params.get("requester_email", ""),
        "assigned_to": "support_team"
    }


async def handle_search_past_tickets(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search historical support tickets."""
    email = params.get("email", "")
    status = params.get("status", "all")
    
    # Mock ticket history
    tickets = [
        {
            "id": "ticket_12345",
            "subject": "API Integration Help",
            "status": "resolved",
            "priority": "normal",
            "created_at": (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
            "resolved_at": (datetime.utcnow() - timedelta(days=6)).isoformat() + "Z"
        },
        {
            "id": "ticket_12346",
            "subject": "Billing Question",
            "status": "resolved",
            "priority": "low",
            "created_at": (datetime.utcnow() - timedelta(days=14)).isoformat() + "Z",
            "resolved_at": (datetime.utcnow() - timedelta(days=13)).isoformat() + "Z"
        }
    ]
    
    return {
        "tickets": tickets,
        "total_found": len(tickets),
        "requester_email": email,
        "status_filter": status
    }


async def handle_escalate_to_human(params: Dict[str, Any]) -> Dict[str, Any]:
    """Escalate conversation to human agent."""
    return {
        "escalation_id": f"esc_{random.randint(1000, 9999)}",
        "reason": params.get("reason", "Customer request"),
        "priority": params.get("priority", "normal"),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "pending_assignment",
        "estimated_wait_time_minutes": random.randint(2, 10),
        "ticket_id": params.get("ticket_id", None)
    }


# ============================================================================
# VAPI WEBHOOK ENDPOINTS
# ============================================================================

@app.post("/api/v1/vapi/webhook")
async def vapi_webhook_handler(
    request: Request,
    x_vapi_signature: Optional[str] = Header(None, alias="x-vapi-signature")
):
    """
    Main Vapi webhook endpoint that receives and processes voice agent function calls.
    
    Handles different message types:
    - function-call: Execute requested functions and return results
    - call-started: Log call initiation
    - call-ended: Log call completion
    - transcript: Store conversation transcript
    
    Security: Validates webhook signature using HMAC-SHA256
    Performance: Target <500ms response time
    """
    start_time = time.time()
    
    try:
        # Read raw body for signature verification
        body = await request.body()
        
        # Verify webhook signature (security requirement)
        if x_vapi_signature:
            if not verify_vapi_signature(body, x_vapi_signature, VAPI_WEBHOOK_SECRET):
                print(f"[SECURITY] Invalid webhook signature from IP: {request.client.host}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid webhook signature"
                )
        else:
            print("[WARNING] Webhook received without signature - accepting in dev mode")
        
        # Parse JSON payload
        try:
            payload = await request.json()
        except Exception as e:
            print(f"[ERROR] Failed to parse webhook payload: {e}")
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON payload"
            )
        
        # Extract message type
        message = payload.get("message", {})
        message_type = message.get("type", "unknown")
        call_data = payload.get("call", {})
        call_id = call_data.get("id", "unknown")
        
        print(f"[VAPI] Received webhook: type={message_type}, call_id={call_id}")
        
        # Route based on message type
        if message_type == "function-call":
            # Extract function details
            function_call = message.get("functionCall", {})
            function_name = function_call.get("name", "")
            parameters = function_call.get("parameters", {})
            
            print(f"[VAPI] Function call: {function_name} with params: {parameters}")
            
            # Execute function via router
            try:
                result = await route_function_call(function_name, parameters)
                
                # Calculate execution time
                execution_time = int((time.time() - start_time) * 1000)
                print(f"[VAPI] Function {function_name} completed in {execution_time}ms")
                
                # Return result in Vapi format
                return {
                    "result": result.get("result", {}),
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "execution_time_ms": execution_time,
                        "success": True,
                        "function_name": function_name
                    }
                }
            
            except HTTPException as e:
                execution_time = int((time.time() - start_time) * 1000)
                print(f"[ERROR] Function {function_name} failed: {e.detail}")
                raise
            except Exception as e:
                execution_time = int((time.time() - start_time) * 1000)
                print(f"[ERROR] Unexpected error in {function_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Function execution error: {str(e)}"
                )
        
        elif message_type == "call-started":
            # Log call start
            print(f"[VAPI] Call started: {call_id}")
            return {
                "status": "acknowledged",
                "message_type": message_type,
                "call_id": call_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        elif message_type == "call-ended":
            # Log call completion
            print(f"[VAPI] Call ended: {call_id}")
            return {
                "status": "acknowledged",
                "message_type": message_type,
                "call_id": call_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        elif message_type == "transcript":
            # Store transcript
            transcript_text = message.get("transcript", "")
            print(f"[VAPI] Transcript received for call {call_id}: {len(transcript_text)} chars")
            return {
                "status": "acknowledged",
                "message_type": message_type,
                "call_id": call_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        else:
            # Unknown message type
            print(f"[WARNING] Unknown message type: {message_type}")
            return {
                "status": "acknowledged",
                "message_type": message_type,
                "call_id": call_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "note": f"Message type '{message_type}' acknowledged but not processed"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        print(f"[ERROR] Webhook handler error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Webhook processing error: {str(e)}"
        )


@app.post("/api/v1/vapi/calls/log")
async def log_vapi_call(call_log: VapiCallLog):
    """
    Log completed Vapi call data for analytics and auditing.
    
    Stores:
    - Agent ID and call ID
    - Duration and cost
    - Full transcript
    - Call outcome
    - Additional metadata
    
    Returns:
    - Call summary
    - Analytics metrics
    - Storage confirmation
    """
    try:
        # Generate log entry
        log_entry = {
            "id": f"vapi_call_{len(call_logs_storage) + 1}",
            "agent_id": call_log.agent_id,
            "call_id": call_log.call_id,
            "duration_seconds": call_log.duration_seconds,
            "transcript": call_log.transcript,
            "outcome": call_log.outcome,
            "cost": call_log.cost,
            "metadata": call_log.metadata,
            "logged_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # Store in memory (in production, save to database)
        call_logs_storage.append(log_entry)
        
        print(f"[VAPI] Call logged: agent={call_log.agent_id}, call_id={call_log.call_id}, outcome={call_log.outcome}")
        
        # Calculate summary statistics
        total_calls = len(call_logs_storage)
        total_cost = sum(log.get("cost", 0) for log in call_logs_storage if log.get("cost"))
        total_duration = sum(log.get("duration_seconds", 0) for log in call_logs_storage if log.get("duration_seconds"))
        
        # Return summary
        return {
            "status": "logged",
            "log_id": log_entry["id"],
            "call_summary": {
                "agent_id": call_log.agent_id,
                "call_id": call_log.call_id,
                "duration_seconds": call_log.duration_seconds,
                "cost": call_log.cost,
                "outcome": call_log.outcome,
                "transcript_length": len(call_log.transcript) if call_log.transcript else 0
            },
            "analytics": {
                "total_calls_logged": total_calls,
                "total_cost": round(total_cost, 4),
                "total_duration_seconds": total_duration,
                "average_call_duration": round(total_duration / total_calls, 2) if total_calls > 0 else 0
            },
            "timestamp": log_entry["logged_at"]
        }
    
    except Exception as e:
        print(f"[ERROR] Failed to log call: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Call logging error: {str(e)}"
        )


@app.get("/api/v1/vapi/calls/logs")
async def get_vapi_call_logs(
    limit: int = 50,
    agent_id: Optional[str] = None,
    outcome: Optional[str] = None
):
    """
    Retrieve logged Vapi calls with optional filtering.
    
    Query Parameters:
    - limit: Maximum number of logs to return (default: 50)
    - agent_id: Filter by specific agent
    - outcome: Filter by call outcome
    """
    try:
        # Apply filters
        filtered_logs = call_logs_storage
        
        if agent_id:
            filtered_logs = [log for log in filtered_logs if log.get("agent_id") == agent_id]
        
        if outcome:
            filtered_logs = [log for log in filtered_logs if log.get("outcome") == outcome]
        
        # Apply limit
        filtered_logs = filtered_logs[-limit:]  # Get most recent
        
        # Reverse to show newest first
        filtered_logs = list(reversed(filtered_logs))
        
        return {
            "total": len(call_logs_storage),
            "filtered": len(filtered_logs),
            "logs": filtered_logs,
            "filters": {
                "agent_id": agent_id,
                "outcome": outcome,
                "limit": limit
            },
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
    
    except Exception as e:
        print(f"[ERROR] Failed to retrieve call logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Log retrieval error: {str(e)}"
        )


# ============================================================================
# AGENT CONFIGURATION API ENDPOINTS - Phase 2
# ============================================================================

@app.get("/api/v1/agents/{agent_id}/config")
async def get_agent_config(agent_id: str):
    """
    Get current agent configuration.
    
    Returns:
        Current configuration with metadata including version and last modified timestamp
    """
    if agent_id not in agent_configs_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Agent configuration not found for: {agent_id}"
        )
    
    config = agent_configs_storage[agent_id]
    history = config_history_storage.get(agent_id, [])
    current_version = len(history)
    last_modified = history[-1]["timestamp"] if history else datetime.utcnow().isoformat() + "Z"
    
    # Check if this is the default config
    config_dir = Path(__file__).parent.parent.parent.parent / "vapi-config" / "assistants"
    filename = AGENT_CONFIG_FILES.get(agent_id)
    is_default = False
    
    if filename and (config_dir / filename).exists():
        try:
            with open(config_dir / filename, 'r', encoding='utf-8') as f:
                default_config = json.load(f)
                is_default = (config == default_config)
        except Exception:
            pass
    
    return {
        "agent_id": agent_id,
        "config": config,
        "metadata": {
            "version": current_version,
            "last_modified": last_modified,
            "modified_by": "system",
            "is_default": is_default
        }
    }


@app.put("/api/v1/agents/{agent_id}/config")
async def update_agent_config(agent_id: str, config: Dict[str, Any]):
    """
    Update agent configuration.
    
    Validates JSON structure before saving and creates version history entry.
    
    Args:
        agent_id: Agent identifier
        config: New configuration dictionary
        
    Returns:
        Updated configuration with new version number
    """
    if agent_id not in AGENT_CONFIG_FILES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent ID: {agent_id}"
        )
    
    # Validate configuration
    is_valid, errors = validate_agent_config(config)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Configuration validation failed",
                "errors": errors
            }
        )
    
    # Save old version for comparison
    old_config = agent_configs_storage.get(agent_id)
    
    # Update configuration
    agent_configs_storage[agent_id] = config
    
    # Create version history entry
    change_summary = "Configuration updated via API"
    if old_config:
        # Generate basic change summary
        changes = []
        if old_config.get("model", {}).get("temperature") != config.get("model", {}).get("temperature"):
            changes.append("temperature modified")
        if old_config.get("model", {}).get("maxTokens") != config.get("model", {}).get("maxTokens"):
            changes.append("maxTokens modified")
        if len(old_config.get("functions", [])) != len(config.get("functions", [])):
            changes.append("functions list modified")
        
        if changes:
            change_summary = f"Updated: {', '.join(changes)}"
    
    save_config_version(agent_id, config, change_summary)
    
    # Get new version number
    current_version = len(config_history_storage[agent_id])
    
    print(f"[CONFIG] Updated {agent_id} to version {current_version}")
    
    return {
        "agent_id": agent_id,
        "config": config,
        "metadata": {
            "version": current_version,
            "last_modified": datetime.utcnow().isoformat() + "Z",
            "modified_by": "api_user",
            "is_default": False
        }
    }


@app.post("/api/v1/agents/{agent_id}/config/validate")
async def validate_config(agent_id: str, config: Dict[str, Any]):
    """
    Validate configuration without saving.
    
    Checks required fields and verifies JSON schema.
    
    Args:
        agent_id: Agent identifier
        config: Configuration to validate
        
    Returns:
        Validation result with any errors found
    """
    if agent_id not in AGENT_CONFIG_FILES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent ID: {agent_id}"
        )
    
    is_valid, errors = validate_agent_config(config)
    
    return {
        "agent_id": agent_id,
        "is_valid": is_valid,
        "errors": errors if not is_valid else [],
        "validated_at": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/v1/agents/{agent_id}/config/history")
async def get_config_history(
    agent_id: str,
    limit: int = 10,
    skip: int = 0
):
    """
    Get configuration version history.
    
    Returns last N versions with timestamps and change summaries.
    
    Args:
        agent_id: Agent identifier
        limit: Maximum number of versions to return (default: 10)
        skip: Number of versions to skip for pagination (default: 0)
        
    Returns:
        List of version entries with metadata
    """
    if agent_id not in AGENT_CONFIG_FILES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent ID: {agent_id}"
        )
    
    history = config_history_storage.get(agent_id, [])
    
    # Reverse to show newest first, then apply pagination
    reversed_history = list(reversed(history))
    paginated_history = reversed_history[skip:skip + limit]
    
    # Remove full config from response for performance, just keep metadata
    summary_history = []
    for entry in paginated_history:
        summary_history.append({
            "version": entry["version"],
            "timestamp": entry["timestamp"],
            "changes": entry["changes"]
        })
    
    return {
        "agent_id": agent_id,
        "total_versions": len(history),
        "returned": len(summary_history),
        "history": summary_history,
        "pagination": {
            "limit": limit,
            "skip": skip
        }
    }


@app.post("/api/v1/agents/{agent_id}/config/restore")
async def restore_config_version(agent_id: str, request: Dict[str, Any]):
    """
    Restore specific version from history.
    
    Creates new version (doesn't delete current) to maintain audit trail.
    
    Args:
        agent_id: Agent identifier
        request: Dict containing version number to restore
        
    Returns:
        Restored configuration with new version number
    """
    if agent_id not in AGENT_CONFIG_FILES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent ID: {agent_id}"
        )
    
    version_to_restore = request.get("version")
    if version_to_restore is None:
        raise HTTPException(
            status_code=400,
            detail="version number is required in request body"
        )
    
    history = config_history_storage.get(agent_id, [])
    
    # Find the version
    version_entry = None
    for entry in history:
        if entry["version"] == version_to_restore:
            version_entry = entry
            break
    
    if not version_entry:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version_to_restore} not found in history"
        )
    
    # Restore the configuration
    restored_config = copy.deepcopy(version_entry["config"])
    agent_configs_storage[agent_id] = restored_config
    
    # Create new version entry for the restore action
    change_summary = f"Restored from version {version_to_restore}"
    save_config_version(agent_id, restored_config, change_summary)
    
    new_version = len(config_history_storage[agent_id])
    
    print(f"[CONFIG] Restored {agent_id} from version {version_to_restore} to new version {new_version}")
    
    return {
        "agent_id": agent_id,
        "config": restored_config,
        "metadata": {
            "version": new_version,
            "restored_from_version": version_to_restore,
            "last_modified": datetime.utcnow().isoformat() + "Z",
            "modified_by": "api_user",
            "is_default": False
        }
    }


@app.post("/api/v1/agents/{agent_id}/config/reset")
async def reset_to_default_config(agent_id: str):
    """
    Reset to default configuration from JSON file.
    
    Creates backup of current config first in version history.
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        Reset configuration with new version number
    """
    if agent_id not in AGENT_CONFIG_FILES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent ID: {agent_id}"
        )
    
    # Load default configuration from file
    config_dir = Path(__file__).parent.parent.parent.parent / "vapi-config" / "assistants"
    filename = AGENT_CONFIG_FILES[agent_id]
    config_file = config_dir / filename
    
    if not config_file.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Default configuration file not found: {filename}"
        )
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            default_config = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load default configuration: {str(e)}"
        )
    
    # Backup current configuration first
    if agent_id in agent_configs_storage:
        current_config = agent_configs_storage[agent_id]
        save_config_version(agent_id, current_config, "Backup before reset to default")
    
    # Reset to default
    agent_configs_storage[agent_id] = default_config
    save_config_version(agent_id, default_config, "Reset to default configuration")
    
    new_version = len(config_history_storage[agent_id])
    
    print(f"[CONFIG] Reset {agent_id} to default configuration, version {new_version}")
    
    return {
        "agent_id": agent_id,
        "config": default_config,
        "metadata": {
            "version": new_version,
            "last_modified": datetime.utcnow().isoformat() + "Z",
            "modified_by": "api_user",
            "is_default": True
        }
    }


# ============================================================================
# EXISTING ENDPOINTS
# ============================================================================

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "service": "Transform Army AI Adapter",
        "version": "1.0.0",
        "environment": "development",
        "status": "operational",
        "mode": "simplified_standalone",
        "documentation": "/docs"
    }

# Health endpoints
@app.get("/health")
async def health():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "service": "adapter"
    }

@app.get("/health/ready")
async def readiness():
    """Readiness check endpoint."""
    return {
        "status": "ready",
        "providers": {
            "crm": "mock",
            "helpdesk": "mock",
            "calendar": "mock"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/health/providers")
async def provider_registry():
    """Enhanced provider registry with detailed health metrics."""
    now = datetime.utcnow()
    
    return {
        "status": "operational",
        "total_providers": 6,
        "last_health_check": now.isoformat() + "Z",
        "by_type": {
            "crm": {
                "count": 2,
                "providers": ["hubspot", "salesforce"],
                "classes": ["HubSpotProvider", "SalesforceProvider"],
                "health": {
                    "hubspot": {
                        "status": "operational",
                        "last_check": (now - timedelta(minutes=2)).isoformat() + "Z",
                        "response_time_ms": 145,
                        "success_rate": 98.5,
                        "rate_limit_remaining": 8500,
                        "rate_limit_total": 10000,
                        "config_status": "configured",
                        "last_error": None
                    },
                    "salesforce": {
                        "status": "operational",
                        "last_check": (now - timedelta(minutes=1)).isoformat() + "Z",
                        "response_time_ms": 210,
                        "success_rate": 97.2,
                        "rate_limit_remaining": 4200,
                        "rate_limit_total": 5000,
                        "config_status": "configured",
                        "last_error": None
                    }
                }
            },
            "helpdesk": {
                "count": 2,
                "providers": ["zendesk", "intercom"],
                "classes": ["ZendeskProvider", "IntercomProvider"],
                "health": {
                    "zendesk": {
                        "status": "operational",
                        "last_check": (now - timedelta(minutes=3)).isoformat() + "Z",
                        "response_time_ms": 198,
                        "success_rate": 99.1,
                        "rate_limit_remaining": 680,
                        "rate_limit_total": 700,
                        "config_status": "configured",
                        "last_error": None
                    },
                    "intercom": {
                        "status": "degraded",
                        "last_check": (now - timedelta(minutes=1)).isoformat() + "Z",
                        "response_time_ms": 456,
                        "success_rate": 92.8,
                        "rate_limit_remaining": 150,
                        "rate_limit_total": 1000,
                        "config_status": "configured",
                        "last_error": "Rate limit approaching threshold"
                    }
                }
            },
            "calendar": {
                "count": 1,
                "providers": ["google_calendar"],
                "classes": ["GoogleCalendarProvider"],
                "health": {
                    "google_calendar": {
                        "status": "operational",
                        "last_check": (now - timedelta(minutes=1)).isoformat() + "Z",
                        "response_time_ms": 167,
                        "success_rate": 99.5,
                        "rate_limit_remaining": 9800,
                        "rate_limit_total": 10000,
                        "config_status": "configured",
                        "last_error": None
                    }
                }
            },
            "email": {
                "count": 1,
                "providers": ["gmail"],
                "classes": ["GmailProvider"],
                "health": {
                    "gmail": {
                        "status": "operational",
                        "last_check": (now - timedelta(minutes=2)).isoformat() + "Z",
                        "response_time_ms": 134,
                        "success_rate": 99.8,
                        "rate_limit_remaining": 24500,
                        "rate_limit_total": 25000,
                        "config_status": "configured",
                        "last_error": None
                    }
                }
            }
        }
    }

# Mock CRM endpoints
@app.post("/api/v1/crm/contacts")
async def create_contact(contact: Dict[str, Any]):
    """Create a contact (mock)."""
    return {
        "id": "mock_contact_123",
        "email": contact.get("email", ""),
        "first_name": contact.get("first_name", ""),
        "last_name": contact.get("last_name", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "provider": "mock_crm",
        "status": "success"
    }

@app.post("/api/v1/crm/contacts/search")
async def search_contacts(query: Dict[str, Any]):
    """Search contacts (mock)."""
    return {
        "results": [
            {
                "id": "mock_contact_1",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "company": "Acme Corp"
            }
        ],
        "total": 1,
        "query": query.get("query", ""),
        "provider": "mock_crm"
    }

# Mock Helpdesk endpoints
@app.post("/api/v1/helpdesk/tickets")
async def create_ticket(ticket: Dict[str, Any]):
    """Create a ticket (mock)."""
    return {
        "id": "mock_ticket_456",
        "subject": ticket.get("subject", ""),
        "description": ticket.get("description", ""),
        "status": "open",
        "priority": ticket.get("priority", "normal"),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "provider": "mock_helpdesk"
    }

@app.post("/api/v1/helpdesk/tickets/search")
async def search_tickets(query: Dict[str, Any]):
    """Search tickets (mock)."""
    return {
        "results": [
            {
                "id": "mock_ticket_1",
                "subject": "Sample Support Request",
                "status": "open",
                "priority": "normal",
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
        ],
        "total": 1,
        "query": query.get("query", ""),
        "provider": "mock_helpdesk"
    }

# Enhanced stats endpoint for frontend
@app.get("/api/v1/logs/stats")
async def get_stats():
    """Get enhanced action statistics with time-series data."""
    now = datetime.utcnow()
    
    # Generate hourly stats for last 24 hours
    hourly_stats = []
    for i in range(24):
        hour_time = now - timedelta(hours=23-i)
        hourly_stats.append({
            "timestamp": hour_time.isoformat() + "Z",
            "hour": hour_time.strftime("%H:00"),
            "total_actions": random.randint(15, 45),
            "successful": random.randint(13, 42),
            "failed": random.randint(0, 3),
            "avg_duration_ms": random.randint(120, 280)
        })
    
    return {
        "total_actions": 1247,
        "successful_actions": 1198,
        "failed_actions": 49,
        "success_rate": 96.1,
        "avg_duration_ms": 187.3,
        
        # Response time percentiles
        "response_time_percentiles": {
            "p50": 145,
            "p95": 312,
            "p99": 487
        },
        
        # Error rate trends
        "error_rate_trend": {
            "current": 3.9,
            "last_hour": 4.2,
            "last_24h": 3.7,
            "trend": "improving"
        },
        
        # Time-series data
        "hourly_stats": hourly_stats,
        
        # Enhanced provider breakdown
        "by_provider": {
            "hubspot": {
                "total": 387,
                "success": 378,
                "failed": 9,
                "success_rate": 97.7,
                "avg_duration_ms": 156,
                "p95_duration_ms": 298
            },
            "salesforce": {
                "total": 234,
                "success": 225,
                "failed": 9,
                "success_rate": 96.2,
                "avg_duration_ms": 223,
                "p95_duration_ms": 445
            },
            "zendesk": {
                "total": 312,
                "success": 303,
                "failed": 9,
                "success_rate": 97.1,
                "avg_duration_ms": 198,
                "p95_duration_ms": 356
            },
            "gmail": {
                "total": 189,
                "success": 182,
                "failed": 7,
                "success_rate": 96.3,
                "avg_duration_ms": 142,
                "p95_duration_ms": 267
            },
            "google_calendar": {
                "total": 125,
                "success": 110,
                "failed": 15,
                "success_rate": 88.0,
                "avg_duration_ms": 234,
                "p95_duration_ms": 512
            }
        },
        
        # Enhanced action type distribution
        "by_action_type": {
            "create_contact": {
                "count": 287,
                "success_rate": 97.2,
                "avg_duration_ms": 165
            },
            "search_contacts": {
                "count": 198,
                "success_rate": 98.5,
                "avg_duration_ms": 132
            },
            "update_contact": {
                "count": 156,
                "success_rate": 96.8,
                "avg_duration_ms": 178
            },
            "create_ticket": {
                "count": 213,
                "success_rate": 97.7,
                "avg_duration_ms": 201
            },
            "search_tickets": {
                "count": 167,
                "success_rate": 99.1,
                "avg_duration_ms": 145
            },
            "update_ticket": {
                "count": 89,
                "success_rate": 95.5,
                "avg_duration_ms": 189
            },
            "create_event": {
                "count": 78,
                "success_rate": 89.7,
                "avg_duration_ms": 245
            },
            "send_email": {
                "count": 59,
                "success_rate": 98.3,
                "avg_duration_ms": 134
            }
        }
    }

# New endpoint: Recent action logs
@app.get("/api/v1/logs/recent")
async def get_recent_logs():
    """Get recent action logs with detailed context."""
    now = datetime.utcnow()
    
    # Sample realistic business data
    companies = ["Acme Corp", "TechStart Inc", "Global Solutions Ltd", "DataFlow Systems", "CloudNine Co"]
    contacts = [
        ("Sarah", "Johnson", "sarah.johnson@acme.example"),
        ("Michael", "Chen", "m.chen@techstart.example"),
        ("Emily", "Rodriguez", "emily.r@global.example"),
        ("David", "Kim", "david.kim@dataflow.example"),
        ("Jessica", "Williams", "j.williams@cloudnine.example"),
        ("Robert", "Taylor", "r.taylor@acme.example"),
        ("Amanda", "Martinez", "amanda.m@techstart.example"),
        ("James", "Brown", "james.brown@global.example")
    ]
    
    action_types = [
        "create_contact", "search_contacts", "update_contact",
        "create_ticket", "search_tickets", "update_ticket",
        "create_event", "send_email"
    ]
    
    providers = ["hubspot", "salesforce", "zendesk", "gmail", "google_calendar"]
    statuses = ["success", "success", "success", "success", "success", "success", "failed"]
    agents = [
        "bdr-concierge", "support-concierge", "research-recon",
        "ops-sapper", "knowledge-librarian", "qa-auditor"
    ]
    
    logs = []
    for i in range(50):
        action = random.choice(action_types)
        status = random.choice(statuses)
        provider = random.choice(providers)
        contact = random.choice(contacts)
        company = random.choice(companies)
        agent = random.choice(agents)
        
        # Create realistic context based on action type
        if action == "create_contact":
            context = {
                "first_name": contact[0],
                "last_name": contact[1],
                "email": contact[2],
                "company": company,
                "source": "website_form",
                "lead_score": random.randint(45, 95)
            }
        elif action == "create_ticket":
            context = {
                "subject": f"Support Request: {random.choice(['Login Issue', 'API Integration', 'Data Export', 'Billing Question'])}",
                "priority": random.choice(["low", "normal", "high"]),
                "requester": contact[2],
                "tags": ["customer_support", random.choice(["technical", "billing", "account"])]
            }
        elif action == "send_email":
            context = {
                "to": contact[2],
                "subject": f"Re: {random.choice(['Your inquiry', 'Meeting follow-up', 'Account update'])}",
                "template": "standard_response"
            }
        else:
            context = {
                "query": random.choice(["email", "company", "recent"]),
                "filters": {"active": True}
            }
        
        log_entry = {
            "id": f"log_{1000 + i}",
            "timestamp": (now - timedelta(minutes=i*2, seconds=random.randint(0, 119))).isoformat() + "Z",
            "action_type": action,
            "status": status,
            "provider": provider,
            "agent": agent,
            "duration_ms": random.randint(78, 498) if status == "success" else random.randint(500, 2000),
            "context": context,
            "error_message": random.choice([
                "Rate limit exceeded",
                "Invalid authentication credentials",
                "Network timeout",
                "Provider service unavailable"
            ]) if status == "failed" else None
        }
        
        logs.append(log_entry)
    
    return {
        "total": 50,
        "logs": logs,
        "generated_at": now.isoformat() + "Z"
    }

# New endpoint: Action logs with filtering and pagination
@app.get("/api/v1/logs/actions")
async def get_action_logs(
    limit: int = 100,
    skip: int = 0,
    action_type: str = None,
    status: str = None,
    provider_name: str = None
):
    """Get action logs with optional filtering and pagination."""
    now = datetime.utcnow()
    
    # Sample realistic business data (same as recent logs)
    companies = ["Acme Corp", "TechStart Inc", "Global Solutions Ltd", "DataFlow Systems", "CloudNine Co"]
    contacts = [
        ("Sarah", "Johnson", "sarah.johnson@acme.example"),
        ("Michael", "Chen", "m.chen@techstart.example"),
        ("Emily", "Rodriguez", "emily.r@global.example"),
        ("David", "Kim", "david.kim@dataflow.example"),
        ("Jessica", "Williams", "j.williams@cloudnine.example"),
        ("Robert", "Taylor", "r.taylor@acme.example"),
        ("Amanda", "Martinez", "amanda.m@techstart.example"),
        ("James", "Brown", "james.brown@global.example")
    ]
    
    action_types = [
        "create_contact", "search_contacts", "update_contact",
        "create_ticket", "search_tickets", "update_ticket",
        "create_event", "send_email"
    ]
    
    providers = ["hubspot", "salesforce", "zendesk", "gmail", "google_calendar"]
    statuses = ["success", "success", "success", "success", "success", "success", "failed"]
    agents = [
        "bdr-concierge", "support-concierge", "research-recon",
        "ops-sapper", "knowledge-librarian", "qa-auditor"
    ]
    
    # Generate all logs first (200 entries for better filtering demonstration)
    all_logs = []
    for i in range(200):
        action = random.choice(action_types)
        log_status = random.choice(statuses)
        provider = random.choice(providers)
        contact = random.choice(contacts)
        company = random.choice(companies)
        agent = random.choice(agents)
        
        # Create realistic context based on action type
        if action == "create_contact":
            context = {
                "first_name": contact[0],
                "last_name": contact[1],
                "email": contact[2],
                "company": company,
                "source": "website_form",
                "lead_score": random.randint(45, 95)
            }
        elif action == "create_ticket":
            context = {
                "subject": f"Support Request: {random.choice(['Login Issue', 'API Integration', 'Data Export', 'Billing Question'])}",
                "priority": random.choice(["low", "normal", "high"]),
                "requester": contact[2],
                "tags": ["customer_support", random.choice(["technical", "billing", "account"])]
            }
        elif action == "send_email":
            context = {
                "to": contact[2],
                "subject": f"Re: {random.choice(['Your inquiry', 'Meeting follow-up', 'Account update'])}",
                "template": "standard_response"
            }
        else:
            context = {
                "query": random.choice(["email", "company", "recent"]),
                "filters": {"active": True}
            }
        
        log_entry = {
            "id": f"log_{2000 + i}",
            "timestamp": (now - timedelta(minutes=i*2, seconds=random.randint(0, 119))).isoformat() + "Z",
            "action_type": action,
            "status": log_status,
            "provider": provider,
            "agent": agent,
            "duration_ms": random.randint(78, 498) if log_status == "success" else random.randint(500, 2000),
            "context": context,
            "error_message": random.choice([
                "Rate limit exceeded",
                "Invalid authentication credentials",
                "Network timeout",
                "Provider service unavailable"
            ]) if log_status == "failed" else None
        }
        
        all_logs.append(log_entry)
    
    # Apply filters
    filtered_logs = all_logs
    
    if action_type:
        filtered_logs = [log for log in filtered_logs if log["action_type"] == action_type]
    
    if status:
        filtered_logs = [log for log in filtered_logs if log["status"] == status]
    
    if provider_name:
        filtered_logs = [log for log in filtered_logs if log["provider"] == provider_name]
    
    # Get total count after filtering
    total_filtered = len(filtered_logs)
    
    # Apply pagination
    paginated_logs = filtered_logs[skip:skip + limit]
    
    return {
        "total": total_filtered,
        "limit": limit,
        "skip": skip,
        "returned": len(paginated_logs),
        "filters": {
            "action_type": action_type,
            "status": status,
            "provider_name": provider_name
        },
        "logs": paginated_logs,
        "generated_at": now.isoformat() + "Z"
    }


# Agents endpoint - Transform Army AI military-themed agents
@app.get("/api/v1/agents")
async def get_agents():
    """Get list of all 6 AI agents with Transform Army AI military profiles."""
    print("[DEBUG] /api/v1/agents endpoint called - returning 6 agents")
    now = datetime.utcnow()
    
    return {
        "total": 6,
        "agents": [
            {
                "id": "agent_bdr_concierge",
                "call_sign": "ALPHA-1",
                "nickname": "Hunter",
                "rank": "SSG",
                "name": "BDR Concierge",
                "role": "Business Development Representative Support",
                "mos": "18F",
                "specialty": "Special Forces",
                "status": "ACTIVE",
                "squad": "Alpha",
                "squad_color": "#00ff41",
                "missions_completed": 523,
                "success_rate": 96.8,
                "avg_response_time_ms": 145,
                "last_activity": (now - timedelta(minutes=3)).isoformat() + "Z",
                "tools": ["crm_tools", "email_tools", "calendar_tools"],
                "model": "gpt-4-turbo",
                "cost_budget": "$50/day"
            },
            {
                "id": "agent_support_concierge",
                "call_sign": "ALPHA-2",
                "nickname": "Medic",
                "rank": "SGT",
                "name": "Support Concierge",
                "role": "Customer Support Specialist",
                "mos": "68W",
                "specialty": "Combat Medic",
                "status": "ACTIVE",
                "squad": "Alpha",
                "squad_color": "#00ff41",
                "missions_completed": 612,
                "success_rate": 97.3,
                "avg_response_time_ms": 132,
                "last_activity": (now - timedelta(minutes=1)).isoformat() + "Z",
                "tools": ["helpdesk_tools", "knowledge_tools"],
                "model": "gpt-4-turbo",
                "cost_budget": "$45/day"
            },
            {
                "id": "agent_research_recon",
                "call_sign": "BRAVO-1",
                "nickname": "Scout",
                "rank": "SFC",
                "name": "Research Recon",
                "role": "Market Intelligence & Research",
                "mos": "19D",
                "specialty": "Cavalry Scout",
                "status": "STANDBY",
                "squad": "Bravo",
                "squad_color": "#c5a641",
                "missions_completed": 447,
                "success_rate": 94.2,
                "avg_response_time_ms": 178,
                "last_activity": (now - timedelta(minutes=15)).isoformat() + "Z",
                "tools": ["research_tools", "web_scraping"],
                "model": "gpt-4-turbo",
                "cost_budget": "$40/day"
            },
            {
                "id": "agent_ops_sapper",
                "call_sign": "BRAVO-2",
                "nickname": "Engineer",
                "rank": "SSG",
                "name": "Ops Sapper",
                "role": "Operations & Infrastructure",
                "mos": "12B",
                "specialty": "Combat Engineer",
                "status": "ACTIVE",
                "squad": "Bravo",
                "squad_color": "#c5a641",
                "missions_completed": 589,
                "success_rate": 98.1,
                "avg_response_time_ms": 121,
                "last_activity": (now - timedelta(minutes=2)).isoformat() + "Z",
                "tools": ["monitoring_tools", "automation_tools"],
                "model": "gpt-4-turbo",
                "cost_budget": "$55/day"
            },
            {
                "id": "agent_knowledge_librarian",
                "call_sign": "CHARLIE-1",
                "nickname": "Intel",
                "rank": "MSG",
                "name": "Knowledge Librarian",
                "role": "Knowledge Management & Documentation",
                "mos": "35L",
                "specialty": "Counterintelligence",
                "status": "TRAINING",
                "squad": "Charlie",
                "squad_color": "#3b82f6",
                "missions_completed": 401,
                "success_rate": 95.7,
                "avg_response_time_ms": 156,
                "last_activity": (now - timedelta(hours=2)).isoformat() + "Z",
                "tools": ["knowledge_tools", "document_processing"],
                "model": "gpt-4-turbo",
                "cost_budget": "$35/day"
            },
            {
                "id": "agent_qa_auditor",
                "call_sign": "CHARLIE-2",
                "nickname": "Guardian",
                "rank": "SFC",
                "name": "QA Auditor",
                "role": "Quality Assurance & Oversight",
                "mos": "35M",
                "specialty": "Human Intel",
                "status": "ACTIVE",
                "squad": "Charlie",
                "squad_color": "#3b82f6",
                "missions_completed": 534,
                "success_rate": 97.8,
                "avg_response_time_ms": 143,
                "last_activity": (now - timedelta(minutes=5)).isoformat() + "Z",
                "tools": ["audit_tools", "quality_tools", "reporting_tools"],
                "model": "gpt-4-turbo",
                "cost_budget": "$42/day"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    # Load default agent configurations on startup
    print("=" * 60)
    print("Transform Army AI Adapter - Configuration Manager")
    print("=" * 60)
    load_default_agent_configs()
    print("=" * 60)
    
    print("Starting Transform Army AI Adapter (Simplified Mode)")
    print("=" * 60)
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("Health: http://localhost:8000/health")
    print("Config API: http://localhost:8000/api/v1/agents/{agent_id}/config")
    print("Mode: Standalone (no database required)")
    print("=" * 60)
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
