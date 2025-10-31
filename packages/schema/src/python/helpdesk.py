"""
Helpdesk schema models for Transform Army AI Adapter Service.

This module defines Pydantic models for helpdesk operations including tickets,
comments, and related functionality across different helpdesk providers
(Zendesk, Freshdesk, etc.).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr, HttpUrl, ConfigDict

from .base import ToolInput, PaginationParams, PaginationResponse, Priority, TicketStatus


class TicketRequester(BaseModel):
    """Information about the person requesting support."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "support-request@example.com",
                "name": "Jane Smith",
                "phone": "+1-555-0123"
            }
        }
    )
    
    email: EmailStr = Field(description="Requester email address")
    name: Optional[str] = Field(
        default=None,
        description="Requester name"
    )
    phone: Optional[str] = Field(
        default=None,
        description="Requester phone number"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID in the system"
    )


class Ticket(BaseModel):
    """
    Helpdesk ticket model.
    
    Represents a support ticket across different helpdesk providers.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "tick_789",
                "ticket_number": "ZD-12345",
                "subject": "Unable to login to dashboard",
                "description": "User reports seeing 'Invalid credentials' error.",
                "status": "open",
                "priority": "high",
                "requester": {
                    "email": "support-request@example.com",
                    "name": "Jane Smith"
                },
                "assignee_id": "agent_001",
                "tags": ["login", "authentication", "urgent"],
                "url": "https://support.example.com/tickets/12345",
                "created_at": "2025-10-31T01:17:00Z"
            }
        }
    )
    
    id: str = Field(description="Unique ticket identifier")
    ticket_number: Optional[str] = Field(
        default=None,
        description="Human-readable ticket number"
    )
    subject: str = Field(description="Ticket subject/title")
    description: str = Field(description="Ticket description/body")
    status: TicketStatus = Field(description="Ticket status")
    priority: Optional[Priority] = Field(
        default=None,
        description="Ticket priority"
    )
    requester: TicketRequester = Field(description="Person requesting support")
    assignee_id: Optional[str] = Field(
        default=None,
        description="ID of assigned agent"
    )
    assignee_name: Optional[str] = Field(
        default=None,
        description="Name of assigned agent"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags associated with the ticket"
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to view ticket in provider system"
    )
    created_at: datetime = Field(description="Ticket creation timestamp")
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="Resolution timestamp"
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Provider-specific custom fields"
    )
    due_date: Optional[datetime] = Field(
        default=None,
        description="Ticket due date"
    )
    group_id: Optional[str] = Field(
        default=None,
        description="Support group/team ID"
    )


class CommentAuthor(BaseModel):
    """Author of a ticket comment."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "agent",
                "id": "agent_support_001",
                "name": "Support Agent",
                "email": "agent@example.com"
            }
        }
    )
    
    type: str = Field(
        description="Author type (e.g., 'agent', 'customer', 'system')"
    )
    id: str = Field(description="Author identifier")
    name: Optional[str] = Field(
        default=None,
        description="Author name"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Author email"
    )


class TicketComment(BaseModel):
    """
    Comment/reply on a helpdesk ticket.
    
    Represents communication on a support ticket.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "comment_456",
                "ticket_id": "tick_789",
                "body": "I've reviewed the logs and identified the issue.",
                "is_public": False,
                "author": {
                    "type": "agent",
                    "id": "agent_support_001",
                    "name": "Support Agent"
                },
                "created_at": "2025-10-31T01:20:00Z"
            }
        }
    )
    
    id: str = Field(description="Unique comment identifier")
    ticket_id: str = Field(description="Associated ticket ID")
    body: str = Field(description="Comment body/content")
    is_public: bool = Field(
        default=True,
        description="Whether comment is visible to requester"
    )
    author: CommentAuthor = Field(description="Comment author")
    created_at: datetime = Field(description="Comment creation timestamp")
    attachments: Optional[List[str]] = Field(
        default=None,
        description="URLs of attached files"
    )


class CreateTicketRequest(ToolInput):
    """
    Request to create a new helpdesk ticket.
    
    Includes options for notifications and automatic assignment.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_ticket123",
                "correlation_id": "cor_req127",
                "ticket": {
                    "subject": "Unable to login to dashboard",
                    "description": "User reports seeing 'Invalid credentials' error.",
                    "requester": {
                        "email": "support-request@example.com",
                        "name": "Jane Smith"
                    },
                    "priority": "high",
                    "tags": ["login", "authentication", "urgent"]
                },
                "options": {
                    "send_notification": True,
                    "auto_assign": True
                }
            }
        }
    )
    
    class TicketData(BaseModel):
        """Ticket data for creation."""
        subject: str = Field(description="Ticket subject")
        description: str = Field(description="Ticket description")
        requester: TicketRequester = Field(description="Person requesting support")
        priority: Optional[Priority] = Field(
            default=None,
            description="Ticket priority"
        )
        status: Optional[TicketStatus] = Field(
            default=TicketStatus.NEW,
            description="Initial ticket status"
        )
        tags: Optional[List[str]] = Field(
            default=None,
            description="Tags to apply"
        )
        assignee_id: Optional[str] = Field(
            default=None,
            description="Assign to specific agent"
        )
        group_id: Optional[str] = Field(
            default=None,
            description="Assign to specific group"
        )
        custom_fields: Optional[Dict[str, Any]] = Field(
            default=None,
            description="Custom fields"
        )
        due_date: Optional[datetime] = Field(
            default=None,
            description="Ticket due date"
        )
    
    class TicketOptions(BaseModel):
        """Options for ticket creation."""
        send_notification: bool = Field(
            default=True,
            description="Send notification to requester"
        )
        auto_assign: bool = Field(
            default=False,
            description="Automatically assign to available agent"
        )
    
    ticket: TicketData = Field(description="Ticket data to create")
    options: Optional[TicketOptions] = Field(
        default=None,
        description="Creation options"
    )


