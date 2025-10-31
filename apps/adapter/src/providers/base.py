"""
Base provider interface defining the contract for all providers.

This module defines the abstract base class that all provider implementations
must inherit from, ensuring consistent interfaces across different providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
import asyncio
import time
from datetime import datetime

from ..core.logging import get_logger, log_provider_call
from ..core.config import settings


logger = get_logger(__name__)


class ProviderCapability(str, Enum):
    """Provider capability enumeration."""
    CRM_CONTACTS = "crm.contacts"
    CRM_COMPANIES = "crm.companies"
    CRM_DEALS = "crm.deals"
    CRM_NOTES = "crm.notes"
    HELPDESK_TICKETS = "helpdesk.tickets"
    HELPDESK_COMMENTS = "helpdesk.comments"
    CALENDAR_EVENTS = "calendar.events"
    CALENDAR_AVAILABILITY = "calendar.availability"
    EMAIL_SEND = "email.send"
    EMAIL_SEARCH = "email.search"
    KNOWLEDGE_SEARCH = "knowledge.search"
    KNOWLEDGE_INDEX = "knowledge.index"


class ProviderError(Exception):
    """Base exception for provider errors."""
    
    def __init__(
        self,
        message: str,
        provider: str,
        action: Optional[str] = None,
        provider_response: Optional[Any] = None,
        retry_after: Optional[int] = None
    ):
        """
        Initialize provider error.
        
        Args:
            message: Error message
            provider: Provider name
            action: Action that failed
            provider_response: Original provider response
            retry_after: Seconds to wait before retry (for rate limits)
        """
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.action = action
        self.provider_response = provider_response
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """Raised when provider authentication fails."""
    pass


class RateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded."""
    pass


class ValidationError(ProviderError):
    """Raised when provider rejects request due to validation errors."""
    pass


class NotFoundError(ProviderError):
    """Raised when requested resource is not found."""
    pass


class ProviderPlugin(ABC):
    """
    Abstract base class for all provider plugins.
    
    All provider implementations must inherit from this class and implement
    the required abstract methods. This ensures consistent interfaces across
    different providers.
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize provider with credentials.
        
        Args:
            credentials: Provider-specific credentials
        """
        self.credentials = credentials
        self._client = None
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return provider name.
        
        Returns:
            Provider name (e.g., 'hubspot', 'zendesk')
        """
        pass
    
    @property
    @abstractmethod
    def supported_capabilities(self) -> List[ProviderCapability]:
        """
        Return list of supported capabilities.
        
        Returns:
            List of ProviderCapability enums
        """
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """
        Validate provider credentials.
        
        Returns:
            True if credentials are valid
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        pass
    
    @abstractmethod
    async def execute_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute provider-specific action.
        
        Args:
            action: Action identifier (e.g., 'create_contact')
            parameters: Action parameters
            idempotency_key: Optional idempotency key
            
        Returns:
            Action result with provider-specific data
            
        Raises:
            ProviderError: If action execution fails
            ValidationError: If parameters are invalid
        """
        pass
    
    @abstractmethod
    def normalize_response(
        self,
        provider_response: Any,
        action: str
    ) -> Dict[str, Any]:
        """
        Normalize provider response to standard format.
        
        Args:
            provider_response: Raw provider API response
            action: Action that was executed
            
        Returns:
            Normalized response matching adapter contract
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check provider health status.
        
        Returns:
            True if provider is healthy
        """
        pass
    
    async def execute_with_retry(
        self,
        action: str,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute action with automatic retry logic.
        
        Implements exponential backoff for transient errors and respects
        rate limiting.
        
        Args:
            action: Action identifier
            parameters: Action parameters
            idempotency_key: Optional idempotency key
            
        Returns:
            Action result
            
        Raises:
            ProviderError: If all retry attempts fail
        """
        max_attempts = settings.retry_max_attempts
        backoff_factor = settings.retry_backoff_factor
        initial_delay = settings.retry_initial_delay
        
        last_error = None
        
        for attempt in range(max_attempts):
            start_time = time.time()
            
            try:
                # Execute the action
                result = await self.execute_action(action, parameters, idempotency_key)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log successful call
                log_provider_call(
                    provider=self.provider_name,
                    action=action,
                    duration_ms=duration_ms,
                    success=True,
                    attempt=attempt + 1
                )
                
                return result
                
            except RateLimitError as e:
                last_error = e
                duration_ms = (time.time() - start_time) * 1000
                
                # Log rate limit
                log_provider_call(
                    provider=self.provider_name,
                    action=action,
                    duration_ms=duration_ms,
                    success=False,
                    error="Rate limit exceeded",
                    attempt=attempt + 1
                )
                
                # Wait for retry_after if provided, otherwise use exponential backoff
                if e.retry_after:
                    wait_time = e.retry_after
                else:
                    wait_time = initial_delay * (backoff_factor ** attempt)
                
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"Rate limit hit for {self.provider_name}.{action}, "
                        f"retrying in {wait_time}s (attempt {attempt + 1}/{max_attempts})"
                    )
                    await asyncio.sleep(wait_time)
                
            except (ConnectionError, TimeoutError) as e:
                last_error = e
                duration_ms = (time.time() - start_time) * 1000
                
                # Log network error
                log_provider_call(
                    provider=self.provider_name,
                    action=action,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e),
                    attempt=attempt + 1
                )
                
                # Retry with exponential backoff
                if attempt < max_attempts - 1:
                    wait_time = initial_delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"Network error for {self.provider_name}.{action}, "
                        f"retrying in {wait_time}s (attempt {attempt + 1}/{max_attempts})"
                    )
                    await asyncio.sleep(wait_time)
                
            except (ValidationError, NotFoundError, AuthenticationError) as e:
                # Don't retry for these errors
                last_error = e
                duration_ms = (time.time() - start_time) * 1000
                
                log_provider_call(
                    provider=self.provider_name,
                    action=action,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e),
                    attempt=attempt + 1
                )
                
                raise
                
            except ProviderError as e:
                last_error = e
                duration_ms = (time.time() - start_time) * 1000
                
                log_provider_call(
                    provider=self.provider_name,
                    action=action,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e),
                    attempt=attempt + 1
                )
                
                # For other provider errors, only retry transient errors
                if attempt < max_attempts - 1:
                    wait_time = initial_delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"Error from {self.provider_name}.{action}, "
                        f"retrying in {wait_time}s (attempt {attempt + 1}/{max_attempts})"
                    )
                    await asyncio.sleep(wait_time)
        
        # All retries exhausted
        logger.error(
            f"All {max_attempts} retry attempts exhausted for "
            f"{self.provider_name}.{action}"
        )
        
        if last_error:
            raise last_error
        else:
            raise ProviderError(
                f"Failed to execute {action} after {max_attempts} attempts",
                provider=self.provider_name,
                action=action
            )
    
    def supports_capability(self, capability: ProviderCapability) -> bool:
        """
        Check if provider supports a capability.
        
        Args:
            capability: Capability to check
            
        Returns:
            True if capability is supported
        """
        return capability in self.supported_capabilities
    
    async def close(self):
        """
        Close provider connections and cleanup resources.
        
        Should be called when the provider is no longer needed.
        """
        if self._client:
            # Close HTTP client or other resources
            if hasattr(self._client, 'aclose'):
                await self._client.aclose()
            elif hasattr(self._client, 'close'):
                self._client.close()
            self._client = None