"""
JSON Schema definitions for healthcare data structures.
Provides comprehensive validation schemas for complex healthcare data.
"""

import jsonschema
from typing import Dict, Any, Optional, List
from marshmallow import Schema, fields, validate, ValidationError
import logging

logger = logging.getLogger(__name__)


class JSONSchemaValidator:
    """Base class for JSON Schema validation."""
    
    @classmethod
    def validate_data(cls, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against JSON schema.
        
        Args:
            data: Data to validate
            schema: JSON schema to validate against
            
        Returns:
            Dict: Validated data
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            jsonschema.validate(instance=data, schema=schema)
            return data
        except jsonschema.ValidationError as e:
            raise ValidationError(f"Schema validation failed: {e.message}")
        except jsonschema.SchemaError as e:
            raise ValidationError(f"Invalid schema: {e.message}")


class PHIValidationSchema(Schema):
    """Base schema for PHI data validation."""
    
    # Patient Demographics
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
        validate=validate.OneOf(['M', 'F', 'O', 'U']),  # Male, Female, Other, Unknown
        description="Patient's gender"
    )
    
    # Contact Information
    phone_primary = fields.String(
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
    
    # Address Information
    street_address = fields.String(
        validate=validate.Length(min=5, max=255),
        description="Street address"
    )
    city = fields.String(
        validate=validate.Length(min=1, max=100),
        description="City"
    )
    state = fields.String(
        validate=validate.Length(min=2, max=2),
        description="State abbreviation"
    )
    zip_code = fields.String(
        validate=validate.Regexp(r'^\d{5}(-\d{4})?$'),
        description="ZIP code"
    )
    
    # Emergency Contact
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
    emergency_contact_relationship = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
        description="Relationship to emergency contact"
    )


class PatientPHISchema(PHIValidationSchema):
    """Comprehensive schema for patient PHI data."""
    
    # Medical Record Information
    mrn = fields.String(
        required=True,
        validate=validate.Regexp(r'^[A-Z0-9]{6,20}$'),
        description="Medical Record Number"
    )
    ssn = fields.String(
        allow_none=True,
        validate=validate.Regexp(r'^\d{3}-?\d{2}-?\d{4}$'),
        description="Social Security Number"
    )
    
    # Additional Demographics
    ethnicity = fields.String(
        allow_none=True,
        validate=validate.OneOf([
            'hispanic_latino', 'not_hispanic_latino', 'unknown', 'declined'
        ]),
        description="Ethnicity"
    )
    race = fields.String(
        allow_none=True,
        validate=validate.OneOf([
            'american_indian', 'asian', 'black', 'hawaiian_pacific', 'white', 'other', 'unknown'
        ]),
        description="Race"
    )
    preferred_language = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
        description="Preferred language"
    )
    marital_status = fields.String(
        allow_none=True,
        validate=validate.OneOf([
            'single', 'married', 'divorced', 'widowed', 'separated', 'domestic_partner', 'unknown'
        ]),
        description="Marital status"
    )
    
    # Employment Information
    employer = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
        description="Employer name"
    )
    occupation = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
        description="Occupation"
    )


class InsuranceSchema(Schema):
    """Schema for insurance information."""
    
    # Primary Insurance
    primary_insurance_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        description="Primary insurance company name"
    )
    primary_policy_number = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
        description="Primary insurance policy number"
    )
    primary_group_number = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
        description="Primary insurance group number"
    )
    primary_subscriber_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        description="Primary subscriber name"
    )
    primary_subscriber_dob = fields.Date(
        required=True,
        description="Primary subscriber date of birth"
    )
    primary_subscriber_relationship = fields.String(
        validate=validate.OneOf(['self', 'spouse', 'child', 'other']),
        description="Relationship to primary subscriber"
    )
    
    # Secondary Insurance (Optional)
    secondary_insurance_name = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
        description="Secondary insurance company name"
    )
    secondary_policy_number = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
        description="Secondary insurance policy number"
    )
    secondary_group_number = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
        description="Secondary insurance group number"
    )
    
    # Insurance Type
    insurance_type = fields.String(
        validate=validate.OneOf(['commercial', 'medicare', 'medicaid', 'self_pay', 'other']),
        description="Type of insurance"
    )
    
    # Verification
    verification_date = fields.Date(
        allow_none=True,
        description="Insurance verification date"
    )
    verification_status = fields.String(
        validate=validate.OneOf(['verified', 'pending', 'failed', 'not_required']),
        description="Insurance verification status"
    )


