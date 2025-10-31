"""
Email schema models for Transform Army AI Adapter Service.

This module defines Pydantic models for email operations including sending emails,
managing attachments, and searching email threads across different email providers
(Gmail, Outlook, etc.).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr, HttpUrl, ConfigDict, field_validator
import base64

from .base import ToolInput, PaginationParams, PaginationResponse


class EmailAddress(BaseModel):
    """
    Email address with optional name.
    
    Used for from, to, cc, and bcc fields.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "name": "John Doe"
            }
        }
    )
    
    email: EmailStr = Field(description="Email address")
    name: Optional[str] = Field(
        default=None,
        description="Display name"
    )


class EmailBody(BaseModel):
    """Email body content in text and HTML formats."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Hi John, Your demo has been scheduled.",
                "html": "<p>Hi John,</p><p>Your demo has been scheduled.</p>"
            }
        }
    )
    
    text: str = Field(description="Plain text version of email body")
    html: Optional[str] = Field(
        default=None,
        description="HTML version of email body"
    )


class Attachment(BaseModel):
    """
    Email attachment model.
    
    Supports both URL-based and base64-encoded content.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "agenda.pdf",
                "content_type": "application/pdf",
                "size_bytes": 245678,
                "content": "base64_encoded_content",
                "attachment_id": "att_123"
            }
        }
    )
    
    filename: str = Field(description="Attachment filename")
    content_type: str = Field(
        description="MIME type (e.g., 'application/pdf', 'image/png')"
    )
    size_bytes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Attachment size in bytes"
    )
    content: Optional[str] = Field(
        default=None,
        description="Base64-encoded content or URL to content"
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to download attachment"
    )
    attachment_id: Optional[str] = Field(
        default=None,
        description="Provider-specific attachment ID"
    )
    
    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate MIME type format."""
        if '/' not in v:
            raise ValueError("content_type must be a valid MIME type (e.g., 'application/pdf')")
        return v


class Email(BaseModel):
    """
    Email message model.
    
    Represents an email message across different email providers.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "msg_abc123",
                "thread_id": "thread_789",
                "from": {
                    "email": "sender@example.com",
                    "name": "Sender Name"
                },
                "to": [
                    {
                        "email": "recipient@example.com",
                        "name": "Recipient Name"
                    }
                ],
                "subject": "Your Demo is Scheduled",
                "body": {
                    "text": "Hi, Your demo has been scheduled.",
                    "html": "<p>Hi,</p><p>Your demo has been scheduled.</p>"
                },
                "date": "2025-10-31T01:17:00Z",
                "snippet": "Hi, Your demo has been scheduled...",
                "labels": ["INBOX", "IMPORTANT"]
            }
        }
    )
    
    id: str = Field(description="Unique message identifier")
    thread_id: Optional[str] = Field(
        default=None,
        description="Thread identifier"
    )
    from_: EmailAddress = Field(
        alias="from",
        description="Sender email address"
    )
    to: List[EmailAddress] = Field(description="Recipient email addresses")
    cc: Optional[List[EmailAddress]] = Field(
        default=None,
        description="CC recipients"
    )
    bcc: Optional[List[EmailAddress]] = Field(
        default=None,
        description="BCC recipients"
    )
    reply_to: Optional[EmailAddress] = Field(
        default=None,
        description="Reply-to address"
    )
    subject: str = Field(description="Email subject")
    body: EmailBody = Field(description="Email body content")
    date: datetime = Field(description="Email date/time")
    snippet: Optional[str] = Field(
        default=None,
        description="Short preview of email content"
    )
    attachments: Optional[List[Attachment]] = Field(
        default=None,
        description="Email attachments"
    )
    labels: Optional[List[str]] = Field(
        default=None,
        description="Labels/folders (e.g., 'INBOX', 'SENT', 'IMPORTANT')"
    )
    is_read: bool = Field(
        default=False,
        description="Whether email has been read"
    )
    is_starred: bool = Field(
        default=False,
        description="Whether email is starred/flagged"
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Custom email headers"
    )
    provider_id: Optional[str] = Field(
        default=None,
        description="Provider-specific message ID"
    )


