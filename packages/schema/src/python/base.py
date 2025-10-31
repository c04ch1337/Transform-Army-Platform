"""
Base schema models for Transform Army AI Adapter Service.

This module defines the foundational Pydantic models that are used across
all adapter operations, including action envelopes, error responses, and
common data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic import EmailStr


class ActionStatus(str, Enum):
    """Status of an action execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    QUEUED = "queued"


class ErrorCode(str, Enum):
    """Standard error codes for adapter operations."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class Priority(str, Enum):
    """Priority levels for tasks, tickets, etc."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, Enum):
    """Status values for helpdesk tickets."""
    OPEN = "open"
    PENDING = "pending"
    SOLVED = "solved"
    CLOSED = "closed"
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"


class PaginationParams(BaseModel):
    """Parameters for paginating list results."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 50,
                "cursor": None
            }
        }
    )
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed)"
    )
    page_size: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of items per page (max 100)"
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Opaque cursor for cursor-based pagination"
    )


class PaginationResponse(BaseModel):
    """Pagination metadata in response."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 50,
                "total_pages": 10,
                "total_items": 487,
                "has_next": True,
                "has_previous": False,
                "next_cursor": "eyJwYWdlIjoyfQ=="
            }
        }
    )
    
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    total_items: int = Field(description="Total number of items")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")
    next_cursor: Optional[str] = Field(
        default=None,
        description="Cursor for next page"
    )


class ErrorDetails(BaseModel):
    """Additional details about an error."""
    
    model_config = ConfigDict(extra="allow")
    
    field: Optional[str] = Field(
        default=None,
        description="Field that caused the error"
    )
    issue: Optional[str] = Field(
        default=None,
        description="Description of the issue"
    )
    value: Optional[Any] = Field(
        default=None,
        description="Invalid value that caused the error"
    )
    provider: Optional[str] = Field(
        default=None,
        description="Provider that reported the error"
    )
    provider_error: Optional[str] = Field(
        default=None,
        description="Original error message from provider"
    )


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": {
                    "field": "email",
                    "issue": "Invalid email format",
                    "value": "not-an-email"
                },
                "correlation_id": "cor_req136",
                "timestamp": "2025-10-31T01:17:00Z",
                "documentation_url": "https://docs.transform-army.ai/errors/VALIDATION_ERROR"
            }
        }
    )
    
    code: ErrorCode = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    details: Optional[ErrorDetails] = Field(
        default=None,
        description="Additional error details"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for request tracing"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
    retry_after: Optional[int] = Field(
        default=None,
        description="Seconds to wait before retrying (for rate limits)"
    )
    documentation_url: Optional[str] = Field(
        default=None,
        description="URL to error documentation"
    )


class ActionMetadata(BaseModel):
    """Metadata about action execution."""
    
    model_config = ConfigDict(extra="allow")
    
    idempotency_key: Optional[str] = Field(
        default=None,
        description="Idempotency key for safe retries"
    )
    retry_count: int = Field(
        default=0,
        description="Number of retries attempted"
    )
    provider_request_id: Optional[str] = Field(
        default=None,
        description="Request ID from provider API"
    )


# Generic type variable for result data
TResult = TypeVar('TResult')


class ToolResult(BaseModel, Generic[TResult]):
    """Generic structure for tool/action results."""
    
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(description="Resource ID")
    provider: str = Field(description="Provider name (e.g., 'hubspot', 'zendesk')")
    provider_id: str = Field(description="ID in provider's system")
    data: TResult = Field(description="Result data specific to the operation")


class ActionEnvelope(BaseModel, Generic[TResult]):
    """
    Standardized envelope for all adapter operations.
    
    This wraps every request/response to provide consistent structure,
    tracing, and metadata across all operations.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action_id": "act_abc123xyz789",
                "correlation_id": "cor_req123",
                "tenant_id": "tenant_001",
                "timestamp": "2025-10-31T01:17:00Z",
                "operation": "crm.contact.create",
                "status": "success",
                "duration_ms": 245,
                "result": {
                    "id": "cont_12345",
                    "provider": "hubspot",
                    "provider_id": "12345",
                    "data": {}
                },
                "metadata": {
                    "idempotency_key": "idm_unique123",
                    "retry_count": 0
                }
            }
        }
    )
    
    action_id: str = Field(
        description="Unique identifier for this action"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for distributed tracing"
    )
    tenant_id: str = Field(
        description="Tenant identifier"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Action execution timestamp"
    )
    operation: str = Field(
        description="Operation name (e.g., 'crm.contact.create')"
    )
    status: ActionStatus = Field(
        description="Action execution status"
    )
    duration_ms: Optional[int] = Field(
        default=None,
        description="Execution duration in milliseconds"
    )
    result: Optional[TResult] = Field(
        default=None,
        description="Operation result data"
    )
    error: Optional[ErrorResponse] = Field(
        default=None,
        description="Error details if status is 'failure'"
    )
    metadata: Optional[ActionMetadata] = Field(
        default=None,
        description="Additional metadata about the action"
    )
    
    @field_validator('duration_ms')
    @classmethod
    def validate_duration(cls, v: Optional[int]) -> Optional[int]:
        """Ensure duration is non-negative."""
        if v is not None and v < 0:
            raise ValueError("duration_ms must be non-negative")
        return v


class ToolInput(BaseModel):
    """Generic structure for tool/action input."""
    
    model_config = ConfigDict(extra="allow")
    
    idempotency_key: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Idempotency key for safe retries (valid for 24 hours)"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for request tracing"
    )
    
    @field_validator('idempotency_key')
    @classmethod
    def validate_idempotency_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate idempotency key format."""
        if v is not None and len(v) > 255:
            raise ValueError("idempotency_key must be 255 characters or less")
        return v


class ProviderCredentials(BaseModel):
    """Provider-specific credentials."""
    
    model_config = ConfigDict(extra="allow")
    
    provider_name: str = Field(
        description="Name of the provider (e.g., 'hubspot', 'zendesk')"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication"
    )
    api_secret: Optional[str] = Field(
        default=None,
        description="API secret for authentication"
    )
    access_token: Optional[str] = Field(
        default=None,
        description="OAuth access token"
    )
    refresh_token: Optional[str] = Field(
        default=None,
        description="OAuth refresh token"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Token expiration timestamp"
    )


class HealthCheckResponse(BaseModel):
    """Health check response format."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-31T01:17:00Z",
                "version": "1.0.0",
                "providers": {
                    "hubspot": "healthy",
                    "zendesk": "healthy"
                }
            }
        }
    )
    
    status: str = Field(description="Overall health status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    version: str = Field(description="API version")
    providers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Health status of individual providers"
    )