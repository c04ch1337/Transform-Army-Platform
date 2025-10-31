"""Helpdesk provider implementations."""

from .zendesk import ZendeskProvider
from ..factory import register_provider


# Register helpdesk providers with the factory
register_provider(ZendeskProvider)


__all__ = ["ZendeskProvider"]