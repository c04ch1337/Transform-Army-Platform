"""
Knowledge schema models for Transform Army AI Adapter Service.

This module defines Pydantic models for knowledge base operations including
document indexing, searching, and retrieval.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator

from .base import ToolInput, PaginationParams, PaginationResponse


class DocumentMetadata(BaseModel):
    """Metadata for a knowledge base document."""
    
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "author": "John Doe",
                "version": "1.0",
                "language": "en",
                "category": "technical",
                "tags": ["api", "integration"],
                "helpful_votes": 42,
                "unhelpful_votes": 3,
                "view_count": 1250,
                "last_reviewed": "2025-10-31T01:17:00Z"
            }
        }
    )
    
    author: Optional[str] = Field(
        default=None,
        description="Document author"
    )
    version: Optional[str] = Field(
        default=None,
        description="Document version"
    )
    language: str = Field(
        default="en",
        description="Document language code (ISO 639-1)"
    )
    category: Optional[str] = Field(
        default=None,
        description="Document category"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Document tags"
    )
    helpful_votes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of helpful votes"
    )
    unhelpful_votes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of unhelpful votes"
    )
    view_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of views"
    )
    last_reviewed: Optional[datetime] = Field(
        default=None,
        description="Last review date"
    )


class KnowledgeDocument(BaseModel):
    """
    Knowledge base document model.
    
    Represents a document in the knowledge base with content, metadata, and relationships.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "doc_abc123",
                "title": "API Integration Guide",
                "content": "# API Integration\n\nThis guide covers...",
                "url": "https://kb.transform-army.ai/docs/api-integration",
                "category": "technical",
                "tags": ["api", "integration", "guide"],
                "published": True,
                "created_at": "2025-10-15T10:00:00Z",
                "updated_at": "2025-10-31T01:17:00Z",
                "published_at": "2025-10-15T12:00:00Z",
                "metadata": {
                    "author": "John Doe",
                    "version": "1.0"
                }
            }
        }
    )
    
    id: str = Field(description="Unique document identifier")
    title: str = Field(description="Document title")
    content: str = Field(description="Document content (supports markdown)")
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to view document"
    )
    category: Optional[str] = Field(
        default=None,
        description="Document category"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Document tags"
    )
    published: bool = Field(
        default=False,
        description="Whether document is published"
    )
    created_at: datetime = Field(description="Document creation timestamp")
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    published_at: Optional[datetime] = Field(
        default=None,
        description="Publication timestamp"
    )
    metadata: Optional[DocumentMetadata] = Field(
        default=None,
        description="Additional document metadata"
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="Parent document ID (for hierarchical documents)"
    )
    related_ids: Optional[List[str]] = Field(
        default=None,
        description="Related document IDs"
    )


class SearchResult(BaseModel):
    """
    Knowledge base search result with relevance score.
    
    Represents a single document match from a search query.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "doc_abc123",
                "title": "API Integration Guide",
                "url": "https://kb.transform-army.ai/docs/api-integration",
                "score": 0.95,
                "snippet": "This guide covers API integration...",
                "category": "technical",
                "tags": ["api", "integration"],
                "metadata": {
                    "author": "John Doe"
                },
                "highlights": [
                    "API integration with Transform Army AI"
                ]
            }
        }
    )
    
    id: str = Field(description="Document ID")
    title: str = Field(description="Document title")
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to view document"
    )
    score: float = Field(
        ge=0,
        le=1,
        description="Relevance score (0-1)"
    )
    snippet: Optional[str] = Field(
        default=None,
        description="Relevant excerpt from document"
    )
    category: Optional[str] = Field(
        default=None,
        description="Document category"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Document tags"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    highlights: Optional[List[str]] = Field(
        default=None,
        description="Highlighted matching text segments"
    )


class ArticleData(BaseModel):
    """Article data for indexing in the knowledge base."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Getting Started Guide",
                "content": "# Getting Started\n\nWelcome to...",
                "category": "onboarding",
                "tags": ["getting-started", "beginner"],
                "metadata": {
                    "author": "Support Team",
                    "version": "1.0"
                }
            }
        }
    )
    
    title: str = Field(description="Article title")
    content: str = Field(description="Article content (markdown supported)")
    category: Optional[str] = Field(
        default=None,
        description="Article category"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Article tags"
    )
    metadata: Optional[DocumentMetadata] = Field(
        default=None,
        description="Additional metadata"
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="Parent document ID"
    )
    related_ids: Optional[List[str]] = Field(
        default=None,
        description="Related document IDs"
    )


class IndexOptions(BaseModel):
    """Options for document indexing."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "auto_vectorize": True,
                "publish": False,
                "update_if_exists": True
            }
        }
    )
    
    auto_vectorize: bool = Field(
        default=True,
        description="Automatically create vector embeddings"
    )
    publish: bool = Field(
        default=False,
        description="Publish document immediately"
    )
    update_if_exists: bool = Field(
        default=True,
        description="Update document if it already exists"
    )


class IndexDocumentRequest(ToolInput):
    """
    Request to index or update a document in the knowledge base.
    
    Includes options for vectorization and publishing.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_doc123",
                "correlation_id": "cor_req145",
                "article": {
                    "title": "Getting Started Guide",
                    "content": "# Getting Started\n\nWelcome to...",
                    "category": "onboarding",
                    "tags": ["getting-started"]
                },
                "options": {
                    "auto_vectorize": True,
                    "publish": True
                }
            }
        }
    )
    
    article: ArticleData = Field(description="Article data to index")
    options: Optional[IndexOptions] = Field(
        default=None,
        description="Indexing options"
    )


