"""
Base knowledge provider interface defining the contract for knowledge providers.

This module defines the abstract base class that all knowledge provider implementations
must inherit from, ensuring consistent interfaces across different knowledge providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..base import ProviderPlugin, ProviderCapability


class KnowledgeProvider(ProviderPlugin):
    """
    Abstract base class for knowledge providers.
    
    Defines the interface for knowledge operations like document indexing,
    searching, and management.
    """
    
    @abstractmethod
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
        Index a document in the knowledge base.
        
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
        pass
    
    @abstractmethod
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
        Update a document in the knowledge base.
        
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
        pass
    
    @abstractmethod
    async def get_document(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Get a document from the knowledge base.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with document data
        """
        pass
    
    @abstractmethod
    async def delete_document(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Delete a document from the knowledge base.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with deletion confirmation
        """
        pass
    
    @abstractmethod
    async def search_documents(
        self,
        query: str,
        max_results: int = 10,
        min_score: float = 0.0,
        categories: Optional[List[str]] = None,
        published_only: bool = True
    ) -> Dict[str, Any]:
        """
        Search documents in the knowledge base.
        
        Args:
            query: Search query text
            max_results: Maximum number of results
            min_score: Minimum relevance score threshold
            categories: Filter by categories
            published_only: Only return published documents
            
        Returns:
            Dictionary with search results
        """
        pass
    
    @abstractmethod
    async def list_documents(
        self,
        category: Optional[str] = None,
        published_only: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List documents in the knowledge base.
        
        Args:
            category: Filter by category
            published_only: Only return published documents
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            Dictionary with document list
        """
        pass
    
    async def add_document(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        published: bool = False
    ) -> Dict[str, Any]:
        """
        Add a document to the knowledge base (alias for index_document).
        
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
        return await self.index_document(
            title=title,
            content=content,
            category=category,
            tags=tags,
            metadata=metadata,
            published=published
        )
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        min_score: float = 0.0,
        categories: Optional[List[str]] = None,
        published_only: bool = True
    ) -> Dict[str, Any]:
        """
        Search documents in the knowledge base (alias for search_documents).
        
        Args:
            query: Search query text
            max_results: Maximum number of results
            min_score: Minimum relevance score threshold
            categories: Filter by categories
            published_only: Only return published documents
            
        Returns:
            Dictionary with search results
        """
        return await self.search_documents(
            query=query,
            max_results=max_results,
            min_score=min_score,
            categories=categories,
            published_only=published_only
        )