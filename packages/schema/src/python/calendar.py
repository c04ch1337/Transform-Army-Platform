"""
Calendar schema models for Transform Army AI Adapter Service.

This module defines Pydantic models for calendar operations including events,
attendees, availability checks, and related functionality across different
calendar providers (Google Calendar, Outlook, etc.).
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr, HttpUrl, ConfigDict, field_validator

from .base import ToolInput, PaginationParams, PaginationResponse


class EventLocation(BaseModel):
    """Location information for a calendar event."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "video",
                "url": "https://meet.google.com/abc-defg-hij",
                "display_name": "Google Meet"
            }
        }
    )
    
    type: str = Field(
        description="Location type (e.g., 'physical', 'video', 'phone')"
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL for video/online meetings"
    )
    display_name: Optional[str] = Field(
        default=None,
        description="Display name for the location"
    )
    address: Optional[str] = Field(
        default=None,
        description="Physical address"
    )
    phone: Optional[str] = Field(
        default=None,
        description="Phone number for phone meetings"
    )


class EventReminder(BaseModel):
    """Reminder configuration for a calendar event."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "method": "email",
                "minutes_before": 1440
            }
        }
    )
    
    method: str = Field(
        description="Reminder method (e.g., 'email', 'notification', 'sms')"
    )
    minutes_before: int = Field(
        ge=0,
        description="Minutes before event to send reminder"
    )


class Attendee(BaseModel):
    """
    Calendar event attendee.
    
    Represents a person invited to a calendar event.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "name": "John Doe",
                "required": True,
                "response_status": "accepted"
            }
        }
    )
    
    email: EmailStr = Field(description="Attendee email address")
    name: Optional[str] = Field(
        default=None,
        description="Attendee name"
    )
    required: bool = Field(
        default=True,
        description="Whether attendance is required"
    )
    response_status: Optional[str] = Field(
        default=None,
        description="Response status (e.g., 'accepted', 'declined', 'tentative', 'needsAction')"
    )
    is_organizer: bool = Field(
        default=False,
        description="Whether this attendee is the event organizer"
    )
    comment: Optional[str] = Field(
        default=None,
        description="Attendee's comment/note"
    )


