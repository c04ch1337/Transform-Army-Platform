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
from .factory import ProviderFactory, provider_registry, register_provider

# Import all provider modules to trigger registration
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
    "provider_registry",
    "register_provider",
]