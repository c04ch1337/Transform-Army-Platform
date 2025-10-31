"""
Stub knowledge base provider implementation.

This is an in-memory knowledge base that simulates document indexing
and vector search for testing and development purposes.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from ..base import (
    ProviderPlugin,
    ProviderCapability,
    ValidationError,
    NotFoundError
)
from ...core.logging import get_logger


logger = get_logger(__name__)


class StubKnowledgeProvider(ProviderPlugin):
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
            "index_document": self._index_document,
            "update_document": self._update_document,
            "get_document": self._get_document,
            "delete_document": self._delete_document,
            "search_documents": self._search_documents,
            "list_documents": self._list_documents
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
    
    async def _index_document(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Index document in knowledge base."""
        article_data = parameters.get("article", {})
        
        # Validate required fields
        if not article_data.get("title"):
            raise ValidationError(
                "Title is required for document indexing",
                provider=self.provider_name,
                action="index_document"
            )
        
        if not article_data.get("content"):
            raise ValidationError(
                "Content is required for document indexing",
                provider=self.provider_name,
                action="index_document"
            )
        
        # Generate document ID
        doc_id = f"kb_doc_{uuid.uuid4().hex[:12]}"
        
        # Get options
        options = parameters.get("options", {})
        
        # Store document
        self._documents[doc_id] = {
            "id": doc_id,
            "title": article_data.get("title"),
            "content": article_data.get("content"),
            "category": article_data.get("category"),
            "tags": article_data.get("tags", []),
            "published": options.get("publish", False),
            "metadata": article_data.get("metadata", {}),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "id": doc_id,
            "provider": self.provider_name,
            "provider_id": doc_id,
            "data": {
                "title": self._documents[doc_id]["title"],
                "url": f"https://kb.example.com/articles/{doc_id}",
                "published": self._documents[doc_id]["published"],
                "created_at": self._documents[doc_id]["created_at"]
            }
        }
    
    async def _update_document(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Update document in knowledge base."""
        doc_id = parameters.get("document_id")
        updates = parameters.get("updates", {})
        
        if doc_id not in self._documents:
            raise NotFoundError(
                f"Document not found: {doc_id}",
                provider=self.provider_name
            )
        
        # Update document
        self._documents[doc_id].update(updates)
        self._documents[doc_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        return {
            "id": doc_id,
            "provider": self.provider_name,
            "provider_id": doc_id,
            "data": self._documents[doc_id]
        }
    
    async def _get_document(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Get document from knowledge base."""
        doc_id = parameters.get("document_id")
        
        if doc_id not in self._documents:
            raise NotFoundError(
                f"Document not found: {doc_id}",
                provider=self.provider_name
            )
        
        return {
            "id": doc_id,
            "provider": self.provider_name,
            "provider_id": doc_id,
            "data": self._documents[doc_id]
        }
    
    async def _delete_document(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Delete document from knowledge base."""
        doc_id = parameters.get("document_id")
        
        if doc_id not in self._documents:
            raise NotFoundError(
                f"Document not found: {doc_id}",
                provider=self.provider_name
            )
        
        # Delete document
        del self._documents[doc_id]
        
        return {
            "id": doc_id,
            "provider": self.provider_name,
            "provider_id": doc_id,
            "deleted": True
        }
    
    async def _search_documents(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Search documents in knowledge base."""
        query = parameters.get("query", {})
        search_text = query.get("text", "").lower()
        filters = query.get("filters", {})
        options = query.get("options", {})
        
        # Get search parameters
        max_results = options.get("max_results", 10)
        min_score = options.get("min_score", 0.0)
        categories = filters.get("categories", [])
        published_only = filters.get("published_only", True)
        
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
    
    async def _list_documents(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """List documents in knowledge base."""
        category = parameters.get("category")
        published_only = parameters.get("published_only", True)
        
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