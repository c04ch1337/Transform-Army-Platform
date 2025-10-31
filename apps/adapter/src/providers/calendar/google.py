"""
Google Calendar provider implementation.

This module provides real integration with the Google Calendar API v3 for calendar operations
including events, availability checking, and meeting scheduling.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import httpx
import uuid

from ..base import (
    CalendarProvider,
    ProviderCapability,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ProviderError
)
from ...core.logging import get_logger


logger = get_logger(__name__)


class GoogleCalendarProvider(CalendarProvider):
    """
    Google Calendar provider implementation using Google Calendar API v3.
    
    Supports OAuth2 authentication with automatic token refresh.
    Implements rate limiting, retry logic, and proper error handling.
    """
    
    # Google Calendar API configuration
    DEFAULT_API_BASE = "https://www.googleapis.com"
    DEFAULT_TIMEOUT = httpx.Timeout(30.0, read=60.0)
    USER_AGENT = "Transform-Army-Adapter/1.0"
    
    # Rate limiting configuration (1,000,000 requests/day ~ 11.57 requests/second)
    MAX_REQUESTS_PER_SECOND = 10
    RATE_LIMIT_WINDOW = 1
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Google Calendar provider.
        
        Args:
            credentials: Google Calendar credentials including:
                - auth_type: 'oauth2' (default)
                - access_token: OAuth2 access token
                - refresh_token: OAuth2 refresh token
                - client_id: OAuth2 client ID
                - client_secret: OAuth2 client secret
                - token_uri: Token refresh URI (default: https://oauth2.googleapis.com/token)
                - default_calendar_id: Default calendar ID (default: 'primary')
        """
        super().__init__(credentials)
        
        self.auth_type = credentials.get("auth_type", "oauth2")
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.token_uri = credentials.get("token_uri", "https://oauth2.googleapis.com/token")
        self.default_calendar_id = credentials.get("default_calendar_id", "primary")
        self.api_base_url = credentials.get("api_base_url", self.DEFAULT_API_BASE)
        
        # Rate limiting state
        self._request_times: List[float] = []
        self._rate_limit_lock = asyncio.Lock()
        
        # Initialize HTTP client
        self._client = None
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "google"
    
    @property
    def supported_capabilities(self) -> List[ProviderCapability]:
        """Return supported capabilities."""
        return [
            ProviderCapability.CALENDAR_EVENTS,
            ProviderCapability.CALENDAR_AVAILABILITY
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
        """Enforce rate limiting to respect Google Calendar's limits."""
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
                
                # Note: In production, you would update the tenant config with new token
                
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
        Make HTTP request to Google Calendar API with rate limiting and error handling.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
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
                    "Google Calendar rate limit exceeded",
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
                            "Invalid Google Calendar credentials after token refresh",
                            provider=self.provider_name,
                            provider_response=response.text
                        )
                else:
                    raise AuthenticationError(
                        "Invalid Google Calendar credentials",
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
                    f"Google Calendar validation error: {error_msg}",
                    provider=self.provider_name,
                    provider_response=error_data
                )
            
            # Handle not found
            if response.status_code == 404:
                raise NotFoundError(
                    "Resource not found in Google Calendar",
                    provider=self.provider_name,
                    provider_response=response.text
                )
            
            # Handle server errors
            if response.status_code >= 500:
                raise ProviderError(
                    f"Google Calendar server error: {response.status_code}",
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
                    "Request to Google Calendar timed out",
                    provider=self.provider_name,
                    provider_response=str(e)
                )
            elif isinstance(e, httpx.NetworkError):
                raise ProviderError(
                    "Network error connecting to Google Calendar",
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
        Validate Google Calendar credentials by making a test API call.
        
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
                f"/calendar/v3/calendars/{self.default_calendar_id}"
            )
            logger.info(f"Google Calendar credentials validated successfully")
            return True
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to validate Google Calendar credentials: {e}")
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
        Execute Google Calendar action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            idempotency_key: Optional idempotency key
            
        Returns:
            Action result
        """
        action_map = {
            "check_availability": self.check_availability,
            "create_event": self.create_event,
            "update_event": self.update_event,
            "cancel_event": self.cancel_event,
            "list_events": self.list_events
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
        Normalize Google Calendar response to standard format.
        
        Args:
            provider_response: Raw Google Calendar response
            action: Action that was executed
            
        Returns:
            Normalized response
        """
        # Google Calendar responses are already in a good format
        return provider_response
    
    async def health_check(self) -> bool:
        """Check Google Calendar provider health."""
        try:
            await self.validate_credentials()
            return True
        except Exception:
            return False
    
    async def check_availability(
        self,
        calendar_id: str,
        start_time: str,
        end_time: str,
        duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Check availability and return free time slots.
        
        Args:
            calendar_id: Calendar identifier to check
            start_time: Start of time range (ISO 8601)
            end_time: End of time range (ISO 8601)
            duration_minutes: Duration of meeting slot in minutes
            
        Returns:
            Dictionary with available time slots
        """
        if not calendar_id:
            calendar_id = self.default_calendar_id
        
        # Query Google Calendar FreeBusy API
        request_body = {
            "timeMin": start_time,
            "timeMax": end_time,
            "items": [{"id": calendar_id}]
        }
        
        response = await self._make_request(
            "POST",
            "/calendar/v3/freeBusy",
            json=request_body
        )
        
        # Extract busy periods
        busy_periods = []
        calendars = response.get("calendars", {})
        calendar_data = calendars.get(calendar_id, {})
        
        for busy in calendar_data.get("busy", []):
            busy_periods.append({
                "start": busy["start"],
                "end": busy["end"]
            })
        
        # Calculate free slots
        available_slots = self._calculate_free_slots(
            start_time,
            end_time,
            busy_periods,
            duration_minutes
        )
        
        return {
            "available_slots": available_slots,
            "calendar_id": calendar_id,
            "checked_at": datetime.utcnow().isoformat() + "Z"
        }
    
    def _calculate_free_slots(
        self,
        start_time: str,
        end_time: str,
        busy_periods: List[Dict[str, str]],
        duration_minutes: int
    ) -> List[Dict[str, str]]:
        """
        Calculate free time slots based on busy periods.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            busy_periods: List of busy periods
            duration_minutes: Required slot duration
            
        Returns:
            List of available time slots
        """
        # Parse datetime strings
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration = timedelta(minutes=duration_minutes)
        
        # Parse busy periods
        busy_intervals = []
        for period in busy_periods:
            busy_start = datetime.fromisoformat(period["start"].replace('Z', '+00:00'))
            busy_end = datetime.fromisoformat(period["end"].replace('Z', '+00:00'))
            busy_intervals.append((busy_start, busy_end))
        
        # Sort busy intervals
        busy_intervals.sort(key=lambda x: x[0])
        
        # Find free slots
        available_slots = []
        current_time = start_dt
        
        for busy_start, busy_end in busy_intervals:
            # Check if there's a free slot before this busy period
            if current_time + duration <= busy_start:
                # Found a free slot
                slot_end = min(busy_start, current_time + duration)
                available_slots.append({
                    "start_time": current_time.isoformat(),
                    "end_time": slot_end.isoformat()
                })
            
            # Move to end of busy period
            current_time = max(current_time, busy_end)
        
        # Check for free slot at the end
        if current_time + duration <= end_dt:
            available_slots.append({
                "start_time": current_time.isoformat(),
                "end_time": (current_time + duration).isoformat()
            })
        
        return available_slots
    
    async def create_event(
        self,
        calendar_id: str,
        summary: str,
        description: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        location: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new calendar event.
        
        Args:
            calendar_id: Calendar identifier
            summary: Event title/summary
            description: Event description
            start_time: Event start time (ISO 8601)
            end_time: Event end time (ISO 8601)
            attendees: List of attendee email addresses
            location: Event location
            metadata: Additional metadata (timezone, conference data, etc.)
            
        Returns:
            Dictionary with event data
        """
        if not calendar_id:
            calendar_id = self.default_calendar_id
        
        if not summary:
            raise ValidationError(
                "Summary is required for event creation",
                provider=self.provider_name,
                action="create_event"
            )
        
        if not start_time or not end_time:
            raise ValidationError(
                "Start time and end time are required",
                provider=self.provider_name,
                action="create_event"
            )
        
        # Build event data for Google Calendar
        event_data = {
            "summary": summary,
            "start": {
                "dateTime": start_time,
                "timeZone": metadata.get("timezone", "UTC") if metadata else "UTC"
            },
            "end": {
                "dateTime": end_time,
                "timeZone": metadata.get("timezone", "UTC") if metadata else "UTC"
            }
        }
        
        if description:
            event_data["description"] = description
        
        if location:
            event_data["location"] = location
        
        if attendees:
            event_data["attendees"] = [{"email": email} for email in attendees]
        
        # Add conference data (Google Meet) if requested
        if metadata and metadata.get("add_conference_data"):
            event_data["conferenceData"] = {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }
        
        # Add query parameter for conference data
        params = {}
        if metadata and metadata.get("add_conference_data"):
            params["conferenceDataVersion"] = 1
        
        if metadata and not metadata.get("send_notifications", True):
            params["sendNotifications"] = "false"
        
        # Make API request
        response = await self._make_request(
            "POST",
            f"/calendar/v3/calendars/{calendar_id}/events",
            json=event_data,
            params=params
        )
        
        # Extract event data
        event_id = response.get("id")
        
        # Extract meeting URL from conference data
        meeting_url = None
        if "conferenceData" in response:
            entry_points = response["conferenceData"].get("entryPoints", [])
            for entry in entry_points:
                if entry.get("entryPointType") == "video":
                    meeting_url = entry.get("uri")
                    break
        
        return {
            "id": f"evt_{event_id}",
            "provider": self.provider_name,
            "provider_id": event_id,
            "calendar_id": calendar_id,
            "summary": response.get("summary"),
            "description": response.get("description"),
            "start_time": response["start"].get("dateTime"),
            "end_time": response["end"].get("dateTime"),
            "attendees": [att.get("email") for att in response.get("attendees", [])],
            "location": response.get("location"),
            "meeting_url": meeting_url,
            "status": response.get("status"),
            "created_at": response.get("created"),
            "updated_at": response.get("updated"),
            "url": response.get("htmlLink")
        }
    
    async def update_event(
        self,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing calendar event.
        
        Args:
            event_id: ID of the event to update
            updates: Dictionary of fields to update
            
        Returns:
            Dictionary with updated event data
        """
        if not event_id:
            raise ValidationError(
                "Event ID is required",
                provider=self.provider_name,
                action="update_event"
            )
        
        # Remove 'evt_' prefix if present
        if event_id.startswith("evt_"):
            event_id = event_id[4:]
        
        # Get calendar_id from updates or use default
        calendar_id = updates.pop("calendar_id", self.default_calendar_id)
        
        # Build update data for Google Calendar
        event_data = {}
        
        if "summary" in updates:
            event_data["summary"] = updates["summary"]
        
        if "description" in updates:
            event_data["description"] = updates["description"]
        
        if "start_time" in updates:
            event_data["start"] = {
                "dateTime": updates["start_time"],
                "timeZone": updates.get("timezone", "UTC")
            }
        
        if "end_time" in updates:
            event_data["end"] = {
                "dateTime": updates["end_time"],
                "timeZone": updates.get("timezone", "UTC")
            }
        
        if "location" in updates:
            event_data["location"] = updates["location"]
        
        if "attendees" in updates:
            event_data["attendees"] = [{"email": email} for email in updates["attendees"]]
        
        # Make API request
        response = await self._make_request(
            "PATCH",
            f"/calendar/v3/calendars/{calendar_id}/events/{event_id}",
            json=event_data
        )
        
        # Extract meeting URL
        meeting_url = None
        if "conferenceData" in response:
            entry_points = response["conferenceData"].get("entryPoints", [])
            for entry in entry_points:
                if entry.get("entryPointType") == "video":
                    meeting_url = entry.get("uri")
                    break
        
        return {
            "id": f"evt_{event_id}",
            "provider": self.provider_name,
            "provider_id": event_id,
            "calendar_id": calendar_id,
            "summary": response.get("summary"),
            "description": response.get("description"),
            "start_time": response["start"].get("dateTime"),
            "end_time": response["end"].get("dateTime"),
            "attendees": [att.get("email") for att in response.get("attendees", [])],
            "location": response.get("location"),
            "meeting_url": meeting_url,
            "status": response.get("status"),
            "created_at": response.get("created"),
            "updated_at": response.get("updated"),
            "url": response.get("htmlLink")
        }
    
    async def cancel_event(
        self,
        event_id: str,
        cancellation_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel a calendar event.
        
        Args:
            event_id: ID of the event to cancel
            cancellation_message: Optional message to send to attendees
            
        Returns:
            Dictionary with cancellation confirmation
        """
        if not event_id:
            raise ValidationError(
                "Event ID is required",
                provider=self.provider_name,
                action="cancel_event"
            )
        
        # Remove 'evt_' prefix if present
        if event_id.startswith("evt_"):
            event_id = event_id[4:]
        
        # Use default calendar
        calendar_id = self.default_calendar_id
        
        # Google Calendar uses DELETE to remove/cancel events
        await self._make_request(
            "DELETE",
            f"/calendar/v3/calendars/{calendar_id}/events/{event_id}",
            params={"sendNotifications": "true"} if cancellation_message else {}
        )
        
        return {
            "event_id": f"evt_{event_id}",
            "status": "cancelled",
            "message": cancellation_message or "Event cancelled successfully",
            "cancelled_at": datetime.utcnow().isoformat() + "Z"
        }
    
    async def list_events(
        self,
        calendar_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        List events in a calendar within a date range.
        
        Args:
            calendar_id: Calendar identifier
            start_date: Start date filter (ISO 8601)
            end_date: End date filter (ISO 8601)
            max_results: Maximum number of events to return
            
        Returns:
            Dictionary with events and pagination info
        """
        if not calendar_id:
            calendar_id = self.default_calendar_id
        
        # Build query parameters
        params = {
            "maxResults": min(max_results, 100),  # Google Calendar max is 250
            "singleEvents": "true",  # Expand recurring events
            "orderBy": "startTime"
        }
        
        if start_date:
            params["timeMin"] = start_date
        
        if end_date:
            params["timeMax"] = end_date
        
        # Make API request
        response = await self._make_request(
            "GET",
            f"/calendar/v3/calendars/{calendar_id}/events",
            params=params
        )
        
        # Extract events
        items = response.get("items", [])
        events = []
        
        for item in items:
            event_id = item.get("id")
            
            # Handle all-day events vs timed events
            start_time = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
            end_time = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
            
            events.append({
                "id": f"evt_{event_id}",
                "provider_id": event_id,
                "summary": item.get("summary"),
                "description": item.get("description"),
                "start_time": start_time,
                "end_time": end_time,
                "status": item.get("status"),
                "location": item.get("location"),
                "url": item.get("htmlLink")
            })
        
        return {
            "events": events,
            "calendar_id": calendar_id,
            "total_count": len(events)
        }