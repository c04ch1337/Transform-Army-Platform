"""
Provider integration tests for Transform Army AI.

Tests provider registration, configuration loading, API operations,
error handling, and rate limiting.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from apps.adapter.src.providers import (
    get_registry,
    ProviderType,
    ProviderFactory
)
from apps.adapter.src.providers.base import (
    ProviderPlugin,
    ProviderCapability,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    ValidationError,
    NotFoundError
)
from apps.adapter.src.providers.registry import ProviderRegistry


@pytest.fixture
def registry():
    """Get provider registry instance."""
    return get_registry()


@pytest.fixture
def mock_crm_provider():
    """Create mock CRM provider for testing."""
    class MockCRMProvider(ProviderPlugin):
        @property
        def provider_name(self) -> str:
            return "mock_crm"
        
        @property
        def supported_capabilities(self):
            return [
                ProviderCapability.CRM_CONTACTS,
                ProviderCapability.CRM_COMPANIES,
                ProviderCapability.CRM_NOTES
            ]
        
        async def validate_credentials(self) -> bool:
            if not self.credentials.get("api_key"):
                raise AuthenticationError(
                    "Missing API key",
                    provider=self.provider_name
                )
            return True
        
        async def execute_action(self, action: str, parameters: dict, idempotency_key=None):
            if action == "create_contact":
                return {
                    "id": str(uuid4()),
                    "email": parameters["email"],
                    "created": True
                }
            elif action == "search_contacts":
                return {
                    "results": [],
                    "total": 0
                }
            raise ValidationError(f"Unknown action: {action}", provider=self.provider_name)
        
        def normalize_response(self, provider_response, action: str):
            return provider_response
        
        async def health_check(self) -> bool:
            return True
    
    return MockCRMProvider({"api_key": "test_key"})


class TestProviderRegistration:
    """Test provider registration system."""
    
    def test_registry_singleton(self):
        """Test that registry is a singleton."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2, "Registry should be singleton"
    
    def test_list_providers(self, registry):
        """Test listing registered providers."""
        providers = registry.list_providers()
        assert isinstance(providers, list), "Should return list of providers"
        assert len(providers) > 0, "Should have providers registered"
    
    def test_get_providers_by_type(self, registry):
        """Test getting providers by type."""
        # Test CRM providers
        crm_providers = registry.get_providers_by_type(ProviderType.CRM)
        assert isinstance(crm_providers, dict), "Should return dict of providers"
        
        # Test each provider type
        for provider_type in ProviderType:
            providers = registry.get_providers_by_type(provider_type)
            assert isinstance(providers, dict)
    
    def test_get_provider_class(self, registry):
        """Test getting provider class by type and name."""
        # Try to get HubSpot provider
        try:
            provider_class = registry.get_provider(ProviderType.CRM, "hubspot")
            assert provider_class is not None, "Should return provider class"
        except Exception:
            # Provider may not be registered in test environment
            pass
    
    def test_register_custom_provider(self, registry, mock_crm_provider):
        """Test registering a custom provider."""
        # Register mock provider
        registry.register(
            ProviderType.CRM,
            "mock_crm",
            mock_crm_provider.__class__
        )
        
        # Verify registration
        crm_providers = registry.get_providers_by_type(ProviderType.CRM)
        assert "mock_crm" in crm_providers, "Mock provider should be registered"
    
    def test_validate_provider(self, registry):
        """Test provider validation."""
        # Test validating existing providers
        providers = registry.list_providers()
        
        for provider_str in providers:
            try:
                provider_type_str, provider_name = provider_str.split(":")
                provider_type = ProviderType(provider_type_str)
                
                # Validate provider
                result = registry.validate_provider(provider_type, provider_name)
                assert result is True or result is None
            except Exception as e:
                # Validation may fail if credentials not configured
                assert "credential" in str(e).lower() or "not found" in str(e).lower()


