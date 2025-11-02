"""
Knowledge API endpoints for the adapter service.

This module provides REST API endpoints for knowledge base operations including
document search, indexing, and management.
"""

from datetime import datetime
from typing import Annotated, Dict, Any, Optional, List

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

# Import schema models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from packages.schema.src.python.knowledge import (
    SearchRequest,
    SearchResponse,
    IndexDocumentRequest,
    ListDocumentsRequest,
    ListDocumentsResponse,
    Document
)

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


async def get_knowledge_provider(
    tenant_id: Annotated[str, Depends(get_tenant_id)]
) -> ProviderPlugin:
    """Get knowledge provider for tenant."""
    registry = get_registry()
    
    # For now, use local knowledge provider as default
    # In production, this would be configured per tenant (vector DB, etc.)
    providers = registry.get_providers_by_type(ProviderType.KNOWLEDGE)
    
    if "local" not in providers:
        raise ProviderException(
            provider="local",
            message="Local knowledge provider not registered"
        )
    
    provider_class = providers["local"]
    
    # In production, get storage path from tenant config
    # For now, use tenant-specific directory
    credentials = {
        "storage_path": f"./data/knowledge/{tenant_id}"
    }
    
    return provider_class(credentials)


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search knowledge base",
    description="""
    Search for documents in the knowledge base.
    
    This endpoint performs full-text search across indexed documents.
    Supports filtering by categories, tags, and other metadata.
    
    **Example Request:**
    ```json
    {
        "query": {
            "text": "How do I reset my password?",
            "filters": {
                "categories": ["authentication", "account"],
                "published_only": true
            },
            "options": {
                "max_results": 5,
                "min_score": 0.7,
                "include_snippets": true
            }
        }
    }
    ```
    """,
    tags=["Knowledge"]
)
async def search_documents(
    query: str,
    max_results: int = Query(default=10, ge=1, le=100),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0),
    categories: Optional[List[str]] = Query(default=None),
    published_only: bool = Query(default=True),
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: ProviderPlugin = Depends(get_knowledge_provider),
    db: AsyncSession = Depends(get_db)
) -> SearchResponse:
    """
    Search knowledge base documents.
    
    Args:
        query: Search query text
        max_results: Maximum number of results to return
        min_score: Minimum relevance score threshold
        categories: Filter by categories
        published_only: Only return published documents
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Knowledge provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        SearchResponse with matching documents
    """
    start_time = datetime.utcnow()
    
    # Validate query
    if not query or len(query.strip()) == 0:
        raise ValidationException(
            message="Search query cannot be empty",
            field="query",
            value=query
        )
    
    request_payload = {
        "query": query,
        "max_results": max_results,
        "min_score": min_score,
        "categories": categories,
        "published_only": published_only
    }
    
    try:
        # Call provider to search documents
        result = await provider.execute_with_retry(
            action="search",
            parameters={
                "query": query,
                "max_results": max_results,
                "min_score": min_score,
                "categories": categories,
                "published_only": published_only
            }
        )
        
        # Build response from provider result
        response = SearchResponse(
            results=result.get("results", []),
            total_results=result.get("total_results", 0),
            query_duration_ms=result.get("query_duration_ms")
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="knowledge_search",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data={"result_count": len(response.results)},
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Knowledge search completed: {len(response.results)} results",
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
            action_type="knowledge_search",
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
            f"Failed to search knowledge base: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to search knowledge base: {str(e)}",
            original_error=e
        )


