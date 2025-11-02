"""
Secret management utilities.

This module provides secure handling of secrets including:
- Environment variable integration
- Encryption/decryption helpers
- API key generation
- Credential rotation helpers
- Secure storage patterns
"""

import os
import secrets
import hashlib
import hmac
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend

from .logging import get_logger
from .security_config import SecuritySettings

logger = get_logger(__name__)


class SecretManager:
    """
    Manager for secure handling of secrets and credentials.
    
    Provides utilities for:
    - Reading secrets from environment variables
    - Encrypting/decrypting sensitive data
    - Generating secure API keys
    - Credential rotation
    - Secure comparison to prevent timing attacks
    """
    
    def __init__(
        self,
        master_key: Optional[str] = None,
        settings: Optional[SecuritySettings] = None
    ):
        """
        Initialize secret manager.
        
        Args:
            master_key: Master encryption key (from API_SECRET_KEY env var)
            settings: Security settings
        """
        self.settings = settings or SecuritySettings.for_environment("production")
        
        # Get master key from environment or parameter
        self.master_key = master_key or os.environ.get("API_SECRET_KEY")
        if not self.master_key:
            raise ValueError(
                "API_SECRET_KEY environment variable is required for secret management"
            )
        
        # Validate master key length
        if len(self.master_key) < 32:
            raise ValueError("Master key must be at least 32 characters")
        
        # Initialize Fernet cipher for encryption
        self._fernet = self._init_fernet()
        
        logger.info("Secret manager initialized")
    
    def _init_fernet(self) -> Fernet:
        """
        Initialize Fernet cipher with derived key.
        
        Returns:
            Fernet cipher instance
        """
        # Derive a Fernet-compatible key from master key using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"transform-army-ai-salt",  # In production, use unique salt per installation
            iterations=self.settings.key_derivation_iterations,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(self.master_key.encode())
        )
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        encrypted = self._fernet.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            ciphertext: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            Exception: If decryption fails (invalid ciphertext or key)
        """
        if not ciphertext:
            return ""
        
        try:
            encrypted = base64.b64decode(ciphertext.encode())
            decrypted = self._fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data - possible key mismatch")
    
    def get_secret(
        self,
        key: str,
        default: Optional[str] = None,
        required: bool = False
    ) -> Optional[str]:
        """
        Get secret from environment variables.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: Whether the secret is required (raise error if missing)
            
        Returns:
            Secret value or default
            
        Raises:
            ValueError: If required secret is missing
        """
        value = os.environ.get(key, default)
        
        if required and not value:
            raise ValueError(f"Required secret '{key}' is not set")
        
        if value:
            logger.debug(f"Retrieved secret: {key}")
        
        return value
    
    def get_encrypted_secret(
        self,
        key: str,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get and decrypt an encrypted secret from environment.
        
        Args:
            key: Environment variable name (should contain encrypted value)
            default: Default value if not found
            
        Returns:
            Decrypted secret value or default
        """
        encrypted_value = os.environ.get(key)
        
        if not encrypted_value:
            return default
        
        try:
            return self.decrypt(encrypted_value)
        except Exception as e:
            logger.error(f"Failed to decrypt secret '{key}': {e}")
            return default
    
    def generate_api_key(
        self,
        prefix: str = "ta_live_",
        length: int = 32
    ) -> str:
        """
        Generate a secure API key.
        
        Args:
            prefix: Key prefix for identification
            length: Length of random portion (excluding prefix)
            
        Returns:
            Generated API key
        """
        if length < self.settings.api_key_requirements.min_length:
            length = self.settings.api_key_requirements.min_length
        
        # Validate prefix
        if self.settings.api_key_requirements.require_prefix:
            if prefix not in self.settings.api_key_requirements.allowed_prefixes:
                raise ValueError(
                    f"API key prefix must be one of: "
                    f"{self.settings.api_key_requirements.allowed_prefixes}"
                )
        
        # Generate random token
        random_token = secrets.token_urlsafe(length)
        
        api_key = f"{prefix}{random_token}"
        
        logger.info(f"Generated new API key with prefix: {prefix}")
        
        return api_key
    
    def generate_test_api_key(self, length: int = 32) -> str:
        """
        Generate a test API key (for non-production use).
        
        Args:
            length: Length of random portion
            
        Returns:
            Generated test API key
        """
        return self.generate_api_key(prefix="ta_test_", length=length)
    
    def hash_secret(self, secret: str, salt: Optional[str] = None) -> str:
        """
        Hash a secret using SHA-256 (for storage/comparison).
        
        Args:
            secret: Secret to hash
            salt: Optional salt (generated if not provided)
            
        Returns:
            Base64-encoded hash
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for password hashing
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=self.settings.key_derivation_iterations,
            backend=default_backend()
        )
        
        hashed = kdf.derive(secret.encode())
        
        # Combine salt and hash for storage
        combined = f"{salt}:{base64.b64encode(hashed).decode()}"
        
        return combined
    
    def verify_secret(self, secret: str, hashed: str) -> bool:
        """
        Verify a secret against its hash (constant-time comparison).
        
        Args:
            secret: Secret to verify
            hashed: Previously hashed secret (salt:hash format)
            
        Returns:
            True if secret matches hash
        """
        try:
            salt, stored_hash = hashed.split(":", 1)
            
            # Hash the input secret with the same salt
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=self.settings.key_derivation_iterations,
                backend=default_backend()
            )
            
            computed_hash = base64.b64encode(kdf.derive(secret.encode())).decode()
            
            # Constant-time comparison to prevent timing attacks
            return hmac.compare_digest(computed_hash, stored_hash)
            
        except Exception as e:
            logger.error(f"Secret verification failed: {e}")
            return False
    
    def constant_time_compare(self, a: str, b: str) -> bool:
        """
        Compare two strings in constant time (timing attack prevention).
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            True if strings are equal
        """
        return hmac.compare_digest(a.encode(), b.encode())
    
    def mask_secret(self, secret: str, visible_chars: int = 4) -> str:
        """
        Mask a secret for safe display (e.g., in logs).
        
        Args:
            secret: Secret to mask
            visible_chars: Number of characters to show at end
            
        Returns:
            Masked secret (e.g., "****abcd")
        """
        if not secret:
            return ""
        
        if len(secret) <= visible_chars:
            return "*" * len(secret)
        
        return f"{'*' * (len(secret) - visible_chars)}{secret[-visible_chars:]}"
    
    def rotate_credentials(
        self,
        old_key: str,
        generate_new: bool = True
    ) -> Dict[str, str]:
        """
        Helper for credential rotation.
        
        Args:
            old_key: Old API key/credential
            generate_new: Whether to generate new key
            
        Returns:
            Dictionary with old_key and new_key (if generated)
        """
        result = {
            "old_key": old_key,
            "old_key_masked": self.mask_secret(old_key),
            "rotation_time": datetime.utcnow().isoformat() + "Z"
        }
        
        if generate_new:
            new_key = self.generate_api_key()
            result["new_key"] = new_key
            result["new_key_masked"] = self.mask_secret(new_key)
        
        logger.info("Credential rotation initiated")
        
        return result
    
    def check_key_expiry(
        self,
        created_at: datetime,
        max_age_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check if a key has expired or should be rotated.
        
        Args:
            created_at: When the key was created
            max_age_days: Maximum age before rotation (from settings if not provided)
            
        Returns:
            Dictionary with expiry information
        """
        if max_age_days is None:
            max_age_days = self.settings.api_key_requirements.max_age_days
        
        age_days = (datetime.utcnow() - created_at).days
        expires_at = created_at + timedelta(days=max_age_days)
        days_until_expiry = (expires_at - datetime.utcnow()).days
        
        # Warn if key is older than rotation period
        rotation_days = self.settings.api_key_requirements.rotation_days or 90
        should_rotate = age_days >= rotation_days
        
        result = {
            "age_days": age_days,
            "expires_at": expires_at.isoformat() + "Z",
            "days_until_expiry": days_until_expiry,
            "is_expired": days_until_expiry < 0,
            "should_rotate": should_rotate,
            "rotation_recommended": age_days >= (rotation_days * 0.9)  # 90% of rotation period
        }
        
        if result["is_expired"]:
            logger.warning(f"Key expired {abs(days_until_expiry)} days ago")
        elif result["should_rotate"]:
            logger.warning(f"Key rotation recommended (age: {age_days} days)")
        
        return result
    
    def generate_csrf_token(self) -> str:
        """
        Generate a CSRF token.
        
        Returns:
            Secure random CSRF token
        """
        return secrets.token_urlsafe(32)
    
    def validate_api_key_format(self, api_key: str) -> bool:
        """
        Validate API key format against requirements.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if format is valid
        """
        if len(api_key) < self.settings.api_key_requirements.min_length:
            return False
        
        if self.settings.api_key_requirements.require_prefix:
            has_valid_prefix = any(
                api_key.startswith(prefix)
                for prefix in self.settings.api_key_requirements.allowed_prefixes
            )
            if not has_valid_prefix:
                return False
        
        return True
    
    def secure_delete(self, secret: str) -> None:
        """
        Securely delete a secret from memory (overwrite).
        
        Args:
            secret: Secret to delete
            
        Note:
            In Python, this is best-effort due to string immutability and
            garbage collection. For highly sensitive data, consider using
            ctypes or specialized libraries.
        """
        # Best effort to overwrite in Python
        # In practice, use memoryview or ctypes for true secure deletion
        if secret:
            # Create a reference that can be modified
            secret_bytes = bytearray(secret.encode())
            for i in range(len(secret_bytes)):
                secret_bytes[i] = 0
            del secret_bytes
    
    def get_all_secrets(self) -> Dict[str, str]:
        """
        Get all configured secrets (masked for security).
        
        Returns:
            Dictionary of secret keys and masked values
        """
        secrets_dict = {}
        
        # Common secret environment variables
        secret_keys = [
            "API_SECRET_KEY",
            "DATABASE_URL",
            "REDIS_URL",
            "REDIS_PASSWORD",
            "ADAPTER_HUBSPOT_API_KEY",
            "ADAPTER_SALESFORCE_CLIENT_SECRET",
            "ADAPTER_ZENDESK_API_TOKEN",
            "ADAPTER_GOOGLE_CLIENT_SECRET"
        ]
        
        for key in secret_keys:
            value = os.environ.get(key)
            if value:
                secrets_dict[key] = self.mask_secret(value)
            else:
                secrets_dict[key] = "NOT_SET"
        
        return secrets_dict