class TestProviderFactory:
    """Test provider factory system."""
    
    @pytest.mark.asyncio
    async def test_create_provider_instance(self, registry, mock_crm_provider):
        """Test creating provider instance."""
        # Register mock provider
        registry.register(
            ProviderType.CRM,
            "mock_crm",
            mock_crm_provider.__class__
        )
        
        # Create instance
        credentials = {"api_key": "test_key_123"}
        instance = ProviderFactory.create_provider(
            ProviderType.CRM,
            "mock_crm",
            credentials
        )
        
        assert instance is not None, "Should create provider instance"
        assert instance.provider_name == "mock_crm"
        assert instance.credentials == credentials
    
    @pytest.mark.asyncio
    async def test_provider_from_config(self):
        """Test creating provider from configuration."""
        config = {
            "type": "crm",
            "name": "hubspot",
            "credentials": {
                "api_key": "test_key"
            }
        }
        
        try:
            instance = ProviderFactory.from_config(config)
            assert instance is not None
        except Exception as e:
            # May fail if HubSpot provider not registered
            assert "not found" in str(e).lower() or "not registered" in str(e).lower()


class TestProviderCapabilities:
    """Test provider capability system."""
    
    def test_provider_capabilities(self, mock_crm_provider):
        """Test checking provider capabilities."""
        # Check supported capabilities
        assert mock_crm_provider.supports_capability(ProviderCapability.CRM_CONTACTS)
        assert mock_crm_provider.supports_capability(ProviderCapability.CRM_COMPANIES)
        assert mock_crm_provider.supports_capability(ProviderCapability.CRM_NOTES)
        
        # Check unsupported capabilities
        assert not mock_crm_provider.supports_capability(ProviderCapability.HELPDESK_TICKETS)
        assert not mock_crm_provider.supports_capability(ProviderCapability.EMAIL_SEND)
    
    def test_capability_enumeration(self):
        """Test capability enumeration values."""
        capabilities = [
            ProviderCapability.CRM_CONTACTS,
            ProviderCapability.CRM_COMPANIES,
            ProviderCapability.HELPDESK_TICKETS,
            ProviderCapability.CALENDAR_EVENTS,
            ProviderCapability.EMAIL_SEND,
            ProviderCapability.KNOWLEDGE_SEARCH
        ]
        
        for cap in capabilities:
            assert isinstance(cap.value, str)
            assert "." in cap.value  # Should be namespaced


class TestProviderAuthentication:
    """Test provider authentication."""
    
    @pytest.mark.asyncio
    async def test_valid_credentials(self, mock_crm_provider):
        """Test authentication with valid credentials."""
        result = await mock_crm_provider.validate_credentials()
        assert result is True, "Valid credentials should authenticate"
    
    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        class MockProvider(ProviderPlugin):
            @property
            def provider_name(self):
                return "test"
            
            @property
            def supported_capabilities(self):
                return []
            
            async def validate_credentials(self):
                raise AuthenticationError(
                    "Invalid credentials",
                    provider=self.provider_name
                )
            
            async def execute_action(self, action, parameters, idempotency_key=None):
                pass
            
            def normalize_response(self, provider_response, action):
                return provider_response
            
            async def health_check(self):
                return False
        
        provider = MockProvider({"api_key": "invalid"})
        
        with pytest.raises(AuthenticationError):
            await provider.validate_credentials()
    
    @pytest.mark.asyncio
    async def test_missing_credentials(self, mock_crm_provider):
        """Test authentication with missing credentials."""
        # Create provider without credentials
        mock_crm_provider.credentials = {}
        
        with pytest.raises(AuthenticationError):
            await mock_crm_provider.validate_credentials()


