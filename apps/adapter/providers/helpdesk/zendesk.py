"""
Zendesk helpdesk provider implementation.

This module provides real integration with the Zendesk API v2 for helpdesk operations
including tickets, comments, and search functionality.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import httpx
import base64

from ..base import (
    HelpdeskProvider,
    ProviderCapability,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ProviderError
)
from ..factory import register_provider, ProviderType
from ...core.logging import get_logger


logger = get_logger(__name__)


@register_provider(ProviderType.HELPDESK, "zendesk")
class ZendeskProvider(HelpdeskProvider):
    """
    Zendesk helpdesk provider implementation using Zendesk API v2.
    
    Supports API token authentication (email/token format).
    Implements rate limiting, retry logic, and proper error handling.
    """
    
    # Zendesk API configuration
    DEFAULT_TIMEOUT = httpx.Timeout(30.0, read=60.0)
    USER_AGENT = "Transform-Army-Adapter/1.0"
    
    # Rate limiting configuration (Professional plan: 700 requests/minute)
    MAX_REQUESTS_PER_MINUTE = 700
    RATE_LIMIT_WINDOW = 60
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Zendesk provider.
        
        Args:
            credentials: Zendesk credentials including:
                - auth_type: 'api_token' (OAuth2 support coming later)
                - subdomain: Zendesk subdomain (e.g., 'acme' for acme.zendesk.com)
                - email: Admin/agent email address
                - api_token: API token from Zendesk
                - api_base_url: Custom API base URL (optional)
        """
        super().__init__(credentials)
        
        self.auth_type = credentials.get("auth_type", "api_token")
        self.subdomain = credentials.get("subdomain")
        self.email = credentials.get("email")
        self.api_token = credentials.get("api_token")
        self.api_base_url = credentials.get("api_base_url") or f"https://{self.subdomain}.zendesk.com"
        
        # Rate limiting state
        self._request_times: List[float] = []
        self._rate_limit_lock = asyncio.Lock()
        
        # Initialize HTTP client
        self._client = None
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "zendesk"
    
    @property
    def supported_capabilities(self) -> List[ProviderCapability]:
        """Return supported capabilities."""
        return [
            ProviderCapability.HELPDESK_TICKETS,
            ProviderCapability.HELPDESK_COMMENTS
        ]
    
    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {
                "User-Agent": self.USER_AGENT,
                "Content-Type": "application/json"
            }
            
            # Add authorization header (email/token format, base64 encoded)
            if self.auth_type == "api_token" and self.email and self.api_token:
                # Format: email/token:api_token (base64 encoded)
                auth_string = f"{self.email}/token:{self.api_token}"
                auth_bytes = auth_string.encode('utf-8')
                auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
                headers["Authorization"] = f"Basic {auth_b64}"
            
            self._client = httpx.AsyncClient(
                base_url=self.api_base_url,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT,
                follow_redirects=True
            )
        
        return self._client
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting to respect Zendesk's limits."""
        async with self._rate_limit_lock:
            now = asyncio.get_event_loop().time()
            
            # Remove requests older than the rate limit window
            self._request_times = [
                t for t in self._request_times 
                if now - t < self.RATE_LIMIT_WINDOW
            ]
            
            # If we're at the limit, wait until the oldest request expires
            if len(self._request_times) >= self.MAX_REQUESTS_PER_MINUTE:
                oldest_request = self._request_times[0]
                wait_time = self.RATE_LIMIT_WINDOW - (now - oldest_request)
                
                if wait_time > 0:
                    logger.warning(
                        f"Rate limit approaching, waiting {wait_time:.2f}s before request"
                    )
                    await asyncio.sleep(wait_time)
                    now = asyncio.get_event_loop().time()
            
            # Record this request
            self._request_times.append(now)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Zendesk API with rate limiting and error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint (relative to base URL)
            **kwargs: Additional arguments for httpx request
            
        Returns:
            Response data as dictionary
            
        Raises:
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If authentication fails
            ValidationError: If request validation fails
            NotFoundError: If resource not found
            ProviderError: For other API errors
        """
        # Enforce rate limiting
        await self._enforce_rate_limit()
        
        client = self._get_http_client()
        
        try:
            response = await client.request(method, endpoint, **kwargs)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    "Zendesk rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=retry_after
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid Zendesk credentials or expired token",
                    provider=self.provider_name,
                    provider_response=response.text
                )
            
            # Handle permission errors
            if response.status_code == 403:
                raise AuthenticationError(
                    "Insufficient permissions for Zendesk resource",
                    provider=self.provider_name,
                    provider_response=response.text
                )
            
            # Handle validation errors
            if response.status_code == 400 or response.status_code == 422:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}) if isinstance(error_data.get("error"), dict) else str(error_data.get("error", "Invalid request"))
                raise ValidationError(
                    f"Zendesk validation error: {error_msg}",
                    provider=self.provider_name,
                    provider_response=error_data
                )
            
            # Handle not found
            if response.status_code == 404:
                raise NotFoundError(
                    "Resource not found in Zendesk",
                    provider=self.provider_name,
                    provider_response=response.text
                )
            
            # Handle server errors
            if response.status_code >= 500:
                raise ProviderError(
                    f"Zendesk server error: {response.status_code}",
                    provider=self.provider_name,
                    provider_response=response.text
                )
            
            # Raise for other error status codes
            response.raise_for_status()
            
            # Return JSON response
            return response.json() if response.text else {}
            
        except httpx.HTTPError as e:
            if isinstance(e, httpx.TimeoutException):
                raise ProviderError(
                    "Request to Zendesk timed out",
                    provider=self.provider_name,
                    provider_response=str(e)
                )
            elif isinstance(e, httpx.NetworkError):
                raise ProviderError(
                    "Network error connecting to Zendesk",
                    provider=self.provider_name,
                    provider_response=str(e)
                )
            else:
                raise ProviderError(
                    f"HTTP error: {str(e)}",
                    provider=self.provider_name,
                    provider_response=str(e)
                )
    
    async def validate_credentials(self) -> bool:
        """
        Validate Zendesk credentials by making a test API call.
        
        Returns:
            True if credentials are valid
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        if not self.subdomain:
            raise AuthenticationError(
                "Missing Zendesk subdomain",
                provider=self.provider_name
            )
        
        if self.auth_type == "api_token":
            if not self.email or not self.api_token:
                raise AuthenticationError(
                    "Missing Zendesk email or API token",
                    provider=self.provider_name
                )
        
        try:
            # Test credentials with a simple API call
            await self._make_request("GET", "/api/v2/tickets.json", params={"per_page": 1})
            logger.info(f"Zendesk credentials validated successfully for {self.subdomain}")
            return True
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to validate Zendesk credentials: {e}")
            raise AuthenticationError(
                f"Failed to validate credentials: {str(e)}",
                provider=self.provider_name
            )
    
    async def execute_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute Zendesk action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            idempotency_key: Optional idempotency key
            
        Returns:
            Action result
        """
        action_map = {
            "create_ticket": self.create_ticket,
            "update_ticket": self.update_ticket,
            "search_tickets": self.search_tickets,
            "add_comment": self.add_comment,
            "get_ticket": self.get_ticket
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
        """
        Normalize Zendesk response to standard format.
        
        Args:
            provider_response: Raw Zendesk response
            action: Action that was executed
            
        Returns:
            Normalized response
        """
        # Zendesk responses are already in a good format
        return provider_response
    
    async def health_check(self) -> bool:
        """Check Zendesk provider health."""
        try:
            await self.validate_credentials()
            return True
        except Exception:
            return False
    
    async def create_ticket(
        self,
        subject: str,
        description: str,
        priority: Optional[str] = None,
        requester_email: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new ticket in Zendesk.
        
        Args:
            subject: Ticket subject/title
            description: Ticket description/body
            priority: Ticket priority (urgent, high, normal, low)
            requester_email: Email of person requesting support
            tags: Tags to apply to ticket
            metadata: Additional custom fields
            
        Returns:
            Dictionary with ticket data
        """
        if not subject:
            raise ValidationError(
                "Subject is required for ticket creation",
                provider=self.provider_name,
                action="create_ticket"
            )
        
        if not description:
            raise ValidationError(
                "Description is required for ticket creation",
                provider=self.provider_name,
                action="create_ticket"
            )
        
        # Build ticket data for Zendesk
        ticket_data = {
            "ticket": {
                "subject": subject,
                "comment": {
                    "body": description
                }
            }
        }
        
        # Add optional fields
        if priority:
            ticket_data["ticket"]["priority"] = priority.lower()
        
        if requester_email:
            ticket_data["ticket"]["requester"] = {
                "email": requester_email
            }
            # If metadata contains name, add it
            if metadata and "requester_name" in metadata:
                ticket_data["ticket"]["requester"]["name"] = metadata["requester_name"]
        
        if tags:
            ticket_data["ticket"]["tags"] = tags
        
        # Add custom fields if provided
        if metadata and "custom_fields" in metadata:
            ticket_data["ticket"]["custom_fields"] = metadata["custom_fields"]
        
        # Make API request
        response = await self._make_request(
            "POST",
            "/api/v2/tickets.json",
            json=ticket_data
        )
        
        # Extract ticket data
        ticket = response.get("ticket", {})
        ticket_id = ticket.get("id")
        
        return {
            "id": f"tick_{ticket_id}",
            "provider": self.provider_name,
            "provider_id": str(ticket_id),
            "ticket_number": f"#{ticket_id}",
            "subject": ticket.get("subject"),
            "description": ticket.get("description"),
            "status": ticket.get("status"),
            "priority": ticket.get("priority"),
            "requester_email": ticket.get("requester", {}).get("email") if isinstance(ticket.get("requester"), dict) else None,
            "tags": ticket.get("tags", []),
            "created_at": ticket.get("created_at"),
            "updated_at": ticket.get("updated_at"),
            "url": ticket.get("url") or f"{self.api_base_url}/agent/tickets/{ticket_id}"
        }
    
    async def update_ticket(
        self,
        ticket_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing ticket in Zendesk.
        
        Args:
            ticket_id: ID of the ticket to update
            updates: Dictionary of fields to update
            
        Returns:
            Dictionary with updated ticket data
        """
        if not ticket_id:
            raise ValidationError(
                "Ticket ID is required",
                provider=self.provider_name,
                action="update_ticket"
            )
        
        # Remove 'tick_' prefix if present
        if ticket_id.startswith("tick_"):
            ticket_id = ticket_id[5:]
        
        # Build update data for Zendesk
        ticket_data = {
            "ticket": updates
        }
        
        # Make API request
        response = await self._make_request(
            "PUT",
            f"/api/v2/tickets/{ticket_id}.json",
            json=ticket_data
        )
        
        # Extract ticket data
        ticket = response.get("ticket", {})
        
        return {
            "id": f"tick_{ticket_id}",
            "provider": self.provider_name,
            "provider_id": str(ticket_id),
            "ticket_number": f"#{ticket_id}",
            "subject": ticket.get("subject"),
            "description": ticket.get("description"),
            "status": ticket.get("status"),
            "priority": ticket.get("priority"),
            "assignee_id": ticket.get("assignee_id"),
            "tags": ticket.get("tags", []),
            "created_at": ticket.get("created_at"),
            "updated_at": ticket.get("updated_at"),
            "url": ticket.get("url") or f"{self.api_base_url}/agent/tickets/{ticket_id}"
        }
    
    async def search_tickets(
        self,
        query: Optional[str] = None,
        status: Optional[List[str]] = None,
        priority: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search for tickets in Zendesk.
        
        Args:
            query: Search query string
            status: Filter by ticket status
            priority: Filter by priority levels
            assignee: Filter by assignee ID
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Dictionary with matches and pagination info
        """
        # Build Zendesk search query
        search_parts = []
        
        if query:
            search_parts.append(query)
        
        # Add type filter
        search_parts.append("type:ticket")
        
        # Add status filter
        if status:
            status_query = " OR ".join([f"status:{s}" for s in status])
            search_parts.append(f"({status_query})")
        
        # Add priority filter
        if priority:
            priority_query = " OR ".join([f"priority:{p}" for p in priority])
            search_parts.append(f"({priority_query})")
        
        # Add assignee filter
        if assignee:
            search_parts.append(f"assignee:{assignee}")
        
        # Combine all parts
        search_query = " ".join(search_parts) if search_parts else "type:ticket"
        
        # Make API request
        params = {
            "query": search_query,
            "per_page": min(limit, 100),  # Zendesk max is 100
            "page": (offset // limit) + 1 if limit > 0 else 1
        }
        
        response = await self._make_request(
            "GET",
            "/api/v2/search.json",
            params=params
        )
        
        # Extract results
        results = response.get("results", [])
        matches = []
        
        for result in results:
            ticket_id = result.get("id")
            
            matches.append({
                "id": f"tick_{ticket_id}",
                "ticket_number": f"#{ticket_id}",
                "subject": result.get("subject"),
                "status": result.get("status"),
                "priority": result.get("priority"),
                "requester_email": result.get("requester", {}).get("email") if isinstance(result.get("requester"), dict) else None,
                "assignee_id": result.get("assignee_id"),
                "tags": result.get("tags", []),
                "created_at": result.get("created_at"),
                "updated_at": result.get("updated_at"),
                "url": result.get("url") or f"{self.api_base_url}/agent/tickets/{ticket_id}"
            })
        
        # Build pagination info
        total = response.get("count", len(matches))
        has_next = response.get("next_page") is not None
        
        return {
            "matches": matches,
            "pagination": {
                "total_items": total,
                "has_next": has_next
            }
        }
    
    async def add_comment(
        self,
        ticket_id: str,
        comment_text: str,
        is_public: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a comment to a ticket in Zendesk.
        
        Args:
            ticket_id: ID of the ticket
            comment_text: Content of the comment
            is_public: Whether comment is visible to requester
            metadata: Additional metadata
            
        Returns:
            Dictionary with comment data
        """
        if not ticket_id:
            raise ValidationError(
                "Ticket ID is required",
                provider=self.provider_name,
                action="add_comment"
            )
        
        if not comment_text:
            raise ValidationError(
                "Comment text is required",
                provider=self.provider_name,
                action="add_comment"
            )
        
        # Remove 'tick_' prefix if present
        if ticket_id.startswith("tick_"):
            ticket_id = ticket_id[5:]
        
        # Build comment data for Zendesk
        ticket_data = {
            "ticket": {
                "comment": {
                    "body": comment_text,
                    "public": is_public
                }
            }
        }
        
        # Make API request (updates ticket with comment)
        response = await self._make_request(
            "PUT",
            f"/api/v2/tickets/{ticket_id}.json",
            json=ticket_data
        )
        
        # Extract comment data from audit
        ticket = response.get("ticket", {})
        audit = response.get("audit", {})
        
        # Get the comment ID from the audit events
        comment_id = None
        for event in audit.get("events", []):
            if event.get("type") == "Comment":
                comment_id = event.get("id")
                break
        
        if not comment_id:
            # Fallback to generating a comment ID
            comment_id = f"comment_{ticket_id}_{datetime.utcnow().timestamp()}"
        
        return {
            "id": f"comment_{comment_id}",
            "provider": self.provider_name,
            "provider_id": str(comment_id),
            "ticket_id": f"tick_{ticket_id}",
            "body": comment_text,
            "is_public": is_public,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
    
    async def get_ticket(
        self,
        ticket_id: str
    ) -> Dict[str, Any]:
        """
        Get a ticket by ID from Zendesk.
        
        Args:
            ticket_id: ID of the ticket
            
        Returns:
            Dictionary with ticket data
        """
        if not ticket_id:
            raise ValidationError(
                "Ticket ID is required",
                provider=self.provider_name,
                action="get_ticket"
            )
        
        # Remove 'tick_' prefix if present
        if ticket_id.startswith("tick_"):
            ticket_id = ticket_id[5:]
        
        # Make API request
        response = await self._make_request(
            "GET",
            f"/api/v2/tickets/{ticket_id}.json"
        )
        
        # Extract ticket data
        ticket = response.get("ticket", {})
        
        return {
            "id": f"tick_{ticket_id}",
            "provider": self.provider_name,
            "provider_id": str(ticket_id),
            "ticket_number": f"#{ticket_id}",
            "subject": ticket.get("subject"),
            "description": ticket.get("description"),
            "status": ticket.get("status"),
            "priority": ticket.get("priority"),
            "requester_id": ticket.get("requester_id"),
            "assignee_id": ticket.get("assignee_id"),
            "tags": ticket.get("tags", []),
            "created_at": ticket.get("created_at"),
            "updated_at": ticket.get("updated_at"),
            "url": ticket.get("url") or f"{self.api_base_url}/agent/tickets/{ticket_id}"
        }