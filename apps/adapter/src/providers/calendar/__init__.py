"""
Calendar provider implementations.

This module registers all available calendar providers.
"""

from ..factory import register_provider
from .google import GoogleCalendarProvider


# Register calendar providers
register_provider(GoogleCalendarProvider)


__all__ = ["GoogleCalendarProvider"]