class MedicalHistorySchema(Schema):
    """Schema for medical history information."""
    
    # Chief Complaint
    chief_complaint = fields.String(
        allow_none=True,
        validate=validate.Length(max=500),
        description="Patient's chief complaint"
    )
    
    # Medical Conditions
    current_medications = fields.List(
        fields.Dict(keys=fields.String(), values=fields.Raw()),
        allow_none=True,
        description="List of current medications"
    )
    allergies = fields.List(
        fields.Dict(keys=fields.String(), values=fields.Raw()),
        allow_none=True,
        description="List of known allergies"
    )
    medical_conditions = fields.List(
        fields.Dict(keys=fields.String(), values=fields.Raw()),
        allow_none=True,
        description="List of current medical conditions"
    )
    surgical_history = fields.List(
        fields.Dict(keys=fields.String(), values=fields.Raw()),
        allow_none=True,
        description="List of previous surgeries"
    )
    
    # Family History
    family_history = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        allow_none=True,
        description="Family medical history"
    )
    
    # Social History
    smoking_status = fields.String(
        allow_none=True,
        validate=validate.OneOf(['never', 'former', 'current', 'unknown']),
        description="Smoking status"
    )
    alcohol_use = fields.String(
        allow_none=True,
        validate=validate.OneOf(['never', 'occasional', 'regular', 'excessive', 'unknown']),
        description="Alcohol use status"
    )
    drug_use = fields.String(
        allow_none=True,
        validate=validate.OneOf(['never', 'former', 'current', 'unknown']),
        description="Drug use status"
    )
    
    # Vital Signs
    height = fields.Float(
        allow_none=True,
        validate=validate.Range(min=12, max=120),  # inches
        description="Height in inches"
    )
    weight = fields.Float(
        allow_none=True,
        validate=validate.Range(min=1, max=1000),  # pounds
        description="Weight in pounds"
    )
    blood_pressure_systolic = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=50, max=300),
        description="Systolic blood pressure"
    )
    blood_pressure_diastolic = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=30, max=200),
        description="Diastolic blood pressure"
    )
    heart_rate = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=30, max=250),
        description="Heart rate in BPM"
    )
    temperature = fields.Float(
        allow_none=True,
        validate=validate.Range(min=90, max=110),  # Fahrenheit
        description="Body temperature in Fahrenheit"
    )


class ContactInfoSchema(Schema):
    """Schema for contact information validation."""
    
    preferred_contact_method = fields.String(
        validate=validate.OneOf(['phone', 'email', 'mail', 'portal']),
        description="Preferred contact method"
    )
    best_time_to_call = fields.String(
        allow_none=True,
        validate=validate.OneOf(['morning', 'afternoon', 'evening', 'anytime']),
        description="Best time to call"
    )
    can_leave_voicemail = fields.Boolean(
        allow_none=True,
        description="Permission to leave voicemail"
    )
    can_send_text = fields.Boolean(
        allow_none=True,
        description="Permission to send text messages"
    )
    communication_preferences = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        allow_none=True,
        description="Additional communication preferences"
    )


