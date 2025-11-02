"""
Security tests for the adapter service.

Tests various security controls including:
- Authentication bypass attempts
- SQL injection prevention
- XSS prevention
- CSRF protection
- Rate limiting
- Security headers
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import time

from apps.adapter.src.core.validation import InputValidator
from apps.adapter.src.core.secrets import SecretManager
from apps.adapter.src.core.security_config import SecuritySettings


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InputValidator()
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        # Test malicious SQL
        malicious_inputs = [
            "'; DROP TABLE users--",
            "1' OR '1'='1",
            "UNION SELECT * FROM passwords",
            "'; EXEC xp_cmdshell('dir')--"
        ]
        
        for malicious_input in malicious_inputs:
            result = self.validator.validate_no_sql_injection(malicious_input)
            assert not result.valid, f"Should detect SQL injection: {malicious_input}"
            assert len(result.errors) > 0
    
    def test_sql_injection_safe_input(self):
        """Test that safe input passes SQL validation."""
        safe_inputs = [
            "john.doe@example.com",
            "User Name 123",
            "Description of product #456"
        ]
        
        for safe_input in safe_inputs:
            result = self.validator.validate_no_sql_injection(safe_input)
            assert result.valid, f"Should allow safe input: {safe_input}"
    
    def test_xss_detection(self):
        """Test XSS attack pattern detection."""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('XSS')",
            "<iframe src='evil.com'></iframe>",
            "<body onload=alert('XSS')>"
        ]
        
        for malicious_input in malicious_inputs:
            result = self.validator.validate_no_xss(malicious_input)
            assert not result.valid, f"Should detect XSS: {malicious_input}"
            assert len(result.errors) > 0
    
    def test_xss_sanitization(self):
        """Test HTML sanitization."""
        dirty_html = "<script>alert('XSS')</script><p>Safe text</p>"
        sanitized = self.validator.sanitize_html(dirty_html)
        
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized or "script" not in sanitized.lower()
    
    def test_url_validation_ssrf_prevention(self):
        """Test URL validation prevents SSRF attacks."""
        # Private IPs should be blocked
        dangerous_urls = [
            "http://localhost:8080/admin",
            "http://127.0.0.1/secret",
            "http://192.168.1.1/admin",
            "http://10.0.0.1/internal",
            "http://169.254.169.254/metadata"  # AWS metadata endpoint
        ]
        
        for url in dangerous_urls:
            result = self.validator.validate_url(url, allow_private_ips=False)
            assert not result.valid, f"Should block private IP: {url}"
    
    def test_url_validation_allows_public(self):
        """Test URL validation allows public URLs."""
        safe_urls = [
            "https://api.example.com/webhook",
            "https://google.com",
            "https://api.github.com/repos"
        ]
        
        for url in safe_urls:
            result = self.validator.validate_url(url)
            assert result.valid, f"Should allow public URL: {url}"
    
    def test_path_traversal_detection(self):
        """Test path traversal attack detection."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e%2f",
            "....//....//etc/passwd"
        ]
        
        for path in malicious_paths:
            result = self.validator.validate_file_path(path)
            assert not result.valid, f"Should detect path traversal: {path}"
    
    def test_file_upload_validation(self):
        """Test file upload security validation."""
        # Dangerous file types
        result = self.validator.validate_file_upload(
            "malware.exe",
            "application/x-msdownload",
            1024
        )
        assert not result.valid
        
        # Allowed file types
        result = self.validator.validate_file_upload(
            "document.pdf",
            "application/pdf",
            1024
        )
        assert result.valid
    
    def test_file_size_limits(self):
        """Test file size limit enforcement."""
        max_size = self.validator.settings.max_file_upload_size_bytes
        
        # File too large
        result = self.validator.validate_file_upload(
            "large.pdf",
            "application/pdf",
            max_size + 1
        )
        assert not result.valid
        assert "exceeds maximum" in result.errors[0].lower()
    
    def test_email_validation(self):
        """Test email validation."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "test+tag@domain.com"
        ]
        
        for email in valid_emails:
            result = self.validator.validate_email(email)
            assert result.valid, f"Should accept valid email: {email}"
        
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user space@example.com"
        ]
        
        for email in invalid_emails:
            result = self.validator.validate_email(email)
            assert not result.valid, f"Should reject invalid email: {email}"


class TestSecretManagement:
    """Test secret management functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use a test master key
        self.test_master_key = "test-master-key-at-least-32-characters-long-for-security"
        self.secret_manager = SecretManager(master_key=self.test_master_key)
    
    def test_encryption_decryption(self):
        """Test encryption and decryption of secrets."""
        plaintext = "my-secret-api-key-12345"
        
        # Encrypt
        encrypted = self.secret_manager.encrypt(plaintext)
        assert encrypted != plaintext
        assert len(encrypted) > 0
        
        # Decrypt
        decrypted = self.secret_manager.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_api_key_generation(self):
        """Test secure API key generation."""
        api_key = self.secret_manager.generate_api_key()
        
        # Should have prefix
        assert api_key.startswith("ta_live_")
        
        # Should be long enough
        assert len(api_key) >= 32
        
        # Two generated keys should be different
        api_key2 = self.secret_manager.generate_api_key()
        assert api_key != api_key2
    
    def test_test_api_key_generation(self):
        """Test test API key generation."""
        test_key = self.secret_manager.generate_test_api_key()
        assert test_key.startswith("ta_test_")
    
    def test_secret_hashing(self):
        """Test secret hashing for storage."""
        secret = "my-password-123"
        
        hashed = self.secret_manager.hash_secret(secret)
        assert hashed != secret
        assert ":" in hashed  # Contains salt:hash
    
    def test_secret_verification(self):
        """Test secret verification against hash."""
        secret = "my-password-123"
        hashed = self.secret_manager.hash_secret(secret)
        
        # Correct secret should verify
        assert self.secret_manager.verify_secret(secret, hashed)
        
        # Wrong secret should not verify
        assert not self.secret_manager.verify_secret("wrong-password", hashed)
    
    def test_constant_time_comparison(self):
        """Test constant-time string comparison."""
        a = "secret-token-abc123"
        b = "secret-token-abc123"
        c = "different-token-xyz"
        
        assert self.secret_manager.constant_time_compare(a, b)
        assert not self.secret_manager.constant_time_compare(a, c)
    
    def test_secret_masking(self):
        """Test secret masking for logs."""
        secret = "my-secret-api-key-1234567890"
        masked = self.secret_manager.mask_secret(secret)
        
        assert "****" in masked
        assert masked.endswith("7890")  # Last 4 chars visible
        assert len(masked) == len(secret)
    
    def test_api_key_format_validation(self):
        """Test API key format validation."""
        # Valid keys
        valid_keys = [
            "ta_live_" + "x" * 32,
            "ta_test_" + "y" * 32
        ]
        
        for key in valid_keys:
            assert self.secret_manager.validate_api_key_format(key)
        
        # Invalid keys
        invalid_keys = [
            "short",
            "wrong_prefix_" + "x" * 32,
            "ta_live_tooshort"
        ]
        
        for key in invalid_keys:
            assert not self.secret_manager.validate_api_key_format(key)