class UpdateTicketRequest(ToolInput):
    """Request to update an existing helpdesk ticket."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_update789",
                "correlation_id": "cor_req129",
                "updates": {
                    "status": "solved",
                    "resolution": "Password reset link sent to user",
                    "tags": ["resolved", "password-reset"]
                }
            }
        }
    )
    
    updates: Dict[str, Any] = Field(
        description="Fields to update (partial update)"
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Resolution notes when closing ticket"
    )


class AddCommentRequest(ToolInput):
    """Request to add a comment to a ticket."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_comment456",
                "correlation_id": "cor_req128",
                "comment": {
                    "body": "I've reviewed the logs and identified the issue.",
                    "is_public": False,
                    "author": {
                        "type": "agent",
                        "id": "agent_support_001"
                    }
                }
            }
        }
    )
    
    class CommentData(BaseModel):
        """Comment data for creation."""
        body: str = Field(description="Comment body/content")
        is_public: bool = Field(
            default=True,
            description="Whether comment is visible to requester"
        )
        author: CommentAuthor = Field(description="Comment author")
        attachments: Optional[List[str]] = Field(
            default=None,
            description="URLs or base64-encoded file content"
        )
    
    comment: CommentData = Field(description="Comment data to add")


class SearchTicketsRequest(BaseModel):
    """Request to search for helpdesk tickets."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": ["open", "pending"],
                "priority": ["high", "urgent"],
                "assignee": "agent_001",
                "requester_email": "support-request@example.com",
                "tags": ["login", "authentication"],
                "created_after": "2025-10-30T00:00:00Z",
                "created_before": "2025-10-31T23:59:59Z",
                "query": "login error",
                "pagination": {
                    "page": 1,
                    "page_size": 50
                }
            }
        }
    )
    
    status: Optional[List[TicketStatus]] = Field(
        default=None,
        description="Filter by ticket status"
    )
    priority: Optional[List[Priority]] = Field(
        default=None,
        description="Filter by priority"
    )
    assignee: Optional[str] = Field(
        default=None,
        description="Filter by assignee ID"
    )
    requester_email: Optional[EmailStr] = Field(
        default=None,
        description="Filter by requester email"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags (any match)"
    )
    created_after: Optional[datetime] = Field(
        default=None,
        description="Filter tickets created after this timestamp"
    )
    created_before: Optional[datetime] = Field(
        default=None,
        description="Filter tickets created before this timestamp"
    )
    query: Optional[str] = Field(
        default=None,
        description="Full-text search query"
    )
    group_id: Optional[str] = Field(
        default=None,
        description="Filter by support group"
    )
    pagination: Optional[PaginationParams] = Field(
        default=None,
        description="Pagination parameters"
    )


class TicketSearchMatch(BaseModel):
    """A single ticket search result."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "tick_789",
                "ticket_number": "ZD-12345",
                "subject": "Unable to login to dashboard",
                "status": "open",
                "priority": "high",
                "requester_email": "support-request@example.com",
                "created_at": "2025-10-31T01:17:00Z",
                "url": "https://support.example.com/tickets/12345"
            }
        }
    )
    
    id: str = Field(description="Ticket ID")
    ticket_number: Optional[str] = Field(
        default=None,
        description="Ticket number"
    )
    subject: str = Field(description="Ticket subject")
    status: TicketStatus = Field(description="Ticket status")
    priority: Optional[Priority] = Field(
        default=None,
        description="Ticket priority"
    )
    requester_email: EmailStr = Field(description="Requester email")
    requester_name: Optional[str] = Field(
        default=None,
        description="Requester name"
    )
    assignee_id: Optional[str] = Field(
        default=None,
        description="Assignee ID"
    )
    assignee_name: Optional[str] = Field(
        default=None,
        description="Assignee name"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Ticket tags"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to view in provider system"
    )


class SearchTicketsResponse(BaseModel):
    """Response from ticket search operation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "matches": [
                    {
                        "id": "tick_789",
                        "ticket_number": "ZD-12345",
                        "subject": "Unable to login to dashboard",
                        "status": "open",
                        "priority": "high",
                        "requester_email": "support-request@example.com",
                        "created_at": "2025-10-31T01:17:00Z"
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 50,
                    "total_pages": 1,
                    "total_items": 1,
                    "has_next": False,
                    "has_previous": False
                }
            }
        }
    )
    
    matches: List[TicketSearchMatch] = Field(description="Search results")
    pagination: Optional[PaginationResponse] = Field(
        default=None,
        description="Pagination metadata"
    )


class TicketMetrics(BaseModel):
    """Metrics and statistics for tickets."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_tickets": 1247,
                "open_tickets": 156,
                "pending_tickets": 42,
                "solved_tickets": 1049,
                "average_resolution_time_hours": 18.5,
                "first_response_time_hours": 2.3
            }
        }
    )
    
    total_tickets: int = Field(description="Total number of tickets")
    open_tickets: int = Field(description="Number of open tickets")
    pending_tickets: int = Field(description="Number of pending tickets")
    solved_tickets: int = Field(description="Number of solved tickets")
    average_resolution_time_hours: Optional[float] = Field(
        default=None,
        description="Average time to resolve tickets (hours)"
    )
    first_response_time_hours: Optional[float] = Field(
        default=None,
        description="Average time to first response (hours)"
    )