class SendEmailRequest(ToolInput):
    """
    Request to send an email.
    
    Includes options for tracking and scheduled delivery.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_email123",
                "correlation_id": "cor_req132",
                "email": {
                    "from": {
                        "email": "noreply@transform-army.ai",
                        "name": "Transform Army AI"
                    },
                    "to": [
                        {
                            "email": "john.doe@example.com",
                            "name": "John Doe"
                        }
                    ],
                    "subject": "Your Demo is Scheduled",
                    "body": {
                        "text": "Hi John, Your demo has been scheduled.",
                        "html": "<p>Hi John,</p><p>Your demo has been scheduled.</p>"
                    }
                },
                "options": {
                    "track_opens": True,
                    "track_clicks": True
                }
            }
        }
    )
    
    class EmailData(BaseModel):
        """Email data for sending."""
        from_: EmailAddress = Field(
            alias="from",
            description="Sender email address"
        )
        to: List[EmailAddress] = Field(
            description="Recipient email addresses"
        )
        cc: Optional[List[EmailAddress]] = Field(
            default=None,
            description="CC recipients"
        )
        bcc: Optional[List[EmailAddress]] = Field(
            default=None,
            description="BCC recipients"
        )
        reply_to: Optional[EmailAddress] = Field(
            default=None,
            description="Reply-to address"
        )
        subject: str = Field(description="Email subject")
        body: EmailBody = Field(description="Email body")
        attachments: Optional[List[Attachment]] = Field(
            default=None,
            description="Email attachments"
        )
        headers: Optional[Dict[str, str]] = Field(
            default=None,
            description="Custom email headers"
        )
        
        @field_validator('to')
        @classmethod
        def validate_recipients(cls, v: List[EmailAddress]) -> List[EmailAddress]:
            """Ensure at least one recipient."""
            if not v or len(v) == 0:
                raise ValueError("At least one recipient is required")
            return v
    
    class EmailOptions(BaseModel):
        """Options for sending email."""
        track_opens: bool = Field(
            default=False,
            description="Track when email is opened"
        )
        track_clicks: bool = Field(
            default=False,
            description="Track link clicks in email"
        )
        send_at: Optional[datetime] = Field(
            default=None,
            description="Schedule email for future delivery"
        )
        priority: Optional[str] = Field(
            default=None,
            description="Email priority (e.g., 'high', 'normal', 'low')"
        )
    
    email: EmailData = Field(description="Email data to send")
    options: Optional[EmailOptions] = Field(
        default=None,
        description="Sending options"
    )


class EmailThread(BaseModel):
    """
    Email thread model.
    
    Represents a conversation thread containing multiple messages.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "thread_id": "thread_789",
                "subject": "Demo Request",
                "messages": [
                    {
                        "id": "msg_001",
                        "from": {
                            "email": "john.doe@example.com",
                            "name": "John Doe"
                        },
                        "subject": "Demo Request",
                        "date": "2025-10-30T15:30:00Z",
                        "snippet": "I'd like to schedule a demo..."
                    }
                ],
                "participants": [
                    {
                        "email": "john.doe@example.com",
                        "name": "John Doe"
                    }
                ]
            }
        }
    )
    
    thread_id: str = Field(description="Thread identifier")
    subject: str = Field(description="Thread subject")
    messages: List[Email] = Field(description="Messages in thread")
    participants: List[EmailAddress] = Field(
        description="All participants in thread"
    )
    message_count: int = Field(
        ge=0,
        description="Number of messages in thread"
    )
    is_read: bool = Field(
        default=False,
        description="Whether all messages are read"
    )
    labels: Optional[List[str]] = Field(
        default=None,
        description="Thread labels"
    )
    last_message_date: datetime = Field(
        description="Date of most recent message"
    )


