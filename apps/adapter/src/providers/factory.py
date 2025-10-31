"""
Provider factory for dependency injection.

This module provides a factory for creating and managing provider instances
based on tenant configuration and provider types.
"""

from typing import Dict, Optional, Type
from enum import Enum

from .base import ProviderPlugin, ProviderCapability, AuthenticationError
from ..core.logging import get_logger
from ..core.config import settings


logger = get_logger(__name__)


class ProviderType(str, Enum):
    """Provider type enumeration."""
    CRM = "crm"
    HELPDESK = "helpdesk"
    CALENDAR = "calendar"
    EMAIL = "email"
    KNOWLEDGE = "knowledge"


class ProviderRegistry:
    """
    Registry for provider plugins.
    
    Manages registration and retrieval of provider implementations.
    """
    
    def __init__(self):
        """Initialize provider registry."""
        self._providers: Dict[str, Type[ProviderPlugin]] = {}
    
    def register(self, provider_class: Type[ProviderPlugin]) -> None:
        """
        Register a provider class.
        
        Args:
            provider_class: Provider class to register
        """
        # Instantiate to get provider name
        temp_instance = provider_class({})
        provider_name = temp_instance.provider_name
        
        self._providers[provider_name] = provider_class
        logger.info(f"Registered provider: {provider_name}")
    
    def get_provider_class(self, provider_name: str) -> Optional[Type[ProviderPlugin]]:
        """
        Get provider class by name.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Provider class or None if not found
        """
        return self._providers.get(provider_name)
    
    def list_providers(self) -> list[str]:
        """
        List all registered provider names.
        
        Returns:
            List of provider names
        """
        return list(self._providers.keys())


# Global provider registry
_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """
    Get the global provider registry.
    
    Returns:
        Global provider registry instance
    """
    return _registry


class ProviderFactory:
    """
    Factory for creating provider instances.
    
    Handles provider instantiation, credential management, and caching
    of provider instances per tenant.
    """
    
    def __init__(self):
        """Initialize provider factory."""
        self._cache: Dict[str, ProviderPlugin] = {}
        self._registry = get_registry()
    
    async def get_provider(
        self,
        provider_type: ProviderType,
        tenant_id: str,
        provider_name: Optional[str] = None
    ) -> ProviderPlugin:
        """
        Get or create a provider instance.
        
        Args:
            provider_type: Type of provider (crm, helpdesk, etc.)
            tenant_id: Tenant identifier
            provider_name: Specific provider name (optional, will use default)
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider is not configured or not found
            AuthenticationError: If provider credentials are invalid
        """
        # Determine which provider to use
        if not provider_name:
            provider_name = self._get_default_provider(provider_type)
        
        # Cache key
        cache_key = f"{tenant_id}:{provider_name}"
        
        # Return cached provider if available
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get credentials for provider
        credentials = self._get_credentials(provider_name, tenant_id)
        
        # Get provider class
        provider_class = self._registry.get_provider_class(provider_name)
        if not provider_class:
            raise ValueError(f"Provider not found: {provider_name}")
        
        # Create provider instance
        logger.info(f"Creating provider instance: {provider_name} for tenant {tenant_id}")
        provider = provider_class(credentials)
        
        # Validate credentials
        try:
            await provider.validate_credentials()
        except Exception as e:
            logger.error(f"Failed to validate credentials for {provider_name}: {e}")
            raise AuthenticationError(
                f"Invalid credentials for {provider_name}",
                provider=provider_name
            )
        
        # Cache the provider
        self._cache[cache_key] = provider
        
        return provider
    
    def _get_default_provider(self, provider_type: ProviderType) -> str:
        """
        Get default provider name for a provider type.
        
        Args:
            provider_type: Provider type
            
        Returns:
            Provider name
            
        Raises:
            ValueError: If no provider is configured for the type
        """
        # Map provider types to default providers based on what's enabled
        type_mapping = {
            ProviderType.CRM: [
                ("hubspot", settings.hubspot_enabled),
                ("salesforce", settings.salesforce_enabled)
            ],
            ProviderType.HELPDESK: [
                ("zendesk", settings.zendesk_enabled)
            ],
            ProviderType.CALENDAR: [
                ("google", settings.google_enabled)
            ],
            ProviderType.EMAIL: [
                ("gmail", settings.gmail_enabled)
            ],
            ProviderType.KNOWLEDGE: [
                ("stub", True)  # Always available
            ]
        }
        
        providers = type_mapping.get(provider_type, [])
        
        # Find first enabled provider
        for provider_name, enabled in providers:
            if enabled:
                return provider_name
        
        raise ValueError(
            f"No provider configured for type: {provider_type}. "
            f"Please enable a provider in configuration."
        )
    
    def _get_credentials(self, provider_name: str, tenant_id: str) -> Dict[str, str]:
        """
        Get credentials for a provider.
        
        In production, this would fetch credentials from a secure store
        (e.g., HashiCorp Vault, AWS Secrets Manager) based on tenant configuration.
        
        For now, it uses global configuration from settings.
        
        Args:
            provider_name: Provider name
            tenant_id: Tenant identifier
            
        Returns:
            Dictionary of credentials
            
        Raises:
            ValueError: If credentials are not configured
        """
        credentials = settings.get_provider_credentials(provider_name)
        
        if not credentials or not credentials.get("enabled"):
            raise ValueError(
                f"Credentials not configured for provider: {provider_name}. "
                f"Please set the required environment variables."
            )
        
        # Remove 'enabled' flag from credentials
        credentials = {k: v for k, v in credentials.items() if k != "enabled"}
        
        return credentials
    
    def clear_cache(self, tenant_id: Optional[str] = None, provider_name: Optional[str] = None):
        """
        Clear provider cache.
        
        Args:
            tenant_id: Specific tenant to clear (None for all)
            provider_name: Specific provider to clear (None for all)
        """
        if tenant_id and provider_name:
            # Clear specific tenant+provider
            cache_key = f"{tenant_id}:{provider_name}"
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.info(f"Cleared cache for {cache_key}")
        elif tenant_id:
            # Clear all providers for tenant
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{tenant_id}:")]
            for key in keys_to_remove:
                del self._cache[key]
            logger.info(f"Cleared cache for tenant {tenant_id}")
        elif provider_name:
            # Clear specific provider for all tenants
            keys_to_remove = [k for k in self._cache.keys() if k.endswith(f":{provider_name}")]
            for key in keys_to_remove:
                del self._cache[key]
            logger.info(f"Cleared cache for provider {provider_name}")
        else:
            # Clear all
            self._cache.clear()
            logger.info("Cleared all provider cache")
    
    async def health_check(self, provider_type: ProviderType, tenant_id: str) -> bool:
        """
        Check health of a provider.
        
        Args:
            provider_type: Provider type
            tenant_id: Tenant identifier
            
        Returns:
            True if provider is healthy
        """
        try:
            provider = await self.get_provider(provider_type, tenant_id)
            return await provider.health_check()
        except Exception as e:
            logger.error(f"Health check failed for {provider_type}: {e}")
            return False


# Global provider factory instance
_factory = ProviderFactory()


def get_factory() -> ProviderFactory:
    """
    Get the global provider factory.
    
    Returns:
        Global provider factory instance
    """
    return _factory


def register_provider(provider_class: Type[ProviderPlugin]) -> None:
    """
    Register a provider class with the global registry.
    
    Args:
        provider_class: Provider class to register
    """
    _registry.register(provider_class)