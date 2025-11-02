"""
Helpdesk API endpoints for the adapter service.

This module provides REST API endpoints for helpdesk operations including
creating/updating tickets, searching tickets, and adding comments.
"""

from datetime import datetime
from typing import Annotated, Dict, Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import schema models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from packages.schema.src.python.helpdesk import (
    TicketResponse,
    CommentResponse,
    SearchTicketsResponse,
    TicketSearchMatch
)
from packages.schema.src.python.base import PaginationResponse

from ..core.dependencies import (
    get_tenant_config,
    get_tenant_id,
    get_correlation_id,
    get_helpdesk_provider,
    log_action
)
from ..core.database import get_db
from ..core.logging import get_logger
from ..core.exceptions import ValidationException, ProviderException
from ..providers.base import HelpdeskProvider


logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/create_ticket",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new helpdesk ticket",
    description="""
    Create a new support ticket in the helpdesk system.
    
    This endpoint creates a ticket record with the provided information.
    The ticket will be created in the configured helpdesk provider (Zendesk, etc.).
    
    **Example Request:**
    ```json
    {
        "subject": "Unable to login to dashboard",
        "description": "User reports seeing 'Invalid credentials' error.",
        "priority": "high",
        "requester_email": "customer@example.com",
        "tags": ["login", "authentication"],
        "metadata": {
            "source": "api",
            "campaign": "support"
        }
    }
    ```
    
    **Example Response:**
    ```json
    {
        "id": "tick_789",
        "ticket_number": "#12345",
        "subject": "Unable to login to dashboard",
        "status": "open",
        "priority": "high",
        "provider": "zendesk",
        "provider_id": "12345",
        "created_at": "2025-10-31T05:00:00Z"
    }
    ```
    """,
    tags=["Helpdesk - Tickets"]
)
async def create_ticket(
    subject: str,
    description: str,
    priority: str = None,
    requester_email: str = None,
    tags: List[str] = None,
    metadata: Dict[str, Any] = None,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: HelpdeskProvider = Depends(get_helpdesk_provider),
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """
    Create a new helpdesk ticket.
    
    Args:
        subject: Ticket subject/title (required)
        description: Ticket description/body (required)
        priority: Ticket priority (urgent, high, normal, low)
        requester_email: Email of person requesting support
        tags: Tags to apply to ticket
        metadata: Additional metadata
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Helpdesk provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        TicketResponse with created ticket details
    """
    start_time = datetime.utcnow()
    
    # Validate required fields
    if not subject:
        raise ValidationException(
            message="Subject is required",
            field="subject",
            value=subject
        )
    
    if not description:
        raise ValidationException(
            message="Description is required",
            field="description",
            value=description
        )
    
    # Build request payload for logging
    request_payload = {
        "subject": subject,
        "description": description,
        "priority": priority,
        "requester_email": requester_email,
        "tags": tags,
        "metadata": metadata
    }
    
    try:
        # Call provider to create ticket
        result = await provider.execute_with_retry(
            action="create_ticket",
            parameters={
                "subject": subject,
                "description": description,
                "priority": priority,
                "requester_email": requester_email,
                "tags": tags,
                "metadata": metadata
            }
        )
        
        # Build response from provider result
        response = TicketResponse(
            id=result.get("id"),
            ticket_number=result.get("ticket_number"),
            subject=result.get("subject"),
            description=result.get("description"),
            status=result.get("status", "open"),
            priority=result.get("priority"),
            requester_email=result.get("requester_email"),
            requester_name=result.get("requester_name"),
            assignee_id=result.get("assignee_id"),
            assignee_name=result.get("assignee_name"),
            tags=result.get("tags"),
            provider=result.get("provider"),
            provider_id=result.get("provider_id"),
            created_at=result.get("created_at") or datetime.utcnow(),
            updated_at=result.get("updated_at"),
            url=result.get("url"),
            custom_fields=metadata
        )
        
        # Calculate execution time
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="helpdesk_create",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=response.model_dump(),
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Ticket created: {response.id}",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return response
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log failed action
        await log_action(
            tenant_id=tenant_id,
            action_type="helpdesk_create",
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
            f"Failed to create ticket: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to create ticket: {str(e)}",
            original_error=e
        )


@router.post(
    "/update_ticket",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing helpdesk ticket",
    description="""
    Update an existing ticket in the helpdesk system.
    
    This endpoint updates the specified fields of an existing ticket.
    Only provided fields will be updated; others remain unchanged.
    
    **Example Request:**
    ```json
    {
        "ticket_id": "tick_789",
        "updates": {
            "status": "solved",
            "priority": "low",
            "assignee_id": "agent_001"
        },
        "metadata": {
            "updated_by": "agent-001"
        }
    }
    ```
    """,
    tags=["Helpdesk - Tickets"]
)
async def update_ticket(
    ticket_id: str,
    updates: Dict[str, Any],
    metadata: Dict[str, Any] = None,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: HelpdeskProvider = Depends(get_helpdesk_provider),
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """
    Update an existing helpdesk ticket.
    
    Args:
        ticket_id: ID of the ticket to update
        updates: Dictionary of fields to update
        metadata: Additional metadata
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Helpdesk provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        TicketResponse with updated ticket details
    """
    start_time = datetime.utcnow()
    
    # Validate required fields
    if not ticket_id:
        raise ValidationException(
            message="Ticket ID is required",
            field="ticket_id",
            value=ticket_id
        )
    
    if not updates:
        raise ValidationException(
            message="Updates dictionary cannot be empty",
            field="updates",
            value=updates
        )
    
    # Build request payload
    request_payload = {
        "ticket_id": ticket_id,
        "updates": updates,
        "metadata": metadata
    }
    
    try:
        # Call provider to update ticket
        result = await provider.execute_with_retry(
            action="update_ticket",
            parameters={
                "ticket_id": ticket_id,
                "updates": updates
            }
        )
        
        # Build response from provider result
        response = TicketResponse(
            id=result.get("id"),
            ticket_number=result.get("ticket_number"),
            subject=result.get("subject"),
            description=result.get("description"),
            status=result.get("status"),
            priority=result.get("priority"),
            requester_email=result.get("requester_email"),
            requester_name=result.get("requester_name"),
            assignee_id=result.get("assignee_id"),
            assignee_name=result.get("assignee_name"),
            tags=result.get("tags"),
            provider=result.get("provider"),
            provider_id=result.get("provider_id"),
            created_at=result.get("created_at") or datetime.utcnow(),
            updated_at=result.get("updated_at") or datetime.utcnow(),
            url=result.get("url"),
            custom_fields=metadata
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="helpdesk_update",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=response.model_dump(),
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Ticket updated: {response.id}",
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
            action_type="helpdesk_update",
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
            f"Failed to update ticket: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to update ticket: {str(e)}",
            original_error=e
        )


@router.post(
    "/search_tickets",
    response_model=SearchTicketsResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for helpdesk tickets",
    description="""
    Search for tickets in the helpdesk system.
    
    This endpoint searches for tickets matching the provided criteria.
    Supports filtering by status, priority, assignee, and more.
    
    **Example Request:**
    ```json
    {
        "query": "login error",
        "status": ["open", "pending"],
        "priority": ["high", "urgent"],
        "assignee": "agent_001",
        "limit": 10,
        "offset": 0
    }
    ```
    """,
    tags=["Helpdesk - Tickets"]
)
async def search_tickets(
    query: str = None,
    status: List[str] = None,
    priority: List[str] = None,
    assignee: str = None,
    limit: int = 10,
    offset: int = 0,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: HelpdeskProvider = Depends(get_helpdesk_provider),
    db: AsyncSession = Depends(get_db)
) -> SearchTicketsResponse:
    """
    Search for helpdesk tickets.
    
    Args:
        query: Search query string
        status: Filter by ticket status
        priority: Filter by priority levels
        assignee: Filter by assignee ID
        limit: Maximum number of results to return
        offset: Number of results to skip
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Helpdesk provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        SearchTicketsResponse with matching tickets
    """
    start_time = datetime.utcnow()
    
    # Validate pagination parameters
    if limit < 1 or limit > 100:
        raise ValidationException(
            message="Limit must be between 1 and 100",
            field="limit",
            value=limit
        )
    
    if offset < 0:
        raise ValidationException(
            message="Offset must be non-negative",
            field="offset",
            value=offset
        )
    
    # Build request payload
    request_payload = {
        "query": query,
        "status": status,
        "priority": priority,
        "assignee": assignee,
        "limit": limit,
        "offset": offset
    }
    
    try:
        # Call provider to search tickets
        result = await provider.execute_with_retry(
            action="search_tickets",
            parameters={
                "query": query,
                "status": status,
                "priority": priority,
                "assignee": assignee,
                "limit": limit,
                "offset": offset
            }
        )
        
        # Convert provider results to TicketSearchMatch objects
        matches = []
        for match_data in result.get("matches", []):
            match = TicketSearchMatch(
                id=match_data.get("id"),
                ticket_number=match_data.get("ticket_number"),
                subject=match_data.get("subject"),
                status=match_data.get("status"),
                priority=match_data.get("priority"),
                requester_email=match_data.get("requester_email") or "unknown@example.com",
                requester_name=match_data.get("requester_name"),
                assignee_id=match_data.get("assignee_id"),
                assignee_name=match_data.get("assignee_name"),
                tags=match_data.get("tags"),
                created_at=match_data.get("created_at") or datetime.utcnow(),
                updated_at=match_data.get("updated_at"),
                url=match_data.get("url")
            )
            matches.append(match)
        
        # Build pagination from provider response
        pagination_data = result.get("pagination", {})
        total_items = pagination_data.get("total_items", len(matches))
        page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_items + limit - 1) // limit if total_items > 0 and limit > 0 else 1
        
        pagination = PaginationResponse(
            page=page,
            page_size=limit,
            total_pages=total_pages,
            total_items=total_items,
            has_next=pagination_data.get("has_next", False),
            has_previous=page > 1,
            next_cursor=None
        )
        
        response = SearchTicketsResponse(
            matches=matches,
            pagination=pagination
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="helpdesk_search",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data={"result_count": len(matches)},
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Ticket search completed: {len(matches)} results",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms,
                "result_count": len(matches)
            }
        )
        
        return response
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="helpdesk_search",
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
            f"Failed to search tickets: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to search tickets: {str(e)}",
            original_error=e
        )