class CalendarEvent(BaseModel):
    """
    Calendar event model.
    
    Represents a calendar event across different calendar providers.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "evt_789",
                "title": "Product Demo - Acme Corp",
                "description": "Demonstrating enterprise features",
                "start_time": "2025-11-05T14:00:00Z",
                "end_time": "2025-11-05T15:00:00Z",
                "timezone": "America/New_York",
                "all_day": False,
                "attendees": [
                    {
                        "email": "john.doe@example.com",
                        "name": "John Doe",
                        "required": True
                    }
                ],
                "location": {
                    "type": "video",
                    "url": "https://meet.google.com/abc-defg-hij"
                },
                "status": "confirmed",
                "url": "https://calendar.google.com/event?eid=abc123"
            }
        }
    )
    
    id: str = Field(description="Unique event identifier")
    calendar_id: Optional[str] = Field(
        default=None,
        description="Calendar identifier where event is stored"
    )
    title: str = Field(description="Event title/summary")
    description: Optional[str] = Field(
        default=None,
        description="Event description"
    )
    start_time: datetime = Field(description="Event start time")
    end_time: datetime = Field(description="Event end time")
    timezone: str = Field(
        default="UTC",
        description="Timezone for the event (e.g., 'America/New_York')"
    )
    all_day: bool = Field(
        default=False,
        description="Whether this is an all-day event"
    )
    attendees: Optional[List[Attendee]] = Field(
        default=None,
        description="Event attendees"
    )
    location: Optional[EventLocation] = Field(
        default=None,
        description="Event location"
    )
    reminders: Optional[List[EventReminder]] = Field(
        default=None,
        description="Event reminders"
    )
    status: Optional[str] = Field(
        default=None,
        description="Event status (e.g., 'confirmed', 'tentative', 'cancelled')"
    )
    visibility: Optional[str] = Field(
        default="default",
        description="Event visibility (e.g., 'default', 'public', 'private')"
    )
    recurrence: Optional[List[str]] = Field(
        default=None,
        description="Recurrence rules (RRULE format)"
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to view event in provider system"
    )
    meeting_url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to join online meeting"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Event creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    organizer_email: Optional[EmailStr] = Field(
        default=None,
        description="Event organizer email"
    )
    organizer_name: Optional[str] = Field(
        default=None,
        description="Event organizer name"
    )
    
    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: datetime, info) -> datetime:
        """Ensure end_time is after start_time."""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError("end_time must be after start_time")
        return v


class CreateEventRequest(ToolInput):
    """
    Request to create a new calendar event.
    
    Includes options for notifications and availability checking.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_meeting123",
                "correlation_id": "cor_req130",
                "event": {
                    "title": "Product Demo - Acme Corp",
                    "description": "Demonstrating enterprise features",
                    "start_time": "2025-11-05T14:00:00Z",
                    "end_time": "2025-11-05T15:00:00Z",
                    "timezone": "America/New_York",
                    "attendees": [
                        {
                            "email": "john.doe@example.com",
                            "name": "John Doe",
                            "required": True
                        }
                    ]
                },
                "options": {
                    "send_notifications": True,
                    "check_availability": True
                }
            }
        }
    )
    
    class EventData(BaseModel):
        """Event data for creation."""
        title: str = Field(description="Event title")
        description: Optional[str] = Field(
            default=None,
            description="Event description"
        )
        start_time: datetime = Field(description="Start time")
        end_time: datetime = Field(description="End time")
        timezone: str = Field(
            default="UTC",
            description="Event timezone"
        )
        all_day: bool = Field(
            default=False,
            description="All-day event flag"
        )
        attendees: Optional[List[Attendee]] = Field(
            default=None,
            description="Event attendees"
        )
        location: Optional[EventLocation] = Field(
            default=None,
            description="Event location"
        )
        reminders: Optional[List[EventReminder]] = Field(
            default=None,
            description="Event reminders"
        )
        visibility: Optional[str] = Field(
            default="default",
            description="Event visibility"
        )
        recurrence: Optional[List[str]] = Field(
            default=None,
            description="Recurrence rules"
        )
        calendar_id: Optional[str] = Field(
            default=None,
            description="Target calendar ID"
        )
        
        @field_validator('end_time')
        @classmethod
        def validate_end_time(cls, v: datetime, info) -> datetime:
            """Ensure end_time is after start_time."""
            if 'start_time' in info.data and v <= info.data['start_time']:
                raise ValueError("end_time must be after start_time")
            return v
    
    class EventOptions(BaseModel):
        """Options for event creation."""
        send_notifications: bool = Field(
            default=True,
            description="Send invitations to attendees"
        )
        check_availability: bool = Field(
            default=False,
            description="Check attendee availability before creating"
        )
    
    event: EventData = Field(description="Event data to create")
    options: Optional[EventOptions] = Field(
        default=None,
        description="Creation options"
    )