class SearchFilters(BaseModel):
    """Filters for knowledge base search."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categories": ["technical", "api"],
                "tags": ["integration"],
                "languages": ["en"],
                "published_only": True,
                "created_after": "2025-01-01T00:00:00Z"
            }
        }
    )
    
    categories: Optional[List[str]] = Field(
        default=None,
        description="Filter by categories"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags (any match)"
    )
    languages: Optional[List[str]] = Field(
        default=None,
        description="Filter by language codes"
    )
    published_only: bool = Field(
        default=True,
        description="Only return published documents"
    )
    created_after: Optional[datetime] = Field(
        default=None,
        description="Filter documents created after date"
    )
    updated_after: Optional[datetime] = Field(
        default=None,
        description="Filter documents updated after date"
    )


class SearchOptions(BaseModel):
    """Options for knowledge base search."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "max_results": 10,
                "min_score": 0.5,
                "include_snippets": True,
                "highlight_matches": True
            }
        }
    )
    
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )
    min_score: float = Field(
        default=0,
        ge=0,
        le=1,
        description="Minimum relevance score threshold"
    )
    include_snippets: bool = Field(
        default=True,
        description="Include text snippets in results"
    )
    highlight_matches: bool = Field(
        default=False,
        description="Highlight matching text in results"
    )


class SearchQuery(BaseModel):
    """Search query parameters for knowledge base."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "API integration authentication",
                "filters": {
                    "categories": ["technical"],
                    "published_only": True
                },
                "options": {
                    "max_results": 10,
                    "min_score": 0.5
                }
            }
        }
    )
    
    text: str = Field(description="Search query text")
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Search filters"
    )
    options: Optional[SearchOptions] = Field(
        default=None,
        description="Search options"
    )


class SearchRequest(BaseModel):
    """Request to search the knowledge base."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "correlation_id": "cor_req146",
                "query": {
                    "text": "API authentication",
                    "filters": {
                        "categories": ["technical"]
                    }
                }
            }
        }
    )
    
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for request tracing"
    )
    query: SearchQuery = Field(description="Search query")


class SearchResponse(BaseModel):
    """Response from knowledge base search operation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "id": "doc_abc123",
                        "title": "API Integration Guide",
                        "score": 0.95,
                        "snippet": "This guide covers API integration..."
                    }
                ],
                "total_results": 1,
                "query_duration_ms": 45,
                "facets": {
                    "categories": {"technical": 1},
                    "tags": {"api": 1, "integration": 1}
                }
            }
        }
    )
    
    results: List[SearchResult] = Field(description="Search results")
    total_results: int = Field(
        ge=0,
        description="Total number of matching documents"
    )
    query_duration_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Query execution time in milliseconds"
    )
    facets: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Faceted search results (categories, tags, etc.)"
    )


class ListDocumentsRequest(BaseModel):
    """Request to list documents in the knowledge base."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "technical",
                "tags": ["api"],
                "published_only": True,
                "sort_by": "updated_at",
                "sort_order": "desc",
                "pagination": {
                    "page": 1,
                    "page_size": 50
                }
            }
        }
    )
    
    category: Optional[str] = Field(
        default=None,
        description="Filter by category"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags (all must match)"
    )
    published_only: bool = Field(
        default=True,
        description="Only return published documents"
    )
    language: Optional[str] = Field(
        default=None,
        description="Filter by language code"
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="Filter by parent document ID"
    )
    sort_by: str = Field(
        default="updated_at",
        description="Field to sort by (e.g., 'title', 'created_at', 'updated_at')"
    )
    sort_order: str = Field(
        default="desc",
        description="Sort order ('asc' or 'desc')"
    )
    pagination: Optional[PaginationParams] = Field(
        default=None,
        description="Pagination parameters"
    )
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort order value."""
        if v not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v


class ListDocumentsResponse(BaseModel):
    """Response from list documents operation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [
                    {
                        "id": "doc_abc123",
                        "title": "API Integration Guide",
                        "category": "technical",
                        "published": True,
                        "created_at": "2025-10-15T10:00:00Z"
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
    
    documents: List[KnowledgeDocument] = Field(description="List of documents")
    pagination: Optional[PaginationResponse] = Field(
        default=None,
        description="Pagination metadata"
    )


class DocumentAnalytics(BaseModel):
    """Analytics and statistics for a knowledge base document."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "doc_abc123",
                "view_count": 1250,
                "helpful_votes": 42,
                "unhelpful_votes": 3,
                "helpfulness_ratio": 0.933,
                "average_time_on_page_seconds": 125.5,
                "search_appearances": 450,
                "click_through_rate": 0.15,
                "last_viewed": "2025-10-31T01:17:00Z"
            }
        }
    )
    
    document_id: str = Field(description="Document ID")
    view_count: int = Field(
        ge=0,
        description="Total views"
    )
    helpful_votes: int = Field(
        ge=0,
        description="Helpful votes"
    )
    unhelpful_votes: int = Field(
        ge=0,
        description="Unhelpful votes"
    )
    helpfulness_ratio: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Ratio of helpful to total votes"
    )
    average_time_on_page_seconds: Optional[float] = Field(
        default=None,
        ge=0,
        description="Average time spent on document"
    )
    search_appearances: Optional[int] = Field(
        default=None,
        ge=0,
        description="Times document appeared in search results"
    )
    click_through_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Click-through rate from search"
    )
    last_viewed: Optional[datetime] = Field(
        default=None,
        description="Last view timestamp"
    )