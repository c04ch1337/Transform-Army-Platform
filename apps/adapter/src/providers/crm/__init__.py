"""CRM provider implementations."""

from .hubspot import HubSpotProvider
from .salesforce import SalesforceProvider

__all__ = ["HubSpotProvider", "SalesforceProvider"]