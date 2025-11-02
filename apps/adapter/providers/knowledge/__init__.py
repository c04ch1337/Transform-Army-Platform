"""Knowledge provider implementations."""

from ..registry import register_provider, ProviderType
from .local import LocalKnowledgeProvider
from .stub import StubKnowledgeProvider

# Register providers with the global registry
register_provider(ProviderType.KNOWLEDGE, "local")(LocalKnowledgeProvider)
register_provider(ProviderType.KNOWLEDGE, "stub")(StubKnowledgeProvider)

__all__ = ["LocalKnowledgeProvider", "StubKnowledgeProvider"]