@router.post(
    "/add_comment",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a helpdesk ticket",
    description="""
    Add a comment or reply to a helpdesk ticket.
    
    This endpoint creates a comment associated with the specified ticket.
    Comments can be public (visible to requester) or private (internal notes).
    
    **Example Request:**
    ```json
    {
        "ticket_id": "tick_789",
        "comment_text": "I've reviewed the logs and identified the issue.",
        "is_public": false,
        "metadata": {
            "author": "agent_001"
        }
    }
    ```
    """,
    tags=["Helpdesk - Comments"]
)
async def add_comment(
    ticket_id: str,
    comment_text: str,
    is_public: bool = True,
    metadata: Dict[str, Any] = None,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: HelpdeskProvider = Depends(get_helpdesk_provider),
    db: AsyncSession = Depends(get_db)
) -> CommentResponse:
    """
    Add a comment to a helpdesk ticket.
    
    Args:
        ticket_id: ID of the ticket to add comment to
        comment_text: Content of the comment
        is_public: Whether comment is visible to requester
        metadata: Additional metadata
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Helpdesk provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        CommentResponse with created comment details
    """
    start_time = datetime.utcnow()
    
    # Validate required fields
    if not ticket_id:
        raise ValidationException(
            message="Ticket ID is required",
            field="ticket_id",
            value=ticket_id
        )
    
    if not comment_text:
        raise ValidationException(
            message="Comment text is required",
            field="comment_text",
            value=comment_text
        )
    
    # Build request payload
    request_payload = {
        "ticket_id": ticket_id,
        "comment_text": comment_text,
        "is_public": is_public,
        "metadata": metadata
    }
    
    try:
        # Call provider to add comment
        result = await provider.execute_with_retry(
            action="add_comment",
            parameters={
                "ticket_id": ticket_id,
                "comment_text": comment_text,
                "is_public": is_public,
                "metadata": metadata
            }
        )
        
        response = CommentResponse(
            id=result.get("id"),
            ticket_id=result.get("ticket_id"),
            body=result.get("body") or comment_text,
            is_public=result.get("is_public", is_public),
            author_id=result.get("author_id"),
            author_name=result.get("author_name"),
            provider=result.get("provider"),
            provider_id=result.get("provider_id"),
            created_at=result.get("created_at") or datetime.utcnow()
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="helpdesk_create",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=response.model_dump(),
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id, "resource_type": "comment"},
            db=db
        )
        
        logger.info(
            f"Comment added: {response.id} to ticket {ticket_id}",
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
            action_type="helpdesk_create",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=None,
            status="failure",
            execution_time_ms=execution_time_ms,
            error_message=str(e),
            metadata={"correlation_id": correlation_id, "resource_type": "comment"},
            db=db
        )
        
        logger.error(
            f"Failed to add comment: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to add comment: {str(e)}",
            original_error=e
        )