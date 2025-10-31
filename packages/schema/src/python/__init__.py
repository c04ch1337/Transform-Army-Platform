"""
Transform Army AI Schema Package.

This package provides Pydantic models for all data structures used in the
Transform Army AI platform, including base models, CRM, helpdesk, calendar,
email, knowledge, and agent schemas.
"""

# Base models and enums
from .base import (
    ActionEnvelope,
    ActionMetadata,
    ActionStatus,
    ErrorCode,
    ErrorDetails,
    ErrorResponse,
    HealthCheckResponse,
    PaginationParams,
    PaginationResponse,
    Priority,
    ProviderCredentials,
    TicketStatus,
    ToolInput,
    ToolResult,
)

# CRM models
from .crm import (
    AddNoteRequest,
    Company,
    Contact,
    ContactSearchMatch,
    CreateContactRequest,
    CreateDealRequest,
    Deal,
    Note,
    SearchContactsRequest,
    SearchContactsResponse,
    UpdateContactRequest,
    UpdateDealRequest,
)

# Helpdesk models
from .helpdesk import (
    AddCommentRequest,
    CommentAuthor,
    CreateTicketRequest,
    SearchTicketsRequest,
    SearchTicketsResponse,
    Ticket,
    TicketComment,
    TicketMetrics,
    TicketRequester,
    TicketSearchMatch,
    UpdateTicketRequest,
)

# Calendar models
from .calendar import (
    Attendee,
    AvailableSlot,
    CalendarEvent,
    CheckAvailabilityRequest,
    CheckAvailabilityResponse,
    CreateEventRequest,
    EventLocation,
    EventReminder,
    ListEventsRequest,
    ListEventsResponse,
    UpdateEventRequest,
    WorkingHours,
)

# Email models
from .email import (
    Attachment,
    Email,
    EmailAddress,
    EmailBody,
    EmailSearchMatch,
    EmailThread,
    SearchEmailsRequest,
    SearchEmailsResponse,
    SendEmailRequest,
    SendEmailResponse,
)

# Knowledge models
from .knowledge import (
    Document,
    DocumentAnalytics,
    DocumentMetadata,
    IndexDocumentRequest,
    ListDocumentsRequest,
    ListDocumentsResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)

# Agent models
from .agent import (
    AgentCapability,
    AgentConfig,
    AgentMessage,
    AgentPerformanceMetrics,
    AgentRole,
    AgentState,
    AgentStatus,
    MessageRole,
    Workflow,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepConfig,
)

__all__ = [
    # Base
    "ActionEnvelope",
    "ActionMetadata",
    "ActionStatus",
    "ErrorCode",
    "ErrorDetails",
    "ErrorResponse",
    "HealthCheckResponse",
    "PaginationParams",
    "PaginationResponse",
    "Priority",
    "ProviderCredentials",
    "TicketStatus",
    "ToolInput",
    "ToolResult",
    # CRM
    "AddNoteRequest",
    "Company",
    "Contact",
    "ContactSearchMatch",
    "CreateContactRequest",
    "CreateDealRequest",
    "Deal",
    "Note",
    "SearchContactsRequest",
    "SearchContactsResponse",
    "UpdateContactRequest",
    "UpdateDealRequest",
    # Helpdesk
    "AddCommentRequest",
    "CommentAuthor",
    "CreateTicketRequest",
    "SearchTicketsRequest",
    "SearchTicketsResponse",
    "Ticket",
    "TicketComment",
    "TicketMetrics",
    "TicketRequester",
    "TicketSearchMatch",
    "UpdateTicketRequest",
    # Calendar
    "Attendee",
    "AvailableSlot",
    "CalendarEvent",
    "CheckAvailabilityRequest",
    "CheckAvailabilityResponse",
    "CreateEventRequest",
    "EventLocation",
    "EventReminder",
    "ListEventsRequest",
    "ListEventsResponse",
    "UpdateEventRequest",
    "WorkingHours",
    # Email
    "Attachment",
    "Email",
    "EmailAddress",
    "EmailBody",
    "EmailSearchMatch",
    "EmailThread",
    "SearchEmailsRequest",
    "SearchEmailsResponse",
    "SendEmailRequest",
    "SendEmailResponse",
    # Knowledge
    "Document",
    "DocumentAnalytics",
    "DocumentMetadata",
    "IndexDocumentRequest",
    "ListDocumentsRequest",
    "ListDocumentsResponse",
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    # Agent
    "AgentCapability",
    "AgentConfig",
    "AgentMessage",
    "AgentPerformanceMetrics",
    "AgentRole",
    "AgentState",
    "AgentStatus",
    "MessageRole",
    "Workflow",
    "WorkflowStatus",
    "WorkflowStep",
    "WorkflowStepConfig",
]

__version__ = "1.0.0"