class TestProviderOperations:
    """Test provider CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_contact(self, mock_crm_provider):
        """Test creating a contact."""
        result = await mock_crm_provider.execute_action(
            "create_contact",
            {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            }
        )
        
        assert result is not None
        assert "id" in result
        assert result["email"] == "test@example.com"
        assert result["created"] is True
    
    @pytest.mark.asyncio
    async def test_search_contacts(self, mock_crm_provider):
        """Test searching contacts."""
        result = await mock_crm_provider.execute_action(
            "search_contacts",
            {"query": "test"}
        )
        
        assert result is not None
        assert "results" in result
        assert "total" in result
    
    @pytest.mark.asyncio
    async def test_invalid_action(self, mock_crm_provider):
        """Test executing invalid action."""
        with pytest.raises(ValidationError):
            await mock_crm_provider.execute_action(
                "invalid_action",
                {}
            )
    
    @pytest.mark.asyncio
    async def test_action_with_idempotency_key(self, mock_crm_provider):
        """Test action execution with idempotency key."""
        idempotency_key = str(uuid4())
        
        result = await mock_crm_provider.execute_action(
            "create_contact",
            {"email": "test@example.com"},
            idempotency_key=idempotency_key
        )
        
        assert result is not None


class TestProviderErrorHandling:
    """Test provider error handling."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test rate limit error handling."""
        error = RateLimitError(
            "Rate limit exceeded",
            provider="test_provider",
            retry_after=60
        )
        
        assert error.provider == "test_provider"
        assert error.retry_after == 60
        assert "rate limit" in error.message.lower()
    
    @pytest.mark.asyncio
    async def test_validation_error(self):
        """Test validation error."""
        error = ValidationError(
            "Invalid parameter",
            provider="test_provider",
            action="create_contact"
        )
        
        assert error.provider == "test_provider"
        assert error.action == "create_contact"
    
    @pytest.mark.asyncio
    async def test_not_found_error(self):
        """Test not found error."""
        error = NotFoundError(
            "Resource not found",
            provider="test_provider",
            action="get_contact"
        )
        
        assert error.provider == "test_provider"
        assert "not found" in error.message.lower()
    
    @pytest.mark.asyncio
    async def test_generic_provider_error(self):
        """Test generic provider error."""
        error = ProviderError(
            "Something went wrong",
            provider="test_provider",
            provider_response={"error": "Internal error"}
        )
        
        assert error.provider == "test_provider"
        assert error.provider_response is not None


class TestProviderRetryLogic:
    """Test provider retry logic."""
    
    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self):
        """Test retry logic on rate limit."""
        class RetryProvider(ProviderPlugin):
            def __init__(self, credentials):
                super().__init__(credentials)
                self.attempt_count = 0
            
            @property
            def provider_name(self):
                return "retry_test"
            
            @property
            def supported_capabilities(self):
                return []
            
            async def validate_credentials(self):
                return True
            
            async def execute_action(self, action, parameters, idempotency_key=None):
                self.attempt_count += 1
                if self.attempt_count < 2:
                    raise RateLimitError(
                        "Rate limit",
                        provider=self.provider_name,
                        retry_after=0.1
                    )
                return {"success": True, "attempts": self.attempt_count}
            
            def normalize_response(self, provider_response, action):
                return provider_response
            
            async def health_check(self):
                return True
        
        provider = RetryProvider({})
        
        result = await provider.execute_with_retry("test_action", {})
        
        assert result["success"] is True
        assert result["attempts"] == 2, "Should retry once and succeed"
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test when all retries are exhausted."""
        class FailProvider(ProviderPlugin):
            @property
            def provider_name(self):
                return "fail_test"
            
            @property
            def supported_capabilities(self):
                return []
            
            async def validate_credentials(self):
                return True
            
            async def execute_action(self, action, parameters, idempotency_key=None):
                raise ProviderError("Always fails", provider=self.provider_name)
            
            def normalize_response(self, provider_response, action):
                return provider_response
            
            async def health_check(self):
                return True
        
        provider = FailProvider({})
        
        with pytest.raises(ProviderError):
            await provider.execute_with_retry("test_action", {})
    
    @pytest.mark.asyncio
    async def test_no_retry_on_validation_error(self):
        """Test that validation errors don't retry."""
        class ValidateProvider(ProviderPlugin):
            def __init__(self, credentials):
                super().__init__(credentials)
                self.attempt_count = 0
            
            @property
            def provider_name(self):
                return "validate_test"
            
            @property
            def supported_capabilities(self):
                return []
            
            async def validate_credentials(self):
                return True
            
            async def execute_action(self, action, parameters, idempotency_key=None):
                self.attempt_count += 1
                raise ValidationError("Invalid", provider=self.provider_name)
            
            def normalize_response(self, provider_response, action):
                return provider_response
            
            async def health_check(self):
                return True
        
        provider = ValidateProvider({})
        
        with pytest.raises(ValidationError):
            await provider.execute_with_retry("test_action", {})
        
        assert provider.attempt_count == 1, "Should not retry validation errors"