# JSON Schema Definitions
PATIENT_RECORD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "Patient Record Schema",
    "description": "Complete patient record with PHI and medical information",
    "properties": {
        "patient_id": {
            "type": "string",
            "pattern": "^[A-Z0-9]{6,20}$",
            "description": "Unique patient identifier"
        },
        "demographics": {
            "type": "object",
            "properties": {
                "first_name": {"type": "string", "minLength": 1, "maxLength": 50},
                "last_name": {"type": "string", "minLength": 1, "maxLength": 50},
                "middle_name": {"type": ["string", "null"], "maxLength": 50},
                "date_of_birth": {"type": "string", "format": "date"},
                "gender": {"type": "string", "enum": ["M", "F", "O", "U"]},
                "ssn": {"type": ["string", "null"], "pattern": "^\\d{3}-?\\d{2}-?\\d{4}$"},
                "mrn": {"type": "string", "pattern": "^[A-Z0-9]{6,20}$"}
            },
            "required": ["first_name", "last_name", "date_of_birth", "mrn"]
        },
        "contact_info": {
            "type": "object",
            "properties": {
                "phone_primary": {"type": "string", "minLength": 10, "maxLength": 15},
                "phone_secondary": {"type": ["string", "null"], "minLength": 10, "maxLength": 15},
                "email": {"type": ["string", "null"], "format": "email"},
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string", "minLength": 1, "maxLength": 255},
                        "city": {"type": "string", "minLength": 1, "maxLength": 100},
                        "state": {"type": "string", "minLength": 2, "maxLength": 2},
                        "zip_code": {"type": "string", "pattern": "^\\d{5}(-\\d{4})?$"}
                    },
                    "required": ["street", "city", "state", "zip_code"]
                }
            }
        },
        "insurance": {
            "type": "object",
            "properties": {
                "primary": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "minLength": 1, "maxLength": 100},
                        "policy_number": {"type": "string", "minLength": 1, "maxLength": 50},
                        "group_number": {"type": ["string", "null"], "maxLength": 50},
                        "subscriber_name": {"type": "string", "minLength": 1, "maxLength": 100},
                        "subscriber_dob": {"type": "string", "format": "date"},
                        "relationship": {"type": "string", "enum": ["self", "spouse", "child", "other"]}
                    },
                    "required": ["company_name", "policy_number", "subscriber_name", "subscriber_dob"]
                },
                "secondary": {
                    "type": ["object", "null"],
                    "properties": {
                        "company_name": {"type": "string", "maxLength": 100},
                        "policy_number": {"type": "string", "maxLength": 50},
                        "group_number": {"type": ["string", "null"], "maxLength": 50}
                    }
                }
            }
        },
        "medical_history": {
            "type": "object",
            "properties": {
                "chief_complaint": {"type": ["string", "null"], "maxLength": 500},
                "current_medications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "maxLength": 100},
                            "dosage": {"type": "string", "maxLength": 50},
                            "frequency": {"type": "string", "maxLength": 50},
                            "prescriber": {"type": ["string", "null"], "maxLength": 100}
                        },
                        "required": ["name", "dosage", "frequency"]
                    }
                },
                "allergies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "allergen": {"type": "string", "maxLength": 100},
                            "reaction": {"type": "string", "maxLength": 200},
                            "severity": {"type": "string", "enum": ["mild", "moderate", "severe", "unknown"]}
                        },
                        "required": ["allergen", "reaction"]
                    }
                },
                "vital_signs": {
                    "type": "object",
                    "properties": {
                        "height": {"type": ["number", "null"], "minimum": 12, "maximum": 120},
                        "weight": {"type": ["number", "null"], "minimum": 1, "maximum": 1000},
                        "bp_systolic": {"type": ["integer", "null"], "minimum": 50, "maximum": 300},
                        "bp_diastolic": {"type": ["integer", "null"], "minimum": 30, "maximum": 200},
                        "heart_rate": {"type": ["integer", "null"], "minimum": 30, "maximum": 250},
                        "temperature": {"type": ["number", "null"], "minimum": 90, "maximum": 110}
                    }
                }
            }
        },
        "audit_info": {
            "type": "object",
            "properties": {
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "string"},
                "updated_by": {"type": "string"},
                "version": {"type": "integer", "minimum": 1}
            },
            "required": ["created_at", "created_by", "version"]
        }
    },
    "required": ["patient_id", "demographics", "audit_info"]
}

INSURANCE_VERIFICATION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "Insurance Verification Schema",
    "description": "Schema for insurance verification data",
    "properties": {
        "verification_id": {"type": "string"},
        "patient_id": {"type": "string"},
        "insurance_type": {"type": "string", "enum": ["primary", "secondary"]},
        "verification_date": {"type": "string", "format": "date-time"},
        "status": {"type": "string", "enum": ["verified", "pending", "failed", "expired"]},
        "coverage_details": {
            "type": "object",
            "properties": {
                "effective_date": {"type": "string", "format": "date"},
                "termination_date": {"type": ["string", "null"], "format": "date"},
                "copay": {"type": ["number", "null"], "minimum": 0},
                "deductible": {"type": ["number", "null"], "minimum": 0},
                "out_of_pocket_max": {"type": ["number", "null"], "minimum": 0}
            }
        },
        "benefits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "service_type": {"type": "string"},
                    "coverage_level": {"type": "string"},
                    "limitations": {"type": ["string", "null"]}
                }
            }
        }
    },
    "required": ["verification_id", "patient_id", "verification_date", "status"]
}

MEDICAL_DOCUMENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "Medical Document Schema",
    "description": "Schema for medical document metadata and content",
    "properties": {
        "document_id": {"type": "string"},
        "patient_id": {"type": "string"},
        "document_type": {
            "type": "string",
            "enum": ["intake_form", "consent", "lab_result", "imaging", "prescription", "referral", "other"]
        },
        "title": {"type": "string", "maxLength": 200},
        "content": {
            "type": "object",
            "properties": {
                "extracted_text": {"type": ["string", "null"]},
                "structured_data": {"type": ["object", "null"]},
                "phi_detected": {"type": "boolean"},
                "confidence_score": {"type": "number", "minimum": 0, "maximum": 1}
            }
        },
        "file_info": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "file_size": {"type": "integer", "minimum": 0},
                "mime_type": {"type": "string"},
                "checksum": {"type": "string"}
            },
            "required": ["filename", "file_size", "mime_type"]
        },
        "processing_info": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "processing", "completed", "failed"]
                },
                "processed_at": {"type": ["string", "null"], "format": "date-time"},
                "processing_notes": {"type": ["string", "null"]}
            },
            "required": ["status"]
        }
    },
    "required": ["document_id", "patient_id", "document_type", "file_info", "processing_info"]
} 