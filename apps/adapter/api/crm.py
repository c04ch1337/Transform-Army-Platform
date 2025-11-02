"""
CRM API endpoints for the adapter service.

This module provides REST API endpoints for CRM operations including
creating/updating contacts, searching contacts, and adding notes.
"""

from datetime import datetime
from typing import Annotated, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import schema models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from packages.schema.src.python.crm import (
    ContactResponse,
    NoteResponse,
    SearchContactsResponse,
    ContactSearchMatch
)
from packages.schema.src.python.base import PaginationResponse

from ..core.dependencies import (
    get_tenant_config,
    get_tenant_id,
    get_correlation_id,
    get_crm_provider,
    log_action
)
from ..core.database import get_db
from ..core.logging import get_logger
from ..core.exceptions import ValidationException, ProviderException
from ..providers.base import CRMProvider


logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/create_contact",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new CRM contact",
    description="""
    Create a new contact in the CRM system.
    
    This endpoint creates a contact record with the provided information.
    The contact will be created in the configured CRM provider (HubSpot, Salesforce, etc.).
    
    **Example Request:**
    ```json
    {
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Acme Corp",
        "phone": "+1-555-0123",
        "metadata": {
            "source": "website",
            "campaign": "spring-2025"
        }
    }
    ```
    
    **Example Response:**
    ```json
    {
        "id": "cont_abc123",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Acme Corp",
        "phone": "+1-555-0123",
        "provider": "hubspot",
        "provider_id": "12345",
        "created_at": "2025-10-31T05:00:00Z"
    }
    ```
    """,
    tags=["CRM - Contacts"]
)
async def create_contact(
    email: str,
    first_name: str = None,
    last_name: str = None,
    company: str = None,
    phone: str = None,
    metadata: Dict[str, Any] = None,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: CRMProvider = Depends(get_crm_provider),
    db: AsyncSession = Depends(get_db)
) -> ContactResponse:
    """
    Create a new CRM contact.
    
    Args:
        email: Contact email address (required)
        first_name: Contact first name
        last_name: Contact last name
        company: Company name
        phone: Phone number
        metadata: Additional metadata
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        db: Database session (from dependency)
        
    Returns:
        ContactResponse with created contact details
    """
    start_time = datetime.utcnow()
    
    # Validate required fields
    if not email:
        raise ValidationException(
            message="Email is required",
            field="email",
            value=email
        )
    
    # Build request payload for logging
    request_payload = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "company": company,
        "phone": phone,
        "metadata": metadata
    }
    
    try:
        # Call provider to create contact
        result = await provider.execute_with_retry(
            action="create_contact",
            parameters={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "company": company,
                "phone": phone,
                "metadata": metadata
            }
        )
        
        # Build response from provider result
        response = ContactResponse(
            id=result.get("id"),
            email=result.get("email"),
            first_name=result.get("first_name"),
            last_name=result.get("last_name"),
            company=result.get("company"),
            phone=result.get("phone"),
            title=result.get("title"),
            provider=result.get("provider"),
            provider_id=result.get("provider_id"),
            created_at=result.get("created_at") or datetime.utcnow(),
            updated_at=result.get("updated_at"),
            custom_fields=metadata,
            url=result.get("url")
        )
        
        # Calculate execution time
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="crm_create",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=response.model_dump(),
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Contact created: {response.id}",
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
            action_type="crm_create",
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
            f"Failed to create contact: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to create contact: {str(e)}",
            original_error=e
        )


@router.post(
    "/update_contact",
    response_model=ContactResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing CRM contact",
    description="""
    Update an existing contact in the CRM system.
    
    This endpoint updates the specified fields of an existing contact.
    Only provided fields will be updated; others remain unchanged.
    
    **Example Request:**
    ```json
    {
        "contact_id": "cont_abc123",
        "updates": {
            "title": "Senior VP of Sales",
            "phone": "+1-555-0199"
        },
        "metadata": {
            "updated_by": "agent-001"
        }
    }
    ```
    """,
    tags=["CRM - Contacts"]
)
async def update_contact(
    contact_id: str,
    updates: Dict[str, Any],
    metadata: Dict[str, Any] = None,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: CRMProvider = Depends(get_crm_provider),
    db: AsyncSession = Depends(get_db)
) -> ContactResponse:
    """
    Update an existing CRM contact.
    
    Args:
        contact_id: ID of the contact to update
        updates: Dictionary of fields to update
        metadata: Additional metadata
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        db: Database session (from dependency)
        
    Returns:
        ContactResponse with updated contact details
    """
    start_time = datetime.utcnow()
    
    # Validate required fields
    if not contact_id:
        raise ValidationException(
            message="Contact ID is required",
            field="contact_id",
            value=contact_id
        )
    
    if not updates:
        raise ValidationException(
            message="Updates dictionary cannot be empty",
            field="updates",
            value=updates
        )
    
    # Build request payload
    request_payload = {
        "contact_id": contact_id,
        "updates": updates,
        "metadata": metadata
    }
    
    try:
        # Call provider to update contact
        result = await provider.execute_with_retry(
            action="update_contact",
            parameters={
                "contact_id": contact_id,
                "updates": updates
            }
        )
        
        # Build response from provider result
        response = ContactResponse(
            id=result.get("id"),
            email=result.get("email"),
            first_name=result.get("first_name"),
            last_name=result.get("last_name"),
            company=result.get("company"),
            phone=result.get("phone"),
            title=result.get("title"),
            provider=result.get("provider"),
            provider_id=result.get("provider_id"),
            created_at=result.get("created_at") or datetime.utcnow(),
            updated_at=result.get("updated_at") or datetime.utcnow(),
            custom_fields=metadata,
            url=result.get("url")
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="crm_update",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=response.model_dump(),
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Contact updated: {response.id}",
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
            action_type="crm_update",
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
            f"Failed to update contact: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to update contact: {str(e)}",
            original_error=e
        )


