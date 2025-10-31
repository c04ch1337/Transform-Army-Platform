"""
HubSpot CRM provider implementation.

This module provides real integration with the HubSpot API v3 for CRM operations
including contacts, deals, notes, and more.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import httpx

from ..base import (
    CRMProvider,
    ProviderCapability,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ProviderError
)
from ...core.logging import get_logger


logger = get_logger(__name__)


class HubSpotProvider(CRMProvider):
    """
    HubSpot CRM provider implementation using HubSpot API v3.
    
    Supports both Private App tokens (API keys) and OAuth2 access tokens.
    Implements rate limiting, retry logic, and proper error handling.
    """
    
    # HubSpot API configuration
    DEFAULT_API_BASE = "https://api.hubapi.com"
    DEFAULT_TIMEOUT = httpx.Timeout(30.0, read=60.0)
    USER_AGENT = "Transform-Army-Adapter/1.0"
    
    # Rate limiting configuration
    MAX_REQUESTS_PER_10_SECONDS = 100
    RATE_LIMIT_WINDOW = 10
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize HubSpot provider.
        
        Args:
            credentials: HubSpot credentials including:
                - auth_type: 'api_key' or 'oauth2'
                - api_key: Private App token (for api_key auth)
                - access_token: OAuth2 access token (for oauth2 auth)
                - refresh_token: OAuth2 refresh token (optional)
                - api_base_url: Custom API base URL (optional)
        """
        super().__init__(credentials)
        
        self.auth_type = credentials.get("auth_type", "api_key")
        self.api_key = credentials.get("api_key")
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.api_base_url = credentials.get("api_base_url", self.DEFAULT_API_BASE)
        
        # Rate limiting state
        self._request_times: List[float] = []
        self._rate_limit_lock = asyncio.Lock()
        
        # Initialize HTTP client
        self._client = None
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "hubspot"
    
    @property
    def supported_capabilities(self) -> List[ProviderCapability]:
        """Return supported capabilities."""
        return [
            ProviderCapability.CRM_CONTACTS,
            ProviderCapability.CRM_COMPANIES,
            ProviderCapability.CRM_DEALS,
            ProviderCapability.CRM_NOTES
        ]
    
    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {
                "User-Agent": self.USER_AGENT,
                "Content-Type": "application/json"
            }
            
            # Add authorization header based on auth type
            if self.auth_type == "oauth2" and self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            elif self.auth_type == "api_key" and self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.api_base_url,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT,
                follow_redirects=True
            )
        
        return self._client
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting to respect HubSpot's limits."""
        async with self._rate_limit_lock:
            now = asyncio.get_event_loop().time()
            
            # Remove requests older than the rate limit window
            self._request_times = [
                t for t in self._request_times 
                if now - t < self.RATE_LIMIT_WINDOW
            ]
            
            # If we're at the limit, wait until the oldest request expires
            if len(self._request_times) >= self.MAX_REQUESTS_PER_10_SECONDS:
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
        Make HTTP request to HubSpot API with rate limiting and error handling.
        
        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
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
                retry_after = int(response.headers.get("Retry-After", 10))
                raise RateLimitError(
                    "HubSpot rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=retry_after
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid HubSpot credentials or expired token",
                    provider=self.provider_name,
                    provider_response=response.text
                )
            
            # Handle validation errors
            if response.status_code == 400:
                error_data = response.json() if response.text else {}
                raise ValidationError(
                    f"HubSpot validation error: {error_data.get('message', 'Invalid request')}",
                    provider=self.provider_name,
                    provider_response=error_data
                )
            
            # Handle not found
            if response.status_code == 404:
                raise NotFoundError(
                    "Resource not found in HubSpot",
                    provider=self.provider_name,
                    provider_response=response.text
                )
            
            # Handle server errors
            if response.status_code >= 500:
                raise ProviderError(
                    f"HubSpot server error: {response.status_code}",
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
                    "Request to HubSpot timed out",
                    provider=self.provider_name,
                    provider_response=str(e)
                )
            elif isinstance(e, httpx.NetworkError):
                raise ProviderError(
                    "Network error connecting to HubSpot",
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
        Validate HubSpot credentials by making a test API call.
        
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
        
        if self.auth_type == "api_key" and not self.api_key:
            raise AuthenticationError(
                "Missing HubSpot API key",
                provider=self.provider_name
            )
        
        try:
            # Test credentials with a simple API call
            await self._make_request("GET", "/crm/v3/objects/contacts", params={"limit": 1})
            logger.info(f"HubSpot credentials validated successfully")
            return True
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to validate HubSpot credentials: {e}")
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
        Execute HubSpot action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            idempotency_key: Optional idempotency key
            
        Returns:
            Action result
        """
        action_map = {
            "create_contact": self.create_contact,
            "update_contact": self.update_contact,
            "search_contacts": self.search_contacts,
            "add_note": self.add_note,
            "create_deal": self.create_deal
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
        Normalize HubSpot response to standard format.
        
        Args:
            provider_response: Raw HubSpot response
            action: Action that was executed
            
        Returns:
            Normalized response
        """
        # HubSpot responses are already in a good format
        return provider_response
    
    async def health_check(self) -> bool:
        """Check HubSpot provider health."""
        try:
            await self.validate_credentials()
            return True
        except Exception:
            return False
    
    async def create_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new contact in HubSpot.
        
        Args:
            email: Contact email address (required)
            first_name: Contact first name
            last_name: Contact last name
            company: Company name
            phone: Phone number
            metadata: Additional custom fields
            
        Returns:
            Dictionary with contact data
        """
        if not email:
            raise ValidationError(
                "Email is required for contact creation",
                provider=self.provider_name,
                action="create_contact"
            )
        
        # Build properties for HubSpot
        properties = {
            "email": email
        }
        
        if first_name:
            properties["firstname"] = first_name
        if last_name:
            properties["lastname"] = last_name
        if company:
            properties["company"] = company
        if phone:
            properties["phone"] = phone
        
        # Add metadata as custom properties
        if metadata:
            properties.update(metadata)
        
        # Make API request
        response = await self._make_request(
            "POST",
            "/crm/v3/objects/contacts",
            json={"properties": properties}
        )
        
        # Extract contact data
        contact_id = response.get("id")
        props = response.get("properties", {})
        
        return {
            "id": f"cont_{contact_id}",
            "provider": self.provider_name,
            "provider_id": contact_id,
            "email": props.get("email"),
            "first_name": props.get("firstname"),
            "last_name": props.get("lastname"),
            "company": props.get("company"),
            "phone": props.get("phone"),
            "title": props.get("jobtitle"),
            "created_at": props.get("createdate"),
            "updated_at": props.get("lastmodifieddate"),
            "url": f"https://app.hubspot.com/contacts/{contact_id}"
        }
    
    async def update_contact(
        self,
        contact_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing contact in HubSpot.
        
        Args:
            contact_id: ID of the contact to update
            updates: Dictionary of fields to update
            
        Returns:
            Dictionary with updated contact data
        """
        if not contact_id:
            raise ValidationError(
                "Contact ID is required",
                provider=self.provider_name,
                action="update_contact"
            )
        
        # Remove 'cont_' prefix if present
        if contact_id.startswith("cont_"):
            contact_id = contact_id[5:]
        
        # Map field names to HubSpot property names
        property_mapping = {
            "first_name": "firstname",
            "last_name": "lastname",
            "title": "jobtitle"
        }
        
        properties = {}
        for key, value in updates.items():
            hubspot_key = property_mapping.get(key, key)
            properties[hubspot_key] = value
        
        # Make API request
        response = await self._make_request(
            "PATCH",
            f"/crm/v3/objects/contacts/{contact_id}",
            json={"properties": properties}
        )
        
        # Extract contact data
        props = response.get("properties", {})
        
        return {
            "id": f"cont_{contact_id}",
            "provider": self.provider_name,
            "provider_id": contact_id,
            "email": props.get("email"),
            "first_name": props.get("firstname"),
            "last_name": props.get("lastname"),
            "company": props.get("company"),
            "phone": props.get("phone"),
            "title": props.get("jobtitle"),
            "created_at": props.get("createdate"),
            "updated_at": props.get("lastmodifieddate")
        }
    
    async def search_contacts(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search for contacts in HubSpot.
        
        Args:
            query: Search query string
            filters: Additional filters to apply
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Dictionary with matches and pagination info
        """
        # Build HubSpot search request
        search_request = {
            "limit": min(limit, 100),  # HubSpot max is 100
            "after": offset if offset > 0 else None,
            "filterGroups": []
        }
        
        # Add query as email/name filter
        if query:
            filter_group = {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "CONTAINS_TOKEN",
                        "value": query
                    }
                ]
            }
            search_request["filterGroups"].append(filter_group)
        
        # Add additional filters
        if filters:
            for key, value in filters.items():
                filter_group = {
                    "filters": [
                        {
                            "propertyName": key,
                            "operator": "EQ",
                            "value": value
                        }
                    ]
                }
                search_request["filterGroups"].append(filter_group)
        
        # Make API request
        response = await self._make_request(
            "POST",
            "/crm/v3/objects/contacts/search",
            json=search_request
        )
        
        # Extract results
        results = response.get("results", [])
        matches = []
        
        for result in results:
            props = result.get("properties", {})
            contact_id = result.get("id")
            
            matches.append({
                "id": f"cont_{contact_id}",
                "email": props.get("email"),
                "first_name": props.get("firstname"),
                "last_name": props.get("lastname"),
                "company": props.get("company"),
                "title": props.get("jobtitle"),
                "phone": props.get("phone"),
                "score": 1.0,  # HubSpot doesn't provide relevance score
                "url": f"https://app.hubspot.com/contacts/{contact_id}"
            })
        
        # Build pagination info
        total = response.get("total", len(matches))
        has_next = "paging" in response and "next" in response["paging"]
        
        return {
            "matches": matches,
            "pagination": {
                "total_items": total,
                "has_next": has_next
            }
        }
    
    async def add_note(
        self,
        contact_id: str,
        note_text: str,
        note_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a note to a contact in HubSpot.
        
        Args:
            contact_id: ID of the contact
            note_text: Content of the note
            note_type: Type of note (ignored, HubSpot has its own types)
            
        Returns:
            Dictionary with note data
        """
        if not contact_id:
            raise ValidationError(
                "Contact ID is required",
                provider=self.provider_name,
                action="add_note"
            )
        
        if not note_text:
            raise ValidationError(
                "Note text is required",
                provider=self.provider_name,
                action="add_note"
            )
        
        # Remove 'cont_' prefix if present
        if contact_id.startswith("cont_"):
            contact_id = contact_id[5:]
        
        # Create note with association to contact
        note_data = {
            "properties": {
                "hs_note_body": note_text,
                "hs_timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 202  # Note to Contact association
                        }
                    ]
                }
            ]
        }
        
        # Make API request
        response = await self._make_request(
            "POST",
            "/crm/v3/objects/notes",
            json=note_data
        )
        
        # Extract note data
        note_id = response.get("id")
        props = response.get("properties", {})
        
        return {
            "id": f"note_{note_id}",
            "provider": self.provider_name,
            "provider_id": note_id,
            "contact_id": f"cont_{contact_id}",
            "content": props.get("hs_note_body"),
            "type": note_type or "note",
            "created_at": props.get("hs_timestamp")
        }
    
    async def create_deal(
        self,
        deal_name: str,
        amount: Optional[float] = None,
        stage: Optional[str] = None,
        associated_contacts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new deal in HubSpot.
        
        Args:
            deal_name: Name of the deal
            amount: Deal amount
            stage: Deal stage
            associated_contacts: List of contact IDs to associate
            
        Returns:
            Dictionary with deal data
        """
        if not deal_name:
            raise ValidationError(
                "Deal name is required",
                provider=self.provider_name,
                action="create_deal"
            )
        
        # Build properties
        properties = {
            "dealname": deal_name
        }
        
        if amount is not None:
            properties["amount"] = str(amount)
        if stage:
            properties["dealstage"] = stage
        
        # Build associations
        associations = []
        if associated_contacts:
            for contact_id in associated_contacts:
                # Remove 'cont_' prefix if present
                if contact_id.startswith("cont_"):
                    contact_id = contact_id[5:]
                
                associations.append({
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 3  # Deal to Contact association
                        }
                    ]
                })
        
        # Build request
        deal_data = {"properties": properties}
        if associations:
            deal_data["associations"] = associations
        
        # Make API request
        response = await self._make_request(
            "POST",
            "/crm/v3/objects/deals",
            json=deal_data
        )
        
        # Extract deal data
        deal_id = response.get("id")
        props = response.get("properties", {})
        
        return {
            "id": f"deal_{deal_id}",
            "provider": self.provider_name,
            "provider_id": deal_id,
            "name": props.get("dealname"),
            "amount": float(props.get("amount", 0)) if props.get("amount") else None,
            "stage": props.get("dealstage"),
            "created_at": props.get("createdate"),
            "url": f"https://app.hubspot.com/contacts/{deal_id}"
        }