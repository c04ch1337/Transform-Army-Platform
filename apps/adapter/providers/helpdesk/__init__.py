"""Helpdesk provider implementations."""

from ..registry import register_provider, ProviderType
from .zendesk import ZendeskProvider

# Register providers with the global registry
register_provider(ProviderType.HELPDESK, "zendesk")(ZendeskProvider)

__all__ = ["ZendeskProvider"]