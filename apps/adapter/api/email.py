"""
Email API endpoints for the adapter service.

This module provides REST API endpoints for email operations including
sending emails, searching messages, and managing threads.
"""

from datetime import datetime
from typing import Annotated, Dict, Any, Optional, List

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

# Import schema models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from packages.schema.src.python.base import PaginationResponse

from ..core.dependencies import (
    get_tenant_id,
    get_correlation_id,
    log_action
)
from ..core.database import get_db
from ..core.logging import get_logger
from ..core.exceptions import ValidationException, ProviderException
from ..providers.base import ProviderPlugin
from ..providers import get_registry, ProviderType


logger = get_logger(__name__)
router = APIRouter()


async def get_email_provider(
    tenant_id: Annotated[str, Depends(get_tenant_id)]
) -> ProviderPlugin:
    """Get email provider for tenant."""
    registry = get_registry()
    
    # For now, use Gmail as default email provider
    # In production, this would be configured per tenant
    providers = registry.get_providers_by_type(ProviderType.EMAIL)
    
    if "gmail" not in providers:
        raise ProviderException(
            provider="gmail",
            message="Gmail provider not registered"
        )
    
    provider_class = providers["gmail"]
    
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
    "/send",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send an email",
    description="""
    Send an email via the configured email provider.
    
    This endpoint sends an email with the specified content, subject, and recipients.
    Supports HTML and plain text formats, CC/BCC recipients, and attachments.
    
    **Example Request:**
    ```json
    {
        "email": {
            "from": {
                "email": "sender@example.com",
                "name": "John Doe"
            },
            "to": [
                {
                    "email": "recipient@example.com",
                    "name": "Jane Smith"
                }
            ],
            "subject": "Meeting Follow-up",
            "body": {
                "text": "Thank you for the meeting today.",
                "html": "<p>Thank you for the meeting today.</p>"
            }
        },
        "options": {
            "track_opens": true,
            "track_clicks": true
        }
    }
    ```
    """,
    tags=["Email"]
)
async def send_email(
    email: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: ProviderPlugin = Depends(get_email_provider),
    db: AsyncSession = Depends(get_db)
):
    """
    Send an email.
    
    Args:
        email: Email data (from, to, subject, body)
        options: Optional sending options
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Email provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        Send email response with message ID
    """
    start_time = datetime.utcnow()
    
    # Validate required fields
    if not email.get("to"):
        raise ValidationException(
            message="To address is required",
            field="email.to",
            value=email.get("to")
        )
    
    if not email.get("subject"):
        raise ValidationException(
            message="Subject is required",
            field="email.subject",
            value=email.get("subject")
        )
    
    # Build request payload
    request_payload = {
        "email": email,
        "options": options
    }
    
    try:
        # Call provider to send email
        result = await provider.execute_with_retry(
            action="send_email",
            parameters={
                "email": email,
                "options": options or {}
            }
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="email_send",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=result,
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Email sent: {result.get('message_id')}",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return result
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="email_send",
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
            f"Failed to send email: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to send email: {str(e)}",
            original_error=e
        )


@router.get(
    "/threads/{thread_id}",
    status_code=status.HTTP_200_OK,
    summary="Get email thread",
    description="""
    Retrieve an email thread by ID.
    
    This endpoint fetches all messages in an email thread.
    """,
    tags=["Email"]
)
async def get_thread(
    thread_id: str,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: ProviderPlugin = Depends(get_email_provider),
    db: AsyncSession = Depends(get_db)
):
    """
    Get email thread.
    
    Args:
        thread_id: Thread identifier
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Email provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        Email thread data
    """
    start_time = datetime.utcnow()
    
    request_payload = {"thread_id": thread_id}
    
    try:
        result = await provider.execute_with_retry(
            action="get_thread",
            parameters={"thread_id": thread_id}
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="email_read",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data={"message_count": len(result.get("messages", []))},
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Thread retrieved: {thread_id}",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return result
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="email_read",
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
            f"Failed to get thread: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to get thread: {str(e)}",
            original_error=e
        )


@router.get(
    "/messages",
    status_code=status.HTTP_200_OK,
    summary="List email messages",
    description="""
    List email messages with pagination.
    
    This endpoint retrieves a paginated list of email messages.
    """,
    tags=["Email"]
)
async def list_messages(
    max_results: int = Query(default=10, ge=1, le=100),
    page_token: Optional[str] = None,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: ProviderPlugin = Depends(get_email_provider),
    db: AsyncSession = Depends(get_db)
):
    """
    List email messages.
    
    Args:
        max_results: Maximum number of messages to return
        page_token: Page token for pagination
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Email provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        List of email messages
    """
    start_time = datetime.utcnow()
    
    request_payload = {
        "max_results": max_results,
        "page_token": page_token
    }
    
    try:
        result = await provider.execute_with_retry(
            action="list_messages",
            parameters={
                "max_results": max_results,
                "page_token": page_token
            }
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="email_list",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data={"message_count": len(result.get("messages", []))},
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Messages listed: {len(result.get('messages', []))} results",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return result
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="email_list",
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
            f"Failed to list messages: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to list messages: {str(e)}",
            original_error=e
        )


@router.get(
    "/search",
    status_code=status.HTTP_200_OK,
    summary="Search email messages",
    description="""
    Search for email messages matching the given criteria.
    
    This endpoint searches messages by query, sender, recipient, subject, etc.
    """,
    tags=["Email"]
)
async def search_messages(
    query: Optional[str] = None,
    from_email: Optional[str] = None,
    to_email: Optional[str] = None,
    subject: Optional[str] = None,
    max_results: int = Query(default=10, ge=1, le=100),
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: ProviderPlugin = Depends(get_email_provider),
    db: AsyncSession = Depends(get_db)
):
    """
    Search email messages.
    
    Args:
        query: Search query string
        from_email: Filter by sender email
        to_email: Filter by recipient email
        subject: Filter by subject
        max_results: Maximum number of results
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Email provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        Search results
    """
    start_time = datetime.utcnow()
    
    request_payload = {
        "query": query,
        "from_email": from_email,
        "to_email": to_email,
        "subject": subject,
        "max_results": max_results
    }
    
    try:
        result = await provider.execute_with_retry(
            action="search_messages",
            parameters={
                "query": query,
                "from_email": from_email,
                "to_email": to_email,
                "subject": subject,
                "max_results": max_results
            }
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="email_search",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data={"result_count": len(result.get("matches", []))},
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Email search completed: {len(result.get('matches', []))} results",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return result
        
    except Exception as e:
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="email_search",
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
            f"Failed to search emails: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to search emails: {str(e)}",
            original_error=e
        )