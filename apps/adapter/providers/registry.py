"""
Provider Registry for Transform Army AI.

Central registry for all provider implementations, enabling automatic
discovery, registration, and retrieval of providers by type.
"""

from typing import Dict, List, Optional, Type, Any
from enum import Enum
import importlib
import inspect
import pkgutil

from .base import (
    ProviderPlugin,
    CRMProvider,
    HelpdeskProvider,
    CalendarProvider,
    ProviderCapability
)
from ..core.logging import get_logger


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
    Central registry for all provider implementations.
    
    This registry provides:
    - Automatic discovery of provider modules
    - Type-safe provider registration
    - Provider retrieval by type and name
    - Validation of provider implementations
    - Listing of available providers
    """
    
    def __init__(self):
        """Initialize the provider registry."""
        self._providers: Dict[ProviderType, Dict[str, Type[ProviderPlugin]]] = {
            ProviderType.CRM: {},
            ProviderType.HELPDESK: {},
            ProviderType.CALENDAR: {},
            ProviderType.EMAIL: {},
            ProviderType.KNOWLEDGE: {}
        }
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_provider(
        self,
        provider_type: ProviderType,
        provider_name: str,
        provider_class: Type[ProviderPlugin]
    ) -> None:
        """
        Register a provider implementation.
        
        Args:
            provider_type: Type of provider (CRM, HELPDESK, etc.)
            provider_name: Unique name for the provider (e.g., 'hubspot', 'zendesk')
            provider_class: Provider class implementation
            
        Raises:
            ValueError: If provider doesn't implement required interface
            ValueError: If provider with same name already registered
        """
        # Validate provider type
        if not isinstance(provider_type, ProviderType):
            raise ValueError(f"Invalid provider type: {provider_type}")
        
        # Validate provider class
        if not inspect.isclass(provider_class):
            raise ValueError(f"Provider must be a class: {provider_class}")
        
        if not issubclass(provider_class, ProviderPlugin):
            raise ValueError(
                f"Provider {provider_class.__name__} must inherit from ProviderPlugin"
            )
        
        # Validate type-specific interface
        if provider_type == ProviderType.CRM and not issubclass(provider_class, CRMProvider):
            raise ValueError(
                f"CRM provider {provider_class.__name__} must inherit from CRMProvider"
            )
        elif provider_type == ProviderType.HELPDESK and not issubclass(provider_class, HelpdeskProvider):
            raise ValueError(
                f"Helpdesk provider {provider_class.__name__} must inherit from HelpdeskProvider"
            )
        elif provider_type == ProviderType.CALENDAR and not issubclass(provider_class, CalendarProvider):
            raise ValueError(
                f"Calendar provider {provider_class.__name__} must inherit from CalendarProvider"
            )
        
        # Check if already registered
        if provider_name in self._providers[provider_type]:
            logger.warning(
                f"Provider {provider_name} already registered for {provider_type.value}, "
                f"overwriting with {provider_class.__name__}"
            )
        
        # Register the provider
        self._providers[provider_type][provider_name] = provider_class
        
        # Store metadata
        full_name = f"{provider_type.value}:{provider_name}"
        self._metadata[full_name] = {
            "provider_type": provider_type.value,
            "provider_name": provider_name,
            "class_name": provider_class.__name__,
            "module": provider_class.__module__
        }
        
        logger.info(
            f"Registered provider: {provider_type.value}/{provider_name} "
            f"-> {provider_class.__name__}"
        )
    
    def get_provider_class(
        self,
        provider_type: ProviderType,
        provider_name: str
    ) -> Optional[Type[ProviderPlugin]]:
        """
        Get provider class by type and name.
        
        Args:
            provider_type: Type of provider
            provider_name: Name of provider
            
        Returns:
            Provider class or None if not found
        """
        return self._providers.get(provider_type, {}).get(provider_name)
    
    def get_provider(
        self,
        tenant_id: str,
        provider_type: ProviderType,
        provider_name: Optional[str] = None
    ) -> Type[ProviderPlugin]:
        """
        Get provider class for instantiation.
        
        Args:
            tenant_id: Tenant identifier (for future multi-tenancy)
            provider_type: Type of provider
            provider_name: Specific provider name (optional, uses default)
            
        Returns:
            Provider class
            
        Raises:
            ValueError: If provider not found or not configured
        """
        # If no provider name specified, get the first registered provider of this type
        if not provider_name:
            providers = self._providers.get(provider_type, {})
            if not providers:
                raise ValueError(
                    f"No providers registered for type: {provider_type.value}"
                )
            provider_name = next(iter(providers.keys()))
            logger.debug(f"Using default provider: {provider_name} for {provider_type.value}")
        
        provider_class = self.get_provider_class(provider_type, provider_name)
        if not provider_class:
            raise ValueError(
                f"Provider not found: {provider_type.value}/{provider_name}"
            )
        
        return provider_class
    
    def list_providers(
        self,
        provider_type: Optional[ProviderType] = None
    ) -> List[str]:
        """
        List all registered provider names.
        
        Args:
            provider_type: Filter by provider type (optional)
            
        Returns:
            List of provider names in format "type:name"
        """
        if provider_type:
            return [
                f"{provider_type.value}:{name}"
                for name in self._providers.get(provider_type, {}).keys()
            ]
        else:
            providers = []
            for ptype, pnames in self._providers.items():
                providers.extend([f"{ptype.value}:{name}" for name in pnames.keys()])
            return providers
    
    def get_providers_by_type(
        self,
        provider_type: ProviderType
    ) -> Dict[str, Type[ProviderPlugin]]:
        """
        Get all providers of a specific type.
        
        Args:
            provider_type: Type of provider
            
        Returns:
            Dictionary mapping provider names to classes
        """
        return self._providers.get(provider_type, {}).copy()
    
    def is_registered(
        self,
        provider_type: ProviderType,
        provider_name: str
    ) -> bool:
        """
        Check if provider is registered.
        
        Args:
            provider_type: Type of provider
            provider_name: Name of provider
            
        Returns:
            True if provider is registered
        """
        return provider_name in self._providers.get(provider_type, {})
    
    def get_metadata(
        self,
        provider_type: ProviderType,
        provider_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a provider.
        
        Args:
            provider_type: Type of provider
            provider_name: Name of provider
            
        Returns:
            Provider metadata or None if not found
        """
        full_name = f"{provider_type.value}:{provider_name}"
        return self._metadata.get(full_name)
    
    def get_capabilities(
        self,
        provider_type: ProviderType,
        provider_name: str
    ) -> List[ProviderCapability]:
        """
        Get capabilities supported by a provider.
        
        Args:
            provider_type: Type of provider
            provider_name: Name of provider
            
        Returns:
            List of supported capabilities
            
        Raises:
            ValueError: If provider not found
        """
        provider_class = self.get_provider_class(provider_type, provider_name)
        if not provider_class:
            raise ValueError(
                f"Provider not found: {provider_type.value}/{provider_name}"
            )
        
        # Create temporary instance to get capabilities
        temp_instance = provider_class({})
        return temp_instance.supported_capabilities
    
    def discover_providers(self, package_path: str = None) -> int:
        """
        Automatically discover and register providers in a package.
        
        Args:
            package_path: Path to providers package (default: current package)
            
        Returns:
            Number of providers discovered and registered
        """
        if package_path is None:
            # Use current package
            import apps.adapter.src.providers as providers_pkg
            package_path = providers_pkg.__path__
            package_name = providers_pkg.__name__
        else:
            package_name = package_path
        
        discovered = 0
        
        # Discover all submodules
        for importer, modname, ispkg in pkgutil.walk_packages(
            package_path,
            prefix=f"{package_name}."
        ):
            if ispkg:
                continue
            
            try:
                # Import the module
                module = importlib.import_module(modname)
                
                # Find all provider classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Skip imported classes
                    if obj.__module__ != modname:
                        continue
                    
                    # Check if it's a provider
                    if not issubclass(obj, ProviderPlugin) or obj is ProviderPlugin:
                        continue
                    
                    # Skip base classes
                    if obj in [CRMProvider, HelpdeskProvider, CalendarProvider]:
                        continue
                    
                    # Determine provider type
                    provider_type = None
                    if issubclass(obj, CRMProvider):
                        provider_type = ProviderType.CRM
                    elif issubclass(obj, HelpdeskProvider):
                        provider_type = ProviderType.HELPDESK
                    elif issubclass(obj, CalendarProvider):
                        provider_type = ProviderType.CALENDAR
                    
                    if provider_type:
                        # Get provider name from class
                        temp_instance = obj({})
                        provider_name = temp_instance.provider_name
                        
                        # Register it
                        self.register_provider(provider_type, provider_name, obj)
                        discovered += 1
                        
            except Exception as e:
                logger.warning(f"Failed to discover providers in {modname}: {e}")
        
        logger.info(f"Discovered and registered {discovered} providers")
        return discovered
    
    def validate_provider(
        self,
        provider_type: ProviderType,
        provider_name: str
    ) -> bool:
        """
        Validate that a provider properly implements its interface.
        
        Args:
            provider_type: Type of provider
            provider_name: Name of provider
            
        Returns:
            True if provider is valid
            
        Raises:
            ValueError: If provider not found or invalid
        """
        provider_class = self.get_provider_class(provider_type, provider_name)
        if not provider_class:
            raise ValueError(
                f"Provider not found: {provider_type.value}/{provider_name}"
            )
        
        # Check required methods are implemented
        required_methods = [
            'provider_name',
            'supported_capabilities',
            'validate_credentials',
            'execute_action',
            'normalize_response',
            'health_check'
        ]
        
        for method in required_methods:
            if not hasattr(provider_class, method):
                raise ValueError(
                    f"Provider {provider_name} missing required method: {method}"
                )
        
        # Type-specific validation
        if provider_type == ProviderType.CRM:
            crm_methods = ['create_contact', 'update_contact', 'search_contacts', 'add_note']
            for method in crm_methods:
                if not hasattr(provider_class, method):
                    raise ValueError(
                        f"CRM provider {provider_name} missing required method: {method}"
                    )
        
        elif provider_type == ProviderType.HELPDESK:
            helpdesk_methods = ['create_ticket', 'update_ticket', 'search_tickets', 'add_comment']
            for method in helpdesk_methods:
                if not hasattr(provider_class, method):
                    raise ValueError(
                        f"Helpdesk provider {provider_name} missing required method: {method}"
                    )
        
        elif provider_type == ProviderType.CALENDAR:
            calendar_methods = ['check_availability', 'create_event', 'update_event', 'cancel_event', 'list_events']
            for method in calendar_methods:
                if not hasattr(provider_class, method):
                    raise ValueError(
                        f"Calendar provider {provider_name} missing required method: {method}"
                    )
        
        return True
    
    def clear(self):
        """Clear all registered providers."""
        for provider_type in self._providers:
            self._providers[provider_type].clear()
        self._metadata.clear()
        logger.info("Cleared all registered providers")


# Global registry instance
_global_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """
    Get the global provider registry instance.
    
    Returns:
        Global provider registry
    """
    return _global_registry


def register_provider(
    provider_type: ProviderType,
    provider_name: str
):
    """
    Decorator for automatic provider registration.
    
    Usage:
        @register_provider(ProviderType.CRM, "hubspot")
        class HubSpotProvider(CRMProvider):
            ...
    
    Args:
        provider_type: Type of provider
        provider_name: Unique provider name
    """
    def decorator(cls):
        _global_registry.register_provider(provider_type, provider_name, cls)
        return cls
    return decorator