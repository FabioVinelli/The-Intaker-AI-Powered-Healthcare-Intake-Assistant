"""
HIPAA-compliant validators for healthcare data.
Provides comprehensive validation for PHI and healthcare-specific data types.
"""

import re
import phonenumbers
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date
from dateutil import parser
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)


class HIPAAValidator:
    """Base class for HIPAA-compliant validation."""
    
    @staticmethod
    def is_phi_field(field_name: str) -> bool:
        """
        Determine if a field contains PHI based on field name.
        
        Args:
            field_name: Name of the field to check
            
        Returns:
            bool: True if field likely contains PHI
        """
        phi_fields = {
            'name', 'first_name', 'last_name', 'full_name', 'patient_name',
            'ssn', 'social_security_number', 'social_security',
            'dob', 'date_of_birth', 'birth_date', 'birthdate',
            'phone', 'phone_number', 'telephone', 'mobile',
            'email', 'email_address',
            'address', 'street_address', 'home_address', 'zip_code', 'postal_code',
            'mrn', 'medical_record_number', 'patient_id',
            'insurance_id', 'insurance_number', 'member_id', 'policy_number',
            'diagnosis', 'medical_history', 'medication', 'allergy',
            'emergency_contact', 'next_of_kin'
        }
        
        field_lower = field_name.lower()
        return any(phi_field in field_lower for phi_field in phi_fields)
    
    @staticmethod
    def validate_required_field(value: Any, field_name: str) -> Any:
        """
        Validate that a required field is present and not empty.
        
        Args:
            value: The value to validate
            field_name: Name of the field for error messages
            
        Returns:
            The validated value
            
        Raises:
            ValidationError: If field is missing or empty
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            raise ValidationError(f"{field_name} is required and cannot be empty")
        return value


class SSNValidator:
    """Social Security Number validator with HIPAA compliance."""
    
    # SSN patterns: XXX-XX-XXXX, XXXXXXXXX, XXX XX XXXX
    SSN_PATTERNS = [
        re.compile(r'^\d{3}-\d{2}-\d{4}$'),      # XXX-XX-XXXX
        re.compile(r'^\d{9}$'),                   # XXXXXXXXX
        re.compile(r'^\d{3}\s\d{2}\s\d{4}$')     # XXX XX XXXX
    ]
    
    # Invalid SSN patterns to reject
    INVALID_SSNS = {
        '000000000', '111111111', '222222222', '333333333', '444444444',
        '555555555', '666666666', '777777777', '888888888', '999999999',
        '123456789', '987654321'
    }
    
    @classmethod
    def validate(cls, value: str) -> str:
        """
        Validate Social Security Number format and patterns.
        
        Args:
            value: SSN to validate
            
        Returns:
            str: Normalized SSN (digits only)
            
        Raises:
            ValidationError: If SSN format is invalid
        """
        if not value:
            raise ValidationError("SSN is required")
        
        # Remove all non-digit characters for validation
        digits_only = re.sub(r'\D', '', str(value))
        
        # Check length
        if len(digits_only) != 9:
            raise ValidationError("SSN must be exactly 9 digits")
        
        # Check against invalid patterns
        if digits_only in cls.INVALID_SSNS:
            raise ValidationError("Invalid SSN pattern")
        
        # Check area number (first 3 digits) - cannot be 000 or 666
        area_number = digits_only[:3]
        if area_number == '000' or area_number == '666':
            raise ValidationError("Invalid SSN area number")
        
        # Check that it's not all the same digit
        if len(set(digits_only)) == 1:
            raise ValidationError("SSN cannot be all the same digit")
        
        # Validate against original patterns to ensure proper format
        original_valid = any(pattern.match(value.strip()) for pattern in cls.SSN_PATTERNS)
        if not original_valid:
            raise ValidationError("SSN must be in format XXX-XX-XXXX, XXXXXXXXX, or XXX XX XXXX")
        
        return digits_only
    
    @classmethod
    def normalize(cls, value: str) -> str:
        """
        Normalize SSN to XXX-XX-XXXX format.
        
        Args:
            value: SSN to normalize
            
        Returns:
            str: Normalized SSN in XXX-XX-XXXX format
        """
        validated = cls.validate(value)
        return f"{validated[:3]}-{validated[3:5]}-{validated[5:]}"


class InsuranceNumberValidator:
    """Insurance number validator for various insurance types."""
    
    # Common insurance number patterns
    PATTERNS = {
        'medicare': re.compile(r'^[0-9]{3}-[0-9]{2}-[0-9]{4}[A-Z]?$'),
        'medicaid': re.compile(r'^[A-Z0-9]{8,12}$'),
        'commercial': re.compile(r'^[A-Z0-9]{6,20}$'),
        'group': re.compile(r'^[A-Z0-9]{1,20}$')
    }
    
    @classmethod
    def validate(cls, value: str, insurance_type: str = 'commercial') -> str:
        """
        Validate insurance number based on type.
        
        Args:
            value: Insurance number to validate
            insurance_type: Type of insurance (medicare, medicaid, commercial, group)
            
        Returns:
            str: Validated insurance number
            
        Raises:
            ValidationError: If insurance number format is invalid
        """
        if not value:
            raise ValidationError("Insurance number is required")
        
        value = str(value).strip().upper()
        
        if insurance_type.lower() not in cls.PATTERNS:
            insurance_type = 'commercial'
        
        pattern = cls.PATTERNS[insurance_type.lower()]
        
        if not pattern.match(value):
            raise ValidationError(f"Invalid {insurance_type} insurance number format")
        
        return value


class MedicalCodeValidator:
    """Validator for medical codes (ICD-10, CPT, etc.)."""
    
    # ICD-10 patterns
    ICD10_PATTERN = re.compile(r'^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$')
    
    # CPT code patterns
    CPT_PATTERN = re.compile(r'^[0-9]{5}$')
    
    # HCPCS patterns
    HCPCS_PATTERN = re.compile(r'^[A-Z][0-9]{4}$')
    
    @classmethod
    def validate_icd10(cls, value: str) -> str:
        """
        Validate ICD-10 diagnostic code.
        
        Args:
            value: ICD-10 code to validate
            
        Returns:
            str: Validated ICD-10 code
            
        Raises:
            ValidationError: If ICD-10 format is invalid
        """
        if not value:
            raise ValidationError("ICD-10 code is required")
        
        value = str(value).strip().upper()
        
        if not cls.ICD10_PATTERN.match(value):
            raise ValidationError("Invalid ICD-10 code format (should be like A00 or A00.1)")
        
        return value
    
    @classmethod
    def validate_cpt(cls, value: str) -> str:
        """
        Validate CPT procedure code.
        
        Args:
            value: CPT code to validate
            
        Returns:
            str: Validated CPT code
            
        Raises:
            ValidationError: If CPT format is invalid
        """
        if not value:
            raise ValidationError("CPT code is required")
        
        value = str(value).strip()
        
        if not cls.CPT_PATTERN.match(value):
            raise ValidationError("Invalid CPT code format (must be 5 digits)")
        
        return value


class PhoneNumberValidator:
    """Phone number validator with international support."""
    
    @classmethod
    def validate(cls, value: str, country_code: str = 'US') -> str:
        """
        Validate phone number using phonenumbers library.
        
        Args:
            value: Phone number to validate
            country_code: Default country code (default: US)
            
        Returns:
            str: Normalized phone number in E.164 format
            
        Raises:
            ValidationError: If phone number format is invalid
        """
        if not value:
            raise ValidationError("Phone number is required")
        
        try:
            # Parse the phone number
            parsed = phonenumbers.parse(str(value), country_code)
            
            # Validate the number
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError("Invalid phone number")
            
            # Return in E.164 format
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            
        except phonenumbers.NumberParseException as e:
            raise ValidationError(f"Invalid phone number format: {e}")


class DateOfBirthValidator:
    """Date of birth validator with age constraints."""
    
    MIN_AGE = 0
    MAX_AGE = 150
    
    @classmethod
    def validate(cls, value: Union[str, datetime, date]) -> date:
        """
        Validate date of birth.
        
        Args:
            value: Date of birth to validate
            
        Returns:
            date: Validated date of birth
            
        Raises:
            ValidationError: If date is invalid or unreasonable
        """
        if not value:
            raise ValidationError("Date of birth is required")
        
        # Parse the date
        if isinstance(value, str):
            try:
                parsed_date = parser.parse(value).date()
            except (ValueError, TypeError):
                raise ValidationError("Invalid date format")
        elif isinstance(value, datetime):
            parsed_date = value.date()
        elif isinstance(value, date):
            parsed_date = value
        else:
            raise ValidationError("Invalid date type")
        
        # Validate date is not in the future
        today = date.today()
        if parsed_date > today:
            raise ValidationError("Date of birth cannot be in the future")
        
        # Calculate age
        age = today.year - parsed_date.year - ((today.month, today.day) < (parsed_date.month, parsed_date.day))
        
        # Validate age constraints
        if age < cls.MIN_AGE:
            raise ValidationError(f"Age cannot be less than {cls.MIN_AGE}")
        
        if age > cls.MAX_AGE:
            raise ValidationError(f"Age cannot be greater than {cls.MAX_AGE}")
        
        return parsed_date


class NameValidator:
    """Name validator with injection protection."""
    
    # Allowed characters in names (letters, spaces, hyphens, apostrophes, periods)
    NAME_PATTERN = re.compile(r"^[a-zA-Z\s\-'\.]+$")
    
    # SQL injection patterns to reject
    SQL_INJECTION_PATTERNS = [
        re.compile(r"('|(\\')|(;)|(\\;)|(\|)|(\*)|(%)|(<)|(>))", re.IGNORECASE),
        re.compile(r"(select|insert|update|delete|drop|create|alter|exec|execute)", re.IGNORECASE),
        re.compile(r"(union|or|and|where|order|group|having)", re.IGNORECASE),
        re.compile(r"(script|javascript|vbscript|onload|onerror)", re.IGNORECASE)
    ]
    
    @classmethod
    def validate(cls, value: str, max_length: int = 100) -> str:
        """
        Validate name with injection protection.
        
        Args:
            value: Name to validate
            max_length: Maximum allowed length
            
        Returns:
            str: Validated and sanitized name
            
        Raises:
            ValidationError: If name format is invalid
        """
        if not value:
            raise ValidationError("Name is required")
        
        value = str(value).strip()
        
        # Check length
        if len(value) > max_length:
            raise ValidationError(f"Name cannot exceed {max_length} characters")
        
        if len(value) < 1:
            raise ValidationError("Name cannot be empty")
        
        # Check for valid characters
        if not cls.NAME_PATTERN.match(value):
            raise ValidationError("Name contains invalid characters")
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if pattern.search(value):
                raise ValidationError("Invalid characters detected in name")
        
        # Additional checks for suspicious patterns
        if len(set(value.replace(' ', ''))) == 1:  # All same character
            raise ValidationError("Invalid name pattern")
        
        if value.count(' ') > 10:  # Too many spaces
            raise ValidationError("Too many spaces in name")
        
        return value.title()  # Proper case


class MRNValidator:
    """Medical Record Number validator."""
    
    # MRN patterns (typically alphanumeric, 6-20 characters)
    MRN_PATTERN = re.compile(r'^[A-Z0-9]{6,20}$')
    
    @classmethod
    def validate(cls, value: str) -> str:
        """
        Validate Medical Record Number.
        
        Args:
            value: MRN to validate
            
        Returns:
            str: Validated MRN
            
        Raises:
            ValidationError: If MRN format is invalid
        """
        if not value:
            raise ValidationError("Medical Record Number is required")
        
        value = str(value).strip().upper()
        
        if not cls.MRN_PATTERN.match(value):
            raise ValidationError("Invalid MRN format (6-20 alphanumeric characters)")
        
        return value


class AddressValidator:
    """Address validator with basic format checking."""
    
    # US ZIP code patterns
    ZIP_PATTERN = re.compile(r'^\d{5}(-\d{4})?$')
    
    @classmethod
    def validate_street_address(cls, value: str) -> str:
        """
        Validate street address.
        
        Args:
            value: Street address to validate
            
        Returns:
            str: Validated street address
            
        Raises:
            ValidationError: If address format is invalid
        """
        if not value:
            raise ValidationError("Street address is required")
        
        value = str(value).strip()
        
        if len(value) < 5:
            raise ValidationError("Street address too short")
        
        if len(value) > 255:
            raise ValidationError("Street address too long")
        
        # Basic injection protection
        for pattern in NameValidator.SQL_INJECTION_PATTERNS:
            if pattern.search(value):
                raise ValidationError("Invalid characters detected in address")
        
        return value
    
    @classmethod
    def validate_zip_code(cls, value: str) -> str:
        """
        Validate US ZIP code.
        
        Args:
            value: ZIP code to validate
            
        Returns:
            str: Validated ZIP code
            
        Raises:
            ValidationError: If ZIP code format is invalid
        """
        if not value:
            raise ValidationError("ZIP code is required")
        
        value = str(value).strip()
        
        if not cls.ZIP_PATTERN.match(value):
            raise ValidationError("Invalid ZIP code format (must be XXXXX or XXXXX-XXXX)")
        
        return value 