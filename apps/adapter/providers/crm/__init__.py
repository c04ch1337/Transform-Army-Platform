"""CRM provider implementations."""

from ..registry import register_provider, ProviderType
from .hubspot import HubSpotProvider
from .salesforce import SalesforceProvider

# Register providers with the global registry
register_provider(ProviderType.CRM, "hubspot")(HubSpotProvider)
register_provider(ProviderType.CRM, "salesforce")(SalesforceProvider)

__all__ = ["HubSpotProvider", "SalesforceProvider"]