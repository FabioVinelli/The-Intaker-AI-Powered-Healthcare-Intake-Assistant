"""
HIPAA-compliant sanitizers for healthcare data.
Provides comprehensive data sanitization for XSS and injection prevention.
"""

import re
import html
import bleach
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class HIPAASanitizer:
    """Base class for HIPAA-compliant data sanitization."""
    
    # Common dangerous patterns to remove
    DANGEROUS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'vbscript:', re.IGNORECASE),
        re.compile(r'onload\s*=', re.IGNORECASE),
        re.compile(r'onerror\s*=', re.IGNORECASE),
        re.compile(r'onclick\s*=', re.IGNORECASE),
        re.compile(r'onmouseover\s*=', re.IGNORECASE),
    ]
    
    @classmethod
    def sanitize_input(cls, value: Any) -> str:
        """
        Basic sanitization for any input value.
        
        Args:
            value: Input value to sanitize
            
        Returns:
            str: Sanitized string value
        """
        if value is None:
            return ""
        
        # Convert to string and strip whitespace
        sanitized = str(value).strip()
        
        # Remove dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = pattern.sub('', sanitized)
        
        # HTML encode special characters
        sanitized = html.escape(sanitized)
        
        return sanitized
    
    @classmethod
    def sanitize_phi_field(cls, value: Any, field_name: str) -> str:
        """
        Sanitize PHI fields with additional security measures.
        
        Args:
            value: PHI value to sanitize
            field_name: Name of the PHI field
            
        Returns:
            str: Sanitized PHI value
        """
        if value is None:
            return ""
        
        sanitized = cls.sanitize_input(value)
        
        # Additional PHI-specific sanitization
        # Remove any remaining HTML tags
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
        
        # Log PHI access for HIPAA compliance
        logger.info(f"PHI field '{field_name}' accessed and sanitized", extra={
            'phi_field': field_name,
            'sanitized': True,
            'action': 'sanitize_phi'
        })
        
        return sanitized