@router.post(
    "/documents",
    status_code=status.HTTP_201_CREATED,
    summary="Add document to knowledge base",
    description="""
    Add a new document to the knowledge base.
    
    This endpoint indexes a document for search and retrieval.
    Supports markdown content and metadata tagging.
    
    **Example Request:**
    ```json
    {
        "title": "Password Reset Guide",
        "content": "# How to Reset Your Password\\n\\nFollow these steps...",
        "category": "authentication",
        "tags": ["password", "account", "security"],
        "metadata": {
            "author": "docs-team",
            "version": "1.0"
        },
        "published": true
    }
    ```
    """,
    tags=["Knowledge"]
)
async def add_document(
    title: str,
    content: str,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    published: bool = False,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: ProviderPlugin = Depends(get_knowledge_provider),
    db: AsyncSession = Depends(get_db)
):
    """
    Add document to knowledge base.
    
    Args:
        title: Document title
        content: Document content
        category: Document category
        tags: Document tags
        metadata: Additional metadata
        published: Whether document is published
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Knowledge provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        Document creation result
    """
    start_time = datetime.utcnow()
    
    # Validate required fields
    if not title or len(title.strip()) == 0:
        raise ValidationException(
            message="Title is required",
            field="title",
            value=title
        )
    
    if not content or len(content.strip()) == 0:
        raise ValidationException(
            message="Content is required",
            field="content",
            value=content
        )
    
    request_payload = {
        "title": title,
        "content": content,
        "category": category,
        "tags": tags,
        "metadata": metadata,
        "published": published
    }
    
    try:
        # Call provider to add document
        result = await provider.execute_with_retry(
            action="add_document",
            parameters={
                "title": title,
                "content": content,
                "category": category,
                "tags": tags,
                "metadata": metadata,
                "published": published
            }
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log successful action
        await log_action(
            tenant_id=tenant_id,
            action_type="knowledge_create",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=result,
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Document added: {result.get('id')}",
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
            action_type="knowledge_create",
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
            f"Failed to add document: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to add document: {str(e)}",
            original_error=e
        )


@router.put(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Update document in knowledge base",
    description="""
    Update an existing document in the knowledge base.
    
    This endpoint updates document content, metadata, or published status.
    """,
    tags=["Knowledge"]
)
async def update_document(
    document_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    published: Optional[bool] = None,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: ProviderPlugin = Depends(get_knowledge_provider),
    db: AsyncSession = Depends(get_db)
):
    """
    Update document in knowledge base.
    
    Args:
        document_id: Document identifier
        title: Updated title
        content: Updated content
        category: Updated category
        tags: Updated tags
        metadata: Updated metadata
        published: Updated published status
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Knowledge provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        Updated document data
    """
    start_time = datetime.utcnow()
    
    # Validate at least one field is being updated
    if all(v is None for v in [title, content, category, tags, metadata, published]):
        raise ValidationException(
            message="At least one field must be provided for update",
            field="updates",
            value=None
        )
    
    request_payload = {
        "document_id": document_id,
        "title": title,
        "content": content,
        "category": category,
        "tags": tags,
        "metadata": metadata,
        "published": published
    }
    
    try:
        # Call provider to update document
        result = await provider.execute_with_retry(
            action="update_document",
            parameters={
                "document_id": document_id,
                "title": title,
                "content": content,
                "category": category,
                "tags": tags,
                "metadata": metadata,
                "published": published
            }
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="knowledge_update",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=result,
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Document updated: {document_id}",
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
            action_type="knowledge_update",
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
            f"Failed to update document: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to update document: {str(e)}",
            original_error=e
        )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete document from knowledge base",
    description="""
    Delete a document from the knowledge base.
    
    This endpoint removes a document and its index entries.
    """,
    tags=["Knowledge"]
)
async def delete_document(
    document_id: str,
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: ProviderPlugin = Depends(get_knowledge_provider),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete document from knowledge base.
    
    Args:
        document_id: Document identifier
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Knowledge provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        Deletion confirmation
    """
    start_time = datetime.utcnow()
    
    request_payload = {"document_id": document_id}
    
    try:
        # Call provider to delete document
        result = await provider.execute_with_retry(
            action="delete_document",
            parameters={"document_id": document_id}
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="knowledge_delete",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data=result,
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Document deleted: {document_id}",
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
            action_type="knowledge_delete",
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
            f"Failed to delete document: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to delete document: {str(e)}",
            original_error=e
        )


@router.get(
    "/documents",
    response_model=ListDocumentsResponse,
    status_code=status.HTTP_200_OK,
    summary="List documents in knowledge base",
    description="""
    List documents in the knowledge base with filtering and pagination.
    
    This endpoint retrieves a list of documents matching the specified criteria.
    """,
    tags=["Knowledge"]
)
async def list_documents(
    category: Optional[str] = None,
    published_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant_id: Annotated[str, Depends(get_tenant_id)] = None,
    correlation_id: Annotated[str, Depends(get_correlation_id)] = None,
    provider: ProviderPlugin = Depends(get_knowledge_provider),
    db: AsyncSession = Depends(get_db)
) -> ListDocumentsResponse:
    """
    List documents in knowledge base.
    
    Args:
        category: Filter by category
        published_only: Only return published documents
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        tenant_id: Tenant ID (from dependency)
        correlation_id: Correlation ID (from dependency)
        provider: Knowledge provider (from dependency)
        db: Database session (from dependency)
        
    Returns:
        ListDocumentsResponse with documents
    """
    start_time = datetime.utcnow()
    
    request_payload = {
        "category": category,
        "published_only": published_only,
        "limit": limit,
        "offset": offset
    }
    
    try:
        # Call provider to list documents
        result = await provider.execute_with_retry(
            action="list_documents",
            parameters={
                "category": category,
                "published_only": published_only,
                "limit": limit,
                "offset": offset
            }
        )
        
        # Build response
        response = ListDocumentsResponse(
            documents=result.get("documents", []),
            pagination=result.get("pagination")
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        await log_action(
            tenant_id=tenant_id,
            action_type="knowledge_list",
            provider_name=provider.provider_name,
            request_payload=request_payload,
            response_data={"document_count": len(response.documents)},
            status="success",
            execution_time_ms=execution_time_ms,
            metadata={"correlation_id": correlation_id},
            db=db
        )
        
        logger.info(
            f"Documents listed: {len(response.documents)} results",
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
            action_type="knowledge_list",
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
            f"Failed to list documents: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        
        raise ProviderException(
            provider=provider.provider_name,
            message=f"Failed to list documents: {str(e)}",
            original_error=e
        )