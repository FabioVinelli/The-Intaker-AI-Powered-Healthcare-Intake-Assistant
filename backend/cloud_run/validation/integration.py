"""
Integration layer for HIPAA-compliant validation with existing API endpoints.
Provides enhanced schemas and validation decorators for The Intaker API.
"""

import functools
import logging
from typing import Dict, Any, Optional, List, Callable
from flask import request, jsonify, g
from marshmallow import Schema, fields, validate, ValidationError, post_load

from .validators import (
    HIPAAValidator, SSNValidator, InsuranceNumberValidator, 
    PhoneNumberValidator, DateOfBirthValidator, NameValidator,
    MRNValidator, AddressValidator
)
from .sanitizers import (
    HIPAASanitizer, TextSanitizer, HTMLSanitizer, 
    PHISanitizer, DataSanitizer
)
from .schemas import (
    PatientPHISchema, InsuranceSchema, MedicalHistorySchema,
    ContactInfoSchema, JSONSchemaValidator, PATIENT_RECORD_SCHEMA
)

logger = logging.getLogger(__name__)


class ValidationConfig:
    """Configuration for validation behavior."""
    
    ENABLE_STRICT_VALIDATION = True
    ENABLE_PHI_LOGGING = True
    ENABLE_SANITIZATION = True
    LOG_VALIDATION_ERRORS = True


