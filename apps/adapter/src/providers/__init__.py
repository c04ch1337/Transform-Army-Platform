"""
Provider system for Transform Army AI Adapter Service.

This module provides the provider abstraction layer, including base classes,
factory, and provider implementations.
"""

from .base import (
    ProviderPlugin,
    ProviderCapability,
    ProviderError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError
)
from .factory import (
    ProviderFactory,
    ProviderRegistry,
    ProviderType,
    get_factory,
    get_registry,
    register_provider
)


__all__ = [
    "ProviderPlugin",
    "ProviderCapability",
    "ProviderError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "ProviderFactory",
    "ProviderRegistry",
    "ProviderType",
    "get_factory",
    "get_registry",
    "register_provider"
]