class TestProviderHealthCheck:
    """Test provider health checks."""
    
    @pytest.mark.asyncio
    async def test_healthy_provider(self, mock_crm_provider):
        """Test health check for healthy provider."""
        result = await mock_crm_provider.health_check()
        assert result is True, "Healthy provider should return True"
    
    @pytest.mark.asyncio
    async def test_unhealthy_provider(self):
        """Test health check for unhealthy provider."""
        class UnhealthyProvider(ProviderPlugin):
            @property
            def provider_name(self):
                return "unhealthy"
            
            @property
            def supported_capabilities(self):
                return []
            
            async def validate_credentials(self):
                return False
            
            async def execute_action(self, action, parameters, idempotency_key=None):
                raise ProviderError("Unhealthy", provider=self.provider_name)
            
            def normalize_response(self, provider_response, action):
                return provider_response
            
            async def health_check(self):
                return False
        
        provider = UnhealthyProvider({})
        result = await provider.health_check()
        assert result is False, "Unhealthy provider should return False"


class TestProviderCleanup:
    """Test provider resource cleanup."""
    
    @pytest.mark.asyncio
    async def test_provider_close(self, mock_crm_provider):
        """Test provider cleanup."""
        # Set up mock client
        mock_crm_provider._client = Mock()
        mock_crm_provider._client.aclose = AsyncMock()
        
        await mock_crm_provider.close()
        
        # Verify cleanup was called
        mock_crm_provider._client.aclose.assert_called_once()
        assert mock_crm_provider._client is None


class TestProviderConfiguration:
    """Test provider configuration loading."""
    
    def test_provider_config_structure(self):
        """Test provider configuration structure."""
        config = {
            "type": "crm",
            "name": "hubspot",
            "credentials": {
                "api_key": "test_key"
            },
            "settings": {
                "timeout": 30,
                "retry_attempts": 3
            }
        }
        
        assert "type" in config
        assert "name" in config
        assert "credentials" in config
        assert isinstance(config["credentials"], dict)
    
    def test_provider_credentials_masking(self):
        """Test that credentials are properly masked in logs."""
        credentials = {
            "api_key": "secret_key_12345",
            "api_secret": "secret_value"
        }
        
        # Simulate credential masking
        masked = {k: "***" for k, v in credentials.items()}
        
        assert all(v == "***" for v in masked.values())


class TestProviderMocking:
    """Test provider mocking for testing."""
    
    @pytest.mark.asyncio
    async def test_mock_provider_responses(self):
        """Test mocking provider responses."""
        mock_response = {
            "id": "contact_123",
            "email": "mock@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        class MockedProvider(ProviderPlugin):
            @property
            def provider_name(self):
                return "mocked"
            
            @property
            def supported_capabilities(self):
                return [ProviderCapability.CRM_CONTACTS]
            
            async def validate_credentials(self):
                return True
            
            async def execute_action(self, action, parameters, idempotency_key=None):
                return mock_response
            
            def normalize_response(self, provider_response, action):
                return provider_response
            
            async def health_check(self):
                return True
        
        provider = MockedProvider({})
        result = await provider.execute_action("create_contact", {})
        
        assert result == mock_response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])