class SearchEmailsRequest(BaseModel):
    """Request to search for emails."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "demo request",
                "from_email": "john.doe@example.com",
                "to_email": "sales@transform-army.ai",
                "subject": "demo",
                "has_attachments": True,
                "labels": ["INBOX"],
                "is_read": False,
                "date_after": "2025-10-01T00:00:00Z",
                "date_before": "2025-10-31T23:59:59Z",
                "pagination": {
                    "page": 1,
                    "page_size": 50
                }
            }
        }
    )
    
    query: Optional[str] = Field(
        default=None,
        description="Full-text search query"
    )
    from_email: Optional[EmailStr] = Field(
        default=None,
        description="Filter by sender email"
    )
    to_email: Optional[EmailStr] = Field(
        default=None,
        description="Filter by recipient email"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Filter by subject (partial match)"
    )
    has_attachments: Optional[bool] = Field(
        default=None,
        description="Filter messages with/without attachments"
    )
    labels: Optional[List[str]] = Field(
        default=None,
        description="Filter by labels (e.g., ['INBOX', 'IMPORTANT'])"
    )
    is_read: Optional[bool] = Field(
        default=None,
        description="Filter by read status"
    )
    is_starred: Optional[bool] = Field(
        default=None,
        description="Filter by starred status"
    )
    date_after: Optional[datetime] = Field(
        default=None,
        description="Filter messages after this date"
    )
    date_before: Optional[datetime] = Field(
        default=None,
        description="Filter messages before this date"
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Filter by thread ID"
    )
    pagination: Optional[PaginationParams] = Field(
        default=None,
        description="Pagination parameters"
    )


class EmailSearchMatch(BaseModel):
    """A single email search result."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "msg_abc123",
                "thread_id": "thread_789",
                "from": {
                    "email": "john.doe@example.com",
                    "name": "John Doe"
                },
                "to": [
                    {
                        "email": "sales@transform-army.ai",
                        "name": "Sales Team"
                    }
                ],
                "subject": "Demo Request",
                "snippet": "I'd like to schedule a demo...",
                "date": "2025-10-30T15:30:00Z",
                "labels": ["INBOX"],
                "is_read": False
            }
        }
    )
    
    id: str = Field(description="Message ID")
    thread_id: Optional[str] = Field(
        default=None,
        description="Thread ID"
    )
    from_: EmailAddress = Field(
        alias="from",
        description="Sender"
    )
    to: List[EmailAddress] = Field(description="Recipients")
    subject: str = Field(description="Email subject")
    snippet: str = Field(description="Email preview snippet")
    date: datetime = Field(description="Email date")
    labels: Optional[List[str]] = Field(
        default=None,
        description="Email labels"
    )
    is_read: bool = Field(description="Read status")
    is_starred: bool = Field(
        default=False,
        description="Starred status"
    )
    has_attachments: bool = Field(
        default=False,
        description="Whether email has attachments"
    )


class SearchEmailsResponse(BaseModel):
    """Response from email search operation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "matches": [
                    {
                        "id": "msg_abc123",
                        "thread_id": "thread_789",
                        "from": {
                            "email": "john.doe@example.com",
                            "name": "John Doe"
                        },
                        "to": [
                            {
                                "email": "sales@transform-army.ai"
                            }
                        ],
                        "subject": "Demo Request",
                        "snippet": "I'd like to schedule a demo...",
                        "date": "2025-10-30T15:30:00Z",
                        "is_read": False
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
    
    matches: List[EmailSearchMatch] = Field(description="Search results")
    pagination: Optional[PaginationResponse] = Field(
        default=None,
        description="Pagination metadata"
    )


class SendEmailResponse(BaseModel):
    """Response from send email operation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_abc123",
                "thread_id": "thread_789",
                "provider": "gmail",
                "provider_message_id": "CAD1234567890",
                "scheduled_for": "2025-10-31T09:00:00Z",
                "estimated_delivery": "2025-10-31T09:00:30Z",
                "status": "queued"
            }
        }
    )
    
    message_id: str = Field(description="Internal message ID")
    thread_id: Optional[str] = Field(
        default=None,
        description="Thread ID if part of thread"
    )
    provider: str = Field(description="Email provider used")
    provider_message_id: str = Field(
        description="Provider's message ID"
    )
    scheduled_for: Optional[datetime] = Field(
        default=None,
        description="Scheduled delivery time"
    )
    estimated_delivery: Optional[datetime] = Field(
        default=None,
        description="Estimated delivery time"
    )
    status: str = Field(
        description="Email status (e.g., 'queued', 'sent', 'delivered')"
    )