def validate_with_hipaa(schema_class: Schema = None, phi_fields: List[str] = None):
    """
    Decorator to add HIPAA-compliant validation to API endpoints.
    
    Args:
        schema_class: Marshmallow schema class for validation
        phi_fields: List of field names that contain PHI
        
    Returns:
        Decorated function with enhanced validation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Get request data
                data = request.get_json() if request.is_json else {}
                
                # Apply sanitization first
                if ValidationConfig.ENABLE_SANITIZATION:
                    data = DataSanitizer.sanitize_dict(data, phi_fields or [])
                
                # Apply schema validation if provided
                if schema_class:
                    try:
                        schema = schema_class()
                        validated_data = schema.load(data)
                        g.validated_data = validated_data
                    except ValidationError as e:
                        if ValidationConfig.LOG_VALIDATION_ERRORS:
                            logger.warning(f"Validation error in {func.__name__}: {e.messages}")
                        return jsonify({
                            'error': 'Validation Error',
                            'message': 'Invalid input data',
                            'details': e.messages
                        }), 400
                
                # Log PHI access if enabled
                if ValidationConfig.ENABLE_PHI_LOGGING and phi_fields:
                    logger.info(f"PHI access in {func.__name__}", extra={
                        'phi_fields': phi_fields,
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'user_id': getattr(g, 'current_user_id', 'unknown')
                    })
                
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Validation error in {func.__name__}: {e}")
                return jsonify({
                    'error': 'Internal Server Error',
                    'message': 'Validation processing failed'
                }), 500
        
        return wrapper
    return decorator


class EnhancedPatientCreateSchema(Schema):
    """Enhanced patient creation schema with HIPAA validation."""
    
    # Basic patient information
    patient_id = fields.String(
        allow_none=True,
        validate=validate.Regexp(r'^[A-Z0-9]{6,20}$'),
        description="Unique patient identifier (auto-generated if not provided)"
    )
    
    # Demographics (PHI)
    first_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
        description="Patient's first name"
    )
    last_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
        description="Patient's last name"
    )
    middle_name = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
        description="Patient's middle name"
    )
    date_of_birth = fields.Date(
        required=True,
        description="Patient's date of birth"
    )
    gender = fields.String(
        validate=validate.OneOf(['M', 'F', 'O', 'U']),
        description="Patient's gender (M/F/O/U)"
    )
    ssn = fields.String(
        allow_none=True,
        validate=validate.Regexp(r'^\d{3}-?\d{2}-?\d{4}$'),
        description="Social Security Number"
    )
    mrn = fields.String(
        allow_none=True,
        validate=validate.Regexp(r'^[A-Z0-9]{6,20}$'),
        description="Medical Record Number"
    )
    
    # Contact Information (PHI)
    phone_primary = fields.String(
        allow_none=True,
        validate=validate.Length(min=10, max=15),
        description="Primary phone number"
    )
    phone_secondary = fields.String(
        allow_none=True,
        validate=validate.Length(min=10, max=15),
        description="Secondary phone number"
    )
    email = fields.Email(
        allow_none=True,
        description="Email address"
    )
    
    # Address Information (PHI)
    street_address = fields.String(
        allow_none=True,
        validate=validate.Length(min=5, max=255),
        description="Street address"
    )
    city = fields.String(
        allow_none=True,
        validate=validate.Length(min=1, max=100),
        description="City"
    )
    state = fields.String(
        allow_none=True,
        validate=validate.Length(min=2, max=2),
        description="State abbreviation"
    )
    zip_code = fields.String(
        allow_none=True,
        validate=validate.Regexp(r'^\d{5}(-\d{4})?$'),
        description="ZIP code"
    )
    
    # Insurance Information (PHI)
    primary_insurance_name = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
        description="Primary insurance company"
    )
    primary_policy_number = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
        description="Primary insurance policy number"
    )
    
    # Emergency Contact (PHI)
    emergency_contact_name = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
        description="Emergency contact name"
    )
    emergency_contact_phone = fields.String(
        allow_none=True,
        validate=validate.Length(min=10, max=15),
        description="Emergency contact phone"
    )
    
    # Non-PHI fields
    status = fields.String(
        validate=validate.OneOf(["pending", "active", "inactive"]),
        missing="pending",
        description="Patient status"
    )
    administrative_notes = fields.String(
        allow_none=True,
        validate=validate.Length(max=1000),
        description="Administrative notes (non-PHI)"
    )
    preferred_language = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
        description="Preferred language"
    )
    
    @post_load
    def validate_and_sanitize(self, data, **kwargs):
        """Apply HIPAA-compliant validation and sanitization."""
        validated_data = {}
        
        for field_name, value in data.items():
            if value is None:
                validated_data[field_name] = value
                continue
            
            try:
                # Apply field-specific validation
                if field_name in ['first_name', 'last_name', 'middle_name', 'emergency_contact_name']:
                    validated_data[field_name] = NameValidator.validate(str(value))
                elif field_name == 'ssn' and value:
                    validated_data[field_name] = SSNValidator.validate(str(value))
                elif field_name == 'mrn' and value:
                    validated_data[field_name] = MRNValidator.validate(str(value))
                elif field_name in ['phone_primary', 'phone_secondary', 'emergency_contact_phone'] and value:
                    validated_data[field_name] = PhoneNumberValidator.validate(str(value))
                elif field_name == 'date_of_birth':
                    validated_data[field_name] = DateOfBirthValidator.validate(value)
                elif field_name == 'street_address' and value:
                    validated_data[field_name] = AddressValidator.validate_street_address(str(value))
                elif field_name == 'zip_code' and value:
                    validated_data[field_name] = AddressValidator.validate_zip_code(str(value))
                elif field_name == 'primary_policy_number' and value:
                    validated_data[field_name] = InsuranceNumberValidator.validate(str(value))
                else:
                    # Apply general sanitization
                    if isinstance(value, str):
                        is_phi = HIPAAValidator.is_phi_field(field_name)
                        if is_phi:
                            validated_data[field_name] = PHISanitizer.sanitize_for_storage(str(value), field_name)
                        else:
                            validated_data[field_name] = TextSanitizer.sanitize(str(value))
                    else:
                        validated_data[field_name] = value
                        
            except ValidationError as e:
                raise ValidationError({field_name: str(e)})
            except Exception as e:
                logger.error(f"Validation error for field {field_name}: {e}")
                raise ValidationError({field_name: f"Validation failed: {str(e)}"})
        
        return validated_data


class EnhancedPatientUpdateSchema(Schema):
    """Enhanced patient update schema with HIPAA validation."""
    
    # Contact Information Updates
    phone_primary = fields.String(
        allow_none=True,
        validate=validate.Length(min=10, max=15),
        description="Primary phone number"
    )
    phone_secondary = fields.String(
        allow_none=True,
        validate=validate.Length(min=10, max=15),
        description="Secondary phone number"
    )
    email = fields.Email(
        allow_none=True,
        description="Email address"
    )
    
    # Address Updates
    street_address = fields.String(
        allow_none=True,
        validate=validate.Length(min=5, max=255),
        description="Street address"
    )
    city = fields.String(
        allow_none=True,
        validate=validate.Length(min=1, max=100),
        description="City"
    )
    state = fields.String(
        allow_none=True,
        validate=validate.Length(min=2, max=2),
        description="State abbreviation"
    )
    zip_code = fields.String(
        allow_none=True,
        validate=validate.Regexp(r'^\d{5}(-\d{4})?$'),
        description="ZIP code"
    )
    
    # Insurance Updates
    primary_insurance_name = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
        description="Primary insurance company"
    )
    primary_policy_number = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
        description="Primary insurance policy number"
    )
    
    # Emergency Contact Updates
    emergency_contact_name = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
        description="Emergency contact name"
    )
    emergency_contact_phone = fields.String(
        allow_none=True,
        validate=validate.Length(min=10, max=15),
        description="Emergency contact phone"
    )
    
    # Status Updates
    status = fields.String(
        allow_none=True,
        validate=validate.OneOf(["active", "inactive"]),
        description="Patient status"
    )
    administrative_notes = fields.String(
        allow_none=True,
        validate=validate.Length(max=1000),
        description="Administrative notes (non-PHI)"
    )
    
    @post_load
    def validate_and_sanitize(self, data, **kwargs):
        """Apply HIPAA-compliant validation and sanitization."""
        validated_data = {}
        
        for field_name, value in data.items():
            if value is None:
                validated_data[field_name] = value
                continue
            
            try:
                # Apply field-specific validation
                if field_name in ['emergency_contact_name']:
                    validated_data[field_name] = NameValidator.validate(str(value))
                elif field_name in ['phone_primary', 'phone_secondary', 'emergency_contact_phone']:
                    validated_data[field_name] = PhoneNumberValidator.validate(str(value))
                elif field_name == 'street_address':
                    validated_data[field_name] = AddressValidator.validate_street_address(str(value))
                elif field_name == 'zip_code':
                    validated_data[field_name] = AddressValidator.validate_zip_code(str(value))
                elif field_name == 'primary_policy_number':
                    validated_data[field_name] = InsuranceNumberValidator.validate(str(value))
                else:
                    # Apply general sanitization
                    if isinstance(value, str):
                        is_phi = HIPAAValidator.is_phi_field(field_name)
                        if is_phi:
                            validated_data[field_name] = PHISanitizer.sanitize_for_storage(str(value), field_name)
                        else:
                            validated_data[field_name] = TextSanitizer.sanitize(str(value))
                    else:
                        validated_data[field_name] = value
                        
            except ValidationError as e:
                raise ValidationError({field_name: str(e)})
            except Exception as e:
                logger.error(f"Validation error for field {field_name}: {e}")
                raise ValidationError({field_name: f"Validation failed: {str(e)}"})
        
        return validated_data


class EnhancedDocumentCreateSchema(Schema):
    """Enhanced document creation schema with HIPAA validation."""
    
    document_id = fields.String(
        allow_none=True,
        validate=validate.Regexp(r'^[A-Z0-9_-]{6,50}$'),
        description="Unique document identifier"
    )
    patient_id = fields.String(
        required=True,
        validate=validate.Regexp(r'^[A-Z0-9]{6,20}$'),
        description="Associated patient ID"
    )
    file_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
        description="Original file name"
    )
    document_type = fields.String(
        required=True,
        validate=validate.OneOf([
            'intake_form', 'consent', 'lab_result', 'imaging', 
            'prescription', 'referral', 'insurance_card', 'other'
        ]),
        description="Type of document"
    )
    file_size = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=1, max=50*1024*1024),  # Max 50MB
        description="File size in bytes"
    )
    mime_type = fields.String(
        allow_none=True,
        validate=validate.OneOf([
            'application/pdf', 'image/jpeg', 'image/png', 'image/tiff',
            'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]),
        description="File MIME type"
    )
    processing_notes = fields.String(
        allow_none=True,
        validate=validate.Length(max=1000),
        description="Processing notes"
    )
    
    @post_load
    def validate_and_sanitize(self, data, **kwargs):
        """Apply HIPAA-compliant validation and sanitization."""
        validated_data = {}
        
        for field_name, value in data.items():
            if value is None:
                validated_data[field_name] = value
                continue
            
            try:
                if field_name == 'file_name':
                    # Sanitize filename but preserve extension
                    sanitized = TextSanitizer.sanitize(str(value), max_length=255)
                    validated_data[field_name] = sanitized
                elif field_name == 'processing_notes':
                    # Allow some HTML in processing notes but sanitize
                    validated_data[field_name] = HTMLSanitizer.sanitize(str(value))
                else:
                    # Apply general sanitization
                    if isinstance(value, str):
                        validated_data[field_name] = TextSanitizer.sanitize(str(value))
                    else:
                        validated_data[field_name] = value
                        
            except Exception as e:
                logger.error(f"Validation error for field {field_name}: {e}")
                raise ValidationError({field_name: f"Validation failed: {str(e)}"})
        
        return validated_data


# PHI field definitions for different endpoints
PHI_FIELDS = {
    'patient_create': [
        'first_name', 'last_name', 'middle_name', 'date_of_birth', 'ssn', 'mrn',
        'phone_primary', 'phone_secondary', 'email', 'street_address', 'city', 
        'state', 'zip_code', 'primary_insurance_name', 'primary_policy_number',
        'emergency_contact_name', 'emergency_contact_phone'
    ],
    'patient_update': [
        'phone_primary', 'phone_secondary', 'email', 'street_address', 'city',
        'state', 'zip_code', 'primary_insurance_name', 'primary_policy_number',
        'emergency_contact_name', 'emergency_contact_phone'
    ],
    'document_create': [],  # No direct PHI in document metadata
    'medical_history': [
        'chief_complaint', 'current_medications', 'allergies', 'medical_conditions',
        'surgical_history', 'family_history'
    ]
}


def get_validation_decorator(endpoint_type: str):
    """
    Get the appropriate validation decorator for an endpoint type.
    
    Args:
        endpoint_type: Type of endpoint (patient_create, patient_update, etc.)
        
    Returns:
        Validation decorator configured for the endpoint type
    """
    schema_mapping = {
        'patient_create': EnhancedPatientCreateSchema,
        'patient_update': EnhancedPatientUpdateSchema,
        'document_create': EnhancedDocumentCreateSchema,
    }
    
    schema_class = schema_mapping.get(endpoint_type)
    phi_fields = PHI_FIELDS.get(endpoint_type, [])
    
    return validate_with_hipaa(schema_class=schema_class, phi_fields=phi_fields)


class ValidationUtils:
    """Utility functions for validation integration."""
    
    @staticmethod
    def validate_json_schema(data: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """
        Validate data against a named JSON schema.
        
        Args:
            data: Data to validate
            schema_name: Name of the schema to use
            
        Returns:
            Validated data
            
        Raises:
            ValidationError: If validation fails
        """
        schema_mapping = {
            'patient_record': PATIENT_RECORD_SCHEMA,
            # Add more schemas as needed
        }
        
        schema = schema_mapping.get(schema_name)
        if not schema:
            raise ValidationError(f"Unknown schema: {schema_name}")
        
        return JSONSchemaValidator.validate_data(data, schema)
    
    @staticmethod
    def sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize data for safe logging.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data safe for logging
        """
        return DataSanitizer.sanitize_for_api_response(data)
    
    @staticmethod
    def detect_phi_in_request(data: Dict[str, Any]) -> List[str]:
        """
        Detect potential PHI fields in request data.
        
        Args:
            data: Request data to analyze
            
        Returns:
            List of field names that likely contain PHI
        """
        phi_fields = []
        for field_name in data.keys():
            if HIPAAValidator.is_phi_field(field_name):
                phi_fields.append(field_name)
        return phi_fields 