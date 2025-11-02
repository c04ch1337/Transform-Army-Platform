"""
Security configuration and settings.

This module defines security-related configuration including CORS policies,
rate limits, session settings, password policies, and environment-specific
security levels following OWASP guidelines.
"""

from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class SecurityLevel(str, Enum):
    """Security level for different environments."""
    MINIMAL = "minimal"      # Development only
    STANDARD = "standard"    # Staging
    STRICT = "strict"        # Production


class PasswordPolicy(BaseModel):
    """Password policy requirements."""
    min_length: int = Field(default=12, ge=8)
    require_uppercase: bool = Field(default=True)
    require_lowercase: bool = Field(default=True)
    require_digits: bool = Field(default=True)
    require_special: bool = Field(default=True)
    max_age_days: Optional[int] = Field(default=90, ge=30)
    prevent_reuse: int = Field(default=5, ge=3)


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    enabled: bool = Field(default=True)
    
    # Global limits
    requests_per_minute: int = Field(default=60, ge=1)
    requests_per_hour: int = Field(default=1000, ge=1)
    
    # Per-endpoint limits
    endpoint_limits: Dict[str, int] = Field(
        default_factory=lambda: {
            "/api/v1/auth/login": 5,        # 5 per minute
            "/api/v1/auth/register": 3,     # 3 per minute
            "/api/v1/*/create": 30,         # 30 per minute
            "/api/v1/*/update": 50,         # 50 per minute
            "/api/v1/*/delete": 20,         # 20 per minute
        }
    )
    
    # IP-based limits
    max_requests_per_ip: int = Field(default=100, ge=1)
    
    # Tenant-based limits
    max_requests_per_tenant: int = Field(default=200, ge=1)
    
    # Exponential backoff
    enable_exponential_backoff: bool = Field(default=True)
    backoff_threshold: int = Field(default=3, ge=1)  # Number of violations
    backoff_duration_seconds: int = Field(default=300, ge=60)  # 5 minutes
    
    # Allow list (bypass rate limiting)
    ip_allow_list: List[str] = Field(default_factory=list)


class SessionConfig(BaseModel):
    """Session management configuration."""
    timeout_minutes: int = Field(default=30, ge=5)
    absolute_timeout_minutes: int = Field(default=480, ge=60)  # 8 hours
    secure_cookie: bool = Field(default=True)
    httponly_cookie: bool = Field(default=True)
    samesite: str = Field(default="lax")
    
    @field_validator("samesite")
    @classmethod
    def validate_samesite(cls, v: str) -> str:
        """Validate SameSite cookie attribute."""
        valid_values = ["strict", "lax", "none"]
        if v.lower() not in valid_values:
            raise ValueError(f"samesite must be one of {valid_values}")
        return v.lower()


class CorsConfig(BaseModel):
    """CORS policy configuration."""
    enabled: bool = Field(default=True)
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    allowed_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH"]
    )
    allowed_headers: List[str] = Field(
        default_factory=lambda: ["*"]
    )
    allow_credentials: bool = Field(default=True)
    max_age: int = Field(default=3600, ge=0)


