"""
Unit test configuration and fixtures.
Enhanced fixtures specifically for isolated unit testing with comprehensive mocking.
"""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
from datetime import datetime
from typing import Dict, Any

# Add the parent directory to the path so we can import our app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application for unit tests."""
    
    # Set test environment variables
    test_env = {
        'FLASK_ENV': 'testing',
        'TESTING': 'true',
        'SECRET_KEY': 'test-secret-key-for-unit-tests',
        'GOOGLE_CLOUD_PROJECT': 'test-project-id',
        'FIRESTORE_DATABASE': 'test-db',
        'GOOGLE_CLIENT_ID': 'test-client-id',
        'GOOGLE_CLIENT_SECRET': 'test-client-secret',
        'DISABLE_AUTH_FOR_TESTING': 'false',  # Enable auth testing in unit tests
        
        # Set rate limiting to high values for testing
        'RATELIMIT_DEFAULT': '10000 per minute',
        'RATELIMIT_PHI_ACCESS': '10000 per minute',
        'RATELIMIT_HEALTH': '10000 per minute',
    }
    
    # Apply test environment
    for key, value in test_env.items():
        os.environ[key] = value
    
    # Create the app with test configuration
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Set up mock rate limiter directly in the app
    from unittest.mock import Mock
    mock_limiter = Mock()
    mock_limiter.limit.return_value = lambda f: f  # Return function unchanged
    mock_limiter.test_request.return_value = None  # No rate limit violation
    app.limiter = mock_limiter
    
    # Create application context
    with app.app_context():
        yield app
    
    # Cleanup environment variables
    for key in test_env:
        os.environ.pop(key, None)


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the Flask application."""
    return app.test_cli_runner()


@pytest.fixture
def mock_firestore_client():
    """Create a comprehensive mock Firestore client."""
    mock_client = Mock()
    mock_db = Mock()
    mock_client.db = mock_db
    
    # Mock collection and document operations
    mock_collection = Mock()
    mock_db.collection.return_value = mock_collection
    
    mock_document = Mock()
    mock_collection.document.return_value = mock_document
    
    # Mock query operations
    mock_collection.where.return_value = mock_collection
    mock_collection.limit.return_value = mock_collection
    mock_collection.offset.return_value = mock_collection
    mock_collection.stream.return_value = []
    mock_collection.get.return_value = []
    
    # Mock document operations
    mock_doc_snapshot = Mock()
    mock_doc_snapshot.exists = False
    mock_doc_snapshot.to_dict.return_value = {}
    mock_document.get.return_value = mock_doc_snapshot
    mock_document.set.return_value = None
    mock_document.update.return_value = None
    mock_document.delete.return_value = None
    
    return mock_client


@pytest.fixture
def mock_firestore_document_storage(mock_firestore_client):
    """Create a mock FirestoreDocumentStorage instance."""
    with patch('cloud_functions.document_processing.firestore_integration.FirestoreDocumentStorage') as mock_storage_class:
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        
        # Set up the mock storage instance
        mock_storage.db = mock_firestore_client.db
        
        # Mock audit logging methods
        mock_storage.log_manual_audit_event = Mock()
        mock_storage.log_phi_access_attempt = Mock()
        mock_storage.log_api_call = Mock()
        mock_storage.log_authentication_event = Mock()
        
        # Mock transaction methods
        mock_storage.create_with_transaction = Mock()
        mock_storage.update_with_transaction = Mock()
        mock_storage.delete_with_transaction = Mock()
        
        yield mock_storage


@pytest.fixture
def sample_patient_data():
    """Provide comprehensive sample patient data for testing."""
    return [
        {
            'patient_id': 'patient_001',
            'registration_date': datetime(2024, 1, 15, 10, 30, 0),
            'document_count': 3,
            'last_document_upload': datetime(2024, 1, 20, 14, 45, 0),
            'status': 'active',
            'administrative_notes': 'Regular patient, prefers email contact',
            'metadata': {
                'source': 'api',
                'priority': 'normal',
                'tags': ['regular', 'email-preferred']
            },
            '_version': 1,
            '_created_at': datetime(2024, 1, 15, 10, 30, 0),
            '_updated_at': datetime(2024, 1, 20, 14, 45, 0),
            '_created_by': 'test_user_001'
        },
        {
            'patient_id': 'patient_002',
            'registration_date': datetime(2024, 1, 16, 9, 15, 0),
            'document_count': 1,
            'last_document_upload': datetime(2024, 1, 16, 9, 30, 0),
            'status': 'pending',
            'administrative_notes': None,
            'metadata': {
                'source': 'manual',
                'priority': 'high',
                'tags': ['new', 'urgent']
            },
            '_version': 1,
            '_created_at': datetime(2024, 1, 16, 9, 15, 0),
            '_updated_at': datetime(2024, 1, 16, 9, 15, 0),
            '_created_by': 'test_user_002'
        },
        {
            'patient_id': 'patient_003',
            'registration_date': datetime(2024, 1, 17, 14, 20, 0),
            'document_count': 5,
            'last_document_upload': datetime(2024, 1, 22, 11, 10, 0),
            'status': 'inactive',
            'administrative_notes': 'Patient completed treatment, archived',
            'metadata': {
                'source': 'api',
                'priority': 'low',
                'tags': ['completed', 'archived']
            },
            '_version': 2,
            '_created_at': datetime(2024, 1, 17, 14, 20, 0),
            '_updated_at': datetime(2024, 1, 22, 11, 10, 0),
            '_created_by': 'test_user_001'
        }
    ]


@pytest.fixture
def sample_document_data():
    """Provide comprehensive sample document data for testing."""
    return [
        {
            'document_id': 'doc_001',
            'patient_id': 'patient_001',
            'file_name': 'intake_form.pdf',
            'document_type': 'intake_form',
            'upload_timestamp': datetime(2024, 1, 20, 14, 45, 0),
            'processing_status': 'completed',
            'phi_detected': True,
            'file_size': 2048576,
            'processing_metadata': {
                'extraction_confidence': 0.95,
                'processing_time_ms': 1200,
                'ocr_engine': 'tesseract',
                'phi_entities_found': 8
            },
            '_version': 1,
            '_created_at': datetime(2024, 1, 20, 14, 45, 0),
            '_updated_at': datetime(2024, 1, 20, 15, 30, 0),
            '_created_by': 'test_user_001'
        },
        {
            'document_id': 'doc_002',
            'patient_id': 'patient_001',
            'file_name': 'lab_results.pdf',
            'document_type': 'lab_result',
            'upload_timestamp': datetime(2024, 1, 21, 9, 0, 0),
            'processing_status': 'pending',
            'phi_detected': False,
            'file_size': 1048576,
            'processing_metadata': None,
            '_version': 1,
            '_created_at': datetime(2024, 1, 21, 9, 0, 0),
            '_updated_at': datetime(2024, 1, 21, 9, 0, 0),
            '_created_by': 'test_user_002'
        },
        {
            'document_id': 'doc_003',
            'patient_id': 'patient_002',
            'file_name': 'insurance_card.jpg',
            'document_type': 'insurance',
            'upload_timestamp': datetime(2024, 1, 16, 9, 30, 0),
            'processing_status': 'failed',
            'phi_detected': True,
            'file_size': 512000,
            'processing_metadata': {
                'extraction_confidence': 0.2,
                'processing_time_ms': 5000,
                'ocr_engine': 'tesseract',
                'error_message': 'Low image quality'
            },
            '_version': 2,
            '_created_at': datetime(2024, 1, 16, 9, 30, 0),
            '_updated_at': datetime(2024, 1, 16, 10, 0, 0),
            '_created_by': 'test_user_002'
        }
    ]


@pytest.fixture
def sample_user_data():
    """Provide comprehensive sample user data for testing."""
    return [
        {
            'uid': 'firebase_uid_001',
            'email': 'doctor@example.com',
            'display_name': 'Dr. John Smith',
            'role': 'doctor',
            'roles': ['doctor', 'user'],
            'phone_number': '+1234567890',
            'email_verified': True,
            'disabled': False,
            'creation_time': datetime(2024, 1, 10, 8, 0, 0),
            'last_sign_in_time': datetime(2024, 1, 20, 9, 30, 0),
            'custom_claims': {
                'department': 'cardiology',
                'license_number': 'MD123456'
            }
        },
        {
            'uid': 'firebase_uid_002',
            'email': 'admin@example.com',
            'display_name': 'Admin User',
            'role': 'admin',
            'roles': ['admin', 'doctor', 'user'],
            'phone_number': '+0987654321',
            'email_verified': True,
            'disabled': False,
            'creation_time': datetime(2024, 1, 5, 10, 0, 0),
            'last_sign_in_time': datetime(2024, 1, 22, 14, 15, 0),
            'custom_claims': {
                'department': 'administration',
                'permissions': ['user_management', 'system_admin']
            }
        },
        {
            'uid': 'firebase_uid_003',
            'email': 'staff@example.com',
            'display_name': 'Staff Member',
            'role': 'staff',
            'roles': ['staff', 'user'],
            'phone_number': None,
            'email_verified': True,
            'disabled': False,
            'creation_time': datetime(2024, 1, 12, 14, 30, 0),
            'last_sign_in_time': datetime(2024, 1, 21, 11, 45, 0),
            'custom_claims': {
                'department': 'reception'
            }
        }
    ]


@pytest.fixture
def mock_firestore_documents(sample_patient_data, sample_document_data):
    """Create mock Firestore document objects from sample data."""
    def create_mock_doc(data):
        mock_doc = Mock()
        mock_doc.to_dict.return_value = data
        mock_doc.exists = True
        mock_doc.id = data.get('patient_id') or data.get('document_id') or 'mock_id'
        return mock_doc
    
    patient_docs = [create_mock_doc(data) for data in sample_patient_data]
    document_docs = [create_mock_doc(data) for data in sample_document_data]
    
    return {
        'patients': patient_docs,
        'documents': document_docs,
        'all': patient_docs + document_docs
    }


@pytest.fixture
def auth_headers():
    """Provide mock authentication headers for testing."""
    return {
        'Authorization': 'Bearer test-jwt-token-for-unit-tests',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def admin_auth_headers():
    """Provide mock admin authentication headers for testing."""
    return {
        'Authorization': 'Bearer test-admin-jwt-token-for-unit-tests',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def mock_jwt_decode():
    """Mock JWT decoding for authentication testing."""
    return {
        'sub': 'test-user-id-123',
        'email': 'test@example.com',
        'name': 'Test User',
        'picture': 'https://example.com/avatar.jpg',
        'email_verified': True,
        'iss': 'https://securetoken.google.com/test-project-id',
        'aud': 'test-project-id',
        'exp': 9999999999,  # Far future expiry
        'iat': 1000000000,   # Past issued time
        'role': 'doctor',
        'roles': ['doctor', 'user'],
        'custom_claims': {
            'department': 'testing',
            'license_number': 'TEST123'
        }
    }


@pytest.fixture
def mock_admin_jwt_decode():
    """Mock admin JWT decoding for authentication testing."""
    return {
        'sub': 'test-admin-user-id-456',
        'email': 'admin@example.com',
        'name': 'Test Admin',
        'picture': 'https://example.com/admin-avatar.jpg',
        'email_verified': True,
        'iss': 'https://securetoken.google.com/test-project-id',
        'aud': 'test-project-id',
        'exp': 9999999999,
        'iat': 1000000000,
        'role': 'admin',
        'roles': ['admin', 'doctor', 'user'],
        'custom_claims': {
            'department': 'administration',
            'permissions': ['user_management', 'system_admin']
        }
    }


@pytest.fixture(autouse=True)
def mock_external_dependencies(monkeypatch, mock_firestore_document_storage, mock_jwt_decode):
    """Automatically mock external dependencies for all unit tests."""
    
    # Mock Firestore client creation
    def mock_get_firestore_client():
        return mock_firestore_document_storage
    
    # Apply mocks to all route modules
    route_modules = ['routes.patients', 'routes.documents', 'routes.users', 'routes.health']
    for module in route_modules:
        try:
            monkeypatch.setattr(f'{module}.get_firestore_client', mock_get_firestore_client)
        except AttributeError:
            # Module might not have this function, skip
            pass
    
    # Mock Google OAuth2 token verification with proper import path
    def mock_verify_oauth2_token(token, request, audience=None):
        if token == 'test-jwt-token-for-unit-tests':
            return mock_jwt_decode
        elif token == 'test-admin-jwt-token-for-unit-tests':
            return {
                **mock_jwt_decode,
                'sub': 'test-admin-user-id-456',
                'email': 'admin@example.com',
                'role': 'admin',
                'roles': ['admin', 'doctor', 'user']
            }
        else:
            raise ValueError("Invalid token")
    
    # Use the correct import path for Google ID token verification
    monkeypatch.setattr('google.oauth2.id_token.verify_oauth2_token', mock_verify_oauth2_token)
    
    # Mock Firebase Admin SDK token verification
    def mock_firebase_verify_token(token):
        if token == 'test-jwt-token-for-unit-tests':
            return mock_jwt_decode
        elif token == 'test-admin-jwt-token-for-unit-tests':
            return {
                **mock_jwt_decode,
                'sub': 'test-admin-user-id-456',
                'email': 'admin@example.com',
                'role': 'admin',
                'roles': ['admin', 'doctor', 'user']
            }
        else:
            raise ValueError("Invalid token")
    
    try:
        monkeypatch.setattr('firebase_admin.auth.verify_id_token', mock_firebase_verify_token)
    except AttributeError:
        # Firebase Admin SDK might not be available
        pass
    
    # Mock Firebase Admin initialization
    monkeypatch.setattr('auth.initialize_firebase_admin', lambda: True)
    
    # Mock get_current_user_id function with proper default
    def mock_get_current_user_id():
        return 'test-user-id-123'
    
    # Mock get_current_user function  
    def mock_get_current_user():
        return {
            'uid': 'test-user-id-123',
            'email': 'test@example.com',
            'role': 'user'
        }
    
    # Apply mocks to auth module and route modules
    monkeypatch.setattr('auth.get_current_user_id', mock_get_current_user_id)
    monkeypatch.setattr('auth.get_current_user', mock_get_current_user)
    
    for module in route_modules:
        try:
            monkeypatch.setattr(f'{module}.get_current_user_id', mock_get_current_user_id)
            monkeypatch.setattr(f'{module}.get_current_user', mock_get_current_user)
        except AttributeError:
            pass


@pytest.fixture
def mock_structured_logger(monkeypatch):
    """Mock structured logger for testing."""
    
    mock_logger = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.debug = Mock()
    
    # Mock the StructuredLogger class
    def mock_structured_logger_init(name, level='INFO'):
        return mock_logger
    
    monkeypatch.setattr('app.StructuredLogger', mock_structured_logger_init)
    
    return mock_logger


@pytest.fixture
def test_error_responses():
    """Provide standard error response templates for testing."""
    return {
        'bad_request': {
            'error': 'Bad Request',
            'message': 'Invalid request format',
            'status_code': 400
        },
        'unauthorized': {
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'status_code': 401
        },
        'forbidden': {
            'error': 'Forbidden',
            'message': 'Insufficient permissions',
            'status_code': 403
        },
        'not_found': {
            'error': 'Not Found',
            'message': 'Resource not found',
            'status_code': 404
        },
        'too_many_requests': {
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded',
            'status_code': 429,
            'retry_after': 60
        },
        'internal_error': {
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }
    }


@pytest.fixture
def mock_validation_schemas(monkeypatch):
    """Mock marshmallow schemas for testing validation."""
    
    # This fixture can be used to override schema validation in specific tests
    # where you want to test the behavior with different validation outcomes
    
    def create_mock_schema(valid=True, error_fields=None):
        mock_schema = Mock()
        
        if valid:
            mock_schema.load.return_value = {'test': 'data'}
            mock_schema.dump.return_value = {'test': 'data'}
        else:
            from marshmallow import ValidationError
            errors = error_fields or {'field': ['This field is required.']}
            mock_schema.load.side_effect = ValidationError(errors)
        
        return mock_schema
    
    return create_mock_schema


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line(
        "markers", 
        "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers",
        "auth: mark test as an authentication test"
    )
    config.addinivalue_line(
        "markers",
        "validation: mark test as a validation test"
    )
    config.addinivalue_line(
        "markers",
        "error_handling: mark test as an error handling test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Mark all tests in unit directory as unit tests
        if 'unit' in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add specific markers based on test names
        if 'auth' in item.name.lower():
            item.add_marker(pytest.mark.auth)
        
        if 'validation' in item.name.lower() or 'schema' in item.name.lower():
            item.add_marker(pytest.mark.validation)
        
        if 'error' in item.name.lower() or 'exception' in item.name.lower():
            item.add_marker(pytest.mark.error_handling) 