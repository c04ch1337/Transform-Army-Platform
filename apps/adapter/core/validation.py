"""
Input validation and sanitization utilities.

This module provides comprehensive input validation to prevent security
vulnerabilities including SQL injection, XSS, path traversal, and other
input-based attacks following OWASP guidelines.
"""

import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ValidationError

from .logging import get_logger
from .security_config import SecuritySettings

logger = get_logger(__name__)


class ValidationResult(BaseModel):
    """Result of input validation."""
    valid: bool
    sanitized_value: Any
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class InputValidator:
    """
    Comprehensive input validator for security.
    
    Provides validation and sanitization for various input types:
    - Text input (XSS prevention)
    - SQL queries (SQL injection prevention)
    - URLs (SSRF prevention)
    - File paths (path traversal prevention)
    - File uploads (malicious file prevention)
    - Email addresses
    - Phone numbers
    """
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\'\s*OR\s*\')",
        r"(xp_cmdshell|sp_executesql)"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers like onclick=
        r"<iframe",
        r"<object",
        r"<embed",
        r"<applet"
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
        r"\\/",
        r"//+"
    ]
    
    def __init__(self, settings: Optional[SecuritySettings] = None):
        """
        Initialize input validator.
        
        Args:
            settings: Security settings for validation rules
        """
        self.settings = settings or SecuritySettings.for_environment("production")
    
    def sanitize_html(self, text: str) -> str:
        """
        Sanitize HTML to prevent XSS attacks.
        
        Args:
            text: Input text that may contain HTML
            
        Returns:
            Sanitized text with HTML entities escaped
        """
        if not text:
            return ""
        
        # HTML escape
        sanitized = html.escape(text)
        
        return sanitized
    
    def sanitize_sql(self, text: str) -> str:
        """
        Sanitize input for SQL queries (basic - prefer parameterized queries).
        
        Args:
            text: Input text that might be used in SQL
            
        Returns:
            Sanitized text
            
        Note:
            This is a defense-in-depth measure. Always use parameterized
            queries as the primary defense against SQL injection.
        """
        if not text:
            return ""
        
        # Remove SQL comments
        text = re.sub(r"--.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        
        # Escape single quotes
        text = text.replace("'", "''")
        
        return text
    
    def validate_no_sql_injection(self, text: str) -> ValidationResult:
        """
        Check for SQL injection patterns.
        
        Args:
            text: Input text to validate
            
        Returns:
            ValidationResult indicating if input is safe
        """
        errors = []
        warnings = []
        
        if not text:
            return ValidationResult(valid=True, sanitized_value="")
        
        text_upper = text.upper()
        
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                errors.append(f"Potential SQL injection detected: {pattern}")
                logger.warning(f"SQL injection attempt detected: {text[:100]}")
        
        sanitized = self.sanitize_sql(text)
        
        return ValidationResult(
            valid=len(errors) == 0,
            sanitized_value=sanitized,
            errors=errors,
            warnings=warnings
        )
    
    def validate_no_xss(self, text: str) -> ValidationResult:
        """
        Check for XSS attack patterns.
        
        Args:
            text: Input text to validate
            
        Returns:
            ValidationResult indicating if input is safe
        """
        errors = []
        warnings = []
        
        if not text:
            return ValidationResult(valid=True, sanitized_value="")
        
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(f"Potential XSS detected: {pattern}")
                logger.warning(f"XSS attempt detected: {text[:100]}")
        
        sanitized = self.sanitize_html(text)
        
        return ValidationResult(
            valid=len(errors) == 0,
            sanitized_value=sanitized,
            errors=errors,
            warnings=warnings
        )
    
    def validate_url(
        self,
        url: str,
        allowed_schemes: Optional[List[str]] = None,
        allow_private_ips: bool = False
    ) -> ValidationResult:
        """
        Validate URL for security issues (SSRF prevention).
        
        Args:
            url: URL to validate
            allowed_schemes: List of allowed URL schemes (default: http, https)
            allow_private_ips: Whether to allow private IP addresses
            
        Returns:
            ValidationResult indicating if URL is safe
        """
        errors = []
        warnings = []
        
        if not url:
            return ValidationResult(valid=False, sanitized_value="", errors=["URL is required"])
        
        if allowed_schemes is None:
            allowed_schemes = ["http", "https"]
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Check scheme
            if parsed.scheme not in allowed_schemes:
                errors.append(f"URL scheme '{parsed.scheme}' not allowed. Allowed: {allowed_schemes}")
            
            # Check for private IPs (SSRF prevention)
            if not allow_private_ips and parsed.hostname:
                if self._is_private_ip(parsed.hostname):
                    errors.append("Private IP addresses are not allowed (SSRF prevention)")
            
            # Check for localhost
            if parsed.hostname in ["localhost", "127.0.0.1", "::1", "0.0.0.0"]:
                if not allow_private_ips:
                    errors.append("Localhost URLs are not allowed (SSRF prevention)")
            
            sanitized = url
            
        except Exception as e:
            errors.append(f"Invalid URL format: {str(e)}")
            sanitized = ""
        
        return ValidationResult(
            valid=len(errors) == 0,
            sanitized_value=sanitized,
            errors=errors,
            warnings=warnings
        )
    
    def _is_private_ip(self, hostname: str) -> bool:
        """
        Check if hostname is a private IP address.
        
        Args:
            hostname: Hostname or IP address
            
        Returns:
            True if hostname is a private IP
        """
        try:
            import ipaddress
            ip = ipaddress.ip_address(hostname)
            return ip.is_private
        except:
            return False
    
    def validate_file_path(
        self,
        path: str,
        allowed_base_paths: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate file path for path traversal attacks.
        
        Args:
            path: File path to validate
            allowed_base_paths: List of allowed base paths
            
        Returns:
            ValidationResult indicating if path is safe
        """
        errors = []
        warnings = []
        
        if not path:
            return ValidationResult(valid=False, sanitized_value="", errors=["Path is required"])
        
        # Check for path traversal patterns
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                errors.append(f"Path traversal detected: {pattern}")
                logger.warning(f"Path traversal attempt: {path}")
        
        # Normalize path
        try:
            normalized = Path(path).resolve()
            sanitized = str(normalized)
            
            # Check if path is within allowed base paths
            if allowed_base_paths:
                is_allowed = any(
                    str(normalized).startswith(str(Path(base).resolve()))
                    for base in allowed_base_paths
                )
                if not is_allowed:
                    errors.append("Path is outside allowed directories")
        
        except Exception as e:
            errors.append(f"Invalid path: {str(e)}")
            sanitized = ""
        
        return ValidationResult(
            valid=len(errors) == 0,
            sanitized_value=sanitized,
            errors=errors,
            warnings=warnings
        )
    
    def validate_file_upload(
        self,
        filename: str,
        content_type: str,
        file_size: int
    ) -> ValidationResult:
        """
        Validate file upload for security.
        
        Args:
            filename: Name of uploaded file
            content_type: MIME type of file
            file_size: Size of file in bytes
            
        Returns:
            ValidationResult indicating if file is safe to accept
        """
        errors = []
        warnings = []
        
        # Check file size
        if file_size > self.settings.max_file_upload_size_bytes:
            errors.append(
                f"File size {file_size} exceeds maximum "
                f"{self.settings.max_file_upload_size_bytes} bytes"
            )
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.settings.allowed_file_types:
            errors.append(
                f"File type '{file_ext}' not allowed. "
                f"Allowed: {self.settings.allowed_file_types}"
            )
        
        # Check for double extensions (e.g., file.php.txt)
        if filename.count('.') > 1:
            warnings.append("File has multiple extensions - potentially suspicious")
        
        # Check for executable extensions
        dangerous_extensions = [
            ".exe", ".bat", ".cmd", ".sh", ".ps1", ".app", ".jar",
            ".php", ".asp", ".aspx", ".jsp", ".cgi"
        ]
        if file_ext in dangerous_extensions:
            errors.append(f"Executable file type '{file_ext}' not allowed")
        
        # Sanitize filename
        sanitized_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        return ValidationResult(
            valid=len(errors) == 0,
            sanitized_value=sanitized_filename,
            errors=errors,
            warnings=warnings
        )
    
    def validate_email(self, email: str) -> ValidationResult:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            ValidationResult indicating if email is valid
        """
        errors = []
        
        if not email:
            return ValidationResult(valid=False, sanitized_value="", errors=["Email is required"])
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            errors.append("Invalid email format")
        
        # Check for SQL injection in email
        sql_result = self.validate_no_sql_injection(email)
        if not sql_result.valid:
            errors.extend(sql_result.errors)
        
        sanitized = email.lower().strip()
        
        return ValidationResult(
            valid=len(errors) == 0,
            sanitized_value=sanitized,
            errors=errors
        )
    
    def validate_phone(self, phone: str) -> ValidationResult:
        """
        Validate phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            ValidationResult indicating if phone is valid
        """
        errors = []
        
        if not phone:
            return ValidationResult(valid=False, sanitized_value="", errors=["Phone is required"])
        
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
        
        # Check if it's all digits (possibly with + prefix)
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            errors.append("Invalid phone format")
        
        return ValidationResult(
            valid=len(errors) == 0,
            sanitized_value=cleaned,
            errors=errors
        )
    
    def validate_json_schema(
        self,
        data: Dict[str, Any],
        required_fields: List[str],
        field_types: Dict[str, type]
    ) -> ValidationResult:
        """
        Validate JSON data against schema.
        
        Args:
            data: JSON data to validate
            required_fields: List of required field names
            field_types: Dictionary mapping field names to expected types
            
        Returns:
            ValidationResult indicating if data matches schema
        """
        errors = []
        warnings = []
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Required field '{field}' is missing")
        
        # Check field types
        for field, expected_type in field_types.items():
            if field in data:
                if not isinstance(data[field], expected_type):
                    errors.append(
                        f"Field '{field}' has wrong type. "
                        f"Expected {expected_type.__name__}, "
                        f"got {type(data[field]).__name__}"
                    )
        
        return ValidationResult(
            valid=len(errors) == 0,
            sanitized_value=data,
            errors=errors,
            warnings=warnings
        )
    
    def validate_request_size(self, size: int) -> ValidationResult:
        """
        Validate request size against limits.
        
        Args:
            size: Request size in bytes
            
        Returns:
            ValidationResult indicating if size is acceptable
        """
        errors = []
        
        if size > self.settings.max_request_size_bytes:
            errors.append(
                f"Request size {size} bytes exceeds maximum "
                f"{self.settings.max_request_size_bytes} bytes"
            )
        
        return ValidationResult(
            valid=len(errors) == 0,
            sanitized_value=size,
            errors=errors
        )