"""
CRM API endpoints.

Provides REST API for CRM operations including contacts, companies, deals, and notes.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from datetime import datetime
from typing import Any, Dict
import uuid
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.schema.src.python.crm import (
    CreateContactRequest,
    UpdateContactRequest,
    CreateDealRequest,
    AddNoteRequest,
    SearchContactsRequest
)
from packages.schema.src.python.base import ActionEnvelope, ActionStatus, ToolResult
from core.dependencies import get_correlation_id_dependency, get_tenant_id
from core.logging import get_logger
from providers.factory import get_factory, ProviderType


router = APIRouter()
logger = get_logger(__name__)


@router.post("/contacts", status_code=status.HTTP_201_CREATED)
async def create_contact(
    request: CreateContactRequest,
    correlation_id: str = Depends(get_correlation_id_dependency),
    tenant_id: str = Depends(get_tenant_id)
) -> ActionEnvelope:
    """
    Create a new CRM contact.
    
    Creates a contact in the configured CRM provider (HubSpot, Salesforce, etc.).
    Supports deduplication and update-if-exists options.
    """
    start_time = datetime.utcnow()
    action_id = f"act_{uuid.uuid4().hex[:16]}"
    
    try:
        # Get CRM provider
        factory = get_factory()
        provider = await factory.get_provider(ProviderType.CRM, tenant_id)
        
        # Execute action with retry
        result = await provider.execute_with_retry(
            action="create_contact",
            parameters={"contact": request.contact.model_dump(), "options": request.options.model_dump() if request.options else {}},
            idempotency_key=request.idempotency_key
        )
        
        # Calculate duration
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return ActionEnvelope(
            action_id=action_id,
            correlation_id=correlation_id or request.correlation_id,
            tenant_id=tenant_id,
            timestamp=start_time,
            operation="crm.contact.create",
            status=ActionStatus.SUCCESS,
            duration_ms=duration_ms,
            result=ToolResult(**result),
            metadata={"idempotency_key": request.idempotency_key, "retry_count": 0}
        )
    
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Failed to create contact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/contacts/{contact_id}", status_code=status.HTTP_200_OK)
async def update_contact(
    contact_id: str,
    request: UpdateContactRequest,
    correlation_id: str = Depends(get_correlation_id_dependency),
    tenant_id: str = Depends(get_tenant_id)
) -> ActionEnvelope:
    """Update an existing CRM contact."""
    start_time = datetime.utcnow()
    action_id = f"act_{uuid.uuid4().hex[:16]}"
    
    try:
        factory = get_factory()
        provider = await factory.get_provider(ProviderType.CRM, tenant_id)
        
        result = await provider.execute_with_retry(
            action="update_contact",
            parameters={"contact_id": contact_id, "updates": request.updates},
            idempotency_key=request.idempotency_key
        )
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return ActionEnvelope(
            action_id=action_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            timestamp=start_time,
            operation="crm.contact.update",
            status=ActionStatus.SUCCESS,
            duration_ms=duration_ms,
            result=ToolResult(**result)
        )
    
    except Exception as e:
        logger.error(f"Failed to update contact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/contacts/{contact_id}", status_code=status.HTTP_200_OK)
async def get_contact(
    contact_id: str,
    correlation_id: str = Depends(get_correlation_id_dependency),
    tenant_id: str = Depends(get_tenant_id)
) -> ActionEnvelope:
    """Get a CRM contact by ID."""
    start_time = datetime.utcnow()
    action_id = f"act_{uuid.uuid4().hex[:16]}"
    
    try:
        factory = get_factory()
        provider = await factory.get_provider(ProviderType.CRM, tenant_id)
        
        result = await provider.execute_with_retry(
            action="get_contact",
            parameters={"contact_id": contact_id}
        )
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return ActionEnvelope(
            action_id=action_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            timestamp=start_time,
            operation="crm.contact.get",
            status=ActionStatus.SUCCESS,
            duration_ms=duration_ms,
            result=ToolResult(**result)
        )
    
    except Exception as e:
        logger.error(f"Failed to get contact: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/contacts/search", status_code=status.HTTP_200_OK)
async def search_contacts(
    request: SearchContactsRequest,
    correlation_id: str = Depends(get_correlation_id_dependency),
    tenant_id: str = Depends(get_tenant_id)
) -> ActionEnvelope:
    """Search for CRM contacts."""
    start_time = datetime.utcnow()
    action_id = f"act_{uuid.uuid4().hex[:16]}"
    
    try:
        factory = get_factory()
        provider = await factory.get_provider(ProviderType.CRM, tenant_id)
        
        result = await provider.execute_with_retry(
            action="search_contacts",
            parameters=request.model_dump()
        )
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return ActionEnvelope(
            action_id=action_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            timestamp=start_time,
            operation="crm.contact.search",
            status=ActionStatus.SUCCESS,
            duration_ms=duration_ms,
            result=result
        )
    
    except Exception as e:
        logger.error(f"Failed to search contacts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/deals", status_code=status.HTTP_201_CREATED)
async def create_deal(
    request: CreateDealRequest,
    correlation_id: str = Depends(get_correlation_id_dependency),
    tenant_id: str = Depends(get_tenant_id)
) -> ActionEnvelope:
    """Create a new CRM deal/opportunity."""
    start_time = datetime.utcnow()
    action_id = f"act_{uuid.uuid4().hex[:16]}"
    
    try:
        factory = get_factory()
        provider = await factory.get_provider(ProviderType.CRM, tenant_id)
        
        result = await provider.execute_with_retry(
            action="create_deal",
            parameters={"deal": request.deal.model_dump()},
            idempotency_key=request.idempotency_key
        )
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return ActionEnvelope(
            action_id=action_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            timestamp=start_time,
            operation="crm.deal.create",
            status=ActionStatus.SUCCESS,
            duration_ms=duration_ms,
            result=ToolResult(**result)
        )
    
    except Exception as e:
        logger.error(f"Failed to create deal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/contacts/{contact_id}/notes", status_code=status.HTTP_201_CREATED)
async def add_note(
    contact_id: str,
    request: AddNoteRequest,
    correlation_id: str = Depends(get_correlation_id_dependency),
    tenant_id: str = Depends(get_tenant_id)
) -> ActionEnvelope:
    """Add a note to a CRM contact."""
    start_time = datetime.utcnow()
    action_id = f"act_{uuid.uuid4().hex[:16]}"
    
    try:
        factory = get_factory()
        provider = await factory.get_provider(ProviderType.CRM, tenant_id)
        
        result = await provider.execute_with_retry(
            action="add_note",
            parameters={"contact_id": contact_id, "note": request.note.model_dump()},
            idempotency_key=request.idempotency_key
        )
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return ActionEnvelope(
            action_id=action_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            timestamp=start_time,
            operation="crm.note.create",
            status=ActionStatus.SUCCESS,
            duration_ms=duration_ms,
            result=ToolResult(**result)
        )
    
    except Exception as e:
        logger.error(f"Failed to add note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )