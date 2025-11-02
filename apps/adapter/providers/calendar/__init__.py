"""Calendar provider implementations."""

from ..registry import register_provider, ProviderType
from .google import GoogleCalendarProvider

# Register providers with the global registry
register_provider(ProviderType.CALENDAR, "google")(GoogleCalendarProvider)

__all__ = ["GoogleCalendarProvider"]