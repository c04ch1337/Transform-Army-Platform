"""
CRM provider implementations.

This module registers all available CRM providers.
"""

from ..factory import register_provider
from .hubspot import HubSpotProvider


# Register CRM providers
register_provider(HubSpotProvider)


__all__ = [
    "HubSpotProvider"
]