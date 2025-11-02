"""
Local file-based knowledge base provider implementation.

This module provides a simple file-based knowledge store using JSON for persistence.
Implements full-text search and document management. Will be replaced with vector DB later.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import json
import os
from pathlib import Path

from .base import KnowledgeProvider
from ..base import (
    ProviderCapability,
    ValidationError,
    NotFoundError,
    ProviderError
)
from ..factory import register_provider, ProviderType
from ...core.logging import get_logger


logger = get_logger(__name__)


@register_provider(ProviderType.KNOWLEDGE, "local")
class LocalKnowledgeProvider(KnowledgeProvider):
    """
    Local file-based knowledge base provider.
    
    Provides document storage with JSON persistence and simple text-based search.
    Suitable for development and testing. Production systems should use vector DB.
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize local knowledge provider.
        
        Args:
            credentials: Provider credentials including:
                - storage_path: Path to store documents (default: ./data/knowledge)
        """
        super().__init__(credentials)
        
        # Set up storage path
        self.storage_path = Path(credentials.get("storage_path", "./data/knowledge"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_path / "index.json"
        
        # Load existing documents
        self._documents = self._load_index()
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "local"
    
    @property
    def supported_capabilities(self) -> List[ProviderCapability]:
        """Return supported capabilities."""
        return [
            ProviderCapability.KNOWLEDGE_SEARCH,
            ProviderCapability.KNOWLEDGE_INDEX
        ]
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load document index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load knowledge index: {e}")
                return {}
        return {}
    
    def _save_index(self):
        """Save document index to disk."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self._documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save knowledge index: {e}")
            raise ProviderError(
                f"Failed to save knowledge index: {str(e)}",
                provider=self.provider_name
            )
    
    async def validate_credentials(self) -> bool:
        """
        Validate credentials (local provider always returns True).
        
        Returns:
            True
        """
        logger.info(f"Local knowledge provider initialized at {self.storage_path}")
        return True
    
    async def execute_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute knowledge base action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            idempotency_key: Optional idempotency key
            
        Returns:
            Action result
        """
        action_map = {
            "search": self.search,
            "index_document": self.index_document,
            "add_document": self.add_document,
            "update_document": self.update_document,
            "delete_document": self.delete_document,
            "get_document": self.get_document,
            "list_documents": self.list_documents
        }
        
        handler = action_map.get(action)
        if not handler:
            raise ValueError(f"Unsupported action: {action}")
        
        # Execute the handler with parameters
        return await handler(**parameters)
    
    def normalize_response(
        self,
        provider_response: Any,
        action: str
    ) -> Dict[str, Any]:
        """Normalize response."""
        return provider_response
    
    async def health_check(self) -> bool:
        """Check provider health."""
        return self.storage_path.exists() and self.storage_path.is_dir()
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        min_score: float = 0.0,
        categories: Optional[List[str]] = None,
        published_only: bool = True
    ) -> Dict[str, Any]:
        """
        Search documents in knowledge base.
        
        Args:
            query: Search query text
            max_results: Maximum number of results
            min_score: Minimum relevance score threshold
            categories: Filter by categories
            published_only: Only return published documents
            
        Returns:
            Dictionary with search results
        """
        search_text = query.lower()
        
        # Search documents
        results = []
        for doc_id, doc in self._documents.items():
            # Filter by published status
            if published_only and not doc.get("published"):
                continue
            
            # Filter by category
            if categories and doc.get("category") not in categories:
                continue
            
            # Calculate simple relevance score based on text matching
            score = 0.0
            title = doc.get("title", "").lower()
            content = doc.get("content", "").lower()
            
            if search_text in title:
                score = 0.95
            elif search_text in content:
                score = 0.75
            else:
                # Check for partial matches
                search_words = search_text.split()
                matches = sum(1 for word in search_words if word in title or word in content)
                if matches > 0:
                    score = 0.5 * (matches / len(search_words))
            
            # Skip if score too low
            if score < min_score:
                continue
            
            # Create snippet
            snippet_start = content.find(search_text)
            if snippet_start >= 0:
                snippet = content[max(0, snippet_start - 50):snippet_start + 150] + "..."
            else:
                snippet = content[:200] + "..." if len(content) > 200 else content
            
            results.append({
                "id": doc_id,
                "title": doc.get("title"),
                "url": f"file://{self.storage_path}/{doc_id}.json",
                "score": score,
                "snippet": snippet,
                "category": doc.get("category"),
                "tags": doc.get("tags"),
                "metadata": {
                    "last_updated": doc.get("updated_at"),
                    "helpful_votes": doc.get("metadata", {}).get("helpful_votes", 0)
                }
            })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:max_results]
        
        return {
            "results": results,
            "total_results": len(results),
            "query_duration_ms": 15
        }
    
    async def index_document(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        published: bool = False
    ) -> Dict[str, Any]:
        """
        Index a document in knowledge base.
        
        Args:
            title: Document title
            content: Document content
            category: Document category
            tags: Document tags
            metadata: Additional metadata
            published: Whether document is published
            
        Returns:
            Dictionary with document data
        """
        # Validate required fields
        if not title:
            raise ValidationError(
                "Title is required for document indexing",
                provider=self.provider_name,
                action="index_document"
            )
        
        if not content:
            raise ValidationError(
                "Content is required for document indexing",
                provider=self.provider_name,
                action="index_document"
            )
        
        # Generate document ID
        doc_id = f"kb_doc_{uuid.uuid4().hex[:12]}"
        
        # Store document
        now = datetime.utcnow().isoformat() + "Z"
        self._documents[doc_id] = {
            "id": doc_id,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags or [],
            "published": published,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now
        }
        
        # Save to disk
        self._save_index()
        
        return {
            "id": doc_id,
            "provider": self.provider_name,
            "provider_id": doc_id,
            "title": title,
            "url": f"file://{self.storage_path}/{doc_id}.json",
            "published": published,
            "created_at": now,
            "updated_at": now
        }
    
    async def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        published: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update document in knowledge base.
        
        Args:
            document_id: Document ID
            title: Updated title
            content: Updated content
            category: Updated category
            tags: Updated tags
            metadata: Updated metadata
            published: Updated published status
            
        Returns:
            Dictionary with updated document data
        """
        if document_id not in self._documents:
            raise NotFoundError(
                f"Document not found: {document_id}",
                provider=self.provider_name
            )
        
        # Update document fields
        doc = self._documents[document_id]
        
        if title is not None:
            doc["title"] = title
        if content is not None:
            doc["content"] = content
        if category is not None:
            doc["category"] = category
        if tags is not None:
            doc["tags"] = tags
        if metadata is not None:
            doc["metadata"] = metadata
        if published is not None:
            doc["published"] = published
        
        doc["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Save to disk
        self._save_index()
        
        return {
            "id": document_id,
            "provider": self.provider_name,
            "provider_id": document_id,
            "title": doc["title"],
            "url": f"file://{self.storage_path}/{document_id}.json",
            "published": doc["published"],
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"]
        }
    
    async def delete_document(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Delete document from knowledge base.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with deletion confirmation
        """
        if document_id not in self._documents:
            raise NotFoundError(
                f"Document not found: {document_id}",
                provider=self.provider_name
            )
        
        # Delete document
        del self._documents[document_id]
        
        # Save to disk
        self._save_index()
        
        return {
            "id": document_id,
            "provider": self.provider_name,
            "provider_id": document_id,
            "deleted": True,
            "deleted_at": datetime.utcnow().isoformat() + "Z"
        }
    
    async def get_document(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Get document from knowledge base.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with document data
        """
        if document_id not in self._documents:
            raise NotFoundError(
                f"Document not found: {document_id}",
                provider=self.provider_name
            )
        
        doc = self._documents[document_id]
        
        return {
            "id": document_id,
            "provider": self.provider_name,
            "provider_id": document_id,
            "title": doc["title"],
            "content": doc["content"],
            "category": doc.get("category"),
            "tags": doc.get("tags", []),
            "published": doc.get("published", False),
            "metadata": doc.get("metadata", {}),
            "url": f"file://{self.storage_path}/{document_id}.json",
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"]
        }
    
    async def list_documents(
        self,
        category: Optional[str] = None,
        published_only: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List documents in knowledge base.
        
        Args:
            category: Filter by category
            published_only: Only return published documents
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            Dictionary with document list
        """
        # Filter documents
        documents = []
        for doc_id, doc in self._documents.items():
            # Filter by published status
            if published_only and not doc.get("published"):
                continue
            
            # Filter by category
            if category and doc.get("category") != category:
                continue
            
            documents.append({
                "id": doc_id,
                "title": doc.get("title"),
                "category": doc.get("category"),
                "tags": doc.get("tags", []),
                "published": doc.get("published"),
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at")
            })
        
        # Apply pagination
        total = len(documents)
        documents = documents[offset:offset + limit]
        
        return {
            "documents": documents,
            "pagination": {
                "total_items": total,
                "has_next": offset + limit < total,
                "has_previous": offset > 0
            }
        }