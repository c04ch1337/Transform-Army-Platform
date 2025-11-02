"""
Gmail email provider implementation.

This module provides real integration with the Gmail API v1 for email operations
including sending emails, searching messages, and managing threads.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import httpx
import base64
import json

from ..base import (
    ProviderPlugin,
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


@register_provider(ProviderType.EMAIL, "gmail")
class GmailProvider(ProviderPlugin):
    """
    Gmail provider implementation using Gmail API v1.
    
    Supports OAuth2 authentication with automatic token refresh.
    Implements rate limiting (1000 requests/day default), retry logic, and proper error handling.
    """
    
    # Gmail API configuration
    DEFAULT_API_BASE = "https://gmail.googleapis.com"
    DEFAULT_TIMEOUT = httpx.Timeout(30.0, read=60.0)
    USER_AGENT = "Transform-Army-Adapter/1.0"
    
    # Rate limiting configuration (1000 requests/day ~ 0.01 requests/second conservative)
    MAX_REQUESTS_PER_SECOND = 5
    RATE_LIMIT_WINDOW = 1
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Gmail provider.
        
        Args:
            credentials: Gmail credentials including:
                - auth_type: 'oauth2' (default)
                - access_token: OAuth2 access token
                - refresh_token: OAuth2 refresh token
                - client_id: OAuth2 client ID
                - client_secret: OAuth2 client secret
                - token_uri: Token refresh URI (default: https://oauth2.googleapis.com/token)
                - user_email: User's email address (default: 'me')
        """
        super().__init__(credentials)
        
        self.auth_type = credentials.get("auth_type", "oauth2")
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.token_uri = credentials.get("token_uri", "https://oauth2.googleapis.com/token")
        self.user_email = credentials.get("user_email", "me")
        self.api_base_url = credentials.get("api_base_url", self.DEFAULT_API_BASE)
        
        # Rate limiting state
        self._request_times: List[float] = []
        self._rate_limit_lock = asyncio.Lock()
        
        # Initialize HTTP client
        self._client = None
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "gmail"
    
    @property
    def supported_capabilities(self) -> List[ProviderCapability]:
        """Return supported capabilities."""
        return [
            ProviderCapability.EMAIL_SEND,
            ProviderCapability.EMAIL_SEARCH
        ]
    
    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {
                "User-Agent": self.USER_AGENT,
                "Content-Type": "application/json"
            }
            
            # Add authorization header
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            
            self._client = httpx.AsyncClient(
                base_url=self.api_base_url,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT,
                follow_redirects=True
            )
        
        return self._client
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting to respect Gmail's limits."""
        async with self._rate_limit_lock:
            now = asyncio.get_event_loop().time()
            
            # Remove requests older than the rate limit window
            self._request_times = [
                t for t in self._request_times 
                if now - t < self.RATE_LIMIT_WINDOW
            ]
            
            # If we're at the limit, wait until the oldest request expires
            if len(self._request_times) >= self.MAX_REQUESTS_PER_SECOND:
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
    
    async def _refresh_token(self):
        """
        Refresh OAuth2 access token using refresh token.
        
        Raises:
            AuthenticationError: If token refresh fails
        """
        if not self.refresh_token:
            raise AuthenticationError(
                "No refresh token available for token refresh",
                provider=self.provider_name
            )
        
        try:
            # Create a separate client for token refresh
            async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
                response = await client.post(
                    self.token_uri,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": self.refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                
                if response.status_code != 200:
                    raise AuthenticationError(
                        f"Token refresh failed: {response.text}",
                        provider=self.provider_name
                    )
                
                data = response.json()
                self.access_token = data["access_token"]
                
                # Update client headers with new token
                if self._client:
                    self._client.headers["Authorization"] = f"Bearer {self.access_token}"
                
                logger.info("OAuth2 access token refreshed successfully")
                
        except Exception as e:
            logger.error(f"Failed to refresh OAuth2 token: {e}")
            raise AuthenticationError(
                f"Token refresh failed: {str(e)}",
                provider=self.provider_name
            )
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Gmail API with rate limiting and error handling.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
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
                    "Gmail rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=retry_after
                )
            
            # Handle authentication errors - may need token refresh
            if response.status_code == 401:
                error_data = response.json() if response.text else {}
                error_message = error_data.get("error", {}).get("message", "")
                
                # Try to refresh token if it's expired
                if "invalid" in error_message.lower() or "expired" in error_message.lower():
                    logger.info("Access token expired, attempting refresh")
                    await self._refresh_token()
                    
                    # Retry the request with new token
                    response = await client.request(method, endpoint, **kwargs)
                    
                    if response.status_code == 401:
                        raise AuthenticationError(
                            "Invalid Gmail credentials after token refresh",
                            provider=self.provider_name,
                            provider_response=response.text
                        )
                else:
                    raise AuthenticationError(
                        "Invalid Gmail credentials",
                        provider=self.provider_name,
                        provider_response=response.text
                    )
            
            # Handle permission errors
            if response.status_code == 403:
                error_data = response.json() if response.text else {}
                raise AuthenticationError(
                    f"Insufficient permissions: {error_data.get('error', {}).get('message', 'Access denied')}",
                    provider=self.provider_name,
                    provider_response=error_data
                )
            
            # Handle validation errors
            if response.status_code == 400:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Invalid request")
                raise ValidationError(
                    f"Gmail validation error: {error_msg}",
                    provider=self.provider_name,
                    provider_response=error_data
                )
            
            # Handle not found
            if response.status_code == 404:
                raise NotFoundError(
                    "Resource not found in Gmail",
                    provider=self.provider_name,
                    provider_response=response.text
                )
            
            # Handle server errors
            if response.status_code >= 500:
                raise ProviderError(
                    f"Gmail server error: {response.status_code}",
                    provider=self.provider_name,
                    provider_response=response.text
                )
            
            # Raise for other error status codes
            response.raise_for_status()
            
            # Return JSON response (or empty dict for 204 No Content)
            return response.json() if response.text else {}
            
        except httpx.HTTPError as e:
            if isinstance(e, httpx.TimeoutException):
                raise ProviderError(
                    "Request to Gmail timed out",
                    provider=self.provider_name,
                    provider_response=str(e)
                )
            elif isinstance(e, httpx.NetworkError):
                raise ProviderError(
                    "Network error connecting to Gmail",
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
        Validate Gmail credentials by making a test API call.
        
        Returns:
            True if credentials are valid
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        if self.auth_type == "oauth2" and not self.access_token:
            raise AuthenticationError(
                "Missing OAuth2 access token",
                provider=self.provider_name
            )
        
        if not self.client_id or not self.client_secret:
            raise AuthenticationError(
                "Missing OAuth2 client credentials",
                provider=self.provider_name
            )
        
        try:
            # Test credentials with a simple API call
            await self._make_request(
                "GET",
                f"/gmail/v1/users/{self.user_email}/profile"
            )
            logger.info(f"Gmail credentials validated successfully")
            return True
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to validate Gmail credentials: {e}")
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
        Execute Gmail action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            idempotency_key: Optional idempotency key
            
        Returns:
            Action result
        """
        action_map = {
            "send_email": self.send_email,
            "get_thread": self.get_thread,
            "list_messages": self.list_messages,
            "search_messages": self.search_messages
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
        Normalize Gmail response to standard format.
        
        Args:
            provider_response: Raw Gmail response
            action: Action that was executed
            
        Returns:
            Normalized response
        """
        return provider_response
    
    async def health_check(self) -> bool:
        """Check Gmail provider health."""
        try:
            await self.validate_credentials()
            return True
        except Exception:
            return False
    
    def _create_mime_message(self, email_data: Dict[str, Any]) -> str:
        """
        Create MIME message for Gmail API.
        
        Args:
            email_data: Email data including from, to, subject, body
            
        Returns:
            Base64-encoded MIME message
        """
        from_addr = email_data.get("from", {})
        to_addrs = email_data.get("to", [])
        cc_addrs = email_data.get("cc", [])
        subject = email_data.get("subject", "")
        body = email_data.get("body", {})
        
        # Build MIME message
        lines = []
        
        # From header
        if isinstance(from_addr, dict):
            from_email = from_addr.get("email", "")
            from_name = from_addr.get("name")
            if from_name:
                lines.append(f"From: {from_name} <{from_email}>")
            else:
                lines.append(f"From: {from_email}")
        
        # To header
        to_list = []
        for addr in to_addrs:
            if isinstance(addr, dict):
                email = addr.get("email", "")
                name = addr.get("name")
                if name:
                    to_list.append(f"{name} <{email}>")
                else:
                    to_list.append(email)
            else:
                to_list.append(addr)
        lines.append(f"To: {', '.join(to_list)}")
        
        # CC header
        if cc_addrs:
            cc_list = []
            for addr in cc_addrs:
                if isinstance(addr, dict):
                    email = addr.get("email", "")
                    name = addr.get("name")
                    if name:
                        cc_list.append(f"{name} <{email}>")
                    else:
                        cc_list.append(email)
                else:
                    cc_list.append(addr)
            lines.append(f"Cc: {', '.join(cc_list)}")
        
        # Subject
        lines.append(f"Subject: {subject}")
        lines.append("MIME-Version: 1.0")
        lines.append("Content-Type: text/plain; charset=utf-8")
        lines.append("")  # Empty line between headers and body
        
        # Body
        body_text = body.get("text", "") if isinstance(body, dict) else str(body)
        lines.append(body_text)
        
        # Encode to base64
        message = "\r\n".join(lines)
        encoded = base64.urlsafe_b64encode(message.encode()).decode()
        
        return encoded
    
    async def send_email(
        self,
        email: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send email via Gmail API.
        
        Args:
            email: Email data (from, to, subject, body)
            options: Optional send options
            
        Returns:
            Dictionary with sent email info
        """
        # Validate required fields
        if not email.get("to"):
            raise ValidationError(
                "To address is required for email",
                provider=self.provider_name,
                action="send_email"
            )
        
        if not email.get("subject"):
            raise ValidationError(
                "Subject is required for email",
                provider=self.provider_name,
                action="send_email"
            )
        
        # Create MIME message
        raw_message = self._create_mime_message(email)
        
        # Send email
        response = await self._make_request(
            "POST",
            f"/gmail/v1/users/{self.user_email}/messages/send",
            json={"raw": raw_message}
        )
        
        # Extract message info
        message_id = response.get("id")
        thread_id = response.get("threadId")
        
        return {
            "message_id": f"msg_{message_id}",
            "thread_id": thread_id,
            "provider": self.provider_name,
            "provider_message_id": message_id,
            "scheduled_for": options.get("send_at") if options else None,
            "estimated_delivery": datetime.utcnow().isoformat() + "Z",
            "status": "sent"
        }
    
    async def get_thread(
        self,
        thread_id: str
    ) -> Dict[str, Any]:
        """
        Get email thread from Gmail.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            Dictionary with thread data and messages
        """
        if not thread_id:
            raise ValidationError(
                "Thread ID is required",
                provider=self.provider_name,
                action="get_thread"
            )
        
        # Get thread from Gmail API
        response = await self._make_request(
            "GET",
            f"/gmail/v1/users/{self.user_email}/threads/{thread_id}",
            params={"format": "metadata"}
        )
        
        # Extract messages
        messages = []
        for msg in response.get("messages", []):
            msg_id = msg.get("id")
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            
            messages.append({
                "id": f"msg_{msg_id}",
                "from": headers.get("From"),
                "subject": headers.get("Subject"),
                "date": headers.get("Date"),
                "snippet": msg.get("snippet")
            })
        
        return {
            "thread_id": thread_id,
            "messages": messages,
            "message_count": len(messages)
        }
    
    async def list_messages(
        self,
        max_results: int = 10,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List messages in Gmail inbox.
        
        Args:
            max_results: Maximum number of messages to return
            page_token: Page token for pagination
            
        Returns:
            Dictionary with messages and pagination
        """
        params = {
            "maxResults": min(max_results, 100)
        }
        
        if page_token:
            params["pageToken"] = page_token
        
        # Get messages list
        response = await self._make_request(
            "GET",
            f"/gmail/v1/users/{self.user_email}/messages",
            params=params
        )
        
        # Get message details
        messages = []
        for msg_ref in response.get("messages", []):
            msg_id = msg_ref.get("id")
            
            # Get message metadata
            msg_data = await self._make_request(
                "GET",
                f"/gmail/v1/users/{self.user_email}/messages/{msg_id}",
                params={"format": "metadata"}
            )
            
            headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
            
            messages.append({
                "id": f"msg_{msg_id}",
                "thread_id": msg_data.get("threadId"),
                "from": headers.get("From"),
                "subject": headers.get("Subject"),
                "snippet": msg_data.get("snippet"),
                "date": headers.get("Date"),
                "is_read": "UNREAD" not in msg_data.get("labelIds", [])
            })
        
        return {
            "messages": messages,
            "next_page_token": response.get("nextPageToken"),
            "total_count": len(messages)
        }
    
    async def search_messages(
        self,
        query: Optional[str] = None,
        from_email: Optional[str] = None,
        to_email: Optional[str] = None,
        subject: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search messages in Gmail.
        
        Args:
            query: Search query string
            from_email: Filter by sender email
            to_email: Filter by recipient email
            subject: Filter by subject
            max_results: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        # Build Gmail search query
        search_parts = []
        
        if query:
            search_parts.append(query)
        
        if from_email:
            search_parts.append(f"from:{from_email}")
        
        if to_email:
            search_parts.append(f"to:{to_email}")
        
        if subject:
            search_parts.append(f"subject:{subject}")
        
        search_query = " ".join(search_parts) if search_parts else ""
        
        # Search messages
        params = {
            "q": search_query,
            "maxResults": min(max_results, 100)
        }
        
        response = await self._make_request(
            "GET",
            f"/gmail/v1/users/{self.user_email}/messages",
            params=params
        )
        
        # Get message details
        matches = []
        for msg_ref in response.get("messages", [])[:max_results]:
            msg_id = msg_ref.get("id")
            
            # Get message metadata
            msg_data = await self._make_request(
                "GET",
                f"/gmail/v1/users/{self.user_email}/messages/{msg_id}",
                params={"format": "metadata"}
            )
            
            headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
            
            matches.append({
                "id": f"msg_{msg_id}",
                "thread_id": msg_data.get("threadId"),
                "from": headers.get("From"),
                "subject": headers.get("Subject"),
                "snippet": msg_data.get("snippet"),
                "date": headers.get("Date"),
                "is_read": "UNREAD" not in msg_data.get("labelIds", []),
                "has_attachments": any("filename" in part for part in msg_data.get("payload", {}).get("parts", []))
            })
        
        return {
            "matches": matches,
            "pagination": {
                "total_items": response.get("resultSizeEstimate", len(matches)),
                "has_next": "nextPageToken" in response
            }
        }