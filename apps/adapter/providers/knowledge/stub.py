"""
Stub knowledge base provider implementation.

This is an in-memory knowledge base that simulates document indexing
and vector search for testing and development purposes.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from .base import KnowledgeProvider
from ..base import (
    ProviderCapability,
    ValidationError,
    NotFoundError
)
from ..factory import register_provider, ProviderType
from ...core.logging import get_logger


logger = get_logger(__name__)


@register_provider(ProviderType.KNOWLEDGE, "stub")
class StubKnowledgeProvider(KnowledgeProvider):
    """
    Stub knowledge base provider implementation.
    
    Provides in-memory document storage and simple text-based search.
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize stub knowledge provider.
        
        Args:
            credentials: Provider credentials (not required for stub)
        """
        super().__init__(credentials)
        self._documents = {}
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "stub"
    
    @property
    def supported_capabilities(self) -> List[ProviderCapability]:
        """Return supported capabilities."""
        return [
            ProviderCapability.KNOWLEDGE_SEARCH,
            ProviderCapability.KNOWLEDGE_INDEX
        ]
    
    async def validate_credentials(self) -> bool:
        """
        Validate credentials (stub always returns True).
        
        Returns:
            True
        """
        logger.info("Stub knowledge provider credentials validated")
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
            "index_document": self.index_document,
            "update_document": self.update_document,
            "get_document": self.get_document,
            "delete_document": self.delete_document,
            "search_documents": self.search_documents,
            "list_documents": self.list_documents
        }
        
        handler = action_map.get(action)
        if not handler:
            raise ValueError(f"Unsupported action: {action}")
        
        return await handler(parameters, idempotency_key)
    
    def normalize_response(
        self,
        provider_response: Any,
        action: str
    ) -> Dict[str, Any]:
        """Normalize response."""
        return provider_response
    
    async def health_check(self) -> bool:
        """Check provider health (stub always returns True)."""
        return True
    
    async def index_document(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        published: bool = False
    ) -> Dict[str, Any]:
        """Index document in knowledge base."""
        
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
        self._documents[doc_id] = {
            "id": doc_id,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags or [],
            "published": published,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "id": doc_id,
            "provider": self.provider_name,
            "provider_id": doc_id,
            "title": title,
            "url": f"https://kb.example.com/articles/{doc_id}",
            "published": published,
            "created_at": self._documents[doc_id]["created_at"],
            "updated_at": self._documents[doc_id]["updated_at"]
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
        """Update document in knowledge base."""
        
        if document_id not in self._documents:
            raise NotFoundError(
                f"Document not found: {document_id}",
                provider=self.provider_name
            )
        
        # Update document
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
        
        return {
            "id": document_id,
            "provider": self.provider_name,
            "provider_id": document_id,
            "title": doc["title"],
            "content": doc["content"],
            "category": doc.get("category"),
            "tags": doc.get("tags", []),
            "published": doc.get("published"),
            "metadata": doc.get("metadata", {}),
            "url": f"https://kb.example.com/articles/{document_id}",
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"]
        }
    
    async def get_document(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """Get document from knowledge base."""
        
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
            "published": doc.get("published"),
            "metadata": doc.get("metadata", {}),
            "url": f"https://kb.example.com/articles/{document_id}",
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"]
        }
    
    async def delete_document(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """Delete document from knowledge base."""
        
        if document_id not in self._documents:
            raise NotFoundError(
                f"Document not found: {document_id}",
                provider=self.provider_name
            )
        
        # Delete document
        del self._documents[document_id]
        
        return {
            "id": document_id,
            "provider": self.provider_name,
            "provider_id": document_id,
            "deleted": True,
            "deleted_at": datetime.utcnow().isoformat() + "Z"
        }
    
    async def search_documents(
        self,
        query: str,
        max_results: int = 10,
        min_score: float = 0.0,
        categories: Optional[List[str]] = None,
        published_only: bool = True
    ) -> Dict[str, Any]:
        """Search documents in knowledge base."""
        search_text = query.lower()
        
        # Get search parameters
        categories = categories or []
        
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
                "url": f"https://kb.example.com/articles/{doc_id}",
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
            "query_duration_ms": 25
        }
    
    async def list_documents(
        self,
        category: Optional[str] = None,
        published_only: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List documents in knowledge base."""
        
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
                "published": doc.get("published"),
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at")
            })
        
        return {
            "documents": documents,
            "pagination": {
                "total_items": len(documents),
                "has_next": False
            }
        }