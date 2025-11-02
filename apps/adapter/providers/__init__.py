"""Provider implementations for Transform Army AI."""

from .base import (
    ProviderPlugin,
    ProviderCapability,
    ProviderError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    CRMProvider,
    HelpdeskProvider,
    CalendarProvider
)
from .factory import ProviderFactory, provider_registry, register_provider as factory_register_provider
from .registry import (
    ProviderRegistry,
    ProviderType,
    get_registry,
    register_provider
)

# Import all provider modules to trigger registration
# Provider classes will auto-register via decorators in their __init__.py files
from . import crm
from . import helpdesk
from . import calendar
from . import email
from . import knowledge

__all__ = [
    "ProviderPlugin",
    "ProviderCapability",
    "ProviderError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "CRMProvider",
    "HelpdeskProvider",
    "CalendarProvider",
    "ProviderFactory",
    "ProviderRegistry",
    "ProviderType",
    "get_registry",
    "register_provider",
    "provider_registry",
    "factory_register_provider",
]