class UpdateEventRequest(ToolInput):
    """Request to update an existing calendar event."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_event_update456",
                "correlation_id": "cor_req131",
                "updates": {
                    "title": "Product Demo - Acme Corp (Updated)",
                    "start_time": "2025-11-05T15:00:00Z",
                    "end_time": "2025-11-05T16:00:00Z"
                },
                "send_notifications": True
            }
        }
    )
    
    updates: Dict[str, Any] = Field(
        description="Fields to update (partial update)"
    )
    send_notifications: bool = Field(
        default=True,
        description="Notify attendees of changes"
    )


class WorkingHours(BaseModel):
    """Working hours configuration for availability checking."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start": "09:00",
                "end": "17:00",
                "timezone": "America/New_York",
                "exclude_weekends": True
            }
        }
    )
    
    start: str = Field(
        description="Start time (HH:MM format)"
    )
    end: str = Field(
        description="End time (HH:MM format)"
    )
    timezone: str = Field(
        description="Timezone for working hours"
    )
    exclude_weekends: bool = Field(
        default=True,
        description="Exclude weekends from available times"
    )
    
    @field_validator('start', 'end')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time is in HH:MM format."""
        try:
            hours, minutes = v.split(':')
            if len(hours) != 2 or len(minutes) != 2:
                raise ValueError
            if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                raise ValueError
        except (ValueError, AttributeError):
            raise ValueError("Time must be in HH:MM format (e.g., '09:00')")
        return v


class CheckAvailabilityRequest(BaseModel):
    """
    Request to check calendar availability.
    
    Used to find available time slots for scheduling meetings.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "correlation_id": "cor_req131",
                "query": {
                    "attendees": ["john.doe@example.com", "sales@transform-army.ai"],
                    "duration_minutes": 60,
                    "date_range": {
                        "start": "2025-11-01",
                        "end": "2025-11-15"
                    },
                    "working_hours": {
                        "start": "09:00",
                        "end": "17:00",
                        "timezone": "America/New_York",
                        "exclude_weekends": True
                    }
                }
            }
        }
    )
    
    class DateRange(BaseModel):
        """Date range for availability search."""
        start: str = Field(description="Start date (YYYY-MM-DD)")
        end: str = Field(description="End date (YYYY-MM-DD)")
    
    class AvailabilityQuery(BaseModel):
        """Availability query parameters."""
        attendees: List[EmailStr] = Field(
            description="Email addresses to check availability for"
        )
        duration_minutes: int = Field(
            ge=1,
            description="Required meeting duration in minutes"
        )
        date_range: "CheckAvailabilityRequest.DateRange" = Field(
            description="Date range to search"
        )
        working_hours: Optional[WorkingHours] = Field(
            default=None,
            description="Working hours constraints"
        )
        buffer_minutes: int = Field(
            default=0,
            ge=0,
            description="Buffer time before/after existing events"
        )
    
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for request tracing"
    )
    query: AvailabilityQuery = Field(description="Availability query")


class AvailableSlot(BaseModel):
    """An available time slot."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start": "2025-11-05T14:00:00Z",
                "end": "2025-11-05T15:00:00Z",
                "all_available": True,
                "available_attendees": ["john.doe@example.com", "sales@transform-army.ai"]
            }
        }
    )
    
    start: datetime = Field(description="Slot start time")
    end: datetime = Field(description="Slot end time")
    all_available: bool = Field(
        description="Whether all attendees are available"
    )
    available_attendees: Optional[List[EmailStr]] = Field(
        default=None,
        description="List of available attendees"
    )
    unavailable_attendees: Optional[List[EmailStr]] = Field(
        default=None,
        description="List of unavailable attendees"
    )


class CheckAvailabilityResponse(BaseModel):
    """Response from availability check."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "available_slots": [
                    {
                        "start": "2025-11-05T14:00:00Z",
                        "end": "2025-11-05T15:00:00Z",
                        "all_available": True
                    }
                ],
                "checked_calendars": 2,
                "timezone": "America/New_York"
            }
        }
    )
    
    available_slots: List[AvailableSlot] = Field(
        description="List of available time slots"
    )
    checked_calendars: int = Field(
        description="Number of calendars checked"
    )
    timezone: str = Field(description="Timezone for results")


class ListEventsRequest(BaseModel):
    """Request to list calendar events."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "calendar_id": "primary",
                "start_date": "2025-11-01",
                "end_date": "2025-11-30",
                "pagination": {
                    "page": 1,
                    "page_size": 50
                }
            }
        }
    )
    
    calendar_id: Optional[str] = Field(
        default=None,
        description="Calendar ID to list events from"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date filter (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date filter (YYYY-MM-DD)"
    )
    pagination: Optional[PaginationParams] = Field(
        default=None,
        description="Pagination parameters"
    )


class ListEventsResponse(BaseModel):
    """Response from list events operation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "events": [
                    {
                        "id": "evt_789",
                        "title": "Product Demo",
                        "start_time": "2025-11-05T14:00:00Z",
                        "end_time": "2025-11-05T15:00:00Z"
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
    
    events: List[CalendarEvent] = Field(description="List of events")
    pagination: Optional[PaginationResponse] = Field(
        default=None,
        description="Pagination metadata"
    )