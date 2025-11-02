"""
Calendar API endpoints for the adapter service.

This module provides REST API endpoints for calendar operations including
creating events, checking availability, and managing schedules.
"""

from datetime import datetime
from typing import Annotated, Dict, Any, Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

# Import schema models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from packages.schema.src.python.calendar import (
    CreateEventApiRequest,
    UpdateEventApiRequest,
    CancelEventApiRequest,
    ListEventsApiRequest,
    CheckAvailabilityApiRequest,
    EventApiResponse,
    ListEventsApiResponse,
    CancelEventApiResponse,
    AvailabilityApiResponse
)

from ..core.dependencies import (
    get_tenant_id,
    get_correlation_id,
    log_action
)
from ..core.database import get_db
from ..core.logging import get_logger
from ..core.exceptions import ValidationException, ProviderException
from ..providers.base import CalendarProvider
from ..providers import get_registry, ProviderType


logger = get_logger(__name__)
router = APIRouter()


async def get_calendar_provider(
    tenant_id: Annotated[str, Depends(get_tenant_id)]
) -> CalendarProvider:
    """Get calendar provider for tenant."""
    registry = get_registry()
    
    # For now, use Google Calendar as default
    # In production, this would be configured per tenant
    providers = registry.get_providers_by_type(ProviderType.CALENDAR)
    
    if "google" not in providers:
        raise ProviderException(
            provider="google",
            message="Google Calendar provider not registered"
        )
    
    provider_class = providers["google"]
    
    # In production, get credentials from tenant config
    # For now, use dummy credentials
    credentials = {
        "auth_type": "oauth2",
        "access_token": "dummy_token",
       "refresh_token": "dummy_refresh",
        "client_id": "dummy_client_id",
        "client_secret": "dummy_client_secret"
    }
    
    return provider_class(credentials)


