"""Email provider implementations."""

from ..registry import register_provider, ProviderType
from .gmail import GmailProvider

# Register providers with the global registry
register_provider(ProviderType.EMAIL, "gmail")(GmailProvider)

__all__ = ["GmailProvider"]