@router.post(
    "/search_contacts",
    response_model=SearchContactsResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for CRM contacts",
    description="""
    Search for contacts in the CRM system.
    
    This endpoint searches for contacts matching the provided query.
    Supports filtering by email, name, company, and other fields.
    
    **Example Request:**
    ```json
    {
        "query": "john doe acme",
        "filters": {
            "company": "Acme Corp"
        },
        "limit": 10,
        "offset": 0
    }
    ```
    """,
    tags=["CRM - Contacts"]
)
async def search_contacts(
    query: str = None,
    filters: Dict[str, Any] = None,
    limit: int = 10,
    offset: int = 0,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: CRMProvider = Depends(get_crm_provider),
    db: AsyncSession = Depends(get_db)
) -> SearchContactsResponse:
    """
    Search for CRM contacts.
    
    Args:
        query: Search query string
        filters: Additional filters to apply
        limit: Maximum number of results to return
        offset: Number of results to skip
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        db: Database session (from dependency)
        
    Returns:
        SearchContactsResponse with matching contacts
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
        "filters": filters,
        "limit": limit,
        "offset": offset
    }
    
    try:
        # Call provider to search contacts
        result = await provider.execute_with_retry(
            action="search_contacts",
            parameters={
                "query": query,
                "filters": filters,
                "limit": limit,
                "offset": offset
            }
        )
        
        # Convert provider results to ContactSearchMatch objects
        matches = []
        for match_data in result.get("matches", []):
            match = ContactSearchMatch(
                id=match_data.get("id"),
                email=match_data.get("email"),
                first_name=match_data.get("first_name"),
                last_name=match_data.get("last_name"),
                company=match_data.get("company"),
                title=match_data.get("title"),
                phone=match_data.get("phone"),
                score=match_data.get("score", 1.0),
                url=match_data.get("url")
            )
            matches.append(match)
        
        # Build pagination from provider response
        pagination_data = result.get("pagination", {})
        total_items = pagination_data.get("total_items", len(matches))
        page = (offset // limit) + 1
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 1
        
        pagination = PaginationResponse(
            page=page,
            page_size=limit,
            total_pages=total_pages,
            total_items=total_items,
            has_next=pagination_data.get("has_next", False),
            has_previous=page > 1,
            next_cursor=None
        )
        
        response = SearchContactsResponse(
            matches=matches,
            pagination=pagination
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="crm_search",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data={"result_count": len(matches)},
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Contact search completed: {len(matches)} results",
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
            action_type="crm_search",
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
            f"Failed to search contacts: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to search contacts: {str(e)}",
            original_error=e
        )


@router.post(
    "/add_note",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a note to a CRM contact",
    description="""
    Add a note or activity to a CRM contact.
    
    This endpoint creates a note associated with the specified contact.
    Notes can be used to track calls, meetings, emails, or other interactions.
    
    **Example Request:**
    ```json
    {
        "contact_id": "cont_abc123",
        "note_text": "Initial qualification call completed. Customer is interested in enterprise plan.",
        "note_type": "call_note",
        "metadata": {
            "call_duration": 1800,
            "outcome": "qualified"
        }
    }
    ```
    """,
    tags=["CRM - Notes"]
)
async def add_note(
    contact_id: str,
    note_text: str,
    note_type: str = "note",
    metadata: Dict[str, Any] = None,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: CRMProvider = Depends(get_crm_provider),
    db: AsyncSession = Depends(get_db)
) -> NoteResponse:
    """
    Add a note to a CRM contact.
    
    Args:
        contact_id: ID of the contact to add note to
        note_text: Content of the note
        note_type: Type of note (e.g., 'call_note', 'email', 'meeting')
        metadata: Additional metadata
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        db: Database session (from dependency)
        
    Returns:
        NoteResponse with created note details
    """
    start_time = datetime.utcnow()
    
    # Validate required fields
    if not contact_id:
        raise ValidationException(
            message="Contact ID is required",
            field="contact_id",
            value=contact_id
        )
    
    if not note_text:
        raise ValidationException(
            message="Note text is required",
            field="note_text",
            value=note_text
        )
    
    # Build request payload
    request_payload = {
        "contact_id": contact_id,
        "note_text": note_text,
        "note_type": note_type,
        "metadata": metadata
    }
    
    try:
        # Call provider to add note
        result = await provider.execute_with_retry(
            action="add_note",
            parameters={
                "contact_id": contact_id,
                "note_text": note_text,
                "note_type": note_type
            }
        )
        
        response = NoteResponse(
            id=result.get("id"),
            contact_id=result.get("contact_id"),
            content=result.get("content"),
            type=result.get("type", note_type),
            provider=result.get("provider"),
            provider_id=result.get("provider_id"),
            created_at=result.get("created_at") or datetime.utcnow()
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="crm_create",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=response.model_dump(),
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id, "resource_type": "note"},
            db=db
        )
        
        logger.info(
            f"Note added: {response.id} to contact {contact_id}",
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
            action_type="crm_create",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=None,
            status="failure",
            execution_time_ms=execution_time_ms,
            error_message=str(e),
            metadata={"correlation_id": correlation_id, "resource_type": "note"},
            db=db
        )
        
        logger.error(
            f"Failed to add note: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to add note: {str(e)}",
            original_error=e
        )