@router.post(
    "/events",
    response_model=EventApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a calendar event",
    description="""
    Create a new calendar event.
    
    This endpoint creates an event in the configured calendar provider.
    Supports Google Meet conference links, attendees, and reminders.
    
    **Example Request:**
    ```json
    {
        "calendar_id": "primary",
        "summary": "Team Meeting",
        "description": "Quarterly planning session",
        "start_time": "2024-01-01T10:00:00-05:00",
        "end_time": "2024-01-01T11:00:00-05:00",
        "attendees": ["john@example.com", "jane@example.com"],
        "location": "Conference Room A",
        "metadata": {
            "add_conference_data": true,
            "send_notifications": true
        }
    }
    ```
    """,
    tags=["Calendar"]
)
async def create_event(
    request: CreateEventApiRequest,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: CalendarProvider = Depends(get_calendar_provider),
    db: AsyncSession = Depends(get_db)
) -> EventApiResponse:
    """
    Create a calendar event.
    
    Args:
        request: Event creation request
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Calendar provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        EventApiResponse with created event details
    """
    start_time = datetime.utcnow()
    
    request_payload = request.model_dump()
    
    try:
        # Call provider to create event
        result = await provider.execute_with_retry(
            action="create_event",
            parameters={
                "calendar_id": request.calendar_id,
                "summary": request.summary,
                "description": request.description,
                "start_time": request.start_time,
                "end_time": request.end_time,
                "attendees": request.attendees,
                "location": request.location,
                "metadata": request.metadata
            }
        )
        
        # Build response
        response = EventApiResponse(
            id=result.get("id"),
            provider=result.get("provider"),
            provider_id=result.get("provider_id"),
            calendar_id=result.get("calendar_id"),
            summary=result.get("summary"),
            description=result.get("description"),
            start_time=result.get("start_time"),
            end_time=result.get("end_time"),
            attendees=result.get("attendees"),
            location=result.get("location"),
            meeting_url=result.get("meeting_url"),
            status=result.get("status"),
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at"),
            url=result.get("url")
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="calendar_create",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=response.model_dump(),
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Event created: {response.id}",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return response
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="calendar_create",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=None,
            status="failure",
            execution_time_ms=execution_time_ms,
            error_message=str(e),
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.error(
            f"Failed to create event: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to create event: {str(e)}",
            original_error=e
        )


@router.get(
    "/events",
    response_model=ListEventsApiResponse,
    status_code=status.HTTP_200_OK,
    summary="List calendar events",
    description="""
    List calendar events within a date range.
    
    This endpoint retrieves events from the calendar.
    """,
    tags=["Calendar"]
)
async def list_events(
    calendar_id: str = Query(default="primary"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = Query(default=10, ge=1, le=100),
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: CalendarProvider = Depends(get_calendar_provider),
    db: AsyncSession = Depends(get_db)
) -> ListEventsApiResponse:
    """
    List calendar events.
    
    Args:
        calendar_id: Calendar identifier
        start_date: Start date filter
        end_date: End date filter
        max_results: Maximum number of results
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Calendar provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        ListEventsApiResponse with events
    """
    start_time = datetime.utcnow()
    
    request_payload = {
        "calendar_id": calendar_id,
        "start_date": start_date,
        "end_date": end_date,
        "max_results": max_results
    }
    
    try:
        result = await provider.execute_with_retry(
            action="list_events",
            parameters={
                "calendar_id": calendar_id,
                "start_date": start_date,
                "end_date": end_date,
                "max_results": max_results
            }
        )
        
        # Build response
        response = ListEventsApiResponse(
            events=result.get("events", []),
            calendar_id=result.get("calendar_id"),
            total_count=result.get("total_count")
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="calendar_list",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data={"event_count": response.total_count},
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Events listed: {response.total_count} results",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return response
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="calendar_list",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=None,
            status="failure",
            execution_time_ms=execution_time_ms,
            error_message=str(e),
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.error(
            f"Failed to list events: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to list events: {str(e)}",
            original_error=e
        )


@router.post(
    "/availability",
    response_model=AvailabilityApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Check calendar availability",
    description="""
    Check availability for scheduling meetings.
    
    This endpoint checks the calendar for free time slots.
    """,
    tags=["Calendar"]
)
async def check_availability(
    request: CheckAvailabilityApiRequest,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: CalendarProvider = Depends(get_calendar_provider),
    db: AsyncSession = Depends(get_db)
) -> AvailabilityApiResponse:
    """
    Check calendar availability.
    
    Args:
        request: Availability check request
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Calendar provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        AvailabilityApiResponse with available slots
    """
    start_time = datetime.utcnow()
    
    request_payload = request.model_dump()
    
    try:
        result = await provider.execute_with_retry(
            action="check_availability",
            parameters={
                "calendar_id": request.calendar_id,
                "start_time": request.start_time,
                "end_time": request.end_time,
                "duration_minutes": request.duration_minutes
            }
        )
        
        # Build response
        response = AvailabilityApiResponse(
            available_slots=result.get("available_slots", []),
            calendar_id=result.get("calendar_id"),
            checked_at=result.get("checked_at")
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="calendar_availability",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data={"slot_count": len(response.available_slots)},
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Availability checked: {len(response.available_slots)} slots found",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return response
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="calendar_availability",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=None,
            status="failure",
            execution_time_ms=execution_time_ms,
            error_message=str(e),
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.error(
            f"Failed to check availability: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to check availability: {str(e)}",
            original_error=e
        )


@router.put(
    "/events/{event_id}",
    response_model=EventApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a calendar event",
    description="""
    Update an existing calendar event.
    
    This endpoint updates the specified fields of an event.
    """,
    tags=["Calendar"]
)
async def update_event(
    event_id: str,
    request: UpdateEventApiRequest,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: CalendarProvider = Depends(get_calendar_provider),
    db: AsyncSession = Depends(get_db)
) -> EventApiResponse:
    """
    Update a calendar event.
    
    Args:
        event_id: Event identifier
        request: Update request
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Calendar provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        EventApiResponse with updated event
    """
    start_time = datetime.utcnow()
    
    request_payload = {
        "event_id": event_id,
        **request.model_dump()
    }
    
    try:
        result = await provider.execute_with_retry(
            action="update_event",
            parameters={
                "event_id": event_id,
                "updates": request.updates
            }
        )
        
        # Build response
        response = EventApiResponse(
            id=result.get("id"),
            provider=result.get("provider"),
            provider_id=result.get("provider_id"),
            calendar_id=result.get("calendar_id"),
            summary=result.get("summary"),
            description=result.get("description"),
            start_time=result.get("start_time"),
            end_time=result.get("end_time"),
            attendees=result.get("attendees"),
            location=result.get("location"),
            meeting_url=result.get("meeting_url"),
            status=result.get("status"),
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at"),
            url=result.get("url")
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="calendar_update",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=response.model_dump(),
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Event updated: {response.id}",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return response
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="calendar_update",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=None,
            status="failure",
            execution_time_ms=execution_time_ms,
            error_message=str(e),
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.error(
            f"Failed to update event: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to update event: {str(e)}",
            original_error=e
        )


@router.delete(
    "/events/{event_id}",
    response_model=CancelEventApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel a calendar event",
    description="""
    Cancel/delete a calendar event.
    
    This endpoint cancels an event and optionally notifies attendees.
    """,
    tags=["Calendar"]
)
async def cancel_event(
    event_id: str,
    cancellation_message: Optional[str] = Query(default=None),
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: CalendarProvider = Depends(get_calendar_provider),
    db: AsyncSession = Depends(get_db)
) -> CancelEventApiResponse:
    """
    Cancel a calendar event.
    
    Args:
        event_id: Event identifier
        cancellation_message: Optional cancellation message
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Calendar provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        CancelEventApiResponse with cancellation confirmation
    """
    start_time = datetime.utcnow()
    
    request_payload = {
        "event_id": event_id,
        "cancellation_message": cancellation_message
    }
    
    try:
        result = await provider.execute_with_retry(
            action="cancel_event",
            parameters={
                "event_id": event_id,
                "cancellation_message": cancellation_message
            }
        )
        
        # Build response
        response = CancelEventApiResponse(
            event_id=result.get("event_id"),
            status=result.get("status"),
            message=result.get("message"),
            cancelled_at=result.get("cancelled_at")
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="calendar_delete",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=response.model_dump(),
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Event cancelled: {response.event_id}",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return response
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="calendar_delete",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=None,
            status="failure",
            execution_time_ms=execution_time_ms,
            error_message=str(e),
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.error(
            f"Failed to cancel event: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to cancel event: {str(e)}",
            original_error=e
        )