class SecurityHeadersConfig(BaseModel):
    """Security headers configuration."""
    
    # Content Security Policy
    content_security_policy: str = Field(
        default=(
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.relevanceai.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    )
    
    # Strict-Transport-Security (HSTS)
    strict_transport_security: str = Field(
        default="max-age=31536000; includeSubDomains; preload"
    )
    
    # X-Frame-Options
    x_frame_options: str = Field(default="DENY")
    
    # X-Content-Type-Options
    x_content_type_options: str = Field(default="nosniff")
    
    # X-XSS-Protection
    x_xss_protection: str = Field(default="1; mode=block")
    
    # Referrer-Policy
    referrer_policy: str = Field(default="strict-origin-when-cross-origin")
    
    # Permissions-Policy
    permissions_policy: str = Field(
        default=(
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
    )


class ApiKeyRequirements(BaseModel):
    """API key security requirements."""
    min_length: int = Field(default=32, ge=16)
    require_prefix: bool = Field(default=True)
    allowed_prefixes: List[str] = Field(
        default_factory=lambda: ["ta_live_", "ta_test_"]
    )
    rotation_days: Optional[int] = Field(default=90, ge=30)
    max_age_days: int = Field(default=365, ge=90)


class SecuritySettings(BaseModel):
    """Comprehensive security settings."""
    
    # Environment-based security level
    security_level: SecurityLevel = Field(default=SecurityLevel.STANDARD)
    
    # Component configurations
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    headers: SecurityHeadersConfig = Field(default_factory=SecurityHeadersConfig)
    password_policy: PasswordPolicy = Field(default_factory=PasswordPolicy)
    api_key_requirements: ApiKeyRequirements = Field(
        default_factory=ApiKeyRequirements
    )
    
    # Security features
    enable_csrf_protection: bool = Field(default=True)
    enable_audit_logging: bool = Field(default=True)
    enable_ip_filtering: bool = Field(default=False)
    enable_geo_blocking: bool = Field(default=False)
    
    # Blocked IPs and countries
    ip_block_list: List[str] = Field(default_factory=list)
    country_block_list: List[str] = Field(default_factory=list)
    
    # Input validation
    max_request_size_bytes: int = Field(default=10485760, ge=1024)  # 10MB
    max_file_upload_size_bytes: int = Field(default=5242880, ge=1024)  # 5MB
    allowed_file_types: List[str] = Field(
        default_factory=lambda: [
            ".pdf", ".docx", ".txt", ".csv", ".json", ".xml"
        ]
    )
    
    # Encryption
    encryption_algorithm: str = Field(default="AES-256-GCM")
    key_derivation_iterations: int = Field(default=100000, ge=10000)
    
    @classmethod
    def for_environment(cls, environment: str) -> "SecuritySettings":
        """
        Create security settings appropriate for the given environment.
        
        Args:
            environment: Environment name (development, staging, production)
            
        Returns:
            SecuritySettings configured for the environment
        """
        env_lower = environment.lower()
        
        if env_lower == "production":
            return cls(
                security_level=SecurityLevel.STRICT,
                rate_limit=RateLimitConfig(
                    requests_per_minute=100,
                    requests_per_hour=2000,
                    enable_exponential_backoff=True
                ),
                session=SessionConfig(
                    timeout_minutes=15,
                    absolute_timeout_minutes=240,
                    secure_cookie=True,
                    httponly_cookie=True,
                    samesite="strict"
                ),
                cors=CorsConfig(
                    allowed_origins=[],  # Must be explicitly configured
                    allow_credentials=True
                ),
                headers=SecurityHeadersConfig(
                    x_frame_options="DENY",
                    strict_transport_security=(
                        "max-age=31536000; includeSubDomains; preload"
                    )
                ),
                enable_csrf_protection=True,
                enable_audit_logging=True,
                enable_ip_filtering=True
            )
        
        elif env_lower == "staging":
            return cls(
                security_level=SecurityLevel.STANDARD,
                rate_limit=RateLimitConfig(
                    requests_per_minute=200,
                    requests_per_hour=5000
                ),
                session=SessionConfig(
                    timeout_minutes=30,
                    secure_cookie=True
                ),
                enable_csrf_protection=True,
                enable_audit_logging=True
            )
        
        else:  # development
            return cls(
                security_level=SecurityLevel.MINIMAL,
                rate_limit=RateLimitConfig(
                    enabled=False  # Disabled in dev for convenience
                ),
                session=SessionConfig(
                    timeout_minutes=480,
                    secure_cookie=False,  # Allow non-HTTPS in dev
                    httponly_cookie=True
                ),
                cors=CorsConfig(
                    allowed_origins=["*"],
                    allow_credentials=True
                ),
                enable_csrf_protection=False,  # Simplified dev experience
                enable_audit_logging=True
            )
    
    def is_production(self) -> bool:
        """Check if configured for production security."""
        return self.security_level == SecurityLevel.STRICT
    
    def is_development(self) -> bool:
        """Check if configured for development."""
        return self.security_level == SecurityLevel.MINIMAL