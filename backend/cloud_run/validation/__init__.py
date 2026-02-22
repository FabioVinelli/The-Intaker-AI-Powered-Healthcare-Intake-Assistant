"""
HIPAA-compliant validation and sanitization library for The Intaker.
Provides comprehensive data validation and sanitization for healthcare data.
"""

from .validators import (
    HIPAAValidator,
    SSNValidator,
    InsuranceNumberValidator,
    MedicalCodeValidator,
    PhoneNumberValidator,
    DateOfBirthValidator,
    NameValidator,
    MRNValidator,
    AddressValidator
)

from .sanitizers import (
    HIPAASanitizer,
    TextSanitizer,
    HTMLSanitizer,
    SQLSanitizer,
    PHISanitizer,
    DataSanitizer
)

from .schemas import (
    PHIValidationSchema,
    PatientPHISchema,
    InsuranceSchema,
    MedicalHistorySchema,
    ContactInfoSchema,
    JSONSchemaValidator,
    PATIENT_RECORD_SCHEMA,
    INSURANCE_VERIFICATION_SCHEMA,
    MEDICAL_DOCUMENT_SCHEMA
)

from .integration import (
    validate_with_hipaa,
    ValidationConfig,
    EnhancedPatientCreateSchema,
    EnhancedPatientUpdateSchema,
    EnhancedDocumentCreateSchema,
    get_validation_decorator,
    ValidationUtils,
    PHI_FIELDS
)

from .errors import (
    ValidationErrorType,
    HIPAAValidationError,
    ValidationErrorHandler,
    handle_validation_error
)

__all__ = [
    # Validators
    'HIPAAValidator',
    'SSNValidator',
    'InsuranceNumberValidator',
    'MedicalCodeValidator',
    'PhoneNumberValidator',
    'DateOfBirthValidator',
    'NameValidator',
    'MRNValidator',
    'AddressValidator',
    
    # Sanitizers
    'HIPAASanitizer',
    'TextSanitizer',
    'HTMLSanitizer',
    'SQLSanitizer',
    'PHISanitizer',
    'DataSanitizer',
    
    # Schemas
    'PHIValidationSchema',
    'PatientPHISchema',
    'InsuranceSchema',
    'MedicalHistorySchema',
    'ContactInfoSchema',
    'JSONSchemaValidator',
    'PATIENT_RECORD_SCHEMA',
    'INSURANCE_VERIFICATION_SCHEMA',
    'MEDICAL_DOCUMENT_SCHEMA',
    
    # Integration
    'validate_with_hipaa',
    'ValidationConfig',
    'EnhancedPatientCreateSchema',
    'EnhancedPatientUpdateSchema',
    'EnhancedDocumentCreateSchema',
    'get_validation_decorator',
    'ValidationUtils',
    'PHI_FIELDS',
    
    # Error Handling
    'ValidationErrorType',
    'HIPAAValidationError',
    'ValidationErrorHandler',
    'handle_validation_error'
] 