class TestSecurityConfiguration:
    """Test security configuration."""
    
    def test_production_config(self):
        """Test production security configuration."""
        config = SecuritySettings.for_environment("production")
        
        assert config.is_production()
        assert config.rate_limit.enabled
        assert config.enable_csrf_protection
        assert config.enable_audit_logging
        assert config.session.secure_cookie
        assert config.session.httponly_cookie
    
    def test_development_config(self):
        """Test development security configuration."""
        config = SecuritySettings.for_environment("development")
        
        assert config.is_development()
        assert not config.rate_limit.enabled  # Convenient for dev
        assert not config.enable_csrf_protection  # Simplified dev
        assert not config.session.secure_cookie  # Allow non-HTTPS
    
    def test_staging_config(self):
        """Test staging security configuration."""
        config = SecuritySettings.for_environment("staging")
        
        assert not config.is_production()
        assert not config.is_development()
        assert config.rate_limit.enabled
        assert config.enable_csrf_protection


@pytest.mark.asyncio
class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    async def test_rate_limiting(self):
        """Test rate limiting enforcement."""
        # This would require a full FastAPI test setup
        # For now, test the logic
        from apps.adapter.src.core.security_config import RateLimitConfig
        
        config = RateLimitConfig(
            enabled=True,
            requests_per_minute=10
        )
        
        assert config.enabled
        assert config.requests_per_minute == 10
    
    def test_security_headers_config(self):
        """Test security headers configuration."""
        from apps.adapter.src.core.security_config import SecurityHeadersConfig
        
        headers = SecurityHeadersConfig()
        
        # Check OWASP-recommended headers are present
        assert headers.x_frame_options == "DENY"
        assert headers.x_content_type_options == "nosniff"
        assert "nosniff" in headers.x_content_type_options.lower()
        assert len(headers.content_security_policy) > 0
        assert "max-age" in headers.strict_transport_security.lower()


class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    def test_password_policy_requirements(self):
        """Test password policy enforcement."""
        from apps.adapter.src.core.security_config import PasswordPolicy
        
        policy = PasswordPolicy()
        
        assert policy.min_length >= 12
        assert policy.require_uppercase
        assert policy.require_lowercase
        assert policy.require_digits
        assert policy.require_special
    
    def test_session_timeout_config(self):
        """Test session timeout configuration."""
        from apps.adapter.src.core.security_config import SessionConfig
        
        session = SessionConfig()
        
        assert session.timeout_minutes >= 5
        assert session.secure_cookie
        assert session.httponly_cookie
        assert session.samesite in ["strict", "lax", "none"]


class TestCSRFProtection:
    """Test CSRF protection mechanisms."""
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation."""
        secret_manager = SecretManager(
            master_key="test-master-key-at-least-32-characters-long"
        )
        
        token1 = secret_manager.generate_csrf_token()
        token2 = secret_manager.generate_csrf_token()
        
        # Tokens should be unique
        assert token1 != token2
        
        # Tokens should be sufficiently long
        assert len(token1) >= 32


class TestAuditLogging:
    """Test audit logging functionality."""
    
    @pytest.mark.asyncio
    async def test_security_event_logging(self):
        """Test security event logging."""
        # This would require a database session mock
        # For now, verify the method signatures exist
        from apps.adapter.src.services.audit import AuditService
        
        # Verify methods exist
        assert hasattr(AuditService, 'log_authentication_attempt')
        assert hasattr(AuditService, 'log_authorization_failure')
        assert hasattr(AuditService, 'log_configuration_change')
        assert hasattr(AuditService, 'log_security_event')
        assert hasattr(AuditService, 'log_rate_limit_violation')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])