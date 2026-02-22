"""
Centralized validation error definitions and standardized error response formats.
Provides consistent error handling across the validation library.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from flask import jsonify

logger = logging.getLogger(__name__)


class ValidationErrorType:
    """Constants for different types of validation errors."""
    FIELD_VALIDATION = "field_validation"
    SCHEMA_VALIDATION = "schema_validation"
    PHI_VALIDATION = "phi_validation"
    SANITIZATION_ERROR = "sanitization_error"
    SECURITY_VIOLATION = "security_violation"
    HIPAA_COMPLIANCE = "hipaa_compliance"
    DATA_TYPE_ERROR = "data_type_error"
    RANGE_ERROR = "range_error"
    FORMAT_ERROR = "format_error"
    REQUIRED_FIELD = "required_field"


class HIPAAValidationError(Exception):
    """Custom exception class for HIPAA-specific validation errors."""
    
    def __init__(self, message: str, error_type: str = ValidationErrorType.HIPAA_COMPLIANCE,
                 field_name: Optional[str] = None, field_value=None, context: Optional[str] = None,
                 phi_detected: bool = False):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.field_name = field_name
        self.field_value = self._sanitize_field_value(field_value, phi_detected)
        self.context = context
        self.phi_detected = phi_detected
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def _sanitize_field_value(self, value, phi_detected: bool) -> Optional[str]:
        """Sanitize field value for safe error reporting."""
        if value is None:
            return None
        if phi_detected:
            return "[PHI_REDACTED]"
        if isinstance(value, str) and len(value) > 50:
            return f"{value[:47]}..."
        return str(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            'error_type': self.error_type,
            'message': self.message,
            'field_name': self.field_name,
            'field_value': self.field_value,
            'context': self.context,
            'phi_detected': self.phi_detected,
            'timestamp': self.timestamp
        }


class ValidationErrorHandler:
    """Centralized handler for validation errors with standardized formatting."""
    
    @staticmethod
    def handle_validation_error(error: Exception, context: Optional[str] = None) -> Dict[str, Any]:
        """Handle any validation error and return standardized response."""
        try:
            if isinstance(error, HIPAAValidationError):
                return ValidationErrorHandler._handle_hipaa_error(error, context)
            elif hasattr(error, 'messages'):  # Marshmallow ValidationError
                return ValidationErrorHandler._handle_marshmallow_error(error, context)
            else:
                return ValidationErrorHandler._handle_generic_error(error, context)
        except Exception as e:
            logger.error(f"Error in validation error handler: {e}")
            return {
                'error': 'Internal Server Error',
                'message': 'Error processing validation failure',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    @staticmethod
    def _handle_hipaa_error(error: HIPAAValidationError, context: Optional[str] = None) -> Dict[str, Any]:
        """Handle HIPAA validation errors."""
        response = {
            'error': 'HIPAA Validation Error',
            'message': error.message,
            'details': error.to_dict(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        if context:
            response['context'] = context
        if error.phi_detected:
            logger.warning(f"PHI validation error in {context or 'unknown context'}")
        return response
    
    @staticmethod
    def _handle_marshmallow_error(error, context: Optional[str] = None) -> Dict[str, Any]:
        """Handle Marshmallow validation errors."""
        return {
            'error': 'Schema Validation Error',
            'message': 'Input data validation failed',
            'details': error.messages if hasattr(error, 'messages') else str(error),
            'context': context,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def _handle_generic_error(error: Exception, context: Optional[str] = None) -> Dict[str, Any]:
        """Handle generic validation errors."""
        logger.error(f"Unexpected validation error in {context}: {error}")
        return {
            'error': 'Validation Error',
            'message': 'An unexpected validation error occurred',
            'details': {'error_message': str(error), 'context': context},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def create_flask_response(error_dict: Dict[str, Any], status_code: int = 400):
        """Create a Flask JSON response from error dictionary."""
        return jsonify(error_dict), status_code


def handle_validation_error(error: Exception, context: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to handle any validation error."""
    return ValidationErrorHandler.handle_validation_error(error, context)