class TextSanitizer:
    """Text sanitizer for general text fields."""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        re.compile(r"('|(\\')|(;)|(\\;)|(\|)|(\*)|(%)|(<)|(>))", re.IGNORECASE),
        re.compile(r"(select|insert|update|delete|drop|create|alter|exec|execute)\s", re.IGNORECASE),
        re.compile(r"(union|or|and|where|order|group|having)\s", re.IGNORECASE),
        re.compile(r"(--|#|\*\/|\/\*)", re.IGNORECASE),
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'vbscript:', re.IGNORECASE),
        re.compile(r'data:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
    ]
    
    @classmethod
    def sanitize(cls, value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize general text input.
        
        Args:
            value: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            str: Sanitized text
        """
        if not value:
            return ""
        
        sanitized = str(value).strip()
        
        # Truncate if too long
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Remove SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            sanitized = pattern.sub('', sanitized)
        
        # Remove XSS patterns
        for pattern in cls.XSS_PATTERNS:
            sanitized = pattern.sub('', sanitized)
        
        # HTML escape
        sanitized = html.escape(sanitized)
        
        return sanitized
    
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        """
        Sanitize name fields with specific validation.
        
        Args:
            value: Name to sanitize
            
        Returns:
            str: Sanitized name
        """
        if not value:
            return ""
        
        sanitized = str(value).strip()
        
        # Allow only letters, spaces, hyphens, apostrophes, and periods
        sanitized = re.sub(r"[^a-zA-Z\s\-'\.]+", '', sanitized)
        
        # Remove multiple consecutive spaces
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Limit length
        sanitized = sanitized[:100]
        
        # Apply general sanitization
        sanitized = cls.sanitize(sanitized)
        
        return sanitized.title()
    
    @classmethod
    def sanitize_address(cls, value: str) -> str:
        """
        Sanitize address fields.
        
        Args:
            value: Address to sanitize
            
        Returns:
            str: Sanitized address
        """
        if not value:
            return ""
        
        sanitized = str(value).strip()
        
        # Allow letters, numbers, spaces, and common address characters
        sanitized = re.sub(r"[^a-zA-Z0-9\s\-\.#/,]+", '', sanitized)
        
        # Remove multiple consecutive spaces
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Limit length
        sanitized = sanitized[:255]
        
        # Apply general sanitization
        sanitized = cls.sanitize(sanitized)
        
        return sanitized


class HTMLSanitizer:
    """HTML content sanitizer using bleach."""
    
    # Allowed HTML tags for medical notes
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ]
    
    # Allowed attributes
    ALLOWED_ATTRIBUTES = {
        '*': ['class'],
    }
    
    # Allowed protocols
    ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
    
    @classmethod
    def sanitize(cls, value: str, strip_tags: bool = False) -> str:
        """
        Sanitize HTML content.
        
        Args:
            value: HTML content to sanitize
            strip_tags: Whether to strip all HTML tags
            
        Returns:
            str: Sanitized HTML content
        """
        if not value:
            return ""
        
        if strip_tags:
            # Strip all HTML tags
            return bleach.clean(value, tags=[], strip=True)
        else:
            # Clean HTML with allowed tags
            return bleach.clean(
                value,
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                protocols=cls.ALLOWED_PROTOCOLS,
                strip=True
            )
    
    @classmethod
    def sanitize_medical_notes(cls, value: str) -> str:
        """
        Sanitize medical notes with specific formatting allowances.
        
        Args:
            value: Medical notes to sanitize
            
        Returns:
            str: Sanitized medical notes
        """
        if not value:
            return ""
        
        # Allow basic formatting for medical notes
        medical_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
        
        sanitized = bleach.clean(
            value,
            tags=medical_tags,
            attributes={},
            protocols=[],
            strip=True
        )
        
        # Additional validation for medical context
        # Remove any potential PHI patterns that shouldn't be in notes
        sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN REDACTED]', sanitized)  # SSN pattern
        sanitized = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE REDACTED]', sanitized)  # Phone pattern
        
        return sanitized


class SQLSanitizer:
    """SQL injection prevention sanitizer."""
    
    # Dangerous SQL keywords
    DANGEROUS_KEYWORDS = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'EXEC', 'EXECUTE', 'UNION', 'SCRIPT', 'TRUNCATE', 'GRANT', 'REVOKE'
    ]
    
    # SQL injection patterns
    SQL_PATTERNS = [
        re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)", re.IGNORECASE),
        re.compile(r"(\b(UNION|OR|AND|WHERE|ORDER|GROUP|HAVING)\b\s)", re.IGNORECASE),
        re.compile(r"(--|#|\*\/|\/\*)"),
        re.compile(r"('|(\\')|(;)|(\\;)|(\|)|(\*)|(<)|(>))"),
    ]
    
    @classmethod
    def sanitize(cls, value: str) -> str:
        """
        Sanitize input to prevent SQL injection.
        
        Args:
            value: Input to sanitize
            
        Returns:
            str: SQL-safe sanitized input
        """
        if not value:
            return ""
        
        sanitized = str(value).strip()
        
        # Remove SQL injection patterns
        for pattern in cls.SQL_PATTERNS:
            sanitized = pattern.sub('', sanitized)
        
        # Remove dangerous keywords
        for keyword in cls.DANGEROUS_KEYWORDS:
            sanitized = re.sub(r'\b' + re.escape(keyword) + r'\b', '', sanitized, flags=re.IGNORECASE)
        
        # Escape single quotes by doubling them
        sanitized = sanitized.replace("'", "''")
        
        return sanitized
    
    @classmethod
    def escape_string(cls, value: str) -> str:
        """
        Escape string for safe SQL usage.
        
        Args:
            value: String to escape
            
        Returns:
            str: Escaped string
        """
        if not value:
            return ""
        
        # Use proper SQL string escaping
        escaped = str(value).replace("'", "''").replace("\\", "\\\\")
        return escaped


class PHISanitizer:
    """Specialized sanitizer for PHI data."""
    
    # PHI patterns to detect and potentially redact
    PHI_PATTERNS = {
        'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
        'phone': re.compile(r'\b\d{3}-?\d{3}-?\d{4}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'zip': re.compile(r'\b\d{5}(-\d{4})?\b'),
        'date': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
    }
    
    @classmethod
    def sanitize_for_logging(cls, value: str) -> str:
        """
        Sanitize PHI for safe logging (redacts sensitive patterns).
        
        Args:
            value: PHI value to sanitize for logging
            
        Returns:
            str: Sanitized value safe for logging
        """
        if not value:
            return ""
        
        sanitized = str(value)
        
        # Redact common PHI patterns
        sanitized = cls.PHI_PATTERNS['ssn'].sub('[SSN]', sanitized)
        sanitized = cls.PHI_PATTERNS['phone'].sub('[PHONE]', sanitized)
        sanitized = cls.PHI_PATTERNS['email'].sub('[EMAIL]', sanitized)
        
        # Truncate if too long
        if len(sanitized) > 50:
            sanitized = sanitized[:47] + "..."
        
        return sanitized
    
    @classmethod
    def sanitize_for_storage(cls, value: str, field_type: str) -> str:
        """
        Sanitize PHI for secure storage.
        
        Args:
            value: PHI value to sanitize
            field_type: Type of PHI field
            
        Returns:
            str: Sanitized value ready for secure storage
        """
        if not value:
            return ""
        
        # Apply basic sanitization
        sanitized = HIPAASanitizer.sanitize_input(value)
        
        # Additional field-specific sanitization
        if field_type in ['name', 'first_name', 'last_name']:
            sanitized = TextSanitizer.sanitize_name(sanitized)
        elif field_type in ['address', 'street_address']:
            sanitized = TextSanitizer.sanitize_address(sanitized)
        elif field_type in ['notes', 'medical_notes']:
            sanitized = HTMLSanitizer.sanitize_medical_notes(sanitized)
        else:
            sanitized = TextSanitizer.sanitize(sanitized, max_length=500)
        
        return sanitized
    
    @classmethod
    def detect_phi_in_text(cls, text: str) -> Dict[str, List[str]]:
        """
        Detect potential PHI patterns in text.
        
        Args:
            text: Text to analyze for PHI
            
        Returns:
            Dict: Dictionary of detected PHI patterns and their matches
        """
        detected = {}
        
        for phi_type, pattern in cls.PHI_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                detected[phi_type] = matches
        
        return detected


class DataSanitizer:
    """Main sanitizer class that combines all sanitization methods."""
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], phi_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sanitize all values in a dictionary.
        
        Args:
            data: Dictionary to sanitize
            phi_fields: List of field names that contain PHI
            
        Returns:
            Dict: Sanitized dictionary
        """
        if not data:
            return {}
        
        phi_fields = phi_fields or []
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value, phi_fields)
            elif isinstance(value, list):
                sanitized[key] = [cls.sanitize_value(item, key, key in phi_fields) for item in value]
            else:
                sanitized[key] = cls.sanitize_value(value, key, key in phi_fields)
        
        return sanitized
    
    @classmethod
    def sanitize_value(cls, value: Any, field_name: str, is_phi: bool = False) -> Any:
        """
        Sanitize a single value based on its type and whether it's PHI.
        
        Args:
            value: Value to sanitize
            field_name: Name of the field
            is_phi: Whether the field contains PHI
            
        Returns:
            Sanitized value
        """
        if value is None:
            return None
        
        if not isinstance(value, str):
            # For non-string values, just return as-is after basic validation
            return value
        
        if is_phi:
            return PHISanitizer.sanitize_for_storage(value, field_name)
        else:
            return TextSanitizer.sanitize(value)
    
    @classmethod
    def sanitize_for_api_response(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize data for API response (removes/redacts sensitive information).
        
        Args:
            data: Data to sanitize for API response
            
        Returns:
            Dict: Sanitized data safe for API response
        """
        if not data:
            return {}
        
        sanitized = {}
        
        for key, value in data.items():
            # Skip or redact sensitive fields
            if key.lower() in ['ssn', 'social_security_number']:
                sanitized[key] = '[REDACTED]'
            elif key.lower() in ['password', 'secret', 'token']:
                continue  # Skip entirely
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_for_api_response(value)
            elif isinstance(value, list):
                sanitized[key] = [cls.sanitize_for_api_response(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value
        
        return sanitized 